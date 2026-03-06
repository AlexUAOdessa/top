import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.colors import LinearSegmentedColormap
from numba import jit, prange
import gc
import os

# --- ГЛОБАЛЬНЫЕ НАСТРОЙКИ 4K 3D ---
WIDTH, HEIGHT = 3840, 2160
FPS, SECONDS = 30, 30
TOTAL_FRAMES = FPS * SECONDS
GRID_RES = 400  # Плотность сетки для 3D ландшафтов
MAX_ITER = 100

# --- ПАЛИТРЫ ---
neon_cmap = LinearSegmentedColormap.from_list("cyber", ["#000000", "#00ffff", "#ffffff", "#ff00ff", "#000000"], N=1024)
gold_cmap = LinearSegmentedColormap.from_list("gold", ["#000000", "#440000", "#ffaa00", "#ffffcc", "#ffffff"], N=1024)
ice_cmap = LinearSegmentedColormap.from_list("ice", ["#000510", "#002244", "#00ccff", "#ffffff", "#00ffcc"], N=1024)

# --- БЛОК 1: РАСТРОВЫЕ 3D ЯДРА (SURFACES) ---

@jit(nopython=True, parallel=True)
def calc_mandel(f):
    x, y = np.linspace(-2.1, 1.0, GRID_RES), np.linspace(-1.2, 1.2, GRID_RES)
    X, Y = np.meshgrid(x, y)
    Z = np.zeros((GRID_RES, GRID_RES))
    zoom = 1.0 + (f / 50)
    for i in prange(GRID_RES):
        for j in range(GRID_RES):
            cx, cy = X[i,j]/zoom - 0.5, Y[i,j]/zoom
            zx, zy, it = 0.0, 0.0, 0
            while zx*zx + zy*zy <= 4 and it < MAX_ITER:
                zx, zy = zx*zx - zy*zy + cx, 2*zx*zy + cy
                it += 1
            Z[i,j] = it
    return X, Y, Z

@jit(nopython=True, parallel=True)
def calc_ship(f):
    x, y = np.linspace(-1.8, -1.7, GRID_RES), np.linspace(-0.05, 0.05, GRID_RES)
    X, Y = np.meshgrid(x, y)
    Z = np.zeros((GRID_RES, GRID_RES))
    zoom = 1.0 + (f / 30)
    for i in prange(GRID_RES):
        for j in range(GRID_RES):
            x0, y0 = X[i,j]/zoom, Y[i,j]/zoom
            zx, zy, it = 0.0, 0.0, 0
            while zx*zx + zy*zy <= 4 and it < MAX_ITER:
                zx, zy = zx*zx - zy*zy + x0, abs(2*zx*zy) + y0
                it += 1
            Z[i,j] = it
    return X, Y, Z

@jit(nopython=True, parallel=True)
def calc_julia(f):
    x, y = np.linspace(-1.5, 1.5, GRID_RES), np.linspace(-1.5, 1.5, GRID_RES)
    X, Y = np.meshgrid(x, y)
    Z = np.zeros((GRID_RES, GRID_RES))
    ca, cb = -0.7 + 0.1*np.cos(f/60), 0.27 + 0.05*np.sin(f/40)
    for i in prange(GRID_RES):
        for j in range(GRID_RES):
            zx, zy, it = X[i,j], Y[i,j], 0
            while zx*zx + zy*zy <= 4 and it < MAX_ITER:
                zx, zy = zx*zx - zy*zy + ca, 2*zx*zy + cb
                it += 1
            Z[i,j] = it
    return X, Y, Z

@jit(nopython=True, parallel=True)
def calc_plasma(f):
    x, y = np.linspace(0, 5, GRID_RES), np.linspace(0, 5, GRID_RES)
    X, Y = np.meshgrid(x, y)
    t = f * 0.1
    Z = (np.sin(X+t) + np.sin((Y+t)/2) + np.cos(np.sqrt(X**2+Y**2)+t)) * 5 + 10
    return X, Y, Z

@jit(nopython=True, parallel=True)
def calc_newton(f):
    x, y = np.linspace(-1, 1, GRID_RES), np.linspace(-1, 1, GRID_RES)
    X, Y = np.meshgrid(x, y)
    Z = np.zeros((GRID_RES, GRID_RES))
    zoom = 1.0 + (f / 40)
    for i in prange(GRID_RES):
        for j in range(GRID_RES):
            z = complex(X[i,j]/zoom, Y[i,j]/zoom)
            it = 0
            for _ in range(30):
                if abs(z) < 1e-6: break
                zn = z - (z**3 - 1)/(3*z**2)
                if abs(zn - z) < 1e-4: break
                z, it = zn, it + 1
            Z[i,j] = it + abs(z)
    return X, Y, Z

@jit(nopython=True, parallel=True)
def calc_biomorph(f):
    x, y = np.linspace(-2, 2, GRID_RES), np.linspace(-2, 2, GRID_RES)
    X, Y = np.meshgrid(x, y)
    Z = np.zeros((GRID_RES, GRID_RES))
    c = complex(0.5 + 0.1*np.sin(f/50), 0.5)
    for i in prange(GRID_RES):
        for j in range(GRID_RES):
            z, it = complex(X[i,j], Y[i,j]), 0
            while abs(z) < 10 and it < 20:
                z = z**5 + c
                if abs(z.real) < 2 or abs(z.imag) < 2:
                    Z[i,j] = it * 5
                    break
                it += 1
    return X, Y, Z

@jit(nopython=True, parallel=True)
def calc_phoenix(f):
    x, y = np.linspace(-1.5, 1.5, GRID_RES), np.linspace(-1.5, 1.5, GRID_RES)
    X, Y = np.meshgrid(x, y)
    Z = np.zeros((GRID_RES, GRID_RES))
    c, p = -0.4, 0.3
    for i in prange(GRID_RES):
        for j in range(GRID_RES):
            z, zp, it = complex(Y[i,j], X[i,j]), 0j, 0
            while abs(z) < 4 and it < 50:
                zn = z*z + c + p*zp
                zp, z, it = z, zn, it + 1
            Z[i,j] = it
    return X, Y, Z

@jit(nopython=True, parallel=True)
def calc_lyapunov(f):
    x, y = np.linspace(3.4, 4.0, GRID_RES), np.linspace(3.4, 4.0, GRID_RES)
    X, Y = np.meshgrid(x, y)
    Z = np.zeros((GRID_RES, GRID_RES))
    for i in prange(GRID_RES):
        for j in range(GRID_RES):
            a, b, cur, lyap = X[i,j], Y[i,j], 0.5, 0.0
            for it in range(50):
                r = a if it%2==0 else b
                cur = r*cur*(1-cur)
                lyap += np.log(abs(r*(1-2*cur)))
            Z[i,j] = lyap if lyap > -50 else -50
    return X, Y, Z

@jit(nopython=True, parallel=True)
def calc_clifford(f):
    res = np.zeros((GRID_RES, GRID_RES))
    a, b, c, d = -1.4 + 0.1*np.sin(f/50), 1.6, 1.0, 0.7
    x, y = 0.0, 0.0
    for _ in range(300000):
        xn, yn = np.sin(a*y) + c*np.cos(a*x), np.sin(b*x) + d*np.cos(b*y)
        x, y = xn, yn
        px, py = int((x+2.5)*GRID_RES/5), int((y+2.5)*GRID_RES/5)
        if 0<=px<GRID_RES and 0<=py<GRID_RES: res[py, px] += 1
    X, Y = np.meshgrid(np.linspace(-2.5,2.5,GRID_RES), np.linspace(-2.5,2.5,GRID_RES))
    return X, Y, np.log1p(res)*5

@jit(nopython=True, parallel=True)
def calc_dejong(f):
    res = np.zeros((GRID_RES, GRID_RES))
    a, b, c, d = 1.4, -2.3 + 0.1*np.sin(f/40), 2.4, -1.2
    x, y = 0.0, 0.0
    for _ in range(300000):
        xn, yn = np.sin(a*y) - np.cos(b*x), np.sin(c*x) - np.cos(d*y)
        x, y = xn, yn
        px, py = int((x+3)*GRID_RES/6), int((y+3)*GRID_RES/6)
        if 0<=px<GRID_RES and 0<=py<GRID_RES: res[py, px] += 1
    X, Y = np.meshgrid(np.linspace(-3,3,GRID_RES), np.linspace(-3,3,GRID_RES))
    return X, Y, np.log1p(res)*5

# --- БЛОК 2: ВЕКТОРНЫЕ 3D ФУНКЦИИ (VOLUMETRIC) ---

def draw_lorenz(ax, f):
    dt, s, r, b, x, y, z = 0.01, 10, 28, 8/3, 0.1, 0, 0
    pts = []
    for _ in range(2500 + f*10):
        dx, dy, dz = s*(y-x)*dt, (x*(r-z)-y)*dt, (x*y-b*z)*dt
        x+=dx; y+=dy; z+=dz
        pts.append([x, y, z])
    p = np.array(pts)
    ax.plot(p[:,0], p[:,1], p[:,2], color='#ff4400', lw=0.8)

def draw_dragon(ax, f):
    it, am = min(12, int(f/70)+6), np.deg2rad(90 + np.sin(f/45)*15)
    pts = np.array([[0,0], [1,0]], dtype=np.float64)
    for _ in range(it):
        c = pts[-1]
        rot = np.array([[np.cos(am), -np.sin(am)], [np.sin(am), np.cos(am)]])
        pts = np.vstack((pts, (np.dot(pts[:-1]-c, rot) + c)[::-1]))
    ax.plot(pts[:,0], pts[:,1], np.linspace(0,10,len(pts)), color='#00ffff', lw=1)

def draw_tree(ax, f):
    ang = np.deg2rad(25 + np.sin(f/30)*10)
    def pb(x, y, z, s, a, d):
        if d==0: return
        x1, y1, z1 = x+s*np.cos(a), y+s*np.sin(a), z+s*0.6
        ax.plot([x,x1], [y,y1], [z,z1], color=gold_cmap(d/10), lw=d)
        pb(x1, y1, z1, s*0.7, a+ang, d-1); pb(x1, y1, z1, s*0.7, a-ang, d-1)
    pb(0,0,0, 5, np.pi/2, 8)

def draw_fern(ax, f):
    n, pts = 8000 + f*200, [[0,0,0]]
    for _ in range(n):
        r, (x,y,z) = np.random.rand(), pts[-1]
        if r<0.01: pts.append([0, 0.16*y, z+0.1])
        elif r<0.86: pts.append([0.85*x+0.04*y, -0.04*x+0.85*y+1.6, z+0.01])
        elif r<0.93: pts.append([0.2*x-0.26*y, 0.23*x+0.22*y+1.6, z+0.05])
        else: pts.append([-0.15*x+0.28*y, 0.26*x+0.24*y+0.44, z+0.05])
    p = np.array(pts)
    ax.scatter(p[:,0], p[:,1], p[:,2], s=0.2, color='#00ff66', alpha=0.3)

def draw_levy(ax, f):
    def lv(p1, p2, d):
        if d==0: return [p1, p2]
        v = p2-p1
        p3 = p1 + 0.5*np.array([v[0]-v[1], v[0]+v[1]])
        return lv(p1,p3,d-1)[:-1] + lv(p3,p2,d-1)
    p = np.array(lv(np.array([-0.5,0]), np.array([0.5,0]), 11))
    ax.plot(p[:,0], p[:,1], np.sin(np.linspace(0,5,len(p))), color='#00ccff', lw=0.8)

def draw_henon(ax, f):
    n, x, y, a, b = 10000+f*300, 0, 0, 1.4, 0.3
    pts = []
    for i in range(n):
        x, y = 1 - a*x**2 + y, b*x
        pts.append([x, y, i/1000])
    p = np.array(pts)
    ax.scatter(p[:,0], p[:,1], p[:,2], s=0.1, color='#ffcc00', alpha=0.4)

def draw_bifur(ax, f):
    r = np.linspace(3.4, 4.0, 1000)
    x = 0.5*np.ones_like(r)
    for _ in range(100): x = r*x*(1-x)
    for i in range(50):
        x = r*x*(1-x)
        ax.plot(r, x, i/10, ',w', color=neon_cmap(0.5), alpha=0.2)

def draw_sierp(ax, f):
    pts = np.array([[0,0,0], [1,0,0], [0.5, 0.86, 0], [0.5, 0.4, 0.8]])
    cur = np.array([0,0,0], dtype=np.float64)
    res = []
    for _ in range(10000):
        cur = (cur + pts[np.random.randint(4)])/2
        res.append(cur.copy())
    p = np.array(res)
    ax.scatter(p[:,0], p[:,1], p[:,2], s=0.1, color='#ffffff')

def draw_lissa(ax, f):
    t = np.linspace(0, 2*np.pi, 2000)
    ax.plot(np.sin(3*t+f/20), np.cos(2*t), np.sin(5*t), color='#ff00ff', lw=2)

def draw_vicsek(ax, f):
    def vs(x, y, z, s, d):
        if d==0:
            ax.scatter([x], [y], [z], s=1, color='#00ffff')
            return
        ns = s/3
        for dx, dy, dz in [(1,1,1), (0,1,1), (2,1,1), (1,0,1), (1,2,1)]:
            vs(x+dx*ns, y+dy*ns, z+dz*ns, ns, d-1)
    vs(0,0,0, 1, 3)

# --- ИСПОЛНИТЕЛЬНЫЙ БЛОК ---

tasks = [
    {"n": "01_Mandel_3D", "m": "s", "f": calc_mandel, "c": neon_cmap},
    {"n": "02_Ship_3D", "m": "s", "f": calc_ship, "c": gold_cmap},
    {"n": "03_Julia_3D", "m": "s", "f": calc_julia, "c": neon_cmap},
    {"n": "04_Plasma_3D", "m": "s", "f": calc_plasma, "c": ice_cmap},
    {"n": "05_Newton_3D", "m": "s", "f": calc_newton, "c": gold_cmap},
    {"n": "06_Bio_3D", "m": "s", "f": calc_biomorph, "c": neon_cmap},
    {"n": "07_Phoenix_3D", "m": "s", "f": calc_phoenix, "c": ice_cmap},
    {"n": "08_Lyap_3D", "m": "s", "f": calc_lyapunov, "c": gold_cmap},
    {"n": "09_Clifford_3D", "m": "s", "f": calc_clifford, "c": neon_cmap},
    {"n": "10_DeJong_3D", "m": "s", "f": calc_dejong, "c": ice_cmap},
    {"n": "11_Lorenz_3D", "m": "v", "f": draw_lorenz},
    {"n": "12_Dragon_3D", "m": "v", "f": draw_dragon},
    {"n": "13_Tree_3D", "m": "v", "f": draw_tree},
    {"n": "14_Fern_3D", "m": "v", "f": draw_fern},
    {"n": "15_Levy_3D", "m": "v", "f": draw_levy},
    {"n": "16_Henon_3D", "m": "v", "f": draw_henon},
    {"n": "17_Bifur_3D", "m": "v", "f": draw_bifur},
    {"n": "18_Sierp_3D", "m": "v", "f": draw_sierp},
    {"n": "19_Lissa_3D", "m": "v", "f": draw_lissa},
    {"n": "20_Vicsek_3D", "m": "v", "f": draw_vicsek}
]

if __name__ == '__main__':
    writer = animation.FFMpegWriter(fps=FPS, bitrate=45000, extra_args=['-pix_fmt', 'yuv420p'])
    
    for t in tasks:
        print(f"\n>>> ГЕНЕРАЦИЯ: {t['n']}")
        fig = plt.figure(figsize=(38.4, 21.6), facecolor='black')
        ax = fig.add_axes([0, 0, 1, 1], projection='3d')
        ax.set_facecolor('black')
        ax.axis('off')

        if t['m'] == "s":
            def update(f):
                ax.clear(); ax.axis('off')
                X, Y, Z = t['f'](f)
                surf = ax.plot_surface(X, Y, Z, cmap=t['c'], linewidth=0, antialiased=False, shade=True)
                ax.view_init(elev=35, azim=f*0.8)
                return [surf]
        else:
            def update(f):
                ax.clear(); ax.axis('off')
                t['f'](ax, f)
                ax.view_init(elev=25, azim=f*1.2)
                return []

        ani = animation.FuncAnimation(fig, update, frames=TOTAL_FRAMES)
        ani.save(f"{t['n']}_4K_3D.mp4", writer=writer)
        plt.close(fig); gc.collect()