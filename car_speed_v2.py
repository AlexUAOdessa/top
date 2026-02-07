import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import os
import re
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.patheffects as path_effects

# =========================
# 1. НАСТРОЙКИ
# =========================
SETTINGS = {
    "CSV_FILE": "car_speed_data_updated.csv", 
    "FORMAT": "9:16",
    "FPS": 60,
    "DPI": 120,
    "SECONDS_PER_TRANSITION": 2.5, 
    "TOP_N": 10,
    "LOGO_DIR": "logos"
}

# =========================
# 2. ПОДГОТОВКА ДАННЫХ
# =========================
def extract_number(value):
    if pd.isna(value): return np.nan
    match = re.search(r"([-+]?\d*\.?\d+)", str(value))
    return float(match.group(1)) if match else np.nan

if not os.path.exists(SETTINGS["CSV_FILE"]):
    SETTINGS["CSV_FILE"] = "car_speed_data.csv"

df = pd.read_csv(SETTINGS["CSV_FILE"])
df["CarLabel"] = df["марка"].str.upper() + " (" + df["модель"] + ")"

for col in ["максимальная_скорость_км_ч", "разгон_0_100_км_ч_сек"]:
    df[col] = df[col].apply(extract_number)

unique_years = sorted(df["год"].unique())
all_cars = df["CarLabel"].unique()
car_to_brand = df.set_index("CarLabel")["марка"].to_dict()

history_speed = []
history_accel = []
current_speed = pd.Series(index=all_cars, dtype=float)
current_accel = pd.Series(index=all_cars, dtype=float)

for yr in unique_years:
    year_data = df[df["год"] == yr]
    for _, row in year_data.iterrows():
        current_speed[row["CarLabel"]] = row["максимальная_скорость_км_ч"]
        current_accel[row["CarLabel"]] = row["разгон_0_100_км_ч_сек"]
    history_speed.append(current_speed.copy())
    history_accel.append(current_accel.copy())

frames_per_step = int(SETTINGS["SECONDS_PER_TRANSITION"] * SETTINGS["FPS"])
total_frames = (len(unique_years) - 1) * frames_per_step

def get_frame_data(frame_idx):
    step = frame_idx // frames_per_step
    alpha = (frame_idx % frames_per_step) / frames_per_step
    if step >= len(unique_years) - 1:
        step, alpha = len(unique_years) - 2, 1.0
        
    s_vals = history_speed[step] * (1 - alpha) + history_speed[step+1] * alpha
    a_vals = history_accel[step] * (1 - alpha) + history_accel[step+1] * alpha
    display_year = unique_years[step] if alpha < 0.5 else unique_years[step+1]
    
    s_active = s_vals.dropna()
    a_active = a_vals.dropna()
    s_ranks = s_active.rank(method='first', ascending=True)
    a_ranks = a_active.rank(method='first', ascending=False)
    
    return s_active, s_ranks, a_active, a_ranks, display_year

# =========================
# 3. ГРАФИКА
# =========================
plt.style.use('default') # Переход на светлую тему

if SETTINGS["FORMAT"] == "9:16":
    fig = plt.figure(figsize=(7, 14.5), facecolor='white')
    gs = fig.add_gridspec(3, 1, height_ratios=[0.08, 0.46, 0.46])
else:
    fig = plt.figure(figsize=(16, 9), facecolor='white')
    gs = fig.add_gridspec(2, 2, height_ratios=[0.85, 0.15])

ax_title, ax_top, ax_bottom = fig.add_subplot(gs[0]), fig.add_subplot(gs[1]), fig.add_subplot(gs[2])
plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05, hspace=0.2)

def draw_logo(ax, car_label, x, y):
    brand = car_to_brand.get(car_label)
    path = os.path.join(SETTINGS["LOGO_DIR"], f"{brand}.png")
    if os.path.exists(path):
        try:
            img = plt.imread(path)
            # Логотип смещен чуть правее текста значения
            ab = AnnotationBbox(OffsetImage(img, zoom=0.07), (x - 0.5, y), frameon=False, box_alignment=(1.1, 0.5))
            ax.add_artist(ab)
        except: pass

def update(i):
    ax_top.clear()
    ax_bottom.clear()
    ax_title.clear()
    
    # Установка белого фона для каждой оси
    for ax in [ax_top, ax_bottom, ax_title]:
        ax.set_facecolor('white')

    s_vals, s_ranks, a_vals, a_ranks, cur_yr = get_frame_data(i)
    
    # Общие настройки эффекта обводки для текста
    stroke = [path_effects.withStroke(linewidth=3, foreground='white')]

    # --- TOP SPEED ---
    n_s = min(len(s_ranks), SETTINGS["TOP_N"])
    top_s_idx = s_ranks.nlargest(n_s).index
    max_s = max(s_vals.max() * 1.1, 400)
    
    for car in top_s_idx:
        val, pos = s_vals[car], s_ranks[car] - (len(s_ranks) - n_s)
        ax_top.barh(pos, val, color="#00d2ff", edgecolor='black', height=0.8)
        
        # Текст от левого края
        txt = ax_top.text(5, pos, f"{car} | {int(val)} km/h", 
                    va='center', ha='left', weight='bold', size=11, color='black')
        txt.set_path_effects(stroke)

    ax_top.set_xlim(0, max_s)
    ax_top.set_ylim(0.4, SETTINGS["TOP_N"] + 0.6)
    ax_top.set_yticks([])
    ax_top.set_title("TOP SPEED (KM/H)", color="black", weight="bold", size=18, pad=15)

    # --- ACCELERATION (0-100 KM/H) ---
    n_a = min(len(a_ranks), SETTINGS["TOP_N"])
    top_a_idx = a_ranks.nlargest(n_a).index
    max_a = max(a_vals.max() * 1.1, 10)
    
    for car in top_a_idx:
        val, pos = a_vals[car], a_ranks[car] - (len(a_ranks) - n_a)
        ax_bottom.barh(pos, val, color="#ff4b2b", edgecolor='black', height=0.8)
        
        # ВАЖНО: Текст начинается от левого края (max_a), так как ось инвертирована
        # Мы используем координаты данных. В инвертированной оси лево — это большее число.
        txt = ax_bottom.text(max_a - 0.2, pos, f"{car} | {val:.2f}s", 
                       va='center', ha='left', weight='bold', size=11, color='black')
        txt.set_path_effects(stroke)
        draw_logo(ax_bottom, car, val, pos)

    ax_bottom.set_xlim(max_a, 0) # Инвертированная ось
    ax_bottom.set_ylim(0.4, SETTINGS["TOP_N"] + 0.6)
    ax_bottom.set_yticks([])
    ax_bottom.set_title("0-100 KM/H (SEC)", color="black", weight="bold", size=18, pad=15)

    # --- YEAR ---
    ax_title.axis("off")
    ax_title.text(0.5, 0.5, f"YEAR: {int(cur_yr)}", ha="center", va="center", 
                  weight="bold", fontsize=50, color='black')

    if i % 30 == 0:
        print(f"Rendering: {int(i/total_frames*100)}%", end='\r')

# =========================
# 4. СОХРАНЕНИЕ
# =========================
ani = animation.FuncAnimation(fig, update, frames=total_frames, interval=1000/SETTINGS["FPS"])
output_file = "car_race_white_clean.mp4"

print(f"Запуск рендеринга... Фон: БЕЛЫЙ. Текст выровнен по левому краю.")
ani.save(output_file, writer='ffmpeg', fps=SETTINGS["FPS"], dpi=SETTINGS["DPI"], 
         codec='libx264', extra_args=['-pix_fmt', 'yuv420p'])

print(f"\n✅ ГОТОВО! Видео сохранено: {output_file}")
plt.close()