import matplotlib.pyplot as plt
import numpy as np

# Настройка стиля
plt.rcParams['figure.facecolor'] = 'white'

# 1. График скорости зарядки (Power vs State of Charge/Time)
# Моделируем кривую зарядки Tesla (Supercharger V3 vs V2 vs Home Wallbox)
soc = np.linspace(0, 100, 100)
# Упрощенные модели кривых мощности (в кВт)
v3 = np.piecewise(soc, [soc < 15, (soc >= 15) & (soc < 30), soc >= 30], 
                  [250, lambda x: 250 - (x-15)*8, lambda x: 130 * np.exp(-0.03*(x-30)) + 20])
v2 = np.piecewise(soc, [soc < 40, soc >= 40], 
                  [150, lambda x: 150 * np.exp(-0.04*(x-40)) + 15])
wallbox = np.full_like(soc, 11) # Стандартный Home Connector 11kW

fig1, ax1 = plt.subplots(figsize=(16, 9))
ax1.plot(soc, v3, label='Supercharger V3 (250kW)', linewidth=3, color='#CC0000')
ax1.plot(soc, v2, label='Supercharger V2 (150kW)', linewidth=3, color='#3d3d3d')
ax1.plot(soc, wallbox, label='Wall Connector (11kW)', linewidth=3, linestyle='--', color='blue')

ax1.set_title('Tesla Charging Speed Comparison', fontsize=20, fontweight='bold', pad=20)
ax1.set_xlabel('State of Charge (SOC) [%]', fontsize=14)
ax1.set_ylabel('Charging Power [kW]', fontsize=14)
ax1.grid(True, linestyle=':', alpha=0.6)
ax1.legend(fontsize=12)
ax1.set_xlim(0, 100)
ax1.set_ylim(0, 270)
plt.tight_layout()
plt.savefig('tesla_charging_speed.png', dpi=300)

# 2. График зависимости дальности пробега от температуры
# Моделируем падение эффективности батареи и затраты на обогрев
temp = np.linspace(-25, 40, 100)
# Базовая дальность 500 км (Model 3 Long Range)
# Эффективность падает при холоде и слегка при сильной жаре (кондиционер)
range_km = 500 * (0.5 + 0.5 * np.exp(-0.001 * (temp - 20)**2)) 
# Дополнительное падение при сильном морозе
range_km = np.where(temp < 0, range_km * (1 + 0.01*temp), range_km)

fig2, ax2 = plt.subplots(figsize=(16, 9))
ax2.plot(temp, range_km, linewidth=4, color='#008000')
ax2.fill_between(temp, range_km, color='#008000', alpha=0.1)

ax2.set_title('Estimated Range vs. Ambient Temperature', fontsize=20, fontweight='bold', pad=20)
ax2.set_xlabel('Outside Temperature [°C]', fontsize=14)
ax2.set_ylabel('Driving Range [km]', fontsize=14)
ax2.axvline(20, color='orange', linestyle='--', label='Optimal Temp (20°C)')
ax2.grid(True, linestyle=':', alpha=0.6)
ax2.legend(fontsize=12)
ax2.set_xlim(-25, 40)
ax2.set_ylim(0, 550)

plt.tight_layout()
plt.savefig('tesla_range_vs_temp.png', dpi=300)

plt.show()