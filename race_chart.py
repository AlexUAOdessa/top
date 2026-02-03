import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.ticker import StrMethodFormatter
import numpy as np

# --- НАСТРОЙКИ ---
FILENAME = 'car_sales.csv'
FRAMES_PER_YEAR = 15
VIDEO_FPS = 30

# === ИСПРАВЛЕНИЕ ШРИФТОВ (WINDOWS) ===
# Используем системный шрифт, который поддерживает эмодзи
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
    
    # Рисуем бары
    y_pos = np.arange(len(d))
    ax.barh(y_pos, d.values, color=[COLORS.get(x, '#adb5bd') for x in d.index], height=0.8)
    
    # Настройки осей
    ax.set_xlim(0, 13)
    ax.xaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}M'))
    ax.xaxis.set_ticks_position('top')
    ax.tick_params(axis='x', colors='#777777', labelsize=10)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(d.index, size=11, fontweight='bold')
    
    # Значения справа
    for i, (value, name) in enumerate(zip(d.values, d.index)):
        ax.text(value + 0.1, i, f'{value:,.1f}M', ha='left', va='center', size=10, fontweight='bold', color='#444444')

    # === STORYTELLING EVENTS ===
    
    year_int = int(current_year)
    
    # --- ИЗМЕНЕНИЕ ЦВЕТА ЗДЕСЬ ---
    # color='#00CC00' — это ярко-зеленый (Matrix green)
    ax.text(0.95, 0.2, year_int, transform=ax.transAxes, color='#00CC00', size=50, ha='right', weight=800)
    ax.text(0.95, 0.14, 'Global Car Sales', transform=ax.transAxes, color='#999999', size=14, ha='right')

    # Логика событий
    
    # 2008-2009: GM Crisis
    if 2008.5 <= current_year <= 2009.8:
        if 'GM' in d.index:
            idx = list(d.index).index('GM')
            val = d['GM']
            ax.annotate('📉 BANKRUPTCY', 
                        xy=(val, idx), xytext=(val + 2, idx),
                        arrowprops=dict(facecolor='#D32F2F', shrink=0.05),
                        fontsize=12, color='#D32F2F',
                        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#D32F2F", alpha=0.9))

    # 2015: VW Dieselgate
    if 2015.5 <= current_year <= 2016.2:
        if 'VW Group' in d.index:
            idx = list(d.index).index('VW Group')
            val = d['VW Group']
            ax.annotate('💨 DIESELGATE', 
                        xy=(val, idx), xytext=(val + 1.5, idx),
                        arrowprops=dict(facecolor='black', shrink=0.05),
                        fontsize=12, color='black')

    # 2020: COVID
    if 2020.0 <= current_year <= 2020.9:
        ax.text(0.5, 0.5, '😷 PANDEMIC CRASH', transform=ax.transAxes, 
                ha='center', va='center', size=24, color='#C62828',
                bbox=dict(boxstyle="round,pad=0.6", fc="white", ec="#C62828", alpha=0.9))

    # 2024+: China/BYD Rise
    if current_year >= 2024.0:
        if 'BYD' in d.index:
            idx = list(d.index).index('BYD')
            val = d['BYD']
            if val > 3.0:
                ax.text(val - 0.2, idx, '🚀 CHINA RISING', color='white', ha='right', va='center')

    for spine in ax.spines.values():
        spine.set_visible(False)
    
    plt.title('Nexus Innovate: Global Auto Market (2000-2026)', size=14, loc='left', color='#333333')

# 3. ЗАПУСК
print("Генерация видео...")
anim = animation.FuncAnimation(fig, draw_barchart, frames=frames, interval=1000/VIDEO_FPS, repeat=False)
anim.save('car_race_2026.mp4', writer='ffmpeg', fps=VIDEO_FPS, dpi=150)
print("Готово!")
plt.show()