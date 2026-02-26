"""
Infinity Telegram V1.0 - Anti-Ban Engine
"""
import random, time, hashlib, json, os, string

DEVICES = [
    "Samsung Galaxy S24 Ultra","Samsung Galaxy S23+","Samsung Galaxy A54",
    "iPhone 15 Pro Max","iPhone 15 Pro","iPhone 14 Pro",
    "Google Pixel 8 Pro","Google Pixel 7a","OnePlus 12","OnePlus 11",
    "Xiaomi 14 Pro","Huawei P60 Pro","Sony Xperia 1 V",
]
SYSTEMS = ["Android 14","Android 13","Android 12","iOS 17.4","iOS 17.3","iOS 17.1","iOS 16.7"]
APP_VERS = ["10.8.1","10.7.2","10.6.3","10.5.0","10.4.5","10.3.2"]
LANGS = ["en","ar","fr","de","es","ru","tr","fa","pt"]

def device_for_phone(phone):
    seed = int(hashlib.md5(phone.encode()).hexdigest()[:8], 16)
    r = random.Random(seed)
    return {
        "device_model": r.choice(DEVICES),
        "system_version": r.choice(SYSTEMS),
        "app_version": r.choice(APP_VERS),
        "lang_code": r.choice(LANGS),
        "system_lang_code": r.choice(LANGS),
    }

def human_delay(action="default"):
    delays = {
        "message": (3,12), "add_member": (15,45), "join": (10,30),
        "scrape": (0.5,2), "login": (2,5), "default": (2,8),
    }
    lo, hi = delays.get(action, delays["default"])
    d = random.uniform(lo, hi) + random.gauss(0, 0.3)
    if random.random() < 0.05:
        d += random.uniform(5, 15)
    return max(0.1, d)

def invisible_chars(n=1):
    chars = ['\u200b','\u200c','\u200d','\ufeff','\u2060']
    return ''.join(random.choices(chars, k=n))

def safe_batch(total, action="add_member"):
    limits = {"add_member":{"b":15,"d":50},"message":{"b":30,"d":200},"join":{"b":10,"d":30}}
    c = limits.get(action, {"b":10,"d":50})
    return {"batch": min(total, c["b"]), "daily_max": c["d"],
            "est_days": max(1, total // c["d"] + 1)}
