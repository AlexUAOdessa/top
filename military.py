# pip install matplotlib numpy
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

# --- НАСТРОЙКИ ДАННЫХ ---
# Данные (накопительный итог по годам, примерные официальные данные)
years = ['2014-2021', '2022', '2023', '2024', '2025']
values = [7000, 65000, 115000, 150000, 190000] 

# Цвета столбцов: первый серый, остальные красные (акцент на вторжении)
colors = ['#7f8c8d', '#e74c3c', '#c0392b', '#a93226', '#922b21']

# --- НАСТРОЙКИ ВИДЕО (9:16 для Shorts) ---
fig, ax = plt.subplots(figsize=(9, 16), facecolor='#111111') # Темный фон
ax.set_facecolor('#111111')

def update(frame):
    ax.clear() # Очищаем кадр
    
    # Вычисляем текущую высоту столбцов для анимации
    # Анимация идет 100 кадров.
    progress = frame / 100.0 
    if progress > 1: progress = 1
    
    current_values = [v * progress for v in values]
    
    # Рисуем бар-чарт
    bars = ax.bar(years, current_values, color=colors, width=0.6)
    
    # Настройки осей
    ax.set_ylim(0, max(values) * 1.15) # Запас сверху для цифр
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('white')
    ax.spines['bottom'].set_color('white')
    ax.tick_params(axis='x', colors='white', labelsize=14)
    ax.tick_params(axis='y', colors='white', labelsize=12)
    
    # Заголовок
    ax.set_title("RUSSIAN WAR CRIMES IN UKRAINE\n(Year-by-Year Estimates)", 
             fontsize=30,       # Увеличили размер (было 24)
             color='#FF0000',   # Ярко-красный цвет
             fontweight='black', # 'black' еще жирнее, чем 'bold'
             pad=25)            # Немного увеличили отступ, чтобы не прилипало

    # Добавляем цифры над столбцами
    for bar, val, target in zip(bars, current_values, values):
        height = bar.get_height()
        # Показываем цифру только если столбец уже начал расти
        if height > 0:
            label = f"{int(height):,}".replace(',', ' ')
            ax.text(bar.get_x() + bar.get_width()/2., height + 2000,
                    label,
                    ha='center', va='bottom', color='white', fontsize=16, fontweight='bold')

# Создаем анимацию
# frames=120 (100 кадров роста + 20 кадров паузы в конце)
# interval=30 (скорость)
ani = animation.FuncAnimation(fig, update, frames=130, interval=30, repeat=False)

# Сохранение (Требует FFMPEG)
print("Генерация видео... Подождите.")
try:
    ani.save('war_crimes_stats.mp4', writer='ffmpeg', fps=30, dpi=100)
    print("Готово! Файл 'war_crimes_stats.mp4' сохранен.")
except Exception as e:
    print(f"Ошибка сохранения видео: {e}")
    print("Убедитесь, что установлен ffmpeg. Или попробуйте сохранить как .gif (writer='pillow')")