import os
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURATION ---
current_dir = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(current_dir, "input.txt")
TEMP_DIR = os.path.join(current_dir, "images_smooth")
OUTPUT_VIDEO = os.path.join(current_dir, "space_race_no_zeros.mp4")

FPS = 60                      
SECONDS_PER_YEAR = 3.5 # Медленная и плавная анимация
FRAMES_PER_PERIOD = int(FPS * SECONDS_PER_YEAR)

WIDTH, HEIGHT = 1920, 1080
BG_COLOR = (255, 255, 255)
BAR_X_START = 420    
BAR_MAX_WIDTH = 1200 
BAR_HEIGHT = 60     
BAR_SPACING = 30     

COLOR_MAP = {
    "USA": (0, 32, 91), "USSR": (205, 0, 0), "Russia": (0, 114, 206),
    "China": (255, 215, 0), "France": (0, 38, 84), "Japan": (188, 0, 45),
    "India": (255, 153, 51), "Europe": (0, 51, 153)
}

def get_color(name):
    return COLOR_MAP.get(name, (140, 140, 140))

def generate_frame(frame_name, display_year, current_state, global_max):
    img = Image.new('RGB', (WIDTH, HEIGHT), color=BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    try:
        font_year = ImageFont.truetype("arialbd.ttf", 350) 
        font_main = ImageFont.truetype("arialbd.ttf", 45)
        font_title = ImageFont.truetype("arialbd.ttf", 80)
    except:
        font_year = font_main = font_title = ImageFont.load_default()

    # --- ULTRA CONTRAST YEAR ---
    year_str = str(int(display_year))
    # Рисуем жирную черную подложку-тень
    draw.text((WIDTH - 108, HEIGHT - 108), year_str, fill=(20, 20, 20), font=font_year, anchor="rs")
    # Основной текст года (темно-серый)
    draw.text((WIDTH - 100, HEIGHT - 100), year_str, fill=(60, 60, 60), font=font_year, anchor="rs")

    draw.text((WIDTH//2, 80), "SUCCESSFUL ORBITAL LAUNCHES", fill=(20, 20, 20), font=font_title, anchor="mm")

    # Сортируем по рангу, чтобы определить порядок отрисовки
    current_state.sort(key=lambda x: x[1]) 

    # Счетчик для физического расположения на экране (чтобы не было дырок)
    display_index = 0

    for name, rank, val in current_state:
        # ЖЕСТКИЙ ФИЛЬТР: Если значение меньше 1, столбец ВООБЩЕ не рисуется
        if val < 1.0: 
            continue
        
        # Ограничиваем топ-12 странами
        if display_index >= 12: 
            break

        # Рассчитываем позицию Y плавно на основе интерполированного ранга
        y_pos = 180 + (rank - 1) * (BAR_HEIGHT + BAR_SPACING)
        bar_w = max(5, int((val / global_max) * BAR_MAX_WIDTH))
        color = get_color(name)

        # Рисуем столбец
        draw.rectangle([BAR_X_START, y_pos, BAR_X_START + bar_w, y_pos + BAR_HEIGHT], fill=color)
        
        # Названия и цифры
        draw.text((BAR_X_START - 20, y_pos + BAR_HEIGHT//2), name.upper(), fill=(40, 40, 40), font=font_main, anchor="rm")
        draw.text((BAR_X_START + bar_w + 15, y_pos + BAR_HEIGHT//2), str(int(val)), fill=(0, 0, 0), font=font_main, anchor="lm")
        
        display_index += 1

    if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)
    img.save(os.path.join(TEMP_DIR, frame_name))

def main():
    if os.path.exists(TEMP_DIR): shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR)

    data_by_year = {}
    all_countries = set()
    vals_for_scale = []
    
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 4: continue
            y, c, r, v = int(parts[0]), parts[1], int(parts[2]), float(parts[3])
            if y not in data_by_year: data_by_year[y] = {}
            data_by_year[y][c] = {'rank': r, 'val': v}
            all_countries.add(c)
            vals_for_scale.append(v)
    
    years = sorted(list(data_by_year.keys()))
    global_max = max(vals_for_scale) if vals_for_scale else 200
    frame_idx = 0

    print("Step 1: Generating frames without zeros...")
    for i in range(len(years) - 1):
        y1, y2 = years[i], years[i+1]
        d1, d2 = data_by_year[y1], data_by_year[y2]
        
        for f in range(FRAMES_PER_PERIOD):
            prog = f / FRAMES_PER_PERIOD
            state = []
            for name in all_countries:
                i1, i2 = d1.get(name), d2.get(name)
                
                # Если страны нет, она считается за пределами экрана (ранг 15)
                v1, v2 = (i1['val'] if i1 else 0), (i2['val'] if i2 else 0)
                r1, r2 = (i1['rank'] if i1 else 15), (i2['rank'] if i2 else 15)
                
                state.append((name, r1 + (r2 - r1) * prog, v1 + (v2 - v1) * prog))
            
            generate_frame(f"frame_{frame_idx:05d}.png", y1 + (y2 - y1) * prog, state, global_max)
            frame_idx += 1

    # Финальная задержка на 6 секунд
    last_year = years[-1]
    final_state = []
    for name in all_countries:
        info = data_by_year[last_year].get(name, {'rank': 15, 'val': 0})
        final_state.append((name, info['rank'], info['val']))
        
    for _ in range(FPS * 6):
        generate_frame(f"frame_{frame_idx:05d}.png", last_year, final_state, global_max)
        frame_idx += 1

    print("Step 2: Encoding video...")
    ffmpeg_cmd = ["ffmpeg", "-y", "-framerate", str(FPS), "-i", os.path.join(TEMP_DIR, "frame_%05d.png"), 
                  "-c:v", "libx264", "-pix_fmt", "yuv420p", "-b:v", "8000k", OUTPUT_VIDEO]
    subprocess.run(ffmpeg_cmd)
    print(f"Success! Final file: {OUTPUT_VIDEO}")

if __name__ == "__main__":
    main()