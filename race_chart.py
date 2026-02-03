# =================================================================
# NEXUS INNOVATE: УЛЬТИМАТИВНЫЙ ГЕНЕРАТОР ВИДЕО-ГРАФИКОВ (ИСПРАВЛЕННЫЙ)
# =================================================================
# Данный скрипт создает динамический график гонки производителей.
# Исправлено: проблема "0 длины" и обрезка финала на 2025 году.
# =================================================================

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.ticker import StrMethodFormatter
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import numpy as np
import subprocess
import os
import re
from tqdm import tqdm


# --- 1. ГЛОБАЛЬНЫЕ НАСТРОЙКИ (SETTINGS) ---
SETTINGS = {
    'FILENAME': 'car_sales.csv',    # Имя файла с данными
    'ORIENTATION': '9:16',          # '9:16' (Shorts/TikTok) или '16:9' (YouTube)
    'LOGO_DIR': 'logos',            # Папка с PNG логотипами
    'SHOW_LOGOS': True,             # Отображать логотипы на барах
    
    # ПАРАМЕТРЫ СКОРОСТИ
    'APPLY_SLOWMO': False,          # ВКЛЮЧИТЬ замедление через FFmpeg
    'SPEED_FACTOR': 0.15,           # Коэффициент замедления (0.15 = 15% от ориг. скорости)
    
    # ТЕХНИЧЕСКИЕ НАСТРОЙКИ
    'USE_GPU': False,               # Поставьте True только если есть NVIDIA GPU
    'VIDEO_FPS': 60,                # Частота кадров
    'DPI': 144,                     # Качество изображения
    'FRAMES_PER_YEAR': 15,          # Количество кадров анимации на один год
    'EXTRA_FINAL_PAUSE': 5          # ЗАПАС В КОНЦЕ (сек): чтобы видео не обрывалось на 2025!
}

# Настройка шрифтов (Arial лучше всего подходит для английского языка)
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['axes.unicode_minus'] = False 

# Цветовая палитра брендов (официальные цвета)
COLORS = {
    'Toyota': '#EB0A1E', 'Honda': '#CC0000', 'Nissan': '#C3002F', 
    'VW Group': '#001E50', 'BMW': '#1C69D2', 'Mercedes-Benz': '#000000',
    'GM': '#294F94', 'Ford': '#003478', 'Tesla': '#E82127', 
    'Hyundai-Kia': '#002C5F', 'BYD': '#00A3A5', 'Volvo': '#003057'
}

# --- 2. ПОДГОТОВКА ДАННЫХ ---
def prepare_data():
    """Загрузка CSV и создание плавных переходов между годами"""
    if not os.path.exists(SETTINGS['FILENAME']):
        raise FileNotFoundError(f"Файл {SETTINGS['FILENAME']} не найден!")
    
    df = pd.read_csv(SETTINGS['FILENAME']).set_index('Year')
    # Линейная интерполяция данных
    years_expanded = np.linspace(df.index.min(), df.index.max(), 
                                 num=int((df.index.max() - df.index.min()) * SETTINGS['FRAMES_PER_YEAR']))
    df_interp = df.reindex(df.index.union(years_expanded)).interpolate(method='linear').reindex(years_expanded)
    return df_interp, years_expanded

# --- 3. НАСТРОЙКА ВИЗУАЛИЗАЦИИ ---
# Автоматический выбор размеров под формат видео
if SETTINGS['ORIENTATION'] == '9:16':
    fig, ax = plt.subplots(figsize=(7, 12.4))
    TITLE_SIZE, LABEL_SIZE, YEAR_SIZE, LOGO_ZOOM = 22, 16, 75, 0.15
else:
    fig, ax = plt.subplots(figsize=(12.5, 7))
    TITLE_SIZE, LABEL_SIZE, YEAR_SIZE, LOGO_ZOOM = 18, 14, 60, 0.22

def draw_barchart(current_year):
    """Функция отрисовки каждого кадра анимации с исправленным положением текста"""
    d = df.loc[current_year].sort_values(ascending=True).tail(10)
    ax.clear()
    
    y_pos = np.arange(len(d))
    bar_colors = [COLORS.get(x, '#adb5bd') for x in d.index]
    
    ax.barh(y_pos, d.values, color=bar_colors, height=0.8)
    
    # Оформление осей
    ax.set_xlim(0, 13)
    ax.xaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}M'))
    ax.xaxis.set_ticks_position('top')
    ax.tick_params(axis='x', colors='#777777', labelsize=LABEL_SIZE-4)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(d.index, size=LABEL_SIZE, fontweight='bold', color='#333333')
    
    for i, (value, name) in enumerate(zip(d.values, d.index)):
        ax.text(value + 0.2, i, f'{value:,.1f}M', ha='left', va='center', 
                size=LABEL_SIZE, fontweight='bold', color='#444444')
        
        if SETTINGS['SHOW_LOGOS']:
            logo_path = os.path.join(SETTINGS['LOGO_DIR'], f"{name}.png")
            if os.path.exists(logo_path):
                img = plt.imread(logo_path)
                imagebox = OffsetImage(img, zoom=LOGO_ZOOM)
                ab = AnnotationBbox(imagebox, (value - 0.5, i), frameon=False, box_alignment=(1, 0.5))
                ax.add_artist(ab)

    
    # 1. Опускаем год вниз (изменили y_year_pos с 0.15 на 0.05)
    y_year_pos = 0.05 if SETTINGS['ORIENTATION'] == '9:16' else 0.1
    ax.text(0.95, y_year_pos, int(current_year), transform=ax.transAxes, 
            color='#00CC00', size=YEAR_SIZE, ha='right', weight=900, alpha=0.7)

    # 2. Смещаем заголовок влево (добавили параметр x=-0.15)
    title_x = -0.15 if SETTINGS['ORIENTATION'] == '9:16' else 0
    plt.title('NEXUS INNOVATE: GLOBAL CAR SALES', size=TITLE_SIZE, 
              loc='left', weight='bold', pad=40, x=title_x)

    for spine in ax.spines.values(): spine.set_visible(False)
    
    # 3. Настройка отступов всей фигуры, чтобы текст не обрезался
    plt.subplots_adjust(left=0.15, right=0.95, top=0.88, bottom=0.08)

# --- 4. FFmpeg ОБРАБОТКА (ИСПРАВЛЕННАЯ) ---
def run_ffmpeg_processing(input_file, output_file):
    """Сборка финального видео без ошибок с "0 длиной"""
    codec = 'h264_nvenc' if SETTINGS['USE_GPU'] else 'libx264'
    preset = 'p4' if SETTINGS['USE_GPU'] else 'medium'
    
    if SETTINGS['APPLY_SLOWMO']:
        print(f"\n--- ПРИМЕНЕНИЕ SLOW-MOTION (x{SETTINGS['SPEED_FACTOR']}) ---")
        pts_multiplier = 1 / SETTINGS['SPEED_FACTOR']
        # ИСПРАВЛЕНИЕ: Удален scdet для совместимости
        filter_str = f"setpts={pts_multiplier}*PTS,minterpolate=mi_mode=mci:mc_mode=aobmc:vsbmc=1"
        total_duration = (len(extended_frames) / SETTINGS['VIDEO_FPS']) * pts_multiplier
    else:
        print("\n--- РЕЖИМ: ОБЫЧНАЯ СКОРОСТЬ ---")
        filter_str = "null"
        total_duration = len(extended_frames) / SETTINGS['VIDEO_FPS']

    cmd = [
        'ffmpeg', '-y', '-hide_banner', '-i', input_file,
        '-vf', filter_str,
        '-c:v', codec, '-preset', preset,
        '-b:v', '6M', '-pix_fmt', 'yuv420p',
        output_file
    ]

    process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True, encoding='utf-8')
    pbar = tqdm(total=100, desc="Rendering Final Video", unit="%")
    t_regex = re.compile(r"time=(\d+):(\d+):(\d+\.\d+)")

    while True:
        line = process.stderr.readline()
        if not line and process.poll() is not None: break
        match = t_regex.search(line)
        if match:
            h, m, s = map(float, match.groups())
            curr_time = h * 3600 + m * 60 + s
            pbar.n = min(99.9, round((curr_time / total_duration) * 100, 1))
            pbar.refresh()
    
    pbar.n = 100; pbar.close(); process.wait()

# --- 5. ЗАПУСК ГЕНЕРАЦИИ ---
if __name__ == '__main__':
    try:
        # Шаг 1: Подготовка данных
        df, frames = prepare_data()
        
        # Шаг 2: ФИКС 2026 ГОДА (Добавление запаса кадров в конец)
        extra_padding = [frames[-1]] * (SETTINGS['VIDEO_FPS'] * SETTINGS['EXTRA_FINAL_PAUSE'])
        extended_frames = np.concatenate([frames, extra_padding])

        temp_raw = 'temp_raw.mp4'
        final_video = f"nexus_innovate_race_{SETTINGS['ORIENTATION'].replace(':','x')}.mp4"

        # Удаление старых файлов
        for f in [temp_raw, final_video]:
            if os.path.exists(f): os.remove(f)

        print(f"Этап 1: Генерация базовой анимации ({len(extended_frames)} кадров)...")
        anim = animation.FuncAnimation(fig, draw_barchart, frames=extended_frames, interval=1000/SETTINGS['VIDEO_FPS'])
        
        # Сохранение временного файла
        anim.save(temp_raw, writer='ffmpeg', fps=SETTINGS['VIDEO_FPS'], dpi=SETTINGS['DPI'])

        # Этап 2: Финальная обработка через FFmpeg
        run_ffmpeg_processing(temp_raw, final_video)

        if os.path.exists(temp_raw): os.remove(temp_raw)
        print(f"\n✅ УСПЕХ! Видео готово: {final_video}")
        

    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")