import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# --- ЗАГРУЗКА ДАННЫХ ---
# Читаем данные из внешнего CSV файла
# Столбцы: Year, Company, Engine_Name, Displacement, Horsepower
try:
    df = pd.read_csv('engines_data.csv')
except FileNotFoundError:
    print("Error: 'engines_data.csv' not found. Please ensure the data file exists.")
    exit()

# --- НАСТРОЙКА ГРАФИКА ---
fig, ax = plt.subplots(figsize=(12, 7))

# Список уникальных годов для анимации (начиная с 2000)
years = sorted(df[df['Year'] >= 2000]['Year'].unique())

def animate(year):
    """
    Функция для отрисовки одного кадра анимации (конкретного года).
    """
    ax.clear() # Очищаем оси для нового кадра
    
    # Фильтруем топ-10 двигателей за текущий год по лошадиным силам
    top_10 = df[df['Year'] == year].nlargest(10, 'Horsepower').sort_values(by='Horsepower', ascending=True)
    
    # Создаем горизонтальный столбчатый график
    # English labels and titles as requested
    bars = ax.barh(top_10['Engine_Name'], top_10['Horsepower'], color='royalblue')
    
    # Настройка осей и заголовков на английском языке
    ax.set_xlabel('Horsepower (hp)', fontsize=12)
    ax.set_title(f'Top 10 Most Powerful Engines: {year}', fontsize=18, fontweight='bold')
    ax.set_xlim(0, df['Horsepower'].max() * 1.1) # Единый масштаб для всех годов
    
    # Добавляем значения л.с. и название компании текстом на столбцы
    for i, (hp, engine) in enumerate(zip(top_10['Horsepower'], top_10['Engine_Name'])):
        ax.text(hp + 5, i, f'{hp} hp', va='center', fontsize=10, fontweight='bold')

# --- ЗАПУСК И СОХРАНЕНИЕ АНИМАЦИИ ---
# Создаем анимацию с интервалом 500мс между годами
ani = animation.FuncAnimation(fig, animate, frames=years, repeat=False, interval=500)

# Сохраняем результат в формате GIF
# Требуется установленный Pillow (pip install pillow)
ani.save('engine_race_chart.gif', writer='pillow')

print("Success: 'engine_race_chart.gif' has been created.")
# plt.show() # Раскомментируйте для предпросмотра