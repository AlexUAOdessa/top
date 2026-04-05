import os
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageOps

# --- CONFIGURATION ---
current_dir = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(current_dir, "input.txt")
TEMP_DIR = os.path.join(current_dir, "images_smooth")
FLAGS_DIR = os.path.join(current_dir, "flag") 
OUTPUT_VIDEO = os.path.join(current_dir, "space_race_2026_fixed.mp4")

FPS = 60                      
SECONDS_PER_YEAR = 3.5 
FRAMES_PER_PERIOD = int(FPS * SECONDS_PER_YEAR)

WIDTH, HEIGHT = 1920, 1080
BG_COLOR = (230, 230, 230) 

BAR_X_START = 400    
BAR_MAX_WIDTH = 1200 
BAR_HEIGHT = 65     
BAR_SPACING = 30     
FLAG_SIZE = (85, 55) 

COUNTRY_TO_CODE = {
    "USA": "us", "Russia": "ru", "China": "cn", 
    "France": "fr", "Japan": "jp", "India": "in", "Europe": "eu"
}

COLOR_MAP = {
    "USA": (0, 32, 91), "USSR": (205, 0, 0), "Russia": (255, 215, 0),
    "China": (0, 114, 206), "France": (0, 38, 84), "Japan": (188, 0, 45),
    "India": (255, 153, 51), "Europe": (0, 51, 153)
}

flag_cache = {}

def get_color(name):
    return COLOR_MAP.get(name, (140, 140, 140))

def get_flag_with_border(name):
    if name in flag_cache: return flag_cache[name]
    if name == "USSR":
        img = Image.new("RGBA", FLAG_SIZE, (205, 0, 0, 255))
    else:
        code = COUNTRY_TO_CODE.get(name, name.lower()[:2])
        flag_path = os.path.join(FLAGS_DIR, f"{code}.png")
        try:
            if os.path.exists(flag_path):
                img = Image.open(flag_path).convert("RGBA")
                img = img.resize(FLAG_SIZE, Image.Resampling.LANCZOS)
            else: return None
        except: return None
    bordered_img = ImageOps.expand(img, border=1, fill=(0, 0, 0, 255))
    flag_cache[name] = bordered_img
    return bordered_img

def generate_frame(frame_name, display_year, current_state, global_max):
    img = Image.new('RGB', (WIDTH, HEIGHT), color=BG_COLOR)
    draw = ImageDraw.Draw(img)
    try:
        font_year = ImageFont.truetype("arialbd.ttf", 380) 
        font_main = ImageFont.truetype("arialbd.ttf", 45)
        font_small = ImageFont.truetype("arialbd.ttf", 28)
        font_title = ImageFont.truetype("arialbd.ttf", 85)
    except:
        font_year = font_main = font_small = font_title = ImageFont.load_default()

    year_str = str(int(display_year))
    draw.text((WIDTH - 97, HEIGHT - 97), year_str, fill=(255, 255, 255), font=font_year, anchor="rs")
    draw.text((WIDTH - 100, HEIGHT - 100), year_str, fill=(20, 20, 20), font=font_year, anchor="rs")
    draw.text((WIDTH//2, 85), "SPACE LAUNCHES: TOTAL PROGRESSION", fill=(30, 30, 30), font=font_title, anchor="mm")

    current_state.sort(key=lambda x: x[2], reverse=True) 

    for idx, (name, val_year, val_total, rank_anim) in enumerate(current_state):
        if val_total < 1.0 or idx >= 12: continue
        y_pos = 190 + (rank_anim - 1) * (BAR_HEIGHT + BAR_SPACING)
        bar_w = int((val_total / global_max) * BAR_MAX_WIDTH) if global_max > 0 else 0
        flag_img = get_flag_with_border(name)
        if flag_img:
            img.paste(flag_img, (BAR_X_START - 360, int(y_pos + 3)), flag_img)
        draw.rectangle([BAR_X_START, y_pos, BAR_X_START + bar_w, y_pos + BAR_HEIGHT], fill=get_color(name))
        draw.text((BAR_X_START - 25, y_pos + BAR_HEIGHT//2), name.upper(), fill=(40, 40, 40), font=font_main, anchor="rm")
        draw.text((BAR_X_START + bar_w + 15, y_pos + 5), f"TOTAL: {int(val_total)}", fill=(0, 0, 0), font=font_main)
        draw.text((BAR_X_START + bar_w + 15, y_pos + 42), f"+{int(val_year)} in {int(display_year)}", fill=(80, 80, 80), font=font_small)

    if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)
    img.save(os.path.join(TEMP_DIR, frame_name))

def main():
    if os.path.exists(TEMP_DIR): shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR)

    data_by_year, all_countries = {}, set()
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 4: continue
            y, c, v = int(parts[0]), parts[1], float(parts[3])
            if y not in data_by_year: data_by_year[y] = {}
            data_by_year[y][c] = v
            all_countries.add(c)
    
    years = sorted(list(data_by_year.keys()))
    totals_history, ranks_history, running_totals = {}, {}, {c: 0 for c in all_countries}
    
    for y in years:
        totals_history[y] = {}
        for c in all_countries:
            running_totals[c] += data_by_year[y].get(c, 0)
            totals_history[y][c] = running_totals[c]
        sorted_c = sorted(all_countries, key=lambda c: totals_history[y][c], reverse=True)
        ranks_history[y] = {c: i+1 for i, c in enumerate(sorted_c)}

    global_max = max(max(y_data.values()) for y_data in totals_history.values())
    frame_idx = 0

    print("Step 1: Generating animation frames...")
    for i in range(len(years) - 1):
        y1, y2 = years[i], years[i+1]
        for f in range(FRAMES_PER_PERIOD):
            prog = f / FRAMES_PER_PERIOD
            state = []
            for name in all_countries:
                v_y = data_by_year[y1].get(name, 0)*(1-prog) + data_by_year[y2].get(name, 0)*prog
                v_t = totals_history[y1][name]*(1-prog) + totals_history[y2][name]*prog
                r_a = ranks_history[y1][name]*(1-prog) + ranks_history[y2][name]*prog
                state.append((name, v_y, v_t, r_a))
            generate_frame(f"frame_{frame_idx:05d}.png", y1 + (y2-y1)*prog, state, global_max)
            frame_idx += 1

    # --- ФИКС: ДОБАВЛЯЕМ 2026 ГОД (ФИНАЛЬНАЯ ЗАДЕРЖКА) ---
    print("Step 2: Adding final freeze for 2026...")
    last_year = years[-1]
    final_state = []
    for name in all_countries:
        final_state.append((name, data_by_year[last_year].get(name, 0), totals_history[last_year][name], ranks_history[last_year][name]))
    
    for _ in range(FPS * 7): # Задержать на 7 секунд
        generate_frame(f"frame_{frame_idx:05d}.png", last_year, final_state, global_max)
        frame_idx += 1

    print("Step 3: Encoding video...")
    subprocess.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", os.path.join(TEMP_DIR, "frame_%05d.png"), 
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-b:v", "9000k", OUTPUT_VIDEO])
    print(f"Done! Final video: {OUTPUT_VIDEO}")

if __name__ == "__main__":
    main()