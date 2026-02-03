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
SPEED_FACTOR = 0.15 

# === ИСПРАВЛЕНИЕ ШРИФТОВ ===
plt.rcParams['font.family'] = 'Segoe UI Emoji'

COLORS = {
    'Toyota': '#EB0A1E', 'VW Group': '#001E50', 'GM': '#294F94',
    'Ford': '#003478', 'Hyundai-Kia': '#002C5F', 'BYD': '#00A3A5',
    'Tesla': '#E82127', 'Stellantis': '#004780', 'Honda': '#CC0000',
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

# Загружаем
df_raw = load_data(FILENAME)
df, frames = interpolate_data(df_raw, FRAMES_PER_YEAR)

# 2. НАСТРОЙКА ГРАФИКА
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
    
    for spine in ax.spines.values():
        spine.set_visible(False)
    plt.title('Nexus Innovate: Car Sales Race', size=14, loc='left', color='#333333')

# 3. ФУНКЦИЯ ЗАМЕДЛЕНИЯ
def create_smooth_slowmo(input_file, output_file, speed_factor=0.15):
    print(f"\n--- ЗАПУСК FFmpeg (Замедление x{speed_factor}) ---")
    pts_multiplier = 1 / speed_factor
    
    # Расчет общей длительности для прогресс-бара
    total_duration_final = (len(extended_frames) / VIDEO_FPS) * pts_multiplier

    # ОЧИЩЕННЫЙ ФИЛЬТР (без scdet)
    filter_str = f"setpts={pts_multiplier}*PTS,minterpolate=mi_mode=mci:mc_mode=aobmc:vsbmc=1"

    cmd = [
        'ffmpeg', '-y', '-hide_banner', '-stats',
        '-i', input_file,
        '-vf', filter_str,
        '-c:v', 'libx264', '-crf', '20', '-preset', 'medium',
        '-pix_fmt', 'yuv420p',
        output_file
    ]

    process = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, 
                               universal_newlines=True, encoding='utf-8')
    
    pbar = tqdm(total=100, desc="Рендеринг (Nexus Innovate)", unit="%")
    time_pattern = re.compile(r"time=(\d+):(\d+):(\d+\.\d+)")
    
    full_stderr = []

    while True:
        line = process.stderr.readline()
        if not line and process.poll() is not None:
            break
        if line:
            full_stderr.append(line)
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

    if process.returncode != 0:
        print("\n❌ ОШИБКА FFMPEG (Лог последних строк):")
        print("".join(full_stderr[-10:]))
    else:
        print(f"\n✅ УСПЕХ! Видео с 2026 годом готово: {output_file}")

# 4. ЗАПУСК
print("1. Подготовка кадров...")
# Добавляем 4 секунды (с запасом) 2026 года в конце
extra_padding = [frames[-1]] * (VIDEO_FPS * 4)
extended_frames = np.concatenate([frames, extra_padding])

temp_file = 'temp_original.mp4'
final_file = 'car_race_2026_FINAL.mp4'

print("2. Генерация временного файла...")
anim = animation.FuncAnimation(fig, draw_barchart, frames=extended_frames, interval=1000/VIDEO_FPS, repeat=False)
anim.save(temp_file, writer='ffmpeg', fps=VIDEO_FPS, dpi=144)

# Запуск замедления
create_smooth_slowmo(temp_file, final_file, speed_factor=SPEED_FACTOR)