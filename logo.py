from manim import *
import subprocess
import sys

class DoomedBrandsHook(Scene):
    def construct(self):
        # 1. Белый фон
        bg = Rectangle(
            width=config.frame_width, 
            height=config.frame_height, 
            fill_color=WHITE, 
            fill_opacity=1,
            stroke_width=0
        )
        self.add(bg)

        brands = [
            "mitsubishi", "alfa_romeo", "maserati", "fiat", 
            "chrysler", "infiniti", "buick", "acura", "lincoln", "jaguar"
        ]
        
        # 2. Создание группы
        logo_group = Group()
        for brand in brands:
            try:
                img = ImageMobject(f"logos/{brand}.png")
                img.height = 1.1 
                logo_group.add(img)
            except Exception:
                fallback = Text(brand.upper(), color=BLACK, font="Arial").scale(0.4)
                logo_group.add(fallback)

        logo_group.arrange_in_grid(rows=2, cols=5, buff=1.0)
        
        # Отступы (масштабируем сетку)
        logo_group.scale(0.7) 
        logo_group.move_to(ORIGIN) 
        
        # 3. Анимация
        appearance_time = 0.8 / len(brands)
        strike_time = 1.2 / len(brands)

        for logo in logo_group:
            self.add(logo)
            self.wait(appearance_time)

        for logo in logo_group:
            # Увеличили толщину до 14 для четкости в 1080p
            cross = VGroup(
                Line(logo.get_corner(UL), logo.get_corner(DR), color=RED, stroke_width=14),
                Line(logo.get_corner(UR), logo.get_corner(DL), color=RED, stroke_width=14)
            )
            self.play(Create(cross), run_time=strike_time)

        self.wait(2)

if __name__ == "__main__":
    # ИЗМЕНЕНИЕ: флаг -pqh для 1080p 60fps
    command = [
        "manim", 
        "-pqh",            # h - high quality (1080p)
        "logo.py", 
        "DoomedBrandsHook"
    ]
    
    try:
        print("Начинаю рендер в 1080p... Это займет чуть больше времени.")
        subprocess.run(command, check=True)
    except Exception as e:
        print(f"Ошибка: {e}")