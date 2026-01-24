import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import sys
import os

# --- 1. ПОДГОТОВКА ДАННЫХ ---
# Метки для оси X (категории)
years = ['2014-2021', '2022', '2023', '2024', '2025']
# Значения для оси Y (высота столбцов)
values = [7000, 65000, 115000, 150000, 190000] 
# Цвета: HEX-коды от серого к насыщенному красному
colors = ['#7f8c8d', '#e74c3c', '#c0392b', '#a93226', '#922b21']

# --- 2. НАСТРОЙКА ВИЗУАЛА (ФИГУРЫ) ---
# figsize=(9, 16) — создаем "вертикальный" холст (соотношение сторон 9:16)
# facecolor — цвет внешнего фона (вокруг графика)
fig, ax = plt.subplots(figsize=(9, 16), facecolor='#111111') 
# set_facecolor — цвет фона внутри области рисования
ax.set_facecolor('#111111')

# --- 3. ФУНКЦИЯ ОБНОВЛЕНИЯ (ВЫЗЫВАЕТСЯ ДЛЯ КАЖДОГО КАДРА) ---
def update(frame):
    # Выводим в консоль текущий кадр, чтобы видеть, что рендеринг идет
    if frame % 10 == 0:
        print(f"Рендеринг кадра: {frame}/150...", end='\r')

    # Очищаем оси, чтобы кадры не накладывались друг на друга
    ax.clear()
    
    # Расчет "времени" анимации от 0.0 до 1.0 за 100 кадров
    t = frame / 100.0
    if t > 1: t = 1
    
    # Эффект Ease-Out (плавное замедление):
    # Используем синус, чтобы в конце движения столбцы замедлялись органично
    progress = np.sin(t * (np.pi / 2)) 
    
    # Расчет прозрачности заголовка (Fade-in):
    # К 40-му кадру значение станет 1.0 (полная видимость)
    title_alpha = min(1.0, frame / 40.0)
    
    # Текущие значения столбцов: целевое значение * прогресс анимации
    current_values = [v * progress for v in values]
    
    # Рисуем столбчатую диаграмму (bar chart)
    bars = ax.bar(years, current_values, color=colors, width=0.6)
    
    # Фиксируем масштаб оси Y, чтобы график не "прыгал" во время роста
    ax.set_ylim(0, max(values) * 1.15)
    
    # Убираем лишние элементы рамки (сверху и справа)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    # Красим оставшиеся оси в белый цвет
    ax.spines['left'].set_color('white')
    ax.spines['bottom'].set_color('white')
    
    # Настраиваем цвет и размер подписей на осях
    ax.tick_params(axis='x', colors='white', labelsize=14)
    ax.tick_params(axis='y', colors='white', labelsize=12)
    
    # Рисуем заголовок. alpha=title_alpha отвечает за эффект проявления
    ax.set_title("RUSSIAN WAR CRIMES IN UKRAINE\n(Year-by-Year Estimates)", 
                 fontsize=30, color='#FF0000', fontweight='black', pad=30, alpha=title_alpha)

    # Добавляем текстовые значения над каждым столбцом
    for bar in bars:
        height = bar.get_height()
        # Показываем текст только если столбец заметен (выше 500 единиц)
        if height > 500:
            # Форматируем число (добавляем пробел как разделитель тысяч)
            label = f"{int(height):,}".replace(',', ' ')
            # ha='center' — центрируем текст по горизонтали относительно столбца
            ax.text(bar.get_x() + bar.get_width()/2., height + 2000,
                    label, ha='center', va='bottom', 
                    color='white', fontsize=16, fontweight='bold', alpha=progress)

# --- 4. НАСТРОЙКА СОХРАНЕНИЯ (RENDER) ---

# Создаем объект анимации. frames=150 (движение + пауза в конце)
ani = animation.FuncAnimation(fig, update, frames=150, interval=30)

if __name__ == "__main__":
    output_filename = 'war_crimes_final.mp4'
    
    # ВАЖНО: Если выдает ошибку "MovieWriter ffmpeg unavailable":
    # 1. Скачай ffmpeg.exe
    # 2. Раскомментируй строку ниже и впиши путь к нему:
    # plt.rcParams['animation.ffmpeg_path'] = r'C:\ffmpeg\bin\ffmpeg.exe'
    
    print("Запуск процесса записи MP4...")
    
    try:
        # FFMpegWriter — специальный "движок" для сборки MP4
        # fps=30 — стандартная частота кадров для плавного видео
        # bitrate=2000 — качество видео (чем выше, тем тяжелее файл)
        writer = animation.FFMpegWriter(fps=30, metadata=dict(artist='AI Assistant'), bitrate=2000)
        
        # Сохраняем результат
        ani.save(output_filename, writer=writer)
        
        print(f"\nГотово! Видео создано: {os.path.abspath(output_filename)}")
        # Закрываем график, чтобы очистить оперативную память
        plt.close(fig) 
        
    except Exception as e:
        print(f"\nКРИТИЧЕСКАЯ ОШИБКА: {e}")
        print("-" * 30)
        print("СОВЕТ: Если ошибка говорит про 'ffmpeg', попробуй:")
        print("1. Установить его (pip install ffmpeg-python не поможет, нужна сама программа).")
        print("2. Либо заменить расширение на '.gif' и writer на 'pillow'.")