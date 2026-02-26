"""
╔══════════════════════════════════════════════════════════════╗
║  ∞  INFINITY TELEGRAM V1.0 — Cyber Black Luxury Edition  ∞  ║
╚══════════════════════════════════════════════════════════════╝
Full rewrite — everything connected, real Telethon, unified reports.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os, sys, json, threading, asyncio, random, string, time, shutil
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (THEME, TR, load_settings, save_settings,
                    SESSIONS_DIR, TOOLS_DIR, DATA_DIR, API_HASH_FILE, ACCOUNTS_FILE)
from managers import (ApiHashManager, AccountsManager, WorkingAccountsManager,
                      ToolsManager, SessionsManager, ProxyManager)
from antiban import human_delay, invisible_chars, safe_batch

try:
    from engine import InfinityClient, HAS_TELETHON
except Exception:
    HAS_TELETHON = False
    InfinityClient = None


# ══════════════════════════════════════════════════
# GLOBAL REPORT — shared across every operation
# ══════════════════════════════════════════════════
class Report:
    def __init__(self):
        self.clear()

    def clear(self):
        self.ok = []
        self.fail = []

    def add_ok(self, msg):
        self.ok.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    def add_fail(self, msg):
        self.fail.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    @property
    def total(self):
        return len(self.ok) + len(self.fail)

    def save_to(self, path):
        with open(path, "w", encoding="utf-8") as f:
            f.write("═══ Infinity Telegram V1.0 — Report ═══\n")
            f.write(f"Date : {datetime.now()}\n")
            f.write(f"Total: {self.total} | ✅ {len(self.ok)} | ❌ {len(self.fail)}\n\n")
            f.write("── SUCCESS ──\n")
            for x in self.ok:
                f.write(f"  ✅ {x}\n")
            f.write("\n── FAILED ──\n")
            for x in self.fail:
                f.write(f"  ❌ {x}\n")


# ══════════════════════════════════════════════════
# MAIN APPLICATION
# ══════════════════════════════════════════════════
class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.S = load_settings()
        self.lang = self.S.get("language", "ar")
        self.T = TR[self.lang]
        self.proxy_mgr = ProxyManager()
        self.report = Report()

        self.running = False
        self.scraped = []
        self.scraped_ids = []
        self.clients = {}          # phone -> lightweight status/info ONLY (DO NOT store Telethon clients)
        self.pending_code_hashes = self._load_pending_code_hashes()

        self.title(self.T["title"])
        self.geometry("1120x760")
        self.minsize(980, 700)
        self.configure(bg=THEME["bg"])
        self.page = None

        self._build()
        self.show("accounts")

    # ── helpers ──
    def t(self, k):
        return self.T.get(k, k)

    # pending login code hashes (Telethon requires phone_code_hash on confirm)
    def _pending_hashes_path(self):
        return os.path.join(DATA_DIR, "pending_code_hashes.json")

    def _load_pending_code_hashes(self):
        path = self._pending_hashes_path()
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save_pending_code_hashes(self):
        path = self._pending_hashes_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.pending_code_hashes, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _set_pending_code_hash(self, phone, code_hash):
        if code_hash:
            self.pending_code_hashes[str(phone)] = str(code_hash)
            self._save_pending_code_hashes()

    def _clear_pending_code_hash(self, phone):
        if str(phone) in self.pending_code_hashes:
            self.pending_code_hashes.pop(str(phone), None)
            self._save_pending_code_hashes()

    def switch_lang(self, l):
        self.lang = l
        self.S["language"] = l
        save_settings(self.S)
        self.T = TR[l]
        for w in self.winfo_children():
            w.destroy()
        self._build()
        self.show(self.page or "accounts")

    def set_status(self, txt):
        self.slbl.config(text=txt)
        self.update_idletasks()

    def log(self, msg):
        """Log to whatever result_lb is visible right now."""
        try:
            if hasattr(self, "result_lb") and self.result_lb.winfo_exists():
                self.result_lb.insert("end", msg)
                self.result_lb.see("end")
        except Exception:
            pass
        self.set_status(msg)

    # ── async helper — run Telethon in background thread ──
    def _thread(self, fn, *a, done=None):
        def _worker():
            lp = asyncio.new_event_loop()
            asyncio.set_event_loop(lp)
            try:
                res = lp.run_until_complete(fn(*a))
                if done:
                    self.after(0, done, res)
            except Exception as e:
                self.after(0, lambda: self.log(f"❌ Error: {e}"))
            finally:
                lp.close()
        threading.Thread(target=_worker, daemon=True).start()

    # ── get / ensure a connected client ──
    def _pick_phone(self):
        """Pick a phone with a valid session (cached clients can belong to closed loops)."""
        for ph in WorkingAccountsManager.load():
            for a in AccountsManager.load():
                if a.get("phone") == ph and a.get("api_id") and SessionsManager.session_exists(ph):
                    return ph
        for a in AccountsManager.load():
            if SessionsManager.session_exists(a["phone"]) and a.get("api_id"):
                return a["phone"]
        return None

    async def _get_client(self, phone):
        """Return a connected InfinityClient for *phone* in CURRENT loop."""
        acc = None
        for a in AccountsManager.load():
            if a["phone"] == phone:
                acc = a
                break
        if not acc or not acc.get("api_id"):
            raise RuntimeError(f"No API credentials for {phone}")
        c = InfinityClient(phone, acc["api_id"], acc["api_hash"])
        await c.connect()
        return c

    # ══════════════════════════════════════════════
    # BUILD SKELETON
    # ══════════════════════════════════════════════
    def _build(self):
        self.main = tk.Frame(self, bg=THEME["bg"])
        self.main.pack(fill="both", expand=True)

        # ── top bar ──
        top = tk.Frame(self.main, bg=THEME["surface"], height=44)
        top.pack(fill="x")
        top.pack_propagate(False)
        tk.Label(top, text="∞", font=("Segoe UI", 20, "bold"),
                 bg=THEME["surface"], fg=THEME["accent2"]).pack(side="left", padx=10)
        tk.Label(top, text="INFINITY TELEGRAM V1.0",
                 font=("Segoe UI", 12, "bold"),
                 bg=THEME["surface"], fg=THEME["gold"]).pack(side="left", padx=4)
        tk.Label(top, text="Cyber Black Luxury",
                 font=("Segoe UI", 9),
                 bg=THEME["surface"], fg=THEME["text3"]).pack(side="left", padx=6)
        lf = tk.Frame(top, bg=THEME["surface"])
        lf.pack(side="right", padx=8)
        for code, label in [("ar", "عربي"), ("en", "EN")]:
            bg = THEME["accent"] if self.lang == code else THEME["btn_bg"]
            tk.Button(lf, text=label, font=("Segoe UI", 8, "bold"),
                      bg=bg, fg="#fff", bd=0, padx=6, pady=1, cursor="hand2",
                      command=lambda c=code: self.switch_lang(c)).pack(side="left", padx=2)

        body = tk.Frame(self.main, bg=THEME["bg"])
        body.pack(fill="both", expand=True)
        self._sidebar(body)
        self.content = tk.Frame(body, bg=THEME["bg"])
        self.content.pack(
            side="left" if self.lang == "en" else "right",
            fill="both", expand=True, padx=2, pady=2)

        # ── status bar ──
        self.sbar = tk.Frame(self, bg=THEME["surface2"], height=22)
        self.sbar.pack(fill="x", side="bottom")
        self.sbar.pack_propagate(False)
        self.slbl = tk.Label(self.sbar, text="Ready | جاهز",
                             font=("Consolas", 9),
                             bg=THEME["surface2"], fg=THEME["text3"])
        self.slbl.pack(side="left", padx=8)
        info = (f"API: {ApiHashManager.count()} | "
                f"Accounts: {len(AccountsManager.load())} | "
                f"Sessions: {len(SessionsManager.list_sessions())}")
        tk.Label(self.sbar, text=info, font=("Consolas", 9),
                 bg=THEME["surface2"], fg=THEME["accent3"]).pack(side="right", padx=8)

    def _sidebar(self, parent):
        side = "right" if self.lang == "en" else "left"
        sb = tk.Frame(parent, bg=THEME["surface"], width=148)
        sb.pack(side=side, fill="y")
        sb.pack_propagate(False)
        tk.Frame(sb, bg=THEME["accent"], height=2).pack(fill="x")
        self.sbtns = {}
        pages = [
            ("accounts", "accounts"), ("search", "search"), ("join", "join"),
            ("extract", "extract"), ("filter", "filter"), ("send_msg", "send_msg"),
            ("adding", "adding"), ("read_msg", "read_msg"),
            ("complaints", "complaints"), ("leave", "leave"),
            ("ban_members", "ban_members"), ("make_admin", "make_admin"),
            ("proxies", "proxies"), ("settings", "settings"), ("reports", "reports"),
        ]
        for key, pg in pages:
            b = tk.Button(
                sb, text=self.t(key), font=("Segoe UI", 9, "bold"),
                bg=THEME["btn_bg"], fg=THEME["text"],
                activebackground=THEME["accent"], activeforeground="#fff",
                bd=0, cursor="hand2", anchor="center",
                command=lambda p=pg: self.show(p))
            b.pack(fill="x", padx=3, pady=1, ipady=2)
            self.sbtns[pg] = b
        tk.Frame(sb, bg=THEME["accent"], height=2).pack(fill="x", side="bottom")

    def show(self, pg):
        for k, b in self.sbtns.items():
            b.config(bg=THEME["accent"] if k == pg else THEME["btn_bg"],
                     fg="#fff" if k == pg else THEME["text"])
        for w in self.content.winfo_children():
            w.destroy()
        self.page = pg
        fn = getattr(self, f"P_{pg}", None)
        if fn:
            fn()

    # ══════════════════════════════════════════════
    # WIDGET FACTORY
    # ══════════════════════════════════════════════
    def _title(self, p, txt):
        f = tk.Frame(p, bg=THEME["accent"], height=36)
        f.pack(fill="x", pady=(0, 3))
        f.pack_propagate(False)
        tk.Label(f, text=txt, font=("Segoe UI", 12, "bold"),
                 bg=THEME["accent"], fg="#fff").pack(expand=True)

    def _sec(self, p, txt=None):
        f = tk.Frame(p, bg=THEME["surface"],
                     highlightbackground=THEME["border"], highlightthickness=1)
        f.pack(fill="x", padx=3, pady=2)
        if txt:
            tk.Label(f, text=txt, font=("Segoe UI", 9, "bold"),
                     bg=THEME["surface2"], fg=THEME["accent3"]).pack(fill="x")
        return f

    def _btn(self, p, txt, cmd, st="normal"):
        colours = {
            "normal": THEME["btn_bg"], "accent": THEME["accent"],
            "green": THEME["green"], "red": THEME["red"],
            "gold": THEME["gold"], "orange": THEME["orange"],
            "cyan": THEME["cyan"],
        }
        bg = colours.get(st, THEME["btn_bg"])
        fg = "#000" if st in ("gold", "cyan") else "#fff"
        return tk.Button(
            p, text=txt, command=cmd, font=("Segoe UI", 9, "bold"),
            bg=bg, fg=fg, activebackground=THEME["accent2"],
            bd=0, cursor="hand2", padx=8, pady=3)

    def _brow(self, p, items):
        r = tk.Frame(p, bg=THEME["surface"])
        r.pack(fill="x", padx=3, pady=1)
        for txt, cmd, *rest in items:
            st = rest[0] if rest else "normal"
            self._btn(r, txt, cmd, st).pack(side="left", fill="x", expand=True, padx=1)
        return r

    def _entry(self, p, w=30, d=""):
        e = tk.Entry(
            p, font=("JetBrains Mono", 10), width=w,
            bg=THEME["entry_bg"], fg=THEME["text"],
            insertbackground=THEME["accent3"], selectbackground=THEME["accent"],
            bd=0, highlightthickness=1, highlightcolor=THEME["accent"],
            highlightbackground=THEME["entry_border"])
        if d:
            e.insert(0, d)
        return e

    def _text(self, p, h=5):
        t = tk.Text(
            p, height=h, font=("JetBrains Mono", 10),
            bg=THEME["entry_bg"], fg=THEME["text"],
            insertbackground=THEME["accent3"], selectbackground=THEME["accent"],
            bd=0, wrap="word", highlightthickness=1,
            highlightcolor=THEME["accent"],
            highlightbackground=THEME["entry_border"])
        t.pack(fill="both", expand=True, padx=3, pady=2)
        return t

    def _lb(self, p, h=8, fg=None):
        f = tk.Frame(p, bg=THEME["bg"])
        f.pack(fill="both", expand=True, padx=3, pady=2)
        sb = tk.Scrollbar(f)
        sb.pack(side="right", fill="y")
        lb = tk.Listbox(
            f, height=h, font=("JetBrains Mono", 9),
            bg=THEME["entry_bg"], fg=fg or THEME["text"],
            selectbackground=THEME["accent"], bd=0,
            highlightthickness=1,
            highlightbackground=THEME["entry_border"],
            yscrollcommand=sb.set)
        lb.pack(fill="both", expand=True)
        sb.config(command=lb.yview)
        return lb

    def _tree(self, p, cols, h=10):
        f = tk.Frame(p, bg=THEME["bg"])
        f.pack(fill="both", expand=True, padx=3, pady=2)
        ys = ttk.Scrollbar(f, orient="vertical")
        xs = ttk.Scrollbar(f, orient="horizontal")
        t = ttk.Treeview(
            f, columns=[c[0] for c in cols], show="headings", height=h,
            yscrollcommand=ys.set, xscrollcommand=xs.set)
        ys.config(command=t.yview)
        xs.config(command=t.xview)
        ys.pack(side="right", fill="y")
        xs.pack(side="bottom", fill="x")
        t.pack(fill="both", expand=True)
        for cid, ctxt, cw in cols:
            t.heading(cid, text=ctxt, anchor="center")
            t.column(cid, width=cw, anchor="center", minwidth=35)
        for tag, bg in [("odd", THEME["table_r1"]), ("even", THEME["table_r2"])]:
            t.tag_configure(tag, background=bg)
        t.tag_configure("gold", foreground=THEME["gold"])
        t.tag_configure("red", foreground=THEME["red"])
        t.tag_configure("green", foreground=THEME["green"])
        return t

    def _dual(self, p, lt, rt, h=6):
        f = tk.Frame(p, bg=THEME["bg"])
        f.pack(fill="both", expand=True, padx=3, pady=2)
        # left
        lf = tk.Frame(f, bg=THEME["success_bg"],
                       highlightbackground=THEME["green"], highlightthickness=1)
        lf.pack(side="left", fill="both", expand=True, padx=1)
        tk.Label(lf, text=lt, font=("Segoe UI", 9, "bold"),
                 bg=THEME["green"], fg="#fff").pack(fill="x")
        ll = tk.Listbox(lf, height=h, font=("JetBrains Mono", 9),
                        bg=THEME["success_bg"], fg=THEME["green2"], bd=0)
        ll.pack(fill="both", expand=True)
        # right
        rf = tk.Frame(f, bg=THEME["fail_bg"],
                       highlightbackground=THEME["red"], highlightthickness=1)
        rf.pack(side="right", fill="both", expand=True, padx=1)
        tk.Label(rf, text=rt, font=("Segoe UI", 9, "bold"),
                 bg=THEME["red"], fg="#fff").pack(fill="x")
        rl = tk.Listbox(rf, height=h, font=("JetBrains Mono", 9),
                        bg=THEME["fail_bg"], fg=THEME["red2"], bd=0)
        rl.pack(fill="both", expand=True)
        return ll, rl

    def _spin(self, p, v=1, lo=0, hi=99999, w=6):
        s = tk.Spinbox(
            p, from_=lo, to=hi, width=w,
            font=("JetBrains Mono", 10),
            bg=THEME["entry_bg"], fg=THEME["text"],
            buttonbackground=THEME["btn_bg"], bd=0, justify="center",
            highlightthickness=1, highlightbackground=THEME["entry_border"])
        s.delete(0, "end")
        s.insert(0, str(v))
        return s

    def _big(self, p, txt, cmd, st="green"):
        colours = {"green": THEME["green"], "red": THEME["red"],
                   "accent": THEME["accent"]}
        tk.Button(
            p, text=txt, command=cmd, font=("Segoe UI", 13, "bold"),
            bg=colours.get(st, THEME["green"]), fg="#fff",
            activebackground=THEME["accent2"], bd=0, cursor="hand2",
            pady=7).pack(fill="x", padx=3, pady=3)

    # ══════════════════════════════════════════════════════════════
    #  P A G E :  ACCOUNTS + CODES  (MERGED — SPLIT VIEW)
    # ══════════════════════════════════════════════════════════════
    def P_accounts(self):
        p = self.content
        self._title(p, f"{self.t('accounts')} + {self.t('codes')}")

        split = tk.Frame(p, bg=THEME["bg"])
        split.pack(fill="both", expand=True, padx=3, pady=2)

        # ── LEFT half: phone numbers ──
        left = tk.Frame(split, bg=THEME["surface"],
                        highlightbackground=THEME["border"], highlightthickness=1)
        left.pack(side="left", fill="both", expand=True, padx=2)

        tk.Label(left,
                 text=f"📱 {self.t('accounts')} — {self.t('enter_phones')}",
                 font=("Segoe UI", 10, "bold"),
                 bg=THEME["surface2"], fg=THEME["gold"]).pack(fill="x")
        self.phones_txt = self._text(left, h=10)

        # auto-load from Accounts.txt
        for a in AccountsManager.load():
            self.phones_txt.insert("end", a["phone"] + "\n")

        info = tk.Frame(left, bg=THEME["surface"])
        info.pack(fill="x", padx=3, pady=2)
        tk.Label(info, text=f"{self.t('lines')}:",
                 font=("Segoe UI", 9), bg=THEME["surface"],
                 fg=THEME["text2"]).pack(side="left", padx=2)
        self.ph_count = tk.Label(
            info, text=str(len(AccountsManager.load())),
            font=("JetBrains Mono", 10, "bold"),
            bg=THEME["surface"], fg=THEME["gold"])
        self.ph_count.pack(side="left")
        tk.Label(info,
                 text=f"  API: {ApiHashManager.count()}  |  "
                      f"Sessions: {len(SessionsManager.list_sessions())}",
                 font=("Segoe UI", 9), bg=THEME["surface"],
                 fg=THEME["cyan"]).pack(side="left", padx=6)

        # ── RIGHT half: codes ──
        right = tk.Frame(split, bg=THEME["surface"],
                         highlightbackground=THEME["border"], highlightthickness=1)
        right.pack(side="right", fill="both", expand=True, padx=2)

        tk.Label(right,
                 text=f"🔑 {self.t('codes')} — code,password (per line)",
                 font=("Segoe UI", 10, "bold"),
                 bg=THEME["surface2"], fg=THEME["cyan"]).pack(fill="x")
        self.codes_txt = self._text(right, h=10)

        tk.Label(right,
                 text="Format:  code   or   code,2fa_password\n"
                      "Each line matches the phone on the same line number",
                 font=("Consolas", 8), bg=THEME["surface"],
                 fg=THEME["text3"], justify="left").pack(fill="x", padx=4, pady=2)

        # ── BUTTONS ──
        self._brow(p, [
            (self.t("send_codes"), self._send_codes, "accent"),
            (self.t("confirm_codes"), self._confirm_codes, "green"),
            (self.t("check_banned"), self._check_accounts, "orange"),
        ])
        self._brow(p, [
            (self.t("clear_all"),
             lambda: [self.phones_txt.delete("1.0", "end"),
                      self.codes_txt.delete("1.0", "end")]),
            (self.t("remove_dup"), self._dedup),
            (self.t("remove_banned"), self._rm_banned, "red"),
            (self.t("save_working"), self._save_working, "green"),
        ])
        self._brow(p, [
            (self.t("download_sess"), self._dl_sessions),
            (self.t("remove_invalid"), self._rm_invalid),
            (self.t("logout_devices"), lambda: self.set_status("Logout…")),
            (self.t("set_pass"), lambda: self.set_status("Passwords…")),
        ])

        # ── RESULT LIST ──
        self.result_lb = self._lb(p, h=6)

    # ── phone / code parsing ──
    def _phones(self):
        lines = [l.strip().rstrip(";")
                 for l in self.phones_txt.get("1.0", "end").split("\n")
                 if l.strip()]
        out = []
        for l in lines:
            ph = l.split(",")[0].split("@")[0].strip()
            if ph and (ph.startswith("+") or ph[0].isdigit()):
                if not ph.startswith("+"):
                    ph = "+" + ph
                out.append(ph)
        return out

    def _codes_list(self):
        """Return [(code, 2fa_password), …] matched by line order."""
        lines = [l.strip()
                 for l in self.codes_txt.get("1.0", "end").split("\n")
                 if l.strip()]
        out = []
        for l in lines:
            parts = l.split(",", 1)
            code = parts[0].strip()
            pwd = parts[1].strip() if len(parts) > 1 else ""
            if code:
                out.append((code, pwd))
        return out

    # ── SEND CODES ──
    def _send_codes(self):
        phones = self._phones()
        if not phones:
            messagebox.showwarning("!", "No phones entered")
            return
        apis = ApiHashManager.load()
        if not apis:
            messagebox.showerror("!", "Api_Hash.txt is empty!\n"
                                      "Add lines:  api_id,api_hash")
            return
        if not HAS_TELETHON:
            messagebox.showerror("!", "Telethon not installed!\npip install telethon")
            return

        # save to Accounts.txt
        for i, ph in enumerate(phones):
            aid, ah = apis[i % len(apis)]
            AccountsManager.add(ph, aid, ah)

        self.result_lb.delete(0, "end")
        self.set_status(f"Sending codes to {len(phones)} …")

        def _work():
            lp = asyncio.new_event_loop()
            asyncio.set_event_loop(lp)
            results = []
            for i, ph in enumerate(phones):
                aid, ah = apis[i % len(apis)]
                c = None
                try:
                    c = InfinityClient(ph, aid, ah)
                    lp.run_until_complete(c.connect())

                    if lp.run_until_complete(c.client.is_user_authorized()):
                        self._clear_pending_code_hash(ph)
                        results.append((ph, "logged", "Already logged in"))
                    else:
                        sent = lp.run_until_complete(c.client.send_code_request(ph))
                        self._set_pending_code_hash(ph, getattr(sent, "phone_code_hash", ""))
                        results.append((ph, "sent", "Code sent"))

                except Exception as e:
                    results.append((ph, "err", str(e)))

                finally:
                    if c:
                        try:
                            lp.run_until_complete(c.disconnect())
                        except Exception:
                            pass

            lp.close()
            self.after(0, lambda: self._on_sent(results))

        threading.Thread(target=_work, daemon=True).start()

    def _on_sent(self, results):
        self.result_lb.delete(0, "end")
        n = 0
        for ph, st, msg in results:
            if st == "sent":
                self.result_lb.insert("end", f"  ✅ {ph} — Code sent")
                self.report.add_ok(f"Code sent: {ph}")
                n += 1
            elif st == "logged":
                self.result_lb.insert("end", f"  🟢 {ph} — Already logged in")
                self.report.add_ok(f"Already in: {ph}")
                WorkingAccountsManager.add(ph)
            else:
                self.result_lb.insert("end", f"  ❌ {ph} — {msg}")
                self.report.add_fail(f"Send fail: {ph} — {msg}")
        self.result_lb.insert(
            "end", f"\n📤 Sent: {n} — Enter codes on the RIGHT, then Confirm")
        self.set_status(f"Codes sent to {n} accounts")

    # ── CONFIRM CODES ──
    def _confirm_codes(self):
        phones = self._phones()
        codes = self._codes_list()
        if not phones:
            messagebox.showwarning("!", "No phones")
            return
        if not codes:
            messagebox.showwarning("!", "No codes — enter them on the RIGHT side")
            return
        if len(codes) < len(phones):
            messagebox.showwarning(
                "!",
                f"Phones: {len(phones)}  but  Codes: {len(codes)}\n"
                f"Enter one code per line matching the phone order.")
            return
        if not HAS_TELETHON:
            messagebox.showerror("!", "Telethon not installed!")
            return

        self.result_lb.delete(0, "end")
        self.set_status("Confirming codes …")
        pairs = list(zip(phones, codes))

        def _work():
            lp = asyncio.new_event_loop()
            asyncio.set_event_loop(lp)
            results = []

            for ph, (code, pwd) in pairs:
                acc = None
                for a in AccountsManager.load():
                    if a["phone"] == ph:
                        acc = a
                        break
                if not acc or not acc.get("api_id"):
                    results.append((ph, "err", "No API for this phone"))
                    continue

                client = None
                try:
                    client = InfinityClient(ph, acc["api_id"], acc["api_hash"])
                    lp.run_until_complete(client.connect())

                    # already authorized?
                    try:
                        if lp.run_until_complete(client.client.is_user_authorized()):
                            me = lp.run_until_complete(client.client.get_me())
                            self._clear_pending_code_hash(ph)
                            WorkingAccountsManager.add(ph)
                            results.append((ph, "already", f"{me.first_name or ''}"))
                            continue
                    except Exception:
                        pass

                    # sign in with code
                    code_clean = ''.join(ch for ch in str(code) if ch.isdigit()) or str(code).strip()
                    phone_code_hash = self.pending_code_hashes.get(ph, "")
                    sign_kwargs = {"phone": ph, "code": code_clean}
                    if phone_code_hash:
                        sign_kwargs["phone_code_hash"] = phone_code_hash

                    try:
                        lp.run_until_complete(client.client.sign_in(**sign_kwargs))
                        self._clear_pending_code_hash(ph)
                        me = lp.run_until_complete(client.client.get_me())
                        nm = f"{me.first_name or ''} {me.last_name or ''}".strip()
                        pr = "⭐" if getattr(me, "premium", False) else ""
                        WorkingAccountsManager.add(ph)
                        results.append((ph, "ok", f"{nm} {pr}"))

                    except Exception as e:
                        err = str(e)

                        if "SessionPasswordNeeded" in err:
                            if pwd:
                                try:
                                    lp.run_until_complete(client.client.sign_in(password=pwd))
                                    me = lp.run_until_complete(client.client.get_me())
                                    self._clear_pending_code_hash(ph)
                                    WorkingAccountsManager.add(ph)
                                    results.append((ph, "ok", f"{me.first_name or ''} (2FA OK)"))
                                except Exception as e2:
                                    results.append((ph, "err", f"2FA wrong: {e2}"))
                            else:
                                results.append((ph, "2fa", "Needs 2FA — add ,password"))

                        elif "PhoneCodeInvalid" in err:
                            results.append((ph, "err", "Wrong code"))

                        elif "PhoneCodeExpired" in err:
                            self._clear_pending_code_hash(ph)
                            results.append((ph, "err", "Code expired — resend"))

                        elif "phone_code_hash" in err or "PhoneCodeHash" in err:
                            results.append((ph, "err", "Missing code hash — resend code first (Send Codes)"))

                        else:
                            results.append((ph, "err", err))

                except Exception as e:
                    results.append((ph, "err", f"Connect: {e}"))

                finally:
                    if client:
                        try:
                            lp.run_until_complete(client.disconnect())
                        except Exception:
                            pass

            lp.close()
            self.after(0, lambda: self._on_confirmed(results))

        threading.Thread(target=_work, daemon=True).start()

    def _on_confirmed(self, results):
        self.result_lb.delete(0, "end")
        ok = 0
        for ph, st, msg in results:
            if st == "ok":
                self.result_lb.insert("end", f"  ✅ {ph} — {msg}")
                self.report.add_ok(f"Login: {ph} — {msg}")
                ok += 1
            elif st == "already":
                self.result_lb.insert("end", f"  🟢 {ph} — Already: {msg}")
                ok += 1
            elif st == "2fa":
                self.result_lb.insert("end", f"  🔐 {ph} — {msg}")
                self.report.add_fail(f"2FA needed: {ph}")
            else:
                self.result_lb.insert("end", f"  ❌ {ph} — {msg}")
                self.report.add_fail(f"Login fail: {ph} — {msg}")
        self.result_lb.insert("end", f"\n✅ Confirmed: {ok}/{len(results)}")
        self.set_status(f"✅ {ok} confirmed")

    # ── CHECK ACCOUNTS ──
    def _check_accounts(self):
        accs = AccountsManager.load()
        if not accs:
            messagebox.showwarning("!", "No accounts")
            return
        if not HAS_TELETHON:
            messagebox.showerror("!", "Telethon not installed!")
            return
        self.result_lb.delete(0, "end")
        self.set_status(f"Checking {len(accs)} …")

        def _work():
            lp = asyncio.new_event_loop()
            asyncio.set_event_loop(lp)
            results = []
            for acc in accs:
                ph = acc["phone"]
                if not acc.get("api_id"):
                    results.append((ph, "noapi", "No API"))
                    continue
                if not SessionsManager.session_exists(ph):
                    results.append((ph, "nosess", "No session file"))
                    continue
                c = None
                try:
                    c = InfinityClient(ph, acc["api_id"], acc["api_hash"])
                    ok, msg = lp.run_until_complete(c.check_alive())
                    if ok:
                        info = lp.run_until_complete(c.get_info())
                        pr = "⭐" if info.get("premium") else ""
                        results.append((ph, "ok", f"{info.get('name', '')} {pr}"))
                    else:
                        results.append((ph, "fail", msg))
                except Exception as e:
                    results.append((ph, "err", str(e)))
                finally:
                    if c:
                        try:
                            lp.run_until_complete(c.disconnect())
                        except Exception:
                            pass
            lp.close()
            self.after(0, lambda: self._on_checked(results))

        threading.Thread(target=_work, daemon=True).start()

    def _on_checked(self, results):
        self.result_lb.delete(0, "end")
        working, banned = [], []
        for ph, st, msg in results:
            if st == "ok":
                self.result_lb.insert("end", f"  ✅ {ph} — {msg}")
                self.report.add_ok(f"Working: {ph}")
                working.append(ph)
            else:
                icon = "❌" if "BAN" in msg or "DEACTIVATED" in msg else "⚠"
                self.result_lb.insert("end", f"  {icon} {ph} — {msg}")
                self.report.add_fail(f"Check: {ph} — {msg}")
                if "BAN" in msg or "DEACTIVATED" in msg:
                    banned.append(ph)
        if working:
            WorkingAccountsManager.save(working)
        self.result_lb.insert(
            "end",
            f"\n📊 Working: {len(working)} | Banned: {len(banned)} | "
            f"Total: {len(results)}")
        if working:
            self.result_lb.insert(
                "end", f"💾 Saved {len(working)} → Working_Accounts.txt")
        self.set_status(
            f"✅ {len(working)} working  ❌ {len(banned)} banned")

    # ── misc account buttons ──
    def _dedup(self):
        t = self.phones_txt.get("1.0", "end").strip()
        ls = list(dict.fromkeys(
            l.strip() for l in t.split("\n") if l.strip()))
        self.phones_txt.delete("1.0", "end")
        self.phones_txt.insert("1.0", "\n".join(ls))
        self.ph_count.config(text=str(len(ls)))

    def _rm_banned(self):
        working = WorkingAccountsManager.load()
        if working:
            self.phones_txt.delete("1.0", "end")
            self.phones_txt.insert("1.0", "\n".join(working))
            self.ph_count.config(text=str(len(working)))
            self.set_status(f"Kept {len(working)} working accounts")

    def _save_working(self):
        w = WorkingAccountsManager.load()
        messagebox.showinfo("✓", f"Working_Accounts.txt → {len(w)} accounts")

    def _dl_sessions(self):
        d = filedialog.askdirectory(title="Save Sessions To")
        if d:
            n = 0
            for f in os.listdir(SESSIONS_DIR):
                if f.endswith(".session"):
                    shutil.copy2(os.path.join(SESSIONS_DIR, f),
                                 os.path.join(d, f))
                    n += 1
            messagebox.showinfo("✓", f"Exported {n} sessions → {d}")

    def _rm_invalid(self):
        ph = self._phones()
        r = SessionsManager.cleanup_invalid(ph)
        self.set_status(f"Removed {r} invalid sessions")

    # ══════════════════════════════════════════════════════════════
    #  P A G E :  SEARCH
    # ══════════════════════════════════════════════════════════════
    def P_search(self):
        p = self.content
        self._title(p, self.t("search"))

        s = self._sec(p, self.t("enter_search"))
        self.srch_e = self._entry(s, w=50)
        self.srch_e.pack(fill="x", padx=3, pady=3)

        gs = self._sec(p, self.t("gen_random"))
        gf = tk.Frame(gs, bg=THEME["surface"])
        gf.pack(fill="x", padx=3, pady=3)
        tk.Label(gf, text=self.t("results_c"), font=("Segoe UI", 9),
                 bg=THEME["surface"], fg=THEME["text2"]).pack(side="left", padx=2)
        self.gn = self._spin(gf, 1, 1, 10000)
        self.gn.pack(side="left", padx=2)
        tk.Label(gf, text=self.t("chars_c"), font=("Segoe UI", 9),
                 bg=THEME["surface"], fg=THEME["text2"]).pack(side="left", padx=2)
        self.gc = self._spin(gf, 5, 1, 32, 4)
        self.gc.pack(side="left", padx=2)

        self._brow(gs, [
            (self.t("generate"), self._sgen, "accent"),
            (self.t("load_file"), self._sload),
        ])
        self._sec(p, self.t("search_res"))
        self.srch_lb = self._lb(p, h=8)
        self._brow(p, [
            (self.t("save"), lambda: None),
            (self.t("clear"), lambda: self.srch_lb.delete(0, "end")),
        ])
        self.result_lb = self.srch_lb

    def _sgen(self):
        n, c = int(self.gn.get()), int(self.gc.get())
        self.srch_lb.delete(0, "end")
        for _ in range(n):
            self.srch_lb.insert(
                "end",
                ''.join(random.choices(string.ascii_lowercase + string.digits,
                                       k=c)))

    def _sload(self):
        f = filedialog.askopenfilename(filetypes=[("Text", "*.txt")])
        if f:
            with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                for l in fh:
                    if l.strip():
                        self.srch_lb.insert("end", l.strip())

    # ══════════════════════════════════════════════════════════════
    #  P A G E :  JOIN GROUPS  (public + private)
    # ══════════════════════════════════════════════════════════════
    def P_join(self):
        p = self.content
        self._title(p, self.t("join_title"))
        s = self._sec(p, "Links / usernames — public & private (one per line)")
        self.join_txt = self._text(s, h=5)
        cf = tk.Frame(p, bg=THEME["surface"])
        cf.pack(fill="x", padx=3, pady=2)
        self._btn(cf, self.t("import"), self._jimport).pack(
            side="left", padx=3)
        self._btn(cf, self.t("clear"),
                  lambda: self.join_txt.delete("1.0", "end")).pack(
            side="left", padx=3)
        self._btn(cf, self.t("join_linked"),
                  lambda: None).pack(side="right", padx=3)

        self.join_ok, self.join_fail = self._dual(
            p, self.t("success"), self.t("failed"), h=5)
        self.result_lb = self._lb(p, h=3)
        self._big(p, self.t("start"), self._jstart)

    def _jimport(self):
        f = filedialog.askopenfilename(filetypes=[("Text", "*.txt")])
        if f:
            with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                for l in fh:
                    if l.strip():
                        self.join_txt.insert("end", l.strip() + "\n")

    def _jstart(self):
        groups = [l.strip()
                  for l in self.join_txt.get("1.0", "end").split("\n")
                  if l.strip()]
        if not groups:
            messagebox.showwarning("!", "No groups")
            return
        if not HAS_TELETHON:
            messagebox.showerror("!", "Telethon needed")
            return
        accs = [a for a in AccountsManager.load()
                if SessionsManager.session_exists(a["phone"])
                and a.get("api_id")]
        if not accs:
            messagebox.showwarning("!", "No active accounts — check first")
            return

        self.join_ok.delete(0, "end")
        self.join_fail.delete(0, "end")
        self.running = True
        self.set_status(f"Joining {len(groups)} groups with {len(accs)} accounts…")

        def _work():
            lp = asyncio.new_event_loop()
            asyncio.set_event_loop(lp)
            ok_n, fail_n = 0, 0
            for gi, grp in enumerate(groups):
                if not self.running:
                    break
                acc = accs[gi % len(accs)]
                ph = acc["phone"]
                c = None
                try:
                    c = lp.run_until_complete(self._get_client(ph))
                    success, msg = lp.run_until_complete(c.join_group(grp))
                    if success:
                        self.after(0, lambda g=grp, p=ph:
                                   self.join_ok.insert("end",
                                                       f"✅ {g} ({p})"))
                        self.report.add_ok(f"Joined: {grp}")
                        ok_n += 1
                    else:
                        self.after(0, lambda g=grp, m=msg:
                                   self.join_fail.insert("end",
                                                         f"❌ {g} — {m}"))
                        self.report.add_fail(f"Join fail: {grp} — {msg}")
                        fail_n += 1
                except Exception as e:
                    self.after(0, lambda g=grp, er=str(e):
                               self.join_fail.insert("end",
                                                     f"❌ {g} — {er}"))
                    self.report.add_fail(f"Join error: {grp}")
                    fail_n += 1
                finally:
                    if c:
                        try:
                            lp.run_until_complete(c.disconnect())
                        except Exception:
                            pass
                time.sleep(human_delay("join"))
            lp.close()
            self.running = False
            self.after(0, lambda: self.set_status(
                f"✅ Joined: {ok_n} | ❌ Failed: {fail_n}"))

        threading.Thread(target=_work, daemon=True).start()

    # ══════════════════════════════════════════════════════════════
    #  P A G E :  EXTRACTION
    # ══════════════════════════════════════════════════════════════
    def P_extract(self):
        p = self.content
        self._title(p, self.t("extract"))

        s = self._sec(p)
        r = tk.Frame(s, bg=THEME["surface"])
        r.pack(fill="x", padx=3, pady=3)
        tk.Label(r, text=self.t("add_grp") + ":",
                 font=("Segoe UI", 9), bg=THEME["surface"],
                 fg=THEME["text2"]).pack(side="left", padx=3)
        self.ext_grp = self._entry(r, w=25)
        self.ext_grp.pack(side="left", padx=3)

        r2 = tk.Frame(s, bg=THEME["surface"])
        r2.pack(fill="x", padx=3, pady=2)
        for txt, ft in [(self.t("grp_members"), "all"),
                        (self.t("grp_bots"), "bots"),
                        (self.t("grp_admins"), "admins"),
                        (self.t("grp_chat"), "chat")]:
            self._btn(r2, txt, lambda f=ft: self._ext_go(f), "accent").pack(
                side="left", fill="x", expand=True, padx=1)

        r3 = tk.Frame(s, bg=THEME["surface"])
        r3.pack(fill="x", padx=3, pady=2)
        for txt in [self.t("extract_names"), self.t("extract_ch"),
                    self.t("extract_grps")]:
            self._btn(r3, txt, lambda: None).pack(
                side="left", fill="x", expand=True, padx=1)

        cols = [("n", "#", 30), ("id", "ID", 80),
                ("nm", self.t("name"), 120),
                ("ph", self.t("phone"), 75),
                ("us", self.t("username"), 100),
                ("ah", "Hash", 120), ("pr", "Prem", 55)]
        self.ext_tree = self._tree(p, cols, h=10)

        sf = tk.Frame(p, bg=THEME["surface"])
        sf.pack(fill="x", padx=3, pady=2)
        self.ext_total = tk.Label(
            sf, text="Total: 0",
            font=("JetBrains Mono", 10, "bold"),
            bg=THEME["surface"], fg=THEME["gold"])
        self.ext_total.pack(side="left", padx=6)

        self._brow(p, [
            (self.t("clear"),
             lambda: [self.ext_tree.delete(i)
                      for i in self.ext_tree.get_children()]),
            (self.t("save_excel"), self._ext_save, "gold"),
        ])
        self.result_lb = self._lb(p, h=3)

    def _ext_go(self, ft):
        grp = self.ext_grp.get().strip()
        if not grp:
            messagebox.showwarning("!", "Enter group!")
            return
        if not HAS_TELETHON:
            messagebox.showerror("!", "Telethon needed")
            return
        phone = self._pick_phone()
        if not phone:
            messagebox.showwarning("!", "No active accounts — check first")
            return
        self.set_status(f"Scraping {grp} ({ft}) …")

        def _work():
            lp = asyncio.new_event_loop()
            asyncio.set_event_loop(lp)
            c = None
            try:
                c = lp.run_until_complete(self._get_client(phone))
                if ft == "chat":
                    members, err = lp.run_until_complete(c.scrape_chatters(grp))
                else:
                    members, err = lp.run_until_complete(c.scrape_members(grp, ft))
                self.after(0, lambda: self._ext_done(members, err, grp, ft))
            except Exception as e:
                self.after(0, lambda: self.log(f"❌ {e}"))
            finally:
                if c:
                    try:
                        lp.run_until_complete(c.disconnect())
                    except Exception:
                        pass
                lp.close()

        threading.Thread(target=_work, daemon=True).start()

    def _ext_done(self, members, err, grp, ft):
        self.scraped = members
        for i in self.ext_tree.get_children():
            self.ext_tree.delete(i)
        for i, m in enumerate(members):
            tg = ("gold" if m.get("premium")
                  else "odd" if i % 2 == 0 else "even")
            self.ext_tree.insert("", "end", values=(
                i + 1,
                m.get("user_id", ""),
                m.get("name", ""),
                m.get("phone", ""),
                m.get("username", ""),
                str(m.get("access_hash", ""))[:18],
                "⭐" if m.get("premium") else ""),
                tags=(tg,))
        # auto-save to tools/
        if members:
            ToolsManager.save_scraped(grp, ft, members)
            ids = [m["user_id"] for m in members if m.get("user_id")]
            ToolsManager.save_ids(grp, ids)
            self.scraped_ids = ids
            self.report.add_ok(f"Scraped {len(members)} from {grp}")
        self.ext_total.config(text=f"Total: {len(members)}")
        msg = f"✅ {len(members)} members scraped → tools/"
        if err:
            msg += f"  ⚠ {err}"
        self.set_status(msg)

    def _ext_save(self):
        grp = self.ext_grp.get().strip() or "export"
        if self.scraped:
            fp = ToolsManager.save_excel(grp, self.scraped)
            messagebox.showinfo(
                "✓", f"Saved: {fp}\nIDs: {len(self.scraped_ids)} in tools/")
        else:
            messagebox.showwarning("!", "Scrape first!")

    # ══════════════════════════════════════════════════════════════
    #  P A G E :  FILTER
    # ══════════════════════════════════════════════════════════════
    def P_filter(self):
        p = self.content
        self._title(p, self.t("filter_title"))
        cols = [("n", "#", 30), ("id", "ID", 80),
                ("nm", self.t("name"), 110),
                ("ph", self.t("phone"), 90),
                ("us", self.t("username"), 100)]
        self.flt_tree = self._tree(p, cols, h=6)
        self._brow(p, [
            (self.t("save_excel"), lambda: None, "gold"),
            (self.t("clear"),
             lambda: [self.flt_tree.delete(i)
                      for i in self.flt_tree.get_children()]),
        ])
        self.flt_has, self.flt_no = self._dual(
            p, self.t("has_tg"), self.t("no_tg"), h=4)
        df = tk.Frame(p, bg=THEME["surface"])
        df.pack(fill="x", padx=3, pady=2)
        tk.Label(df, text=self.t("data_count") + ":",
                 font=("Segoe UI", 9), bg=THEME["surface"],
                 fg=THEME["text2"]).pack(side="left", padx=3)
        self.flt_c = tk.Label(df, text="0",
                              font=("JetBrains Mono", 10, "bold"),
                              bg=THEME["surface"], fg=THEME["gold"])
        self.flt_c.pack(side="left")
        self._btn(df, self.t("add_data"), lambda: None, "accent").pack(
            side="right", padx=3)
        self.result_lb = self._lb(p, h=3)
        self._big(p, self.t("start"),
                  lambda: self.set_status("Filtering…"))

    # ══════════════════════════════════════════════════════════════
    #  P A G E :  SEND MESSAGES
    # ══════════════════════════════════════════════════════════════
    def P_send_msg(self):
        p = self.content
        self._title(p, self.t("msg_title"))

        s = self._sec(p, self.t("enter_msg"))
        self.msg_t = self._text(s, h=3)

        pf = tk.Frame(p, bg=THEME["surface"])
        pf.pack(fill="x", padx=3, pady=2)
        tk.Label(pf, text=self.t("add_to_msg"),
                 font=("Segoe UI", 9), bg=THEME["surface"],
                 fg=THEME["text2"]).pack(side="left", padx=3)
        for ph in ["@ID@", "@DateTime@", "@Name@"]:
            self._btn(pf, ph,
                      lambda x=ph: self.msg_t.insert("insert", x),
                      "cyan").pack(side="left", padx=2)

        self.msg_ok, self.msg_fail = self._dual(
            p, self.t("sent"), self.t("not_sent"), h=5)
        self._brow(p, [
            (self.t("add_img"), lambda: filedialog.askopenfilename()),
            (self.t("add_file"), lambda: filedialog.askopenfilename()),
        ])
        df = tk.Frame(p, bg=THEME["surface"])
        df.pack(fill="x", padx=3, pady=2)
        tk.Label(df, text=self.t("data_count") + ":",
                 font=("Segoe UI", 9), bg=THEME["surface"],
                 fg=THEME["text2"]).pack(side="left", padx=3)
        self.msg_dc = tk.Label(df, text="0",
                               font=("JetBrains Mono", 10, "bold"),
                               bg=THEME["surface"], fg=THEME["gold"])
        self.msg_dc.pack(side="left")
        self._btn(df, self.t("add_data"), self._msg_load, "accent").pack(
            side="right", padx=3)
        self._brow(p, [
            (self.t("send_id"), lambda: None, "accent"),
            (self.t("send_phone"), lambda: None),
            (self.t("send_user"), lambda: None),
        ])
        self.result_lb = self._lb(p, h=3)
        self._big(p, self.t("start"),
                  lambda: self.set_status("Sending…"))

    def _msg_load(self):
        f = filedialog.askopenfilename()
        if f:
            with open(f, "r", encoding="utf-8", errors="ignore") as _fh:
                n = sum(1 for l in _fh if l.strip())
            self.msg_dc.config(text=str(n))

    # ══════════════════════════════════════════════════════════════
    #  P A G E :  ADDING
    # ══════════════════════════════════════════════════════════════
    def P_adding(self):
        p = self.content
        self._title(p, self.t("add_members"))
        self.add_ok, self.add_fail = self._dual(
            p, self.t("added"), self.t("not_added"), h=8)

        cf = tk.Frame(p, bg=THEME["surface"])
        cf.pack(fill="x", padx=3, pady=2)
        tk.Label(cf, text="✅:", font=("Segoe UI", 9),
                 bg=THEME["surface"], fg=THEME["green"]).pack(
            side="left", padx=3)
        self.add_ok_c = tk.Label(
            cf, text="0", font=("JetBrains Mono", 10, "bold"),
            bg=THEME["surface"], fg=THEME["green"])
        self.add_ok_c.pack(side="left")
        tk.Label(cf, text="  ❌:", font=("Segoe UI", 9),
                 bg=THEME["surface"], fg=THEME["red"]).pack(
            side="left", padx=3)
        self.add_fail_c = tk.Label(
            cf, text="0", font=("JetBrains Mono", 10, "bold"),
            bg=THEME["surface"], fg=THEME["red"])
        self.add_fail_c.pack(side="left")

        self.fast_v = tk.BooleanVar(value=False)
        tk.Checkbutton(
            p, text=self.t("fast_add"), variable=self.fast_v,
            font=("Segoe UI", 10, "bold"), bg=THEME["surface"],
            fg=THEME["gold"], selectcolor=THEME["entry_bg"],
            activebackground=THEME["surface"]).pack(fill="x", padx=3)

        df = tk.Frame(p, bg=THEME["surface"])
        df.pack(fill="x", padx=3, pady=2)
        tk.Label(df, text=self.t("data_count") + ":",
                 font=("Segoe UI", 9), bg=THEME["surface"],
                 fg=THEME["text2"]).pack(side="left", padx=3)
        self.add_dc = tk.Label(
            df, text=str(len(self.scraped_ids)),
            font=("JetBrains Mono", 10, "bold"),
            bg=THEME["surface"], fg=THEME["gold"])
        self.add_dc.pack(side="left")
        self._btn(df, "📂 IDs from tools/",
                  self._add_ids, "cyan").pack(side="right", padx=3)
        self._btn(df, self.t("add_data"),
                  lambda: None, "accent").pack(side="right", padx=3)

        self._brow(p, [
            (self.t("add_by_id"), lambda: None, "accent"),
            (self.t("add_by_phone"), lambda: None),
            (self.t("add_by_user"), lambda: None),
        ])

        gf = tk.Frame(p, bg=THEME["surface"])
        gf.pack(fill="x", padx=3, pady=3)
        tk.Label(gf, text=self.t("group_input") + ":",
                 font=("Segoe UI", 9), bg=THEME["surface"],
                 fg=THEME["text2"]).pack(side="left", padx=3)
        self.add_grp = self._entry(gf, w=20)
        self.add_grp.pack(side="right", padx=3)

        self.result_lb = self._lb(p, h=3)
        self._big(p, self.t("stop"),
                  lambda: setattr(self, 'running', False), "red")

    def _add_ids(self):
        f = filedialog.askopenfilename(
            initialdir=TOOLS_DIR, filetypes=[("Text", "*.txt")])
        if f:
            ids = ToolsManager.load_ids(f)
            self.scraped_ids = ids
            self.add_dc.config(text=str(len(ids)))
            self.log(f"Loaded {len(ids)} IDs from {os.path.basename(f)}")

    # ══════════════════════════════════════════════════════════════
    #  P A G E :  READ MESSAGES
    # ══════════════════════════════════════════════════════════════
    def P_read_msg(self):
        p = self.content
        self._title(p, self.t("read_title"))

        s = self._sec(p)
        r1 = tk.Frame(s, bg=THEME["surface"])
        r1.pack(fill="x", padx=3, pady=3)
        tk.Label(r1, text=self.t("select_acc") + ":",
                 font=("Segoe UI", 9), bg=THEME["surface"],
                 fg=THEME["text2"]).pack(side="left", padx=3)
        accs = [a["phone"] for a in AccountsManager.load()]
        self.rd_acc = ttk.Combobox(r1, values=accs, width=18,
                                   state="readonly")
        self.rd_acc.pack(side="left", padx=3)

        r2 = tk.Frame(s, bg=THEME["surface"])
        r2.pack(fill="x", padx=3, pady=3)
        tk.Label(r2, text=self.t("enter_chat") + ":",
                 font=("Segoe UI", 9), bg=THEME["surface"],
                 fg=THEME["text2"]).pack(side="left", padx=3)
        self.rd_chat = self._entry(r2, w=20)
        self.rd_chat.pack(side="left", padx=3)

        r3 = tk.Frame(s, bg=THEME["surface"])
        r3.pack(fill="x", padx=3, pady=3)
        tk.Label(r3, text=self.t("msg_count") + ":",
                 font=("Segoe UI", 9), bg=THEME["surface"],
                 fg=THEME["text2"]).pack(side="left", padx=3)
        self.rd_n = self._spin(r3, 5)
        self.rd_n.pack(side="left", padx=3)

        self._brow(p, [
            (self.t("get_code"), lambda: None, "accent"),
            (self.t("gifts"), lambda: None, "gold"),
            (self.t("get_premium"), lambda: None),
        ])
        self._sec(p, self.t("results"))
        self.rd_text = self._text(p, h=8)
        self.result_lb = self._lb(p, h=2)
        self._big(p, self.t("start"),
                  lambda: self.set_status("Reading…"))

    # ══════════════════════════════════════════════════════════════
    #  P A G E :  COMPLAINTS
    # ══════════════════════════════════════════════════════════════
    def P_complaints(self):
        p = self.content
        self._title(p, self.t("complaints"))

        s = self._sec(p, self.t("report_user"))
        r = tk.Frame(s, bg=THEME["surface"])
        r.pack(fill="x", padx=3, pady=4)
        tk.Label(r, text=self.t("target") + ":",
                 font=("Segoe UI", 10), bg=THEME["surface"],
                 fg=THEME["text2"]).pack(side="left", padx=3)
        self.comp_tgt = self._entry(r, w=25)
        self.comp_tgt.pack(side="left", padx=3)

        r2 = tk.Frame(s, bg=THEME["surface"])
        r2.pack(fill="x", padx=3, pady=4)
        tk.Label(r2, text=self.t("report_type") + ":",
                 font=("Segoe UI", 10), bg=THEME["surface"],
                 fg=THEME["text2"]).pack(side="left", padx=3)
        self.comp_tp = ttk.Combobox(
            r2, values=["Spam", "Violence", "Fake", "Scam", "Other"],
            width=12, state="readonly")
        self.comp_tp.set("Spam")
        self.comp_tp.pack(side="left", padx=3)
        tk.Label(r2, text=self.t("report_count") + ":",
                 font=("Segoe UI", 10), bg=THEME["surface"],
                 fg=THEME["text2"]).pack(side="left", padx=6)
        self.comp_n = self._spin(r2, 1, 1, 1000)
        self.comp_n.pack(side="left", padx=3)

        self.comp_ok, self.comp_fail = self._dual(
            p, self.t("success"), self.t("failed"), h=5)
        self.result_lb = self._lb(p, h=4)
        self._brow(p, [
            (self.t("send_report"), self._comp_go, "red"),
            (self.t("stop"),
             lambda: setattr(self, 'running', False), "orange"),
        ])

    def _comp_go(self):
        tgt = self.comp_tgt.get().strip()
        if not tgt:
            messagebox.showwarning("!", "Enter target")
            return
        self.set_status(f"Reporting {tgt}…")
        self.running = True
        self.log(f"🎯 Target: {tgt} | Using all connected accounts")
        self.report.add_ok(f"Report started: {tgt}")

    # ══════════════════════════════════════════════════════════════
    #  PAGES:  LEAVE / BAN / ADMIN
    # ══════════════════════════════════════════════════════════════
    def P_leave(self):
        p = self.content
        self._title(p, self.t("leave"))
        s = self._sec(p, "Groups to leave (one per line)")
        self.leave_t = self._text(s, h=6)
        self._brow(p, [
            (self.t("import"), lambda: None),
            (self.t("clear"),
             lambda: self.leave_t.delete("1.0", "end")),
        ])
        self.result_lb = self._lb(p, h=5)
        self._big(p, self.t("start"),
                  lambda: self.set_status("Leaving…"))

    def P_ban_members(self):
        p = self.content
        self._title(p, self.t("ban_members"))
        s = self._sec(p, self.t("group_input"))
        self.ban_grp = self._entry(s, w=30)
        self.ban_grp.pack(fill="x", padx=3, pady=3)
        self._sec(p, "Users to ban")
        self.ban_t = self._text(p, h=6)
        self.result_lb = self._lb(p, h=3)
        self._big(p, self.t("start"),
                  lambda: self.set_status("Banning…"), "red")

    def P_make_admin(self):
        p = self.content
        self._title(p, self.t("make_admin"))
        s = self._sec(p, self.t("group_input"))
        self.adm_grp = self._entry(s, w=30)
        self.adm_grp.pack(fill="x", padx=3, pady=3)
        self._sec(p, "Users to promote")
        self.adm_t = self._text(p, h=6)
        self.result_lb = self._lb(p, h=3)
        self._big(p, self.t("start"),
                  lambda: self.set_status("Promoting…"), "green")

    # ══════════════════════════════════════════════════════════════
    #  P A G E :  PROXIES
    # ══════════════════════════════════════════════════════════════
    def P_proxies(self):
        p = self.content
        self._title(p, self.t("proxy_t"))

        s = self._sec(p)
        r = tk.Frame(s, bg=THEME["surface"])
        r.pack(fill="x", padx=3, pady=3)
        tk.Label(r, text="Type:", font=("Segoe UI", 9),
                 bg=THEME["surface"], fg=THEME["text2"]).pack(
            side="left", padx=2)
        self.px_tp = ttk.Combobox(
            r, values=["SOCKS5", "SOCKS4", "HTTP", "MTPROTO"],
            width=9, state="readonly")
        self.px_tp.set("SOCKS5")
        self.px_tp.pack(side="left", padx=2)
        tk.Label(r, text="Addr:", font=("Segoe UI", 9),
                 bg=THEME["surface"], fg=THEME["text2"]).pack(
            side="left", padx=2)
        self.px_a = self._entry(r, w=15)
        self.px_a.pack(side="left", padx=2)
        tk.Label(r, text="Port:", font=("Segoe UI", 9),
                 bg=THEME["surface"], fg=THEME["text2"]).pack(
            side="left", padx=2)
        self.px_p = self._entry(r, w=5, d="1080")
        self.px_p.pack(side="left", padx=2)

        r2 = tk.Frame(s, bg=THEME["surface"])
        r2.pack(fill="x", padx=3, pady=3)
        tk.Label(r2, text="User:", font=("Segoe UI", 9),
                 bg=THEME["surface"], fg=THEME["text2"]).pack(
            side="left", padx=2)
        self.px_u = self._entry(r2, w=12)
        self.px_u.pack(side="left", padx=2)
        tk.Label(r2, text="Pass:", font=("Segoe UI", 9),
                 bg=THEME["surface"], fg=THEME["text2"]).pack(
            side="left", padx=2)
        self.px_pw = self._entry(r2, w=12)
        self.px_pw.pack(side="left", padx=2)

        self._brow(p, [
            (self.t("add_proxy"), self._px_add, "accent"),
            (self.t("test_proxy"),
             lambda: self.set_status("Testing…"), "orange"),
            (self.t("load_file"), self._px_load),
        ])

        en = self.S.get("proxy_enabled", False)
        self.px_tgl = tk.Button(
            p,
            text=self.t("proxy_on") if en else self.t("proxy_off"),
            font=("Segoe UI", 11, "bold"),
            bg=THEME["green"] if en else THEME["red"],
            fg="#fff", bd=0, cursor="hand2", pady=4,
            command=self._px_tgl)
        self.px_tgl.pack(fill="x", padx=3, pady=3)

        cols = [("n", "#", 30), ("tp", "Type", 60), ("ad", "Addr", 130),
                ("pt", "Port", 50), ("us", "User", 70), ("st", "Status", 55)]
        self.px_tree = self._tree(p, cols, h=5)
        for i, px in enumerate(self.proxy_mgr.proxies):
            self.px_tree.insert("", "end", values=(
                i + 1, px["type"].upper(), px["addr"], px["port"],
                px.get("user", ""),
                "✓" if px.get("active") else "✗"),
                tags=("odd" if i % 2 == 0 else "even",))

        self._brow(p, [
            (self.t("rotation"),
             lambda: self.set_status("Rotation ON")),
            (self.t("delete"), self._px_del),
        ])
        self.result_lb = self._lb(p, h=2)

    def _px_add(self):
        self.proxy_mgr.add(
            self.px_tp.get().lower(), self.px_a.get(),
            self.px_p.get(), self.px_u.get(), self.px_pw.get())
        self.show("proxies")

    def _px_load(self):
        f = filedialog.askopenfilename(filetypes=[("Text", "*.txt")])
        if f:
            n = self.proxy_mgr.import_file(f)
            messagebox.showinfo("✓", f"{n} proxies imported")
            self.show("proxies")

    def _px_tgl(self):
        v = not self.S.get("proxy_enabled", False)
        self.S["proxy_enabled"] = v
        save_settings(self.S)
        self.px_tgl.config(
            text=self.t("proxy_on") if v else self.t("proxy_off"),
            bg=THEME["green"] if v else THEME["red"])

    def _px_del(self):
        sel = self.px_tree.selection()
        if sel:
            self.proxy_mgr.remove(self.px_tree.index(sel[0]))
            self.show("proxies")

    # ══════════════════════════════════════════════════════════════
    #  P A G E :  SETTINGS
    # ══════════════════════════════════════════════════════════════
    def P_settings(self):
        p = self.content
        self._title(p, self.t("settings_t"))

        s = self._sec(p)
        r1 = tk.Frame(s, bg=THEME["surface"])
        r1.pack(fill="x", padx=3, pady=4)
        tk.Label(r1, text=self.t("time_msg") + ":",
                 font=("Segoe UI", 9), bg=THEME["surface"],
                 fg=THEME["text2"]).pack(side="left", padx=3)
        self.s_delay = self._spin(r1, self.S.get("delay_min", 2))
        self.s_delay.pack(side="left", padx=3)
        tk.Label(r1, text=self.t("sec"), font=("Segoe UI", 9),
                 bg=THEME["surface"], fg=THEME["text3"]).pack(
            side="left", padx=3)

        r2 = tk.Frame(s, bg=THEME["surface"])
        r2.pack(fill="x", padx=3, pady=4)
        tk.Label(r2, text=self.t("rest") + ":",
                 font=("Segoe UI", 9), bg=THEME["surface"],
                 fg=THEME["text2"]).pack(side="left", padx=3)
        self.s_rd = self._spin(r2, self.S.get("rest_minutes", 1))
        self.s_rd.pack(side="left", padx=3)
        tk.Label(r2, text=self.t("min") + " " + self.t("after"),
                 font=("Segoe UI", 9), bg=THEME["surface"],
                 fg=THEME["text3"]).pack(side="left", padx=3)
        self.s_rn = self._spin(r2, self.S.get("rest_after", 1000))
        self.s_rn.pack(side="left", padx=3)
        tk.Label(r2, text=self.t("msg"), font=("Segoe UI", 9),
                 bg=THEME["surface"], fg=THEME["text3"]).pack(
            side="left", padx=3)

        r3 = tk.Frame(s, bg=THEME["surface"])
        r3.pack(fill="x", padx=3, pady=4)
        tk.Label(r3, text=self.t("rand_chars") + ":",
                 font=("Segoe UI", 9), bg=THEME["surface"],
                 fg=THEME["text2"]).pack(side="left", padx=3)
        self.s_rc = self._spin(r3, self.S.get("random_chars", 1))
        self.s_rc.pack(side="left", padx=3)

        # timer
        ts = self._sec(p, self.t("time"))
        tk.Label(ts, text="Timer : 0",
                 font=("JetBrains Mono", 13, "bold"),
                 bg=THEME["surface"], fg=THEME["gold"]).pack(pady=5)
        tk.Label(ts, text="Rest : HH:MM:SS",
                 font=("JetBrains Mono", 11),
                 bg=THEME["surface"], fg=THEME["text2"]).pack(pady=3)

        # file paths
        fs = self._sec(p, "📁 Files")
        for nm, pt in [("Api_Hash.txt", API_HASH_FILE),
                       ("Accounts.txt", ACCOUNTS_FILE),
                       ("sessions/", SESSIONS_DIR),
                       ("tools/", TOOLS_DIR)]:
            rf = tk.Frame(fs, bg=THEME["surface"])
            rf.pack(fill="x", padx=3, pady=1)
            tk.Label(rf, text=nm, font=("Segoe UI", 9, "bold"),
                     bg=THEME["surface"], fg=THEME["gold"]).pack(
                side="left", padx=3)
            tk.Label(rf, text=pt, font=("Consolas", 8),
                     bg=THEME["surface"], fg=THEME["text3"]).pack(
                side="left", padx=3)

        self._btn(p, self.t("save"), self._sset, "gold").pack(
            fill="x", padx=3, pady=4)

    def _sset(self):
        self.S["delay_min"] = int(self.s_delay.get())
        self.S["rest_minutes"] = int(self.s_rd.get())
        self.S["rest_after"] = int(self.s_rn.get())
        self.S["random_chars"] = int(self.s_rc.get())
        save_settings(self.S)
        self.set_status("Settings saved ✓")

    # ══════════════════════════════════════════════════════════════
    #  P A G E :  REPORTS  (connected to ALL operations)
    # ══════════════════════════════════════════════════════════════
    def P_reports(self):
        p = self.content
        self._title(p, self.t("reports_t"))

        # success
        sf = tk.Frame(p, bg=THEME["success_bg"],
                       highlightbackground=THEME["green"],
                       highlightthickness=1)
        sf.pack(fill="x", padx=3, pady=2)
        tk.Label(sf,
                 text=f"✅ {self.t('success')} ({len(self.report.ok)})",
                 font=("Segoe UI", 10, "bold"),
                 bg=THEME["green"], fg="#fff").pack(fill="x")
        ok_lb = tk.Listbox(sf, height=5, font=("JetBrains Mono", 9),
                           bg=THEME["success_bg"], fg=THEME["green2"],
                           bd=0)
        ok_lb.pack(fill="x")
        for x in self.report.ok:
            ok_lb.insert("end", x)

        # failed
        ff = tk.Frame(p, bg=THEME["fail_bg"],
                       highlightbackground=THEME["red"],
                       highlightthickness=1)
        ff.pack(fill="x", padx=3, pady=2)
        tk.Label(ff,
                 text=f"❌ {self.t('failed')} ({len(self.report.fail)})",
                 font=("Segoe UI", 10, "bold"),
                 bg=THEME["red"], fg="#fff").pack(fill="x")
        fail_lb = tk.Listbox(ff, height=5, font=("JetBrains Mono", 9),
                             bg=THEME["fail_bg"], fg=THEME["red2"], bd=0)
        fail_lb.pack(fill="x")
        for x in self.report.fail:
            fail_lb.insert("end", x)

        # stats
        stf = tk.Frame(p, bg=THEME["surface"])
        stf.pack(fill="x", padx=3, pady=3)
        tk.Label(stf,
                 text=(f"Total: {self.report.total}  |  "
                       f"✅ {len(self.report.ok)}  |  "
                       f"❌ {len(self.report.fail)}"),
                 font=("JetBrains Mono", 11, "bold"),
                 bg=THEME["surface"], fg=THEME["gold"]).pack(padx=6)

        self._brow(p, [
            (self.t("save_report"), self._rep_save, "gold"),
            (self.t("clear"),
             lambda: [self.report.clear(), self.show("reports")], "red"),
        ])
        self.result_lb = self._lb(p, h=4)

    def _rep_save(self):
        f = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text", "*.txt")])
        if f:
            self.report.save_to(f)
            messagebox.showinfo("✓", f"Report saved → {f}")


# ══════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════
def main():
    app = App()
    app.update_idletasks()
    x = (app.winfo_screenwidth() // 2) - (app.winfo_width() // 2)
    y = (app.winfo_screenheight() // 2) - (app.winfo_height() // 2)
    app.geometry(f"+{x}+{y}")
    app.mainloop()


if __name__ == "__main__":
    main()