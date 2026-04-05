import os
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageFont

# --- КОНФИГУРАЦИЯ ---
current_dir = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(current_dir, "input_sp.txt")
TEMP_DIR = os.path.join(current_dir, "frames")
FLAGS_DIR = os.path.join(current_dir, "flag") 
OUTPUT_VIDEO = os.path.join(current_dir, "space_progression_final_2026.mp4")

FPS = 60                      
SECONDS_PER_PERIOD = 3.5      
FRAMES_PER_PERIOD = int(FPS * SECONDS_PER_PERIOD)
FINAL_FREEZE_SECONDS = 7      

WIDTH, HEIGHT = 1920, 1080
BG_COLOR = (211, 211, 211)    # Светло-серый
TEXT_COLOR = (20, 20, 25)     # Темно-серый
TITLE_TEXT = "Total Satellites in Orbit by Country"

BAR_X_START = 450    
BAR_MAX_WIDTH = 1150 
BAR_HEIGHT = 65     
BAR_SPACING = 25     

# Исключения и маппинг флагов
EXCEPTION_FLAGS = {"USSR": "red_rect"}
COUNTRY_TO_CODE = {
    "USA": "us", "Russia": "ru", "China": "cn", "France": "fr",
    "Japan": "jp", "India": "in", "United Kingdom": "gb", "UK": "gb",
    "Canada": "ca", "Germany": "de", "South Korea": "kr", "USSR": "su"
}

# --- ПРОФЕССИОНАЛЬНАЯ КОНТРАСТНАЯ ПАЛИТРА ---
COLORS_PALETTE = [
    (255, 120, 0),   # Насыщенный оранжевый (USA)
    (30, 215, 96),   # Ярко-зеленый (China)
    (0, 112, 255),   # Синий электрик
    (255, 45, 85),   # Ярко-розовый/красный
    (175, 82, 222),  # Фиолетовый
    (255, 204, 0),   # Солнечно-желтый
    (90, 200, 250),  # Голубой небесный
    (88, 86, 214),   # Индиго
    (255, 59, 48),   # Коралловый
    (0, 150, 136),   # Тиловый
    (141, 110, 99),  # Коричневый темный
    (67, 160, 71),   # Лесной зеленый
    (233, 30, 99),   # Маджента
    (63, 81, 181),   # Королевский синий
    (255, 152, 0),   # Янтарный
    (156, 39, 176),  # Пурпурный
    (0, 188, 212),   # Циан
    (139, 195, 74),  # Лайм
    (255, 87, 34),   # Огненный
    (96, 125, 139)   # Стальной
]

def get_flag(country_name):
    if EXCEPTION_FLAGS.get(country_name) == "red_rect":
        return Image.new("RGBA", (60, 40), (255, 0, 0, 255))
    
    code = COUNTRY_TO_CODE.get(country_name, "un")
    path = os.path.join(FLAGS_DIR, f"{code}.png")
    if os.path.exists(path):
        return Image.open(path).convert("RGBA")
    return None

def generate_frame(filename, current_year, state, global_max, country_colors):
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    try:
        font_main = ImageFont.truetype("arial.ttf", 40)
        font_title = ImageFont.truetype("arial.ttf", 60)
        font_year = ImageFont.truetype("arial.ttf", 150)
    except:
        font_main = ImageFont.load_default()
        font_title = ImageFont.load_default()
        font_year = ImageFont.load_default()

    # Заголовок
    bbox_title = draw.textbbox((0, 0), TITLE_TEXT, font=font_title)
    title_w = bbox_title[2] - bbox_title[0]
    draw.text(((WIDTH - title_w) // 2, 50), TITLE_TEXT, fill=TEXT_COLOR, font=font_title)

    # Топ-10 стран
    sorted_state = sorted(state, key=lambda x: x[2], reverse=True)[:10]

    for i, (name, _, val, _) in enumerate(sorted_state):
        if val <= 0: continue
        
        y_pos = 180 + i * (BAR_HEIGHT + BAR_SPACING)
        bar_w = int((val / global_max) * BAR_MAX_WIDTH) if global_max > 0 else 0
        
        # Получаем зафиксированный цвет для страны
        color = country_colors.get(name, (150, 150, 150))
        draw.rectangle([BAR_X_START, y_pos, BAR_X_START + bar_w, y_pos + BAR_HEIGHT], fill=color)
        
        # Текст (страна)
        bbox_name = draw.textbbox((0, 0), name, font=font_main)
        name_w = bbox_name[2] - bbox_name[0]
        draw.text((BAR_X_START - name_w - 20, y_pos + 10), name, fill=TEXT_COLOR, font=font_main)
        
        # Текст (число)
        draw.text((BAR_X_START + bar_w + 15, y_pos + 10), f"{int(val):,}", fill=TEXT_COLOR, font=font_main)
        
        # Флаг
        flag = get_flag(name)
        if flag:
            flag = flag.resize((60, 40))
            img.paste(flag, (BAR_X_START - name_w - 90, y_pos + 12), flag if flag.mode == 'RGBA' else None)

    # Год в углу
    year_str = str(int(current_year))
    bbox_year = draw.textbbox((0, 0), year_str, font=font_year)
    year_w = bbox_year[2] - bbox_year[0]
    year_h = bbox_year[3] - bbox_year[1]
    draw.text((WIDTH - year_w - 50, HEIGHT - year_h - 50), year_str, fill=TEXT_COLOR, font=font_year)

    img.save(os.path.join(TEMP_DIR, filename))

def main():
    if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)
    
    data_by_year = {}
    all_countries_ordered = [] # Для стабильного распределения цветов
    
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 4: continue
            try:
                year, country, count = int(parts[0]), parts[1], int(parts[3])
                if year not in data_by_year: data_by_year[year] = {}
                data_by_year[year][country] = count
                if country not in all_countries_ordered:
                    all_countries_ordered.append(country)
            except: continue

    # ФИКСИРУЕМ ЦВЕТА ЗА СТРАНАМИ
    country_colors = {}
    for i, country in enumerate(all_countries_ordered):
        country_colors[country] = COLORS_PALETTE[i % len(COLORS_PALETTE)]

    years = sorted(data_by_year.keys())
    all_countries_set = set(all_countries_ordered)
    totals_history = {}
    running_totals = {c: 0 for c in all_countries_set}
    last_active = {c: years[0] for c in all_countries_set}

    # Подсчет истории накопления
    for y in years:
        for c in all_countries_set:
            if c in data_by_year[y]:
                running_totals[c] += data_by_year[y][c]
                if data_by_year[y][c] > 0: last_active[c] = y
            if y - last_active[c] > 2: running_totals[c] = 0
        totals_history[y] = running_totals.copy()
        
    global_max = max(max(t.values()) for t in totals_history.values()) if totals_history else 1

    frame_idx = 0
    print("Генерация кадров...")
    for i in range(len(years) - 1):
        y1, y2 = years[i], years[i+1]
        for f in range(FRAMES_PER_PERIOD):
            prog = f / FRAMES_PER_PERIOD
            state = [(n, 0, totals_history[y1][n]*(1-prog) + totals_history[y2][n]*prog, 0) for n in all_countries_set]
            generate_frame(f"frame_{frame_idx:05d}.png", y1 + (y2-y1)*prog, state, global_max, country_colors)
            frame_idx += 1

    # Заморозка финала
    last_year = years[-1]
    final_state = [(n, 0, totals_history[last_year][n], 0) for n in all_countries_set]
    for i in range(int(FPS * FINAL_FREEZE_SECONDS)):
        generate_frame(f"frame_{frame_idx:05d}.png", last_year, final_state, global_max, country_colors)
        frame_idx += 1

    print("Сборка видео...")
    subprocess.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", os.path.join(TEMP_DIR, "frame_%05d.png"), 
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", OUTPUT_VIDEO])
    shutil.rmtree(TEMP_DIR)
    print(f"Готово! Результат: {OUTPUT_VIDEO}")

if __name__ == "__main__":
    main()