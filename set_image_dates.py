import os
import re
import sys
import time
import ctypes
import platform
import subprocess
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS

# ----------------- 获取当前文件夹 -----------------
def get_target_folder():
    """获取程序运行所在的文件夹"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

# ----------------- EXIF / 文件名提取时间 -----------------
def get_exif_create_date(img_path):
    """尝试从图片 EXIF 读取拍摄时间"""
    try:
        image = Image.open(img_path)
        exif_data = image._getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'DateTimeOriginal':
                    return value  # 'YYYY:MM:DD HH:MM:SS'
    except Exception:
        pass
    return None

def get_date_from_filename(filename):
    """尝试从文件名提取日期，支持多种格式"""
    patterns = [
        r'(\d{4}-\d{2}-\d{2})[ _]?(\d{6})',
        r'(\d{8})[ _]?(\d{6})'
    ]
    for pat in patterns:
        match = re.search(pat, filename)
        if match:
            date_part, time_part = match.groups()
            if len(date_part) == 8:
                date_part = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:]}"
            try:
                dt = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H%M%S")
                return dt.strftime("%Y:%m:%d %H:%M:%S")
            except Exception:
                continue
    return None

# ----------------- Windows 创建时间修改 -----------------
def set_file_times_ctypes(path, new_time_str):
    """使用 ctypes 修改 Windows 文件创建时间、修改时间、访问时间"""
    dt = datetime.strptime(new_time_str, '%Y:%m:%d %H:%M:%S')
    timestamp = time.mktime(dt.timetuple())
    os.utime(path, (timestamp, timestamp))  # 修改时间 & 访问时间

    FILE_WRITE_ATTRIBUTES = 0x100
    OPEN_EXISTING = 3
    FILE_FLAG_BACKUP_SEMANTICS = 0x02000000

    def datetime_to_filetime(dt_obj):
        t = int((dt_obj - datetime(1601, 1, 1)).total_seconds() * 10000000)
        low = t & 0xFFFFFFFF
        high = t >> 32
        return low, high

    low, high = datetime_to_filetime(dt)
    handle = ctypes.windll.kernel32.CreateFileW(
        path, FILE_WRITE_ATTRIBUTES, 0, None, OPEN_EXISTING,
        FILE_FLAG_BACKUP_SEMANTICS, None
    )
    if handle == -1:
        print(f"⚠️ 打开文件失败: {path}")
        return

    class FILETIME(ctypes.Structure):
        _fields_ = [("dwLowDateTime", ctypes.c_uint32),
                    ("dwHighDateTime", ctypes.c_uint32)]

    ft = FILETIME(low, high)
    res = ctypes.windll.kernel32.SetFileTime(
        handle, ctypes.byref(ft), ctypes.byref(ft), ctypes.byref(ft)
    )
    ctypes.windll.kernel32.CloseHandle(handle)
    if res == 0:
        print(f"⚠️ 无法修改创建时间: {path}")

# ----------------- macOS 创建时间修改 -----------------
def set_macos_create_time(path, new_time_str):
    """修改 macOS 文件创建时间（调用 SetFile 命令）"""
    try:
        t = datetime.strptime(new_time_str, "%Y:%m:%d %H:%M:%S")
        mac_time = t.strftime("%Y-%m-%dT%H:%M:%S")
        subprocess.run(["SetFile", "-d", mac_time, path], stderr=subprocess.DEVNULL)
        subprocess.run(["SetFile", "-m", mac_time, path], stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"⚠️ macOS 创建时间修改失败: {path}, 错误: {e}")

# ----------------- 统一接口 -----------------
def update_file_timestamp(file_path, new_time):
    """修改文件时间，跨平台处理"""
    system = platform.system().lower()
    if system.startswith("win"):
        set_file_times_ctypes(file_path, new_time)
    elif system == "darwin":
        set_macos_create_time(file_path, new_time)
    else:
        timestamp = time.mktime(datetime.strptime(new_time, '%Y:%m:%d %H:%M:%S').timetuple())
        os.utime(file_path, (timestamp, timestamp))

# ----------------- 主处理 -----------------
def process_images_in_folder(folder):
    supported_exts = ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.heic']
    count = 0
    log_lines = []

    for root, _, files in os.walk(folder):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext not in supported_exts:
                continue
            path = os.path.join(root, file)
            date = get_exif_create_date(path)
            source = "EXIF"
            if not date:
                date = get_date_from_filename(file)
                source = "文件名"
            if date:
                update_file_timestamp(path, date)
                count += 1
                log_lines.append(f"{file} -> {date} ({source})")

    log_path = os.path.join(folder, "修正日志.txt")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"共修改 {count} 张图片\n\n")
        f.write("\n".join(log_lines))

    return count, log_path

# ----------------- 通知 -----------------
def notify(msg):
    try:
        system = platform.system().lower()
        if system.startswith("win"):
            os.system(f'powershell -command "Add-Type -AssemblyName PresentationFramework;'
                      f'[System.Windows.MessageBox]::Show(\'{msg}\',\'图片时间修正工具\')"')
        elif system == "darwin":
            os.system(f"osascript -e 'display notification \"{msg}\" with title \"图片时间修正工具\"'")
    except Exception:
        pass

# ----------------- 主入口 -----------------
def main():
    folder = get_target_folder()
    total, log_path = process_images_in_folder(folder)
    msg = f"已完成，共修改 {total} 张图片。\n详情见日志文件：{os.path.basename(log_path)}"
    notify(msg)

if __name__ == "__main__":
    main()
