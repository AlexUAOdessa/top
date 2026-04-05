import numpy as np
import matplotlib.pyplot as plt
import imageio.v2 as imageio
import os
import shutil

# ---------------- ПОДГОТОВКА ПАПКИ ----------------
temp_dir = "temp"
if os.path.exists(temp_dir):
    shutil.rmtree(temp_dir)
os.makedirs(temp_dir)

# ---------------- ДАННЫЕ (Регионы и типы двигателей) ----------------
years = list(range(2015, 2027))

data = {
    "China | EV":     [0.2, 0.4, 0.6, 1.1, 1.2, 1.5, 3.3, 6.0, 8.0, 10.0, 12.0, 15.0],
    "China | Hybrid": [0.1, 0.1, 0.2, 0.3, 0.4, 0.6, 1.0, 1.5, 2.5, 3.5, 4.5, 6.0],
    "China | ICE":    [24.0, 23.5, 24.0, 22.0, 20.0, 18.0, 16.0, 14.0, 12.0, 10.0, 8.0, 6.5],
    
    "EU | EV":        [0.1, 0.2, 0.3, 0.4, 0.6, 1.3, 2.3, 2.8, 3.2, 3.8, 4.5, 5.5],
    "EU | Hybrid":    [0.4, 0.5, 0.6, 0.8, 1.0, 1.8, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0],
    "EU | ICE":       [14.0, 14.5, 14.5, 13.5, 12.0, 10.0, 8.5, 7.5, 6.5, 5.5, 4.5, 3.5],
    
    "USA | EV":       [0.1, 0.1, 0.2, 0.4, 0.3, 0.4, 0.8, 1.2, 1.8, 2.5, 3.5, 4.5],
    "USA | Hybrid":   [0.4, 0.4, 0.5, 0.5, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.2],
    "USA | ICE":      [17.0, 17.5, 17.5, 17.0, 16.5, 14.0, 13.5, 13.0, 12.5, 11.5, 10.5, 9.0]
}

categories = list(data.keys())
colors_map = {"EV": "#00c853", "Hybrid": "#2979ff", "ICE": "#424242"}
colors = [colors_map[cat.split(" | ")[1]] for cat in categories]

# ---------------- НАСТРОЙКИ ----------------
fps = 30
steps_between_years = 25
final_hold_sec = 4  # Удержание финала 4 секунды
frames_paths = []

fig, ax = plt.subplots(figsize=(9, 16))
# bottom=0.10 прижимает график ближе к тексту года
plt.subplots_adjust(left=0.28, right=0.85, top=0.92, bottom=0.10)

def ease(t):
    return t * t * (3 - 2 * t)

# ---------------- АНИМАЦИЯ ----------------
print("Генерация кадров...")
last_frame_path = ""

for i in range(len(years) - 1):
    for step in range(steps_between_years):
        t = ease(step / steps_between_years)
        ax.clear()
        ax.set_facecolor("white")

        interpolated = []
        for c in categories:
            v1 = data[c][i]
            v2 = data[c][i + 1]
            interpolated.append(v1 + (v2 - v1) * t)

        bars = ax.barh(categories, interpolated, color=colors, height=0.7)
        ax.set_xlim(0, 27) 
        ax.invert_yaxis() 
        
        ax.set_title("Vehicle Sales by Region\n& Powertrain", fontsize=32, weight='bold', pad=20)

        # ГОД (Поднят за счет изменения координаты y на -0.03)
        display_year = years[i] if t < 0.5 else years[i+1]
        ax.text(0.5, -0.01, f"{display_year}", transform=ax.transAxes,
                ha='center', va='top', fontsize=110, color='red', weight='bold')

        # КРУПНЫЕ ЦИФРЫ ПРОДАЖ (Размер 24)
        for bar in bars:
            width = bar.get_width()
            ax.text(width + 0.6, bar.get_y() + bar.get_height()/2,
                    f"{width:.1f}", va='center', fontsize=24, weight='bold')

        # Оформление осей
        ax.spines[['top', 'right', 'bottom']].set_visible(False)
        ax.set_xticks([]) 
        ax.tick_params(axis='y', labelsize=18)

        filename = os.path.join(temp_dir, f"frame_{i:02d}_{step:02d}.png")
        plt.savefig(filename, dpi=120)
        frames_paths.append(filename)
        last_frame_path = filename

# ---------------- ЭКСПОРТ ВИДЕО ----------------
print("Сборка видео...")
output = "car_sales_final_v2.mp4"

with imageio.get_writer(output, fps=fps) as writer:
    # Записываем основную анимацию
    for f_path in frames_paths:
        writer.append_data(imageio.imread(f_path))
    
    # Плавное удержание последнего кадра на 4 секунды (без скачков)
    final_frame_img = imageio.imread(last_frame_path)
    for _ in range(int(final_hold_sec * fps)):
        writer.append_data(final_frame_img)

plt.close(fig)
print(f"ГОТОВО: {output}")