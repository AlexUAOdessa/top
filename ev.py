import os
import subprocess
import shutil
import colorsys
from PIL import Image, ImageDraw, ImageFont

# --- 1. ГЛОБАЛЬНЫЕ НАСТРОЙКИ ---
current_dir = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(current_dir, "input.txt")
TEMP_DIR = os.path.join(current_dir, "frames_pro")
LOGOS_DIR = r"c:\Python\top\logos"
OUTPUT_VIDEO = os.path.join(current_dir, "vw_5min_staggered.mp4")

FPS = 60                      
# 4.6 сек * 66 лет ≈ 303 секунды (5 минут)
SECONDS_PER_YEAR = 4.6        
FRAMES_PER_PERIOD = int(FPS * SECONDS_PER_YEAR)

WIDTH, HEIGHT = 1920, 1080
BG_COLOR = (248, 250, 252)

BAR_X_START = 520    
BAR_MAX_WIDTH = 1200 
BAR_HEIGHT = 78     
BAR_SPACING = 10     # Плотная сетка

color_map = {
    "Beetle": (230, 180, 0), "Golf": (0, 70, 150), "Tiguan": (200, 0, 0),
    "ID.4": (0, 180, 255), "Polo": (100, 100, 100), "Passat": (50, 150, 50)
}

def get_color(name):
    if name in color_map: return color_map[name]
    h = (abs(hash(name)) % 100) / 100.0
    color_map[name] = tuple(int(c * 255) for c in colorsys.hsv_to_rgb(h, 0.65, 0.85))
    return color_map[name]

def draw_frame(f_idx, year, items):
    img = Image.new('RGB', (WIDTH, HEIGHT), color=BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    try:
        f_year = ImageFont.truetype("arialbd.ttf", 200)
        f_m = ImageFont.truetype("arial.ttf", 36)
        f_v = ImageFont.truetype("arialbd.ttf", 40)
        f_title = ImageFont.truetype("arialbd.ttf", 55)
    except:
        f_year = f_m = f_v = f_title = ImageFont.load_default()

    # ГОД: Правый нижний угол, четкий темно-серый цвет
    draw.text((WIDTH - 60, HEIGHT - 60), str(int(year)), fill=(50, 60, 70), font=f_year, anchor="rs")
    draw.text((WIDTH//2, 70), "VOLKSWAGEN: SALES HISTORY", fill=(0, 40, 80), font=f_title, anchor="mm")

    # Авто-масштаб по текущему лидеру
    c_max = max([it[2] for it in items] + [10])
    items.sort(key=lambda x: x[1])

    for name, rank, val in items:
        if rank > 10.5 or val < 1: continue

        y = 150 + rank * (BAR_HEIGHT + BAR_SPACING)
        w = int((val / c_max) * BAR_MAX_WIDTH)
        col = get_color(name)

        # Рисуем полосу
        draw.rounded_rectangle([BAR_X_START, y, BAR_X_START + w, y + BAR_HEIGHT], radius=10, fill=col)
        # Название и значение
        draw.text((BAR_X_START - 20, y + BAR_HEIGHT//2), name, fill=(30, 30, 30), font=f_m, anchor="rm")
        draw.text((BAR_X_START + w + 15, y + BAR_HEIGHT//2), f"{int(val)}k", fill=(0, 0, 0), font=f_v, anchor="lm")

        # Логотип
        l_path = os.path.join(LOGOS_DIR, f"{name}.png")
        if os.path.exists(l_path):
            try:
                logo = Image.open(l_path).convert("RGBA")
                logo.thumbnail((110, 110))
                img.paste(logo, (BAR_X_START - 440, int(y - 15)), logo)
            except: pass

    img.save(os.path.join(TEMP_DIR, f"f_{f_idx:05d}.png"))

def main():
    if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)
    
    milestones = {}
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            p = [x.strip() for x in line.split('|')]
            y, m, r, v = int(p[0]), p[1], int(p[2])-1, float(p[3])
            if y not in milestones: milestones[y] = {}
            milestones[y][m] = {'r': r, 'v': v}

    years = sorted(milestones.keys())
    frame_count = 0

    # ГЕНЕРАЦИЯ КАЖДОГО ГОДА
    for i in range(len(years)-1):
        y_start, y_end = years[i], years[i+1]
        all_m = set(milestones[y_start].keys()) | set(milestones[y_end].keys())
        
        # Для каждого года между вехами
        for current_y in range(y_start, y_end):
            # Процесс внутри одного года
            for f in range(FRAMES_PER_PERIOD):
                t = f / FRAMES_PER_PERIOD
                frame_data = []
                
                # Интерполяция для каждого года
                y_prog = (current_y - y_start) / (y_end - y_start)
                next_y_prog = (current_y + 1 - y_start) / (y_end - y_start)
                
                for m in all_m:
                    # Стартовые и конечные значения для ТЕКУЩЕГО года
                    v_s = milestones[y_start].get(m, {'v':0, 'r':11})['v']
                    v_e = milestones[y_end].get(m, {'v':0, 'r':11})['v']
                    r_s = milestones[y_start].get(m, {'v':0, 'r':11})['r']
                    r_e = milestones[y_end].get(m, {'v':0, 'r':11})['r']
                    
                    # Значения на начало и конец секунды
                    val_now = v_s + (v_e - v_s) * y_prog
                    val_next = v_s + (v_e - v_s) * next_y_prog
                    rank_now = r_s + (r_e - r_s) * y_prog
                    rank_next = r_s + (r_e - r_s) * next_y_prog

                    # --- ПООЧЕРЕДНОЕ ДВИЖЕНИЕ ---
                    # Столбцы сверху (низкий ранг) начинают движение раньше
                    stagger_delay = rank_now * 0.04 
                    local_t = max(0, min(1, (t - stagger_delay) / 0.6))
                    ease_t = 1 - (1 - local_t)**3 # Ease Out
                    
                    frame_data.append((m, rank_now + (rank_next - rank_now) * ease_t, 
                                          val_now + (val_next - val_now) * ease_t))
                
                draw_frame(frame_count, current_y, frame_data)
                frame_count += 1
            print(f"Год {current_y} готов")

    subprocess.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", os.path.join(TEMP_DIR, "f_%05d.png"), 
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", OUTPUT_VIDEO])
    shutil.rmtree(TEMP_DIR)

if __name__ == "__main__":
    main()