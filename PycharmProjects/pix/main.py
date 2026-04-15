import customtkinter as ctk
from PIL import Image, ImageEnhance, ImageOps, ImageDraw
import json
import os
from tkinter import filedialog, messagebox, colorchooser
import tkinter as tk
from collections import OrderedDict
import colorsys
import math
import requests
import io
import uuid
import time

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ColorPickerDialog(ctk.CTkToplevel):
    """Кастомный диалог выбора цвета с кругом, ползунками и полями для копирования"""
    
    def __init__(self, parent, initial_color=(255, 255, 255), title="Выбор цвета"):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x650")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        
        self.result_color = None
        self.initial_color = initial_color
        self.r, self.g, self.b = initial_color
        
        # Переменные для ползунков
        self.hue_var = tk.DoubleVar()
        self.sat_var = tk.DoubleVar()
        self.val_var = tk.DoubleVar()
        self.alpha_var = tk.DoubleVar(value=1.0)
        
        # Переменные для полей ввода
        self.hex_var = tk.StringVar()
        self.r_var = tk.IntVar(value=self.r)
        self.g_var = tk.IntVar(value=self.g)
        self.b_var = tk.IntVar(value=self.b)
        
        self.create_widgets()
        self.update_from_rgb()
        
    def create_widgets(self):
        # Заголовок
        ctk.CTkLabel(self, text="Редактор цвета", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        
        # Превью цвета
        preview_frame = ctk.CTkFrame(self)
        preview_frame.pack(pady=5)
        
        self.preview_label = ctk.CTkLabel(preview_frame, text="", width=60, height=40)
        self.preview_label.pack(padx=10, pady=5)
        
        # Цветовой круг (canvas)
        self.color_wheel = tk.Canvas(self, width=200, height=200, bg='white', highlightthickness=0)
        self.color_wheel.pack(pady=5)
        self.draw_color_wheel()
        
        # Обработчик клика на цветовом круге
        self.color_wheel.bind("<B1-Motion>", self.on_wheel_click)
        self.color_wheel.bind("<Button-1>", self.on_wheel_click)
        
        # Ползунки
        sliders_frame = ctk.CTkFrame(self)
        sliders_frame.pack(pady=5, padx=20, fill="x")
        
        # Hue
        ctk.CTkLabel(sliders_frame, text="H:", width=20, anchor="w").grid(row=0, column=0, padx=5, pady=2)
        self.hue_slider = ctk.CTkSlider(sliders_frame, from_=0, to=360, variable=self.hue_var,
                                        command=self.on_slider_change, width=200)
        self.hue_slider.grid(row=0, column=1, padx=5, pady=2)
        
        # Saturation
        ctk.CTkLabel(sliders_frame, text="S:", width=20, anchor="w").grid(row=1, column=0, padx=5, pady=2)
        self.sat_slider = ctk.CTkSlider(sliders_frame, from_=0, to=100, variable=self.sat_var,
                                        command=self.on_slider_change, width=200)
        self.sat_slider.grid(row=1, column=1, padx=5, pady=2)
        
        # Value
        ctk.CTkLabel(sliders_frame, text="V:", width=20, anchor="w").grid(row=2, column=0, padx=5, pady=2)
        self.val_slider = ctk.CTkSlider(sliders_frame, from_=0, to=100, variable=self.val_var,
                                        command=self.on_slider_change, width=200)
        self.val_slider.grid(row=2, column=1, padx=5, pady=2)
        
        # Alpha
        ctk.CTkLabel(sliders_frame, text="A:", width=20, anchor="w").grid(row=3, column=0, padx=5, pady=2)
        self.alpha_slider = ctk.CTkSlider(sliders_frame, from_=0, to=1, variable=self.alpha_var,
                                          command=self.on_slider_change, width=200)
        self.alpha_slider.grid(row=3, column=1, padx=5, pady=2)
        
        # Поля для ввода/копирования
        fields_frame = ctk.CTkFrame(self)
        fields_frame.pack(pady=5, padx=20, fill="x")
        
        # HEX поле
        hex_row = ctk.CTkFrame(fields_frame)
        hex_row.pack(fill="x", pady=2)
        ctk.CTkLabel(hex_row, text="HEX:", width=40, anchor="w").pack(side="left", padx=5)
        self.hex_entry = ctk.CTkEntry(hex_row, textvariable=self.hex_var, width=100)
        self.hex_entry.pack(side="left", padx=5)
        ctk.CTkButton(hex_row, text="Копировать", width=60, height=20,
                      command=self.copy_hex).pack(side="left", padx=2)
        
        # RGB поля
        rgb_row = ctk.CTkFrame(fields_frame)
        rgb_row.pack(fill="x", pady=2)
        ctk.CTkLabel(rgb_row, text="R:", width=40, anchor="w").pack(side="left", padx=5)
        ctk.CTkEntry(rgb_row, textvariable=self.r_var, width=50).pack(side="left", padx=2)
        ctk.CTkLabel(rgb_row, text="G:", width=20, anchor="w").pack(side="left", padx=2)
        ctk.CTkEntry(rgb_row, textvariable=self.g_var, width=50).pack(side="left", padx=2)
        ctk.CTkLabel(rgb_row, text="B:", width=20, anchor="w").pack(side="left", padx=2)
        ctk.CTkEntry(rgb_row, textvariable=self.b_var, width=50).pack(side="left", padx=2)
        
        # Alpha поле
        alpha_row = ctk.CTkFrame(fields_frame)
        alpha_row.pack(fill="x", pady=2)
        ctk.CTkLabel(alpha_row, text="A:", width=40, anchor="w").pack(side="left", padx=5)
        self.alpha_entry = ctk.CTkEntry(alpha_row, textvariable=self.alpha_var, width=50)
        self.alpha_entry.pack(side="left", padx=5)
        
        # Кнопки
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=15)
        
        ctk.CTkButton(btn_frame, text="ОК", width=80, command=self.ok).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Отмена", width=80, command=self.cancel).pack(side="left", padx=5)
        
    def draw_color_wheel(self):
        """Рисуем цветовой круг"""
        size = 200
        center = size // 2
        radius = 90
        
        # Рисуем цветовой круг
        for angle in range(0, 360, 2):
            for r in range(0, radius, 2):
                x = center + int(r * math.cos(math.radians(angle)))
                y = center + int(r * math.sin(math.radians(angle)))
                
                if r <= radius:
                    h = angle / 360.0
                    s = r / radius
                    v = 1.0
                    rgb = colorsys.hsv_to_rgb(h, s, v)
                    color = f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"
                    self.color_wheel.create_oval(x-1, y-1, x+1, y+1, fill=color, outline=color)
    
    def on_wheel_click(self, event):
        """Обработка клика на цветовом круге"""
        center = 100
        dx = event.x - center
        dy = event.y - center
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > 90:
            distance = 90
        
        angle = math.atan2(dy, dx)
        if angle < 0:
            angle += 2 * math.pi
        
        hue = angle / (2 * math.pi) * 360
        sat = distance / 90 * 100
        
        self.hue_var.set(hue)
        self.sat_var.set(sat)
        self.update_from_hsv()
    
    def on_slider_change(self, value=None):
        """Изменение ползунков"""
        self.update_from_hsv()
    
    def update_from_rgb(self):
        """Обновление всех элементов из RGB"""
        r, g, b = self.r, self.g, self.b
        
        # Конвертация в HSV
        h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        
        self.hue_var.set(h * 360)
        self.sat_var.set(s * 100)
        self.val_var.set(v * 100)
        
        # Обновление полей
        self.hex_var.set(f"#{r:02x}{g:02x}{b:02x}")
        self.r_var.set(r)
        self.g_var.set(g)
        self.b_var.set(b)
        
        # Обновление превью
        self.update_preview()
    
    def update_from_hsv(self):
        """Обновление из HSV"""
        h = self.hue_var.get() / 360.0
        s = self.sat_var.get() / 100.0
        v = self.val_var.get() / 100.0
        
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        self.r = int(r * 255)
        self.g = int(g * 255)
        self.b = int(b * 255)
        
        # Обновление полей
        self.hex_var.set(f"#{self.r:02x}{self.g:02x}{self.b:02x}")
        self.r_var.set(self.r)
        self.g_var.set(self.g)
        self.b_var.set(self.b)
        
        # Обновление превью
        self.update_preview()
    
    def update_preview(self):
        """Обновление превью цвета"""
        hex_color = f"#{self.r:02x}{self.g:02x}{self.b:02x}"
        self.preview_label.configure(fg_color=hex_color)
    
    def copy_hex(self):
        """Копировать HEX значение"""
        self.clipboard_clear()
        self.clipboard_append(self.hex_var.get())
    
    def ok(self):
        """ОК - вернуть цвет"""
        a = int(self.alpha_var.get() * 255)
        self.result_color = (self.r, self.g, self.b, a)
        self.destroy()
    
    def cancel(self):
        """Отмена"""
        self.result_color = None
        self.destroy()


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class AnimationTab(ctk.CTkFrame):
    """Вкладка анимации через ComfyUI"""
    
    def __init__(self, parent, main_app):
        super().__init__(parent)
        self.main_app = main_app
        self.animation_frames = []  # Список кадров анимации
        self.comfyui_url = "http://127.0.0.1:8000"
        self.workflow_json = None  # Загруженный workflow JSON
        self.workflow_path = ""  # Путь к загруженному файлу
        
        self.create_widgets()
    
    def create_widgets(self):
        # Заголовок
        ctk.CTkLabel(self, text="Анимация через ComfyUI", 
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Кнопка загрузки JSON workflow
        workflow_frame = ctk.CTkFrame(self)
        workflow_frame.pack(pady=5)
        
        ctk.CTkButton(workflow_frame, text="Загрузить JSON workflow из ComfyUI", 
                      command=self.load_workflow_json).pack(side="left", padx=5)
        
        self.workflow_label = ctk.CTkLabel(workflow_frame, text="Workflow не загружен", 
                                           text_color="red")
        self.workflow_label.pack(side="left", padx=10)
        
        # Поле промпта
        ctk.CTkLabel(self, text="Промпт для анимации:", wraplength=400).pack(pady=5)
        self.prompt_text = ctk.CTkTextbox(self, width=500, height=80)
        self.prompt_text.pack(pady=5)
        self.prompt_text.insert("0.0", "pixel art animation, smooth movement, retro style")
        
        # Количество кадров
        ctk.CTkLabel(self, text="Количество кадров:").pack(pady=5)
        self.frames_var = ctk.StringVar(value="8")
        frames_combo = ctk.CTkComboBox(self, values=["4", "6", "8", "12"], 
                                       variable=self.frames_var, width=100)
        frames_combo.pack(pady=5)
        
        # Кнопка генерации
        self.gen_btn = ctk.CTkButton(self, text="Генерировать анимацию через ComfyUI",
                                     fg_color="#2d8a4e", height=50, font=ctk.CTkFont(size=14, weight="bold"),
                                     command=self.generate_animation)
        self.gen_btn.pack(pady=15)
        
        # Область предпросмотра кадров
        ctk.CTkLabel(self, text="Предпросмотр кадров:").pack(pady=5)
        self.frames_scroll = ctk.CTkScrollableFrame(self, width=600, height=300)
        self.frames_scroll.pack(pady=5)
        
        # Кнопки сохранения
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=10)
        
        ctk.CTkButton(btn_frame, text="Сохранить все кадры как PNG", 
                      command=self.save_frames_as_png).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Сохранить как спрайтшит", 
                      command=self.save_as_spritesheet).pack(side="left", padx=5)
        
        # Статус
        self.status_label = ctk.CTkLabel(self, text="Готов к генерации", text_color="gray")
        self.status_label.pack(pady=5)
    
    def load_workflow_json(self):
        """Загрузка JSON workflow из ComfyUI"""
        filepath = filedialog.askopenfilename(
            title="Выберите JSON workflow из ComfyUI",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not filepath:
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.workflow_json = json.load(f)
            self.workflow_path = filepath
            filename = os.path.basename(filepath)
            self.workflow_label.configure(text=f"✓ {filename}", text_color="green")
            messagebox.showinfo("Успех", f"Workflow загружен:\n{filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить workflow:\n{str(e)}")
            self.workflow_json = None
            self.workflow_label.configure(text="Ошибка загрузки", text_color="red")
    
    def generate_animation(self):
        """Генерация анимации через ComfyUI"""
        if self.main_app.result_image is None:
            messagebox.showwarning("Ошибка", "Сначала создайте спрайт на основной вкладке!")
            return
        
        if self.workflow_json is None:
            messagebox.showwarning("Ошибка", "Сначала загрузите JSON workflow из ComfyUI!")
            return
        
        try:
            self.gen_btn.configure(state="disabled")
            self.status_label.configure(text="Подключение к ComfyUI...", text_color="yellow")
            self.update()
            
            # Проверка подключения к ComfyUI
            try:
                response = requests.get(f"{self.comfyui_url}/", timeout=5)
                if response.status_code != 200:
                    raise Exception("ComfyUI не отвечает")
            except:
                messagebox.showerror("Ошибка", "Не удалось подключиться к ComfyUI.\n"
                                    "Убедитесь, что ComfyUI запущен на http://127.0.0.1:8000")
                self.gen_btn.configure(state="normal")
                self.status_label.configure(text="Ошибка подключения", text_color="red")
                return
            
            # Получаем промпт
            prompt = self.prompt_text.get("0.0", "end").strip()
            if not prompt:
                messagebox.showwarning("Ошибка", "Введите промпт для анимации!")
                self.gen_btn.configure(state="normal")
                return
            
            num_frames = int(self.frames_var.get())
            
            self.status_label.configure(text=f"Загрузка изображения...", text_color="yellow")
            self.update()
            
            # Загружаем изображение в ComfyUI
            image_filename = self.upload_image_to_comfyui(self.main_app.result_image)
            if not image_filename:
                raise Exception("Не удалось загрузить изображение в ComfyUI")
            
            self.status_label.configure(text=f"Генерация {num_frames} кадров...", text_color="yellow")
            self.update()
            
            # Модифицируем workflow
            workflow = self.modify_workflow(prompt, num_frames, image_filename)
            
            # Отправляем запрос
            response = requests.post(f"{self.comfyui_url}/prompt", json=workflow)
            if response.status_code != 200:
                raise Exception(f"Ошибка ComfyUI: {response.text}")
            
            result = response.json()
            prompt_id = result.get("prompt_id")
            
            # Ожидаем завершения генерации
            self.wait_for_completion(prompt_id, num_frames)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка генерации:\n{str(e)}")
            self.gen_btn.configure(state="normal")
            self.status_label.configure(text="Ошибка генерации", text_color="red")
    
    def upload_image_to_comfyui(self, image):
        """Загрузка изображения в ComfyUI через /upload/image"""
        try:
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)
            files = {"image": ("sprite.png", buffer, "image/png")}
            data = {"overwrite": "true"}
            response = requests.post(f"{self.comfyui_url}/upload/image", files=files, data=data)
            if response.status_code == 200:
                result = response.json()
                return result.get("name", "")
            else:
                return None
        except Exception as e:
            print(f"Ошибка загрузки изображения: {e}")
            return None
    
    def modify_workflow(self, prompt, num_frames, image_filename):
        """Модификация workflow JSON перед отправкой"""
        import copy
        workflow = copy.deepcopy(self.workflow_json)
        
        # Модифицируем параметры
        for node_id, node in workflow.items():
            inputs = node.get("inputs", {})
            
            # Ищем узел CLIPTextEncode и меняем промпт
            if node.get("class_type") == "CLIPTextEncode":
                if "text" in inputs:
                    inputs["text"] = prompt
            
            # Ищем узел KSampler и меняем batch_size
            if node.get("class_type") == "KSampler":
                if "batch_size" in inputs:
                    inputs["batch_size"] = num_frames
                # Меняем seed на случайный
                if "seed" in inputs:
                    inputs["seed"] = int(time.time() * 1000) % (2**32)
            
            # Ищем узел EmptyLatentImage и меняем размер
            if node.get("class_type") == "EmptyLatentImage":
                inputs["width"] = self.main_app.result_image.width
                inputs["height"] = self.main_app.result_image.height
                if "batch_size" in inputs:
                    inputs["batch_size"] = num_frames
        
        return workflow
    
    def create_workflow(self, prompt, num_frames):
        """Создание workflow для ComfyUI"""
        workflow = {
            "prompt": prompt,
            "negative_prompt": "blurry, low quality, distorted, deformed",
            "steps": 20,
            "cfg": 7.0,
            "sampler": "euler_a",
            "scheduler": "normal",
            "seed": -1,
            "batch_size": num_frames,
            "width": self.main_app.result_image.width,
            "height": self.main_app.result_image.height,
        }
        return {"workflow": workflow}
    
    def wait_for_completion(self, prompt_id, num_frames):
        """Ожидание завершения генерации"""
        max_attempts = 60  # 5 минут максимум
        for i in range(max_attempts):
            try:
                response = requests.get(f"{self.comfyui_url}/history/{prompt_id}")
                if response.status_code == 200:
                    history = response.json()
                    if prompt_id in history:
                        # Генерация завершена
                        self.process_output(prompt_id, history[prompt_id], num_frames)
                        return
            except:
                pass
            time.sleep(5)  # Ждём 5 секунд между проверками
        
        raise Exception("Превышено время ожидания генерации")
    
    def process_output(self, prompt_id, history, num_frames):
        """Обработка результата генерации"""
        self.status_label.configure(text="Обработка кадров...", text_color="yellow")
        self.update()
        
        # Получаем изображения из истории
        outputs = history.get("outputs", {})
        self.animation_frames = []
        
        for node_id, node_output in outputs.items():
            if "images" in node_output:
                for img_data in node_output["images"]:
                    # Загружаем изображение
                    if "data" in img_data:
                        img_bytes = img_data["data"]
                        img = Image.open(io.BytesIO(img_bytes))
                        
                        # Применяем пост-обработку
                        img = self.post_process_frame(img)
                        self.animation_frames.append(img)
        
        if not self.animation_frames:
            raise Exception("ComfyUI не вернул кадры")
        
        # Отображаем кадры
        self.display_frames()
        
        self.status_label.configure(text=f"Готово! {len(self.animation_frames)} кадров", text_color="green")
        self.gen_btn.configure(state="normal")
    
    def post_process_frame(self, frame):
        """Пост-обработка кадра (мягче, чем основная)"""
        # Конвертируем в RGB если нужно
        if frame.mode != "RGB":
            frame = frame.convert("RGB")
        
        # Мягкий контраст и чёткость
        frame = ImageEnhance.Contrast(frame).enhance(1.1)  # Меньше чем на основной (1.8)
        frame = ImageEnhance.Sharpness(frame).enhance(1.2)  # Меньше чем на основной (2.0)
        
        # Квантизация
        colors = self.main_app.colors_var.get()
        dither = self.main_app.dither_var.get()
        dither_mode = Image.Dither.FLOYD_STEINBERG if dither else Image.Dither.NONE
        frame = frame.quantize(colors=colors, dither=dither_mode)
        frame = frame.convert("RGB")
        
        # Применение палитры если включено
        if self.main_app.use_palette_var.get():
            frame = self.apply_palette_to_frame(frame)
        
        return frame
    
    def apply_palette_to_frame(self, frame):
        """Применение палитры к кадру"""
        # Находим подходящую палитру
        rgb_frame = frame.convert("RGB")
        colors = list(OrderedDict.fromkeys(rgb_frame.getdata()))
        
        for name, palette in self.main_app.PALETTES.items():
            if len(palette) == len(colors):
                # Сортируем по яркости
                def get_lum_rgb(c):
                    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
                
                def get_lum_int(c):
                    r = (c >> 16) & 0xFF
                    g = (c >> 8) & 0xFF
                    b = c & 0xFF
                    return 0.299 * r + 0.587 * g + 0.114 * b
                
                sorted_colors = sorted(colors, key=get_lum_rgb, reverse=True)
                sorted_palette = sorted(palette, key=get_lum_int, reverse=True)
                
                color_map = {}
                for i, color in enumerate(sorted_colors):
                    if i < len(sorted_palette):
                        p = sorted_palette[i]
                        color_map[color] = ((p >> 16) & 0xFF, (p >> 8) & 0xFF, p & 0xFF)
                
                pixels = rgb_frame.load()
                for y in range(rgb_frame.height):
                    for x in range(rgb_frame.width):
                        if pixels[x, y] in color_map:
                            pixels[x, y] = color_map[pixels[x, y]]
                
                return rgb_frame
        
        return frame
    
    def display_frames(self):
        """Отображение кадров в сетке"""
        # Очищаем старые превью
        for widget in self.frames_scroll.winfo_children():
            widget.destroy()
        
        # Вычисляем сетку
        num_frames = len(self.animation_frames)
        cols = min(num_frames, 4)
        rows = (num_frames + cols - 1) // cols
        
        for i, frame in enumerate(self.animation_frames):
            # Увеличиваем для превью
            preview = frame.resize((frame.width * 8, frame.height * 8), Image.NEAREST)
            ctk_img = ctk.CTkImage(light_image=preview, dark_image=preview, size=preview.size)
            
            label = ctk.CTkLabel(self.frames_scroll, image=ctk_img, text=f"Кадр {i+1}")
            label.grid(row=i // cols, column=i % cols, padx=5, pady=5)
    
    def save_frames_as_png(self):
        """Сохранение всех кадров как отдельные PNG"""
        if not self.animation_frames:
            messagebox.showwarning("Ошибка", "Сначала сгенерируйте анимацию!")
            return
        
        folder = filedialog.askdirectory()
        if not folder:
            return
        
        for i, frame in enumerate(self.animation_frames):
            path = os.path.join(folder, f"frame_{i+1:03d}.png")
            frame.save(path)
        
        messagebox.showinfo("Готово", f"Сохранено {len(self.animation_frames)} кадров в:\n{folder}")
    
    def save_as_spritesheet(self):
        """Сохранение как горизонтальный спрайтшит"""
        if not self.animation_frames:
            messagebox.showwarning("Ошибка", "Сначала сгенерируйте анимацию!")
            return
        
        # Создаём горизонтальный спрайтшит
        frame_w = self.animation_frames[0].width
        frame_h = self.animation_frames[0].height
        total_w = frame_w * len(self.animation_frames)
        
        spritesheet = Image.new("RGB", (total_w, frame_h))
        
        for i, frame in enumerate(self.animation_frames):
            spritesheet.paste(frame, (i * frame_w, 0))
        
        # Сохраняем
        path = filedialog.asksaveasfilename(defaultextension=".png",
                                           filetypes=[("PNG", "*.png")])
        if path:
            spritesheet.save(path)
            messagebox.showinfo("Готово", f"Спрайтшит сохранён:\n{path}")


class PixelSpriter(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Jackal56 - AI to Retro Sprite Converter")
        self.geometry("1280x800")
        self.minsize(1100, 650)

        self.config_file = "config.json"
        self.load_config()

        self.original_images = []  # Список кортежей (path, image) для пакетной обработки
        self.result_images = []    # Список обработанных изображений
        self.current_index = 0     # Текущий отображаемый индекс
        self.original_result_image = None  # Оригинальный результат до применения палитр

        self.create_widgets()

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        else:
            self.config = {
                "target_size": 32,
                "colors": 16,
                "contrast": 1.8,
                "sharpness": 2.0,
                "dither": True,
                "upscale_factor": 2,
                "last_input_path": "",
                "last_output_path": ""
            }

    def save_config(self):
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4)

    def create_widgets(self):
        # Левая панель управления
        left_frame = ctk.CTkFrame(self, width=260)
        left_frame.pack(side="left", fill="y", padx=5, pady=10)
        left_frame.pack_propagate(False)  # Фиксировать ширину

        ctk.CTkLabel(left_frame, text="Jackal56", font=ctk.CTkFont(size=16, weight="bold"),
                     wraplength=240).pack(pady=10)

        ctk.CTkButton(left_frame, text="Загрузить", height=35,
                      command=self.load_image).pack(pady=5, padx=10, fill="x")

        # Размер спрайта
        ctk.CTkLabel(left_frame, text="Размер:", wraplength=240).pack(anchor="w", padx=10, pady=(10, 3))
        self.size_var = ctk.StringVar(value=str(self.config["target_size"]))
        for s in ["8", "16", "32", "64"]:
            ctk.CTkRadioButton(left_frame, text=f"{s}×{s}", variable=self.size_var,
                               value=s, width=120).pack(anchor="w", padx=20)

        # Кастомный размер (два поля: ширина × высота)
        self.custom_width_var = tk.StringVar(value="")
        self.custom_height_var = tk.StringVar(value="")
        custom_size_frame = ctk.CTkFrame(left_frame)
        custom_size_frame.pack(anchor="w", padx=20)
        self.custom_radio = ctk.CTkRadioButton(custom_size_frame, text="Свой:", variable=self.size_var,
                                               value="custom", command=self.toggle_custom_size, width=120)
        self.custom_radio.pack(side="left")
        # Поля ввода и разделитель создаются, но скрываются
        self.custom_width_entry = ctk.CTkEntry(custom_size_frame, textvariable=self.custom_width_var, width=35)
        self.custom_x_label = ctk.CTkLabel(custom_size_frame, text="×")
        self.custom_height_entry = ctk.CTkEntry(custom_size_frame, textvariable=self.custom_height_var, width=35)
        # По умолчанию скрыты (не pack'ятся)

        # Количество цветов
        ctk.CTkLabel(left_frame, text="Цветов:", wraplength=240).pack(anchor="w", padx=10, pady=(10, 3))
        self.colors_var = ctk.IntVar(value=self.config["colors"])
        ctk.CTkEntry(left_frame, textvariable=self.colors_var, width=80).pack(padx=10, fill="x")

        # Пресеты цветов
        frame_presets = ctk.CTkFrame(left_frame)
        frame_presets.pack(padx=10, pady=3, fill="x")
        for text, val in [("NES", 54), ("SNES", 32), ("GB", 4), ("16", 16), ("8", 8)]:
            ctk.CTkButton(frame_presets, text=text, height=22, width=30,
                          command=lambda v=val: self.colors_var.set(v)).pack(side="left", padx=2)

        # Настройки
        ctk.CTkLabel(left_frame, text="Контраст:", wraplength=150).pack(anchor="w", padx=10, pady=(10, 3))
        self.contrast_var = ctk.DoubleVar(value=self.config["contrast"])
        ctk.CTkSlider(left_frame, from_=0.5, to=3.0, variable=self.contrast_var).pack(padx=10, fill="x")

        ctk.CTkLabel(left_frame, text="Чёткость:", wraplength=150).pack(anchor="w", padx=10, pady=(5, 3))
        self.sharpness_var = ctk.DoubleVar(value=self.config["sharpness"])
        ctk.CTkSlider(left_frame, from_=0.0, to=4.0, variable=self.sharpness_var).pack(padx=10, fill="x")

        self.dither_var = ctk.BooleanVar(value=self.config["dither"])
        ctk.CTkCheckBox(left_frame, text="Дизеринг", variable=self.dither_var).pack(anchor="w", padx=10, pady=5)

        ctk.CTkLabel(left_frame, text="Увеличение:", wraplength=150).pack(anchor="w", padx=10, pady=(5, 3))
        self.upscale_var = ctk.IntVar(value=self.config["upscale_factor"])
        ctk.CTkComboBox(left_frame, values=["1", "2", "3", "4"], variable=self.upscale_var,
                        width=80).pack(padx=10, fill="x")

        # Кнопка START
        ctk.CTkButton(left_frame, text="▶ START", fg_color="#4a8a4a", height=45,
                      font=ctk.CTkFont(size=16, weight="bold"),
                      command=self.start_conversion).pack(pady=15, padx=10, fill="x")

        # Опции сохранения
        self.spritesheet_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(left_frame, text="Сохранить как спрайтшит",
                        variable=self.spritesheet_var).pack(anchor="w", padx=10, pady=5)

        self.sync_colors_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(left_frame, text="Синхронизировать цвета",
                        variable=self.sync_colors_var).pack(anchor="w", padx=10, pady=2)

        ctk.CTkButton(left_frame, text="Сохранить", height=35,
                      command=self.save_result).pack(pady=5, padx=10, fill="x")

        # Кнопка открытия вкладки Анимация
        ctk.CTkButton(left_frame, text="🎬 Анимация", height=35, fg_color="#2d8a4e",
                      command=self.open_animation_tab).pack(pady=10, padx=10, fill="x")

        # Контейнер для изображений (справа от панели управления)
        images_frame = ctk.CTkFrame(self)
        images_frame.pack(side="right", fill="both", expand=True, padx=5, pady=10)

        # Горизонтальный контейнер для двух колонок
        horizontal_frame = ctk.CTkFrame(images_frame)
        horizontal_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Левая колонка - Исходное изображение
        source_frame = ctk.CTkFrame(horizontal_frame)
        source_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(source_frame, text="Исходное изображение",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        
        # Навигация между изображениями
        nav_frame = ctk.CTkFrame(source_frame)
        nav_frame.pack(pady=2)
        
        self.prev_btn = ctk.CTkButton(nav_frame, text="◀", width=40, height=25,
                                       command=self.prev_image, state="disabled")
        self.prev_btn.pack(side="left", padx=2)
        
        self.image_counter_label = ctk.CTkLabel(nav_frame, text="0/0", width=40)
        self.image_counter_label.pack(side="left", padx=2)
        
        self.next_btn = ctk.CTkButton(nav_frame, text="▶", width=40, height=25,
                                       command=self.next_image, state="disabled")
        self.next_btn.pack(side="left", padx=2)
        
        self.source_preview = ctk.CTkLabel(source_frame, text="Загрузите изображение")
        self.source_preview.pack(pady=5, fill="both", expand=True)

        # Правая колонка - Результат
        result_frame = ctk.CTkFrame(horizontal_frame)
        result_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(result_frame, text="Результат",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)

        # Большое превью результата
        self.result_preview = ctk.CTkLabel(result_frame, text="Нажмите START")
        self.result_preview.pack(pady=5, fill="both", expand=True)

        # Маленькое превью результата (оригинальный размер спрайта)
        ctk.CTkLabel(result_frame, text="Оригинальный размер:",
                     font=ctk.CTkFont(size=11)).pack(pady=(10, 2))
        self.result_small_preview = ctk.CTkLabel(result_frame, text="—")
        self.result_small_preview.pack(pady=(2, 10))

        # Третья колонка - Палитра цветов
        palette_column = ctk.CTkFrame(horizontal_frame, width=240)
        palette_column.pack(side="left", fill="y", padx=5, pady=5)
        palette_column.pack_propagate(False)

        ctk.CTkLabel(palette_column, text="Цвета",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)

        # Чекбокс включения палитр
        self.use_palette_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(palette_column, text="Применить палитру",
                        variable=self.use_palette_var,
                        command=self.toggle_palette).pack(pady=5)

        # Кнопки палитр - в две колонки
        palette_btn_frame = ctk.CTkFrame(palette_column)
        palette_btn_frame.pack(pady=5, fill="x", padx=5)
        buttons = [("NES", 32), ("SNES", 32), ("C64", 16), ("GB", 4), ("MR", 8)]
        for i, (text, count) in enumerate(buttons):
            row = i // 3
            col = i % 3
            ctk.CTkButton(palette_btn_frame, text=f"{text}({count})", height=22, width=65,
                          command=lambda t=text: self.apply_palette(t)).grid(row=row, column=col, padx=2, pady=1)

        # Контейнер для цветовой сетки
        self.palette_scroll = ctk.CTkScrollableFrame(palette_column)
        self.palette_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        self.color_buttons = []  # Список кнопок цветов
        self.current_palette = []  # Текущая палитра

        # Создаём вкладку "Анимация"
        self.create_animation_tab()

    def create_animation_tab(self):
        """Создание вкладки Анимация"""
        # Создаём Toplevel окно для вкладки Анимация
        self.animation_window = None
    
    def open_animation_tab(self):
        """Открыть вкладку Анимация"""
        if self.animation_window is not None:
            self.animation_window.focus()
            return
        
        self.animation_window = ctk.CTkToplevel(self)
        self.animation_window.title("Анимация - Jackal56")
        self.animation_window.geometry("800x700")
        self.animation_window.protocol("WM_DELETE_WINDOW", self.close_animation_tab)
        
        # Создаём вкладку анимации
        animation_tab = AnimationTab(self.animation_window, self)
        animation_tab.pack(fill="both", expand=True, padx=10, pady=10)
    
    def close_animation_tab(self):
        """Закрыть вкладку Анимация"""
        self.animation_window = None

    # Кнопка для открытия вкладки Анимация (добавим в левую панель)
    def add_animation_button(self):
        """Добавить кнопку открытия вкладки Анимация"""
        # Эта функция вызывается после создания виджетов
        pass

    # ====================== ПАЛИТРЫ ======================
    PALETTES = {
        "NES": [0x7C7C7C, 0x0000FC, 0x0000BC, 0x4428BC, 0x940084, 0xA80020, 0xA81000, 0x8C1800,
                0x503000, 0x007800, 0x006800, 0x005800, 0x004058, 0x000000, 0x000000, 0x000000,
                0xBCBCBC, 0x0078F8, 0x0058F8, 0x6844FC, 0xD800CC, 0xE40058, 0xF83800, 0xE45C10,
                0xAC7C00, 0x00B800, 0x00A800, 0x00A844, 0x008888, 0x000000, 0x000000, 0x000000],

        "SNES": [0x000000, 0xFFFFFF, 0x212121, 0x525252, 0x949494, 0xCECECE,
                 0xFF0000, 0xAD0000, 0x630000,
                 0xFF8400, 0xAD5A00, 0x633900,
                 0xFFFF00, 0xADAD00, 0x636300,
                 0x00FF00, 0x00AD00, 0x006300, 0x214210,
                 0x00FFFF, 0x00ADAD, 0x006363,
                 0x0000FF, 0x0000AD, 0x000063, 0x212194,
                 0xFF00FF, 0xAD00AD, 0x630063,
                 0xFFCE94, 0xAD7B42, 0x633110],

        "C64": [0x000000, 0xFFFFFF, 0x68372B, 0x70A4B2, 0x6F3D86, 0x588D43, 0x352879, 0xB8C76F,
                0x6F4F25, 0x433900, 0x9A6759, 0x444444, 0x6C6C6C, 0x9AD284, 0x6C5EB5, 0x959595],

        "GB": [0x0F380F, 0x306230, 0x8BAC0F, 0x9BBC0F],

        "MR": [0x1a1a2e, 0x16213e, 0x0f3460, 0xe94560, 0x53354e, 0xf0c38e, 0x4a7c59, 0xf2a359]
    }

    def toggle_custom_size(self):
        """Показать/скрыть поля ввода кастомного размера"""
        if self.size_var.get() == "custom":
            # Pack в правильном порядке: ширина, ×, высота
            self.custom_width_entry.pack(side="left", padx=2)
            self.custom_x_label.pack(side="left", padx=1)
            self.custom_height_entry.pack(side="left", padx=2)
        else:
            self.custom_width_entry.pack_forget()
            self.custom_x_label.pack_forget()
            self.custom_height_entry.pack_forget()

    def apply_palette(self, palette_name):
        """Применить палитру к результату"""
        if self.result_image is None or palette_name not in self.PALETTES:
            return

        palette = self.PALETTES[palette_name]
        palette_count = len(palette)

        # Получаем уникальные цвета из результата
        rgb_image = self.result_image.convert("RGB")
        colors = list(OrderedDict.fromkeys(rgb_image.getdata()))
        result_count = len(colors)

        # Если цветов в результате больше, чем в палитре - берём только первые palette_count
        # Если меньше - берём все цвета из палитры

        # Сортируем цвета по яркости (от светлого к тёмному)
        def get_luminance_from_rgb(color):
            r, g, b = color
            return 0.299 * r + 0.587 * g + 0.114 * b

        def get_luminance_from_int(color_int):
            r = (color_int >> 16) & 0xFF
            g = (color_int >> 8) & 0xFF
            b = color_int & 0xFF
            return 0.299 * r + 0.587 * g + 0.114 * b

        sorted_colors = sorted(colors, key=get_luminance_from_rgb, reverse=True)  # от светлого к тёмному
        sorted_palette = sorted(palette, key=get_luminance_from_int, reverse=True)

        # Создаём карту замены цветов (берём min(result_count, palette_count) цветов)
        color_map = {}
        for i, color in enumerate(sorted_colors):
            if i < len(sorted_palette):
                p = sorted_palette[i]
                color_map[color] = ((p >> 16) & 0xFF, (p >> 8) & 0xFF, p & 0xFF)
            # Если палитра меньше, чем цветов в результате - оставляем без замены

        # Применяем замену
        pixels = rgb_image.load()
        for y in range(rgb_image.height):
            for x in range(rgb_image.width):
                if pixels[x, y] in color_map:
                    pixels[x, y] = color_map[pixels[x, y]]

        self.result_image = rgb_image

        # Обновляем превью
        target_size, target_height = self.get_target_size()
        large_result = self.result_image.resize((target_size * 10, target_height * 10), Image.NEAREST)
        self.show_preview(large_result, self.result_preview, max_size=(500, 500))
        small_result = self.result_image.resize((target_size * 4, target_height * 4), Image.NEAREST)
        self.show_preview(small_result, self.result_small_preview, max_size=(128, 128))

        # Обновляем палитру
        self.update_palette_display()

    def toggle_palette(self):
        """Вкл/выкл применение палитры"""
        if self.original_result_image is None:
            return

        if self.use_palette_var.get():
            # Включаем - находим подходящую палитру
            rgb_img = self.original_result_image.convert("RGB")
            unique_colors = list(OrderedDict.fromkeys(rgb_img.getdata()))
            for name, palette in self.PALETTES.items():
                if len(palette) == len(unique_colors):
                    self.apply_palette(name)
                    break
        else:
            # Выключаем - возвращаем оригинальное изображение
            self.result_image = self.original_result_image.copy()

            # Обновляем превью
            target_size, target_height = self.get_target_size()
            large_result = self.result_image.resize((target_size * 10, target_height * 10), Image.NEAREST)
            self.show_preview(large_result, self.result_preview, max_size=(500, 500))
            small_result = self.result_image.resize((target_size * 4, target_height * 4), Image.NEAREST)
            self.show_preview(small_result, self.result_small_preview, max_size=(128, 128))

            # Обновляем палитру
            self.update_palette_display()

    def get_target_size(self):
        """Получить целевой размер с учётом кастомного значения"""
        if self.size_var.get() == "custom":
            try:
                width = int(self.custom_width_var.get())
                height = int(self.custom_height_var.get())
                return width, height
            except ValueError:
                messagebox.showwarning("Ошибка", "Введите корректные числа для размера!")
                return None, None
        size = int(self.size_var.get())
        return size, size


    def update_palette_display(self):
        """Обновить отображение палитры цветов результата"""
        if self.result_image is None:
            return

        # Получаем уникальные цвета из результата
        rgb_image = self.result_image.convert("RGB")
        colors = list(OrderedDict.fromkeys(rgb_image.getdata()))

        # Очищаем старые кнопки
        for widget in self.palette_scroll.winfo_children():
            widget.destroy()
        self.color_buttons = []

        # Создаём новые кнопки для каждого цвета
        cols = 4  # Количество колонок в сетке
        for i, color in enumerate(colors):
            r, g, b = color
            hex_color = f"#{r:02x}{g:02x}{b:02x}"

            btn = ctk.CTkButton(
                self.palette_scroll,
                text="",
                width=30,
                height=25,
                fg_color=hex_color,
                hover_color=hex_color,
                command=lambda c=color, idx=i: self.edit_color(c, idx)
            )
            btn.grid(row=i // cols, column=i % cols, padx=2, pady=2)
            self.color_buttons.append(btn)

    def edit_color(self, old_color, index):
        """Редактировать цвет в палитре"""
        r, g, b = old_color
        hex_color = "#{:02x}{:02x}{:02x}".format(r, g, b).lower()

        # Открываем кастомный диалог выбора цвета
        dialog = ColorPickerDialog(self, initial_color=(r, g, b), title=f"Цвет: {hex_color}")
        dialog.update()  # Обновляем диалог для корректного отображения
        self.wait_window(dialog)
        
        if dialog.result_color is None:
            return  # Пользователь отменил

        nr, ng, nb, na = dialog.result_color

        # Заменяем цвет в result_image
        if self.result_image is not None:
            rgb_image = self.result_image.convert("RGB")
            pixels = rgb_image.load()
            for y in range(rgb_image.height):
                for x in range(rgb_image.width):
                    if pixels[x, y] == old_color:
                        pixels[x, y] = (nr, ng, nb)
            self.result_image = rgb_image

            # Обновляем превью
            target_size, target_height = self.get_target_size()
            large_result = self.result_image.resize((target_size * 10, target_height * 10), Image.NEAREST)
            self.show_preview(large_result, self.result_preview, max_size=(500, 500))
            small_result = self.result_image.resize((target_size * 4, target_height * 4), Image.NEAREST)
            self.show_preview(small_result, self.result_small_preview, max_size=(128, 128))

            # Обновляем палитру
            self.update_palette_display()

    def load_image(self):
        """Загрузка одного или нескольких изображений для пакетной обработки"""
        paths = filedialog.askopenfilenames(
            title="Выберите изображения для обработки",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp")]
        )
        if not paths:
            return
        
        self.original_images = []
        for path in paths:
            try:
                img = Image.open(path).convert("RGB")
                self.original_images.append((path, img))
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить {path}:\n{str(e)}")
        
        if self.original_images:
            # Отображаем первое изображение
            self.current_index = 0
            self.show_current_source()
            messagebox.showinfo("Загружено", f"Загружено изображений: {len(self.original_images)}")
    
    def show_current_source(self):
        """Показать текущее исходное изображение"""
        if self.original_images and self.current_index < len(self.original_images):
            path, img = self.original_images[self.current_index]
            self.show_preview(img, self.source_preview, max_size=(500, 500))
        self.update_navigation()

    def update_navigation(self):
        """Обновить состояние кнопок навигации и счётчик"""
        total = len(self.original_images)
        if total > 0:
            self.image_counter_label.configure(text=f"{self.current_index + 1}/{total}")
            self.prev_btn.configure(state="normal" if self.current_index > 0 else "disabled")
            self.next_btn.configure(state="normal" if self.current_index < total - 1 else "disabled")
        else:
            self.image_counter_label.configure(text="0/0")
            self.prev_btn.configure(state="disabled")
            self.next_btn.configure(state="disabled")

    def prev_image(self):
        """Переключиться на предыдущее изображение"""
        if self.current_index > 0:
            self.current_index -= 1
            self.show_current_source()
            # Если есть обработанные результаты, показываем и их
            if self.result_images:
                self.show_current_result()

    def next_image(self):
        """Переключиться на следующее изображение"""
        if self.original_images and self.current_index < len(self.original_images) - 1:
            self.current_index += 1
            self.show_current_source()
            # Если есть обработанные результаты, показываем и их
            if self.result_images:
                self.show_current_result()

    def show_preview(self, pil_image, label_widget, max_size=(420, 420)):
        if pil_image is None:
            return
        preview = pil_image.copy()
        preview.thumbnail(max_size, Image.LANCZOS)
        ctk_img = ctk.CTkImage(light_image=preview, dark_image=preview, size=preview.size)
        label_widget.configure(image=ctk_img, text="")

    def process_single_image(self, img, target_size, target_height):
        """Обработка одного изображения с применением всех настроек"""
        colors = self.colors_var.get()
        contrast = self.contrast_var.get()
        sharpness = self.sharpness_var.get()
        dither = self.dither_var.get()
        upscale = int(self.upscale_var.get())

        processed = img.copy().convert("RGB")

        # 1. Увеличение
        if upscale > 1:
            processed = processed.resize((processed.width * upscale, processed.height * upscale), Image.NEAREST)

        # 2. Контраст и чёткость
        processed = ImageEnhance.Contrast(processed).enhance(contrast)
        processed = ImageEnhance.Sharpness(processed).enhance(sharpness)

        # 3. Autocontrast ТОЛЬКО ДО квантизации
        processed = ImageOps.autocontrast(processed, cutoff=2)

        # 4. Квантизация
        dither_mode = Image.Dither.FLOYD_STEINBERG if hasattr(Image.Dither, "FLOYD_STEINBERG") else Image.Dither.NONE
        processed = processed.quantize(colors=colors, dither=dither_mode if dither else Image.Dither.NONE)

        # 5. Уменьшение
        processed = processed.resize((target_size, target_height), Image.NEAREST)

        # 6. Финальная обработка (без autocontrast в режиме P)
        processed = processed.convert("RGB")
        processed = ImageEnhance.Contrast(processed).enhance(1.2)

        return processed

    def start_conversion(self):
        if not self.original_images:
            messagebox.showwarning("Ошибка", "Сначала загрузите изображения!")
            return

        target_size, target_height = self.get_target_size()
        if target_size is None:
            return

        try:
            self.result_images = []
            total = len(self.original_images)

            for i, (path, img) in enumerate(self.original_images):
                # Обработка каждого изображения
                processed = self.process_single_image(img, target_size, target_height)
                self.result_images.append((path, processed))

            # Устанавливаем первое изображение как текущее
            self.current_index = 0
            self.result_image = self.result_images[0][1]
            self.original_result_image = self.result_image.copy()

            # Показываем большое превью результата
            large_result = self.result_image.resize((target_size * 10, target_height * 10), Image.NEAREST)
            self.show_preview(large_result, self.result_preview, max_size=(500, 500))

            # Показываем маленькое превью
            small_result = self.result_image.resize((target_size * 4, target_height * 4), Image.NEAREST)
            self.show_preview(small_result, self.result_small_preview, max_size=(128, 128))

            # Применяем палитру если включено
            if self.use_palette_var.get() and self.result_image is not None:
                rgb_img = self.result_image.convert("RGB")
                unique_colors = list(OrderedDict.fromkeys(rgb_img.getdata()))
                for name, palette in self.PALETTES.items():
                    if len(palette) == len(unique_colors):
                        self.apply_palette(name)
                        break

            # Если палитра выключена, обновляем всё равно
            if not self.use_palette_var.get():
                self.update_palette_display()

            # Обновляем палитру цветов
            self.update_palette_display()

            self.save_config()
            messagebox.showinfo("Готово", f"Обработано изображений: {total}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка:\n{str(e)}")
            print("Ошибка в start_conversion:", e)

    def sync_colors_to_all(self):
        """Синхронизировать цвета текущего изображения со всеми остальными"""
        if not self.result_images or self.current_index >= len(self.result_images):
            return
        
        # Получаем цвета текущего изображения
        current_img = self.result_images[self.current_index][1].convert("RGB")
        source_colors = list(OrderedDict.fromkeys(current_img.getdata()))
        
        def get_luminance(color):
            r, g, b = color
            return 0.299 * r + 0.587 * g + 0.114 * b
        
        # Сортируем цвета источника по яркости
        sorted_source = sorted(source_colors, key=get_luminance, reverse=True)
        
        # Применяем к каждому изображению
        for i, (path, img) in enumerate(self.result_images):
            if i == self.current_index:
                continue  # Пропускаем текущее изображение
            
            rgb_img = img.convert("RGB")
            img_colors = list(OrderedDict.fromkeys(rgb_img.getdata()))
            sorted_img_colors = sorted(img_colors, key=get_luminance, reverse=True)
            
            # Создаём карту замены: сопоставляем цвета по порядку яркости
            color_map = {}
            for j, color in enumerate(sorted_img_colors):
                if j < len(sorted_source):
                    color_map[color] = sorted_source[j]
                else:
                    # Если цветов больше, чем в источнике - заменяем на ближайший по яркости
                    if sorted_source:
                        color_map[color] = sorted_source[-1]  # Последний (самый тёмный)
            
            # Применяем замену
            pixels = rgb_img.load()
            for y in range(rgb_img.height):
                for x in range(rgb_img.width):
                    if pixels[x, y] in color_map:
                        pixels[x, y] = color_map[pixels[x, y]]
            
            # Обновляем изображение в списке
            self.result_images[i] = (path, rgb_img)
        
        # Обновляем текущее изображение и превью
        self.show_current_result()
    
    def show_current_result(self):
        """Показать текущий результат"""
        if self.result_images and self.current_index < len(self.result_images):
            target_size, target_height = self.get_target_size()
            if target_size is None:
                return
            
            _, result_img = self.result_images[self.current_index]
            self.result_image = result_img
            
            # Показываем большое превью результата
            large_result = result_img.resize((target_size * 10, target_height * 10), Image.NEAREST)
            self.show_preview(large_result, self.result_preview, max_size=(500, 500))
            
            # Показываем маленькое превью
            small_result = result_img.resize((target_size * 4, target_height * 4), Image.NEAREST)
            self.show_preview(small_result, self.result_small_preview, max_size=(128, 128))
            
            # Обновляем палитру
            self.update_palette_display()

    def save_result(self):
        if not self.result_images:
            messagebox.showwarning("Ошибка", "Сначала нажмите START!")
            return

        # Если включена синхронизация цветов - применяем цвета текущего изображения ко всем
        if self.sync_colors_var.get() and len(self.result_images) > 1:
            self.sync_colors_to_all()

        # Если только одно изображение - сохраняем как раньше
        if len(self.result_images) == 1:
            path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG", "*.png"), ("All files", "*.*")]
            )
            if path:
                _, result_img = self.result_images[0]
                result_img.save(path)
                messagebox.showinfo("Готово", f"Спрайт сохранён:\n{path}")
        else:
            # Проверяем опцию спрайтшита
            if self.spritesheet_var.get():
                # Сохраняем как спрайтшит
                self.save_as_spritesheet()
            else:
                # Пакетное сохранение - спрашиваем папку
                result = messagebox.askyesno(
                    "Сохранение",
                    f"У вас {len(self.result_images)} обработанных изображений.\n"
                    "Сохранить все в папку?"
                )
                if result:
                    folder = filedialog.askdirectory()
                    if folder:
                        saved_count = 0
                        for orig_path, result_img in self.result_images:
                            # Создаём имя файла на основе оригинального
                            filename = os.path.basename(orig_path)
                            name, ext = os.path.splitext(filename)
                            save_path = os.path.join(folder, f"{name}_processed{ext}")
                            result_img.save(save_path)
                            saved_count += 1
                        messagebox.showinfo("Готово", f"Сохранено {saved_count} изображений в:\n{folder}")
                else:
                    # Сохраняем только текущее
                    path = filedialog.asksaveasfilename(
                        defaultextension=".png",
                        filetypes=[("PNG", "*.png"), ("All files", "*.*")]
                    )
                    if path:
                        _, result_img = self.result_images[self.current_index]
                        result_img.save(path)
                        messagebox.showinfo("Готово", f"Спрайт сохранён:\n{path}")

    def save_as_spritesheet(self):
        """Сохранение всех изображений как горизонтальный спрайтшит"""
        if not self.result_images:
            return

        # Получаем размеры первого изображения
        _, first_img = self.result_images[0]
        img_width = first_img.width
        img_height = first_img.height
        total_width = img_width * len(self.result_images)

        # Создаём спрайтшит
        spritesheet = Image.new("RGB", (total_width, img_height))

        # Размещаем все изображения в ряд
        for i, (_, img) in enumerate(self.result_images):
            spritesheet.paste(img, (i * img_width, 0))

        # Сохраняем
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("All files", "*.*")]
        )
        if path:
            spritesheet.save(path)
            messagebox.showinfo("Готово", f"Спрайтшит сохранён:\n{path}")


if __name__ == "__main__":
    app = PixelSpriter()
    app.mainloop()