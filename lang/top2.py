import os
import random
import subprocess
import shutil
import colorsys
from PIL import Image, ImageDraw, ImageFont

# --- 1. ГЛОБАЛЬНЫЕ НАСТРОЙКИ ---
current_dir = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(current_dir, "input.txt")
TEMP_DIR = os.path.join(current_dir, "images_smooth")
OUTPUT_VIDEO = os.path.join(current_dir, "final_race.mp4")

# Настройки скорости (60 FPS для идеальной плавности)
FPS = 60                      
SECONDS_PER_YEAR = 1.0        
FRAMES_PER_PERIOD = int(FPS * SECONDS_PER_YEAR)

# Геометрия экрана (Full HD)
WIDTH, HEIGHT = 1920, 1080
# BG_COLOR = (245, 245, 245)
BG_COLOR = (240, 240, 240)

# Координаты сетки
BAR_X_START = 550    # Увеличено, чтобы названия языков слева не мешали столбцам
BAR_MAX_WIDTH = 1100 # Ширина рабочей зоны графика
BAR_HEIGHT = 60     
BAR_SPACING = 35     

# Глобальные переменные для логики
language_colors = {}
current_hue = 0.0
GLOBAL_MAX_VAL = 30.0 # Будет рассчитано автоматически

def get_color(lang):
    """Генерация уникального контрастного цвета по золотому сечению."""
    global current_hue
    if lang not in language_colors:
        current_hue = (current_hue + 0.618033988749895) % 1.0
        s = random.uniform(0.75, 0.95)
        v = random.uniform(0.85, 1.0)
        r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(current_hue, s, v)]
        language_colors[lang] = (r, g, b)
    return language_colors[lang]

def generate_frame(frame_name, display_year, current_state):
    """Отрисовка одного кадра видео."""
    img = Image.new('RGB', (WIDTH, HEIGHT), color=BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    try:
        font_year = ImageFont.truetype("arial.ttf", 250)
        font_main = ImageFont.truetype("arial.ttf", 40)
        font_title = ImageFont.truetype("arial.ttf", 65)
    except:
        font_year = font_main = font_title = ImageFont.load_default()

    # Заголовок (статичный)
    draw.text((WIDTH//2, 60), "Most Popular Programming Languages", fill=(40, 40, 40), font=font_title, anchor="mm")

    # Фоновый год (Темно-серый, хорошо видимый)
    draw.text((WIDTH - 750, HEIGHT - 250), str(display_year), fill=(110, 110, 110), font=font_year)

    # Сортируем, чтобы лидеры отрисовывались последними (поверх остальных)
    current_state.sort(key=lambda x: x[1], reverse=True)

    for name, rank, val in current_state:
        if rank > 11.5: continue # Не рисуем тех, кто слишком глубоко "уплыл"

        # Вертикальная позиция (Y) на основе плавного дробного ранга
        y = 180 + rank * (BAR_HEIGHT + BAR_SPACING)
        val = max(0, val)
        
        # Длина столбца зависит от GLOBAL_MAX_VAL (Динамический масштаб)
        current_bar_width = int((val / GLOBAL_MAX_VAL) * BAR_MAX_WIDTH) 
        color = get_color(name)

        # ТЕКСТ СЛЕВА: Название языка (anchor="ra" - выравнивание по правому краю от точки)
        draw.text((BAR_X_START - 30, y + 8), name, fill=(40, 40, 40), font=font_main, anchor="ra")
        
        # ТЕНЬ И СТОЛБЕЦ
        draw.rounded_rectangle([BAR_X_START + 4, y + 4, BAR_X_START + current_bar_width + 4, y + BAR_HEIGHT + 4], radius=12, fill=(215, 215, 215))
        draw.rounded_rectangle([BAR_X_START, y, BAR_X_START + current_bar_width, y + BAR_HEIGHT], radius=12, fill=color)
        
        # ТЕКСТ СПРАВА: Проценты (anchor="la" - выравнивание по левому краю от точки)
        percent_str = f"{val:.2f}%"
        draw.text((BAR_X_START + current_bar_width + 25, y + 8), percent_str, fill=(60, 60, 60), font=font_main)

    img.save(os.path.join(TEMP_DIR, f"{frame_name}.png"))

def build_video_with_ffmpeg():
    """Сборка видеоряда через консольный FFmpeg."""
    print("\n--- Запуск склейки через FFmpeg ---")
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-framerate", str(FPS), 
        "-i", os.path.join(TEMP_DIR, "frame_%04d.png"), 
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-b:v", "6000k", OUTPUT_VIDEO
    ]
    try:
        subprocess.run(ffmpeg_cmd, check=True)
        shutil.rmtree(TEMP_DIR) # Удаляем временные картинки
        print(f"\nГОТОВО! Видео сохранено: {OUTPUT_VIDEO}")
    except Exception as e:
        print(f"Ошибка при работе FFmpeg: {e}")

def main():
    global GLOBAL_MAX_VAL
    if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)

    # 1. ЧТЕНИЕ ДАННЫХ И ПОИСК МАКСИМУМА
    data_by_year = {}
    vals_for_scale = []
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if '|' not in line: continue
            parts = [p.strip() for p in line.split('|')]
            y, l, r, v = parts[0], parts[1], int(parts[2])-1, float(parts[3].replace('%', ''))
            if y not in data_by_year: data_by_year[y] = {}
            data_by_year[y][l] = {'rank': r, 'val': v}
            vals_for_scale.append(v)
    
    # Масштабируем график по самому высокому значению во всем файле
    GLOBAL_MAX_VAL = max(vals_for_scale) + 2 

    # 2. ГЕНЕРАЦИЯ КАДРОВ
    years = sorted(list(data_by_year.keys()))
    frame_counter = 0

    print(f"Обработка {len(years)} лет данных...")

    for i in range(len(years) - 1):
        y1, y2 = years[i], years[i+1]
        d1, d2 = data_by_year[y1], data_by_year[y2]
        all_langs = set(d1.keys()).union(set(d2.keys()))
        
        for f in range(FRAMES_PER_PERIOD):
            prog = f / FRAMES_PER_PERIOD
            state = []
            for l in all_langs:
                info1, info2 = d1.get(l), d2.get(l)
                
                # ЛОГИКА "БЕЗ ПРЫЖКОВ": если языка нет в году, он ждет/уходит на 12-ю позицию
                r1 = info1['rank'] if info1 else 12
                v1 = info1['val'] if info1 else 0.0
                r2 = info2['rank'] if info2 else 12
                v2 = info2['val'] if info2 else 0.0
                
                state.append((l, r1 + (r2 - r1) * prog, v1 + (v2 - v1) * prog))
            
            generate_frame(f"frame_{frame_counter:04d}", y1 if prog < 0.5 else y2, state)
            frame_counter += 1
        print(f"Завершен год: {y1}")

    # 3. ФИНАЛЬНАЯ СКЛЕЙКА
    build_video_with_ffmpeg()

if __name__ == "__main__":
    main()