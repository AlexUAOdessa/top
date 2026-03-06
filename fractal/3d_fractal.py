import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D
import time
import gc

# --- НАСТРОЙКИ КАЧЕСТВА ---
WIDTH, HEIGHT = 3840, 2160
FPS, SECONDS = 30, 20  # 600 кадров всего
TOTAL_FRAMES = FPS * SECONDS

# Настройки леса
NUM_TREES = 30  # Количество деревьев
np.random.seed(42)
tree_pos = np.random.uniform(-40, 40, (NUM_TREES, 2))
tree_heights = np.random.uniform(7, 13, NUM_TREES)
tree_depths = np.random.randint(5, 7, NUM_TREES)

# Время начала для расчета прогресса
start_time = time.time()

def draw_forest_frame(f, ax):
    ax.clear()
    ax.set_facecolor('black')
    ax.axis('off')
    
    # Расчет прогресса в консоли
    if f > 0:
        elapsed = time.time() - start_time
        per_frame = elapsed / f
        remaining = per_frame * (TOTAL_FRAMES - f)
        print(f"Кадр {f}/{TOTAL_FRAMES} | Осталось примерно: {remaining/60:.1f} мин.", end='\r')

    # Ветер (плавное качание)
    wind = np.sin(f / 20) * 0.05
    
    def draw_leaf(x, y, z, size, angle):
        n_pts = 500  # Точек на один лист (баланс качества и скорости)
        pts = np.zeros((n_pts, 3))
        lx, ly = 0.0, 0.0
        for i in range(1, n_pts):
            r = np.random.rand()
            if r < 0.01: lx, ly = 0.0, 0.16 * ly
            elif r < 0.86: lx, ly = 0.85 * lx + 0.04 * ly, -0.04 * lx + 0.85 * ly + 1.6
            elif r < 0.93: lx, ly = 0.2 * lx - 0.26 * ly, 0.23 * lx + 0.22 * ly + 1.6
            else: lx, ly = -0.15 * lx + 0.28 * ly, 0.26 * lx + 0.24 * ly + 0.44
            
            s_ang, c_ang = np.sin(angle), np.cos(angle)
            pts[i] = [x + (lx*c_ang - ly*s_ang)*size, 
                      y + (lx*s_ang + ly*c_ang)*size, 
                      z + ly*size*0.4]
        
        ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], color='#2ecc71', lw=0.3, alpha=0.3)

    def build_branch(x, y, z, s, a, d, t_idx):
        if d == 0:
            draw_leaf(x, y, z, s * 0.5, a)
            return
        
        # Наклон от ветра зависит от высоты ветки (d)
        w_effect = wind * (7 - d) 
        x1 = x + s * np.cos(a + w_effect)
        y1 = y + s * np.sin(a + w_effect)
        z1 = z + s * 0.8
        
        ax.plot([x, x1], [y, y1], [z, z1], color='#4b3621', lw=d*1.1, alpha=0.7)
        
        new_s = s * 0.73
        # Угол ветвления немного "дышит"
        branch_split = np.deg2rad(25 + np.sin(f/30 + t_idx)*3)
        build_branch(x1, y1, z1, new_s, a + branch_split, d - 1, t_idx)
        build_branch(x1, y1, z1, new_s, a - branch_split, d - 1, t_idx)

    # Рисуем все деревья
    for i in range(NUM_TREES):
        build_branch(tree_pos[i,0], tree_pos[i,1], 0, tree_heights[i], np.pi/2, tree_depths[i], i)

    # Фиксируем камеру и лимиты
    ax.set_xlim(-60, 60)
    ax.set_ylim(-60, 60)
    ax.set_zlim(0, 50)
    # Облет камеры по кругу с изменением высоты
    ax.view_init(elev=20 + np.cos(f/60)*10, azim=f*0.6)

# --- Исполнение ---
fig = plt.figure(figsize=(WIDTH/100, HEIGHT/100), dpi=100, facecolor='black')
ax = fig.add_axes([0, 0, 1, 1], projection='3d')

# Исправленная строка FuncAnimation (передаем ax через lambda)
ani = animation.FuncAnimation(fig, lambda f: draw_forest_frame(f, ax), frames=TOTAL_FRAMES)

print(f">>> Запуск рендеринга 4K: {WIDTH}x{HEIGHT}")
writer = animation.FFMpegWriter(fps=FPS, bitrate=40000)
ani.save("Fractal_Forest_4K_Final.mp4", writer=writer)

plt.close()
print(f"\n>>> Готово! Файл сохранен. Общее время: {(time.time()-start_time)/60:.1f} мин.")