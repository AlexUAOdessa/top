import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

# Настройки шрифтов
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']

# Месяцы
months = ['Sep 2025', 'Oct 2025', 'Nov 2025', 'Dec 2025', 'Jan 2026', 'Feb 2026', 'Mar 2026']

# Данные продаж (в тысячах)
bev_sales = [145,  75,  65,  86,  73,  68,  70]
hev_sales = [151, 159, 158, 186, 139, 145, 150]
ice_sales = [1100,1050,1000,1050, 950, 920, 900]

# Цвета
colors = {
    'BEV': '#1f77b4',
    'HEV': '#2ca02c',
    'ICE': '#d62728'
}

# Фигура 16:9
fig, ax = plt.subplots(figsize=(19.2, 10.8), facecolor='white')
ax.set_facecolor('white')

ax.set_ylim(0, 1300)
ax.set_ylabel('Monthly Sales (thousands)', fontsize=20, fontweight='bold')
ax.set_title('BEV vs HEV vs ICE\nSep 2025 – Mar 2026', 
             fontsize=28, fontweight='bold', pad=30)

# Убираем верхнюю и правую рамку + Figure 1
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.suptitle('')  # убираем автоматический заголовок Figure 1

ax.tick_params(axis='both', which='major', labelsize=16)

x = np.arange(len(months))
width = 0.25

bar_bev = ax.bar(x - width, [0]*len(months), width, label='BEV (Electric)', color=colors['BEV'])
bar_hev = ax.bar(x,        [0]*len(months), width, label='HEV (Hybrid)',   color=colors['HEV'])
bar_ice = ax.bar(x + width,[0]*len(months), width, label='ICE (Gasoline)', color=colors['ICE'])

ax.set_xticks(x)
ax.set_xticklabels(months, fontsize=16, rotation=15, ha='right')

# Легенда — короче и компактнее
ax.legend(fontsize=18, loc='upper right', frameon=False, bbox_to_anchor=(1.0, 0.98))

# Тексты над барами — уменьшенный шрифт
text_bev = [ax.text(i - width, 0, '', ha='center', va='bottom', fontsize=13, fontweight='bold') for i in x]
text_hev = [ax.text(i,        0, '', ha='center', va='bottom', fontsize=13, fontweight='bold') for i in x]
text_ice = [ax.text(i + width,0, '', ha='center', va='bottom', fontsize=13, fontweight='bold') for i in x]

def animate(frame):
    progress = frame / 100.0
    
    for i in range(len(months)):
        h_bev = bev_sales[i] * progress
        h_hev = hev_sales[i] * progress
        h_ice = ice_sales[i] * progress
        
        bar_bev[i].set_height(h_bev)
        bar_hev[i].set_height(h_hev)
        bar_ice[i].set_height(h_ice)
        
        if progress > 0.5:
            offset = 20
            text_bev[i].set_y(h_bev + offset)
            text_bev[i].set_text(f'{int(bev_sales[i])}k')
            
            text_hev[i].set_y(h_hev + offset)
            text_hev[i].set_text(f'{int(hev_sales[i])}k')
            
            text_ice[i].set_y(h_ice + offset)
            text_ice[i].set_text(f'{int(ice_sales[i])}k')
    
    return

ani = animation.FuncAnimation(
    fig, 
    animate, 
    frames=101,
    interval=40,
    blit=False,
    repeat=True
)

# Сохраняем видео
ani.save(
    'us_vehicle_sales_comparison_fixed.mp4',
    writer='ffmpeg',
    fps=30,
    dpi=100,
    bitrate=5000,
    metadata=dict(artist='Grok', title='US Sales: BEV vs HEV vs ICE')
)

plt.tight_layout(pad=2.0)  # увеличиваем внутренние отступы
plt.show()