import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.patheffects as path_effects
import matplotlib.ticker as ticker
import os

# --- НАСТРОЙКИ ---
DATA_FILE = 'engines_data.csv'
LOGOS_DIR = 'logos'
OUTPUT_FILE = 'engine_race_final_consistent.mp4'
INTERVAL = 2000 
LOGO_ZOOM = 0.18 
FONT_SIZE = 14

# --- ЦВЕТОВАЯ ПАЛИТРА БРЕНДОВ ---
# Здесь вы можете задать конкретные цвета для узнаваемости.
# Все остальные бренды получат случайные, но фиксированные цвета.
BRAND_COLORS = {
    'Ferrari': '#FF0000',      # Красный
    'BMW': '#0066AD',          # Синий
    'Mercedes-AMG': '#C0C0C0', # Серебристый
    'Lamborghini': '#FFCC00',  # Желтый
    'Porsche': '#000000',      # Черный
    'Bugatti': '#0000FF',      # Ярко-синий
    'Ford': '#003478',         # Темно-синий
    'McLaren': '#FF8700',      # Оранжевый
    'Audi': '#BB0A30',         # Красный Audi
}

# --- ПОДГОТОВКА ДАННЫХ И ФИКСАЦИЯ ЦВЕТОВ ---
df = pd.read_csv(DATA_FILE)
unique_companies = sorted(df['Company'].unique()) # Сортировка важна для стабильности индексов

# Создаем единую карту цветов на весь ролик
colormap = plt.get_cmap('tab20')
company_colors = {}
for i, company in enumerate(unique_companies):
    if company in BRAND_COLORS:
        company_colors[company] = BRAND_COLORS[company]
    else:
        # Берем цвет из палитры tab20 по индексу
        company_colors[company] = colormap(i % 20)

# --- НАСТРОЙКА ФИГУРЫ ---
fig, ax = plt.subplots(figsize=(9, 16))
fig.patch.set_facecolor('white')

def get_logo(company_name):
    path = os.path.join(LOGOS_DIR, f"{company_name}.png")
    if os.path.exists(path):
        return plt.imread(path)
    return None

def animate(year):
    ax.clear()
    ax.set_facecolor('white')
    
    # Данные за год
    top_10 = df[df['Year'] == year].nlargest(10, 'Horsepower').sort_values(by='Horsepower', ascending=True)
    overall_max_hp = df['Horsepower'].max()
    max_hp_limit = overall_max_hp * 1.3 # Запас места справа для текста

    # 1. СЕТКА
    ax.xaxis.set_major_locator(ticker.MultipleLocator(200))
    ax.xaxis.grid(True, linestyle='--', alpha=0.3, color='gray', zorder=0)
    ax.set_axisbelow(True)

    # 2. СТОЛБЦЫ (Используем зафиксированные цвета)
    colors = [company_colors[c] for c in top_10['Company']]
    ax.barh(top_10['Engine_Name'], top_10['Horsepower'], color=colors, 
            height=0.6, edgecolor='black', linewidth=0.5, zorder=3)

    # 3. ОФОРМЛЕНИЕ
    ax.set_xlim(0, max_hp_limit)
    ax.set_yticks([]) 
    ax.set_xlabel('Horsepower (HP)', fontsize=15, fontweight='bold', labelpad=15)
    ax.set_title(f'YEAR: {year}\nTOP 10 ENGINE PERFORMANCE', 
                 fontsize=24, fontweight='bold', pad=40, color='#222222')
    
    for spine in ['top', 'right', 'left']:
        ax.spines[spine].set_visible(False)

    # --- ОТСТУПЫ ---
    logo_x = overall_max_hp * 0.02
    text_x = overall_max_hp * 0.25 # Еще больше увеличил промежуток по вашей просьбе

    # 4. ОТРИСОВКА
    for i, (idx, row) in enumerate(top_10.iterrows()):
        company = row['Company']
        display_text = f"{row['Engine_Name']}   |   {row['Displacement']}L   |   {row['Horsepower']} HP"

        # Логотип
        img = get_logo(company)
        if img is not None:
            imagebox = OffsetImage(img, zoom=LOGO_ZOOM)
            ab = AnnotationBbox(imagebox, (logo_x, i),
                                frameon=False, box_alignment=(0, 0.5),
                                xycoords='data', zorder=4)
            ax.add_artist(ab)

        # Текст (черный на белой обводке)
        txt = ax.text(text_x, i, display_text, 
                      va='center', fontsize=FONT_SIZE, fontweight='bold', color='black', zorder=5)
        txt.set_path_effects([
            path_effects.withStroke(linewidth=3, foreground='white'),
            path_effects.Normal()
        ])

# --- СОХРАНЕНИЕ ---
years = sorted(df['Year'].unique())
frames = years + [years[-1]] * 3

try:
    # Убедитесь, что fps=1 соответствует вашему желаемому темпу (1 год в секунду)
    writer = animation.FFMpegWriter(fps=1, metadata=dict(artist='Engine Stats'), bitrate=2500)
    print("Generating video with consistent brand colors...")
    ani = animation.FuncAnimation(fig, animate, frames=frames, interval=INTERVAL)
    ani.save(OUTPUT_FILE, writer=writer)
    print(f"Success! Video saved as {OUTPUT_FILE}")
except Exception as e:
    print(f"Error: {e}. Check if ffmpeg is installed.")