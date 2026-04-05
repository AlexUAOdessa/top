import numpy as np
import matplotlib.pyplot as plt
import imageio.v2 as imageio
import os
import shutil

# ---------------- ПОДГОТОВКА ----------------
temp_dir = "temp"
if os.path.exists(temp_dir):
    shutil.rmtree(temp_dir)
os.makedirs(temp_dir)

# ---------------- DATA ----------------
years = list(range(2015, 2027))

data = {
    "EV":     [0.5, 0.7, 1.0, 1.5, 2.2, 3.5, 5.0, 7.5, 10.5, 14.0, 18.0, 22.5],
    "Hybrid": [2.0, 2.3, 2.8, 3.2, 3.8, 4.5, 5.3, 6.0, 6.8, 7.5, 8.0, 10.5],
    "ICE":    [70, 72, 74, 75, 76, 74, 72, 70, 67, 63, 60, 55]
}

categories = list(data.keys())
colors = {"EV": "#00c853", "Hybrid": "#2979ff", "ICE": "#424242"}

# ---------------- SETTINGS ----------------
fps = 30
steps_between_years = 30
final_hold = 6
intro_duration = 2
frames_paths = []

fig, ax = plt.subplots(figsize=(9, 16))
# Увеличил отступ сверху, чтобы заголовок и год не теснились
plt.subplots_adjust(top=0.85) 

def ease(t):
    return t * t * (3 - 2 * t)

# ---------------- INTRO ----------------
print("Generating Intro...")
for i in range(int(intro_duration * fps)):
    ax.clear()
    ax.set_facecolor("white")
    alpha = i / (intro_duration * fps)
    ax.text(0.5, 0.55, "THE AUTOMOTIVE SHIFT", transform=ax.transAxes, 
            ha='center', fontsize=42, color=(0,0,0,alpha), weight='bold')
    ax.text(0.5, 0.45, "2015 — 2026", transform=ax.transAxes, 
            ha='center', fontsize=32, color=(0,0,0,alpha*0.7))
    ax.axis('off')
    filename = os.path.join(temp_dir, f"intro_{i:03d}.png")
    plt.savefig(filename, dpi=120)
    frames_paths.append(filename)

# ---------------- MAIN ----------------
print("Generating Main Animation...")
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

        bars = ax.bar(categories, interpolated, color=[colors[c] for c in categories], width=0.6)
        ax.set_ylim(0, 85)

        # --- TITLE ---
        ax.set_title("Global Car Sales\nby Powertrain", fontsize=38, weight='bold', pad=30)

        # --- YEAR (ТЕПЕРЬ ОДНИМ ЧИСЛОМ) ---
        # Выводим текущий год i. Когда прогресс t > 0.5, можно переключать на i+1, 
        # чтобы цифра менялась в середине анимации бара.
        display_year = years[i] if t < 0.5 else years[i+1]
        
        ax.text(
            0.5, 0.78, # Немного опустил, чтобы не залезало на Title
            f"{display_year}",
            transform=ax.transAxes,
            ha='center',
            fontsize=80, # Увеличил шрифт, раз теперь места больше
            color='red',
            weight='bold'
        )

        ax.set_ylabel("Millions of Vehicles", fontsize=26)
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, h + 1.5, f"{h:.1f}",
                    ha='center', fontsize=22, weight='bold')

        ax.spines[['top', 'right']].set_visible(False)
        ax.tick_params(axis='x', labelsize=26)
        ax.tick_params(axis='y', labelsize=18)

        filename = os.path.join(temp_dir, f"frame_{i:02d}_{step:02d}.png")
        plt.savefig(filename, dpi=120)
        frames_paths.append(filename)

# ---------------- FINAL ----------------
print("Generating Final Frame...")
ax.clear()
ax.set_facecolor("white")
final_values = [data[c][-1] for c in categories]
bars = ax.bar(categories, final_values, color=[colors[c] for c in categories], width=0.6)
ax.set_ylim(0, 85)
ax.set_title("Global Car Sales\nby Powertrain", fontsize=40, weight='bold', pad=30)

ax.text(0.5, 0.78, f"{years[-1]}", transform=ax.transAxes, ha='center',
        fontsize=90, color='red', weight='bold')

ax.set_ylabel("Millions of Vehicles", fontsize=26)
for bar in bars:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, h + 2, f"{h:.1f}",
            ha='center', fontsize=24, weight='bold')

ax.spines[['top', 'right']].set_visible(False)
final_path = os.path.join(temp_dir, "final.png")
plt.savefig(final_path, dpi=120)

# ---------------- EXPORT ----------------
print("Exporting Video...")
output = "car_sales_single_year.mp4"
with imageio.get_writer(output, fps=fps) as writer:
    for f_path in frames_paths:
        writer.append_data(imageio.imread(f_path))
    final_image = imageio.imread(final_path)
    for _ in range(int(final_hold * fps)):
        writer.append_data(final_image)

plt.close(fig)
print(f"DONE: {output}")