# pip install tqdm
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.ticker import StrMethodFormatter
import numpy as np
import subprocess
import os
import re
from tqdm import tqdm

# --- НАСТРОЙКИ ---
FILENAME = 'car_sales.csv'
FRAMES_PER_YEAR = 15
VIDEO_FPS = 30

# === ИСПРАВЛЕНИЕ ШРИФТОВ (WINDOWS) ===
plt.rcParams['font.family'] = 'Segoe UI Emoji'

# Цвета брендов
COLORS = {
    'Toyota': '#EB0A1E',
    'VW Group': '#001E50',
    'GM': '#294F94',
    'Ford': '#003478',
    'Hyundai-Kia': '#002C5F',
    'BYD': '#00A3A5',
    'Tesla': '#E82127',
    'Stellantis': '#004780',
    'Honda': '#CC0000',
    'Nissan': '#C3002F'
}

# 1. ЗАГРУЗКА И ПОДГОТОВКА ДАННЫХ
def load_data(filename):
    df = pd.read_csv(filename)
    df.set_index('Year', inplace=True)
    return df

def interpolate_data(df, frames_per_year):
    years_expanded = np.linspace(df.index.min(), df.index.max(), 
                                 num=int((df.index.max() - df.index.min()) * frames_per_year))
    df_interp = df.reindex(df.index.union(years_expanded)).interpolate(method='linear').reindex(years_expanded)
    return df_interp, years_expanded

df_raw = load_data(FILENAME)
df, frames = interpolate_data(df_raw, FRAMES_PER_YEAR)

# 2. НАСТРОЙКА ВИЗУАЛИЗАЦИИ
fig, ax = plt.subplots(figsize=(12, 7))

def draw_barchart(current_year):
    d = df.loc[current_year].sort_values(ascending=True).tail(10)
    ax.clear()
    
    y_pos = np.arange(len(d))
    ax.barh(y_pos, d.values, color=[COLORS.get(x, '#adb5bd') for x in d.index], height=0.8)
    
    ax.set_xlim(0, 13)
    ax.xaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}M'))
    ax.xaxis.set_ticks_position('top')
    ax.tick_params(axis='x', colors='#777777', labelsize=10)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(d.index, size=11, fontweight='bold')
    
    for i, (value, name) in enumerate(zip(d.values, d.index)):
        ax.text(value + 0.1, i, f'{value:,.1f}M', ha='left', va='center', size=10, fontweight='bold', color='#444444')

    year_int = int(current_year)
    ax.text(0.95, 0.2, year_int, transform=ax.transAxes, color='#00CC00', size=50, ha='right', weight=800)
    ax.text(0.95, 0.14, 'Global Car Sales', transform=ax.transAxes, color='#999999', size=14, ha='right')

    # Логика событий (кратко)
    if 2008.5 <= current_year <= 2009.8 and 'GM' in d.index:
        idx = list(d.index).index('GM')
        ax.annotate('📉 BANKRUPTCY', xy=(d['GM'], idx), xytext=(d['GM'] + 2, idx),
                    arrowprops=dict(facecolor='#D32F2F', shrink=0.05), fontsize=12, color='#D32F2F')

    if 2020.0 <= current_year <= 2020.9:
        ax.text(0.5, 0.5, '😷 PANDEMIC CRASH', transform=ax.transAxes, ha='center', size=24, color='#C62828')

    for spine in ax.spines.values():
        spine.set_visible(False)
    plt.title('Nexus Innovate: Global Auto Market (2000-2026)', size=14, loc='left', color='#333333')

# 3. ФУНКЦИЯ ПОСТ-ОБРАБОТКИ С ПРОГРЕСС-БАРОМ
def create_smooth_slowmo(input_file, output_file, speed_factor=0.85, preset_ffmpeg='fast'):
    """
    Пресеты FFmpeg:
    - 'ultrafast': максимум скорости, хуже сжатие.
    - 'superfast', 'veryfast', 'faster', 'fast': сбалансированные (сейчас 'fast').
    - 'medium': стандартный.
    - 'slow', 'slower', 'veryslow': лучшее качество/размер, но ОЧЕНЬ долго.
    """
    print(f"\n--- НАЧИНАЮ ЗАМЕДЛЕНИЕ (x{speed_factor}) ---")
    pts_multiplier = 1 / speed_factor
    
    # Примерная длительность финального видео для tqdm
    # (Длительность оригинала * множитель замедления)
    total_duration_final = (len(df) / VIDEO_FPS) * pts_multiplier

    cmd = [
        'ffmpeg', '-y', '-stats',
        '-i', input_file,
        '-filter:v', f"setpts={pts_multiplier}*PTS,minterpolate='mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1'",
        '-c:v', 'libx264', '-crf', '18',
        '-preset', preset_ffmpeg,
        output_file
    ]

    process = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, 
                               universal_newlines=True, encoding='utf-8')
    
    pbar = tqdm(total=100, desc="Рендеринг видео (Nexus Innovate)", unit="%")
    time_pattern = re.compile(r"time=(\d+):(\d+):(\d+\.\d+)")

    while True:
        line = process.stderr.readline()
        if not line and process.poll() is not None:
            break
        
        match = time_pattern.search(line)
        if match:
            h, m, s = map(float, match.groups())
            current_time = h * 3600 + m * 60 + s
            progress = min(99.9, (current_time / total_duration_final) * 100)
            pbar.n = round(progress, 1)
            pbar.refresh()

    pbar.n = 100
    pbar.close()
    process.wait()

    if process.returncode == 0:
        print(f"✅ УСПЕХ! Видео готово: {output_file}")
    else:
        print(f"❌ ОШИБКА FFmpeg (код {process.returncode})")

# 4. ЗАПУСК
print("1. Генерация исходной анимации (Matplotlib)...")
anim = animation.FuncAnimation(fig, draw_barchart, frames=frames, interval=1000/VIDEO_FPS, repeat=False)

normal_speed_file = 'car_race_original.mp4'
final_slow_file = 'car_race_2026_SLOW_MO.mp4'

anim.save(normal_speed_file, writer='ffmpeg', fps=VIDEO_FPS, dpi=150)
print(f"Исходный файл готов: {normal_speed_file}")

# Запуск замедления с прогресс-баром
# speed_factor=0.15 — сильное замедление
# preset_ffmpeg — 'fast', 'medium', 'slow' и т.д.
create_smooth_slowmo(normal_speed_file, final_slow_file, speed_factor=0.15, preset_ffmpeg='fast')

print("\n--- СКРИПТ ЗАВЕРШЕН ---")