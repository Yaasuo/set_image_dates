import os
import re
import time
from datetime import datetime
from PIL import Image

# 支持的图片扩展名
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.heic', '.bmp', '.tiff', '.webp')

# 匹配文件名中的日期模式，例如：
# 2025-02-21 223354 或 2025-02-21_223354 或 20250221_223354 等
DATE_PATTERNS = [
    r"(\d{4})[-_]?(\d{2})[-_]?(\d{2})[\s_]*(\d{2})(\d{2})(\d{2})",
    r"(\d{4})[-_]?(\d{2})[-_]?(\d{2})"
]

def extract_datetime_from_filename(filename):
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, filename)
        if match:
            groups = match.groups()
            try:
                if len(groups) == 6:
                    # 完整的日期时间
                    return datetime.strptime("".join(groups), "%Y%m%d%H%M%S")
                elif len(groups) == 3:
                    # 只有日期
                    return datetime.strptime("".join(groups), "%Y%m%d")
            except ValueError:
                continue
    return None

def set_file_times(filepath, new_datetime):
    timestamp = new_datetime.timestamp()
    # 修改访问时间与修改时间
    os.utime(filepath, (timestamp, timestamp))

    # macOS 创建时间需要单独处理
    try:
        # 使用 xattr 或者 SetFile 修改创建时间（macOS 专用命令）
        formatted_time = new_datetime.strftime("%m/%d/%Y %H:%M:%S")
        os.system(f'SetFile -d "{formatted_time}" "{filepath}"')
    except Exception as e:
        print(f"⚠️ 无法修改创建时间: {filepath}, 错误: {e}")

def main():
    # 获取当前执行目录
    current_dir = os.getcwd()
    print(f"📁 当前目录: {current_dir}")

    # 找出所有图片文件
    images = [
        f for f in os.listdir(current_dir)
        if f.lower().endswith(IMAGE_EXTENSIONS)
    ]

    if not images:
        print("⚠️ 当前目录没有图片文件可处理。")
        return

    print(f"🔍 找到 {len(images)} 张图片，开始处理...")

    for filename in images:
        filepath = os.path.join(current_dir, filename)
        dt = extract_datetime_from_filename(filename)
        if dt:
            set_file_times(filepath, dt)
            print(f"✅ 已修改: {filename} → {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"⏩ 跳过: {filename} (未检测到日期)")

    print("\n🎉 处理完成！所有检测到日期的图片时间已更新。")

if __name__ == "__main__":
    main()
