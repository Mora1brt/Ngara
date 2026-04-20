import threading
import telebot
import subprocess
import os
import json
import zipfile
import tempfile
import shutil
import requests
import re
import gc
import logging
import json
import hashlib
import sys
import socket
import psutil
import time
from telebot import types
from datetime import datetime, timedelta
import signal
import sqlite3
import platform
import uuid
import base64

import os
import sys
from telebot.types import BotCommand






BASE_DIR = os.path.dirname(os.path.abspath(__file__))



PENDING_BOTS_DIR = os.path.join(BASE_DIR, 'pending_bots')
ACTIVE_BOTS_DIR = os.path.join(BASE_DIR, 'active_bots')
HOSTING_MANAGER_DIR = os.path.join(BASE_DIR, 'hosting_manager')

print(f"📁 المسار الأساسي: {BASE_DIR}")


for directory in [PENDING_BOTS_DIR, ACTIVE_BOTS_DIR, HOSTING_MANAGER_DIR]:
    if not os.path.exists(directory):
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ تم إنشاء المجلد: {directory}")
        except Exception as e:
            print(f"❌ فشل في إنشاء المجلد {directory}: {e}")

            BASE_DIR = '/tmp/bot_hosting' if os.access('/tmp', os.W_OK) else os.getcwd()
            break


uploaded_files_dir = ACTIVE_BOTS_DIR


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot_security.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SecureBot")


TOKEN = '8396344168:AAHri03e_afzF6CE9NkTwx0kJpXAOShJFbc'
ADMIN_ID = 8405201865
YOUR_USERNAME = '@mora_330'
CHANNEL_USERNAME = '@I_FIY'


bot = telebot.TeleBot(TOKEN)


bot_scripts = {}
stored_tokens = {}
user_subscriptions = {}
user_files = {}
active_users = set()
banned_users = set()
pending_approvals = {}

bot_locked = False
free_mode = False

def setup_bot_commands():
    commands = [
        BotCommand('start', '『✧』 بـــدء الــبــــوت'),
        BotCommand('menu', '『📋』 قــائــمــة الــأوامــر'),
        BotCommand('upload', '『🚀』 رفـــع بــوت جــديــد'),
        BotCommand('mybots', '『🤖』 بــوتــاتــي الــنــشــطــة'),
        BotCommand('speed', '『⚡』 اخــتــبــار الــســرعــة'),
        BotCommand('install', '『📦』 تــثــبــيــت مــكــتــبــة'),
        BotCommand('help', '『🆘』 الــمــســاعــدة والــدعــم'),
        BotCommand('profile', '『👤』 الــمــلــف الــشــخــصــي'),
        BotCommand('subscription', '『💎』 حــالــة الاشــتــراك'),
        BotCommand('contact', '『📞』 الــتــواصــل مــع الــمــالــك')
    ]

    admin_commands = commands + [
        BotCommand('admin', '『🛡️』 لــوحــة الــمــطــور'),
        BotCommand('users', '『👥』 إدارة الــمــســتــخــدمــيــن'),
        BotCommand('pending', '『⏳』 الــطــلــبــات الــمــعــلــقــة'),
        BotCommand('stats', '『📊』 إحــصــائــيــات الــنــظــام'),
        BotCommand('broadcast', '『📢』 إرســال إذاعــة'),
        BotCommand('ban', '『⛔』 حــظــر مــســتــخــدم'),
        BotCommand('unban', '『✅』 إلــغــاء حــظــر')
    ]

    try:
        bot.set_my_commands(commands)
        print("✅ تم إعداد أوامر البوت الجانبية")
    except Exception as e:
        print(f"❌ خطأ في إعداد الأوامر: {e}")
# إضافة بعد المتغيرات الأخرى
installed_libraries = set()  # مجموعة لتتبع المكتبات المثبتة

def load_installed_libraries():
    """تحميل قائمة المكتبات المثبتة من ملف"""
    global installed_libraries
    try:
        if os.path.exists('installed_libs.json'):
            with open('installed_libs.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                installed_libraries = set(data.get('libraries', []))
                logger.info(f"تم تحميل {len(installed_libraries)} مكتبة مثبتة")
    except Exception as e:
        logger.error(f"خطأ في تحميل المكتبات المثبتة: {e}")

def save_installed_libraries():
    """حفظ قائمة المكتبات المثبتة في ملف"""
    try:
        data = {'libraries': list(installed_libraries)}
        with open('installed_libs.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"خطأ في حفظ المكتبات المثبتة: {e}")

def add_installed_libraries(libraries):
    """إضافة مكتبات إلى القائمة المثبتة"""
    global installed_libraries
    for lib in libraries:
        # استخراج اسم المكتبة الأساسي (بدون إصدار أو شروط)
        lib_name = lib.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].strip()
        installed_libraries.add(lib_name)
    save_installed_libraries()
    logger.info(f"تم إضافة {len(libraries)} مكتبة إلى القائمة المثبتة")

def is_library_installed(library):
    """التحقق مما إذا كانت المكتبة مثبتة بالفعل"""
    lib_name = library.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].strip()
    return lib_name in installed_libraries

def filter_installed_libraries(required_libs):
    """فلترة المكتبات المطلوبة وإرجاع فقط غير المثبتة"""
    new_libs = []
    for lib in required_libs:
        if not is_library_installed(lib):
            new_libs.append(lib)
    return new_libs
    
def extract_bot_info_from_folder(folder_name):
    """استخراج معلومات البوت من اسم المجلد"""
    try:

        if folder_name.startswith('bot_'):
            parts = folder_name.split('_')
            if len(parts) >= 3:
                user_id = int(parts[1])
                file_name = '_'.join(parts[2:]) + '.py'
                return user_id, file_name
        return None, None
    except:
        return None, None

def get_main_script_in_folder(folder_path):
    """الحصول على ملف البايثون الرئيسي في المجلد"""
    try:
        py_files = [f for f in os.listdir(folder_path)
                   if f.endswith('.py') and not f.startswith('__')]


        for preferred in ['main.py', 'bot.py', 'start.py']:
            if preferred in py_files:
                return os.path.join(folder_path, preferred)


        if py_files:
            return os.path.join(folder_path, py_files[0])

        return None
    except:
        return None
def start_existing_bots():
    """فحص مجلد البوتات النشطة وتشغيل جميع البوتات الموجودة"""
    try:
        logger.info("🔍 جاري فحص مجلد البوتات النشطة وتشغيل البوتات الموجودة...")


        if not os.path.exists(ACTIVE_BOTS_DIR):
            logger.warning("مجلد البوتات النشطة غير موجود")
            return


        bot_folders = [f for f in os.listdir(ACTIVE_BOTS_DIR)
                      if os.path.isdir(os.path.join(ACTIVE_BOTS_DIR, f))]

        if not bot_folders:
            logger.info("لا توجد بوتات مخزنة للبدء")
            return

        started_count = 0

        for bot_folder in bot_folders:
            try:
                bot_folder_path = os.path.join(ACTIVE_BOTS_DIR, bot_folder)


                parts = bot_folder.split('_')
                if len(parts) >= 3:
                    user_id = int(parts[1])
                    file_name = '_'.join(parts[2:]) + '.py'


                    py_files = [f for f in os.listdir(bot_folder_path) if f.endswith('.py')]
                    if not py_files:
                        logger.warning(f"لا توجد ملفات بايثون في {bot_folder}")
                        continue

                    script_path = os.path.join(bot_folder_path, py_files[0])


                    requirements_path = os.path.join(bot_folder_path, 'requirements.txt')
                    if os.path.exists(requirements_path):
                        logger.info(f"جاري تثبيت المتطلبات لـ {bot_folder}")
                        subprocess.check_call(['pip', 'install', '-r', requirements_path])


                    logger.info(f"جاري تشغيل البوت: {bot_folder}")


                    process = subprocess.Popen(
                        ['python3', script_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        cwd=bot_folder_path
                    )


                    bot_scripts[user_id] = {
                        'process': process,
                        'folder_path': bot_folder_path,
                        'file_name': file_name,
                        'script_path': script_path,
                        'status': 'running',
                        'start_time': datetime.now(),
                        'bot_folder_name': bot_folder
                    }


                    threading.Thread(target=monitor_bot_process,
                                   args=(process, user_id, file_name),
                                   daemon=True).start()

                    started_count += 1
                    logger.info(f"✅ تم تشغيل البوت: {bot_folder}")


                    try:
                        token = extract_token_from_script(script_path)
                        if token:
                            bot_info = requests.get(f'https://api.telegram.org/bot{token}/getMe').json()
                            if bot_info.get('ok'):
                                bot_username = bot_info['result']['username']
                                bot.send_message(
                                    ADMIN_ID,
                                    f"🤖 تم تشغيل البوت تلقائياً عند بدء التشغيل:\n"
                                    f"📁 المجلد: {bot_folder}\n"
                                    f"👤 المستخدم: {user_id}\n"
                                    f"🤖 البوت: @{bot_username}\n"
                                    f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                                )
                    except Exception as e:
                        logger.error(f"خطأ في إعلام الأدمن: {e}")

            except Exception as e:
                logger.error(f"❌ فشل في تشغيل البوت {bot_folder}: {e}")

        logger.info(f"✅ تم تشغيل {started_count} بوت من أصل {len(bot_folders)}")


        if started_count > 0:
            bot.send_message(
                ADMIN_ID,
                f"📊 تقرير بدء التشغيل التلقائي:\n\n"
                f"✅ تم تشغيل {started_count} بوت تلقائياً\n"
                f"📁 مجلدات موجودة: {len(bot_folders)}\n"
                f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

    except Exception as e:
        logger.error(f"❌ خطأ في بدء البوتات التلقائي: {e}")

for directory in [PENDING_BOTS_DIR, ACTIVE_BOTS_DIR, HOSTING_MANAGER_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"تم إنشاء المجلد: {directory}")

def init_db():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS subscriptions
                 (user_id INTEGER PRIMARY KEY, expiry TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS user_files
                 (user_id INTEGER, file_name TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS active_users
                 (user_id INTEGER PRIMARY KEY)''')

    c.execute('''CREATE TABLE IF NOT EXISTS banned_users
                 (user_id INTEGER PRIMARY KEY, reason TEXT, ban_date TEXT)''')


    c.execute('''CREATE TABLE IF NOT EXISTS pending_uploads
                 (user_id INTEGER,
                  file_name TEXT,
                  temp_path TEXT,
                  libraries TEXT,
                  request_time TEXT,
                  PRIMARY KEY (user_id, file_name))''')

    conn.commit()
    conn.close()

def save_pending_upload(user_id, file_name, temp_path, libraries):
    """حفظ طلب الرفع في قاعدة البيانات"""
    try:
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()

        libraries_str = json.dumps(libraries)

        c.execute('''INSERT OR REPLACE INTO pending_uploads
                     (user_id, file_name, temp_path, libraries, request_time)
                     VALUES (?, ?, ?, ?, ?)''',
                  (user_id, file_name, temp_path, libraries_str, datetime.now().isoformat()))

        conn.commit()
        conn.close()
        logger.info(f"تم حفظ طلب الرفع للمستخدم {user_id} - الملف: {file_name}")
    except Exception as e:
        logger.error(f"فشل في حفظ طلب الرفع: {e}")

def load_pending_uploads():
    """تحميل طلبات الرفع من قاعدة البيانات"""
    try:
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()

        c.execute('SELECT * FROM pending_uploads')
        uploads = c.fetchall()

        pending_uploads = {}
        for user_id, file_name, temp_path, libraries_str, request_time in uploads:
            libraries = json.loads(libraries_str) if libraries_str else []
            pending_uploads[(user_id, file_name)] = {
                'temp_path': temp_path,
                'libraries': libraries,
                'request_time': datetime.fromisoformat(request_time)
            }

        conn.close()
        logger.info(f"تم تحميل {len(pending_uploads)} طلب رفع من قاعدة البيانات")
        return pending_uploads
    except Exception as e:
        logger.error(f"فشل في تحميل طلبات الرفع: {e}")
        return {}

def remove_pending_upload(user_id, file_name):
    """حذف طلب الرفع من قاعدة البيانات"""
    try:
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()

        c.execute('DELETE FROM pending_uploads WHERE user_id = ? AND file_name = ?',
                  (user_id, file_name))

        conn.commit()
        conn.close()
        logger.info(f"تم حذف طلب الرفع للمستخدم {user_id} - الملف: {file_name}")
    except Exception as e:
        logger.error(f"فشل في حذف طلب الرفع: {e}")

def cleanup_old_requests():
    """حذف الطلبات الأقدم من 7 أيام والملفات المؤقتة من pending_bots"""
    try:
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()

        week_ago = (datetime.now() - timedelta(days=7)).isoformat()


        c.execute('SELECT user_id, file_name, temp_path FROM pending_uploads WHERE request_time < ?', (week_ago,))
        old_requests = c.fetchall()


        for user_id, file_name, temp_path in old_requests:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    logger.info(f"تم حذف الملف المؤقت: {temp_path}")
                except Exception as e:
                    logger.error(f"فشل في حذف الملف المؤقت {temp_path}: {e}")


            pending_file_path = os.path.join(PENDING_BOTS_DIR, file_name)
            if os.path.exists(pending_file_path):
                try:
                    os.remove(pending_file_path)
                    logger.info(f"تم حذف الملف من pending_bots: {pending_file_path}")
                except Exception as e:
                    logger.error(f"فشل في حذف الملف من pending_bots: {e}")


        c.execute('DELETE FROM pending_uploads WHERE request_time < ?', (week_ago,))

        deleted_count = len(old_requests)
        conn.commit()
        conn.close()

        logger.info(f"تم تنظيف {deleted_count} طلب قديم")
        return deleted_count
    except Exception as e:
        logger.error(f"فشل في تنظيف الطلبات القديمة: {e}")
        return 0

def load_data():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()

    c.execute('SELECT * FROM subscriptions')
    subscriptions = c.fetchall()
    for user_id, expiry in subscriptions:
        user_subscriptions[user_id] = {'expiry': datetime.fromisoformat(expiry)}

    c.execute('SELECT * FROM user_files')
    user_files_data = c.fetchall()
    for user_id, file_name in user_files_data:
        if user_id not in user_files:
            user_files[user_id] = []
        user_files[user_id].append(file_name)

    c.execute('SELECT * FROM active_users')
    active_users_data = c.fetchall()
    for user_id, in active_users_data:
        active_users.add(user_id)

    c.execute('SELECT user_id FROM banned_users')
    banned_users_data = c.fetchall()
    for user_id, in banned_users_data:
        banned_users.add(user_id)

    conn.close()


    global pending_approvals
    pending_uploads = load_pending_uploads()
    for key, value in pending_uploads.items():
        pending_approvals[key] = value

    logger.info(f"تم تحميل {len(pending_approvals)} طلب معلق")


    cleaned_count = cleanup_old_requests()
    if cleaned_count > 0:
        logger.info(f"تم تنظيف {cleaned_count} طلب قديم عند بدء التشغيل")

def save_subscription(user_id, expiry):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO subscriptions (user_id, expiry) VALUES (?, ?)',
              (user_id, expiry.isoformat()))
    conn.commit()
    conn.close()

def remove_subscription_db(user_id):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('DELETE FROM subscriptions WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def save_user_file(user_id, file_name):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('INSERT INTO user_files (user_id, file_name) VALUES (?, ?)',
              (user_id, file_name))
    conn.commit()
    conn.close()

def remove_user_file_db(user_id, file_name):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('DELETE FROM user_files WHERE user_id = ? AND file_name = ?',
              (user_id, file_name))
    conn.commit()
    conn.close()

def add_active_user(user_id):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO active_users (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()

def remove_active_user(user_id):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('DELETE FROM active_users WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def ban_user(user_id, reason):
    banned_users.add(user_id)
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO banned_users (user_id, reason, ban_date) VALUES (?, ?, ?)',
              (user_id, reason, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    logger.warning(f"تم حظر المستخدم {user_id} بسبب: {reason}")

def unban_user(user_id):
    if user_id in banned_users:
        banned_users.remove(user_id)
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute('DELETE FROM banned_users WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        logger.info(f"تم إلغاء حظر المستخدم {user_id}")
        return True
    return False

def is_user_subscribed_to_channel(user_id):
    try:
        chat_member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"فشل في التحقق من اشتراك المستخدم في القناة: {e}")
        return False

def extract_imports_from_file(file_path):
    """
    استخراج جميع المكتبات المستوردة من ملف بايثون
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()

        imports = []


        import_patterns = [
            r'^\s*import\s+(\w+)',
            r'^\s*from\s+(\w+)\s+import',
            r'^\s*import\s+(\w+\.\w+)',
            r'^\s*from\s+(\w+\.\w+)\s+import'
        ]

        for pattern in import_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            imports.extend(matches)


        unique_imports = list(set(imports))


        standard_libs = [
            'os', 'sys', 're', 'json', 'time', 'datetime', 'math', 'random',
            'threading', 'subprocess', 'shutil', 'tempfile', 'logging',
            'hashlib', 'socket', 'platform', 'uuid', 'base64', 'sqlite3',
            'urllib', 'itertools', 'collections', 'functools', 'operator',
            'pathlib', 'typing', 'enum', 'calendar', 'csv', 'html', 'http',
            'email', 'ssl', 'zipfile', 'gzip', 'tarfile', 'json', 'pickle',
            'shelve', 'dbm', 'sqlite3', 'xml', 'webbrowser', 'cgi', 'cgitb',
            'wsgiref', 'urllib', 'ftplib', 'poplib', 'imaplib', 'nntplib',
            'smtplib', 'telnetlib', 'uuid', 'socket', 'ssl', 'select',
            'selectors', 'asyncore', 'asynchat', 'signal', 'mmap', 'errno',
            'glob', 'fnmatch', 'linecache', 'shlex', 'macpath', 'stat',
            'filecmp', 'tempfile', 'fileinput', 'statvfs', 'fileinput',
            'ast', 'symtable', 'symbol', 'token', 'keyword', 'tokenize',
            'py_compile', 'compileall', 'dis', 'pickletools', 'formatter',
            'tabnanny', 'pyclbr', 'py_compile', 'compileall', 'dis',
            'pickletools', 'formatter', 'imputil', 'code', 'codeop',
            'pty', 'tty', 'termios', 'resource', 'nis', 'syslog', 'posix',
            'pwd', 'spwd', 'grp', 'crypt', 'dl', 'dbm', 'gdbm', 'termios',
            'tty', 'pty', 'fcntl', 'pipes', 'posixfile', 'resource',
            'nis', 'syslog', 'commands', 'getopt', 'argparse', 'getpass',
            'curses', 'platform', 'errno', 'ctypes', 'struct', 'weakref',
            'types', 'copy', 'pprint', 'reprlib', 'enum', 'numbers', 'math',
            'cmath', 'decimal', 'fractions', 'random', 'statistics', 'itertools',
            'functools', 'operator', 'collections', 'heapq', 'bisect', 'array',
            'weakref', 'copy', 'pprint', 'reprlib', 'enum', 'graphlib'
        ]


        filtered_imports = []
        for lib in unique_imports:

            base_lib = lib.split('.')[0]
            if base_lib not in standard_libs:
                filtered_imports.append(lib)

        return filtered_imports

    except Exception as e:
        logger.error(f"خطأ في استخراج المكتبات من {file_path}: {e}")
        return []
        
def get_user_info(user_id):
    """الحصول على معلومات المستخدم"""
    try:
        user_info = bot.get_chat(user_id)
        user_name = user_info.first_name or "بدون اسم"
        user_username = f"@{user_info.username}" if user_info.username else "بدون يوزر"
        return user_name, user_username
    except Exception as e:
        logger.error(f"فشل في جلب معلومات المستخدم {user_id}: {e}")
        return "غير متاح", "غير متاح"
        
def get_user_bots(user_id):
    """الحصول على جميع البوتات الخاصة بالمستخدم"""
    user_bots = {}
    
    # البحث في bot_scripts
    for chat_id, bot_info in bot_scripts.items():
        if chat_id == user_id:
            user_bots[bot_info.get('file_name', '')] = {
                'status': bot_info.get('status', 'stopped'),
                'folder_path': bot_info.get('folder_path', ''),
                'script_path': bot_info.get('script_path', ''),
                'bot_folder_name': bot_info.get('bot_folder_name', ''),
                'start_time': bot_info.get('start_time', 'غير معروف')
            }
    
    # البحث في user_files
    if user_id in user_files:
        for file_name in user_files[user_id]:
            if file_name not in user_bots:
                user_bots[file_name] = {
                    'status': 'stopped',
                    'folder_path': '',
                    'script_path': '',
                    'bot_folder_name': '',
                    'start_time': 'غير معروف'
                }
    
    return user_bots
    
def modify_bot_database_path(script_path, new_db_path, bot_folder):
    """تعديل مسار قاعدة البيانات والملفات ليكون كل شيء في مجلد البوت"""
    try:
        with open(script_path, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()


        data_dir = os.path.join(bot_folder, 'data')
        logs_dir = os.path.join(bot_folder, 'logs')
        temp_dir = os.path.join(bot_folder, 'temp')
        assets_dir = os.path.join(bot_folder, 'assets')

        for directory in [data_dir, logs_dir, temp_dir, assets_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)


        patterns = [

            (r"sqlite3\.connect\(['\"]([^'\"]*\.db)['\"]\)", f"sqlite3.connect('{new_db_path}')"),
            (r"sqlite3\.connect\(['\"]([^'\"]*\.sqlite)['\"]\)", f"sqlite3.connect('{new_db_path}')"),


            (r"open\(['\"]([^'\"]*\.json)['\"]", r"open('{}' + r'\1'".format(os.path.join(data_dir, ''))),
            (r"open\(['\"]([^'\"]*\.txt)['\"]", r"open('{}' + r'\1'".format(os.path.join(data_dir, ''))),
            (r"open\(['\"]([^'\"]*\.csv)['\"]", r"open('{}' + r'\1'".format(os.path.join(data_dir, ''))),


            (r"logging\.FileHandler\(['\"]([^'\"]*\.log)['\"]\)", r"logging.FileHandler('{}' + r'\1')".format(os.path.join(logs_dir, ''))),
        ]

        modified_content = content

        for pattern, replacement in patterns:
            modified_content = re.sub(pattern, replacement, modified_content)


        setup_code = f"""

import os
import sqlite3


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
TEMP_DIR = os.path.join(BASE_DIR, 'temp')
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')


DB_PATH = os.path.join(BASE_DIR, '{os.path.basename(new_db_path)}')


for directory in [DATA_DIR, LOGS_DIR, TEMP_DIR, ASSETS_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)


conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

"""

        lines = modified_content.split('\n')
        imports_end = 0
        for i, line in enumerate(lines):
            if line.startswith(('import ', 'from ')) or line.strip() == '':
                imports_end = i
            else:
                break

        lines.insert(imports_end + 1, setup_code)
        modified_content = '\n'.join(lines)


        modified_script_path = os.path.join(bot_folder, f"modified_{os.path.basename(script_path)}")
        with open(modified_script_path, 'w', encoding='utf-8') as file:
            file.write(modified_content)

        logger.info(f"✅ تم إعداد البوت بمسارات منفصلة في: {bot_folder}")
        return modified_script_path

    except Exception as e:
        logger.error(f"❌ فشل في تعديل مسارات البوت: {e}")
        return script_path
        
def install_libraries(libraries):
    """
    تثبيت قائمة من المكتبات مع تخطي المثبتة مسبقاً
    """
    # فلترة المكتبات غير المثبتة
    new_libraries = filter_installed_libraries(libraries)
    
    if not new_libraries:
        return ["✅ جميع المكتبات مثبتة مسبقاً"]
    
    results = []
    installed_count = 0
    
    for lib in new_libraries:
        try:
            # محاولة التثبيت
            subprocess.check_call(['pip', 'install', lib, '--quiet'])
            results.append(f"✅ {lib} - تم التثبيت بنجاح")
            installed_count += 1
            
            # إضافة إلى قائمة المثبتة
            lib_name = lib.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].strip()
            installed_libraries.add(lib_name)
            
        except subprocess.CalledProcessError:
            try:
                # محاولة التثبيت مع تحديث
                subprocess.check_call(['pip', 'install', lib, '--upgrade', '--quiet'])
                results.append(f"✅ {lib} - تم التثبيت مع التحديث")
                installed_count += 1
                
                # إضافة إلى قائمة المثبتة
                lib_name = lib.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].strip()
                installed_libraries.add(lib_name)
                
            except subprocess.CalledProcessError as e:
                results.append(f"❌ {lib} - فشل في التثبيت")
        except Exception as e:
            results.append(f"❌ {lib} - خطأ: {e}")
    
    # حفظ المكتبات المثبتة
    if installed_count > 0:
        save_installed_libraries()
    
    # إضافة معلومات عن المكتبات المتخطية
    skipped_count = len(libraries) - len(new_libraries)
    if skipped_count > 0:
        results.insert(0, f"⏭️ تم تخطي {skipped_count} مكتبة مثبتة مسبقاً")
    
    return results

def install_single_library(library_name):
    """
    تثبيت مكتبة واحدة مع التحقق من التثبيت المسبق
    """
    # التحقق مما إذا كانت مثبتة بالفعل
    if is_library_installed(library_name):
        return f"⏭️ المكتبة {library_name} مثبتة مسبقاً"
    
    try:
        # التثبيت
        result = subprocess.run([
            'pip', 'install', library_name,
            '--no-cache-dir',
            '--quiet',
            '--user'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            # إضافة إلى القائمة
            lib_name = library_name.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].strip()
            installed_libraries.add(lib_name)
            save_installed_libraries()
            return f"✅ تم تثبيت المكتبة {library_name} بنجاح"
        else:
            # محاولة التثبيت بدون تبعيات
            result = subprocess.run([
                'pip', 'install', library_name,
                '--no-dependencies',
                '--quiet',
                '--user'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                lib_name = library_name.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].strip()
                installed_libraries.add(lib_name)
                save_installed_libraries()
                return f"✅ تم تثبيت {library_name} (بدون تبعيات)"
            else:
                return f"❌ فشل في تثبيت {library_name}"
                
    except subprocess.TimeoutExpired:
        return f"⏰ انتهى وقت تثبيت {library_name}"
    except Exception as e:
        return f"❌ خطأ في تثبيت {library_name}: {str(e)[:50]}"
        
def install_libraries_safe(libraries):
    """
    تثبيت المكتبات بشكل آمن مع تخطي المثبتة
    """
    # فلترة المكتبات غير المثبتة
    new_libraries = filter_installed_libraries(libraries)
    
    if not new_libraries:
        return ["✅ جميع المكتبات مثبتة مسبقاً"]
    
    results = []
    skipped_count = len(libraries) - len(new_libraries)
    
    if skipped_count > 0:
        results.append(f"⏭️ تم تخطي {skipped_count} مكتبة مثبتة مسبقاً")
    
    for i, lib in enumerate(new_libraries):
        try:
            # فحص الذاكرة
            memory = psutil.virtual_memory()
            if memory.percent > 80:
                results.append(f"🛑 إيقاف التثبيت - الذاكرة {memory.percent}%")
                break
            
            # فاصل زمني بين التثبيتات
            if i > 0:
                time.sleep(5)
            
            # التثبيت
            result = subprocess.run([
                'python', '-m', 'pip', 'install', lib,
                '--no-cache-dir',
                '--quiet',
                '--user',
                '--no-warn-script-location'
            ], capture_output=True, text=True, timeout=90)
            
            if result.returncode == 0:
                results.append(f"✅ {lib} - ناجح")
                # إضافة إلى قائمة المثبتة
                lib_name = lib.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].strip()
                installed_libraries.add(lib_name)
            else:
                results.append(f"❌ {lib} - فشل")
                
        except Exception as e:
            results.append(f"❌ {lib} - خطأ: {str(e)[:30]}")
    
    # حفظ القائمة إذا تم تثبيت أي مكتبة
    save_installed_libraries()
    return results
    
init_db()
load_data()

def create_main_menu(user_id):
    markup = types.InlineKeyboardMarkup()
    upload_button = types.InlineKeyboardButton('📤 رفع ملف', callback_data='upload')
    my_bots_button = types.InlineKeyboardButton('🤖 بوتاتي', callback_data='my_bots')  # زر جديد
    speed_button = types.InlineKeyboardButton('⚡ سرعة البوت', callback_data='speed')
    install_lib_button = types.InlineKeyboardButton('📚 تثبيت مكتبة', callback_data='install_library')
    contact_button = types.InlineKeyboardButton('📞 تواصل مع المالك', url=f'https://t.me/{YOUR_USERNAME[1:]}')

    if user_id == ADMIN_ID:
        subscription_button = types.InlineKeyboardButton('💳 الاشتراكات', callback_data='subscription')
        stats_button = types.InlineKeyboardButton('📊 إحصائيات', callback_data='stats')
        lock_button = types.InlineKeyboardButton('🔒 قفل البوت', callback_data='lock_bot')
        unlock_button = types.InlineKeyboardButton('🔓 فتح البوت', callback_data='unlock_bot')
        free_mode_button = types.InlineKeyboardButton('🔓 بدون اشتراك', callback_data='free_mode')
        broadcast_button = types.InlineKeyboardButton('📢 إذاعة', callback_data='broadcast')
        ban_button = types.InlineKeyboardButton('🔨 حظر مستخدم', callback_data='ban_user')
        unban_button = types.InlineKeyboardButton('🔓 إلغاء حظر', callback_data='unban_user')
        active_bots_button = types.InlineKeyboardButton('🤖 البوتات النشطة', callback_data='active_bots')
        pending_uploads_button = types.InlineKeyboardButton('📋 الطلبات المعلقة', callback_data='pending_uploads')

        markup.add(upload_button, my_bots_button)  # إضافة الزر للادمن أيضاً
        markup.add(speed_button, subscription_button, stats_button)
        markup.add(lock_button, unlock_button, free_mode_button)
        markup.add(broadcast_button)
        markup.add(ban_button, unban_button)
        markup.add(active_bots_button, pending_uploads_button)
    else:
        markup.add(upload_button, my_bots_button)  # إضافة الزر للمستخدمين العاديين
        markup.add(speed_button)
        markup.add(install_lib_button)  # نقل زر تثبيت المكتبة لصف منفصل

    markup.add(contact_button)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id

    if user_id in banned_users:
        bot.send_message(message.chat.id, "⛔ أنت محظور من استخدام هذا البوت. يرجى التواصل مع المطور إذا كنت تعتقد أن هذا خطأ.")
        return

    if bot_locked:
        bot.send_message(message.chat.id, "⚠️ البوت مقفل حالياً. الرجاء المحاولة لاحقًا.")
        return

    if not is_user_subscribed_to_channel(user_id):
        markup = types.InlineKeyboardMarkup()
        channel_button = types.InlineKeyboardButton('انضم إلى القناة', url=f'https://t.me/{CHANNEL_USERNAME[1:]}')
        check_button = types.InlineKeyboardButton('✅ تحقق من الاشتراك', callback_data='check_subscription')
        markup.add(channel_button, check_button)
        bot.send_message(message.chat.id, "⚠️ يجب عليك الانضمام إلى قناتنا أولاً لاستخدام البوت.", reply_markup=markup)
        return

    user_name = message.from_user.first_name
    user_username = message.from_user.username

    try:
        user_profile = bot.get_chat(user_id)
        user_bio = user_profile.bio if user_profile.bio else "لا يوجد بايو"
    except Exception as e:
        logger.error(f"فشل في جلب البايو: {e}")
        user_bio = "لا يوجد بايو"

    try:
        user_profile_photos = bot.get_user_profile_photos(user_id, limit=1)
        if user_profile_photos.photos:
            photo_file_id = user_profile_photos.photos[0][-1].file_id
        else:
            photo_file_id = None
    except Exception as e:
        logger.error(f"فشل في جلب صورة المستخدم: {e}")
        photo_file_id = None

    if user_id not in active_users:
        active_users.add(user_id)
        add_active_user(user_id)

        try:
            welcome_message_to_admin = f"🎉 انضم مستخدم جديد إلى البوت!\n\n"
            welcome_message_to_admin += f"👤 الاسم: {user_name}\n"
            welcome_message_to_admin += f"📌 اليوزر: @{user_username}\n"
            welcome_message_to_admin += f"🆔 الـ ID: {user_id}\n"
            welcome_message_to_admin += f"📝 البايو: {user_bio}\n"

            if photo_file_id:
                bot.send_photo(ADMIN_ID, photo_file_id, caption=welcome_message_to_admin)
            else:
                bot.send_message(ADMIN_ID, welcome_message_to_admin)
        except Exception as e:
            logger.error(f"فشل في إرسال تفاصيل المستخدم إلى الأدمن: {e}")

    welcome_message = f"〽️┇اهلا بك: {user_name}\n"
    welcome_message += f"🆔┇ايديك: {user_id}\n"
    welcome_message += f"♻️┇يوزرك: @{user_username}\n"
    welcome_message += f"📰┇بايو: {user_bio}\n\n"
    welcome_message += "〽️ أنا بوت استضافة ملفات بايثون 🎗 يمكنك استخدام الأزرار أدناه للتحكم ♻️"

    if photo_file_id:
        bot.send_photo(message.chat.id, photo_file_id, caption=welcome_message, reply_markup=create_main_menu(user_id))
    else:
        bot.send_message(message.chat.id, welcome_message, reply_markup=create_main_menu(user_id))

# Handlers للأوامر الجانبية
@bot.message_handler(commands=['menu'])
def show_menu(message):
    user_id = message.from_user.id
    if user_id in banned_users:
        return
    
    markup = create_main_menu(user_id)
    bot.send_message(message.chat.id, "📋 القائمة الرئيسية:", reply_markup=markup)

@bot.message_handler(commands=['upload'])
def upload_command(message):
    ask_to_upload_file(message)

@bot.message_handler(commands=['mybots'])
def show_my_bots(message):
    """عرض بوتاتي (للأمر النصي)"""
    user_id = message.from_user.id
    if user_id in banned_users:
        bot.send_message(message.chat.id, "⛔ أنت محظور من استخدام هذا البوت.")
        return
    
    # استخدام الدالة الجديدة
    user_bots = get_user_bots(user_id)
    
    if not user_bots:
        bot.send_message(message.chat.id, "📭 ليس لديك أي بوتات حالياً.")
        return
    
    bot.send_message(message.chat.id, f"🤖 لديك {len(user_bots)} بوت:")
    
    # عرض كل بوت مع أزرار التحكم
    for file_name, bot_info in user_bots.items():
        status = bot_info.get('status', 'stopped')
        bot_msg = f"📄 {file_name} - الحالة: {status}"
        
        markup = create_user_bot_controls(user_id, file_name, status)
        bot.send_message(message.chat.id, bot_msg, reply_markup=markup, parse_mode='HTML')

import time

@bot.message_handler(commands=['speed'])
def speed_command(message):
    try:
        # إرسال رسالة أولية مع شريط تحميل وهمي
        status_msg = bot.reply_to(message, "🔌 جاري قياس سرعة الاستجابة...\n[⚪⚪⚪⚪⚪⚪⚪⚪⚪⚪] 0%")
        
        start_time = time.time()
        
        # محاكاة حركة الشريط (اختياري ليعطي شكل جمالي)
        time.sleep(0.3)
        bot.edit_message_text("📡 جاري الاتصال بخوادم تليجرام...\n[🔵🔵🔵🔵⚪⚪⚪⚪⚪⚪] 40%", status_msg.chat.id, status_msg.message_id)
        
        # القياس الحقيقي
        response = requests.get(f'https://api.telegram.org/bot{TOKEN}/getMe')
        latency = (time.time() - start_time) * 1000  # تحويل إلى ميلي ثانية
        
        if response.ok:
            # تحديد الحالة والرموز التعبيرية بناءً على السرعة
            if latency < 200:
                status = "سريع جداً 🚀"
                bar = "🔵🔵🔵🔵🔵🔵🔵🔵🔵🔵"
            elif latency < 500:
                status = "سريع ⚡"
                bar = "🟢🟢🟢🟢🟢🟢🟢🟢🟢⚪"
            elif latency < 1000:
                status = "متوسط 🟡"
                bar = "🟡🟡🟡🟡🟡🟡⚪⚪⚪⚪"
            else:
                status = "بطيء 🐢"
                bar = "🔴🔴🔴🔴⚪⚪⚪⚪⚪⚪"

            final_text = (
                f"📊 نتائج فحص السرعة:\n\n"
                f"⏱ الوقت المستغرق: `{latency:.0f}ms`\n"
                f"📈 الحالة: {status}\n"
                f"📶 الشريط: [{bar}]"
            )
            
            bot.edit_message_text(final_text, status_msg.chat.id, status_msg.message_id, parse_mode='Markdown')
        else:
            bot.edit_message_text("⚠️ فشل في الحصول على سرعة البوت.", status_msg.chat.id, status_msg.message_id)
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ: {e}")


@bot.message_handler(commands=['install'])
def install_command(message):
    bot.send_message(message.chat.id, "📚 أرسل اسم المكتبة التي تريد تثبيتها:\n\nمثال:\n`telebot`\n`requests`\n`python-telegram-bot`")
    bot.register_next_step_handler(message, process_library_installation)

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
🆘 المساعدة والدعم:

📋 الأوامر المتاحة:
/start - بدء استخدام البوت
/menu - عرض القائمة الرئيسية
/upload - رفع بوت جديد
/mybots - عرض بوتاتي النشطة
/speed - اختبار سرعة البوت
/install - تثبيت مكتبة
/help - المساعدة والدعم

📞 للتواصل مع المالك:
@mora_330

⚠️ ملاحظات هامة:
1. يجب الانضمام للقناة أولاً
2. الملفات يجب أن تكون بصيغة .py أو .zip
3. في حالة وجود مشاكل راسل المطور
"""
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

@bot.message_handler(commands=['profile'])
def profile_command(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    user_username = message.from_user.username or "بدون يوزر"
    
    try:
        user_profile = bot.get_chat(user_id)
        user_bio = user_profile.bio or "لا يوجد بايو"
    except:
        user_bio = "لا يوجد بايو"
    
    profile_text = f"""
👤 الملف الشخصي:

🆔 الايدي: `{user_id}`
👤 الاسم: {user_name}
📌 اليوزر: @{user_username}
📝 البايو: {user_bio}
"""
    bot.send_message(message.chat.id, profile_text, parse_mode='HTML')

@bot.message_handler(commands=['subscription'])
def subscription_command(message):
    user_id = message.from_user.id
    
    if user_id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup()
        add_subscription_button = types.InlineKeyboardButton('➕ إضافة اشتراك', callback_data='add_subscription')
        remove_subscription_button = types.InlineKeyboardButton('➖ إزالة اشتراك', callback_data='remove_subscription')
        markup.add(add_subscription_button, remove_subscription_button)
        bot.send_message(message.chat.id, "اختر الإجراء الذي تريد تنفيذه:", reply_markup=markup)
    else:
        if free_mode:
            bot.send_message(message.chat.id, "🆓 حالة الاشتراك: البوت يعمل في الوضع الحر")
        elif user_id in user_subscriptions and user_subscriptions[user_id]['expiry'] > datetime.now():
            expiry = user_subscriptions[user_id]['expiry']
            days_left = (expiry - datetime.now()).days
            bot.send_message(message.chat.id, f"💎 حالة الاشتراك: مفعل\n⏳ المتبقي: {days_left} يوم")
        else:
            bot.send_message(message.chat.id, "⚠️ حالة الاشتراك: غير مفعل\n📞 للاستفسار: @mora_330")

@bot.message_handler(commands=['contact'])
def contact_command(message):
    bot.send_message(message.chat.id, f"📞 للتواصل مع المالك:\n@{YOUR_USERNAME[1:]}")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup(row_width=2)
        users_btn = types.InlineKeyboardButton('👥 المستخدمين', callback_data='users')
        pending_btn = types.InlineKeyboardButton('⏳ الطلبات المعلقة', callback_data='pending')
        stats_btn = types.InlineKeyboardButton('📊 الإحصائيات', callback_data='stats')
        broadcast_btn = types.InlineKeyboardButton('📢 إذاعة', callback_data='broadcast')
        ban_btn = types.InlineKeyboardButton('⛔ حظر', callback_data='ban_user')
        unban_btn = types.InlineKeyboardButton('✅ إلغاء حظر', callback_data='unban_user')
        markup.add(users_btn, pending_btn, stats_btn, broadcast_btn, ban_btn, unban_btn)
        bot.send_message(message.chat.id, "🛡️ لوحة تحكم المطور:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "⚠️ هذا الأمر للمطور فقط")

@bot.message_handler(commands=['users'])
def users_management(message):
    if message.from_user.id == ADMIN_ID:
        users_count = len(user_files)
        active_count = len(active_users)
        banned_count = len(banned_users)
        
        users_text = f"""
👥 إدارة المستخدمين:

👤 المستخدمين الكلي: {users_count}
🟢 النشطين: {active_count}
🔴 المحظورين: {banned_count}

📌 لحظر مستخدم: /ban <user_id> <السبب>
📌 لإلغاء الحظر: /unban <user_id>
"""
        bot.send_message(message.chat.id, users_text)
    else:
        bot.send_message(message.chat.id, "⚠️ هذا الأمر للمطور فقط")

@bot.message_handler(commands=['pending'])
def pending_requests(message):
    if message.from_user.id == ADMIN_ID:
        show_pending_uploads(message)
    else:
        bot.send_message(message.chat.id, "⚠️ هذا الأمر للمطور فقط")

@bot.callback_query_handler(func=lambda call: call.data == 'check_subscription')
def check_subscription(call):
    user_id = call.from_user.id
    if is_user_subscribed_to_channel(user_id):
        bot.send_message(call.message.chat.id, "✅ شكراً للانضمام إلى قناتنا! يمكنك الآن استخدام البوت.")
        send_welcome(call.message)
    else:
        markup = types.InlineKeyboardMarkup()
        channel_button = types.InlineKeyboardButton('انضم إلى القناة', url=f'https://t.me/{CHANNEL_USERNAME[1:]}')
        check_button = types.InlineKeyboardButton('✅ تحقق من الاشتراك', callback_data='check_subscription')
        markup.add(channel_button, check_button)
        bot.send_message(call.message.chat.id, "⚠️ لم تنضم بعد إلى القناة. يرجى الانضمام أولاً.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'install_library')
def install_library_callback(call):
    user_id = call.from_user.id

    if user_id in banned_users:
        bot.send_message(call.message.chat.id, "⛔ أنت محظور من استخدام هذا البوت.")
        return

    if bot_locked:
        bot.send_message(call.message.chat.id, "⚠️ البوت مقفل حالياً.")
        return

    if not is_user_subscribed_to_channel(user_id):
        markup = types.InlineKeyboardMarkup()
        channel_button = types.InlineKeyboardButton('انضم إلى القناة', url=f'https://t.me/{CHANNEL_USERNAME[1:]}')
        check_button = types.InlineKeyboardButton('✅ تحقق من الاشتراك', callback_data='check_subscription')
        markup.add(channel_button, check_button)
        bot.send_message(call.message.chat.id, "⚠️ يجب عليك الانضمام إلى قناتنا أولاً.", reply_markup=markup)
        return

    bot.send_message(call.message.chat.id, "📚 أرسل اسم المكتبة التي تريد تثبيتها:\n\nمثال:\n`telebot`\n`requests`\n`python-telegram-bot`")
    bot.register_next_step_handler(call.message, process_library_installation)
def stop_bot_completely(chat_id):
    """إيقاف البوت تماماً بدون حذف الملفات"""
    if chat_id in bot_scripts:
        try:

            if bot_scripts[chat_id].get('process'):
                kill_process_tree(bot_scripts[chat_id]['process'])


            script_path = bot_scripts[chat_id].get('script_path')
            if script_path and os.path.exists(script_path):
                kill_process_by_script_path(script_path)


            bot_scripts[chat_id]['process'] = None
            bot_scripts[chat_id]['status'] = 'stopped'

            logger.info(f"تم إيقاف البوت للمستخدم {chat_id}")
            return True

        except Exception as e:
            logger.error(f"فشل في إيقاف البوت: {e}")
            return False
    return False


def find_bot_by_token(token):
    """البحث عن البوتات النشطة باستخدام توكن معين"""
    active_bots = []

    for chat_id, bot_info in bot_scripts.items():
        if bot_info.get('status') == 'running':
            try:
                script_path = bot_info.get('script_path')
                if script_path and os.path.exists(script_path):
                    current_token = extract_token_from_script(script_path)
                    if current_token == token:
                        active_bots.append({
                            'chat_id': chat_id,
                            'file_name': bot_info.get('file_name'),
                            'process': bot_info.get('process'),
                            'script_path': script_path,
                            'folder_path': bot_info.get('folder_path')
                        })
            except Exception as e:
                logger.error(f"خطأ في البحث عن البوت بالتوكن: {e}")

    return active_bots

def stop_and_remove_duplicate_bots(new_token, current_user_id, current_file_name):
    """إيقاف وحذف البوتات القديمة التي تستخدم نفس التوكن"""
    try:
        duplicate_bots = find_bot_by_token(new_token)
        stopped_count = 0

        for bot_info in duplicate_bots:

            if (bot_info['chat_id'] == current_user_id and
                bot_info['file_name'] == current_file_name):
                continue

            logger.info(f"وجد بوت مكرر: {bot_info['file_name']} للمستخدم {bot_info['chat_id']}")


            if stop_bot_completely(bot_info['chat_id']):
                stopped_count += 1
                logger.info(f"تم إيقاف البوت المكرر: {bot_info['file_name']}")


                try:
                    bot.send_message(
                        bot_info['chat_id'],
                        f"⚠️ تم إيقاف بوتك ({bot_info['file_name']}) تلقائياً لأنه تم رفع بوت جديد بنفس التوكن"
                    )
                except:
                    pass


                delete_bot_files(bot_info['chat_id'])

        return stopped_count

    except Exception as e:
        logger.error(f"خطأ في إيقاف البوتات المكررة: {e}")
        return 0

def delete_bot_files(chat_id):
    """حذف ملفات البوت مع الاحتفاظ بالسجلات"""
    if chat_id in bot_scripts:
        try:
            file_name = bot_scripts[chat_id].get('file_name', '')
            folder_path = bot_scripts[chat_id].get('folder_path', '')


            if folder_path and os.path.exists(folder_path):
                if os.path.isfile(folder_path):

                    os.remove(folder_path)
                    logger.info(f"تم حذف ملف البوت: {folder_path}")
                else:

                    py_files = [f for f in os.listdir(folder_path) if f.endswith('.py')]
                    for py_file in py_files:
                        file_path = os.path.join(folder_path, py_file)
                        os.remove(file_path)
                        logger.info(f"تم حذف ملف: {file_path}")


            if chat_id in user_files and file_name in user_files[chat_id]:
                user_files[chat_id].remove(file_name)
                remove_user_file_db(chat_id, file_name)


            if chat_id in bot_scripts:
                del bot_scripts[chat_id]

            return True

        except Exception as e:
            logger.error(f"فشل في حذف ملفات البوت: {e}")
            return False
    return False

def check_token_conflict(new_script_path, user_id, file_name):
    """فحص التعارض في التوكن وإيقاف البوتات المكررة"""
    try:
        new_token = extract_token_from_script(new_script_path)
        if not new_token:
            return False


        duplicate_bots = find_bot_by_token(new_token)

        if duplicate_bots:
            stopped_count = stop_and_remove_duplicate_bots(new_token, user_id, file_name)
            return stopped_count > 0

    except Exception as e:
        logger.error(f"خطأ في فحص تعارض التوكن: {e}")

    return False
def process_library_installation(message):
    user_id = message.from_user.id
    library_name = message.text.strip()

    if not library_name:
        bot.send_message(message.chat.id, "⚠️ يرجى إرسال اسم مكتبة صحيح.")
        return


    dangerous_commands = [';', '&', '|', '&&', '||', '`', '$', '(', ')', '<', '>']
    if any(cmd in library_name for cmd in dangerous_commands):
        bot.send_message(message.chat.id, "❌ اسم المكتبة يحتوي على أحرف خطيرة.")
        return

    bot.send_message(message.chat.id, f"🔄 جاري تثبيت المكتبة `{library_name}`...")


    result = install_single_library(library_name)
    bot.send_message(message.chat.id, result)

@bot.callback_query_handler(func=lambda call: call.data == 'broadcast')
def broadcast_callback(call):
    if call.from_user.id == ADMIN_ID:
        bot.send_message(call.message.chat.id, "أرسل الرسالة التي تريد إذاعتها:")
        bot.register_next_step_handler(call.message, process_broadcast_message)
    else:
        bot.send_message(call.message.chat.id, "⚠️ أنت لست المطور.")

def process_broadcast_message(message):
    if message.from_user.id == ADMIN_ID:
        broadcast_message = message.text
        success_count = 0
        fail_count = 0

        for user_id in active_users:
            try:
                bot.send_message(user_id, broadcast_message)
                success_count += 1
            except Exception as e:
                logger.error(f"فشل في إرسال الرسالة إلى المستخدم {user_id}: {e}")
                fail_count += 1

        bot.send_message(message.chat.id, f"✅ تم إرسال الرسالة إلى {success_count} مستخدم.\n❌ فشل إرسال الرسالة إلى {fail_count} مستخدم.")
    else:
        bot.send_message(message.chat.id, "⚠️ أنت لست المطور.")

@bot.callback_query_handler(func=lambda call: call.data == 'speed')
def bot_speed_info(call):
    try:
        start_time = time.time()
        response = requests.get(f'https://api.telegram.org/bot{TOKEN}/getMe')
        latency = time.time() - start_time
        if response.ok:
            bot.send_message(call.message.chat.id, f"⚡ سرعة البوت: {latency:.2f} ثانية.")
        else:
            bot.send_message(call.message.chat.id, "⚠️ فشل في الحصول على سرعة البوت.")
    except Exception as e:
        logger.error(f"حدث خطأ أثناء فحص سرعة البوت: {e}")
        bot.send_message(call.message.chat.id, f"❌ حدث خطأ أثناء فحص سرعة البوت: {e}")


def ask_to_upload_file(message):
    """استدعاء من الأمر /upload"""
    user_id = message.from_user.id
    
    if user_id in banned_users:
        bot.send_message(message.chat.id, "⛔ أنت محظور من استخدام هذا البوت.")
        return
    
    if bot_locked:
        bot.send_message(message.chat.id, "⚠️ البوت مقفل حالياً.")
        return
    
    if not is_user_subscribed_to_channel(user_id):
        markup = types.InlineKeyboardMarkup()
        channel_button = types.InlineKeyboardButton('انضم إلى القناة', url=f'https://t.me/{CHANNEL_USERNAME[1:]}')
        check_button = types.InlineKeyboardButton('✅ تحقق من الاشتراك', callback_data='check_subscription')
        markup.add(channel_button, check_button)
        bot.send_message(message.chat.id, "⚠️ يجب عليك الانضمام إلى قناتنا أولاً.", reply_markup=markup)
        return
    
    if free_mode or (user_id in user_subscriptions and user_subscriptions[user_id]['expiry'] > datetime.now()):
        bot.send_message(message.chat.id, "📄 من فضلك، أرسل الملف الذي تريد رفعه (ملف .py أو .zip)")
    else:
        bot.send_message(message.chat.id, "⚠️ يجب عليك الاشتراك لاستخدام هذه الميزة.")


@bot.callback_query_handler(func=lambda call: call.data == 'active_bots')
def show_active_bots_panel(call):
    """عرض لوحة البوتات النشطة للادمن - جميع البوتات في مجلد active_bots"""
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "⚠️ هذا القسم للمطور فقط", show_alert=True)
        return

    try:
        # 🔄 التعديل هنا: فحص مجلد active_bots بدلاً من bot_scripts فقط
        if not os.path.exists(ACTIVE_BOTS_DIR):
            bot.send_message(call.message.chat.id, "📭 مجلد البوتات النشطة غير موجود")
            return

        # جلب جميع المجلدات في ACTIVE_BOTS_DIR
        bot_folders = [f for f in os.listdir(ACTIVE_BOTS_DIR)
                      if os.path.isdir(os.path.join(ACTIVE_BOTS_DIR, f))]

        if not bot_folders:
            bot.send_message(call.message.chat.id, "📭 لا توجد بوتات مخزنة")
            return

        # إرسال رسالة التحميل
        status_msg = bot.send_message(call.message.chat.id, f"🔍 جاري فحص {len(bot_folders)} بوت...")

        # عد البوتات حسب الحالة
        running_bots = 0
        stopped_bots = 0
        crashed_bots = 0
        all_bots_info = {}  # لتخزين معلومات كل البوتات

        for bot_folder in bot_folders:
            try:
                bot_folder_path = os.path.join(ACTIVE_BOTS_DIR, bot_folder)
                
                # استخراج معلومات من اسم المجلد
                parts = bot_folder.split('_')
                if len(parts) >= 3:
                    folder_user_id = int(parts[1])
                    file_name = '_'.join(parts[2:]) + '.py'
                    
                    # تحديد حالة البوت
                    status = 'stopped'
                    if folder_user_id in bot_scripts:
                        bot_info = bot_scripts[folder_user_id]
                        if bot_info.get('bot_folder_name') == bot_folder:
                            status = bot_info.get('status', 'stopped')
                    
                    # تحديث العدادات
                    if status == 'running':
                        running_bots += 1
                    elif status == 'crashed':
                        crashed_bots += 1
                    else:
                        stopped_bots += 1
                    
                    # البحث عن ملف البايثون الرئيسي
                    py_files = [f for f in os.listdir(bot_folder_path) if f.endswith('.py')]
                    main_script = py_files[0] if py_files else 'غير معروف'
                    script_path = os.path.join(bot_folder_path, main_script) if py_files else ''
                    
                    # محاولة استخراج توكن البوت
                    bot_username = "غير متاح"
                    if script_path and os.path.exists(script_path):
                        token = extract_token_from_script(script_path)
                        if token:
                            try:
                                bot_info_api = requests.get(f'https://api.telegram.org/bot{token}/getMe').json()
                                if bot_info_api.get('ok'):
                                    bot_username = f"@{bot_info_api['result']['username']}"
                            except:
                                pass
                    
                    # الحصول على معلومات المستخدم
                    try:
                        user_info = bot.get_chat(folder_user_id)
                        user_name = user_info.first_name or "بدون اسم"
                        user_username = f"@{user_info.username}" if user_info.username else "بدون يوزر"
                    except:
                        user_name = "غير متاح"
                        user_username = "غير متاح"
                    
                    # تخزين المعلومات
                    all_bots_info[bot_folder] = {
                        'user_id': folder_user_id,
                        'file_name': file_name,
                        'status': status,
                        'bot_username': bot_username,
                        'user_name': user_name,
                        'user_username': user_username,
                        'folder_path': bot_folder_path,
                        'script_path': script_path,
                        'folder_name': bot_folder
                    }
                    
            except Exception as e:
                logger.error(f"خطأ في معالجة مجلد {bot_folder}: {e}")
                continue

        # إعداد الإحصائيات
        stats_msg = f"""
📊 إحصائيات البوتات المخزنة:

🤖 إجمالي البوتات: {len(bot_folders)}
🟢 قيد التشغيل: {running_bots}
🔴 متوقفة: {stopped_bots}
⚫ معطلة: {crashed_bots}

────────────────
"""

        # إرسال الإحصائيات أولاً
        bot.edit_message_text(stats_msg, status_msg.chat.id, status_msg.message_id, parse_mode='HTML')

        # إرسال كل بوت على حدة مع أزرار التحكم
        for bot_folder, bot_info in all_bots_info.items():
            try:
                # إعداد نص البوت
                bot_msg = f"""
🤖 معلومات البوت:

📁 المجلد: `{bot_folder}`
📄 الملف: `{bot_info['file_name']}`
🆔 المستخدم: `{bot_info['user_id']}`
👤 الاسم: {bot_info['user_name']}
📌 اليوزر: {bot_info['user_username']}
🤖 يوزر البوت: {bot_info['bot_username']}
🟢 الحالة: `{bot_info['status']}`
────────────────
"""

                # إنشاء أزرار التحكم
                markup = types.InlineKeyboardMarkup()
                
                # أزرار التحكم بالحالة
                if bot_info['status'] == 'running':
                    stop_button = types.InlineKeyboardButton('⏹️ إيقاف', 
                        callback_data=f'stop_{bot_info["user_id"]}_{bot_info["file_name"]}')
                    markup.add(stop_button)
                else:
                    start_button = types.InlineKeyboardButton('▶️ تشغيل', 
                        callback_data=f'start_{bot_info["user_id"]}_{bot_info["file_name"]}')
                    markup.add(start_button)
                
                # زر الحذف
                delete_button = types.InlineKeyboardButton('🗑️ حذف', 
                    callback_data=f'delete_{bot_info["user_id"]}_{bot_info["file_name"]}')
                markup.add(delete_button)
                
                # زر معلومات إضافية
                info_button = types.InlineKeyboardButton('ℹ️ معلومات', 
                    callback_data=f'info_{bot_info["user_id"]}_{bot_info["file_name"]}')
                markup.add(info_button)

                # إرسال رسالة البوت
                bot.send_message(
                    call.message.chat.id,
                    bot_msg,
                    reply_markup=markup,
                    parse_mode='HTML'
                )

            except Exception as e:
                logger.error(f"خطأ في عرض بوت {bot_folder}: {e}")
                continue

        # إرسال رسالة التلخيص النهائية
        summary_msg = f"""
✅ تم عرض جميع البوتات المخزنة

📋 الملخص النهائي:
• تم عرض {len(all_bots_info)} بوت من أصل {len(bot_folders)}
• 🟢 {running_bots} بوت قيد التشغيل
• 🔴 {stopped_bots} بوت متوقف
• ⚫ {crashed_bots} بوت معطل

🛠 يمكنك التحكم بكل بوت من خلال الأزرار أسفل كل رسالة.
"""
        bot.send_message(call.message.chat.id, summary_msg)

        # زر الرجوع للقائمة الرئيسية
        back_markup = types.InlineKeyboardMarkup()
        back_button = types.InlineKeyboardButton('🔙 رجوع للقائمة', callback_data='back_to_menu')
        back_markup.add(back_button)
        bot.send_message(call.message.chat.id, "🔄 العودة للقائمة الرئيسية:", reply_markup=back_markup)

    except Exception as e:
        logger.error(f"خطأ في عرض البوتات النشطة: {e}")
        bot.send_message(call.message.chat.id, f"❌ حدث خطأ في عرض البوتات: {str(e)[:200]}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('info_'))
def show_bot_info(call):
    """عرض معلومات مفصلة عن البوت"""
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "⚠️ هذا القسم للمطور فقط", show_alert=True)
        return
    
    try:
        _, target_chat_id, file_name = call.data.split('_', 2)
        target_chat_id = int(target_chat_id)
        
        if target_chat_id not in bot_scripts:
            bot.answer_callback_query(call.id, "❌ البوت غير موجود", show_alert=True)
            return
        
        bot_info = bot_scripts[target_chat_id]
        
        # جمع المعلومات
        status = bot_info.get('status', 'unknown')
        folder_path = bot_info.get('folder_path', 'غير معروف')
        script_path = bot_info.get('script_path', 'غير معروف')
        start_time = bot_info.get('start_time', 'غير معروف')
        
        if isinstance(start_time, datetime):
            start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
            uptime = datetime.now() - start_time
            uptime_str = f"{uptime.days} يوم, {uptime.seconds // 3600} ساعة, {(uptime.seconds % 3600) // 60} دقيقة"
        else:
            start_time_str = str(start_time)
            uptime_str = "غير متاح"
        
        # معلومات المستخدم
        user_name, user_username = get_user_info(target_chat_id)
        
        # معلومات البوت
        bot_username = "غير متاح"
        token = extract_token_from_script(script_path) if os.path.exists(script_path) else None
        if token:
            try:
                bot_info_api = requests.get(f'https://api.telegram.org/bot{token}/getMe').json()
                if bot_info_api.get('ok'):
                    bot_username = f"@{bot_info_api['result']['username']}"
            except:
                pass
        
        # حجم المجلد
        folder_size = "غير متاح"
        if os.path.exists(folder_path):
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(folder_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total_size += os.path.getsize(fp)
            folder_size = f"{total_size / 1024:.2f} KB"
        
        # إعداد الرسالة
        info_msg = f"""
🔍 معلومات مفصلة عن البوت:

📄 اسم الملف: `{file_name}`
🆔 معرف المستخدم: `{target_chat_id}`
👤 اسم المستخدم: {user_name}
📌 يوزر المستخدم: {user_username}
🤖 يوزر البوت: {bot_username}
📁 مسار المجلد: `{folder_path}`
📊 حجم المجلد: {folder_size}
🟢 الحالة: `{status}`
⏰ وقت البدء: {start_time_str}
⏳ مدة التشغيل: {uptime_str}
📝 مسار السكريبت: `{script_path}`
────────────────
"""
        
        # أزرار التحكم
        markup = types.InlineKeyboardMarkup()
        
        # أزرار الإجراءات
        if status == 'running':
            stop_button = types.InlineKeyboardButton('⏹️ إيقاف', callback_data=f'stop_{target_chat_id}_{file_name}')
            markup.add(stop_button)
        else:
            start_button = types.InlineKeyboardButton('▶️ تشغيل', callback_data=f'start_{target_chat_id}_{file_name}')
            markup.add(start_button)
        
        delete_button = types.InlineKeyboardButton('🗑️ حذف', callback_data=f'delete_{target_chat_id}_{file_name}')
        markup.add(delete_button)
        
        # أزرار التنقل
        refresh_button = types.InlineKeyboardButton('🔄 تحديث', callback_data=f'info_{target_chat_id}_{file_name}')
        back_button = types.InlineKeyboardButton('🔙 رجوع', callback_data='active_bots')
        markup.add(refresh_button, back_button)
        
        # إرسال الرسالة
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=info_msg,
                reply_markup=markup,
                parse_mode='HTML'
            )
        except:
            bot.send_message(
                call.message.chat.id,
                info_msg,
                reply_markup=markup,
                parse_mode='HTML'
            )
        
    except Exception as e:
        logger.error(f"خطأ في عرض معلومات البوت: {e}")
        bot.answer_callback_query(call.id, f"❌ حدث خطأ: {str(e)[:50]}", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == 'subscription')
def subscription_menu(call):
    if call.from_user.id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup()
        add_subscription_button = types.InlineKeyboardButton('➕ إضافة اشتراك', callback_data='add_subscription')
        remove_subscription_button = types.InlineKeyboardButton('➖ إزالة اشتراك', callback_data='remove_subscription')
        markup.add(add_subscription_button, remove_subscription_button)
        bot.send_message(call.message.chat.id, "اختر الإجراء الذي تريد تنفيذه:", reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, "⚠️ أنت لست المطور.")

@bot.callback_query_handler(func=lambda call: call.data == 'stats')
def stats_menu(call):
    if call.from_user.id == ADMIN_ID:
        total_files = sum(len(files) for files in user_files.values())
        total_users = len(user_files)
        active_users_count = len(active_users)
        banned_users_count = len(banned_users)
        bot.send_message(call.message.chat.id, f"📊 الإحصائيات:\n\n📂 عدد الملفات المرفوعة: {total_files}\n👤 عدد المستخدمين: {total_users}\n👥 المستخدمين النشطين: {active_users_count}\n🚫 المستخدمين المحظورين: {banned_users_count}")
    else:
        bot.send_message(call.message.chat.id, "⚠️ أنت لست المطور.")

@bot.callback_query_handler(func=lambda call: call.data == 'add_subscription')
def add_subscription_callback(call):
    if call.from_user.id == ADMIN_ID:
        bot.send_message(call.message.chat.id, "أرسل معرف المستخدم وعدد الأيام بالشكل التالي:\n/add_subscription <user_id> <days>")
    else:
        bot.send_message(call.message.chat.id, "⚠️ أنت لست المطور.")

@bot.callback_query_handler(func=lambda call: call.data == 'remove_subscription')
def remove_subscription_callback(call):
    if call.from_user.id == ADMIN_ID:
        bot.send_message(call.message.chat.id, "أرسل معرف المستخدم بالشكل التالي:\n/remove_subscription <user_id>")
    else:
        bot.send_message(call.message.chat.id, "⚠️ أنت لست المطور.")

@bot.callback_query_handler(func=lambda call: call.data == 'ban_user')
def ban_user_callback(call):
    if call.from_user.id == ADMIN_ID:
        bot.send_message(call.message.chat.id, "أرسل معرف المستخدم وسبب الحظر بالشكل التالي:\n/ban <user_id> <reason>")
    else:
        bot.send_message(call.message.chat.id, "⚠️ أنت لست المطور.")

@bot.callback_query_handler(func=lambda call: call.data == 'unban_user')
def unban_user_callback(call):
    if call.from_user.id == ADMIN_ID:
        bot.send_message(call.message.chat.id, "أرسل معرف المستخدم بالشكل التالي:\n/unban <user_id>")
    else:
        bot.send_message(call.message.chat.id, "⚠️ أنت لست المطور.")

@bot.message_handler(commands=['add_subscription'])
def add_subscription(message):
    if message.from_user.id == ADMIN_ID:
        try:
            user_id = int(message.text.split()[1])
            days = int(message.text.split()[2])
            expiry_date = datetime.now() + timedelta(days=days)
            user_subscriptions[user_id] = {'expiry': expiry_date}
            save_subscription(user_id, expiry_date)
            bot.send_message(message.chat.id, f"✅ تمت إضافة اشتراك لمدة {days} أيام للمستخدم {user_id}.")
            bot.send_message(user_id, f"🎉 تم تفعيل الاشتراك لك لمدة {days} أيام. يمكنك الآن استخدام البوت!")
        except Exception as e:
            logger.error(f"حدث خطأ أثناء إضافة اشتراك: {e}")
            bot.send_message(message.chat.id, f"❌ حدث خطأ: {e}")
    else:
        bot.send_message(message.chat.id, "⚠️ أنت لست المطور.")

@bot.message_handler(commands=['remove_subscription'])
def remove_subscription(message):
    if message.from_user.id == ADMIN_ID:
        try:
            user_id = int(message.text.split()[1])
            if user_id in user_subscriptions:
                del user_subscriptions[user_id]
                remove_subscription_db(user_id)
                bot.send_message(message.chat.id, f"✅ تم إزالة الاشتراك للمستخدم {user_id}.")
                bot.send_message(user_id, "⚠️ تم إزالة اشتراكك. لم يعد بإمكانك استخدام البوت.")
            else:
                bot.send_message(message.chat.id, f"⚠️ المستخدم {user_id} ليس لديه اشتراك.")
        except Exception as e:
            logger.error(f"حدث خطأ أثناء إزالة اشتراك: {e}")
            bot.send_message(message.chat.id, f"❌ حدث خطأ: {e}")
    else:
        bot.send_message(message.chat.id, "⚠️ أنت لست المطور.")

@bot.message_handler(commands=['user_files'])
def show_user_files(message):
    if message.from_user.id == ADMIN_ID:
        try:
            user_id = int(message.text.split()[1])
            if user_id in user_files:
                files_list = "\n".join(user_files[user_id])
                bot.send_message(message.chat.id, f"📂 الملفات التي رفعها المستخدم {user_id}:\n{files_list}")
            else:
                bot.send_message(message.chat.id, f"⚠️ المستخدم {user_id} لم يرفع أي ملفات.")
        except Exception as e:
            logger.error(f"حدث خطأ أثناء عرض ملفات المستخدم: {e}")
            bot.send_message(message.chat.id, f"❌ حدث خطأ: {e}")
    else:
        bot.send_message(message.chat.id, "⚠️ أنت لست المطور.")

@bot.message_handler(commands=['lock'])
def lock_bot(message):
    if message.from_user.id == ADMIN_ID:
        global bot_locked
        bot_locked = True
        bot.send_message(message.chat.id, "🔒 تم قفل البوت.")
    else:
        bot.send_message(message.chat.id, "⚠️ أنت لست المطور.")

@bot.message_handler(commands=['unlock'])
def unlock_bot(message):
    if message.from_user.id == ADMIN_ID:
        global bot_locked
        bot_locked = False
        bot.send_message(message.chat.id, "🔓 تم فتح البوت.")
    else:
        bot.send_message(message.chat.id, "⚠️ أنت لست المطور.")

@bot.callback_query_handler(func=lambda call: call.data == 'lock_bot')
def lock_bot_callback(call):
    if call.from_user.id == ADMIN_ID:
        global bot_locked
        bot_locked = True
        bot.send_message(call.message.chat.id, "🔒 تم قفل البوت.")
    else:
        bot.send_message(call.message.chat.id, "⚠️ أنت لست المطور.")

@bot.callback_query_handler(func=lambda call: call.data == 'unlock_bot')
def unlock_bot_callback(call):
    if call.from_user.id == ADMIN_ID:
        global bot_locked
        bot_locked = False
        bot.send_message(call.message.chat.id, "🔓 تم فتح البوت.")
    else:
        bot.send_message(call.message.chat.id, "⚠️ أنت لست المطور.")

@bot.callback_query_handler(func=lambda call: call.data == 'free_mode')
def toggle_free_mode(call):
    if call.from_user.id == ADMIN_ID:
        global free_mode
        free_mode = not free_mode
        status = "مفتوح" if free_mode else "مغلق"
        bot.send_message(call.message.chat.id, f"🔓 تم تغيير وضع البوت بدون اشتراك إلى: {status}.")
    else:
        bot.send_message(call.message.chat.id, "⚠️ أنت لست المطور.")

@bot.message_handler(commands=['ban'])
def ban_user_command(message):
    if message.from_user.id == ADMIN_ID:
        try:
            parts = message.text.split(maxsplit=2)
            if len(parts) < 3:
                bot.send_message(message.chat.id, "⚠️ الصيغة الصحيحة: /ban <user_id> <reason>")
                return

            user_id = int(parts[1])
            reason = parts[2]

            ban_user(user_id, reason)
            bot.send_message(message.chat.id, f"✅ تم حظر المستخدم {user_id} بسبب: {reason}")
            try:
                bot.send_message(user_id, f"⛔ تم حظرك من استخدام البوت بسبب: {reason}")
            except:
                pass
        except Exception as e:
            logger.error(f"حدث خطأ أثناء حظر المستخدم: {e}")
            bot.send_message(message.chat.id, f"❌ حدث خطأ: {e}")
    else:
        bot.send_message(message.chat.id, "⚠️ أنت لست المطور.")

@bot.message_handler(commands=['unban'])
def unban_user_command(message):
    if message.from_user.id == ADMIN_ID:
        try:
            user_id = int(message.text.split()[1])

            if unban_user(user_id):
                bot.send_message(message.chat.id, f"✅ تم إلغاء حظر المستخدم {user_id}")
                try:
                    bot.send_message(user_id, f"🎉 تم إلغاء الحظر عنك. يمكنك الآن استخدام البوت مرة أخرى.")
                except:
                    pass
            else:
                bot.send_message(message.chat.id, f"⚠️ المستخدم {user_id} غير محظور.")
        except Exception as e:
            logger.error(f"فشل في إلغاء حظر المستخدم: {e}")
            bot.send_message(message.chat.id, f"❌ حدث خطأ: {e}")
    else:
        bot.send_message(message.chat.id, "⚠️ أنت لست المطور.")


@bot.message_handler(content_types=['document'])
def handle_file(message):
    user_id = message.from_user.id

    if user_id in banned_users:
        bot.reply_to(message, "🚫 <b>حظر دائم</b>\n\n⚡ حسابك محظور من استخدام البوت\n📞 للاستفسار: @mora_330", parse_mode='HTML')
        return

    if bot_locked:
        bot.reply_to(message, "🔒 <b>البوت مغلق مؤقتاً</b>\n\n✨ جاري الصيانة، حاول لاحقاً", parse_mode='HTML')
        return

    if not is_user_subscribed_to_channel(user_id):
        markup = types.InlineKeyboardMarkup()
        channel_button = types.InlineKeyboardButton('📢 الانضمام للقناة', url=f'https://t.me/{CHANNEL_USERNAME[1:]}')
        check_button = types.InlineKeyboardButton('✅ التحقق', callback_data='check_subscription')
        markup.add(channel_button, check_button)
        
        bot.reply_to(message, 
            "🎯 <b>اشتراك مطلوب</b>\n\n"
            "📌 للوصول للخدمة، انضم أولاً لقناتنا\n"
            "✨ @mora_brt", 
            reply_markup=markup, 
            parse_mode='HTML'
        )
        return

    # تصميم بداية رائع
    status_msg = bot.reply_to(message, 
        "⚡ <b>جاري بدء المعالجة</b>\n"
        "━━━━━━━━━━━━━━━━\n"
        "🔄 <i>التجهيز...</i>\n"
        "⏳ <i>انتظر قليلاً...</i>", 
        parse_mode='HTML'
    )

    try:
        file_id = message.document.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_name = message.document.file_name

        # تحديث حالة التحميل
        bot.edit_message_text(
            f"📥 <b>تحميل الملف</b>\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📄 <b>الاسم:</b> <code>{file_name}</code>\n"
            f"📦 <b>الحجم:</b> <code>{len(downloaded_file) // 1024} KB</code>\n\n"
            f"⏳ <i>جارٍ التحميل...</i>",
            status_msg.chat.id, status_msg.message_id,
            parse_mode='HTML'
        )

        if not file_name.endswith('.py') and not file_name.endswith('.zip'):
            bot.edit_message_text(
                "❌ <b>نوع غير مدعوم</b>\n"
                "━━━━━━━━━━━━━━━━\n"
                "🎯 <b>يدعم فقط:</b>\n"
                "• ملفات بايثون <code>.py</code>\n"
                "• أرشيفات <code>.zip</code>\n\n"
                "✨ <i>غير ذلك مرفوض</i>",
                status_msg.chat.id, status_msg.message_id,
                parse_mode='HTML'
            )
            return

        temp_path = os.path.join(PENDING_BOTS_DIR, file_name)
        with open(temp_path, 'wb') as temp_file:
            temp_file.write(downloaded_file)

        # فحص الملف
        bot.edit_message_text(
            f"🔍 <b>فحص الملف</b>\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📄 <code>{file_name}</code>\n"
            f"⚙️ <i>جارٍ الفحص...</i>",
            status_msg.chat.id, status_msg.message_id,
            parse_mode='HTML'
        )

        required_libraries = []
        if file_name.endswith('.py'):
            required_libraries = extract_imports_from_file(temp_path)
        elif file_name.endswith('.zip'):
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file.endswith('.py'):
                            file_path = os.path.join(root, file)
                            required_libraries.extend(extract_imports_from_file(file_path))

        required_libraries = list(set(required_libraries))
        libs_count = len(required_libraries)

        # حالة خاصة للإدمن
        if user_id == ADMIN_ID:
            bot.edit_message_text(
                "👑 <b>وضع المطور</b>\n"
                "━━━━━━━━━━━━━━━━\n"
                f"📚 <b>المكتبات:</b> {libs_count}\n"
                f"⚡ <i>معالجة تلقائية...</i>",
                status_msg.chat.id, status_msg.message_id,
                parse_mode='HTML'
            )

            try:
                bot_folder_name = f"bot_{user_id}_{file_name.replace('.', '_').replace(' ', '_')}"
                bot_folder_path = os.path.join(ACTIVE_BOTS_DIR, bot_folder_name)

                if not os.path.exists(bot_folder_path):
                    os.makedirs(bot_folder_path)

                if required_libraries:
                    new_libs = filter_installed_libraries(required_libraries)
                    skipped_count = libs_count - len(new_libs)
                    
                    if skipped_count > 0:
                        bot.edit_message_text(
                            f"📚 <b>فحص المكتبات</b>\n"
                            f"━━━━━━━━━━━━━━━━\n"
                            f"✅ <b>مثبتة:</b> {skipped_count}\n"
                            f"🔧 <b>جديدة:</b> {len(new_libs)}\n"
                            f"⚡ <i>جارٍ التثبيت...</i>",
                            status_msg.chat.id, status_msg.message_id,
                            parse_mode='HTML'
                        )
                    
                    if new_libs:
                        bot.edit_message_text(
                            f"📦 <b>تثبيت جديد</b>\n"
                            f"━━━━━━━━━━━━━━━━\n"
                            f"🔧 <b>المطلوب:</b> {len(new_libs)}\n"
                            f"✨ <code>{', '.join(new_libs[:3])}{'...' if len(new_libs) > 3 else ''}</code>",
                            status_msg.chat.id, status_msg.message_id,
                            parse_mode='HTML'
                        )
                        
                        results = install_libraries(new_libs)
                        success_count = len([r for r in results if '✅' in r])
                        
                        bot.edit_message_text(
                            f"✅ <b>تم التثبيت</b>\n"
                            f"━━━━━━━━━━━━━━━━\n"
                            f"📊 <b>النتيجة:</b>\n"
                            f"• ✅ نجاح: {success_count}\n"
                            f"• ❌ فشل: {len(new_libs) - success_count}\n"
                            f"• ⏭️ متخطى: {skipped_count}",
                            status_msg.chat.id, status_msg.message_id,
                            parse_mode='HTML'
                        )
                    else:
                        bot.edit_message_text(
                            f"✅ <b>كل شيء مثبت</b>\n"
                            f"━━━━━━━━━━━━━━━━\n"
                            f"📚 <b>المكتبات:</b> {libs_count}\n"
                            f"✨ <i>كلها جاهزة</i>",
                            status_msg.chat.id, status_msg.message_id,
                            parse_mode='HTML'
                        )

                if file_name.endswith('.zip'):
                    with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                        zip_ref.extractall(bot_folder_path)
                    py_files = [f for f in os.listdir(bot_folder_path) if f.endswith('.py')]
                    if py_files:
                        main_script = py_files[0]
                        final_script_path = os.path.join(bot_folder_path, main_script)
                    else:
                        bot.edit_message_text(
                            "❌ <b>خطأ في الأرشيف</b>\n"
                            "━━━━━━━━━━━━━━━━\n"
                            "📭 لا يوجد ملفات بايثون\n"
                            "🔍 تأكد من المحتوى",
                            status_msg.chat.id, status_msg.message_id,
                            parse_mode='HTML'
                        )
                        return
                else:
                    final_script_path = os.path.join(bot_folder_path, file_name)
                    shutil.copy2(temp_path, final_script_path)

                run_script_from_approval(final_script_path, user_id, bot_folder_path, file_name, message)
                
                bot.edit_message_text(
                    "🎉 <b>تم بنجاح!</b>\n"
                    "━━━━━━━━━━━━━━━━\n"
                    f"🤖 <b>الملف:</b> <code>{file_name}</code>\n"
                    f"📁 <b>المجلد:</b> <code>{bot_folder_name}</code>\n"
                    f"📚 <b>المكتبات:</b> {libs_count}\n\n"
                    f"✨ <i>يمكنك التحكم من القائمة</i>",
                    status_msg.chat.id, status_msg.message_id,
                    parse_mode='HTML'
                )

                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return

            except Exception as e:
                logger.error(f"❌ فشل في معالجة ملف الإدمن: {e}")
                bot.edit_message_text(
                    f"💥 <b>حدث خطأ</b>\n"
                    f"━━━━━━━━━━━━━━━━\n"
                    f"❌ <code>فشل العملية</code>\n\n"
                    f"🔧 <b>السبب:</b>\n<code>{str(e)[:150]}</code>\n\n"
                    f"📞 <i>اتصل بالدعم</i>",
                    status_msg.chat.id, status_msg.message_id,
                    parse_mode='HTML'
                )
                return

        # للمستخدمين العاديين
        user_info = f"@{message.from_user.username}" if message.from_user.username else f"ID: {user_id}"
        user_name = message.from_user.first_name or "مجهول"
        
        new_libs = filter_installed_libraries(required_libraries) if required_libraries else []
        skipped_count = libs_count - len(new_libs) if required_libraries else 0
        
        bot.edit_message_text(
            "📤 <b>تم الرفع</b>\n"
            "━━━━━━━━━━━━━━━━\n"
            f"👤 <b>المستخدم:</b> {user_name}\n"
            f"📄 <b>الملف:</b> <code>{file_name}</code>\n"
            f"📦 <b>المكتبات:</b> {libs_count or 'لا يوجد'}\n"
            f"⏭️ <b>جاهزة:</b> {skipped_count}\n"
            f"🔧 <b>جديدة:</b> {len(new_libs)}\n\n"
            "⏳ <i>بانتظار المراجعة...</i>\n"
            "🔔 <i>سيتم إشعارك</i>",
            status_msg.chat.id, status_msg.message_id,
            parse_mode='HTML'
        )

        pending_approvals[(user_id, file_name)] = {
            'temp_path': temp_path, 
            'libraries': required_libraries,
            'new_libraries': new_libs,
            'skipped_count': skipped_count
        }
        save_pending_upload(user_id, file_name, temp_path, required_libraries)

        # طلب موافقة للأدمن بتصميم رايق
        approval_html = f"""
🎯 <b>طلب رفع جديد</b>
━━━━━━━━━━━━━━━━

👤 <b>المستخدم:</b> {user_name}
📌 <b>اليوزر:</b> {user_info}
🆔 <b>ID:</b> <code>{user_id}</code>

📄 <b>الملف:</b> <code>{file_name}</code>
📊 <b>الحجم:</b> {len(downloaded_file) // 1024} KB
📚 <b>المكتبات:</b> {libs_count}

✨ <b>التفاصيل:</b>
✅ <i>جاهزة:</i> {skipped_count}
🔧 <i>جديدة:</i> {len(new_libs)}

━━━━━━━━━━━━━━━━
🎮 <i>اختر الإجراء المناسب:</i>
        """
        
        # أزرار بتصميم جميل
        markup = types.InlineKeyboardMarkup(row_width=2)
        approve_button = types.InlineKeyboardButton('✅ تشغيل', callback_data=f'approve_{user_id}_{file_name}')
        reject_button = types.InlineKeyboardButton('❌ رفض', callback_data=f'reject_{user_id}_{file_name}')
        preview_button = types.InlineKeyboardButton('👁️ معاينة', callback_data=f'preview_{user_id}_{file_name}')
        info_button = types.InlineKeyboardButton('📊 معلومات', callback_data=f'libs_info_{user_id}_{file_name}')
        
        markup.add(approve_button, reject_button)
        markup.add(preview_button, info_button)

        # إرسال الملف
        with open(temp_path, 'rb') as file:
            bot.send_document(
                ADMIN_ID, 
                file, 
                caption=approval_html,
                reply_markup=markup,
                parse_mode='HTML'
            )

    except Exception as e:
        logger.error(f"❌ فشل في معالجة الملف: {e}")
        bot.edit_message_text(
            f"💥 <b>خطأ غير متوقع</b>\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"❌ <code>فشل المعالجة</code>\n\n"
            f"🔧 <b>الخطأ:</b>\n<code>{str(e)[:120]}</code>\n\n"
            f"📞 <i>اتصل بالدعم</i>",
            status_msg.chat.id, status_msg.message_id,
            parse_mode='HTML'
        )

@bot.message_handler(func=lambda message: message.from_user.id in globals().get('token_changes', {}))
def handle_token_change(message):
    """معالجة تغيير التوكن"""
    user_id = message.from_user.id
    token_changes = globals().get('token_changes', {})
    
    if user_id not in token_changes:
        return
    
    file_name = token_changes[user_id]['file_name']
    new_token = message.text.strip()
    
    # التحقق من صحة التوكن
    token_pattern = r'^\d{9,10}:[A-Za-z0-9_-]{35}$'
    
    if not re.match(token_pattern, new_token):
        bot.send_message(
            user_id,
            "❌ توكن غير صالح\n\n"
            "يجب أن يكون التوكن على الشكل:\n"
            "`1234567890:ABCdefGHIjklMNopQRstUVwxyz`\n\n"
            "يرجى إرسال توكن صحيح:",
            parse_mode='HTML'
        )
        return
    
    # البحث عن البوت
    if user_id not in bot_scripts or bot_scripts[user_id].get('file_name') != file_name:
        bot.send_message(user_id, "❌ البوت غير موجود أو غير نشط")
        del token_changes[user_id]
        return
    
    try:
        script_path = bot_scripts[user_id].get('script_path', '')
        folder_path = bot_scripts[user_id].get('folder_path', '')
        
        if not os.path.exists(script_path):
            bot.send_message(user_id, "❌ ملف البوت غير موجود")
            del token_changes[user_id]
            return
        
        # 1. قراءة المحتوى
        with open(script_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # 2. البحث عن التوكن القديم
        old_token = extract_token_from_script(script_path)
        if not old_token:
            bot.send_message(user_id, "❌ لم أتمكن من العثور على التوكن القديم")
            del token_changes[user_id]
            return
        
        # 3. استبدال التوكن
        content = content.replace(old_token, new_token)
        
        # 4. حفظ الملف
        with open(script_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
        # 5. إيقاف البوت إذا كان يعمل
        was_running = False
        if bot_scripts[user_id].get('status') == 'running':
            was_running = True
            stop_bot_completely(user_id)
            time.sleep(2)
        
        # 6. إعادة تشغيل البوت
        if was_running:
            if restart_bot(user_id):
                status_msg = "وإعادة التشغيل"
            else:
                status_msg = "ولكن فشل إعادة التشغيل"
        else:
            status_msg = "ولكن البوت متوقف"
        
        # 7. إرسال رسالة التأكيد
        success_msg = f"""
✅ تم تغيير التوكن بنجاح {status_msg}

📄 البوت: `{file_name}`
🔄 الحالة: {'🟢 يعمل' if was_running and bot_scripts[user_id].get('status') == 'running' else '🔴 متوقف'}

🤖 يمكنك التحقق من عمل البوت بالتوكن الجديد.
"""
        
        bot.send_message(user_id, success_msg, parse_mode='HTML')
        
        # 8. تحديث واجهة التحكم
        try:
            # إرسال رسالة جديدة مع الأزرار المحدثة
            status = bot_scripts[user_id].get('status', 'stopped') if user_id in bot_scripts else 'stopped'
            markup = create_bot_control_markup(user_id, file_name, status)
            
            update_msg = f"""
🔄 تم تحديث معلومات البوت

📄 البوت: `{file_name}`
🟢 الحالة: `{status}`
✅ تم تغيير التوكن بنجاح
"""
            
            bot.send_message(user_id, update_msg, reply_markup=markup, parse_mode='HTML')
        except:
            pass
        
    except Exception as e:
        logger.error(f"خطأ في تغيير التوكن: {e}")
        bot.send_message(
            user_id,
            f"❌ خطأ في تغيير التوكن\n\n"
            f"فشل العملية: {str(e)[:100]}",
            parse_mode='HTML'
        )
    
    # 9. حذف حالة التغيير
    if user_id in token_changes:
        del token_changes[user_id]

def create_admin_control_markup(chat_id, file_name, status):
    """إنشاء أزرار تحكم ديناميكية للأدمن"""
    markup = types.InlineKeyboardMarkup()

    # إضافة زر المزيد من المعلومات
    info_button = types.InlineKeyboardButton('ℹ️ معلومات', callback_data=f'info_{chat_id}_{file_name}')
    markup.add(info_button)
    
    if status == 'running':
        stop_button = types.InlineKeyboardButton(f"⏹️ إيقاف {file_name}", callback_data=f'stop_{chat_id}_{file_name}')
        delete_button = types.InlineKeyboardButton(f"🗑️ حذف {file_name}", callback_data=f'delete_{chat_id}_{file_name}')
        markup.add(stop_button, delete_button)
    else:
        start_button = types.InlineKeyboardButton(f"▶️ تشغيل {file_name}", callback_data=f'start_{chat_id}_{file_name}')
        delete_button = types.InlineKeyboardButton(f"🗑️ حذف {file_name}", callback_data=f'delete_{chat_id}_{file_name}')
        markup.add(start_button, delete_button)
    
    # إضافة زر الرجوع
    back_button = types.InlineKeyboardButton('🔙 رجوع', callback_data='active_bots')
    markup.add(back_button)

    return markup

def create_user_bot_controls(user_id, file_name, status):
    """إنشاء أزرار تحكم للبوتات للمستخدم"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # أزرار التشغيل/الإيقاف
    if status == 'running':
        stop_button = types.InlineKeyboardButton('⏹️ إيقاف', callback_data=f'user_stop_{file_name}')
        markup.add(stop_button)
    else:
        start_button = types.InlineKeyboardButton('▶️ تشغيل', callback_data=f'user_start_{file_name}')
        markup.add(start_button)
    
    # أزرار إضافية
    delete_button = types.InlineKeyboardButton('🗑️ حذف', callback_data=f'user_delete_{file_name}')
    change_token_button = types.InlineKeyboardButton('🔑 تغيير التوكن', callback_data=f'user_token_{file_name}')
    download_button = types.InlineKeyboardButton('📥 تحميل', callback_data=f'user_download_{file_name}')
    
    markup.add(delete_button, change_token_button)
    markup.add(download_button)
    
    return markup

def create_user_control_markup(chat_id, file_name, status):
    """إنشاء أزرار تحكم ديناميكية للمستخدم"""
    markup = types.InlineKeyboardMarkup()

    if status == 'running':

        stop_button = types.InlineKeyboardButton(f"⏹️ إيقاف {file_name}", callback_data=f'stop_{chat_id}_{file_name}')
        markup.add(stop_button)
    else:

        start_button = types.InlineKeyboardButton(f"▶️ تشغيل {file_name}", callback_data=f'start_{chat_id}_{file_name}')
        markup.add(start_button)

    return markup
    
def run_script_from_approval(script_path, chat_id, folder_path, file_name, original_message):
    """تشغيل البوت بعد الموافقة (بدون إنشاء نسخ إضافية)"""
    try:

        bot_db_path = os.path.join(folder_path, f'bot_{chat_id}.db')


        modified_script_path = modify_bot_database_path(script_path, bot_db_path, folder_path)


        token_conflict = check_token_conflict(modified_script_path, chat_id, file_name)
        if token_conflict:
            bot.send_message(chat_id, "🔄 جاري إيقاف البوت القديم بنفس التوكن...")


        requirements_path = os.path.join(folder_path, 'requirements.txt')
        if os.path.exists(requirements_path):
            bot.send_message(chat_id, "🔄 جارٍ تثبيت المتطلبات...")
            subprocess.check_call(['pip', 'install', '-r', requirements_path])

        bot.send_message(chat_id, f"🚀 جارٍ تشغيل البوت {file_name}...")


        env = os.environ.copy()
        env["PYTHONPATH"] = folder_path


        process = subprocess.Popen(
            ['python3', modified_script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=folder_path
        )


        bot_scripts[chat_id] = {
            'process': process,
            'folder_path': folder_path,
            'file_name': file_name,
            'script_path': modified_script_path,
            'status': 'running',
            'start_time': datetime.now(),
            'bot_folder_name': os.path.basename(folder_path),
            'db_path': bot_db_path
        }

        token = extract_token_from_script(modified_script_path)
        if token:
            try:
                bot_info = requests.get(f'https://api.telegram.org/bot{token}/getMe').json()
                if bot_info.get('ok'):
                    bot_username = bot_info['result']['username']

                    user_info = f"@{original_message.from_user.username}" if original_message.from_user.username else str(original_message.from_user.id)
                    caption = f"📤 قام المستخدم {user_info} برفع ملف بوت جديد. معرف البوت: @{bot_username}"

                    if token_conflict:
                        caption += "\n⚠️ تم إيقاف البوت القديم بنفس التوكن تلقائياً"

                    bot.send_document(ADMIN_ID, open(modified_script_path, 'rb'), caption=caption)


                    admin_markup = create_admin_control_markup(chat_id, file_name, 'running')
                    status_msg = f"🤖 البوت {file_name} يعمل الآن\n📁 المجلد: {os.path.basename(folder_path)}"
                    if token_conflict:
                        status_msg += "\n⚠️ تم إيقاف البوت القديم بنفس التوكن"
                    bot.send_message(ADMIN_ID, status_msg, reply_markup=admin_markup)


                    user_markup = create_user_control_markup(chat_id, file_name, 'running')
                    user_status_msg = f"🤖 البوت {file_name} يعمل الآن\n📁 المجلد: {os.path.basename(folder_path)}"
                    if token_conflict:
                        user_status_msg += "\n⚠️ تم إيقاف البوت القديم بنفس التوكن"
                    bot.send_message(chat_id, user_status_msg, reply_markup=user_markup)

            except Exception as e:
                logger.error(f"فشل في التحقق من معرف البوت: {e}")
        else:
            user_info = f"@{original_message.from_user.username}" if original_message.from_user.username else str(original_message.from_user.id)
            caption = f"📤 قام المستخدم {user_info} برفع ملف بوت جديد، ولكن لم أتمكن من جلب معرف البوت."
            if token_conflict:
                caption += "\n⚠️ تم إيقاف البوت القديم بنفس التوكن تلقائياً"
            bot.send_document(ADMIN_ID, open(modified_script_path, 'rb'), caption=caption)


        threading.Thread(target=monitor_bot_process, args=(process, chat_id, file_name), daemon=True).start()

    except Exception as e:
        logger.error(f"فشل في تشغيل البوت: {e}")
        bot.send_message(chat_id, f"❌ حدث خطأ أثناء تشغيل البوت: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith(('approve_', 'reject_')))
def handle_approval(call):
    if call.from_user.id == ADMIN_ID:

        action, user_id, file_name = call.data.split('_', 2)
        user_id = int(user_id)
        file_key = (user_id, file_name)


        if file_key in pending_approvals:
            temp_path = pending_approvals[file_key]['temp_path']
            libraries = pending_approvals[file_key]['libraries']
        else:

            pending_uploads = load_pending_uploads()
            if file_key in pending_uploads:
                temp_path = pending_uploads[file_key]['temp_path']
                libraries = pending_uploads[file_key]['libraries']
                pending_approvals[file_key] = pending_uploads[file_key]
            else:
                bot.send_message(ADMIN_ID, "⚠️ انتهت صلاحية طلب الموافقة أو تم معالجته مسبقاً.")
                return

        if action == 'approve':
            try:

                if libraries:
                    bot.send_message(ADMIN_ID, f"📚 جاري تثبيت المكتبات المطلوبة للملف {file_name}...")
                    results = install_libraries(libraries)


                    success_count = len([r for r in results if '✅' in r])
                    bot.send_message(ADMIN_ID, f"✅ تم تثبيت {success_count} من {len(libraries)} مكتبة بنجاح")


                bot_folder_name = f"bot_{user_id}_{file_name.replace('.', '_').replace(' ', '_')}"
                bot_folder_path = os.path.join(ACTIVE_BOTS_DIR, bot_folder_name)

                if not os.path.exists(bot_folder_path):
                    os.makedirs(bot_folder_path)


                if file_name.endswith('.zip'):

                    with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                        zip_ref.extractall(bot_folder_path)


                    py_files = [f for f in os.listdir(bot_folder_path) if f.endswith('.py')]
                    if py_files:
                        main_script = py_files[0]
                        final_script_path = os.path.join(bot_folder_path, main_script)
                    else:
                        bot.send_message(ADMIN_ID, f"❌ لم يتم العثور على أي ملفات بايثون في الأرشيف.")
                        bot.send_message(user_id, "❌ لم يتم العثور على أي ملفات بايثون في الأرشيف.")
                        return
                else:

                    final_script_path = os.path.join(bot_folder_path, file_name)
                    shutil.copy2(temp_path, final_script_path)


                run_script_from_approval(final_script_path, user_id, bot_folder_path, file_name, call.message)


                if user_id not in user_files:
                    user_files[user_id] = []
                user_files[user_id].append(file_name)
                save_user_file(user_id, file_name)


                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    logger.info(f"✅ تم حذف الملف من pending_bots: {temp_path}")

                bot.send_message(ADMIN_ID, f"✅ تمت الموافقة على رفع الملف {file_name} للمستخدم {user_id}.")
                bot.send_message(user_id, f"⟣━✨✅ تمت الموافقة على رفع ملفك {file_name} وتم تشغيله بنجاح — وتم تفعيل الطلب بنظام ملكي ⚔️✨━⟢")

            except Exception as e:
                logger.error(f"❌ فشل في معالجة الملف بعد الموافقة: {e}")
                bot.send_message(ADMIN_ID, f"❌ فشل في معالجة الملف بعد الموافقة: {e}")
                bot.send_message(user_id, f"❌ حدث خطأ أثناء معالجة ملفك: {e}")
        else:

            if os.path.exists(temp_path):
                os.remove(temp_path)
                logger.info(f"✅ تم حذف الملف المرفوض من pending_bots: {temp_path}")
            bot.send_message(ADMIN_ID, f"❌ تم رفض رفع الملف {file_name} للمستخدم {user_id}.")
            bot.send_message(user_id, f"⟢⚡❌ تم رفض ملفك {file_name} يا عيل هكر كرتونة، أبعد عن البوت قبل ما ندفنك ديجيتالياً 👑💀⟣")


        if file_key in pending_approvals:
            del pending_approvals[file_key]
        remove_pending_upload(user_id, file_name)
    else:
        bot.send_message(call.message.chat.id, "⚠️ أنت لست المطور.")

def backup_installed_libraries():
    """نسخ احتياطي للمكتبات المثبتة"""
    try:
        import shutil
        backup_file = f'installed_libs_backup_{datetime.now().strftime("%Y%m%d")}.json'
        shutil.copy2('installed_libs.json', backup_file)
        logger.info(f"تم إنشاء نسخة احتياطية: {backup_file}")
        return backup_file
    except Exception as e:
        logger.error(f"فشل في النسخ الاحتياطي: {e}")
        return None

def run_script(script_path, chat_id, folder_path, file_name, original_message):
    try:

        token_conflict = check_token_conflict(script_path, chat_id, file_name)
        if token_conflict:
            bot.send_message(chat_id, "🔄 جاري إيقاف البوت القديم بنفس التوكن...")


        bot_folder_name = f"bot_{chat_id}_{file_name.replace('.', '_')}"
        bot_folder_path = os.path.join(ACTIVE_BOTS_DIR, bot_folder_name)

        if not os.path.exists(bot_folder_path):
            os.makedirs(bot_folder_path)


        if file_name.endswith('.zip'):

            with zipfile.ZipFile(script_path, 'r') as zip_ref:
                zip_ref.extractall(bot_folder_path)


            py_files = [f for f in os.listdir(bot_folder_path) if f.endswith('.py')]
            if py_files:
                main_script = py_files[0]
                final_script_path = os.path.join(bot_folder_path, main_script)
            else:
                raise Exception("لم يتم العثور على أي ملفات بايثون في الأرشيف")
        else:

            final_script_path = os.path.join(bot_folder_path, file_name)
            shutil.copy2(script_path, final_script_path)


        requirements_path = os.path.join(bot_folder_path, 'requirements.txt')
        if os.path.exists(requirements_path):
            bot.send_message(chat_id, "🔄 جارٍ تثبيت المتطلبات...")
            subprocess.check_call(['pip', 'install', '-r', requirements_path])

        bot.send_message(chat_id, f"🚀 جارٍ تشغيل البوت {file_name}...")

        env = os.environ.copy()
        env["PYTHONPATH"] = bot_folder_path

        process = subprocess.Popen(['python3', final_script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)


        bot_scripts[chat_id] = {
            'process': process,
            'folder_path': bot_folder_path,
            'file_name': file_name,
            'script_path': final_script_path,
            'status': 'running',
            'start_time': datetime.now(),
            'bot_folder_name': bot_folder_name
        }

        token = extract_token_from_script(final_script_path)
        if token:
            try:
                bot_info = requests.get(f'https://api.telegram.org/bot{token}/getMe').json()
                if bot_info.get('ok'):
                    bot_username = bot_info['result']['username']

                    user_info = f"@{original_message.from_user.username}" if original_message.from_user.username else str(original_message.from_user.id)
                    caption = f"📤 قام المستخدم {user_info} برفع ملف بوت جديد. معرف البوت: @{bot_username}"

                    if token_conflict:
                        caption += "\n⚠️ تم إيقاف البوت القديم بنفس التوكن تلقائياً"

                    bot.send_document(ADMIN_ID, open(final_script_path, 'rb'), caption=caption)


                    admin_markup = create_admin_control_markup(chat_id, file_name, 'running')
                    status_msg = f"🤖 البوت {file_name} يعمل الآن\n📁 المجلد: {bot_folder_name}"
                    if token_conflict:
                        status_msg += "\n⚠️ تم إيقاف البوت القديم بنفس التوكن"
                    bot.send_message(ADMIN_ID, status_msg, reply_markup=admin_markup)


                    user_markup = create_user_control_markup(chat_id, file_name, 'running')
                    user_status_msg = f"🤖 البوت {file_name} يعمل الآن\n📁 المجلد: {bot_folder_name}"
                    if token_conflict:
                        user_status_msg += "\n⚠️ تم إيقاف البوت القديم بنفس التوكن"
                    bot.send_message(chat_id, user_status_msg, reply_markup=user_markup)

                else:
                    bot.send_message(chat_id, f"✅ تم تشغيل البوت بنجاح! ولكن لم أتمكن من التحقق من معرف البوت.")
            except Exception as e:
                logger.error(f"فشل في التحقق من معرف البوت: {e}")
                bot.send_message(chat_id, f"✅ تم تشغيل البوت بنجاح! ولكن لم أتمكن من التحقق من معرف البوت.")
        else:
            bot.send_message(chat_id, f"✅ تم تشغيل البوت بنجاح! ولكن لم أتمكن من جلب معرف البوت.")
            user_info = f"@{original_message.from_user.username}" if original_message.from_user.username else str(original_message.from_user.id)
            caption = f"📤 قام المستخدم {user_info} برفع ملف بوت جديد، ولكن لم أتمكن من جلب معرف البوت."
            if token_conflict:
                caption += "\n⚠️ تم إيقاف البوت القديم بنفس التوكن تلقائياً"
            bot.send_document(ADMIN_ID, open(final_script_path, 'rb'), caption=caption)


        threading.Thread(target=monitor_bot_process, args=(process, chat_id, file_name), daemon=True).start()

    except Exception as e:
        logger.error(f"فشل في تشغيل البوت: {e}")
        bot.send_message(chat_id, f"❌ حدث خطأ أثناء تشغيل البوت: {e}")




def get_bot_status(chat_id, file_name):
    """الحصول على حالة البوت"""
    if chat_id in bot_scripts:
        script_info = bot_scripts[chat_id]
        if script_info.get('file_name') == file_name:
            return script_info.get('status', 'stopped')
    return 'stopped'
def monitor_bot_process(process, chat_id, file_name):
    """مراقبة عملية البوت وحذفه فوراً إذا توقف بسبب أخطاء"""
    try:
        stdout, stderr = process.communicate(timeout=1)
        
        # إذا توقف البوت
        if process.poll() is not None:
            if chat_id in bot_scripts:
                bot_scripts[chat_id]['status'] = 'crashed'
            
            error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "غير معروف"
            
            # تقصير رسالة الخطأ إذا كانت طويلة
            error_display = error_msg[:500] if len(error_msg) > 500 else error_msg
            if len(error_msg) > 500:
                error_display += "\n... (تم اقتطاع الخطأ)"
            
            logger.warning(f"البوت {file_name} للمستخدم {chat_id} توقف بسبب أخطاء. الخطأ: {error_msg[:200]}")
            
            # الحصول على مسار مجلد البوت قبل الحذف
            folder_path = ""
            if chat_id in bot_scripts:
                folder_path = bot_scripts[chat_id].get('folder_path', '')
            
            # 1. إزالة البوت من bot_scripts أولاً
            if chat_id in bot_scripts:
                del bot_scripts[chat_id]
            
            # 2. حذف مجلد البوت إذا كان موجوداً
            deleted_folders = []
            if folder_path and os.path.exists(folder_path):
                try:
                    shutil.rmtree(folder_path)
                    deleted_folders.append(os.path.basename(folder_path))
                    logger.info(f"✅ تم حذف مجلد البوت التالف: {folder_path}")
                except Exception as e:
                    logger.error(f"❌ فشل في حذف المجلد الرئيسي {folder_path}: {e}")
            
            # 3. البحث عن أي مجلدات أخرى للبوت في ACTIVE_BOTS_DIR
            if os.path.exists(ACTIVE_BOTS_DIR):
                for folder in os.listdir(ACTIVE_BOTS_DIR):
                    if os.path.isdir(os.path.join(ACTIVE_BOTS_DIR, folder)):
                        if folder.startswith(f"bot_{chat_id}_"):
                            folder_file_name = '_'.join(folder.split('_')[2:]) + '.py'
                            if folder_file_name == file_name and folder not in deleted_folders:
                                folder_path = os.path.join(ACTIVE_BOTS_DIR, folder)
                                try:
                                    shutil.rmtree(folder_path)
                                    deleted_folders.append(folder)
                                    logger.info(f"✅ تم حذف مجلد البوت البديل: {folder_path}")
                                except Exception as e:
                                    logger.error(f"❌ فشل في حذف المجلد البديل {folder_path}: {e}")
            
            # 4. إزالة من user_files
            if chat_id in user_files and file_name in user_files[chat_id]:
                user_files[chat_id].remove(file_name)
                remove_user_file_db(chat_id, file_name)
            
            # 5. إرسال رسالة واحدة للمستخدم
            try:
                # تحديد عدد المجلدات المحذوفة
                folders_count = len(deleted_folders)
                folders_info = f"🗑️ تم حذف {folders_count} مجلد للبوت"
                
                if deleted_folders:
                    folders_info += f": {', '.join(deleted_folders[:3])}"
                    if len(deleted_folders) > 3:
                        folders_info += f" و {len(deleted_folders) - 3} أخرى"
                
                bot.send_message(
                    chat_id,
                    f"❌ تم إيقاف وحذف بوتك\n\n"
                    f"📄 اسم الملف: `{file_name}`\n\n"
                    f"{folders_info}\n\n"
                    f"⚠️ الخطأ الذي حدث:\n"
                    f"```\n{error_display}\n```\n\n"
                    f"🔧 الحل:\n"
                    f"1. قم بإصلاح الأخطاء في ملفك\n"
                    f"2. تأكد من صحة التوكن والمكتبات\n"
                    f"3. أعد رفع الملف بعد التصحيح\n\n"
                    f"📞 للدعم الفني: @mora_330",
                    parse_mode='HTML'
                )
                
                # إرسال إشعار للأدمن أيضاً
                try:
                    user_name, user_username = get_user_info(chat_id)
                    bot.send_message(
                        ADMIN_ID,
                        f"🧹 تم حذف بوت تالف تلقائياً\n\n"
                        f"👤 المستخدم: {user_name}\n"
                        f"📌 اليوزر: {user_username}\n"
                        f"🆔 ID: {chat_id}\n"
                        f"📄 الملف: {file_name}\n"
                        f"🗑️ المجلدات المحذوفة: {folders_count}\n"
                        f"❌ سبب الحذف: أخطاء في التنفيذ\n"
                        f"📝 الخطأ: {error_msg[:200]}...",
                        parse_mode='HTML'
                    )
                except:
                    pass
                    
            except Exception as e:
                logger.error(f"❌ فشل في إرسال رسالة الحذف للمستخدم {chat_id}: {e}")
    
    except subprocess.TimeoutExpired:
        # البوت لا يزال يعمل - هذا طبيعي
        pass
    except Exception as e:
        logger.error(f"❌ خطأ في مراقبة البوت: {e}")

def extract_token_from_script(script_path):
    """
    استخراج التوكن من ملف البوت بجميع الطرق الممكنة
    يدعم اكتشاف التوكن بجميع الصيغ والثغرات
    """
    try:
        if not os.path.exists(script_path):
            logger.warning(f"❌ الملف غير موجود: {script_path}")
            return None
        
        with open(script_path, 'r', encoding='utf-8', errors='ignore') as script_file:
            file_content = script_file.read()
        
        # =========== 1. الأنماط القياسية ===========
        standard_patterns = [
            # التوكن المباشر بين علامات تنصيص
            r"['\"]([0-9]{8,11}:[A-Za-z0-9_-]{34,36})['\"]",
            
            # المتغيرات الشائعة
            r"(?:TOKEN|token|BOT_TOKEN|BotToken|API_KEY|API_TOKEN|TELEGRAM_TOKEN)\s*=\s*['\"]([0-9]{8,11}:[A-Za-z0-9_-]{34,36})['\"]",
            r"(?:TOKEN|token|BOT_TOKEN|BotToken|API_KEY|API_TOKEN|TELEGRAM_TOKEN)\s*:\s*['\"]([0-9]{8,11}:[A-Za-z0-9_-]{34,36})['\"]",
            
            # في دوال التهيئة
            r"(?:TeleBot|telebot\.TeleBot|Updater|Application\.builder\(\)\.token)\(['\"]([0-9]{8,11}:[A-Za-z0-9_-]{34,36})['\"]",
            r"bot\.(?:run|setWebhook)\(['\"]([0-9]{8,11}:[A-Za-z0-9_-]{34,36})['\"]",
            
            # في config أو dict
            r"['\"]token['\"]\s*:\s*['\"]([0-9]{8,11}:[A-Za-z0-9_-]{34,36})['\"]",
            r"['\"]bot_token['\"]\s*:\s*['\"]([0-9]{8,11}:[A-Za-z0-9_-]{34,36})['\"]",
            
            # في requests URLs
            r"https://api\.telegram\.org/bot([0-9]{8,11}:[A-Za-z0-9_-]{34,36})/",
            r"api\.telegram\.org/bot([0-9]{8,11}:[A-Za-z0-9_-]{34,36})/",
            
            # التوكن في f-strings
            r"f?['\"].*?{([0-9]{8,11}:[A-Za-z0-9_-]{34,36})}.*?['\"]",
            
            # التوكن مع مسافات أو أسطر جديدة
            r"['\"]((?:[0-9]{8,11}:[A-Za-z0-9_-]{34,36}\s*)+)['\"]",
        ]
        
        for pattern in standard_patterns:
            token_match = re.search(pattern, file_content, re.MULTILINE | re.IGNORECASE)
            if token_match:
                token = token_match.group(1).strip()
                if validate_token_format(token):
                    logger.info(f"✅ تم العثور على توكن (نمط قياسي): {token[:15]}...")
                    return token
        
        # =========== 2. البحث المتقدم ===========
        advanced_tokens = []
        
        # أ. البحث في التعليقات (بعض المطورين يضعونه في تعليقات للاختبار)
        comment_patterns = [
            r"#\s*(?:TOKEN|token):\s*([0-9]{8,11}:[A-Za-z0-9_-]{34,36})",
            r"#\s*(?:BOT_TOKEN|bot_token):\s*([0-9]{8,11}:[A-Za-z0-9_-]{34,36})",
            r"//\s*(?:TOKEN|token):\s*([0-9]{8,11}:[A-Za-z0-9_-]{34,36})",
            r"<!--\s*(?:TOKEN|token):\s*([0-9]{8,11}:[A-Za-z0-9_-]{34,36})\s*-->",
        ]
        
        for pattern in comment_patterns:
            matches = re.findall(pattern, file_content, re.MULTILINE | re.IGNORECASE)
            advanced_tokens.extend(matches)
        
        # ب. البحث عن توكن مقسم على عدة أسطر
        multiline_token = re.search(r"['\"]([0-9]{8,11})\s*[:]\s*([A-Za-z0-9_-]{34,36})['\"]", file_content, re.MULTILINE | re.IGNORECASE)
        if multiline_token:
            token = f"{multiline_token.group(1)}:{multiline_token.group(2)}"
            advanced_tokens.append(token)
        
        # ج. البحث في متغيرات البيئة داخل الكود
        env_patterns = [
            r"os\.(?:getenv|environ\.get)\(['\"](?:BOT_TOKEN|TELEGRAM_TOKEN|TOKEN)['\"][^)]*\)\s*or\s*['\"]([0-9]{8,11}:[A-Za-z0-9_-]{34,36})['\"]",
            r"os\.(?:getenv|environ\.get)\(['\"](?:BOT_TOKEN|TELEGRAM_TOKEN|TOKEN)['\"][^)]*\)\s*\|\s*['\"]([0-9]{8,11}:[A-Za-z0-9_-]{34,36})['\"]",
        ]
        
        for pattern in env_patterns:
            matches = re.findall(pattern, file_content, re.MULTILINE | re.IGNORECASE)
            advanced_tokens.extend(matches)
        
        # د. البحث عن توكن مشفر/مخفي
        # 1. Base64
        base64_pattern = r"[A-Za-z0-9+/=]{48,80}"
        base64_matches = re.findall(base64_pattern, file_content)
        for match in base64_matches[:5]:  # أول 5 فقط لتجنب الإبطاء
            try:
                decoded = base64.b64decode(match + '=' * (-len(match) % 4)).decode('utf-8', errors='ignore')
                if validate_token_format(decoded):
                    advanced_tokens.append(decoded)
                    logger.debug(f"🔍 وجد توكن في Base64: {decoded[:15]}...")
            except:
                pass
        
        # 2. Hex
        hex_pattern = r"[0-9a-fA-F]{70,100}"
        hex_matches = re.findall(hex_pattern, file_content)
        for match in hex_matches[:3]:
            try:
                decoded = bytes.fromhex(match).decode('utf-8', errors='ignore')
                if validate_token_format(decoded):
                    advanced_tokens.append(decoded)
                    logger.debug(f"🔍 وجد توكن في Hex: {decoded[:15]}...")
            except:
                pass
        
        # 3. Rot13 أو تشفير بسيط
        rot_patterns = [
            r"[N-ZA-Mn-za-m0-9]{48,80}",  # ROT13
        ]
        
        for pattern in rot_patterns:
            matches = re.findall(pattern, file_content)
            for match in matches[:3]:
                try:
                    decoded = match.translate(str.maketrans(
                        'N-ZA-Mn-za-m0-9', 'A-Za-z0-9'
                    ))
                    if validate_token_format(decoded):
                        advanced_tokens.append(decoded)
                except:
                    pass
        
        # هـ. البحث عن توكن في متغيرات JavaScript/Node.js
        js_patterns = [
            r"(?:token|botToken|telegramToken)\s*[:=]\s*['\"]([0-9]{8,11}:[A-Za-z0-9_-]{34,36})['\"]",
            r"process\.env\.(?:BOT_TOKEN|TELEGRAM_TOKEN)\s*\|\|?\s*['\"]([0-9]{8,11}:[A-Za-z0-9_-]{34,36})['\"]",
        ]
        
        for pattern in js_patterns:
            matches = re.findall(pattern, file_content, re.MULTILINE | re.IGNORECASE)
            advanced_tokens.extend(matches)
        
        # و. البحث عن توكن في سلاسل نصية طويلة
        long_strings = re.findall(r'["\']([^"\']{45,60})["\']', file_content)
        for string in long_strings:
            token_pattern = r'([0-9]{8,11}:[A-Za-z0-9_-]{34,36})'
            matches = re.findall(token_pattern, string)
            advanced_tokens.extend(matches)
        
        # ز. البحث باستخدام split وتوليد أنماط ديناميكية
        lines = file_content.split('\n')
        for line in lines:
            # البحث عن أي سطر يحتوي على : وأرقام وحروف
            if ':' in line and any(char.isdigit() for char in line):
                # استخراج الجزء الذي يبدو كتوكن
                parts = re.findall(r'([0-9]{8,11}:[A-Za-z0-9_-]{34,36})', line)
                advanced_tokens.extend(parts)
        
        # =========== 3. معالجة النتائج المتقدمة ===========
        if advanced_tokens:
            # إزالة التكرارات
            unique_tokens = []
            seen = set()
            for token in advanced_tokens:
                if token and token not in seen:
                    seen.add(token)
                    unique_tokens.append(token)
            
            # فلترة وتحقق
            valid_tokens = []
            for token in unique_tokens:
                # تنظيف التوكن (إزالة مسافات، أسطر جديدة)
                clean_token = token.strip().replace('\n', '').replace('\r', '').replace(' ', '')
                
                if validate_token_format(clean_token):
                    valid_tokens.append(clean_token)
            
            if valid_tokens:
                # ترتيب حسب الطول (عادة الأطول هو الأصح)
                valid_tokens.sort(key=len, reverse=True)
                
                # إذا وجدنا أكثر من توكن، نختار الأفضل
                best_token = valid_tokens[0]
                
                # التحقق الإضافي: إذا كان التوكن يحتوي على `\\n` أو `\n`
                if '\\n' in best_token or '\n' in best_token:
                    best_token = best_token.replace('\\n', '').replace('\n', '')
                
                logger.info(f"✅ تم العثور على توكن (بحث متقدم): {best_token[:15]}...")
                return best_token
        
        # =========== 4. البحث في ملفات مجاورة ===========
        script_dir = os.path.dirname(script_path)
        nearby_files = [
            'config.json', 'settings.json', 'config.py', 'settings.py',
            '.env', 'secrets.json', 'credentials.json', 'keys.json',
            'bot_config.json', 'telegram_config.json'
        ]
        
        for file_name in nearby_files:
            file_path = os.path.join(script_dir, file_name)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # البحث السريع في الملف
                    token_pattern = r'([0-9]{8,11}:[A-Za-z0-9_-]{34,36})'
                    matches = re.findall(token_pattern, content)
                    
                    for token in matches:
                        if validate_token_format(token):
                            logger.info(f"✅ تم العثور على توكن في ملف مجاور {file_name}: {token[:15]}...")
                            return token
                    
                    # إذا كان ملف JSON
                    if file_name.endswith('.json'):
                        try:
                            data = json.loads(content)
                            # البحث بشكل متكرر في JSON
                            def search_json(obj, path=""):
                                tokens = []
                                if isinstance(obj, dict):
                                    for key, value in obj.items():
                                        if isinstance(value, str) and validate_token_format(value):
                                            tokens.append(value)
                                        elif isinstance(value, (dict, list)):
                                            tokens.extend(search_json(value, f"{path}.{key}"))
                                elif isinstance(obj, list):
                                    for item in obj:
                                        if isinstance(item, str) and validate_token_format(item):
                                            tokens.append(item)
                                        elif isinstance(item, (dict, list)):
                                            tokens.extend(search_json(item, path))
                                return tokens
                            
                            json_tokens = search_json(data)
                            if json_tokens:
                                logger.info(f"✅ تم العثور على توكن في JSON {file_name}: {json_tokens[0][:15]}...")
                                return json_tokens[0]
                        except:
                            pass
                            
                except Exception as e:
                    logger.debug(f"❌ فشل قراءة ملف مجاور {file_name}: {e}")
        
        # =========== 5. البحث عن أنماط مشبوهة (للتسجيل فقط) ===========
        suspicious = re.findall(r'[0-9]{7,12}:[A-Za-z0-9_-]{20,50}', file_content)
        if suspicious:
            logger.info(f"⚠️ أنماط مشبوهة في الملف (ليست توكنات صالحة): {suspicious[:3]}")
        
        # =========== 6. إذا لم يتم العثور بأي طريقة ===========
        logger.warning(f"❌ لم يتم العثور على توكن صالح في {os.path.basename(script_path)}")
        
        # محاولة أخيرة: البحث عن أي شيء يشبه توكن
        last_resort = re.findall(r'([0-9]+:[A-Za-z0-9_-]+)', file_content)
        for candidate in last_resort:
            if 40 <= len(candidate) <= 55 and ':' in candidate:
                logger.debug(f"🔍 مرشح أخير: {candidate}")
                # يمكن إرجاعه مع تحذير
                # return candidate
        
        return None
        
    except Exception as e:
        logger.error(f"❌ فشل في استخراج التوكن من {script_path}: {e}")
        return None


def validate_token_format(token):
    """التحقق من صيغة التوكن بدقة"""
    if not token or not isinstance(token, str):
        return False
    
    # تنظيف التوكن
    clean_token = token.strip()
    if not clean_token:
        return False
    
    # الطول المعقول للتوكن
    if len(clean_token) < 40 or len(clean_token) > 60:
        return False
    
    # يجب أن يحتوي على :
    if ':' not in clean_token:
        return False
    
    parts = clean_token.split(':')
    if len(parts) != 2:
        return False
    
    bot_id, bot_key = parts
    
    # التحقق من ID البوت
    if not bot_id.isdigit():
        return False
    
    # رقم البوت عادة بين 8-11 رقم
    if len(bot_id) < 8 or len(bot_id) > 11:
        return False
    
    # التحقق من مفتاح البوت
    if not re.match(r'^[A-Za-z0-9_-]+$', bot_key):
        return False
    
    # مفتاح البوت عادة 34-36 حرف
    if len(bot_key) < 34 or len(bot_key) > 36:
        return False
    
    # نمط محدد: عادة يبدأ بحرف كبير أو رقم
    if not (bot_key[0].isalpha() or bot_key[0].isdigit()):
        return False
    
    return True


def restart_bot(chat_id):
    """إعادة تشغيل البوت المتوقف"""
    if chat_id in bot_scripts and bot_scripts[chat_id].get('status') in ['stopped', 'crashed']:
        try:
            script_path = bot_scripts[chat_id].get('script_path')
            folder_path = bot_scripts[chat_id].get('folder_path')
            file_name = bot_scripts[chat_id].get('file_name')

            if script_path and os.path.exists(script_path):
                env = os.environ.copy()
                env["PYTHONPATH"] = os.path.dirname(script_path)

                process = subprocess.Popen(['python3', script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)

                bot_scripts[chat_id]['process'] = process
                bot_scripts[chat_id]['status'] = 'running'
                bot_scripts[chat_id]['start_time'] = datetime.now()


                threading.Thread(target=monitor_bot_process, args=(process, chat_id, file_name), daemon=True).start()

                logger.info(f"تم إعادة تشغيل البوت للمستخدم {chat_id}")
                return True
        except Exception as e:
            logger.error(f"فشل في إعادة تشغيل البوت: {e}")

    return False
def stop_running_bot(chat_id):
    """إيقاف تشغيل البوت مع الاحتفاظ بالملفات"""
    if stop_bot_completely(chat_id):
        bot.send_message(chat_id, "🔴 تم إيقاف تشغيل البوت بنجاح.")
    else:
        bot.send_message(chat_id, "⚠️ لا يوجد بوت يعمل حالياً أو حدث خطأ في الإيقاف.")


@bot.callback_query_handler(func=lambda call: call.data == 'pending_uploads')
def show_pending_uploads(call):
    if call.from_user.id == ADMIN_ID:
        try:
            # تحديث القائمة من قاعدة البيانات للتأكد من وجود كل الطلبات
            pending_uploads = load_pending_uploads()
            for key, value in pending_uploads.items():
                if key not in pending_approvals:
                    pending_approvals[key] = value

            if pending_approvals:
                bot.send_message(call.message.chat.id, f"📂 جاري جلب {len(pending_approvals)} طلبات معلقة...")
                
                for (user_id, file_name), data in pending_approvals.items():
                    temp_path = data['temp_path']
                    libs = ', '.join(data['libraries']) if data['libraries'] else 'لا يوجد'
                    
                    # تجهيز نص الرسالة
                    caption = (
                        f"⏳ طلب معلق جديد\n"
                        f"👤 المستخدم: `{user_id}`\n"
                        f"📄 الملف: `{file_name}`\n"
                        f"📚 المكتبات: `{libs}`\n"
                        f"────────────────"
                    )

                    # إنشاء أزرار الموافقة والرفض
                    markup = types.InlineKeyboardMarkup()
                    approve_button = types.InlineKeyboardButton('✅ الموافقة والتشغيل', callback_data=f'approve_{user_id}_{file_name}')
                    reject_button = types.InlineKeyboardButton('❌ رفض الطلب', callback_data=f'reject_{user_id}_{file_name}')
                    markup.add(approve_button, reject_button)

                    # التحقق من وجود الملف وإرساله
                    if os.path.exists(temp_path):
                        with open(temp_path, 'rb') as file:
                            bot.send_document(
                                call.message.chat.id, 
                                file, 
                                caption=caption, 
                                reply_markup=markup,
                                parse_mode='Markdown'
                            )
                    else:
                        # في حال حُذف الملف المؤقت لسبب ما
                        bot.send_message(
                            call.message.chat.id, 
                            f"⚠️ الملف `{file_name}` غير موجود في المسار المؤقت!\n{caption}", 
                            reply_markup=markup
                        )
            else:
                bot.send_message(call.message.chat.id, "✅ لا توجد طلبات معلقة حالياً.")

        except Exception as e:
            logger.error(f"خطأ في عرض الطلبات المعلقة: {e}")
            bot.send_message(call.message.chat.id, f"❌ حدث خطأ في عرض الطلبات: {e}")
    else:
        bot.answer_callback_query(call.id, "⚠️ أنت لست المطور.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == 'my_bots')
def show_my_bots_callback(call):
    """عرض قائمة البوتات الخاصة بالمستخدم"""
    user_id = call.from_user.id
    
    if user_id in banned_users:
        bot.answer_callback_query(call.id, "⛔ أنت محظور من استخدام هذا البوت.", show_alert=True)
        return
    
    user_bots = get_user_bots(user_id)
    
    if not user_bots:
        bot.send_message(call.message.chat.id, "📭 ليس لديك أي بوتات حالياً.")
        return
    
    # إنشاء القائمة
    markup = create_active_bots_menu(user_id)
    
    # إعداد الرسالة
    total_bots = len(user_bots)
    running_count = sum(1 for bot_info in user_bots.values() if bot_info.get('status') == 'running')
    
    message_text = f"""
🤖 بوتاتك النشطة

📊 الإحصائيات:
• 🤖 إجمالي البوتات: {total_bots}
• 🟢 قيد التشغيل: {running_count}
• 🔴 متوقفة: {total_bots - running_count}

👇 اختر البوت الذي تريد التحكم به:
"""
    
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            reply_markup=markup,
            parse_mode='HTML'
        )
    except:
        bot.send_message(
            call.message.chat.id,
            message_text,
            reply_markup=markup,
            parse_mode='HTML'
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith('bot_details_'))
def show_bot_details(call):
    """عرض تفاصيل البوت المحدد مع أزرار التحكم"""
    user_id = call.from_user.id
    file_name = call.data.replace('bot_details_', '', 1)
    
    # جلب معلومات البوت
    user_bots = get_user_bots(user_id)
    
    if file_name not in user_bots:
        bot.answer_callback_query(call.id, "❌ البوت غير موجود", show_alert=True)
        return
    
    bot_info = user_bots[file_name]
    status = bot_info.get('status', 'stopped')
    start_time = bot_info.get('start_time', 'غير معروف')
    
    # تحويل الوقت إذا كان من نوع datetime
    if isinstance(start_time, datetime):
        start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
        if status == 'running':
            uptime = datetime.now() - start_time
            uptime_str = f"{uptime.days} يوم, {uptime.seconds // 3600} ساعة, {(uptime.seconds % 3600) // 60} دقيقة"
        else:
            uptime_str = "غير متاح"
    else:
        start_time_str = str(start_time)
        uptime_str = "غير متاح"
    
    # محاولة الحصول على معلومات البوت من التوكن
    bot_username = "غير متاح"
    if user_id in bot_scripts and bot_scripts[user_id].get('file_name') == file_name:
        script_path = bot_scripts[user_id].get('script_path', '')
        if script_path and os.path.exists(script_path):
            token = extract_token_from_script(script_path)
            if token:
                try:
                    bot_info_api = requests.get(f'https://api.telegram.org/bot{token}/getMe', timeout=5).json()
                    if bot_info_api.get('ok'):
                        bot_username = f"@{bot_info_api['result']['username']}"
                except:
                    pass
    
    # إعداد الرسالة
    message_text = f"""
🔍 معلومات البوت

📄 الاسم: `{file_name}`
🤖 يوزر البوت: {bot_username}
🟢 الحالة: `{status}`
⏰ تاريخ الرفع: {start_time_str}
"""

    if status == 'running':
        message_text += f"⏳ مدة التشغيل: {uptime_str}\n"

    message_text += "\n🎮 التحكم بالبوت:"
    
    # إنشاء أزرار التحكم
    markup = create_bot_control_markup(user_id, file_name, status)
    
    # إرسال الرسالة
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            reply_markup=markup,
            parse_mode='HTML'
        )
    except:
        bot.send_message(
            call.message.chat.id,
            message_text,
            reply_markup=markup,
            parse_mode='HTML'
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith('user_stop_'))
def user_stop_bot(call):
    """إيقاف البوت من قبل المستخدم"""
    user_id = call.from_user.id
    file_name = call.data.replace('user_stop_', '', 1)
    
    if user_id in bot_scripts and bot_scripts[user_id].get('file_name') == file_name:
        if stop_bot_completely(user_id):
            # تحديث الواجهة
            try:
                markup = create_bot_control_markup(user_id, file_name, 'stopped')
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=f"⏹️ تم إيقاف البوت\n\n📄 `{file_name}`\n\n🔄 الحالة الآن: 🔴 متوقف",
                    reply_markup=markup,
                    parse_mode='HTML'
                )
                bot.answer_callback_query(call.id, "✅ تم إيقاف البوت")
            except Exception as e:
                logger.error(f"خطأ في تحديث واجهة الإيقاف: {e}")
                bot.answer_callback_query(call.id, "✅ تم الإيقاف ولكن حدث خطأ في التحديث")
        else:
            bot.answer_callback_query(call.id, "⚠️ لا يمكن إيقاف البوت")
    else:
        bot.answer_callback_query(call.id, "❌ البوت غير موجود أو غير نشط")

@bot.callback_query_handler(func=lambda call: call.data.startswith('user_start_'))
def user_start_bot(call):
    """تشغيل البوت من قبل المستخدم"""
    user_id = call.from_user.id
    file_name = call.data.replace('user_start_', '', 1)
    
    # محاولة إعادة التشغيل
    if restart_bot(user_id):
        # تحديث الواجهة
        try:
            markup = create_bot_control_markup(user_id, file_name, 'running')
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"▶️ تم تشغيل البوت\n\n📄 `{file_name}`\n\n🔄 الحالة الآن: 🟢 يعمل",
                reply_markup=markup,
                parse_mode='HTML'
            )
            bot.answer_callback_query(call.id, "✅ تم تشغيل البوت")
        except Exception as e:
            logger.error(f"خطأ في تحديث واجهة التشغيل: {e}")
            bot.answer_callback_query(call.id, "✅ تم التشغيل ولكن حدث خطأ في التحديث")
    else:
        bot.answer_callback_query(call.id, "⚠️ لا يمكن تشغيل البوت")

@bot.callback_query_handler(func=lambda call: call.data.startswith('user_delete_'))
def user_delete_bot(call):
    """حذف البوت من قبل المستخدم"""
    user_id = call.from_user.id
    file_name = call.data.replace('user_delete_', '', 1)
    
    # تأكيد الحذف
    markup = types.InlineKeyboardMarkup()
    confirm_button = types.InlineKeyboardButton('✅ نعم، احذف', callback_data=f'confirm_delete_{file_name}')
    cancel_button = types.InlineKeyboardButton('❌ إلغاء', callback_data='my_bots')
    markup.add(confirm_button, cancel_button)
    
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"⚠️ تأكيد الحذف\n\nهل أنت متأكد من حذف البوت:\n`{file_name}`\n\nهذا الإجراء لا يمكن التراجع عنه!",
            reply_markup=markup,
            parse_mode='HTML'
        )
    except:
        bot.send_message(
            call.message.chat.id,
            f"⚠️ تأكيد الحذف\n\nهل أنت متأكد من حذف البوت:\n`{file_name}`\n\nهذا الإجراء لا يمكن التراجع عنه!",
            reply_markup=markup,
            parse_mode='HTML'
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_delete_'))
def confirm_delete_bot(call):
    """تأكيد حذف البوت"""
    user_id = call.from_user.id
    file_name = call.data.replace('confirm_delete_', '', 1)
    
    if delete_uploaded_file(user_id):
        bot.answer_callback_query(call.id, "✅ تم حذف البوت")
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"🗑️ تم الحذف\n\nتم حذف البوت `{file_name}` بنجاح.",
            parse_mode='HTML'
        )
    else:
        bot.answer_callback_query(call.id, "❌ فشل في حذف البوت")

@bot.callback_query_handler(func=lambda call: call.data.startswith('user_token_'))
def change_bot_token(call):
    """طلب تغيير توكن البوت"""
    user_id = call.from_user.id
    file_name = call.data.replace('user_token_', '', 1)
    
    # البحث عن البوت
    if user_id not in bot_scripts or bot_scripts[user_id].get('file_name') != file_name:
        bot.answer_callback_query(call.id, "❌ البوت غير نشط", show_alert=True)
        return
    
    # حفظ حالة التغيير
    if 'token_changes' not in globals():
        globals()['token_changes'] = {}
    
    globals()['token_changes'][user_id] = {
        'file_name': file_name,
        'action': 'change_token'
    }
    
    # إرسال رسالة الطلب
    message = bot.send_message(
        user_id,
        f"🔄 تغيير توكن البوت\n\n"
        f"البوت: `{file_name}`\n\n"
        f"📝 أرسل التوكن الجديد الآن:\n"
        f"يجب أن يكون على الشكل:\n"
        f"`1234567890:ABCdefGHIjklMNopQRstUVwxyz`\n\n"
        f"⚠️ ملاحظة: سيتم إعادة تشغيل البوت تلقائياً بعد تغيير التوكن.",
        parse_mode='HTML'
    )
    
    bot.answer_callback_query(call.id, "📝 أرسل التوكن الجديد")

@bot.callback_query_handler(func=lambda call: call.data.startswith('user_download_'))
def download_bot_file(call):
    """تحميل ملف البوت"""
    user_id = call.from_user.id
    file_name = call.data.replace('user_download_', '', 1)
    
    # البحث عن مسار البوت
    if user_id in bot_scripts and bot_scripts[user_id].get('file_name') == file_name:
        script_path = bot_scripts[user_id].get('script_path', '')
        
        if os.path.exists(script_path):
            try:
                with open(script_path, 'rb') as file:
                    bot.send_document(
                        user_id,
                        file,
                        caption=f"📥 ملف البوت\n\n📄 `{file_name}`\n\n✅ تم تحميل الملف بنجاح",
                        parse_mode='HTML'
                    )
                bot.answer_callback_query(call.id, "✅ تم إرسال الملف إلى الخاص")
            except Exception as e:
                logger.error(f"خطأ في إرسال الملف: {e}")
                bot.answer_callback_query(call.id, "❌ فشل في إرسال الملف")
        else:
            bot.answer_callback_query(call.id, "❌ الملف غير موجود")
    else:
        bot.answer_callback_query(call.id, "❌ البوت غير موجود")

def delete_uploaded_file(chat_id):
    """حذف البوت مع إيقافه وحذف مجلده بالكامل بما فيه قاعدة البيانات"""
    try:
        # حالة 1: البوت نشط في bot_scripts
        if chat_id in bot_scripts:
            file_name = bot_scripts[chat_id].get('file_name', '')
            folder_path = bot_scripts[chat_id].get('folder_path', '')
            db_path = bot_scripts[chat_id].get('db_path', '')

            # 1. إيقاف البوت إذا كان يعمل
            stop_bot_completely(chat_id)

            # 2. حذف مجلد البوت إذا كان موجوداً
            if folder_path and os.path.exists(folder_path) and folder_path.startswith(ACTIVE_BOTS_DIR):
                shutil.rmtree(folder_path)
                logger.info(f"✅ تم حذف مجلد البوت بالكامل: {folder_path}")

            # 3. حذف من user_files
            if chat_id in user_files and file_name in user_files[chat_id]:
                user_files[chat_id].remove(file_name)
                remove_user_file_db(chat_id, file_name)

            # 4. حذف من bot_scripts
            del bot_scripts[chat_id]

            bot.send_message(chat_id, "🗑️ تم حذف البوت وإيقافه تماماً مع جميع بياناته.")
            return True

        # حالة 2: البوت غير نشط ولكن له مجلد في ACTIVE_BOTS_DIR
        else:
            # البحث عن جميع مجلدات المستخدم في ACTIVE_BOTS_DIR
            user_folders = []
            for folder in os.listdir(ACTIVE_BOTS_DIR):
                if os.path.isdir(os.path.join(ACTIVE_BOTS_DIR, folder)):
                    # استخراج user_id من اسم المجلد: bot_{user_id}_{filename}
                    if folder.startswith(f"bot_{chat_id}_"):
                        user_folders.append(folder)
            
            if not user_folders:
                bot.send_message(chat_id, "⚠️ لا يوجد بوتات مخزنة لحذفها.")
                return False

            # حذف كل المجلدات الخاصة بالمستخدم
            deleted_count = 0
            for folder in user_folders:
                folder_path = os.path.join(ACTIVE_BOTS_DIR, folder)
                try:
                    if os.path.exists(folder_path):
                        shutil.rmtree(folder_path)
                        logger.info(f"✅ تم حذف مجلد البوت: {folder_path}")
                        deleted_count += 1
                        
                        # استخراج اسم الملف من اسم المجلد
                        parts = folder.split('_')
                        if len(parts) >= 3:
                            file_name = '_'.join(parts[2:]) + '.py'
                            # حذف من user_files
                            if chat_id in user_files and file_name in user_files[chat_id]:
                                user_files[chat_id].remove(file_name)
                                remove_user_file_db(chat_id, file_name)
                except Exception as e:
                    logger.error(f"❌ فشل في حذف مجلد {folder}: {e}")
                    continue

            if deleted_count > 0:
                bot.send_message(chat_id, f"🗑️ تم حذف {deleted_count} بوت مع جميع بياناته.")
                return True
            else:
                bot.send_message(chat_id, "⚠️ فشل في حذف البوتات.")
                return False

    except Exception as e:
        logger.error(f"❌ فشل في حذف البوت: {e}")
        bot.send_message(chat_id, f"❌ حدث خطأ أثناء حذف البوت: {e}")
        return False

def kill_process_tree(process):
    try:
        parent = psutil.Process(process.pid)
        children = parent.children(recursive=True)
        for child in children:
            child.kill()
        parent.kill()
    except Exception as e:
        logger.error(f"فشل في قتل العملية: {e}")

def kill_process_by_script_path(script_path):
    """قتل جميع العمليات المرتبطة بمسار script معين"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and len(cmdline) > 1:
                    if script_path in cmdline[1]:
                        proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception as e:
        logger.error(f"فشل في قتل العمليات لـ {script_path}: {e}")

def create_active_bots_menu(user_id):
    """إنشاء قائمة أزرار للبوتات النشطة"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # جلب جميع البوتات الخاصة بالمستخدم
    user_bots = get_user_bots(user_id)
    
    if not user_bots:
        no_bots_button = types.InlineKeyboardButton('📭 لا توجد بوتات', callback_data='no_bots')
        markup.add(no_bots_button)
        return markup
    
    # إضافة زر لكل بوت
    for file_name, bot_info in user_bots.items():
        status = bot_info.get('status', 'stopped')
        status_icon = '🟢' if status == 'running' else '🔴'
        bot_button = types.InlineKeyboardButton(
            f'{status_icon} {file_name}',
            callback_data=f'bot_details_{file_name}'
        )
        markup.add(bot_button)
    
    # إضافة زر الرجوع
    back_button = types.InlineKeyboardButton('🔙 رجوع', callback_data='back_to_menu')
    markup.add(back_button)
    
    return markup

def create_bot_control_markup(user_id, file_name, status):
    """إنشاء أزرار تحكم للبوت المحدد"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # زر التشغيل/الإيقاف
    if status == 'running':
        stop_button = types.InlineKeyboardButton('⏹️ إيقاف', callback_data=f'user_stop_{file_name}')
        markup.add(stop_button)
    else:
        start_button = types.InlineKeyboardButton('▶️ تشغيل', callback_data=f'user_start_{file_name}')
        markup.add(start_button)
    
    # الأزرار الأخرى
    change_token_button = types.InlineKeyboardButton('🔑 تغيير التوكن', callback_data=f'user_token_{file_name}')
    download_button = types.InlineKeyboardButton('📥 سحب الملف', callback_data=f'user_download_{file_name}')
    delete_button = types.InlineKeyboardButton('🗑️ حذف', callback_data=f'user_delete_{file_name}')
    
    markup.add(change_token_button, download_button)
    markup.add(delete_button)
    
    # زر الرجوع لقائمة البوتات
    back_button = types.InlineKeyboardButton('🔙 رجوع للقائمة', callback_data='my_bots')
    markup.add(back_button)
    
    return markup

@bot.message_handler(commands=['delete_user_file'])
def delete_user_file(message):
    if message.from_user.id == ADMIN_ID:
        try:
            user_id = int(message.text.split()[1])
            file_name = message.text.split()[2]

            if user_id in user_files and file_name in user_files[user_id]:
                file_path = os.path.join(uploaded_files_dir, file_name)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    user_files[user_id].remove(file_name)
                    remove_user_file_db(user_id, file_name)
                    bot.send_message(message.chat.id, f"✅ تم حذف الملف {file_name} للمستخدم {user_id}.")
                else:
                    bot.send_message(message.chat.id, f"⚠️ الملف {file_name} غير موجود.")
            else:
                bot.send_message(message.chat.id, f"⚠️ المستخدم {user_id} لم يرفع الملف {file_name}.")
        except Exception as e:
            logger.error(f"فشل في حذف ملف المستخدم: {e}")
            bot.send_message(message.chat.id, f"❌ حدث خطأ: {e}")
    else:
        bot.send_message(message.chat.id, "⚠️ أنت لست المطور.")

@bot.message_handler(commands=['stop_user_bot'])
def stop_user_bot(message):
    if message.from_user.id == ADMIN_ID:
        try:
            user_id = int(message.text.split()[1])
            file_name = message.text.split()[2]

            if user_id in user_files and file_name in user_files[user_id]:
                for chat_id, script_info in bot_scripts.items():
                    if script_info.get('folder_path', '').endswith(file_name.split('.')[0]):
                        kill_process_tree(script_info['process'])
                        bot.send_message(chat_id, f"🔴 تم إيقاف تشغيل البوت {file_name}.")
                        bot.send_message(message.chat.id, f"✅ تم إيقاف تشغيل البوت {file_name} للمستخدم {user_id}.")
                        break
                else:
                    bot.send_message(message.chat.id, f"⚠️ البوت {file_name} غير قيد التشغيل.")
            else:
                bot.send_message(message.chat.id, f"⚠️ المستخدم {user_id} لم يرفع الملف {file_name}.")
        except Exception as e:
            logger.error(f"فشل في إيقاف بوت المستخدم: {e}")
            bot.send_message(message.chat.id, f"❌ حدث خطأ: {e}")
    else:
        bot.send_message(message.chat.id, "⚠️ أنت لست المطور.")
@bot.message_handler(commands=['host_status'])
def host_status(message):
    """فحص حالة استضافة Wesbsite - للادمن فقط"""
    user_id = message.from_user.id


    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ هذا الأمر للمطور فقط")
        return

    try:

        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu = psutil.cpu_percent(interval=1)


        active_bots = len([proc for proc in psutil.process_iter() if 'python' in proc.name()])

        status_msg = "🔧 حالة الاستضافة (للمطور فقط):\n\n"
        status_msg += f"🧠 الذاكرة: {memory.percent}% ({memory.used//1024//1024}MB / {memory.total//1024//1024}MB)\n"
        status_msg += f"💾 التخزين: {disk.percent}% ({disk.used//1024//1024}MB / {disk.total//1024//1024}MB)\n"
        status_msg += f"⚡ المعالج: {cpu}% مستخدم\n"
        status_msg += f"🤖 البوتات النشطة: {active_bots}\n"
        status_msg += f"👥 المستخدمين النشطين: {len(active_users)}\n\n"


        warnings = []
        if memory.percent > 90:
            warnings.append("🔴 الذاكرة خطيرة - قد يتوقف الخادم")
        elif memory.percent > 80:
            warnings.append("🟡 الذاكرة مرتفعة - تجنب تثبيت مكتبات جديدة")

        if disk.percent > 95:
            warnings.append("🔴 التخزين خطير - مساحة منخفضة جداً")
        elif disk.percent > 85:
            warnings.append("🟡 التخزين مرتفع - مساحة محدودة")

        if cpu > 95:
            warnings.append("🔴 المعالج خطير - حمل مرتفع جداً")
        elif cpu > 80:
            warnings.append("🟡 المعالج مرتفع - حمل عالي")

        if warnings:
            status_msg += "⚠️ التنبيهات:\n" + "\n".join(warnings) + "\n\n"
        else:
            status_msg += "✅ الحالة مستقرة\n\n"

        status_msg += "🛠 أوامر الصيانة:\n"
        status_msg += "/clean_memory - تنظيف الذاكرة\n"
        status_msg += "/restart_bot - إعادة تشغيل البوت\n"
        status_msg += "/bot_stats - إحصائيات البوت"

        bot.send_message(message.chat.id, status_msg)

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ في فحص الحالة: {str(e)}")

@bot.message_handler(commands=['bot_stats'])
def bot_stats(message):
    """إحصائيات البوت - للادمن فقط"""
    user_id = message.from_user.id

    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ هذا الأمر للمطور فقط")
        return

    try:
        total_files = sum(len(files) for files in user_files.values())
        active_bots = len(bot_scripts)
        pending_requests = len(pending_approvals)

        stats_msg = "📊 إحصائيات البوت (للمطور فقط):\n\n"
        stats_msg += f"👥 المستخدمين: {len(user_files)}\n"
        stats_msg += f"📁 الملفات: {total_files}\n"
        stats_msg += f"🤖 البوتات النشطة: {active_bots}\n"
        stats_msg += f"⏳ الطلبات المعلقة: {pending_requests}\n"
        stats_msg += f"🔨 المحظورين: {len(banned_users)}\n"
        stats_msg += f"🆓 الوضع الحر: {'مفعل' if free_mode else 'معطل'}\n"
        stats_msg += f"🔒 قفل البوت: {'مقفل' if bot_locked else 'مفتوح'}\n\n"


        if bot_scripts:
            stats_msg += "🔍 البوتات النشطة:\n"
            for user_id, bot_info in list(bot_scripts.items())[:5]:
                stats_msg += f"• {bot_info.get('file_name', 'غير معروف')} (للمستخدم {user_id})\n"
            if len(bot_scripts) > 5:
                stats_msg += f"• ... و {len(bot_scripts) - 5} بوت آخر\n"

        bot.send_message(message.chat.id, stats_msg)

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ في جلب الإحصائيات: {str(e)}")
@bot.message_handler(commands=['active_bots'])
def show_active_bots(message):
    """عرض البوتات النشطة مع مجلداتها"""
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ هذا الأمر للمطور فقط")
        return

    try:
        if not bot_scripts:
            bot.send_message(message.chat.id, "📭 لا توجد بوتات نشطة حالياً")
            return

        bots_list = "🤖 البوتات النشطة:\n\n"

        for chat_id, bot_info in bot_scripts.items():
            status = bot_info.get('status', 'unknown')
            folder_name = bot_info.get('bot_folder_name', 'غير معروف')
            file_name = bot_info.get('file_name', 'غير معروف')
            start_time = bot_info.get('start_time', 'غير معروف')

            bots_list += f"📁 المجلد: {folder_name}\n"
            bots_list += f"📄 الملف: {file_name}\n"
            bots_list += f"👤 المستخدم: {chat_id}\n"
            bots_list += f"🟢 الحالة: {status}\n"
            bots_list += f"⏰ بدء التشغيل: {start_time}\n"
            bots_list += "─" * 30 + "\n"

        bot.send_message(message.chat.id, bots_list)

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ في عرض البوتات: {str(e)}")
@bot.message_handler(commands=['clean_memory'])
def clean_memory(message):
    """تنظيف الذاكرة - للادمن فقط"""
    user_id = message.from_user.id

    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ هذا الأمر للمطور فقط")
        return

    try:
        import gc
        memory_before = psutil.virtual_memory().percent


        gc.collect()


        if 'pending_approvals' in globals():
            pending_approvals.clear()

        memory_after = psutil.virtual_memory().percent

        bot.send_message(message.chat.id,
                        f"🧹 تم تنظيف الذاكرة:\n"
                        f"قبل: {memory_before}%\n"
                        f"بعد: {memory_after}%\n"
                        f"التحسن: {memory_before - memory_after:.1f}%")

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ فشل في تنظيف الذاكرة: {str(e)}")

@bot.message_handler(commands=['restart_bot'])
def restart_bot_command(message):
    """إعادة تشغيل البوت - للادمن فقط"""
    user_id = message.from_user.id

    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ هذا الأمر للمطور فقط")
        return

    try:
        bot.send_message(message.chat.id, "🔄 جاري إعادة تشغيل البوت...")


        import gc
        gc.collect()


        python = sys.executable
        os.execl(python, python, *sys.argv)

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ فشل في إعادة التشغيل: {str(e)}")

@bot.message_handler(commands=['installed_libs'])
def show_installed_libraries(message):
    """عرض المكتبات المثبتة - للادمن فقط"""
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ هذا الأمر للمطور فقط")
        return
    
    try:
        libs_count = len(installed_libraries)
        
        if libs_count == 0:
            bot.send_message(message.chat.id, "📭 لا توجد مكتبات مثبتة")
            return
        
        # تجميع المكتبات في صفحات
        libs_list = list(installed_libraries)
        libs_list.sort()
        
        # عرض أول 20 مكتبة
        libs_text = "📚 المكتبات المثبتة:\n\n"
        for i, lib in enumerate(libs_list[:20], 1):
            libs_text += f"{i}. `{lib}`\n"
        
        if libs_count > 20:
            libs_text += f"\n... و {libs_count - 20} مكتبة أخرى"
        
        libs_text += f"\n\n📊 الإجمالي: {libs_count} مكتبة"
        
        bot.send_message(message.chat.id, libs_text, parse_mode='Markdown')
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ في عرض المكتبات: {str(e)}")

@bot.message_handler(commands=['clear_libs_cache'])
def clear_libraries_cache(message):
    """مسح ذاكرة المكتبات المثبتة - للادمن فقط"""
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ هذا الأمر للمطور فقط")
        return
    
    try:
        global installed_libraries
        old_count = len(installed_libraries)
        installed_libraries.clear()
        save_installed_libraries()
        
        bot.send_message(message.chat.id, 
            f"🧹 تم مسح ذاكرة المكتبات\n"
            f"🗑️ تم حذف {old_count} مكتبة من الذاكرة")
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ في مسح الذاكرة: {str(e)}")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    try:
        # 1. زر الرجوع للقائمة الرئيسية (جديد)
        if call.data == 'back_to_menu':
            if user_id == ADMIN_ID:
                markup = create_main_menu(user_id)
                try:
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text="📋 القائمة الرئيسية:",
                        reply_markup=markup
                    )
                except:
                    bot.send_message(chat_id, "📋 القائمة الرئيسية:", reply_markup=markup)
            return
        
        # 2. زر القائمة الرئيسية (موجود)
        elif call.data == 'menu':
            markup = create_main_menu(user_id)
            try:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="📋 القائمة الرئيسية:",
                    reply_markup=markup
                )
            except:
                bot.send_message(chat_id, "📋 القائمة الرئيسية:", reply_markup=markup)
            return

        # 3. زر البوتات النشطة (جديد - تم نقله لدالة منفصلة)
        elif call.data == 'active_bots':
            # تم التعامل معه في دالة show_active_bots_panel المنفصلة
            return

        # 4. زر المعلومات التفصيلية للبوت (جديد)
        elif call.data.startswith('info_'):
            # تم التعامل معه في دالة show_bot_info المنفصلة
            return

        # 5. إيقاف البوت
        elif 'stop_' in call.data:
            try:
                _, target_chat_id, file_name = call.data.split('_', 2)
                target_chat_id = int(target_chat_id)
                
                # التحقق من الصلاحيات
                if user_id != ADMIN_ID and user_id != target_chat_id:
                    bot.answer_callback_query(call.id, "⚠️ ليس لديك صلاحية لإيقاف هذا البوت", show_alert=True)
                    return
                
                if stop_bot_completely(target_chat_id):
                    bot.answer_callback_query(call.id, "✅ تم إيقاف البوت")
                    
                    # تحديث الرسالة الأصلية
                    try:
                        if user_id == ADMIN_ID:
                            admin_markup = create_admin_control_markup(target_chat_id, file_name, 'stopped')
                            bot.edit_message_reply_markup(
                                chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                reply_markup=admin_markup
                            )
                        else:
                            user_markup = create_user_control_markup(target_chat_id, file_name, 'stopped')
                            bot.edit_message_reply_markup(
                                chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                reply_markup=user_markup
                            )
                    except Exception as e:
                        logger.error(f"خطأ في تحديث واجهة الإيقاف: {e}")
                    
                    # إرسال رسالة للمستخدم إذا كان الإيقاف من الأدمن
                    if user_id == ADMIN_ID and user_id != target_chat_id:
                        try:
                            user_markup = create_user_control_markup(target_chat_id, file_name, 'stopped')
                            bot.send_message(target_chat_id, f"⏹️ تم إيقاف البوت {file_name} من قبل الأدمن", reply_markup=user_markup)
                        except:
                            pass
                            
                else:
                    bot.answer_callback_query(call.id, "⚠️ لا يمكن إيقاف البوت أو هو غير نشط")
                    
            except Exception as e:
                logger.error(f"خطأ في إيقاف البوت: {e}")
                bot.answer_callback_query(call.id, "❌ حدث خطأ في الإيقاف")

        # 6. تشغيل البوت
        elif 'start_' in call.data:
            try:
                _, target_chat_id, file_name = call.data.split('_', 2)
                target_chat_id = int(target_chat_id)
                
                # التحقق من الصلاحيات
                if user_id != ADMIN_ID and user_id != target_chat_id:
                    bot.answer_callback_query(call.id, "⚠️ ليس لديك صلاحية لتشغيل هذا البوت", show_alert=True)
                    return
                
                if restart_bot(target_chat_id):
                    bot.answer_callback_query(call.id, "✅ تم تشغيل البوت")
                    
                    # تحديث الرسالة الأصلية
                    try:
                        if user_id == ADMIN_ID:
                            admin_markup = create_admin_control_markup(target_chat_id, file_name, 'running')
                            bot.edit_message_reply_markup(
                                chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                reply_markup=admin_markup
                            )
                        else:
                            user_markup = create_user_control_markup(target_chat_id, file_name, 'running')
                            bot.edit_message_reply_markup(
                                chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                reply_markup=user_markup
                            )
                    except Exception as e:
                        logger.error(f"خطأ في تحديث واجهة التشغيل: {e}")
                    
                    # إرسال رسالة للمستخدم إذا كان التشغيل من الأدمن
                    if user_id == ADMIN_ID and user_id != target_chat_id:
                        try:
                            user_markup = create_user_control_markup(target_chat_id, file_name, 'running')
                            bot.send_message(target_chat_id, f"▶️ تم تشغيل البوت {file_name} من قبل الأدمن", reply_markup=user_markup)
                        except:
                            pass
                            
                else:
                    bot.answer_callback_query(call.id, "⚠️ لا يمكن تشغيل البوت")
                    
            except Exception as e:
                logger.error(f"خطأ في تشغيل البوت: {e}")
                bot.answer_callback_query(call.id, "❌ حدث خطأ في التشغيل")

        # 7. حذف البوت
        elif 'delete_' in call.data:
            try:
                _, target_chat_id, file_name = call.data.split('_', 2)
                target_chat_id = int(target_chat_id)
                
                # التحقق من الصلاحيات (الإدمن فقط)
                if user_id != ADMIN_ID:
                    bot.answer_callback_query(call.id, "⚠️ فقط الأدمن يمكنه حذف البوتات", show_alert=True)
                    return
                
                if delete_uploaded_file(target_chat_id):
                    bot.answer_callback_query(call.id, "✅ تم حذف البوت")
                    
                    # تحديث الرسالة
                    try:
                        bot.edit_message_text(
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            text=f"🗑️ تم حذف البوت {file_name} تماماً",
                            reply_markup=None
                        )
                    except:
                        pass
                    
                    # إرسال رسالة للمستخدم
                    try:
                        bot.send_message(target_chat_id, f"🗑️ تم حذف البوت {file_name} من قبل الأدمن")
                    except:
                        pass
                        
                else:
                    bot.answer_callback_query(call.id, "⚠️ لا يمكن حذف البوت")
                    
            except Exception as e:
                logger.error(f"خطأ في حذف البوت: {e}")
                bot.answer_callback_query(call.id, "❌ حدث خطأ في الحذف")

        # 8. معالجات الكوال الأخرى الموجودة أصلاً
        elif call.data == 'upload':
            ask_to_upload_file(call.message)
            
        elif call.data == 'speed':
            bot_speed_info(call)
            
        elif call.data == 'install_library':
            install_library_callback(call)
            
        elif call.data == 'subscription':
            subscription_menu(call)
            
        elif call.data == 'stats':
            stats_menu(call)
            
        elif call.data == 'broadcast':
            broadcast_callback(call)
            
        elif call.data == 'ban_user':
            ban_user_callback(call)
            
        elif call.data == 'unban_user':
            unban_user_callback(call)
            
        elif call.data == 'pending_uploads':
            show_pending_uploads(call)
            
        elif call.data == 'lock_bot':
            lock_bot_callback(call)
            
        elif call.data == 'unlock_bot':
            unlock_bot_callback(call)
            
        elif call.data == 'free_mode':
            toggle_free_mode(call)
            
        elif call.data == 'check_subscription':
            check_subscription(call)
            
        elif call.data.startswith('approve_'):
            handle_approval(call)
            
        elif call.data.startswith('reject_'):
            handle_approval(call)
            
        elif call.data == 'add_subscription':
            add_subscription_callback(call)
            
        elif call.data == 'remove_subscription':
            remove_subscription_callback(call)
            
        elif call.data == 'users':
            if user_id == ADMIN_ID:
                users_count = len(user_files)
                active_count = len(active_users)
                banned_count = len(banned_users)
                
                users_text = f"""
👥 إدارة المستخدمين:

👤 المستخدمين الكلي: {users_count}
🟢 النشطين: {active_count}
🔴 المحظورين: {banned_count}

📌 لحظر مستخدم: /ban <user_id> <السبب>
📌 لإلغاء الحظر: /unban <user_id>
"""
                bot.send_message(chat_id, users_text)
            else:
                bot.send_message(chat_id, "⚠️ هذا الأمر للمطور فقط")
                
        elif call.data == 'pending':
            if user_id == ADMIN_ID:
                show_pending_uploads(call)
            else:
                bot.send_message(chat_id, "⚠️ هذا الأمر للمطور فقط")

        # 9. زر المساعدة للمستخدم
        elif call.data.startswith('help_'):
            try:
                _, target_chat_id, file_name = call.data.split('_', 2)
                target_chat_id = int(target_chat_id)
                
                if user_id == target_chat_id or user_id == ADMIN_ID:
                    help_text = f"""
🆘 مساعدة بخصوص البوت: {file_name}

📌 الأوامر المتاحة:
• إيقاف/تشغيل البوت من خلال الأزرار
• للحصول على دعم فني: /contact
• لإعادة تشغيل البوت: تواصل مع الأدمن

📞 للتواصل مع المالك:
{YOUR_USERNAME}

⚠️ ملاحظات:
1. تأكد من أن التوكن صالح
2. تأكد من تثبيت جميع المكتبات المطلوبة
3. في حالة المشاكل الفنية راسل الدعم
"""
                    bot.send_message(chat_id, help_text, parse_mode='HTML')
                else:
                    bot.answer_callback_query(call.id, "⚠️ ليس لديك صلاحية لعرض هذه المعلومات", show_alert=True)
                    
            except Exception as e:
                logger.error(f"خطأ في عرض المساعدة: {e}")

        # 10. أي كوال أخرى غير معروفة
        else:
            logger.warning(f"كوال غير معالج: {call.data}")
            bot.answer_callback_query(call.id, "⚠️ الأمر غير معروف")

    except Exception as e:
        logger.error(f"خطأ عام في معالجة الكوال: {e}")
        try:
            bot.answer_callback_query(call.id, f"❌ حدث خطأ: {str(e)[:50]}", show_alert=True)
        except:
            pass

if __name__ == "__main__":
    time.sleep(2)
    
    # تحميل المكتبات المثبتة
    load_installed_libraries()
    
    start_existing_bots()
    time.sleep(1)
    setup_bot_commands()
    
    logger.info(f'بدء تشغيل البوت الرئيسي بنجاح - {len(installed_libraries)} مكتبة مثبتة')
    print(f'✅ تم تشغيل البوت الرئيسي - {len(installed_libraries)} مكتبة مثبتة')
    
    bot.infinity_polling()
