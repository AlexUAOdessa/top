# pip install Pillow
import os
import random
from PIL import Image, ImageDraw, ImageFont

# --- НАСТРОЙКИ ---
INPUT_FILE = "input.txt"
OUTPUT_DIR = "images"
WIDTH, HEIGHT = 1920, 1080  # 16:9 Full HD
BG_COLOR = (245, 245, 245)

# Координаты колонок
NAME_X = 150       # Позиция для названия языка
BAR_X_START = 450  # Начало столбца (даем место под длинные названия)
BAR_MAX_WIDTH = 1000 
PERCENT_X = 1500   # Позиция для текста с процентами

BAR_HEIGHT = 60
BAR_SPACING = 30

language_colors = {}

def get_color(lang):
    if lang not in language_colors:
        # Генерируем приятные цвета (не слишком светлые)
        r, g, b = [random.randint(50, 180) for _ in range(3)]
        language_colors[lang] = (r, g, b)
    return language_colors[lang]

def generate_image(year, languages):
    """Создает одно изображение для конкретного года"""
    img = Image.new('RGB', (WIDTH, HEIGHT), color=BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    try:
        font_year = ImageFont.truetype("arial.ttf", 250)
        font_main = ImageFont.truetype("arial.ttf", 40)
    except:
        font_year = font_main = ImageFont.load_default()

    # РИСУЕМ ГОД ЗЕЛЕНЫМ ЦВЕТОМ (RGB: 34, 139, 34)
    # Мы используем координаты из вашего последнего запроса для правого нижнего угла
    year_text = str(year)
    draw.text((WIDTH - 800, HEIGHT - 280), year_text, fill=(34, 139, 34), font=font_year)

    for i, (name, rank, percent) in enumerate(languages[:12]): # Лимит 12 строк для красоты
        y = 120 + i * (BAR_HEIGHT + BAR_SPACING)
        
        try:
            val = float(percent.replace('%', '').strip())
        except:
            val = 0
            
        current_bar_width = int((val / 30) * BAR_MAX_WIDTH) # База расчета - 30%
        color = get_color(name)

        # 1. Название языка (выравнивание слева от столбца)
        draw.text((NAME_X, y + 8), name, fill=(50, 50, 50), font=font_main)

        # 2. Тень и столбец
        draw.rounded_rectangle(
            [BAR_X_START + 5, y + 5, BAR_X_START + current_bar_width + 5, y + BAR_HEIGHT + 5],
            radius=15, fill=(210, 210, 210)
        )
        draw.rounded_rectangle(
            [BAR_X_START, y, BAR_X_START + current_bar_width, y + BAR_HEIGHT],
            radius=15, fill=color
        )

        # 3. Процент (отдельной колонкой справа)
        draw.text((BAR_X_START + current_bar_width + 25, y + 8), percent, fill=(70, 70, 70), font=font_main)

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    img.save(os.path.join(OUTPUT_DIR, f"{year}_stats.png"))

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Файл {INPUT_FILE} не найден!")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    data_by_year = {}
    for line in lines:
        if '|' not in line: continue
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 4:
            year = parts[0]
            if year not in data_by_year: data_by_year[year] = []
            data_by_year[year].append((parts[1], parts[2], parts[3]))

    for year in sorted(data_by_year.keys()):
        generate_image(year, data_by_year[year])
        print(f"Готово: {year}")

if __name__ == "__main__":
    main()