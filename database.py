# database.py
import sqlite3
import logging
from typing import List, Dict, Optional, Union, Any
from contextlib import contextmanager

# تنظیمات لاگینگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@contextmanager
def db_connection():
    """مدیریت اتصال به پایگاه داده با استفاده از context manager"""
    conn = None
    try:
        conn = sqlite3.connect("bot.db", isolation_level=None)
        conn.row_factory = sqlite3.Row  # برای دسترسی به ستون‌ها با نام
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")  # فعال کردن کلیدهای خارجی
        yield cursor
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def init_db():
    """مقداردهی اولیه پایگاه داده"""
    with db_connection() as c:
        try:
            # جدول ادمین‌ها
            c.execute('''CREATE TABLE IF NOT EXISTS admins (
                        user_id INTEGER PRIMARY KEY,
                        level INTEGER NOT NULL CHECK(level BETWEEN 1 AND 4)
                    )''')
            
            # جدول کانال‌ها
            c.execute('''CREATE TABLE IF NOT EXISTS channels (
                        user_id INTEGER NOT NULL,
                        channel TEXT NOT NULL,
                        PRIMARY KEY (user_id, channel),
                        FOREIGN KEY (user_id) REFERENCES admins(user_id) ON DELETE CASCADE
                    )''')
            
            # جدول تنظیمات
            c.execute('''CREATE TABLE IF NOT EXISTS settings (
                        user_id INTEGER PRIMARY KEY,
                        interface_lang TEXT NOT NULL DEFAULT 'fa',
                        dest_lang TEXT NOT NULL DEFAULT 'en',
                        chat_destination TEXT,
                        message_format TEXT NOT NULL DEFAULT 'text_with_source',
                        stopped INTEGER NOT NULL DEFAULT 0,
                        pending_level INTEGER,
                        pending_channel TEXT,
                        invite_link TEXT,
                        FOREIGN KEY (user_id) REFERENCES admins(user_id) ON DELETE CASCADE
                    )''')
            
            # جدول فیلترها
            c.execute('''CREATE TABLE IF NOT EXISTS filters (
                        user_id INTEGER NOT NULL,
                        channel TEXT NOT NULL,
                        blacklist TEXT,
                        whitelist TEXT,
                        PRIMARY KEY (user_id, channel),
                        FOREIGN KEY (user_id) REFERENCES admins(user_id) ON DELETE CASCADE
                    )''')
            
            # جدول لیست سیاه
            c.execute('''CREATE TABLE IF NOT EXISTS blacklist (
                        channel TEXT PRIMARY KEY
                    )''')
            
            # جدول لاگ‌ها
            c.execute('''CREATE TABLE IF NOT EXISTS logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        action TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES admins(user_id) ON DELETE CASCADE
                    )''')
            
            logger.info("Database initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            raise

# --- توابع کاربران ---
def get_user_channels(user_id: int) -> List[str]:
    """دریافت لیست کانال‌های کاربر"""
    with db_connection() as c:
        c.execute("SELECT channel FROM channels WHERE user_id = ?", (user_id,))
        return [row['channel'] for row in c.fetchall()]

def get_user_settings(user_id: int) -> Dict[str, Any]:
    """دریافت تنظیمات کاربر"""
    with db_connection() as c:
        c.execute("SELECT * FROM settings WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        
        if not row:
            # ایجاد تنظیمات پیش‌فرض اگر کاربر وجود نداشته باشد
            default_settings = {
                "user_id": user_id,
                "interface_lang": "fa",
                "dest_lang": "en",
                "chat_destination": None,
                "message_format": "text_with_source",
                "stopped": 0,
                "pending_level": None,
                "pending_channel": None,
                "invite_link": None
            }
            c.execute('''INSERT INTO settings (
                        user_id, interface_lang, dest_lang, chat_destination,
                        message_format, stopped, pending_level, pending_channel, invite_link
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', tuple(default_settings.values()))
            return default_settings
        
        return dict(row)

# --- توابع ادمین‌ها ---
def get_admin_level(user_id: int) -> Optional[int]:
    """دریافت سطح ادمین"""
    with db_connection() as c:
        c.execute("SELECT level FROM admins WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        return row['level'] if row else None

def get_all_admins() -> List[int]:
    """دریافت لیست تمام ادمین‌ها"""
    with db_connection() as c:
        c.execute("SELECT user_id FROM admins WHERE level IS NOT NULL")
        return [row['user_id'] for row in c.fetchall()]

def add_admin(user_id: int, level: Optional[int]) -> bool:
    """اضافه کردن یا به‌روزرسانی ادمین"""
    with db_connection() as c:
        try:
            if level is None:
                c.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
            else:
                c.execute('''INSERT OR REPLACE INTO admins (user_id, level)
                            VALUES (?, ?)''', (user_id, level))
            return True
        except sqlite3.Error:
            return False

# --- توابع کانال‌ها ---
def add_channel(user_id: int, channel: str) -> bool:
    """اضافه کردن کانال جدید"""
    with db_connection() as c:
        try:
            c.execute('''INSERT OR IGNORE INTO channels (user_id, channel)
                        VALUES (?, ?)''', (user_id, channel))
            return True
        except sqlite3.Error:
            return False

def remove_channel(user_id: int, channel: str) -> bool:
    """حذف کانال"""
    with db_connection() as c:
        try:
            c.execute('''DELETE FROM channels 
                        WHERE user_id = ? AND channel = ?''', (user_id, channel))
            return True
        except sqlite3.Error:
            return False

# --- توابع فیلترها ---
def get_filters(user_id: int, channel: str) -> Dict[str, str]:
    """دریافت فیلترهای یک کانال"""
    with db_connection() as c:
        c.execute('''SELECT blacklist, whitelist FROM filters
                    WHERE user_id = ? AND channel = ?''', (user_id, channel))
        row = c.fetchone()
        return {
            "blacklist": row['blacklist'] if row else "",
            "whitelist": row['whitelist'] if row else ""
        }

def add_filter(user_id: int, channel: str, blacklist: str, whitelist: str) -> bool:
    """اضافه کردن یا به‌روزرسانی فیلتر"""
    with db_connection() as c:
        try:
            c.execute('''INSERT OR REPLACE INTO filters 
                        (user_id, channel, blacklist, whitelist)
                        VALUES (?, ?, ?, ?)''', 
                        (user_id, channel, blacklist, whitelist))
            return True
        except sqlite3.Error:
            return False

# --- توابع لیست سیاه ---
def is_blacklisted(channel: str) -> bool:
    """بررسی وجود کانال در لیست سیاه"""
    with db_connection() as c:
        c.execute("SELECT 1 FROM blacklist WHERE channel = ?", (channel,))
        return c.fetchone() is not None

def add_blacklist(channel: str) -> bool:
    """اضافه کردن به لیست سیاه"""
    with db_connection() as c:
        try:
            c.execute('''INSERT OR IGNORE INTO blacklist (channel)
                        VALUES (?)''', (channel,))
            return True
        except sqlite3.Error:
            return False

# --- توابع تنظیمات ---
def update_settings(user_id: int, **kwargs) -> bool:
    """به‌روزرسانی تنظیمات کاربر"""
    with db_connection() as c:
        try:
            valid_fields = [
                'interface_lang', 'dest_lang', 'chat_destination',
                'message_format', 'stopped', 'pending_level',
                'pending_channel', 'invite_link'
            ]
            
            updates = []
            values = []
            for key, value in kwargs.items():
                if key in valid_fields:
                    updates.append(f"{key} = ?")
                    values.append(value)
            
            if updates:
                query = f"UPDATE settings SET {', '.join(updates)} WHERE user_id = ?"
                values.append(user_id)
                c.execute(query, tuple(values))
            
            return True
        except sqlite3.Error:
            return False

# --- توابع لاگ ---
def log_action(user_id: int, action: str) -> bool:
    """ثبت عمل در لاگ"""
    with db_connection() as c:
        try:
            c.execute('''INSERT INTO logs (user_id, action)
                        VALUES (?, ?)''', (user_id, action))
            return True
        except sqlite3.Error:
            return False

# --- توابع سطح دسترسی ---
def adjust_channels_on_demote(user_id: int, new_level: int) -> int:
    """تنظیم کانال‌ها پس از تنزل سطح"""
    limits = {1: 20, 2: 20, 3: 15, 4: 10}
    current_channels = get_user_channels(user_id)
    
    if len(current_channels) > limits[new_level]:
        excess = len(current_channels) - limits[new_level]
        for channel in current_channels[:excess]:
            remove_channel(user_id, channel)
        return excess
    return 0 
