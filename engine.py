"""
Infinity Telegram V1.0 - Telegram Client Engine
Real functional wrapper around Telethon
"""
import asyncio, os, random, time
from urllib.parse import urlparse
from config import SESSIONS_DIR
from antiban import device_for_phone, human_delay

try:
    from telethon import TelegramClient, errors
    from telethon.tl.functions.channels import (
        GetParticipantsRequest, JoinChannelRequest, LeaveChannelRequest,
        InviteToChannelRequest, GetFullChannelRequest)
    from telethon.tl.functions.messages import (
        GetHistoryRequest, ImportChatInviteRequest, ReportRequest)
    from telethon.tl.functions.contacts import (
        ResolveUsernameRequest, ImportContactsRequest)
    from telethon.tl.functions.account import (
        GetAuthorizationsRequest, ResetAuthorizationRequest)
    from telethon.tl.types import (
        ChannelParticipantsSearch, ChannelParticipantsRecent,
        ChannelParticipantsAdmins, ChannelParticipantsBots,
        InputPhoneContact, InputPeerUser, InputReportReasonSpam,
        InputReportReasonViolence, InputReportReasonOther,
        UserStatusOnline, UserStatusRecently)
    HAS_TELETHON = True
except ImportError:
    HAS_TELETHON = False

# Session lock to prevent concurrent access to the same SQLite session file
_SESSION_LOCKS = {}

def _lock_for(phone: str) -> asyncio.Lock:
    key = phone.replace("+", "").strip()
    lock = _SESSION_LOCKS.get(key)
    if lock is None:
        lock = asyncio.Lock()
        _SESSION_LOCKS[key] = lock
    return lock

def _normalize_link(link: str) -> str:
    s = (link or "").strip()
    # remove spaces and trailing slashes
    s = s.replace(" ", "").rstrip("/")
    # handle raw +HASH
    if s.startswith("+"):
        return s
    # handle t.me links
    if "t.me/" in s:
        # strip schema
        if s.startswith("http://") or s.startswith("https://"):
            p = urlparse(s)
            s = (p.path or "").lstrip("/")
        else:
            s = s.split("t.me/", 1)[1]
    # drop query params like ?start=...
    s = s.split("?", 1)[0]
    return s


class InfinityClient:
    """Full-featured Telegram client with anti-ban."""

    def __init__(self, phone, api_id, api_hash, proxy=None):
        self.phone = phone
        self.api_id = int(api_id)
        self.api_hash = api_hash
        self.proxy = proxy
        self.client = None
        self.connected = False
        self.me = None

    async def connect(self):
        if not HAS_TELETHON:
            raise ImportError("telethon not installed")

        async with _lock_for(self.phone):
            if self.client and self.connected:
                return

            dev = device_for_phone(self.phone)
            kw = {
                "session": os.path.join(SESSIONS_DIR, self.phone.replace("+", "")),
                "api_id": self.api_id,
                "api_hash": self.api_hash,
                "device_model": dev["device_model"],
                "system_version": dev["system_version"],
                "app_version": dev["app_version"],
                "lang_code": dev["lang_code"],
            }
            if self.proxy:
                kw["proxy"] = self.proxy

            self.client = TelegramClient(**kw)
            await self.client.connect()
            self.connected = True

    async def login(self, code_cb=None, pass_cb=None):
        async with _lock_for(self.phone):
            if not self.client:
                await self.connect()

            if not await self.client.is_user_authorized():
                sent = await self.client.send_code_request(self.phone)
                code = await code_cb() if code_cb else input(f"Code for {self.phone}: ")
                code_clean = ''.join(ch for ch in str(code) if ch.isdigit()) or str(code).strip()
                try:
                    await self.client.sign_in(
                        phone=self.phone,
                        code=code_clean,
                        phone_code_hash=getattr(sent, "phone_code_hash", None)
                    )
                except errors.SessionPasswordNeededError:
                    pw = await pass_cb() if pass_cb else input("2FA: ")
                    await self.client.sign_in(password=pw)

            self.me = await self.client.get_me()
            return self.me

    async def check_alive(self):
        """Check if account is alive/working."""
        try:
            if not self.client:
                await self.connect()
            if await self.client.is_user_authorized():
                self.me = await self.client.get_me()
                return True, "working"
            return False, "not_authorized"
        except errors.AuthKeyDuplicatedError:
            return False, "AUTH_KEY_DUPLICATED"
        except errors.UserDeactivatedBanError:
            return False, "USER_DEACTIVATED_BAN"
        except errors.UserDeactivatedError:
            return False, "USER_DEACTIVATED"
        except Exception as e:
            return False, str(e)

    async def get_info(self):
        me = self.me or await self.client.get_me()
        return {"id": me.id, "phone": me.phone,
                "name": f"{me.first_name or ''} {me.last_name or ''}".strip(),
                "username": me.username or "",
                "premium": getattr(me, "premium", False),
                "access_hash": me.access_hash}

    async def scrape_members(self, group, ftype="all", limit=0):
        members = []
        try:
            entity = await self.client.get_entity(group)
        except Exception as e:
            return [], str(e)
        filters = {"all": ChannelParticipantsSearch(""),
                   "recent": ChannelParticipantsRecent(),
                   "admins": ChannelParticipantsAdmins(),
                   "bots": ChannelParticipantsBots()}
        sf = filters.get(ftype, filters["all"])
        offset = 0
        while True:
            try:
                r = await self.client(GetParticipantsRequest(
                    channel=entity, filter=sf, offset=offset, limit=100, hash=0))
                if not r.users: break
                for u in r.users:
                    m = {"user_id": u.id,
                         "name": f"{u.first_name or ''} {u.last_name or ''}".strip(),
                         "username": u.username or "", "phone": u.phone or "",
                         "access_hash": str(u.access_hash or ""),
                         "status": 1 if isinstance(u.status, UserStatusOnline) else
                                   2 if isinstance(u.status, UserStatusRecently) else 0,
                         "premium": getattr(u, "premium", False), "bot": u.bot}
                    members.append(m)
                offset += len(r.users)
                if limit and len(members) >= limit:
                    return members[:limit], None
                if len(r.users) < 100: break
                await asyncio.sleep(random.uniform(0.5, 2))
            except errors.FloodWaitError as e:
                await asyncio.sleep(e.seconds + 5)
            except Exception as e:
                return members, str(e)
        return members, None

    async def scrape_chatters(self, group, limit=0):
        """Scrape members who posted messages (works on closed groups)."""
        members = {}
        try:
            entity = await self.client.get_entity(group)
        except Exception as e:
            return [], str(e)
        offset_id = 0
        total = 0
        while True:
            try:
                h = await self.client(GetHistoryRequest(
                    peer=entity, offset_id=offset_id, offset_date=None,
                    add_offset=0, limit=100, max_id=0, min_id=0, hash=0))
                if not h.messages: break
                for msg in h.messages:
                    if hasattr(msg, 'from_id') and msg.from_id:
                        uid = getattr(msg.from_id, 'user_id', None)
                        if uid and uid not in members:
                            for u in h.users:
                                if u.id == uid:
                                    members[uid] = {
                                        "user_id": u.id,
                                        "name": f"{u.first_name or ''} {u.last_name or ''}".strip(),
                                        "username": u.username or "", "phone": u.phone or "",
                                        "access_hash": str(u.access_hash or ""),
                                        "premium": getattr(u, "premium", False)}
                                    break
                offset_id = h.messages[-1].id
                total += len(h.messages)
                if limit and total >= limit: break
                await asyncio.sleep(random.uniform(0.3, 1))
            except errors.FloodWaitError as e:
                await asyncio.sleep(e.seconds + 5)
            except Exception as e:
                return list(members.values()), str(e)
        return list(members.values()), None

    async def add_member(self, group, user, method="username"):
        try:
            entity = await self.client.get_entity(group)
            if method == "username" and user.get("username"):
                ue = await self.client.get_entity(user["username"])
            elif method == "id" and user.get("user_id"):
                ue = await self.client.get_input_entity(
                    InputPeerUser(int(user["user_id"]), int(user.get("access_hash", 0))))
            elif method == "phone" and user.get("phone"):
                c = InputPhoneContact(client_id=random.randint(0,2**31),
                    phone=user["phone"], first_name=user.get("name","U"), last_name="")
                await self.client(ImportContactsRequest([c]))
                ue = await self.client.get_entity(user["phone"])
            else:
                return False, "NO_IDENTIFIER"
            await self.client(InviteToChannelRequest(channel=entity, users=[ue]))
            return True, "OK"
        except errors.UserPrivacyRestrictedError: return False, "PRIVACY"
        except errors.UserNotMutualContactError: return False, "NOT_MUTUAL"
        except errors.UserAlreadyParticipantError: return False, "ALREADY_IN"
        except errors.FloodWaitError as e: return False, f"FLOOD_{e.seconds}"
        except errors.PeerFloodError: return False, "PEER_FLOOD"
        except errors.ChatWriteForbiddenError: return False, "WRITE_FORBIDDEN"
        except Exception as e: return False, str(e)

    async def join_group(self, link):
        try:
            s = _normalize_link(link)

            # Private invites:
            # - "+HASH"
            # - "joinchat/HASH"
            # - "t.me/+HASH" becomes "+HASH" after normalize
            if s.startswith("+") or s.startswith("joinchat/"):
                h = s.replace("joinchat/", "").replace("+", "")
                await self.client(ImportChatInviteRequest(h))
            else:
                # Public username/link
                e = await self.client.get_entity(s)
                await self.client(JoinChannelRequest(e))

            return True, "OK"

        except errors.UserAlreadyParticipantError:
            return True, "ALREADY"
        except errors.FloodWaitError as e:
            return False, f"FLOOD_{e.seconds}"
        except errors.InviteHashExpiredError:
            return False, "EXPIRED"
        except errors.InviteHashInvalidError:
            return False, "INVITE_INVALID"
        except Exception as e:
            return False, str(e)

    async def leave_group(self, group):
        try:
            e = await self.client.get_entity(group)
            await self.client(LeaveChannelRequest(e))
            return True, "OK"
        except Exception as e: return False, str(e)

    async def send_message(self, target, msg, file=None, image=None):
        try:
            e = await self.client.get_entity(target)
            if image: await self.client.send_file(e, image, caption=msg)
            elif file: await self.client.send_file(e, file, caption=msg)
            else: await self.client.send_message(e, msg)
            return True, "OK"
        except errors.FloodWaitError as e: return False, f"FLOOD_{e.seconds}"
        except errors.UserIsBlockedError: return False, "BLOCKED"
        except errors.PeerFloodError: return False, "PEER_FLOOD"
        except Exception as e: return False, str(e)

    async def read_messages(self, chat, limit=5):
        try:
            e = await self.client.get_entity(chat)
            msgs = []
            async for m in self.client.iter_messages(e, limit=limit):
                msgs.append({"id":m.id,"date":m.date.isoformat() if m.date else "",
                             "text":m.text or "","from":getattr(m.from_id,"user_id",None) if m.from_id else None})
            return msgs, None
        except Exception as e: return [], str(e)

    async def report_user(self, user, reason_type="spam"):
        """Report a user/channel for spam or other reasons."""
        try:
            e = await self.client.get_entity(user)
            reasons = {"spam": InputReportReasonSpam(),
                       "violence": InputReportReasonViolence(),
                       "other": InputReportReasonOther()}
            r = reasons.get(reason_type, InputReportReasonSpam())
            await self.client(ReportRequest(peer=e, id=[], reason=r, message=""))
            return True, "REPORTED"
        except Exception as e:
            return False, str(e)

    async def disconnect(self):
        async with _lock_for(self.phone):
            if self.client:
                try:
                    await self.client.disconnect()
                except Exception:
                    pass
                finally:
                    self.client = None
            self.connected = False