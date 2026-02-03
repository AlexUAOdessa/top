# 1. Подготовка среды
!pip install tqdm pandas matplotlib numpy

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.ticker import StrMethodFormatter
import numpy as np
import subprocess
import os
import re
from tqdm import tqdm
from google.colab import files

# --- НАСТРОЙКИ ---
FILENAME = 'car_sales.csv'
FRAMES_PER_YEAR = 15
VIDEO_FPS = 30
SPEED_FACTOR = 0.15 
USE_GPU = True  # Включить использование T4 GPU (h264_nvenc)

plt.rcParams['font.family'] = 'DejaVu Sans'

COLORS = {
    'Toyota': '#EB0A1E', 'VW Group': '#001E50', 'GM': '#294F94',
    'Ford': '#003478', 'Hyundai-Kia': '#002C5F', 'BYD': '#00A3A5',
    'Tesla': '#E82127', 'Stellantis': '#004780', 'Honda': '#CC0000',
    'Nissan': '#C3002F'
}

# 1. ЗАГРУЗКА ДАННЫХ
def load_data(filename):
    if not os.path.exists(filename):
        print(f"❌ ОШИБКА: Загрузите {filename} в Colab!")
        return None
    df = pd.read_csv(filename)
    df.set_index('Year', inplace=True)
    return df

def interpolate_data(df, frames_per_year):
    years_expanded = np.linspace(df.index.min(), df.index.max(), 
                                 num=int((df.index.max() - df.index.min()) * frames_per_year))
    df_interp = df.reindex(df.index.union(years_expanded)).interpolate(method='linear').reindex(years_expanded)
    return df_interp, years_expanded

# 2. ОРИСОВКА
fig, ax = plt.subplots(figsize=(12, 7))

def draw_barchart(current_year):
    d = df.loc[current_year].sort_values(ascending=True).tail(10)
    ax.clear()
    y_pos = np.arange(len(d))
    ax.barh(y_pos, d.values, color=[COLORS.get(x, '#adb5bd') for x in d.index], height=0.8)
    ax.set_xlim(0, 13)
    ax.xaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}M'))
    ax.xaxis.set_ticks_position('top')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(d.index, size=11, fontweight='bold')
    for i, (value, name) in enumerate(zip(d.values, d.index)):
        ax.text(value + 0.1, i, f'{value:,.1f}M', ha='left', va='center', size=10, fontweight='bold')
    ax.text(0.95, 0.2, int(current_year), transform=ax.transAxes, color='#00CC00', size=50, ha='right', weight=800)
    for spine in ax.spines.values(): spine.set_visible(False)
    plt.title('Nexus Innovate: Global Car Market Evolution', size=14, loc='left')

# 3. ФУНКЦИЯ ОБРАБОТКИ
def process_video(input_file, output_file, thumb_file, speed_factor=0.15):
    print(f"\n--- РЕНДЕРИНГ (GPU: {USE_GPU}) ---")
    pts_multiplier = 1 / speed_factor
    total_duration = (len(extended_frames) / VIDEO_FPS) * pts_multiplier

    # Выбор кодека: NVENC для GPU T4 или libx264 для CPU
    codec = 'h264_nvenc' if USE_GPU else 'libx264'
    
    # Команда для замедления
    filter_str = f"setpts={pts_multiplier}*PTS,minterpolate=mi_mode=mci:mc_mode=aobmc:vsbmc=1"
    
    cmd = [
        'ffmpeg', '-y', '-i', input_file,
        '-vf', filter_str,
        '-c:v', codec, '-preset', 'p4', # p4 - оптимальный пресет для NVENC
        '-b:v', '5M', # Битрейт для высокого качества
        '-pix_fmt', 'yuv420p', output_file
    ]

    process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True)
    pbar = tqdm(total=100, desc="Прогресс видео", unit="%")
    time_pattern = re.compile(r"time=(\d+):(\d+):(\d+\.\d+)")

    while True:
        line = process.stderr.readline()
        if not line and process.poll() is not None: break
        match = time_pattern.search(line)
        if match:
            h, m, s = map(float, match.groups())
            current_time = h * 3600 + m * 60 + s
            pbar.n = min(99.9, round((current_time / total_duration) * 100, 1))
            pbar.refresh()
    pbar.n = 100; pbar.close(); process.wait()

    # СОЗДАНИЕ ОБЛОЖКИ (Thumbnail) - берем последний кадр
    print("--- СОЗДАНИЕ ОБЛОЖКИ ---")
    thumb_cmd = ['ffmpeg', '-y', '-sseof', '-1', '-i', output_file, '-update', '1', '-q:v', '2', thumb_file]
    subprocess.run(thumb_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# 4. ЗАПУСК
df_raw = load_data(FILENAME)
if df_raw is not None:
    df, frames = interpolate_data(df_raw, FRAMES_PER_YEAR)
    extra_padding = [frames[-1]] * (VIDEO_FPS * 3)
    extended_frames = np.concatenate([frames, extra_padding])

    temp_file = 'temp.mp4'
    final_video = 'nexus_race_2026.mp4'
    final_thumb = 'nexus_thumbnail_2026.jpg'

    print("Шаг 1: Генерация кадров...")
    anim = animation.FuncAnimation(fig, draw_barchart, frames=extended_frames, interval=1000/VIDEO_FPS)
    anim.save(temp_file, writer='ffmpeg', fps=VIDEO_FPS, dpi=150)

    print("Шаг 2: Замедление и обложка...")
    process_video(temp_file, final_video, final_thumb, speed_factor=SPEED_FACTOR)

    print("\n--- ГОТОВО! СКАЧИВАНИЕ... ---")
    files.download(final_video)
    files.download(final_thumb)