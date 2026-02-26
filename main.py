#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║  ∞  INFINITY TELEGRAM V1.0 — Cyber Black Luxury Edition  ∞  ║
║                                                              ║
║  Features:                                                   ║
║  • Multi-account with unique API_ID/API_HASH per account     ║
║  • External Api_Hash.txt / Accounts.txt / Working_Accounts   ║
║  • sessions/ folder for all session files                    ║
║  • tools/ folder for scraped data & IDs                      ║
║  • Advanced proxy management (SOCKS5/HTTP/MTPROTO)           ║
║  • Anti-ban with human behavior simulation                   ║
║  • Complaints/Reporting system                               ║
║  • Member scraping (even closed groups via chat history)      ║
║  • Premium vs Normal filtering                               ║
║  • ID-based adding from extracted data                       ║
║  • Arabic/English bilingual interface                        ║
║  • Cyber Black Luxury theme                                  ║
╚══════════════════════════════════════════════════════════════╝

File Structure:
  infinity_telegram/
  ├── main.py              ← Entry point
  ├── app.py               ← GUI Application
  ├── config.py            ← Theme, translations, paths
  ├── managers.py          ← File & data managers
  ├── engine.py            ← Telegram client engine
  ├── antiban.py           ← Anti-ban system
  ├── requirements.txt     ← Dependencies
  ├── Api_Hash.txt         ← API ID,Hash pairs (one per line)
  ├── Accounts.txt         ← Phone accounts with API
  ├── Working_Accounts.txt ← Confirmed working accounts
  ├── sessions/            ← Session files (.session)
  ├── tools/               ← Scraped data, IDs, exports
  └── data/                ← Settings, proxy list

Requirements:
  pip install telethon openpyxl

Usage:
  python main.py
"""
import sys, os

if sys.version_info < (3, 10):
    print("❌ Python 3.10+ required!")
    sys.exit(1)

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

def check_deps():
    missing = []
    for mod, pkg in [("telethon","telethon"),("openpyxl","openpyxl")]:
        try: __import__(mod)
        except ImportError: missing.append(pkg)
    if missing:
        print(f"⚠ Missing: {', '.join(missing)}")
        print(f"  Install: pip install {' '.join(missing)}")
        print("  GUI will launch but Telegram features need these.\n")

def init_files():
    """Create default files if they don't exist."""
    from config import API_HASH_FILE, ACCOUNTS_FILE, WORKING_ACCOUNTS_FILE, SESSIONS_DIR, TOOLS_DIR
    for d in [SESSIONS_DIR, TOOLS_DIR]:
        os.makedirs(d, exist_ok=True)
    if not os.path.exists(API_HASH_FILE):
        with open(API_HASH_FILE, "w") as f:
            f.write("# Api_Hash.txt - Format: api_id,api_hash (one pair per line)\n")
            f.write("# Example: 29907707,bc62461b45f748bc7675c81e3dc4d481\n")
    if not os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "w") as f:
            f.write("# Accounts.txt - Format: +phone,api_id@api_hash;\n")
    if not os.path.exists(WORKING_ACCOUNTS_FILE):
        with open(WORKING_ACCOUNTS_FILE, "w") as f:
            f.write("# Working_Accounts.txt - Auto-generated after check\n")

if __name__ == "__main__":
    print("="*60)
    print("  ∞ INFINITY TELEGRAM V1.0")
    print("  Cyber Black Luxury Edition")
    print("="*60)
    check_deps()
    init_files()
    print("🚀 Launching...")
    from app import main
    main()
