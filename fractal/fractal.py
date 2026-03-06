import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import LinearSegmentedColormap
from numba import jit, prange
import gc
import os

# --- ГЛОБАЛЬНЫЕ НАСТРОЙКИ 4K ---
WIDTH, HEIGHT = 3840, 2160
FPS, SECONDS = 30, 30
TOTAL_FRAMES = FPS * SECONDS
MAX_ITER = 120

# --- СЛОЖНЫЕ ЦИКЛИЧЕСКИЕ ПАЛИТРЫ (2048 ОТТЕНКОВ) ---
# Радужный вихрь (для Мандельброта/Жюлиа)
neon_colors = [(0, "#000000"), (0.1, "#1a0033"), (0.2, "#00ffff"), 
               (0.4, "#ffffff"), (0.6, "#ff00ff"), (0.8, "#ffee00"), (1, "#000000")]
neon_cmap = LinearSegmentedColormap.from_list("neon_wave", neon_colors, N=2048)

# Кибер-огонь (для Огненного корабля/Плазмы)
fire_colors = [(0, "#000000"), (0.1, "#330000"), (0.3, "#ff4400"), 
               (0.5, "#ffee00"), (0.7, "#ffffff"), (0.9, "#ff00ff"), (1, "#000000")]
fire_cmap = LinearSegmentedColormap.from_list("solar_flare", fire_colors, N=2048)

# Глубокий космос (для Ляпунова/Феникса)
bio_colors = [(0, "#000000"), (0.2, "#001144"), (0.4, "#00ffcc"), 
              (0.6, "#ffffff"), (0.8, "#ff00ff"), (1, "#000000")]
bio_cmap = LinearSegmentedColormap.from_list("deep_sea", bio_colors, N=2048)

# --- РАСТРОВЫЕ ЯДРА (1-10) - С ГЛУБОКИМ СГЛАЖИВАНИЕМ И ДИНАМИКОЙ ---

@jit(nopython=True, parallel=True)
def render_fire_plasma(w, h, frame):
    plasma = np.empty((h, w), dtype=np.float64)
    t = frame * 0.08
    for i in prange(h):
        for j in range(w):
            x, y = j/w*4, i/h*4
            v = np.sin(x+t) + np.sin((y+t)/2) + np.sin((x+y+t)/2)
            cx, cy = x + 0.5*np.sin(t/3), y + 0.5*np.cos(t/5)
            v += np.sin(np.sqrt(cx*cx+cy*cy+1)+t)
            # Циклическое изменение цвета
            plasma[i, j] = (v + 4) / 8 * 100
    return plasma

@jit(nopython=True, parallel=True)
def render_mandelbrot_dynamic(w, h, frame):
    fractal = np.zeros((h, w), dtype=np.float64)
    # Экспоненциальный зум и вращение
    zoom = 1.5 * (0.94 ** (frame**0.6))
    angle = frame * 0.015
    cx, cy = -0.743643887037151, 0.13182590420643
    s_a, c_a = np.sin(angle), np.cos(angle)
    sx, sy = zoom, zoom * (h/w)
    for i in prange(h):
        for j in range(w):
            nx, ny = -sx + (2*sx*j/w), -sy + (2*sy*i/h)
            x0, y0 = cx + nx*c_a - ny*s_a, cy + nx*s_a + ny*c_a
            x, y, it = 0.0, 0.0, 0
            while x*x + y*y <= 256 and it < MAX_ITER:
                x, y, it = x*x - y*y + x0, 2*x*y + y0, it + 1
            if it < MAX_ITER:
                lz = np.log(x*x + y*y)/2
                fractal[i, j] = it + 1 - np.log(lz/np.log(2))/np.log(2)
    return fractal

@jit(nopython=True, parallel=True)
def render_burning_ship_turbo(w, h, frame):
    fractal = np.zeros((h, w), dtype=np.float64)
    # Быстрый зум
    zoom = 1.2 * (0.96 ** (frame**0.5))
    cx, cy = -1.75, -0.03
    for i in prange(h):
        for j in range(w):
            x0, y0 = cx - zoom + (2*zoom*j/w), cy - zoom*(h/w) + (2*zoom*(h/w)*i/h)
            x, y, it = 0.0, 0.0, 0
            while x*x + y*y <= 10 and it < MAX_ITER:
                x, y = x*x - y*y + x0, abs(2*x*y) + y0
                it += 1
            fractal[i, j] = it
    return fractal

@jit(nopython=True, parallel=True)
def render_phoenix_morph(w, h, frame):
    fractal = np.zeros((h, w), dtype=np.float64)
    # Дышащий зум и изменение формы
    zoom = 1.2 + np.sin(frame/100)*0.2
    c, p = -0.4 + 0.02*np.sin(frame/40), 0.3
    for i in prange(h):
        for j in range(w):
            x, y = -zoom + (2*zoom*j/w), -zoom*(h/w) + (2*zoom*(h/w)*i/h)
            z, zp, it = complex(y, x), 0j, 0
            while abs(z) < 4 and it < MAX_ITER:
                zn = z*z + c + p*zp
                zp, z, it = z, zn, it + 1
            fractal[i, j] = it
    return fractal

@jit(nopython=True, parallel=True)
def render_newton_crystal(w, h, frame):
    fractal = np.zeros((h, w), dtype=np.float64)
    # Ускоряющийся зум и вращение
    zoom = 1.5 / (1.1 ** (frame / 12))
    angle = frame * 0.02
    s_a, c_a = np.sin(angle), np.cos(angle)
    for i in prange(h):
        for j in range(w):
            nx, ny = -zoom + (2*zoom*j/w), -zoom*(h/w) + (2*zoom*(h/w)*i/h)
            z = complex(nx*c_a - ny*s_a, nx*s_a + ny*c_a)
            it = 0
            for _ in range(40):
                if abs(z) < 1e-6: break
                zn = z - (z**3 - 1)/(3*z**2)
                if abs(zn - z) < 1e-4: break
                z, it = zn, it + 1
            # Плавный цвет на основе корня
            fractal[i, j] = it * 2 + abs(z)
    return fractal

@jit(nopython=True, parallel=True)
def render_biomorph_alien(w, h, frame):
    fractal = np.zeros((h, w), dtype=np.float64)
    # Пульсация биоморфной формы
    c = complex(0.5 + 0.1*np.sin(frame/50), 0.5)
    zoom = 1.5 + 0.1*np.sin(frame/40)
    for i in prange(h):
        for j in range(w):
            z = complex(-zoom + (2*zoom*j/w), -zoom*(h/w) + (2*zoom*(h/w)*i/h))
            it = 0
            while abs(z) < 100 and it < 40:
                z = z**5 + c
                if abs(z.real) < 10 or abs(z.imag) < 10:
                    fractal[i, j] = it * 2.5
                    break
                it += 1
    return fractal

@jit(nopython=True, parallel=True)
def render_lyapunov_space(w, h, frame):
    fractal = np.zeros((h, w), dtype=np.float64)
    # Изменение последовательности AB
    seq_val = 2 + np.sin(frame/50)
    for i in prange(h):
        for j in range(w):
            a, b = 3.5 + j/w*0.5, 3.5 + i/h*0.5
            x, lyap = 0.5, 0.0
            for it in range(100):
                r = a if it % 2 == 0 else b
                x = r * x * (1 - x)
                lyap += np.log(abs(r * (1 - 2 * x)))
            fractal[i, j] = 50 + (lyap / 100) * 50
    return fractal

@jit(nopython=True, parallel=True)
def render_clifford_smoke(w, h, frame):
    res = np.zeros((h, w), dtype=np.float64)
    # Медленный дрейф параметров
    a = -1.4 + 0.1*np.sin(frame/50)
    b, c, d = 1.6, 1.0 + 0.2*np.sin(frame/60), 0.7
    x, y = 0.0, 0.0
    for _ in range(500000): # Глубокая итерация для плотности
        xn, yn = np.sin(a*y) + c*np.cos(a*x), np.sin(b*x) + d*np.cos(b*y)
        x, y = xn, yn
        px, py = int((x+2.5)*w/5), int((y+2.5)*h/5)
        if 0<=px<w and 0<=py<h: res[py, px] += 1
    return np.log1p(res) * 20

@jit(nopython=True, parallel=True)
def render_dejong_plasma(w, h, frame):
    res = np.zeros((h, w), dtype=np.float64)
    # Быстрое изменение формы
    a, b, c, d = 1.4 + 0.1*np.sin(frame/40), -2.3, 2.4, -1.2
    x, y = 0.0, 0.0
    for _ in range(500000):
        xn, yn = np.sin(a*y) - np.cos(b*x), np.sin(c*x) - np.cos(d*y)
        x, y = xn, yn
        px, py = int((x+3)*w/6), int((y+3)*h/6)
        if 0<=px<w and 0<=py<h: res[py, px] += 1
    return np.log1p(res) * 20

@jit(nopython=True, parallel=True)
def render_julia_morph(w, h, frame):
    res = np.zeros((h, w), dtype=np.float64)
    # Трансформация C и дышащий зум
    ca = -0.7 + 0.3*np.cos(frame/60)
    cb = 0.27 + 0.15*np.sin(frame/40)
    zoom = 1.2 + 0.4*np.sin(frame/100)
    for i in prange(h):
        for j in range(w):
            zx, zy, it = -zoom + (2*zoom*j/w), -zoom*(h/w) + (2*zoom*(h/w)*i/h), 0
            while zx*zx + zy*zy <= 256 and it < MAX_ITER:
                zx, zy, it = zx*zx - zy*zy + ca, 2*zx*zy + cb, it + 1
            if it < MAX_ITER:
                lz = np.log(zx*zx + zy*zy)/2
                res[i, j] = it + 1 - np.log(lz/np.log(2))/np.log(2)
    return res

# --- ВЕКТОРНЫЕ И ХАОС-ИГРЫ (11-20) - С ГРАДИЕНТАМИ СВЕЧЕНИЯ ---

def draw_lorenz_glow(ax, f):
    dt, s, r, b = 0.01, 10, 28, 8/3
    x, y, z = 0.1, 0.0, 0.0
    pts = []
    num_points = 2000 + f * 12
    for _ in range(num_points):
        dx, dy, dz = s*(y-x)*dt, (x*(r-z)-y)*dt, (x*y-b*z)*dt
        x+=dx; y+=dy; z+=dz
        pts.append((x,y,z,np.sqrt(dx**2+dy**2+dz**2))) # Сохраняем скорость
    pts = np.array(pts)
    # Отрисовка сегментами для эффекта "свечения"
    for i in range(0, len(pts)-60, 60):
        seg = pts[i:i+61]
        ax.plot(seg[:,0], seg[:,1], seg[:,2], color=fire_cmap(i/len(pts)), lw=max(0.5, 5-seg[-1,3]*0.5), alpha=0.8)
    ax.view_init(25, f*0.6)

def draw_dragon_morph(ax, f):
    it, am = min(13, int(f/65)+6), np.deg2rad(90 + np.sin(f/45)*12)
    pts = np.array([[0,0], [1,0]], dtype=np.float64)
    for _ in range(it):
        c = pts[-1]
        rot = np.array([[np.cos(am), -np.sin(am)], [np.sin(am), np.cos(am)]])
        # Рекурсивное "развертывание"
        pts = np.vstack((pts, (np.dot(pts[:-1]-c, rot) + c)[::-1]))
    pts -= np.mean(pts, axis=0)
    pts *= 1.3 / (np.max(np.abs(pts)) + 0.1)
    # Динамический цвет по времени построения
    ax.plot(pts[:,0], pts[:,1], color=neon_cmap(0.5+0.3*np.sin(f/40)), lw=1.5)

def draw_pythagoras_wind_tree(ax, f):
    # Угол "колыхания" под ветром
    ang = np.deg2rad(30 + np.sin(f/25)*12)
    def pb(x, y, s, a, d):
        if d==0: return
        x1, y1 = x+s*np.cos(a), y+s*np.sin(a)
        ax.plot([x,x1], [y,y1], color=neon_cmap(d/10), lw=d*0.8)
        pb(x1, y1, s*0.8, a+ang, d-1); pb(x1, y1, s*0.8, a-ang, d-1)
    pb(0, -1.5, 0.5, np.pi/2, 10)

def draw_barnsley_fern_growth(ax, f):
    n, pts = 10000 + f*500, [[0,0]]
    for _ in range(n):
        r, (x,y) = np.random.rand(), pts[-1]
        if r<0.01: pts.append([0, 0.16*y])
        elif r<0.86: pts.append([0.85*x+0.04*y, -0.04*x+0.85*y+1.6])
        elif r<0.93: pts.append([0.2*x-0.26*y, 0.23*x+0.22*y+1.6])
        else: pts.append([-0.15*x+0.28*y, 0.26*x+0.24*y+0.44])
    p = np.array(pts)
    ax.scatter(p[:,0], p[:,1], s=0.1, color='#00ff66', alpha=0.5)

def draw_levy_curve_morph(ax, f):
    def lv(p1, p2, d):
        if d==0: return [p1, p2]
        v = p2-p1
        p3 = p1 + 0.5*np.array([v[0]-v[1], v[0]+v[1]])
        return lv(p1,p3,d-1)[:-1] + lv(p3,p2,d-1)
    p = np.array(lv(np.array([-0.5,0]), np.array([0.5,0]), min(12, 5+int(f/80))))
    ax.plot(p[:,0], p[:,1], color=bio_cmap(0.5), lw=1)

def draw_henon_star_dust(ax, f):
    n, x, y, a, b = 15000+f*600, 0, 0, 1.4, 0.3
    pts = []
    for _ in range(n):
        x, y = 1 - a*x**2 + y, b*x
        pts.append([x, y])
    p = np.array(pts)
    ax.scatter(p[:,0], p[:,1], s=0.2, color=fire_cmap(0.7), alpha=0.4)

def draw_bifurcation_flow(ax, f):
    # Зум в область хаоса
    r = np.linspace(2.8+f/TOTAL_FRAMES, 4.0, 8000)
    x = 0.5*np.ones_like(r)
    for _ in range(400): x = r*x*(1-x)
    for _ in range(150):
        x = r*x*(1-x)
        ax.plot(r, x, ',w', alpha=0.15, color=neon_cmap(f/TOTAL_FRAMES))

def draw_sierpinski_gasket_dots(ax, f):
    pts = np.array([[0,0], [1,0], [0.5, 0.86]])
    cur = np.array([0.5, 0.5])
    res = []
    for _ in range(10000 + f*500):
        # Хаос-игра
        cur = (cur + pts[np.random.randint(3)])/2
        res.append(cur)
    p = np.array(res)
    ax.scatter(p[:,0], p[:,1], s=0.1, color=bio_cmap(0.6))

def draw_lissajous_neon_flow(ax, f):
    t = np.linspace(0, 2*np.pi, 10000)
    # Трансформация частот и фазы
    a, b = 5+np.sin(f/120)*2, 4
    delta = f*0.04
    ax.plot(np.sin(a*t + delta), np.sin(b*t), color=neon_cmap(0.6), lw=2)

def draw_vicsek_fractal_morph(ax, f):
    def vs(x, y, s, d):
        if d==0: 
            ax.add_patch(plt.Rectangle((x,y), s, s, color=neon_cmap(0.4)))
            return
        ns = s/3
        # Крестообразное деление
        for dx, dy in [(0,0), (2,0), (1,1), (0,2), (2,2)]:
            vs(x+dx*ns, y+dy*ns, ns, d-1)
    vs(-0.5, -0.5, 1.0, min(4, 2+int(f/200)))

# --- ГРАНДИОЗНЫЙ СПИСОК ЗАДАЧ (20 ШЕДЕВРОВ) ---
tasks = [
    {"n": "01_Liquid_Fire_Plasma", "t": "r", "f": render_fire_plasma, "c": fire_cmap},
    {"n": "02_Turbo_Mandelbrot", "t": "r", "f": render_mandelbrot_dynamic, "c": neon_cmap},
    {"n": "03_Burning_Ship_Z", "t": "r", "f": render_burning_ship_turbo, "c": fire_cmap},
    {"n": "04_Phoenix_Morph", "t": "r", "f": render_phoenix_morph, "c": bio_cmap},
    {"n": "05_Newton_Crystal", "t": "r", "f": render_newton_crystal, "c": fire_cmap},
    {"n": "06_Alien_Biomorph", "t": "r", "f": render_biomorph_alien, "c": neon_cmap},
    {"n": "07_Lyapunov_Space", "t": "r", "f": render_lyapunov_space, "c": fire_cmap},
    {"n": "08_Clifford_Smoke", "t": "r", "f": render_clifford_smoke, "c": neon_cmap},
    {"n": "09_DeJong_Plasma", "t": "r", "f": render_dejong_plasma, "c": fire_cmap},
    {"n": "10_Morph_Julia", "t": "r", "f": render_julia_morph, "c": neon_cmap},
    {"n": "11_Lorenz_Energy_Glow", "t": "3", "f": draw_lorenz_glow},
    {"n": "12_Dragon_Morph", "t": "v", "f": draw_dragon_morph},
    {"n": "13_Pythagoras_Wind_Tree", "t": "v", "f": draw_pythagoras_wind_tree},
    {"n": "14_Barnsley_Fern", "t": "v", "f": draw_barnsley_fern_growth},
    {"n": "15_Levy_Curve", "t": "v", "f": draw_levy_curve_morph},
    {"n": "16_Henon_Dust", "t": "v", "f": draw_henon_star_dust},
    {"n": "17_Bifurcation_Flow", "t": "v", "f": draw_bifurcation_flow},
    {"n": "18_Sierpinski_Gasket", "t": "v", "f": draw_sierpinski_gasket_dots},
    {"n": "19_Lissajous_Flow", "t": "v", "f": draw_lissajous_neon_flow},
    {"n": "20_Vicsek_Fractal", "t": "v", "f": draw_vicsek_fractal_morph}
]

# --- ИСПОЛНЕНИЕ (С ОЧИСТКОЙ ПАМЯТИ) ---
if __name__ == '__main__':
    writer = animation.FFMpegWriter(fps=FPS, bitrate=35000, extra_args=['-pix_fmt', 'yuv420p', '-preset', 'faster'])
    
    for t in tasks:
        print(f"\n>>> Начинаю рендеринг: {t['n']}...")
        # Устанавливаем черный фон сразу при создании фигуры
        fig = plt.figure(figsize=(38.4, 21.6), facecolor='black')
        
        if t['t'] == "r": # Растровые задачи
            ax = fig.add_axes([0, 0, 1, 1])
            ax.axis('off')
            img = ax.imshow(np.zeros((HEIGHT, WIDTH)), cmap=t['c'], vmin=0, vmax=100, origin='lower', aspect='auto')
            def update(f):
                img.set_data(t['f'](WIDTH, HEIGHT, f))
                if f % 10 == 0: print(f"Кадр {f}/{TOTAL_FRAMES}", end='\r')
                return [img]
        else: # Векторные и 3D задачи
            is3 = t['t']=="3"
            ax = fig.add_axes([0, 0, 1, 1], projection='3d' if is3 else None)
            def update(f):
                ax.clear(); ax.set_facecolor('black'); ax.axis('off')
                if not is3: ax.set_xlim(-1.2, 1.2); ax.set_ylim(-0.7, 0.7)
                t['f'](ax, f)
                if f % 10 == 0: print(f"Кадр {f}/{TOTAL_FRAMES}", end='\r')
                return []

        ani = animation.FuncAnimation(fig, update, frames=TOTAL_FRAMES)
        ani.save(f"{t['n']}_4K.mp4", writer=writer)
        # Явная очистка ресурсов после каждого видео
        plt.close(fig)
        gc.collect() # Принудительный запуск сборщика мусора

print("\n\nГОТОВО! Фрактальная Энциклопедия из 20 шедевров создана.")