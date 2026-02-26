"""
Infinity Telegram V1.0 - Configuration & Theme
Cyber Black Luxury Edition
"""
import os, json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")
TOOLS_DIR = os.path.join(BASE_DIR, "tools")
DATA_DIR = os.path.join(BASE_DIR, "data")

# External files
API_HASH_FILE = os.path.join(BASE_DIR, "Api_Hash.txt")
ACCOUNTS_FILE = os.path.join(BASE_DIR, "Accounts.txt")
WORKING_ACCOUNTS_FILE = os.path.join(BASE_DIR, "Working_Accounts.txt")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
PROXIES_FILE = os.path.join(DATA_DIR, "proxy_list.json")

for d in [SESSIONS_DIR, TOOLS_DIR, DATA_DIR]:
    os.makedirs(d, exist_ok=True)

# ─── Luxury Dark Theme ───
THEME = {
    "bg":           "#0a0a0f",
    "bg2":          "#101018",
    "bg3":          "#161622",
    "surface":      "#1a1a2e",
    "surface2":     "#1e1e34",
    "border":       "#2a2a44",
    "border_glow":  "#6c3ce0",
    "accent":       "#7c3aed",
    "accent2":      "#a855f7",
    "accent3":      "#c084fc",
    "gold":         "#f5c842",
    "gold2":        "#fbbf24",
    "cyan":         "#22d3ee",
    "green":        "#10b981",
    "green2":       "#34d399",
    "red":          "#ef4444",
    "red2":         "#f87171",
    "orange":       "#f97316",
    "white":        "#f8fafc",
    "text":         "#e2e8f0",
    "text2":        "#94a3b8",
    "text3":        "#64748b",
    "entry_bg":     "#12121e",
    "entry_border": "#2d2d4a",
    "btn_bg":       "#1e1e36",
    "btn_hover":    "#2a2a4e",
    "table_h":      "#14142a",
    "table_r1":     "#111120",
    "table_r2":     "#0e0e1a",
    "success_bg":   "#0a1f0a",
    "fail_bg":      "#1f0a0a",
}

DEFAULT_SETTINGS = {
    "delay_min": 2, "delay_max": 8,
    "rest_after": 1000, "rest_minutes": 1,
    "random_chars": 1, "language": "ar",
    "proxy_enabled": False,
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            s = DEFAULT_SETTINGS.copy(); s.update(json.load(f)); return s
    return DEFAULT_SETTINGS.copy()

def save_settings(s):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2, ensure_ascii=False)

# ─── Translations ───
TR = {
 "ar": {
    "title":"Infinity Telegram V1.0 — Cyber Black Luxury","main_menu":"القائمة الرئيسية",
    "accounts":"الأكونتات","codes":"الأكواد","search":"البحث","join":"إنضمام للجروبات",
    "extract":"الإستخراج","filter":"الفلترة","send_msg":"إرسال رسائل","adding":"الإضافة",
    "read_msg":"قراءة الرسائل","settings":"الإعدادات","reports":"التقارير","proxies":"البروكسيات",
    "complaints":"البلاغات","leave":"مغادرة الجروبات","ban_members":"حظر الأعضاء",
    "make_admin":"عمل إضافة أدمن","views":"المشاهدات والتفاعلات","lang":"اللغة",
    "arabic":"العربية","english":"الإنجليزية","start":"إبدأ","stop":"توقف",
    "save":"حفظ","clear":"مسح","delete":"إزالة","count":"العدد","total":"الكل",
    "phone":"الهاتف","name":"الإسم","username":"اليوزرنيم","status":"الحالة",
    "premium":"بريميوم","add_data":"إضافة داتا","data_count":"عدد الداتا",
    "add_by_user":"إضافة باليوزرنيم","add_by_phone":"إضافة بالهاتف","add_by_id":"إضافة بالأيدي",
    "group_input":"يوزر أو أيدي الجروب","fast_add":"الإضافة السريعة",
    "added":"تمت إضافته","not_added":"لم تتم إضافته","add_members":"إضافة الأعضاء",
    "send_codes":"أرسل الأكواد","confirm_codes":"تأكيد الأكواد","clear_all":"مسح الكل",
    "remove_dup":"إزالة المكرر","check_banned":"تفقد الأرقام المحظورة",
    "remove_banned":"إزالة المحظورة","download_sess":"تحميل السيشنات",
    "remove_invalid":"إزالة السيشنات التالفة","logout_devices":"خروج من الأجهزة",
    "set_pass":"عمل باسوورد","send_email":"إرسال أكواد الإيميل",
    "confirm_email":"تأكيد أكواد الإيميل","lines":"عدد السطور",
    "instructions":"إضغط هنا لمشاهدة التعليمات","enter_num":"أدخل الرقم",
    "login_num":"تسجيل دخول الرقم","extract_grp":"إستخراج الجروب",
    "add_grp":"أضف الجروب","grp_members":"أعضاء الجروب","grp_bots":"بوتات الجروب",
    "grp_admins":"أدمن الجروب","grp_chat":"مراسلين الجروب","extract_names":"إستخراج أسماء",
    "extract_ch":"إستخراج قنواتي","extract_grps":"إستخراج جروباتي",
    "extract_all":"إستخراج جميع الأيديهات بدقة عالية","extract_chatters":"إستخراج أيديهات المراسلين",
    "extract_only":"إستخراج فقط","save_excel":"حفظ ملف إكسل","phones_c":"الهواتف",
    "users_c":"اليوزرات","acc_name":"إسم الأكونت","enter_search":"أدخل ما تبحث عنه",
    "gen_random":"توليد يوزرات عشوائية","results_c":"عدد النتائج","chars_c":"عدد الحروف",
    "generate":"توليد","calc":"حساب النتيجة","load_file":"إستدعاء من ملف",
    "load":"إستدعاء","search_res":"نتائج البحث","groups":"الجروبات","channels":"القنوات",
    "ended":"إنتهى","divide":"تقسيم ب","join_title":"الإنضمام للجروبات",
    "import":"إستيراد","join_linked":"الإنضمام للجروب المربوط بالقناة",
    "filter_title":"بيانات الأرقام","has_tg":"لديه تليجرام","no_tg":"ليس لديه تليجرام",
    "total_c":"العدد الكلي","user_c":"عدد اليوزر","msg_title":"الرسالة",
    "enter_msg":"أدخل نص الرسالة هنا","add_to_msg":">> أضف إلى رسالتك",
    "sent":"تم الإرسال","not_sent":"لم يتم الإرسال","add_img":"إضافة صورة",
    "add_file":"إضافة ملف","send_user":"الإرسال باليوزرنيم","send_phone":"الإرسال بالهاتف",
    "send_id":"الإرسال بال Id","read_title":"قراءة الرسائل","select_acc":"إختر أكونتك",
    "enter_chat":"أدخل أيدي الشات","msg_count":"عدد الرسائل","get_code":"الحصول على الكود",
    "gifts":"إستخرج الهدايا","get_premium":"حساباتي البريميوم","results":"النتائج",
    "settings_t":"الإعدادات","time_msg":"الوقت بين كل رسالة","sec":"ثانية","msg":"رسالة",
    "rest":"راحة لـ","after":"بعد","min":"دقيقة","rand_chars":"حروف النص العشوائي",
    "char":"حرف","time":"الوقت","end_set":"نهاية الإعدادات","reports_t":"التقارير",
    "success":"ناجح","failed":"فاشل","total_sent":"كل ما تم إرساله",
    "total_nsent":"كل ما لم يتم إرساله","remaining":"المتبقي","save_report":"حفظ التقرير",
    "proxy_t":"إدارة البروكسيات","proxy_type":"نوع البروكسي","proxy_addr":"العنوان",
    "proxy_port":"المنفذ","proxy_user":"المستخدم","proxy_pass":"كلمة المرور",
    "add_proxy":"إضافة بروكسي","test_proxy":"فحص البروكسي","proxy_on":"البروكسيات مفعلة",
    "proxy_off":"البروكسيات معطلة","rotation":"تدوير البروكسي",
    "access_hash":"Access Hash","id":"ID","num":"#",
    "enter_phones":"أدخل الأرقام هنا (رقم في كل سطر)","enter_code_for":"أدخل الكود لـ",
    "code":"الكود","verify":"تحقق","working":"يعمل","not_working":"لا يعمل",
    "check_all":"تفقد الكل","report_user":"الإبلاغ عن مستخدم","report_spam":"بلاغ سبام",
    "report_count":"عدد البلاغات","target":"الهدف","report_type":"نوع البلاغ",
    "send_report":"إرسال البلاغ","infinity":"∞","loading":"جاري التحميل...",
    "connected":"متصل","disconnected":"غير متصل","checking":"جاري الفحص...",
    "api_loaded":"تم تحميل API","no_api":"لا يوجد ملف API","acc_loaded":"تم تحميل الأكونتات",
    "save_working":"حفظ الشغالين","total_accounts":"إجمالي الأكونتات",
    "working_accounts":"الأكونتات الشغالة","banned_accounts":"الأكونتات المحظورة",
 },
 "en": {
    "title":"Infinity Telegram V1.0 — Cyber Black Luxury","main_menu":"Main Menu",
    "accounts":"Accounts","codes":"Codes","search":"Search","join":"Join Groups",
    "extract":"Extract","filter":"Filter","send_msg":"Send Messages","adding":"Adding",
    "read_msg":"Read Messages","settings":"Settings","reports":"Reports","proxies":"Proxies",
    "complaints":"Complaints","leave":"Leave Groups","ban_members":"Ban Members",
    "make_admin":"Make Admin","views":"Views & Reactions","lang":"Language",
    "arabic":"Arabic","english":"English","start":"Start","stop":"Stop",
    "save":"Save","clear":"Clear","delete":"Remove","count":"Count","total":"Total",
    "phone":"Phone","name":"Name","username":"Username","status":"Status",
    "premium":"Premium","add_data":"Add Data","data_count":"Data Count",
    "add_by_user":"Add by Username","add_by_phone":"Add by Phone","add_by_id":"Add by ID",
    "group_input":"Group username or ID","fast_add":"Fast Add",
    "added":"Added","not_added":"Not Added","add_members":"Add Members",
    "send_codes":"Send Codes","confirm_codes":"Confirm Codes","clear_all":"Clear All",
    "remove_dup":"Remove Duplicates","check_banned":"Check Banned",
    "remove_banned":"Remove Banned","download_sess":"Download Sessions",
    "remove_invalid":"Remove Invalid","logout_devices":"Logout Devices",
    "set_pass":"Set Passwords","send_email":"Send Email Codes",
    "confirm_email":"Confirm Email Codes","lines":"Lines",
    "instructions":"Click for instructions","enter_num":"Enter Number",
    "login_num":"Login Number","extract_grp":"Extract Group",
    "add_grp":"Add Group","grp_members":"Group Members","grp_bots":"Group Bots",
    "grp_admins":"Group Admins","grp_chat":"Chat Members","extract_names":"Extract Names",
    "extract_ch":"My Channels","extract_grps":"My Groups",
    "extract_all":"Extract all IDs (high accuracy)","extract_chatters":"Extract Chatter IDs",
    "extract_only":"Extract Only","save_excel":"Save Excel","phones_c":"Phones",
    "users_c":"Usernames","acc_name":"Account Name","enter_search":"Enter search query",
    "gen_random":"Generate random usernames","results_c":"Results","chars_c":"Characters",
    "generate":"Generate","calc":"Calculate","load_file":"Load from File",
    "load":"Load","search_res":"Search Results","groups":"Groups","channels":"Channels",
    "ended":"Ended","divide":"Divide by","join_title":"Join Groups",
    "import":"Import","join_linked":"Join linked group",
    "filter_title":"Phone Number Data","has_tg":"Has Telegram","no_tg":"No Telegram",
    "total_c":"Total Count","user_c":"Username Count","msg_title":"Message",
    "enter_msg":"Enter message text here","add_to_msg":">> Add to message",
    "sent":"Sent","not_sent":"Not Sent","add_img":"Add Image",
    "add_file":"Add File","send_user":"Send by Username","send_phone":"Send by Phone",
    "send_id":"Send by ID","read_title":"Read Messages","select_acc":"Select Account",
    "enter_chat":"Enter Chat ID","msg_count":"Message Count","get_code":"Get Code",
    "gifts":"Extract Gifts","get_premium":"Premium Accounts","results":"Results",
    "settings_t":"Settings","time_msg":"Time between messages","sec":"seconds","msg":"messages",
    "rest":"Rest for","after":"after","min":"minutes","rand_chars":"Random text chars",
    "char":"chars","time":"Time","end_set":"End of Settings","reports_t":"Reports",
    "success":"Success","failed":"Failed","total_sent":"Total Sent",
    "total_nsent":"Total Not Sent","remaining":"Remaining","save_report":"Save Report",
    "proxy_t":"Proxy Management","proxy_type":"Type","proxy_addr":"Address",
    "proxy_port":"Port","proxy_user":"Username","proxy_pass":"Password",
    "add_proxy":"Add Proxy","test_proxy":"Test Proxy","proxy_on":"Proxies ON",
    "proxy_off":"Proxies OFF","rotation":"Rotation",
    "access_hash":"Access Hash","id":"ID","num":"#",
    "enter_phones":"Enter phone numbers (one per line)","enter_code_for":"Enter code for",
    "code":"Code","verify":"Verify","working":"Working","not_working":"Not Working",
    "check_all":"Check All","report_user":"Report User","report_spam":"Spam Report",
    "report_count":"Report Count","target":"Target","report_type":"Report Type",
    "send_report":"Send Report","infinity":"∞","loading":"Loading...",
    "connected":"Connected","disconnected":"Disconnected","checking":"Checking...",
    "api_loaded":"API Loaded","no_api":"No API file","acc_loaded":"Accounts Loaded",
    "save_working":"Save Working","total_accounts":"Total Accounts",
    "working_accounts":"Working Accounts","banned_accounts":"Banned Accounts",
 }
}
