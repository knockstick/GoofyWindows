"""
GoofyWindows
Author: knockstick
URL: https://github.com/knockstick/GoofyWindows
Version: 1.0

Probably never gonna update this again.
"""

from PIL import Image, ImageTk, ImageOps, ImageDraw
from threading import Thread
import tkinter as tk
import numpy as np
import pyautogui
import random
import pygame
import ctypes
import time
import sys
import os

SETTINGS = {
    'runtime_seconds': 30,
    'effect_duration': 0.5,
    'min_effects': 1,
    'max_effects': 3,
    'frame_delay': 10,
    'overlay_speed': 15,
    'overlay_min_duration': 1.0,
    'overlay_max_duration': 2.5,
    'overlay_max_size': 400,
    'rotation_speed': 5,
    'wave_intensity': 35.0,
    'color_shift_amount': 15,
    'glitch_lines': 20,
    'ripple_intensity': 30,
}

ASSETS = {
    'overlay_image': 'as/overlay.png',
    'jumpscare_image': 'as/fart.png',
    'jumpscare_sound': 'snd/f.mp3',
    'sounds_dir': 'snd',
}

MESSAGES = {
    'error_title': 'Error',
    'error_message': 'Fatal error: Unable to fart in memory at address 0x00006969',
    'image_not_found': 'fart.png NOT FOUND!',
}

print("GoofyWindows by knockstick\nhttps://github.com/knockstick/GoofyWindows")

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class Jumpscare:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.root = tk.Tk()
        self.root.configure(bg='black')
        self.root.overrideredirect(True)

        self.root.geometry(f"{width}x{height}+0+0")
        self.root.attributes('-topmost', True)

        self.canvas = tk.Canvas(
            self.root,
            bg='black',
            highlightthickness=0,
            borderwidth=0,
            width=width,
            height=height
        )
        self.canvas.pack(fill='both', expand=True, padx=0, pady=0)

        try:
            jumpscare_img = Image.open(resource_path(ASSETS['jumpscare_image']))
            jumpscare_img = jumpscare_img.resize((width, height), Image.Resampling.LANCZOS)
        except:
            jumpscare_img = Image.new('RGB', (width, height), 'black')
            draw = ImageDraw.Draw(jumpscare_img)
            draw.text((width/2-100, height/2), MESSAGES['image_not_found'], fill="red")

        self.photo = ImageTk.PhotoImage(jumpscare_img)
        self.canvas.create_image(0, 0, image=self.photo, anchor='nw')

        try:
            jumpscare_sound = pygame.mixer.Sound(resource_path(ASSETS['jumpscare_sound']))
            jumpscare_sound.play()

            self.root.after(int(jumpscare_sound.get_length() * 1000), self.close)
        except:
            self.root.after(2000, self.close)

        self.root.mainloop()
    
    def close(self):
        self.root.destroy()
        sys.exit()

class ScreenEffectsApp:
    def __init__(self):
        pygame.mixer.init()

        self.sounds = []
        sound_dir = resource_path(ASSETS['sounds_dir'])
        if os.path.exists(sound_dir):
            for file in os.listdir(sound_dir):
                if file.endswith('.mp3'):
                    sound_path = os.path.join(sound_dir, file)
                    try:
                        sound = pygame.mixer.Sound(sound_path)
                        self.sounds.append(sound)
                    except:
                        print(f"Failed to load sound: {file}")
        
        screenshot = pyautogui.screenshot()
        self.original_image = Image.fromarray(np.array(screenshot))
        
        self.root = tk.Tk()
        self.root.configure(bg='black')

        self.root.overrideredirect(True)

        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()
        self.root.geometry(f"{self.width}x{self.height}+0+0")

        self.root.attributes('-topmost', True)

        self.canvas = tk.Canvas(
            self.root,
            bg='black',
            highlightthickness=0,
            borderwidth=0,
            width=self.width,
            height=self.height
        )
        self.canvas.pack(fill='both', expand=True, padx=0, pady=0)
        
        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()

        self.effects = [
            self.mirror_horizontal,
            self.mirror_vertical,
            self.rotate_image,
            self.wave_effect,
            self.color_shift,
            self.pixelate,
            self.kaleidoscope,
            self.zoom_pulse,
            self.glitch_effect,
            self.ripple_effect,
            self.fisheye_effect,
            self.swirl_effect,
        ]
        
        overlay_path = resource_path(ASSETS['overlay_image'])
        try:
            self.overlay_image = Image.open(overlay_path).convert('RGBA')

            if self.overlay_image.size[0] > SETTINGS['overlay_max_size'] or self.overlay_image.size[1] > SETTINGS['overlay_max_size']:
                self.overlay_image.thumbnail((SETTINGS['overlay_max_size'], SETTINGS['overlay_max_size']), Image.Resampling.LANCZOS)
        except:
            self.overlay_image = Image.new('RGBA', (200, 200), (0, 0, 0, 0))
            draw = ImageDraw.Draw(self.overlay_image)
            draw.ellipse([0, 0, 199, 199], fill=(255, 0, 0, 128))

        self.overlay_x = random.randint(0, self.width - self.overlay_image.size[0])
        self.overlay_y = random.randint(0, self.height - self.overlay_image.size[1])
        self.overlay_angle = 0
        self.overlay_start_time = 0
        self.overlay_target_x = random.randint(0, self.width - self.overlay_image.size[0])
        self.overlay_target_y = random.randint(0, self.height - self.overlay_image.size[1])
        self.overlay_x = self.overlay_target_x
        self.overlay_y = self.overlay_target_y
        self.overlay_speed = SETTINGS['overlay_speed']
        self.is_overlay_active = False

        self.effects.append(self.overlay_effect)

        self.current_image = self.original_image.copy()
        self.frame_count = 0
        self.effect_start_time = time.time()
        self.start_time = time.time()
        self.current_effects = self.get_random_effects()
        
        self.animate()
        self.root.bind('<Escape>', self.on_exit)
        self.root.mainloop()
    
    def get_new_target_position(self):
        return (
            random.randint(0, self.width - self.overlay_image.size[0]),
            random.randint(0, self.height - self.overlay_image.size[1])
        )

    def play_random_sound(self):
        if self.sounds:
            sound = random.choice(self.sounds)
            Thread(target=sound.play).start()

    def on_exit(self, event):
        pygame.mixer.quit()
        self.root.destroy()

    def get_random_effects(self):
        self.play_random_sound()
        return random.sample(self.effects, random.randint(SETTINGS['min_effects'], SETTINGS['max_effects']))

    def apply_effects(self, img):
        result = img
        for effect in self.current_effects:
            result = effect(result)
        return result

    def fisheye_effect(self, img):
        img_array = np.array(img)
        rows, cols = img_array.shape[:2]
        
        y, x = np.mgrid[0:rows, 0:cols]
        x = 2 * (x - cols/2) / cols
        y = 2 * (y - rows/2) / rows
        
        r = x**2 + y**2
        theta = np.arctan2(y, x)
        
        r_fisheye = (r + 1e-5)**(0.5 + 0.2 * np.sin(self.frame_count / 10))
        
        x_fish = r_fisheye * np.cos(theta)
        y_fish = r_fisheye * np.sin(theta)
        
        x_indices = ((x_fish + 1) * cols/2).astype(np.int32)
        y_indices = ((y_fish + 1) * rows/2).astype(np.int32)
        
        x_indices = np.clip(x_indices, 0, cols-1)
        y_indices = np.clip(y_indices, 0, rows-1)
        
        return Image.fromarray(img_array[y_indices, x_indices])

    def swirl_effect(self, img):
        img_array = np.array(img)
        rows, cols = img_array.shape[:2]
        
        y, x = np.mgrid[0:rows, 0:cols]
        
        center_y, center_x = rows/2, cols/2
        dy = y - center_y
        dx = x - center_x
        radius = np.sqrt(dx**2 + dy**2)
        
        angle = np.arctan2(dy, dx) + radius/30.0 * np.sin(self.frame_count / 10)
        
        new_y = center_y + radius * np.sin(angle)
        new_x = center_x + radius * np.cos(angle)
        
        new_y = np.clip(new_y, 0, rows-1).astype(np.int32)
        new_x = np.clip(new_x, 0, cols-1).astype(np.int32)
        
        return Image.fromarray(img_array[new_y, new_x])

    def mirror_horizontal(self, img):
        return ImageOps.mirror(img)
    
    def mirror_vertical(self, img):
        return ImageOps.flip(img)
    
    def rotate_image(self, img):
        angle = (self.frame_count * SETTINGS['rotation_speed']) % 360
        return img.rotate(angle, expand=False)
    
    def wave_effect(self, img):
        img_array = np.array(img)
        rows, cols = img_array.shape[:2]
        
        for i in range(rows):
            img_array[i] = np.roll(img_array[i],
                                 int(SETTINGS['wave_intensity'] * np.sin(2 * np.pi * i / 150 + self.frame_count / 5)))
        return Image.fromarray(img_array)
    
    def color_shift(self, img):
        img_array = np.array(img)
        r, g, b = img_array[:,:,0], img_array[:,:,1], img_array[:,:,2]
        
        shift_x = int(SETTINGS['color_shift_amount'] * np.sin(self.frame_count / 5))
        shift_y = int(SETTINGS['color_shift_amount'] * np.cos(self.frame_count / 5))
        
        r = np.roll(r, shift_x, axis=1)
        b = np.roll(b, shift_y, axis=1)
        
        img_array[:,:,0] = r
        img_array[:,:,2] = b
        
        return Image.fromarray(img_array)
    
    def pixelate(self, img):
        size_factor = abs(np.sin(self.frame_count / 20)) * 30 + 10
        size = (int(self.width/size_factor), int(self.height/size_factor))
        small_img = img.resize(size, Image.Resampling.NEAREST)
        return small_img.resize((self.width, self.height), Image.Resampling.NEAREST)
    
    def kaleidoscope(self, img):
        size = min(img.size) // 2
        center = (img.size[0] // 2, img.size[1] // 2)
        angle = (self.frame_count * 5) % 360
        
        box = (center[0] - size, center[1] - size,
               center[0] + size, center[1] + size)
        cropped = img.crop(box)
        
        rotated = cropped.rotate(angle)
        mirrored = ImageOps.mirror(rotated)
        
        result = img.copy()
        result.paste(rotated, box)
        result.paste(mirrored, (center[0], center[1] - size))
        return result
    
    def zoom_pulse(self, img):
        scale = 1.0 + 0.2 * np.sin(self.frame_count / 5)
        size = (int(img.size[0] * scale), int(img.size[1] * scale))
        zoomed = img.resize(size, Image.Resampling.BILINEAR)
        
        left = (zoomed.size[0] - self.width) // 2
        top = (zoomed.size[1] - self.height) // 2
        return zoomed.crop((left, top, left + self.width, top + self.height))
    
    def glitch_effect(self, img):
        img_array = np.array(img)
        
        if self.frame_count % 5 == 0:
            for _ in range(SETTINGS['glitch_lines']):
                y = np.random.randint(0, img_array.shape[0])
                shift = np.random.randint(-100, 100)
                img_array[y:y+3] = np.roll(img_array[y:y+3], shift, axis=1)
        
        return Image.fromarray(img_array)
    
    def ripple_effect(self, img):
        img_array = np.array(img)
        rows, cols = img_array.shape[:2]
        
        y, x = np.ogrid[:rows, :cols]
        
        center_y, center_x = rows/2, cols/2
        distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
        
        ripple = np.sin(distance/10 - self.frame_count/3) * SETTINGS['ripple_intensity']
        
        x_shift, y_shift = np.indices((rows, cols))
        x_shift = x_shift + ripple
        y_shift = y_shift + ripple
        
        x_shift = np.clip(x_shift, 0, rows-1).astype(np.int32)
        y_shift = np.clip(y_shift, 0, cols-1).astype(np.int32)
        
        img_array = img_array[x_shift, y_shift]
        return Image.fromarray(img_array)
    
    def overlay_effect(self, img):
        current_time = time.time()

        if not self.is_overlay_active:
            self.overlay_start_time = current_time
            self.is_overlay_active = True
            self.overlay_target_x, self.overlay_target_y = self.get_new_target_position()
        
        if current_time - self.overlay_start_time >= random.uniform(SETTINGS['overlay_min_duration'], SETTINGS['overlay_max_duration']):
            self.is_overlay_active = False
            return img
        
        dx = self.overlay_target_x - self.overlay_x
        dy = self.overlay_target_y - self.overlay_y
        distance = (dx**2 + dy**2)**0.5

        if distance < self.overlay_speed:
            self.overlay_target_x, self.overlay_target_y = self.get_new_target_position()
        else:
            move_x = (dx / distance) * self.overlay_speed
            move_y = (dy / distance) * self.overlay_speed
            self.overlay_x += move_x
            self.overlay_y += move_y

        self.overlay_angle += 5

        result = img.copy()

        rotated_overlay = self.overlay_image.rotate(self.overlay_angle, expand=True, resample=Image.Resampling.BILINEAR)

        overlay = Image.new('RGBA', result.size, (0, 0, 0, 0))

        paste_x = int(self.overlay_x - (rotated_overlay.size[0] - self.overlay_image.size[0]) / 2)
        paste_y = int(self.overlay_y - (rotated_overlay.size[1] - self.overlay_image.size[1]) / 2)

        overlay.paste(rotated_overlay, (paste_x, paste_y), rotated_overlay)

        result = Image.alpha_composite(result.convert('RGBA'), overlay)
        
        return result.convert('RGB')

    def on_exit(self, event):
        pygame.mixer.quit()
        self.root.destroy()
        ctypes.windll.user32.MessageBoxW(0, 
            MESSAGES['error_message'],
            MESSAGES['error_title'],
            0x10)
        Jumpscare(self.width, self.height)
        
    def animate(self):
        current_time = time.time()
        
        if current_time - self.start_time > SETTINGS['runtime_seconds']:
            self.on_exit(None)
            return
            
        if current_time - self.effect_start_time > SETTINGS['effect_duration']:
            if not self.is_overlay_active or current_time - self.overlay_start_time >= random.randint(1, 2):
                self.current_effects = self.get_random_effects()
                self.effect_start_time = current_time
            
        processed_image = self.apply_effects(self.current_image)
        
        photo = ImageTk.PhotoImage(processed_image)
        
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=photo, anchor='nw')
        self.canvas.image = photo
        
        self.frame_count += 1
        self.root.after(SETTINGS['frame_delay'], self.animate)

if __name__ == "__main__":
    app = ScreenEffectsApp()