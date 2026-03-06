"""
НЕОНОВЫЕ ФРАКТАЛЬНОЕ ДЕРЕВО С ПАПОРОТНИКАМИ + BLOOM
Версия, которая должна работать без ошибок типизации Numba и проблем с imageio

Установка (если ещё не):
    pip install --upgrade numba numpy imageio av

Для теста уменьшите разрешение и количество кадров:
    WIDTH=1280; HEIGHT=720; FRAMES=120; TREE_DEPTH=10; FERN_POINTS=5000; BLOOM_PASSES=2
"""

import numba as nb
import numpy as np
import imageio
import time
import math

# ==================== НАСТРОЙКИ ====================
WIDTH       = 3840
HEIGHT      = 2160
FRAMES      = 900           # 30 сек × 30 fps
FPS         = 30

TREE_DEPTH         = 13
FERN_POINTS        = 10000
FERN_ON_BRANCH_LEN = 8.0

# Bloom
BLOOM_THRESHOLD    = 0.75
BLOOM_INTENSITY    = 1.4
BLOOM_PASSES       = 3
BLOOM_SIGMA_BASE   = 6.0

# Тестовый режим — раскомментировать при необходимости
# WIDTH=1280; HEIGHT=720; FRAMES=120; TREE_DEPTH=10; FERN_POINTS=5000; BLOOM_PASSES=2

@nb.njit(fastmath=True, cache=True)
def hsv_to_rgb(h, s, v):
    h = h % 1.0
    i = int(h * 6)
    f = h * 6 - i
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    if   i == 0: return v, t, p
    elif i == 1: return q, v, p
    elif i == 2: return p, v, t
    elif i == 3: return p, q, v
    elif i == 4: return t, p, v
    else:        return v, p, q

# ==================== BLOOM ====================
@nb.njit(fastmath=True, parallel=True, cache=True)
def apply_gaussian_blur(img_in, img_out, sigma):
    ksize = int(sigma * 3.5) * 2 + 1
    if ksize % 2 == 0: ksize += 1
    half = ksize // 2
    
    weight_sum = 0.0
    weights = np.zeros(ksize, dtype=np.float32)
    for i in range(ksize):
        x = i - half
        w = math.exp(-0.5 * (x*x) / (sigma*sigma))
        weights[i] = w
        weight_sum += w
    for i in range(ksize):
        weights[i] /= weight_sum
    
    h, w, _ = img_in.shape
    temp = np.zeros((h, w, 3), dtype=np.float32)
    
    # Horizontal
    for y in nb.prange(h):
        for x in range(w):
            r = g = b = 0.0
            for k in range(ksize):
                xx = x + (k - half)
                if 0 <= xx < w:
                    ww = weights[k]
                    r += img_in[y, xx, 0] * ww
                    g += img_in[y, xx, 1] * ww
                    b += img_in[y, xx, 2] * ww
            temp[y, x, 0] = r; temp[y, x, 1] = g; temp[y, x, 2] = b
    
    # Vertical
    for y in nb.prange(h):
        for x in range(w):
            r = g = b = 0.0
            for k in range(ksize):
                yy = y + (k - half)
                if 0 <= yy < h:
                    ww = weights[k]
                    r += temp[yy, x, 0] * ww
                    g += temp[yy, x, 1] * ww
                    b += temp[yy, x, 2] * ww
            img_out[y, x, 0] = r; img_out[y, x, 1] = g; img_out[y, x, 2] = b

@nb.njit(fastmath=True, parallel=True, cache=True)
def apply_bloom(img, temp1, temp2):
    h, w, _ = img.shape
    for y in nb.prange(h):
        for x in range(w):
            brightness = max(img[y,x,0], img[y,x,1], img[y,x,2]) / 255.0
            if brightness > BLOOM_THRESHOLD:
                mul = (brightness - BLOOM_THRESHOLD) / (1.0 - BLOOM_THRESHOLD)
                mul *= mul
                temp1[y,x,0] = img[y,x,0] * mul / 255.0
                temp1[y,x,1] = img[y,x,1] * mul / 255.0
                temp1[y,x,2] = img[y,x,2] * mul / 255.0
            else:
                temp1[y,x,:] = 0.0
    
    sigma = BLOOM_SIGMA_BASE
    apply_gaussian_blur(temp1, temp2, sigma)
    for _ in range(1, BLOOM_PASSES):
        sigma *= 1.6
        apply_gaussian_blur(temp2, temp1, sigma)
        apply_gaussian_blur(temp1, temp2, sigma)
    
    for y in nb.prange(h):
        for x in range(w):
            img[y,x,0] = min(255, img[y,x,0] + int(temp2[y,x,0] * 255 * BLOOM_INTENSITY))
            img[y,x,1] = min(255, img[y,x,1] + int(temp2[y,x,1] * 255 * BLOOM_INTENSITY))
            img[y,x,2] = min(255, img[y,x,2] + int(temp2[y,x,2] * 255 * BLOOM_INTENSITY))

# ==================== РЕНДЕР ДЕРЕВА ====================
@nb.njit(fastmath=True, cache=True)
def barnsley_fern_step(x, y):
    r = np.random.random()
    if r < 0.01:
        return 0.0, 0.16 * y
    elif r < 0.86:
        return 0.85 * x + 0.04 * y, -0.04 * x + 0.85 * y + 1.6
    elif r < 0.93:
        return 0.20 * x - 0.26 * y, 0.23 * x + 0.22 * y + 1.6
    else:
        return -0.15 * x + 0.28 * y, 0.26 * x + 0.24 * y + 0.44

@nb.njit(fastmath=True, parallel=True, cache=True)
def render_tree_fern(frame_idx, w, h, img, temp1, temp2):
    t = frame_idx / 180.0
    cam_angle = t * 0.55 + math.sin(t * 0.2) * 0.15
    cam_dist = 240 + 45 * math.sin(t * 0.35)
    
    cam_x = math.cos(cam_angle) * cam_dist
    cam_z = math.sin(cam_angle) * cam_dist
    cam_y = 50 + 35 * math.sin(t * 0.6)
    
    # Очистка кадра — векторное присваивание (самый надёжный способ для Numba)
    img[:] = np.array([3, 6, 10], dtype=np.uint8)
    
    MAX_STACK = 1024
    stack_x1   = np.zeros(MAX_STACK, dtype=np.float32)
    stack_y1   = np.zeros(MAX_STACK, dtype=np.float32)
    stack_z1   = np.zeros(MAX_STACK, dtype=np.float32)
    stack_x2   = np.zeros(MAX_STACK, dtype=np.float32)
    stack_y2   = np.zeros(MAX_STACK, dtype=np.float32)
    stack_z2   = np.zeros(MAX_STACK, dtype=np.float32)
    stack_len  = np.zeros(MAX_STACK, dtype=np.float32)
    stack_depth= np.zeros(MAX_STACK, dtype=np.int32)
    sp = 0
    
    stack_x1[0] = 0.0; stack_y1[0] = 0.0; stack_z1[0] = 0.0
    stack_x2[0] = 0.0; stack_y2[0] = 140.0; stack_z2[0] = 0.0
    stack_len[0] = 140.0
    stack_depth[0] = 0
    sp = 1
    
    while sp > 0:
        sp -= 1
        x1 = stack_x1[sp]; y1 = stack_y1[sp]; z1 = stack_z1[sp]
        x2 = stack_x2[sp]; y2 = stack_y2[sp]; z2 = stack_z2[sp]
        blen = stack_len[sp]; depth = stack_depth[sp]
        
        if depth >= TREE_DEPTH or blen < 3.0:
            continue
        
        def project(xx, yy, zz):
            dx = xx - cam_x; dy = yy - cam_y; dz = zz - cam_z
            depth_val = max(dz + 320, 20)
            scale = 420.0 / depth_val
            sx = int(w/2 + dx * scale)
            sy = int(h/2 - dy * scale)
            return sx, sy, scale
        
        sx1, sy1, _ = project(x1, y1, z1)
        sx2, sy2, thick = project(x2, y2, z2)
        
        if not (0 <= sx1 < w and 0 <= sy1 < h and 0 <= sx2 < w and 0 <= sy2 < h):
            continue
        
        thickness = max(1, int(thick * blen * 0.22))
        
        base_hue = 0.28 + depth * 0.03
        cr, cg, cb = hsv_to_rgb(base_hue, 0.85, 0.9 + 0.1 * math.sin(frame_idx*0.04 + depth))
        col_r = int(cr * 255); col_g = int(cg * 255); col_b = int(cb * 255)
        
        dx = sx2 - sx1; dy = sy2 - sy1
        steps = max(abs(dx), abs(dy), 1)
        xinc = dx / steps; yinc = dy / steps
        x, y = float(sx1), float(sy1)
        for _ in range(int(steps) + 2):
            ix, iy = int(x), int(y)
            if 0 <= ix < w and 0 <= iy < h:
                for dy_ in range(-thickness//2, thickness//2 + 1):
                    for dx_ in range(-thickness//2, thickness//2 + 1):
                        nix = ix + dx_; niy = iy + dy_
                        if 0 <= nix < w and 0 <= niy < h:
                            dist = math.sqrt(dx_*dx_ + dy_*dy_)
                            alpha = max(0.0, 1.0 - dist / (thickness * 0.65))
                            if alpha > 0:
                                img[niy, nix, 0] = min(255, int(img[niy, nix, 0] + col_r * alpha * 0.7))
                                img[niy, nix, 1] = min(255, int(img[niy, nix, 1] + col_g * alpha * 0.8))
                                img[niy, nix, 2] = min(255, int(img[niy, nix, 2] + col_b * alpha * 0.9))
            x += xinc; y += yinc
        
        if blen < FERN_ON_BRANCH_LEN:
            fx, fy, fz = x2, y2, z2
            scale_fern = blen * 0.55
            
            fern_hue = 0.32 + depth * 0.055 + math.sin(frame_idx * 0.012 + depth * 1.8) * 0.08
            fern_sat = 0.92 - depth * 0.03
            fern_val_base = 0.88 + 0.12 * math.sin(frame_idx * 0.19 + depth * 0.7)
            
            for p in range(FERN_POINTS):
                if p == 0:
                    px = py = 0.0
                else:
                    px, py = barnsley_fern_step(px, py)
                
                angle_fern = frame_idx * 0.009 + depth * 0.5 + math.sin(t + depth) * 0.3
                rx = px * math.cos(angle_fern) - py * math.sin(angle_fern)
                ry = px * math.sin(angle_fern) + py * math.cos(angle_fern)
                
                rx *= scale_fern; ry *= scale_fern
                
                sx, sy, _ = project(fx + rx, fy + ry * 0.7, fz + rx * 0.15)
                
                if 0 <= sx < w and 0 <= sy < h:
                    fern_val = fern_val_base + 0.08 * math.sin(frame_idx * 0.25 + p * 0.0005)
                    fr, fg, fb = hsv_to_rgb(fern_hue, fern_sat, fern_val)
                    gr = int(fr * 255 * 1.1)
                    gg = int(fg * 255 * 1.3)
                    gb = int(fb * 255 * 0.9)
                    
                    img[sy, sx, 0] = min(255, img[sy, sx, 0] + gr)
                    img[sy, sx, 1] = min(255, img[sy, sx, 1] + gg)
                    img[sy, sx, 2] = min(255, img[sy, sx, 2] + gb)
            
            continue
        
        if depth + 1 < TREE_DEPTH:
            angle_l = 0.95 + 0.25 * math.sin(t * 1.4 + depth * 2.1) + (np.random.random() - 0.5) * 0.4
            angle_r = -0.90 - 0.22 * math.cos(t * 1.7 + depth * 1.9) + (np.random.random() - 0.5) * 0.35
            
            scale_next = 0.58 + 0.10 * math.sin(t * 2.4 + depth * 4.2)
            next_len = blen * scale_next
            
            if sp + 2 < MAX_STACK:
                dx = x2 - x1; dy = y2 - y1; dz = z2 - z1
                len_orig = math.sqrt(dx*dx + dy*dy + dz*dz) or 1.0
                ux = dx / len_orig; uy = dy / len_orig; uz = dz / len_orig
                
                nx_l = ux * math.cos(angle_l) - uz * math.sin(angle_l)
                nz_l = ux * math.sin(angle_l) + uz * math.cos(angle_l)
                ny_l = uy * 0.9
                
                stack_x1[sp] = x2; stack_y1[sp] = y2; stack_z1[sp] = z2
                stack_x2[sp] = x2 + nx_l * next_len
                stack_y2[sp] = y2 + ny_l * next_len
                stack_z2[sp] = z2 + nz_l * next_len
                stack_len[sp] = next_len
                stack_depth[sp] = depth + 1
                sp += 1
                
                nx_r = ux * math.cos(angle_r) - uz * math.sin(angle_r)
                nz_r = ux * math.sin(angle_r) + uz * math.cos(angle_r)
                ny_r = uy * 0.9
                
                stack_x1[sp] = x2; stack_y1[sp] = y2; stack_z1[sp] = z2
                stack_x2[sp] = x2 + nx_r * next_len
                stack_y2[sp] = y2 + ny_r * next_len
                stack_z2[sp] = z2 + nz_r * next_len
                stack_len[sp] = next_len
                stack_depth[sp] = depth + 1
                sp += 1

# ==================== СОХРАНЕНИЕ ВИДЕО ====================
def render_and_save(filename):
    print(f"\n=== Рендер: {filename} ===")
    start = time.time()
    
    # Самый простой и совместимый вариант — минимум параметров
    writer = imageio.get_writer(
        filename,
        fps=FPS,
        codec='libx264',
    )
    
    # Если хотите лучшее качество — раскомментируйте и используйте этот вариант вместо предыдущего:
    # writer = imageio.get_writer(
    #     filename,
    #     fps=FPS,
    #     codec='libx264',
    #     codec_kwargs={
    #         'crf': 19,
    #         'preset': 'medium',
    #     }
    # )
    
    buffer = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    bloom_temp1 = np.zeros((HEIGHT, WIDTH, 3), dtype=np.float32)
    bloom_temp2 = np.zeros((HEIGHT, WIDTH, 3), dtype=np.float32)
    
    for f in range(FRAMES):
        t0 = time.time()
        render_tree_fern(f, WIDTH, HEIGHT, buffer, bloom_temp1, bloom_temp2)
        
        if BLOOM_PASSES > 0:
            apply_bloom(buffer.astype(np.float32), bloom_temp1, bloom_temp2)
        
        writer.append_data(buffer)
        print(f"  кадр {f+1:4d}/{FRAMES}   — {time.time()-t0:5.2f} с")
    
    writer.close()
    print(f"Готово за {(time.time()-start)/60:.1f} минут\n")

if __name__ == "__main__":
    print("Запуск рендера неонового дерева с папоротниками + bloom")
    render_and_save("neon_tree_fern_bloom_final_4k_30s.mp4")
    print("Готово!")