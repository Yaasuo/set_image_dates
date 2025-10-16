#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
from datetime import datetime
import re

def extract_date_from_filename(filename):
    """从文件名中提取日期时间，如 '2025-02-21 223354'"""
    match = re.search(r'(\d{4})[-_]?(\d{2})[-_]?(\d{2})[ _-]?(\d{2})(\d{2})(\d{2})', filename)
    if match:
        y, m, d, hh, mm, ss = match.groups()
        return f"{y}-{m}-{d} {hh}:{mm}:{ss}"
    return None

def set_file_times(file_path, date_str):
    """修改文件创建时间和修改时间"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        ts = time.mktime(dt.timetuple())
        os.utime(file_path, (ts, ts))  # 修改访问时间和修改时间

        # macOS 修改创建时间
        mac_time = dt.strftime("%Y%m%d%H%M.%S")
        os.system(f"touch -t {mac_time} '{file_path}'")

        print(f"✅ 已修改: {os.path.basename(file_path)} → {date_str}")
    except Exception as e:
        print(f"⚠️ 修改失败: {file_path}, 错误: {e}")

def main():
    folder = os.path.dirname(os.path.abspath(__file__))
    print(f"📁 当前目录: {folder}")

    image_exts = ['.jpg', '.jpeg', '.png', '.heic', '.gif', '.tiff', '.bmp', '.webp']
    files = [f for f in os.listdir(folder) if any(f.lower().endswith(ext) for ext in image_exts)]
    if not files:
        print("⚠️ 当前目录没有图片文件可处理。")
        return

    for filename in files:
        date_str = extract_date_from_filename(filename)
        if date_str:
            file_path = os.path.join(folder, filename)
            set_file_times(file_path, date_str)

    print("🎉 全部处理完成！")

if __name__ == "__main__":
    main()
