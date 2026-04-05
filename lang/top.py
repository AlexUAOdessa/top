import os
import random
import subprocess
import shutil
import colorsys
from PIL import Image, ImageDraw, ImageFont

# --- ГЛОБАЛЬНЫЕ НАСТРОЙКИ ---
current_dir = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(current_dir, "input.txt")
TEMP_DIR = os.path.join(current_dir, "images_smooth")
OUTPUT_VIDEO = os.path.join(current_dir, "final_race.mp4")

FPS = 60
SECONDS_PER_YEAR = 1.0 
FRAMES_PER_PERIOD = int(FPS * SECONDS_PER_YEAR)

WIDTH, HEIGHT = 1920, 1080
BG_COLOR = (245, 245, 245)

# ИСПРАВЛЕННЫЕ КООРДИНАТЫ (Больше места для текста)
NAME_X = 100        
BAR_X_START = 550    # Увеличено, чтобы названия не налезали на столбцы
BAR_MAX_WIDTH = 1100 # Оптимальная ширина
BAR_HEIGHT = 60     
BAR_SPACING = 35     

language_colors = {}
current_hue = 0.0
GLOBAL_MAX_VAL = 30.0 # Будет обновлено автоматически из файла

def get_color(lang):
    global current_hue
    if lang not in language_colors:
        current_hue = (current_hue + 0.618033988749895) % 1.0
        s = random.uniform(0.75, 0.95)
        v = random.uniform(0.85, 1.0)
        r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(current_hue, s, v)]
        language_colors[lang] = (r, g, b)
    return language_colors[lang]

def generate_frame(frame_name, display_year, current_state):
    img = Image.new('RGB', (WIDTH, HEIGHT), color=BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    try:
        font_year = ImageFont.truetype("arial.ttf", 250)
        font_main = ImageFont.truetype("arial.ttf", 40)
        font_title = ImageFont.truetype("arial.ttf", 60) # Шрифт для заголовка
    except:
        font_year = font_main = font_title = ImageFont.load_default()

    # 1. Заголовок видео
    draw.text((WIDTH//2, 50), "Top Programming Languages", fill=(50, 50, 50), font=font_title, anchor="mm")

    # 2. Фоновый год (Темный и четкий)
    draw.text((WIDTH - 750, HEIGHT - 250), str(display_year), fill=(100, 100, 100), font=font_year)

    current_state.sort(key=lambda x: x[1], reverse=True)

    for name, rank, val in current_state:
        if rank > 11: continue # Ограничим до Топ-12

        y = 150 + rank * (BAR_HEIGHT + BAR_SPACING) # Чуть ниже из-за заголовка
        val = max(0, val)
        
        # ДИНАМИЧЕСКИЙ МАСШТАБ: используем GLOBAL_MAX_VAL вместо жесткого числа 30
        current_bar_width = int((val / GLOBAL_MAX_VAL) * BAR_MAX_WIDTH) 
        color = get_color(name)

        # Название языка (с выравниванием по правому краю до начала столбца)
        draw.text((BAR_X_START - 30, y + 8), name, fill=(40, 40, 40), font=font_main, anchor="ra")
        
        # Тень и столбец
        draw.rounded_rectangle([BAR_X_START + 5, y + 5, BAR_X_START + current_bar_width + 5, y + BAR_HEIGHT + 5], radius=10, fill=(210, 210, 210))
        draw.rounded_rectangle([BAR_X_START, y, BAR_X_START + current_bar_width, y + BAR_HEIGHT], radius=10, fill=color)
        
        # Проценты
        percent_str = f"{val:.2f}%"
        draw.text((BAR_X_START + current_bar_width + 20, y + 8), percent_str, fill=(60, 60, 60), font=font_main)

    img.save(os.path.join(TEMP_DIR, f"{frame_name}.png"))

def build_video_with_ffmpeg():
    print("\n--- Склейка видео ---")
    ffmpeg_cmd = ["ffmpeg", "-y", "-framerate", str(FPS), "-i", os.path.join(TEMP_DIR, "frame_%04d.png"), 
                  "-c:v", "libx264", "-pix_fmt", "yuv420p", "-b:v", "5000k", OUTPUT_VIDEO]
    try:
        subprocess.run(ffmpeg_cmd, check=True)
        shutil.rmtree(TEMP_DIR)
        print(f"Готово: {OUTPUT_VIDEO}")
    except Exception as e:
        print(f"Ошибка FFmpeg: {e}")

def main():
    global GLOBAL_MAX_VAL
    if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)

    # --- ШАГ 1. Чтение данных и поиск МАКСИМУМА ---
    data_by_year = {}
    all_values = []
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if '|' not in line: continue
            parts = [p.strip() for p in line.split('|')]
            year, lang, rank, val_str = parts[0], parts[1], int(parts[2])-1, float(parts[3].replace('%', ''))
            
            if year not in data_by_year: data_by_year[year] = {}
            data_by_year[year][lang] = {'rank': rank, 'val': val_str}
            all_values.append(val_str)
    
    # Автоматически определяем масштаб (берем самый большой процент в истории + 5% запаса)
    GLOBAL_MAX_VAL = max(all_values) + 5 

    # --- ШАГ 2. Генерация кадров ---
    years = sorted(list(data_by_year.keys()))
    frame_counter = 0

    for i in range(len(years) - 1):
        y1, y2 = years[i], years[i+1]
        d1, d2 = data_by_year[y1], data_by_year[y2]
        all_langs = set(d1.keys()).union(set(d2.keys()))
        
        for f in range(FRAMES_PER_PERIOD):
            prog = f / FRAMES_PER_PERIOD
            state = []
            for l in all_langs:
                r1, v1 = d1.get(l, {}).get('rank', 15), d1.get(l, {}).get('val', 0.0)
                r2, v2 = d2.get(l, {}).get('rank', 15), d2.get(l, {}).get('val', 0.0)
                state.append((l, r1 + (r2 - r1) * prog, v1 + (v2 - v1) * prog))
            
            generate_frame(f"frame_{frame_counter:04d}", y1 if prog < 0.5 else y2, state)
            frame_counter += 1
        print(f"Год {y1} готов")

    build_video_with_ffmpeg()

if __name__ == "__main__":
    main()