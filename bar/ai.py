import pandas as pd
import bar_chart_race as bcr
import matplotlib.pyplot as plt
import os
import warnings

# Игнорируем предупреждения matplotlib (чтобы консоль была чистой)
warnings.filterwarnings("ignore")

# --- 1. DATA ---
data = {
    'Year': list(range(2010, 2027)),
    'AI': [
        1, 2, 5, 10, 50, 200, 1000, 5000, 20000,
        100000, 500000, 1000000, 5000000,
        10000000, 50000000, 100000000, 500000000
    ],
    'Human': [
        100, 101, 102, 103, 104, 105, 106, 107, 108,
        109, 110, 111, 112, 113, 114, 115, 116
    ]
}
df = pd.DataFrame(data).set_index('Year')

# Нормализация для наглядности разрыва
df = df / df.max()

# --- 2. DARK MODE & СТИЛИЗАЦИЯ (КИБЕРПАНК) ---
plt.rcParams['axes.facecolor'] = '#050505'     # Глубокий черный фон графика
plt.rcParams['figure.facecolor'] = '#050505'   # Фон всего окна
plt.rcParams['text.color'] = 'white'           # Белый текст
plt.rcParams['xtick.color'] = '#050505'        # Прячем нижние цифры (чтобы не мусорить экран)
plt.rcParams['ytick.color'] = 'white'          # Белые названия (AI / Human)
plt.rcParams['axes.grid'] = False              # Убираем скучную сетку
plt.rcParams['axes.spines.top'] = False        # Убираем рамки
plt.rcParams['axes.spines.right'] = False
plt.rcParams['axes.spines.bottom'] = False
plt.rcParams['axes.spines.left'] = False

base_video = "ai_vs_human_base.mp4"

# --- 3. ГЕНЕРАЦИЯ БАЗОВОГО ВИДЕО ---
print("⏳ Генерируем плавный график...")
bcr.bar_chart_race(
    df=df,
    filename=base_video,
    orientation='h',
    sort='desc',
    n_bars=2,
    steps_per_period=40,    # 40 сделает анимацию супер-плавной
    period_length=600,      # Чуть длиннее период для драматизма
    figsize=(6, 10),        # Пропорции, близкие к экрану телефона
    cmap=['#ff003c', '#00e5ff'], # ИСПРАВЛЕННЫЙ ПАРАМЕТР: список цветов (красный для AI, голубой для Human)
    title='',
    bar_label_size=16,
    tick_label_size=18,
    # Красивый счетчик годов в правом нижнем углу
    period_label={'x': .95, 'y': .10, 'ha': 'right', 'va': 'center', 'size': 45, 'color': '#ffffff', 'weight': 'bold'}
)
print("✅ Базовое видео готово")

# --- 4. FFmpeg: КИНЕМАТОГРАФИЧНЫЙ SHORTS ---
final_video = "ai_vs_human_SHORTS.mp4"

# Что делает этот фильтр:
# 1. scale+pad: вписывает график в рамки 1080x1920 (формат Shorts/Reels) на черном фоне без искажений.
# 2. vignette: затемняет края экрана для концентрации внимания по центру.
# 3. drawtext: добавляет драматичные надписи по таймингам с тенями (shadowx/shadowy).
ffmpeg_cmd = f"""
ffmpeg -y -i {base_video} -vf "
scale=1080:1920:force_original_aspect_ratio=decrease,
pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0x050505,
vignette=PI/3.5,
drawtext=text='THE END OF AN ERA':fontcolor=white:fontsize=70:x=(w-text_w)/2:y=h*0.15:shadowcolor=black:shadowx=5:shadowy=5:enable='between(t,0,3)',
drawtext=text='AI IS WAKING UP':fontcolor=0xff003c:fontsize=85:x=(w-text_w)/2:y=h*0.25:shadowcolor=black:shadowx=5:shadowy=5:enable='between(t,3.5,6)',
drawtext=text='HUMANITY SURPASSED':fontcolor=white:fontsize=75:x=(w-text_w)/2:y=h*0.15:shadowcolor=black:shadowx=5:shadowy=5:enable='between(t,6.5,9)',
drawtext=text='WELCOME TO THE FUTURE':fontcolor=0xff003c:fontsize=85:x=(w-text_w)/2:y=h*0.85:shadowcolor=black:shadowx=5:shadowy=5:enable='between(t,8,12)'
" -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p {final_video}
"""

print("🎥 Накладываем эффекты и текст...")
os.system(ffmpeg_cmd.replace('\n', ' '))
print(f"🔥 Идеальный Shorts готов: {final_video}")