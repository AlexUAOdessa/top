import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

# Настройка стиля
plt.style.use('dark_background')

# Данные (в миллиардах USD)
years = ['2024', '2025']
tesla_profit = [7.1, 3.8]
toyota_profit = [36.5, 34.5]

# Настройка фигуры 16:9
fig, ax = plt.subplots(figsize=(16, 9), dpi=100)
x = np.arange(len(years))
width = 0.35

def animate(i):
    ax.clear()
    ax.set_ylim(0, 45)  # Запас высоты для меток
    
    # Плавное "вырастание" столбцов
    current_tesla = [val * (i/100) for val in tesla_profit]
    current_toyota = [val * (i/100) for val in toyota_profit]
    
    rects1 = ax.bar(x - width/2, current_tesla, width, label='Tesla', color='#E81010')
    rects2 = ax.bar(x + width/2, current_toyota, width, label='Toyota', color='#9B9B9B')
    
    # Оформление (на английском)
    ax.set_ylabel('Net Income (Billion USD)', fontsize=14, color='white')
    ax.set_title('Tesla vs Toyota: Annual Net Income Comparison (2024-2025)', fontsize=20, pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(years, fontsize=14)
    ax.legend(fontsize=12)
    
    # Добавление числовых значений сверху
    if i == 100: # Показываем финальные цифры в конце анимации
        for r1, r2, t, toy in zip(rects1, rects2, tesla_profit, toyota_profit):
            ax.text(r1.get_x() + r1.get_width()/2, t + 0.5, f'${t}B', ha='center', color='white', fontweight='bold')
            ax.text(r2.get_x() + r2.get_width()/2, toy + 0.5, f'${toy}B', ha='center', color='white', fontweight='bold')
    
    plt.tight_layout()

# Создание анимации (100 кадров)
ani = animation.FuncAnimation(fig, animate, frames=101, interval=20)

# Сохранение (требуется установленный ffmpeg)
ani.save('tesla_vs_toyota.mp4', writer='ffmpeg', fps=30)

plt.show()