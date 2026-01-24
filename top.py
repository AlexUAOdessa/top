# pip install Pillow
import os
import random
from PIL import Image, ImageDraw, ImageFont

# --- ГЛОБАЛЬНЫЕ НАСТРОЙКИ ВИЗУАЛИЗАЦИИ ---
INPUT_FILE = "input.txt"   # Исходный файл с данными (формат: Год | Язык | Ранг | Процент)
OUTPUT_DIR = "images"      # Папка, куда будут сохраняться готовые PNG
WIDTH, HEIGHT = 1920, 1080 # Разрешение кадра (стандартное Full HD 16:9)
BG_COLOR = (245, 245, 245) # Цвет фона в формате RGB (светло-серый)

# Координаты элементов на холсте (сетка)
NAME_X = 150        # Отступ слева для названий языков программирования
BAR_X_START = 450   # Точка начала отрисовки цветного столбца (горизонтально)
BAR_MAX_WIDTH = 1000 # Максимально возможная длина столбца при 100% (или базовом значении)
PERCENT_X = 1500    # Координата для текста с процентным значением

BAR_HEIGHT = 60     # Высота (толщина) одного столбца
BAR_SPACING = 30    # Вертикальное расстояние между соседними столбцами

# Словарь для хранения цветов. Один раз назначенный цвет закрепляется за языком навсегда.
language_colors = {}

def get_color(lang):
    """
    Назначает уникальный случайный цвет для каждого нового языка.
    Если язык уже встречался, возвращает ранее созданный цвет.
    """
    if lang not in language_colors:
        # Генерируем компоненты RGB в диапазоне 50-180 (избегаем слишком темных и слишком ярких)
        r, g, b = [random.randint(50, 180) for _ in range(3)]
        language_colors[lang] = (r, g, b)
    return language_colors[lang]

def generate_image(year, languages):
    """
    Основная логика отрисовки одного кадра (года).
    year: строка или число (например, "2024")
    languages: список кортежей [(название, ранг, процент), ...]
    """
    # Создаем новый пустой холст с заданным цветом фона
    img = Image.new('RGB', (WIDTH, HEIGHT), color=BG_COLOR)
    draw = ImageDraw.Draw(img) # Создаем объект для рисования на холсте
    
    # Попытка загрузки шрифтов. Если arial.ttf нет в системе, загрузится стандартный (мелкий) шрифт.
    try:
        font_year = ImageFont.truetype("arial.ttf", 250) # Шрифт для большого года на фоне
        font_main = ImageFont.truetype("arial.ttf", 40)  # Шрифт для названий и цифр
    except:
        font_year = font_main = ImageFont.load_default()

    # --- ОТРИСОВКА ФОНОВОГО ГОДА ---
    # Размещаем год в правой нижней части экрана зеленым цветом (Forest Green)
    year_text = str(year)
    draw.text((WIDTH - 800, HEIGHT - 280), year_text, fill=(34, 139, 34), font=font_year)

    # --- ОТРИСОВКА СТОЛБЦОВ (TOP 12) ---
    for i, (name, rank, percent) in enumerate(languages[:12]):
        # Вычисляем вертикальную позицию Y для текущей строки
        y = 120 + i * (BAR_HEIGHT + BAR_SPACING)
        
        # Преобразуем строку процента (напр. "15.5%") в число для расчета ширины
        try:
            val = float(percent.replace('%', '').strip())
        except:
            val = 0
            
        # Рассчитываем ширину столбца. В данном случае 30% — это полная ширина BAR_MAX_WIDTH.
        current_bar_width = int((val / 30) * BAR_MAX_WIDTH)
        color = get_color(name) # Получаем фиксированный цвет языка

        # 1. Отрисовка названия языка программирования
        # Смещаем на 8 пикселей вниз (+8), чтобы текст был визуально по центру высоты столбца
        draw.text((NAME_X, y + 8), name, fill=(50, 50, 50), font=font_main)

        # 2. Отрисовка "тени" столбца (с небольшим смещением +5 пикселей)
        # rounded_rectangle создает прямоугольник со скругленными углами
        draw.rounded_rectangle(
            [BAR_X_START + 5, y + 5, BAR_X_START + current_bar_width + 5, y + BAR_HEIGHT + 5],
            radius=15, fill=(210, 210, 210)
        )
        
        # 3. Отрисовка основного цветного столбца
        draw.rounded_rectangle(
            [BAR_X_START, y, BAR_X_START + current_bar_width, y + BAR_HEIGHT],
            radius=15, fill=color
        )

        # 4. Отрисовка текстового значения процента справа от столбца
        # BAR_X_START + current_bar_width + 25 — ставим текст сразу после окончания бара
        draw.text((BAR_X_START + current_bar_width + 25, y + 8), percent, fill=(70, 70, 70), font=font_main)

    # Создаем папку, если она еще не существует
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # Сохраняем готовый файл в формате PNG
    img.save(os.path.join(OUTPUT_DIR, f"{year}_stats.png"))

def main():
    """
    Точка входа в программу. Отвечает за чтение данных и запуск цикла генерации.
    """
    if not os.path.exists(INPUT_FILE):
        print(f"Файл {INPUT_FILE} не найден!")
        return

    # Читаем данные из текстового файла
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Группируем данные по годам (один год — много языков)
    data_by_year = {}
    for line in lines:
        if '|' not in line: continue # Пропускаем пустые или некорректные строки
        
        # Разрезаем строку по символу "|" и убираем лишние пробелы
        parts = [p.strip() for p in line.split('|')]
        
        if len(parts) >= 4:
            year = parts[0]
            if year not in data_by_year: 
                data_by_year[year] = []
            # Добавляем данные (Имя, Ранг, Процент) в список этого года
            data_by_year[year].append((parts[1], parts[2], parts[3]))

    # Сортируем годы по порядку и запускаем генерацию для каждого
    for year in sorted(data_by_year.keys()):
        generate_image(year, data_by_year[year])
        print(f"Готово: {year}")

if __name__ == "__main__":
    main()