import matplotlib.pyplot as plt
import numpy as np
import imageio.v2 as imageio # Принудительно используем v2, чтобы убрать DeprecationWarning
import io

# 1. Данные и настройка стиля (остаются прежними)
plt.style.use('dark_background')
years = ['2024', '2025']
# Прибыль в миллиардах USD (для корректного сравнения)
tesla_profit = [7.1, 3.8]
toyota_profit = [36.5, 34.5]

# Настройка фигуры 16:9
fig, ax = plt.subplots(figsize=(16, 9), dpi=100)
x = np.arange(len(years))
width = 0.35

# 2. Параметры анимации
fps = 30                        # Кадров в секунду
animation_duration = 3.0       # Продолжительность роста столбцов (сек)
freeze_duration = 2.0         # Продолжительность задержки в конце (сек)

total_anim_frames = int(fps * animation_duration)
total_freeze_frames = int(fps * freeze_duration)

# 3. Функция для отрисовки ОДНОГО кадра (остается прежней)
def render_frame(frame_index, total_frames):
    ax.clear()
    ax.set_ylim(0, 45)  # Фиксированная шкала Y
    
    # Рассчитываем текущее значение для анимации (от 0 до 100%)
    progress = frame_index / total_frames
    current_tesla = [val * progress for val in tesla_profit]
    current_toyota = [val * progress for val in toyota_profit]
    
    # Отрисовка столбцов
    rects1 = ax.bar(x - width/2, current_tesla, width, label='Tesla (Net Income)', color='#E81010')
    rects2 = ax.bar(x + width/2, current_toyota, width, label='Toyota (Net Income)', color='#9B9B9B')
    
    # Оформление (English labels)
    ax.set_ylabel('Annual Net Income (Billion USD)', fontsize=14, color='white')
    ax.set_title('Tesla vs Toyota: Financial Performance (2024-2025)', fontsize=22, pad=25, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(years, fontsize=16)
    ax.legend(fontsize=13, loc='upper left')
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    
    return rects1, rects2

# 4. Функция для сохранения кадра (ИСПРАВЛЕНО: v2.imread)
def get_image_from_plot():
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1)
    buf.seek(0)
    # Используем v2 напрямую, чтобы избежать DeprecationWarning
    return imageio.imread(buf)

# 5. Генерация видео (ИСПРАВЛЕНО: writer='ffmpeg')
print(f"Generating animation ({total_anim_frames} frames)...")
# ЯВНО УКАЗЫВАЕМ WRITER='FFMPEG', чтобы использовать imageio-ffmpeg и quality
with imageio.get_writer('tesla_toyota_comparison_fixed.mp4', fps=fps, writer='ffmpeg', codec='libx264', quality=8) as writer:
    for i in range(total_anim_frames):
        render_frame(i, total_anim_frames)
        image = get_image_from_plot()
        writer.append_data(image)

    print(f"Freezing final frame for {freeze_duration} seconds ({total_freeze_frames} frames)...")
    
    r1, r2 = render_frame(total_anim_frames, total_anim_frames)
    for rect1, rect2, t, toy in zip(r1, r2, tesla_profit, toyota_profit):
        ax.text(rect1.get_x() + rect1.get_width()/2, t + 1.0, f'${t}B', ha='center', color='white', fontweight='bold', fontsize=14)
        ax.text(rect2.get_x() + rect2.get_width()/2, toy + 1.0, f'${toy}B', ha='center', color='white', fontweight='bold', fontsize=14)
    
    final_image = get_image_from_plot()
    for _ in range(total_freeze_frames):
        writer.append_data(final_image)

plt.close(fig)
print("Video saved as 'tesla_toyota_comparison_fixed.mp4'")