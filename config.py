# config.py
import json
import os
from pathlib import Path
from typing import Dict, Any

# بارگذاری متغیرهای محیطی
CREATOR_ID = int(os.getenv("CREATOR_ID"))
MASTER_PASSWORD = os.getenv("MASTER_PASSWORD")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

# دیکشنری وضعیت کاربران
USER_STATES: Dict[int, str] = {}

# مسیر فایل JSON برای متون چندزبانه
TEXTS_JSON_PATH = Path(__file__).parent / "menu_texts.json"

class Config:
    _instance = None
    _texts_loaded = False
    _menu_texts: Dict[str, Dict[str, Any]] = {
        "fa": {}, "en": {}, "ar": {}, "ru": {}
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._load_texts()
        return cls._instance

    @classmethod
    def _load_texts(cls):
        """بارگذاری متون از فایل JSON یا استفاده از نسخه پیش‌فرض"""
        try:
            if TEXTS_JSON_PATH.exists():
                with open(TEXTS_JSON_PATH, 'r', encoding='utf-8') as f:
                    cls._menu_texts = json.load(f)
            else:
                # نسخه پیش‌فرض در صورت عدم وجود فایل JSON
                cls._menu_texts = {
                    "fa": {
                        "creator_success": "شما به عنوان سازنده ثبت شدید!",
                        # ... (همه متون فارسی)
                    },
                    "en": {
                        "creator_success": "You have been registered as the creator!",
                        # ... (همه متون انگلیسی)
                    },
                    "ar": {
                        "creator_success": "تم تسجيلك كمنشئ!",
                        # ... (همه متون عربی)
                    },
                    "ru": {
                        "creator_success": "Вы зарегистрированы как создатель!",
                        # ... (همه متون روسی)
                    }
                }
                cls._save_texts()
            cls._texts_loaded = True
        except Exception as e:
            print(f"Error loading menu texts: {e}")
            cls._texts_loaded = False

    @classmethod
    def _save_texts(cls):
        """ذخیره متون در فایل JSON"""
        try:
            with open(TEXTS_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(cls._menu_texts, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving menu texts: {e}")

    @classmethod
    def get_text(cls, lang: str, key: str, default: str = "") -> str:
        """دریافت متن با مدیریت خطا"""
        if not cls._texts_loaded:
            cls._load_texts()
        
        try:
            return cls._menu_texts.get(lang, {}).get(key, default)
        except Exception:
            return default

    @classmethod
    def get_menu(cls, lang: str, menu_name: str) -> list:
        """دریافت منو با مدیریت خطا"""
        return cls.get_text(lang, f"{menu_name}_menu", [])

# سازگاری با نسخه قبلی
MENU_TEXTS = Config._menu_texts
