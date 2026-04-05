import os
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageFont

# ====================== КОНФИГУРАЦИЯ ======================
current_dir = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(current_dir, "input_sp.txt")
TEMP_DIR = os.path.join(current_dir, "frames")
FLAGS_DIR = os.path.join(current_dir, "flag")
OUTPUT_VIDEO = os.path.join(current_dir, "space_progression_final_2026.mp4")

FPS = 60
SECONDS_PER_PERIOD = 2.8      # можно уменьшить ещё сильнее
FRAMES_PER_PERIOD = int(FPS * SECONDS_PER_PERIOD)
FINAL_FREEZE_SECONDS = 6

WIDTH, HEIGHT = 1920, 1080
BG_COLOR = (211, 211, 211)
TEXT_COLOR = (20, 20, 25)

TITLE_TEXT = "Total Satellites in Orbit by Country"

BAR_X_START = 450
BAR_MAX_WIDTH = 1150
BAR_HEIGHT = 65
BAR_SPACING = 25

# ====================== ЦВЕТА ПОД ПРИМЕР ======================
COUNTRY_COLORS = {
    "USA": (255, 140, 0),      # оранжевый
    "China": (0, 200, 80),     # зелёный
    "United Kingdom": (0, 120, 255),  # синий
    "UK": (0, 120, 255),
    "Russia": (140, 40, 210),  # фиолетовый
    "France": (255, 80, 180),  # розовый
    "Japan": (255, 200, 0),    # жёлтый
    "Germany": (0, 220, 200),  # бирюзовый
    "Canada": (200, 30, 30),   # тёмно-красный
    "India": (40, 140, 255),   # голубой
    "South Korea": (80, 220, 60), # светло-зелёный
    "USSR": (200, 0, 0),       # красный (как в твоей старой логике)
}

# Запасные цвета, если вдруг появятся новые страны
FALLBACK_COLORS = [
    (255, 100, 100), (100, 255, 100), (100, 100, 255),
    (255, 255, 100), (255, 100, 255), (100, 255, 255)
]

def get_color(country):
    return COUNTRY_COLORS.get(country, FALLBACK_COLORS[hash(country) % len(FALLBACK_COLORS)])

def get_flag(country_name):
    if country_name == "USSR":
        flag = Image.new("RGBA", (60, 40), (200, 0, 0, 255))
        return flag
    code = {"USA": "us", "Russia": "ru", "China": "cn", "France": "fr",
            "Japan": "jp", "India": "in", "United Kingdom": "gb", "UK": "gb",
            "Canada": "ca", "Germany": "de", "South Korea": "kr"}.get(country_name, "un")
    
    path = os.path.join(FLAGS_DIR, f"{code}.png")
    if os.path.exists(path):
        return Image.open(path).convert("RGBA")
    return None


def main():
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)

    # --- Чтение данных ---
    data_by_year = {}
    all_countries = set()

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: 
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 4: 
                continue
            try:
                year = int(parts[0])
                country = parts[1]
                count = int(parts[3])
                if year not in data_by_year:
                    data_by_year[year] = {}
                data_by_year[year][country] = count
                all_countries.add(country)
            except:
                continue

    years = sorted(data_by_year.keys())

    # --- Накопительные итоги ---
    running_totals = {c: 0 for c in all_countries}
    last_active = {c: years[0] for c in all_countries}
    totals_history = {}

    for y in years:
        for c in all_countries:
            if c in data_by_year[y]:
                running_totals[c] += data_by_year[y][c]
                last_active[c] = y
            # Сбрасываем, если страна давно неактивна
            if y - last_active[c] > 3:
                running_totals[c] = 0
        totals_history[y] = running_totals.copy()

    global_max = max(max(t.values()) for t in totals_history.values()) if totals_history else 1

    # --- Кэширование шрифтов ---
    try:
        font_title = ImageFont.truetype("arial.ttf", 60)
        font_main = ImageFont.truetype("arial.ttf", 40)
        font_year = ImageFont.truetype("arial.ttf", 150)
    except:
        font_title = ImageFont.load_default()
        font_main = ImageFont.load_default()
        font_year = ImageFont.load_default()

    # ====================== ГЕНЕРАЦИЯ КАДРОВ ======================
    frame_idx = 0
    print("Генерация кадров...")

    for i in range(len(years) - 1):
        y1, y2 = years[i], years[i + 1]
        for f in range(FRAMES_PER_PERIOD):
            prog = f / FRAMES_PER_PERIOD
            current_year = y1 + (y2 - y1) * prog

            img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
            draw = ImageDraw.Draw(img)

            # Заголовок
            draw.text((WIDTH//2 - 380, 50), TITLE_TEXT, fill=TEXT_COLOR, font=font_title, anchor="mm")

            # Топ-10
            state = sorted(
                [(name, totals_history[y1].get(name, 0) * (1 - prog) + totals_history[y2].get(name, 0) * prog)
                 for name in all_countries], 
                key=lambda x: x[1], reverse=True
            )[:10]

            for rank, (name, val) in enumerate(state):
                if val <= 0: 
                    continue
                y_pos = 180 + rank * (BAR_HEIGHT + BAR_SPACING)
                bar_w = int((val / global_max) * BAR_MAX_WIDTH)

                color = get_color(name)
                draw.rectangle([BAR_X_START, y_pos, BAR_X_START + bar_w, y_pos + BAR_HEIGHT], fill=color)

                # Название
                draw.text((BAR_X_START - 20, y_pos + 12), name, fill=TEXT_COLOR, font=font_main, anchor="ra")
                # Значение
                draw.text((BAR_X_START + bar_w + 20, y_pos + 12), f"{int(val):,}", fill=TEXT_COLOR, font=font_main)

                # Флаг
                flag = get_flag(name)
                if flag:
                    flag = flag.resize((60, 40))
                    img.paste(flag, (BAR_X_START - 380, y_pos + 12), flag)

            # Год
            year_str = str(int(current_year))
            draw.text((WIDTH - 80, HEIGHT - 80), year_str, fill=TEXT_COLOR, font=font_year, anchor="rb")

            img.save(os.path.join(TEMP_DIR, f"frame_{frame_idx:05d}.png"))
            frame_idx += 1

    # Финальная пауза
    print("Финальные кадры...")
    final_state = sorted([(n, totals_history[years[-1]].get(n, 0)) for n in all_countries], 
                        key=lambda x: x[1], reverse=True)[:10]
    
    for _ in range(int(FPS * FINAL_FREEZE_SECONDS)):
        img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)
        draw.text((WIDTH//2 - 380, 50), TITLE_TEXT, fill=TEXT_COLOR, font=font_title, anchor="mm")

        for rank, (name, val) in enumerate(final_state):
            if val <= 0: continue
            y_pos = 180 + rank * (BAR_HEIGHT + BAR_SPACING)
            bar_w = int((val / global_max) * BAR_MAX_WIDTH)
            
            draw.rectangle([BAR_X_START, y_pos, BAR_X_START + bar_w, y_pos + BAR_HEIGHT], fill=get_color(name))
            draw.text((BAR_X_START - 20, y_pos + 12), name, fill=TEXT_COLOR, font=font_main, anchor="ra")
            draw.text((BAR_X_START + bar_w + 20, y_pos + 12), f"{int(val):,}", fill=TEXT_COLOR, font=font_main)

            flag = get_flag(name)
            if flag:
                flag = flag.resize((60, 40))
                img.paste(flag, (BAR_X_START - 380, y_pos + 12), flag)

        draw.text((WIDTH - 80, HEIGHT - 80), str(years[-1]), fill=TEXT_COLOR, font=font_year, anchor="rb")
        img.save(os.path.join(TEMP_DIR, f"frame_{frame_idx:05d}.png"))
        frame_idx += 1

    # ====================== СБОРКА ВИДЕО ======================
    print("Сборка видео через ffmpeg...")
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(FPS),
        "-i", os.path.join(TEMP_DIR, "frame_%05d.png"),
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", OUTPUT_VIDEO
    ])

    shutil.rmtree(TEMP_DIR)
    print(f"Готово! Видео сохранено: {OUTPUT_VIDEO}")


if __name__ == "__main__":
    main()