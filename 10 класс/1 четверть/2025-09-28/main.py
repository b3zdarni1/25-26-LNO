#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Doodle Jumper: Космическая Котлета
==================================
Весёлый клон Doodle Jump на Python + Pygame в ОДНОМ файле.

Запуск:  pip install pygame && python main.py

Ключевые фишки: ломающиеся платформы, джетпаки, монстрики, система рекордов
(saves.json), кейсы/скины «67»/«52» и рекламные мемы MusorDrop.
Вся графика и звук генерируются кодом — внешних файлов нет.
"""

import os
import json
import math
import random
import time
import datetime
import traceback
from array import array

import pygame

# ═══════════════════════════════════════════════════════════════════════════
#  КОНСТАНТЫ: ЭКРАН И ФИЗИКА
# ═══════════════════════════════════════════════════════════════════════════
SCREEN_W = 480                      # ширина окна
SCREEN_H = 720                      # высота окна
FPS = 60                            # целевой FPS
MAX_DT = 1.0 / 30.0                 # ограничение dt (защита от «прыжков» при лаге)
TITLE = "Doodle Jumper: Космическая Котлета"

GRAVITY = 1900.0                    # гравитация, px/с²
JUMP_POWER = -820.0                 # скорость обычного прыжка, px/с (вверх = минус)
MAX_FALL_SPEED = 1400.0             # предел скорости падения
SPRING_MULT = 2.5                   # множитель пружины
ROCKET_POWER = -2600.0              # стартовая скорость ракеты
ROCKET_TRAIL_TIME = 0.9             # сколько секунд ракета рисует огненный след
PLAYER_SPEED = 400.0                # максимальная горизонтальная скорость игрока, px/с
PLAYER_ACCEL = 3200.0               # горизонтальное ускорение (обычное)
PLAYER_ACCEL_JETPACK = 1400.0       # горизонтальное ускорение при полёте на джетпаке (плавнее)
PLAYER_W = 40                       # ширина хитбокса игрока
PLAYER_H = 50                       # высота хитбокса игрока
PLAYER_START_Y = SCREEN_H - 130     # стартовая мировая y игрока (центр тела)
CAMERA_LINE = 0.45                  # доля высоты экрана, выше которой камера едет за игроком
DEATH_MARGIN = 80                   # насколько ниже экрана надо упасть, чтобы умереть

PIXELS_PER_METER = 10.0             # 10 px = 1 метр высоты

# Платформы
PLATFORM_W = 68
PLATFORM_H = 16
ROW_GAP_MIN = 60                    # минимальный вертикальный зазор между рядами
ROW_GAP_MAX_EASY = 100              # максимальный зазор в начале
ROW_GAP_MAX_HARD = 145              # максимальный зазор на большой высоте (< высоты прыжка ≈ 177 px)
SAFE_ROWS = 3                       # первые ряды без ломающихся платформ
SAFE_METERS = 300                   # до этой высоты монстров нет
MOVING_PLATFORM_SPEED = (60, 160)   # диапазон скорости синих платформ
CRUMBLE_TIME = 0.8                  # время от первого касания до обвала хрупкой платформы
CRUMBLE_STAGES = 3                  # стадии трещин
CRUMBLE_GRACE = 0.1                 # после CRUMBLE_TIME плашка ещё CRUMBLE_GRACE с «проваливается» и держит
                                    # последнее приземление (прыжок на месте возвращает игрока через ~0.86 с)
DEBRIS_COUNT = (6, 10)              # осколков на платформу
DEBRIS_POOL_SIZE = 240              # размер пула осколков
PARKOUR_STREAK = 3                  # ломающихся подряд для «ПАРКУР!»
PARKOUR_BONUS = 50
PARKOUR_RUN_CHANCE = (0.035, 0.07)  # шанс начать «паркур-забег» после ряда (лёгкая .. тяжёлая сложность)
PARKOUR_RUN_ROWS = (3, 4)           # рядов подряд в паркур-забеге (в каждом есть и твёрдая основная)
PARKOUR_RUN_GAP = (100, 125)        # шаг рядов в забеге: ступенька всегда достижима (< высоты прыжка ≈ 177 px),
                                    # а через ряд — уже нет, так что путь идёт по ломающимся подряд
PARKOUR_LANE_DX = 40                # сдвиг «дорожки» ломающихся по x от ряда к ряду (почти вертикально вверх)
PARKOUR_LANE_LIFT = (6, 12)         # ступенька забега чуть выше основной платформы своего ряда

# Джетпак
JETPACK_TIME = 3.0                  # обычный джетпак, сек
TURBO_JETPACK_TIME = 5.0            # турбо-джетпак, сек
JETPACK_SPEED = -900.0              # скорость подъёма на джетпаке
TURBO_JETPACK_SPEED = -1100.0
JETPACK_SPAWN_CHANCE = 0.04         # шанс появления джетпака на ряд
TURBO_JETPACK_SHARE = 0.15          # доля турбо среди джетпаков
JETPACK_EASE_TIME = 0.4             # последние секунды полёта: тяга плавно спадает (без резкой остановки)
JETPACK_END_SPEED = -250.0          # скорость к моменту, когда джетпак слетает (дальше — обычная гравитация)
JETPACK_END_GRACE = 0.4             # короткая неуязвимость после того, как джетпак слетел

# Бонусы
HELI_TIME = 4.0                     # шапка-вертолёт
HELI_SPEED = -320.0
MAGNET_TIME = 8.0
MAGNET_RADIUS = 220
STAR_TIME = 5.0
SHIELD_INVULN = 1.0                 # неуязвимость после потери щита
BONUS_SPAWN_CHANCE = 0.07           # шанс бонуса на ряд

# Монстры и комбо
MONSTER_CHANCE_MIN = 0.05           # шанс монстра на ряд на 300 м
MONSTER_CHANCE_MAX = 0.24           # шанс монстра на ряд на максимальной сложности
COMBO_WINDOW = 4.0                  # сек между убийствами, чтобы комбо продолжилось
COMBO_RAINBOW = 5                   # с этого комбо — радужный след
KILL_SCORE = 100                    # очки за монстра (умножаются на комбо)
UFO_TELEPORT_METERS = 500
DIFFICULTY_METERS = 3000.0          # высота, на которой сложность = 1.0

# Тряска экрана
SHAKE_BREAK = (6, 0.10)             # (интенсивность px, длительность сек) — разрушение
SHAKE_JETPACK = (3, 0.25)
SHAKE_HIT = (10, 0.30)

# Сохранения
SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saves.json")
SAVE_INTERVAL = 5.0                 # батч-сохранение раз в 5 сек
SAVE_RETRY_MAX = 60.0               # потолок паузы между повторами неудачной записи, сек
LOAD_RETRIES = 4                    # попыток прочитать занятый файл сохранения при старте
LOAD_RETRY_DELAY = 0.12             # пауза между этими попытками, сек
TOP_RECORDS = 5
DATE_FORMAT = "%d.%m.%Y"

# Реклама / попапы
AD_INGAME_INTERVAL = 120.0          # раз в ~2 мин
AD_INGAME_DURATION = 3.0
AD_CLOSE_DELAY = 1.0
AD_CLOSE_CAPS = 5
AD_POPUP_CAPS = 10
MENU_POPUP_INTERVAL = (20.0, 45.0)  # случайный интервал мем-попапов в меню
SPLASH_TIME = 1.5
PROMO_CAPS = 50
RECORD_CAPS = 50

# Слоу-мо скина «67×52»
SLOWMO_TIME = 2.0
SLOWMO_SCALE = 0.3
SLOWMO_COOLDOWN = 10.0

# ═══════════════════════════════════════════════════════════════════════════
#  ЦВЕТА
# ═══════════════════════════════════════════════════════════════════════════
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (130, 130, 130)
DARK_GRAY = (60, 60, 60)
LIGHT_GRAY = (200, 200, 200)
RED = (230, 60, 60)
ORANGE = (255, 150, 40)
YELLOW = (255, 220, 60)
GOLD = (255, 200, 40)
GREEN = (110, 200, 80)
DARK_GREEN = (50, 130, 50)
BLUE = (70, 140, 240)
DARK_BLUE = (30, 60, 140)
PURPLE = (170, 80, 220)
PINK = (255, 120, 200)
CYAN = (80, 220, 240)
BROWN = (150, 105, 60)
DARK_BROWN = (100, 65, 35)
SKY_DAY = (170, 215, 250)
SKY_SUNSET = (250, 150, 110)
SKY_NIGHT = (30, 35, 80)
SKY_SPACE = (5, 5, 20)
UI_BG = (25, 30, 50)
UI_PANEL = (40, 48, 80)
UI_BTN = (70, 110, 200)
UI_BTN_HOVER = (110, 150, 240)
UI_BTN_DANGER = (200, 70, 70)
UI_BTN_OK = (70, 180, 100)

# Цвета платформ
PLAT_NORMAL = (100, 200, 80)
PLAT_MOVING = (80, 150, 240)
PLAT_BREAKING = (235, 235, 235)
PLAT_CRUMBLING = (160, 110, 60)
PLAT_SPRING = (250, 220, 60)
PLAT_ROCKET = (230, 70, 60)

# Цвета редкости скинов
RARITY_ORDER = ["common", "rare", "epic", "legendary", "imba"]
RARITY_NAMES = {
    "common": "ОБЫЧНЫЙ", "rare": "РЕДКИЙ", "epic": "ЭПИК",
    "legendary": "ЛЕГЕНДАРНЫЙ", "imba": "ИМБА",
}
RARITY_COLORS = {
    "common": (220, 220, 220), "rare": (80, 150, 255), "epic": (190, 90, 255),
    "legendary": (255, 200, 40), "imba": (255, 90, 200),   # ИМБА рисуется радугой, это базовый цвет
}
RARITY_CHANCES = {"common": 60.0, "rare": 25.0, "epic": 12.0, "legendary": 2.5, "imba": 0.5}
RARITY_DUPE_CAPS = {"common": 10, "rare": 50, "epic": 200, "legendary": 1000, "imba": 5000}

# ═══════════════════════════════════════════════════════════════════════════
#  СКИНЫ (18 штук)
#  special — строка-подсказка для отрисовки особенностей; trail — тип следа;
#  sound — имя звука при прыжке (None = обычный "jump")
# ═══════════════════════════════════════════════════════════════════════════
SKINS = [
    {"id": "classic",  "name": "Классика",        "rarity": "common",    "body": (120, 200, 80),  "nose": (90, 160, 60),   "accent": (40, 100, 30),   "trail": None,        "special": None,      "sound": None},
    {"id": "potato",   "name": "Картошка",        "rarity": "common",    "body": (195, 155, 95),  "nose": (170, 130, 75),  "accent": (120, 85, 45),   "trail": None,        "special": "potato",  "sound": None},
    {"id": "banana",   "name": "Банан",           "rarity": "common",    "body": (250, 225, 70),  "nose": (230, 200, 50),  "accent": (150, 120, 20),  "trail": None,        "special": "banana",  "sound": None},
    {"id": "cucumber", "name": "Огурчик",         "rarity": "common",    "body": (70, 160, 70),   "nose": (60, 140, 60),   "accent": (30, 90, 30),    "trail": None,        "special": "cucumber", "sound": None},
    {"id": "whale",    "name": "Синий Кит",       "rarity": "rare",      "body": (70, 120, 220),  "nose": (60, 100, 200),  "accent": (30, 50, 140),   "trail": "bubbles",   "special": "whale",   "sound": None},
    {"id": "orange",   "name": "Апельсинка",      "rarity": "rare",      "body": (255, 150, 40),  "nose": (240, 130, 30),  "accent": (60, 140, 40),   "trail": None,        "special": "orange",  "sound": None},
    {"id": "alien",    "name": "Инопланетянин",   "rarity": "rare",      "body": (120, 240, 140), "nose": (90, 210, 110),  "accent": (40, 120, 60),   "trail": "green",     "special": "alien",   "sound": None},
    {"id": "fire",     "name": "Огненный",        "rarity": "epic",      "body": (255, 110, 40),  "nose": (255, 170, 60),  "accent": (200, 40, 20),   "trail": "fire",      "special": "fire",    "sound": None},
    {"id": "ice",      "name": "Ледяной",         "rarity": "epic",      "body": (150, 220, 255), "nose": (200, 240, 255), "accent": (60, 120, 200),  "trail": "ice",       "special": "ice",     "sound": None},
    {"id": "rainbow",  "name": "Радужный",        "rarity": "epic",      "body": None,            "nose": None,            "accent": (255, 255, 255), "trail": "rainbow",   "special": "rainbow", "sound": None},
    {"id": "skull",    "name": "Черепушка",       "rarity": "epic",      "body": (235, 235, 235), "nose": (200, 200, 200), "accent": (30, 30, 30),    "trail": "smoke",     "special": "skull",   "sound": None},
    {"id": "king",     "name": "Король",          "rarity": "legendary", "body": (200, 70, 200),  "nose": (230, 120, 220), "accent": (255, 200, 40),  "trail": "gold",      "special": "king",    "sound": None},
    {"id": "cyber",    "name": "Кибер-дудлер",    "rarity": "legendary", "body": (60, 60, 85),    "nose": (90, 90, 120),   "accent": (0, 255, 220),   "trail": "neon",      "special": "cyber",   "sound": None},
    {"id": "dragon",   "name": "Дракончик",       "rarity": "legendary", "body": (210, 50, 50),   "nose": (240, 90, 60),   "accent": (255, 200, 60),  "trail": "fire",      "special": "dragon",  "sound": None},
    {"id": "s67",      "name": "67",              "rarity": "imba",      "body": (35, 35, 40),    "nose": (60, 60, 70),    "accent": (255, 60, 60),   "trail": "digits67",  "special": "67",      "sound": "six_seven"},
    {"id": "s52",      "name": "52",              "rarity": "imba",      "body": (35, 35, 40),    "nose": (60, 60, 70),    "accent": (60, 120, 255),  "trail": "digits52",  "special": "52",      "sound": "five_two"},
    {"id": "s6752",    "name": "67×52",           "rarity": "imba",      "body": (20, 20, 25),    "nose": (50, 50, 60),    "accent": (255, 60, 200),  "trail": "digits6752", "special": "6752",   "sound": "six_seven"},
    {"id": "trash",    "name": "Мусорный Дроппер", "rarity": "imba",     "body": (115, 125, 115), "nose": (100, 110, 100), "accent": (60, 70, 60),    "trail": "caps",      "special": "trash",   "sound": "ding"},
]
SKINS_BY_ID = {s["id"]: s for s in SKINS}
IMBA_WEIGHTS = {"s67": 40, "s52": 40, "trash": 15, "s6752": 5}   # веса внутри редкости ИМБА
DEFAULT_SKIN = "classic"

# Кейсы: chances — таблица шансов редкости именно для этого кейса
CASES = [
    {"id": "common",  "name": "ОБЫЧНЫЙ",           "price": 100,  "tier": 1,
     "chances": {"common": 60.0, "rare": 25.0, "epic": 12.0, "legendary": 2.5, "imba": 0.5},
     "desc": "Классика жанра. Твой шанс на дроп!"},
    {"id": "rare",    "name": "РЕДКИЙ",             "price": 500,  "tier": 2,
     "chances": {"common": 40.0, "rare": 38.0, "epic": 17.0, "legendary": 4.0, "imba": 1.0},
     "desc": "Шансы получше. Жми, не тормози!"},
    {"id": "imba67",  "name": "ИМБА-КЕЙС «67»",     "price": 1000, "tier": 3,
     "chances": {"rare": 55.0, "epic": 33.0, "legendary": 10.0, "imba": 2.0},
     "desc": "Гарантия РЕДКИЙ+. Шесть-семь!"},
    {"id": "legend52", "name": "ЛЕГЕНДАРНЫЙ «52»",  "price": 2500, "tier": 4,
     "chances": {"epic": 70.0, "legendary": 25.0, "imba": 5.0},
     "desc": "Гарантия ЭПИК+. Пять-два!"},
]

# ═══════════════════════════════════════════════════════════════════════════
#  ТЕКСТЫ: РЕКЛАМА MUSORDROP (реальный слоган из TikTok — «Твой высокий шанс на большой дроп»)
# ═══════════════════════════════════════════════════════════════════════════
MUSOR_MAIN_SLOGAN = "MUSORDROP — ТВОЙ ШАНС НА БОЛЬШОЙ ДРОП!"
MUSOR_REAL_SLOGAN = "ТВОЙ ВЫСОКИЙ ШАНС НА БОЛЬШОЙ ДРОП!"
MUSOR_MENU_BANNERS = [
    "MUSORDROP — ТВОЙ ШАНС НА БОЛЬШОЙ ДРОП!",
    "MUSORDROP — ЖМИ, НЕ ТОРМОЗИ, ЛУЧШИЕ СКИНЫ УЖЕ ВПЕРЕДИ!",
    "КЕЙС ОТКРЫЛ — И СНОВА ВПЕРЕДИ!",
    "MUSORDROP — ТВОЙ ВЫСОКИЙ ШАНС НА БОЛЬШОЙ ДРОП!",
]
MUSOR_INGAME_BANNERS = [
    "MUSORDROP — ТВОЙ ШАНС НА БОЛЬШОЙ ДРОП!",
    "МУСОР ДРОП — БОЛЬШОЙ ДРОП! КЭШ ПОДНЯЛ!",
    "MUSORDROP — ТВОЙ ВЫСОКИЙ ШАНС НА БОЛЬШОЙ ДРОП!",
]
MUSOR_POPUPS = [
    "БОЛЬШОЙ ДРОП! — КЭШ ПОДНЯЛ!",
    "ТВОЙ ШАНС НА БОЛЬШОЙ ДРОП — УЖЕ ЗДЕСЬ!",
    "MUSORDROP — ОТКРЫВАЙ И ЗАБИРАЙ!",
    "ТВОЙ ВЫСОКИЙ ШАНС НА БОЛЬШОЙ ДРОП!",
]
PROMO_CODES = ["BIGDROP", "ТВОЙШАНС", "MUSORDROP"]

# Фразы-реакции (ключ → текст). Показываются крупным всплывающим текстом.
PHRASES = {
    "nice": "НЕПЛОХО!",
    "space": "КОСМОС!",
    "jetpack": "ДЖЕТПАК РУЛИТ!",
    "crack": "КРАК!",
    "parkour": "ПАРКУР!",
    "record": "НОВЫЙ РЕКОРД!",
    "legend": "ТЫ ЛЕГЕНДА!",
    "combo": "КОМБО!",
    "squish": "ПЫХ!",
    "ufo": "ТЕЛЕПОРТ +500 м!",
    "chirik": "ЧИРИК! ЩИТ!",
    "promo": "ПРОМОКОД АКТИВИРОВАН! +50 КРЫШЕК!",
    "spring": "ВЖУХ!",
    "rocket": "РАКЕТА!",
    "shield_lost": "ЩИТ СПАС!",
    "six_seven": "ШЕСТЬ-СЕМЬ!",
    "five_two": "ПЯТЬ-ДВА!",
    "ding": "ДЗЫНЬ!",
}
# Фразы по высоте: (метры, ключ или текст)
HEIGHT_PHRASES = [
    (100, "НЕПЛОХО!"),
    (300, "МОНСТРИКИ ПРОСНУЛИСЬ!"),
    (500, "ЗАКАТ!"),
    (1000, "НОЧЬ. ТИХО..."),
    (2000, "КОСМОС!"),
    (3000, "ТЫ ЛЕГЕНДА!"),
    (5000, "КОСМИЧЕСКАЯ КОТЛЕТА!"),
]

# Имена звуков, которые обязан уметь SoundManager (все генерируются кодом)
SOUND_NAMES = [
    "jump", "spring", "rocket", "crack", "break", "squish", "jetpack", "jetpack_end",
    "pickup", "coin", "hit", "death", "record", "combo", "ufo", "shoot", "click",
    "case_tick", "case_open", "case_epic", "case_imba", "six_seven", "five_two",
    "ding", "chirp", "ad", "promo", "shield", "star", "heli", "magnet", "caps",
]

# ═══════════════════════════════════════════════════════════════════════════
#  КОНСТАНТЫ ТОНКОЙ НАСТРОЙКИ ПО МОДУЛЯМ (тайминги, скорости, раскладка, палитры)
# ═══════════════════════════════════════════════════════════════════════════
# --- ШРИФТЫ И КЭШИ ОТРИСОВКИ (кэши — в классе RenderCache, ограничены по памяти) -------
FONT_CANDIDATES = ["arial", "segoeui", "dejavusans", "verdana", "freesansbold"]
FONT_CACHE_MAX = 256                # шрифтов (size, bold) в кэше
TEXT_CACHE_MAX = 600                # отрендеренных надписей
TEXT_CACHE_BYTES = 24 * 1024 * 1024     # и не больше ~24 МБ пикселей
GLOW_CACHE_MAX = 200                # готовых свечений
GLOW_CACHE_BYTES = 16 * 1024 * 1024     # и не больше ~16 МБ (большие анимированные свечения)
PARTICLE_SPRITE_CACHE_MAX = 400     # спрайтов частиц
PARTICLE_SPRITE_CACHE_BYTES = 4 * 1024 * 1024
TEXT_ANCHORS = ("center", "topleft", "topright", "midtop", "midbottom",
                "midleft", "midright", "bottomleft", "bottomright")
OUTLINE_OFFSETS = tuple((dx, dy) for dx in (-2, -1, 0, 1, 2) for dy in (-2, -1, 0, 1, 2)
                        if (dx, dy) != (0, 0))

# --- ПЛАТФОРМЫ И ОСКОЛКИ ---------------------------------------------------
PLATFORM_PRESS_TIME = 0.16          # длительность «проседания» плашки при приземлении, сек
SPRING_COMPRESS_TIME = 0.25         # время распрямления пружины, сек
SPRING_HEIGHT = 18                  # высота пружины в покое, px
ROCKET_BURN_TIME = 0.15             # ракета сжигает платформу за столько секунд (коротко: камера
                                    # улетает за ракетой ~2600 px/с, обвал должен успеть попасть в кадр)
DEBRIS_DRAG = 1.6                   # воздушное сопротивление осколков (доля скорости в секунду)

# --- ДУДЛЕР, ДЖЕТПАК, СЛЕД -------------------------------------------------
P3_FLAME_COLORS = ((225, 55, 30), (255, 160, 40), (255, 245, 140))   # пламя: снаружи внутрь
P3_TRAIL_LIFE = 0.55            # время жизни точки следа, сек
P3_TRAIL_MAX = 48               # максимум точек следа игрока
P3_TRAIL_INTERVAL = 0.03        # интервал появления точек следа, сек
P3_DIGIT_TRAIL_EVERY = 3        # цифры «67»/«52» — на каждой N-й точке следа (~0.09 с), чтобы не рябило
P3_DIGIT_TRAIL_LIFE = 0.8       # время жизни цифры следа, сек
P3_DIGIT_TRAIL_MAX = 14         # максимум цифр следа
P3_DIGIT_TRAIL_OFFSET = 30      # насколько позади центра тела (по ходу движения) появляется цифра, px
P3_WRAP_DRAW_MARGIN = 48        # у края экрана ближе этого — рисуем копию дудлера у противоположного края
P3_FIRE_INTERVAL = 1.0 / 60.0   # шаг испускания огня (джетпак, ракета): частицы по времени, а не по кадрам
P3_STAR_SPARK_INTERVAL = 1.0 / 15.0    # искры звезды-неуязвимости
P3_MAGNET_FX_INTERVAL = 0.1     # искорки магнита вокруг игрока
P3_JET_COLOR = (225, 55, 45)    # цвет обычного джетпака
P3_JET_TURBO_COLOR = (255, 200, 40)   # цвет турбо-джетпака (золотой)
P3_METAL = (150, 160, 170)      # металл (ведро, нозл)
P3_METAL_DARK = (95, 105, 115)
P3_HELI_CAP = (215, 60, 60)     # цвет кепки-вертолёта
P3_TRAIL_COLORS = {             # цвет точек следа по типу trail скина
    "green": (120, 255, 140),
    "ice": (185, 235, 255),
    "neon": (0, 255, 220),
    "gold": (255, 210, 60),
    "bubbles": (170, 215, 255),
}

# --- МОНСТРИКИ -------------------------------------------------------------
MONSTER_DEATH_TIME = 0.4                 # длительность анимации «пых» (сек)
MONSTER_BLINK_TIME = 0.12                # длительность моргания (сек)
OCTOPUS_RANGE = 350.0                    # дальность стрельбы осьминожка (px)
OCTOPUS_SHOOT_INTERVAL = (1.8, 2.6)      # пауза между выстрелами (сек)
OCTOPUS_RETRY_DELAY = (0.35, 0.6)        # повторная попытка, если осьминожек ещё за краем экрана (сек)
INK_SPEED = 270.0                        # скорость чернильной капли (px/с)
INK_GRAVITY = 300.0                      # слабая гравитация капли (px/с²)
INK_LIFE = 3.0                           # время жизни капли (сек)
CHIRP_INTERVAL = 3.0                     # как часто чирикает Чирик (сек)
UFO_FLYAWAY_TIME = 0.8                   # длительность эффекта улёта НЛО (сек)

# --- ЭКРАНЫ, КЕЙСЫ, РЕКЛАМА ------------------------------------------------
ROULETTE_CARD_W = 118           # ширина карточки в рулетке кейса
ROULETTE_CARD_H = 150           # высота карточки в рулетке
ROULETTE_PITCH = 130            # шаг между карточками
ROULETTE_CARDS = 40             # сколько карточек крутится
ROULETTE_TARGET = 33            # индекс карточки-результата (рулетка остановится на ней)
CASE_SHAKE_TIME = 1.0           # фаза «кейс трясётся», сек
CASE_ROLL_TIME = 3.5            # фаза «рулетка», сек
CASE_SETTLE_TIME = 0.45         # пауза после остановки рулетки перед вспышкой
CASE_REVEAL_INPUT_DELAY = 0.6   # сек после вспышки, когда кнопки результата ещё не реагируют
                                # (Enter «пропустить» + Enter не должен купить второй кейс)
RESET_CONFIRM_TIME = 3.0        # таймаут подтверждения сброса рекордов
MENU_BANNER_SWITCH = 4.0        # смена баннера в меню, сек
AD_FIRST_DELAY = 90.0           # первый баннер в игре — через 90 с
SKIN_GRID_COLS = 3
SKIN_GRID_ROWS = 6
SKIN_CARD_W = 130
SKIN_CARD_H = 85
UI_BG_TOP = (18, 22, 46)        # градиент фона экранов меню
UI_BG_BOTTOM = (48, 58, 100)
UI_BORDER = (95, 108, 160)
# Цвета коробок кейсов по тиру: (основной, тёмный)
CASE_BOX_COLORS = {
    1: ((120, 175, 95), (70, 115, 55)),
    2: ((85, 145, 240), (40, 80, 170)),
    3: ((195, 85, 245), (115, 40, 165)),
    4: ((255, 200, 45), (190, 130, 20)),
}
CONFETTI_COLORS = [RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, PINK, CYAN, WHITE]

# --- ФОН -------------------------------------------------------------------
BG_T_SUNSET = (350.0, 550.0)        # день -> закат
BG_T_NIGHT = (850.0, 1050.0)        # закат -> ночь
BG_T_SPACE = (1800.0, 2100.0)       # ночь -> космос

# Цвета неба для четырёх зон: верх экрана темнее/насыщеннее, низ светлее.
# Средний тон каждой зоны соответствует SKY_DAY / SKY_SUNSET / SKY_NIGHT / SKY_SPACE из part0.
BG_SKY_TOP = {
    "day": (105, 170, 245),
    "sunset": (125, 70, 150),
    "night": (12, 14, 46),
    "space": (2, 2, 10),
}
BG_SKY_BOTTOM = {
    "day": (205, 235, 255),
    "sunset": (255, 195, 120),
    "night": (52, 62, 122),
    "space": SKY_SPACE,
}

# Параллакс слоёв фона (доля смещения камеры)
BG_PARALLAX_CLOUDS = 0.30
BG_PARALLAX_STARS = 0.30
BG_PARALLAX_STARS_FAR = 0.20
BG_PARALLAX_PLANETS = 0.15

# Цвета звёзд (белые, тёплые, холодные)
BG_STAR_COLORS = [(255, 255, 255), (255, 255, 255), (255, 240, 200), (200, 220, 255)]

# Палитра планет: (основной цвет, тёмные полосы, есть ли кольцо)
BG_PLANETS = [
    ((225, 135, 85), (180, 95, 60), True),
    ((120, 170, 230), (80, 120, 190), False),
    ((190, 125, 220), (140, 80, 180), False),
]

# --- ИГРА И HUD ------------------------------------------------------------
HUD_PANEL_ALPHA = 110                # прозрачность подложек HUD
GAME_OVER_TIME = 1.6                 # длительность улёта дудлера перед экраном Game Over
GAME_OVER_FLY_SPEED = -500.0         # скорость улёта вверх
GAME_OVER_SPIN_SPEED = 7.0           # рад/с — вращение дудлера при game over
CAMERA_LERP_K = 12.0                 # коэффициент сглаживания камеры
CAMERA_HARD_MARGIN = 70              # игрок никогда не выше этой линии от верха экрана
TELEPORT_FLASH_TIME = 0.6            # длительность белой вспышки телепорта
TELEPORT_GRACE = 0.8                 # неуязвимость после телепорта сверх времени вспышки, с
TELEPORT_SAFE_ZONE = 420             # px над посадочной площадкой, где после телепорта нет врагов
RECORD_FLASH_TIME = 2.0              # длительность мерцания «НОВЫЙ РЕКОРД!»
RECORD_FLASH_Y = SCREEN_H * 0.44     # центр надписи «НОВЫЙ РЕКОРД!» (кубок — на 60 px выше)
RECORD_FLASH_PHRASE_GAP = 70         # пока идёт вспышка, крупные фразы — ниже неё (не наезжают)
BONUS_ICON_KINDS = ("shield", "heli", "magnet", "star")
WORLD_STATES = ("play", "pause", "gameover")   # состояния, в которых на экране виден мир
COMBO_HUD_POS = (SCREEN_W - 93, 86)  # центр индикатора комбо: под панелью крышек (x 302..472)
COMBO_HUD_MAX_W = 164                # максимальная ширина надписи комбо, px


# ═══════════════════════════════════════════════════════════════════════════
# ═══ ЧАСТЬ 1: БАЗОВЫЕ СЕРВИСЫ (хелперы, звук, сохранения, частицы, UI) ═══
# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
#  ЧАСТЬ 1: БАЗОВЫЕ СЕРВИСЫ
#  Хелперы (математика, цвета, шрифты, текст, примитивы), SoundManager
#  (процедурный звук), SaveManager (надёжные сохранения), частицы,
#  всплывающий текст, кнопки и клавиатурная навигация.
# ═══════════════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────────────
#  КЭШИ ОТРИСОВКИ
#  Никаких изменяемых глобальных переменных: все кэши принадлежат классу
#  RenderCache и ограничены и по числу записей, и по объёму памяти (LRU).
# ───────────────────────────────────────────────────────────────────────────
class SurfaceCache:
    """Ограниченный кэш готовых картинок (Surface) или шрифтов.
    Давно не использованные записи вытесняются по одной (LRU), когда превышен
    лимит числа записей или объёма пикселей — без резких «очисток всего сразу»."""

    def __init__(self, max_items, max_bytes=0):
        self.max_items = max(1, int(max_items))
        self.max_bytes = max(0, int(max_bytes))     # 0 — объём не ограничиваем (шрифты)
        self.items = {}                             # dict хранит порядок: первый — самый старый
        self.bytes = 0

    def __len__(self):
        return len(self.items)

    def __contains__(self, key):
        return key in self.items

    @staticmethod
    def _cost(value):
        """Примерный объём Surface в байтах (для шрифтов и прочего — 0)."""
        try:
            w, h = value.get_size()
            return int(w) * int(h) * 4
        except Exception:
            return 0

    def get(self, key):
        """Взять значение и отметить его как свежее (или None)."""
        value = self.items.pop(key, None)
        if value is not None:
            self.items[key] = value
        return value

    def put(self, key, value):
        """Положить значение; при переполнении вытеснить самые старые записи."""
        old = self.items.pop(key, None)
        if old is not None:
            self.bytes -= self._cost(old)
        self.items[key] = value
        self.bytes += self._cost(value)
        while len(self.items) > 1 and (len(self.items) > self.max_items
                                       or (self.max_bytes and self.bytes > self.max_bytes)):
            oldest = next(iter(self.items))
            self.bytes -= self._cost(self.items.pop(oldest))
        self.bytes = max(0, self.bytes)

    def clear(self):
        self.items.clear()
        self.bytes = 0


class RenderCache:
    """Владелец всех кэшей отрисовки: шрифты, отрендеренные надписи, свечения, спрайты частиц."""

    fonts = SurfaceCache(FONT_CACHE_MAX)                                   # (size, bold) -> Font
    text = SurfaceCache(TEXT_CACHE_MAX, TEXT_CACHE_BYTES)                   # (text, size, ...) -> Surface
    glow = SurfaceCache(GLOW_CACHE_MAX, GLOW_CACHE_BYTES)                   # (radius, color, alpha) -> Surface
    particles = SurfaceCache(PARTICLE_SPRITE_CACHE_MAX, PARTICLE_SPRITE_CACHE_BYTES)

    @classmethod
    def clear_all(cls):
        """Сбросить все кэши (например, при нехватке памяти)."""
        for cache in (cls.fonts, cls.text, cls.glow, cls.particles):
            cache.clear()


# ───────────────────────────────────────────────────────────────────────────
#  МАТЕМАТИКА И ЦВЕТА
# ───────────────────────────────────────────────────────────────────────────
def clamp(v, lo, hi):
    """Ограничить значение отрезком [lo, hi] (порядок границ не важен)."""
    if lo > hi:
        lo, hi = hi, lo
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def lerp(a, b, t):
    """Линейная интерполяция между a и b по параметру t."""
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    """Плавный переход между двумя цветами (t ограничивается [0, 1])."""
    t = clamp(t, 0.0, 1.0)
    return (int(c1[0] + (c2[0] - c1[0]) * t + 0.5),
            int(c1[1] + (c2[1] - c1[1]) * t + 0.5),
            int(c1[2] + (c2[2] - c1[2]) * t + 0.5))


def hsv_color(h, s=1.0, v=1.0):
    """HSV -> RGB. h в [0, 1) (по кругу), s и v в [0, 1]."""
    h = h % 1.0
    s = clamp(s, 0.0, 1.0)
    v = clamp(v, 0.0, 1.0)
    i = int(h * 6.0)
    f = h * 6.0 - i
    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)
    i %= 6
    if i == 0:
        r, g, b = v, t, p
    elif i == 1:
        r, g, b = q, v, p
    elif i == 2:
        r, g, b = p, v, t
    elif i == 3:
        r, g, b = p, q, v
    elif i == 4:
        r, g, b = t, p, v
    else:
        r, g, b = v, p, q
    return (int(r * 255 + 0.5), int(g * 255 + 0.5), int(b * 255 + 0.5))


def rainbow(t):
    """Радужный цвет по времени/фазе t (любое число, берётся дробная часть)."""
    return hsv_color(t % 1.0)


def shade_color(color, factor):
    """Затемнить (factor < 1) или осветлить (factor > 1) цвет."""
    return (int(clamp(color[0] * factor, 0, 255)),
            int(clamp(color[1] * factor, 0, 255)),
            int(clamp(color[2] * factor, 0, 255)))


# ───────────────────────────────────────────────────────────────────────────
#  ШРИФТЫ И ТЕКСТ
# ───────────────────────────────────────────────────────────────────────────
def _font_has_cyrillic(font):
    """Проверить, что шрифт умеет рисовать кириллицу (по метрикам глифов)."""
    try:
        metrics = font.metrics("Жя")
        return bool(metrics) and all(m is not None for m in metrics)
    except Exception:
        return True   # если метрики недоступны — доверяем шрифту


def get_font(size, bold=False):
    """Шрифт нужного размера из кэша. Ищем системный шрифт с кириллицей,
    иначе — встроенный шрифт pygame (он тоже содержит кириллицу)."""
    size = max(6, int(size))
    bold = bool(bold)
    key = (size, bold)
    font = RenderCache.fonts.get(key)
    if font is not None:
        return font
    try:
        if not pygame.font.get_init():
            pygame.font.init()
    except Exception:
        pass
    font = None
    for name in FONT_CANDIDATES:
        try:
            path = pygame.font.match_font(name, bold=bold)
            fake_bold = False
            if not path and bold:
                path = pygame.font.match_font(name)
                fake_bold = True
            if not path:
                continue
            candidate = pygame.font.Font(path, size)
            if fake_bold:
                candidate.set_bold(True)
            if _font_has_cyrillic(candidate):
                font = candidate
                break
        except Exception:
            continue
    if font is None:
        try:
            font = pygame.font.Font(None, size)
            if bold:
                font.set_bold(True)
        except Exception:
            font = pygame.font.SysFont(None, size, bold=bold)
    RenderCache.fonts.put(key, font)
    return font


def _render_text_surface(text, size, color, bold, outline, shadow):
    """Отрендерить текст (с обводкой/тенью) в Surface с кэшированием."""
    key = (text, size, color, bold, outline, shadow)
    surf = RenderCache.text.get(key)
    if surf is not None:
        return surf
    font = get_font(size, bold)
    base = font.render(text, True, color)
    pad = 2 if outline else 0
    sh = 2 if shadow else 0
    w = base.get_width() + pad * 2 + sh
    h = base.get_height() + pad * 2 + sh
    out = pygame.Surface((max(1, w), max(1, h)), pygame.SRCALPHA)
    if shadow:
        shadow_surf = font.render(text, True, shadow)
        out.blit(shadow_surf, (pad + sh, pad + sh))
    if outline:
        outline_surf = font.render(text, True, outline)
        for dx, dy in OUTLINE_OFFSETS:
            out.blit(outline_surf, (pad + dx, pad + dy))
    out.blit(base, (pad, pad))
    RenderCache.text.put(key, out)
    return out


def draw_text(surf, text, x, y, size=24, color=WHITE, anchor="center", bold=False,
              shadow=None, outline=None, alpha=255):
    """Нарисовать текст с привязкой (anchor), тенью, обводкой и прозрачностью.
    Возвращает Rect, в который текст был нарисован."""
    text = "" if text is None else str(text)
    if text == "":
        return pygame.Rect(int(x), int(y), 0, 0)
    color = tuple(color[:3])
    shadow = tuple(shadow[:3]) if shadow else None
    outline = tuple(outline[:3]) if outline else None
    rendered = _render_text_surface(text, int(size), color, bool(bold), outline, shadow)
    rect = rendered.get_rect()
    if anchor not in TEXT_ANCHORS:
        anchor = "center"
    setattr(rect, anchor, (int(x), int(y)))
    alpha = int(clamp(alpha, 0, 255))
    if alpha <= 0:
        return rect
    if alpha < 255:
        tmp = rendered.copy()
        tmp.set_alpha(alpha)
        surf.blit(tmp, rect)
    else:
        surf.blit(rendered, rect)
    return rect


# ───────────────────────────────────────────────────────────────────────────
#  ПРИМИТИВЫ
# ───────────────────────────────────────────────────────────────────────────
def draw_rounded_rect(surf, rect, color, radius=8, width=0, border_color=None):
    """Закруглённый прямоугольник. width=0 — заливка (+ рамка border_color 2px),
    width>0 — только контур цветом color. Цвет с альфой (r,g,b,a) поддерживается."""
    rect = pygame.Rect(rect)
    if rect.w <= 0 or rect.h <= 0:
        return
    radius = int(max(0, min(radius, rect.w // 2, rect.h // 2)))
    if len(color) == 4 and color[3] < 255:
        tmp = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        pygame.draw.rect(tmp, color, tmp.get_rect(), width, border_radius=radius)
        if width == 0 and border_color:
            pygame.draw.rect(tmp, border_color, tmp.get_rect(), 2, border_radius=radius)
        surf.blit(tmp, rect.topleft)
        return
    pygame.draw.rect(surf, color, rect, width, border_radius=radius)
    if width == 0 and border_color:
        pygame.draw.rect(surf, border_color, rect, 2, border_radius=radius)


def _quantize_glow(radius, color, alpha):
    """Квантование ключа свечения: анимированные (растущие, мигающие, радужные) свечения
    попадают в небольшое число корзин, а не создают новую большую Surface каждый кадр."""
    r = int(radius)
    if r > 128:
        r = int(round(r / 8.0)) * 8
    elif r > 32:
        r = int(round(r / 4.0)) * 4
    col = tuple(min(255, int(round(int(c) / 16.0)) * 16) for c in color[:3])
    a = int(clamp(alpha, 0, 255))
    if a > 0:
        a = max(8, min(255, int(round(a / 8.0)) * 8))
    return r, col, a


def draw_glow(surf, cx, cy, radius, color, alpha=90):
    """Мягкое свечение: несколько концентрических полупрозрачных кругов.
    Готовые свечения кэшируются по квантованному (радиус, цвет, альфа), кэш ограничен по памяти."""
    if int(radius) <= 0:
        return
    r, color, alpha = _quantize_glow(radius, color, alpha)
    if r <= 0 or alpha <= 0:
        return
    key = (r, color, alpha)
    glow = RenderCache.glow.get(key)
    if glow is None:
        size = r * 2 + 2
        glow = pygame.Surface((size, size), pygame.SRCALPHA)
        layers = 5
        # подбираем альфу слоя так, чтобы в центре получилось ~alpha
        a_total = alpha / 255.0
        a_layer = 1.0 - (1.0 - a_total) ** (1.0 / layers)
        layer_alpha = int(clamp(a_layer * 255, 1, 255))
        for i in range(layers):
            rr = max(1, int(r * (1.0 - i / layers)))
            pygame.draw.circle(glow, color + (layer_alpha,), (r + 1, r + 1), rr)
        RenderCache.glow.put(key, glow)
    surf.blit(glow, (int(cx) - r - 1, int(cy) - r - 1))


def draw_eyes(surf, cx, cy, look_x, look_y, spacing=10, eye_r=6, pupil_r=3,
              color=WHITE, pupil=BLACK):
    """Два глаза в (cx - spacing, cy) и (cx + spacing, cy) — spacing это смещение
    каждого глаза от центра; зрачки смотрят в точку (look_x, look_y) — в тех же
    координатах, что и cx, cy."""
    eye_r = max(1, int(eye_r))
    pupil_r = max(1, min(int(pupil_r), eye_r))
    dx = look_x - cx
    dy = look_y - cy
    dist = math.hypot(dx, dy)
    max_off = max(0, eye_r - pupil_r - 1)
    if dist > 0.001 and max_off > 0:
        k = max_off * min(1.0, dist / 60.0) / dist
        ox, oy = dx * k, dy * k
    else:
        ox, oy = 0.0, 0.0
    rim = shade_color(color, 0.45)
    half = float(spacing)
    for ex in (cx - half, cx + half):
        ex_i, cy_i = int(ex), int(cy)
        pygame.draw.circle(surf, rim, (ex_i, cy_i), eye_r + 1)
        pygame.draw.circle(surf, color, (ex_i, cy_i), eye_r)
        px, py = int(ex + ox), int(cy + oy)
        pygame.draw.circle(surf, pupil, (px, py), pupil_r)
        hl = max(1, pupil_r // 3)
        pygame.draw.circle(surf, WHITE, (px - pupil_r // 3, py - pupil_r // 3), hl)


def draw_cap_icon(surf, cx, cy, r=9):
    """Иконка «мусорной крышки»: серый кружок с ободком, углублением и бликом."""
    r = max(3, int(r))
    cx, cy = int(cx), int(cy)
    pygame.draw.circle(surf, (70, 75, 80), (cx, cy + 1), r + 1)          # тень/контур
    pygame.draw.circle(surf, (150, 158, 165), (cx, cy), r)               # крышка
    pygame.draw.circle(surf, (110, 118, 125), (cx, cy), r, max(1, r // 4))  # ободок
    inner = max(1, int(r * 0.55))
    pygame.draw.circle(surf, (125, 133, 140), (cx, cy), inner)           # углубление
    handle_w = max(2, int(r * 0.8))
    handle_h = max(2, int(r * 0.28))
    handle = pygame.Rect(cx - handle_w // 2, cy - handle_h // 2, handle_w, handle_h)
    pygame.draw.rect(surf, (85, 92, 100), handle, border_radius=handle_h // 2)  # ручка
    hl_r = max(1, int(r * 0.22))
    pygame.draw.circle(surf, (215, 222, 228), (cx - int(r * 0.45), cy - int(r * 0.45)), hl_r)  # блик


def format_time(seconds):
    """Секунды -> строка: '1ч 23м 45с' / '5м 03с' / '42с'."""
    try:
        total = max(0, int(seconds))
    except (TypeError, ValueError):
        total = 0
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    if h > 0:
        return f"{h}ч {m:02d}м {s:02d}с"
    if m > 0:
        return f"{m}м {s:02d}с"
    return f"{s}с"


def today_str():
    """Сегодняшняя дата в формате DATE_FORMAT (ДД.ММ.ГГГГ)."""
    return datetime.date.today().strftime(DATE_FORMAT)


def weighted_choice(weights):
    """Случайный ключ словаря по весам {ключ: вес}. Пустой словарь -> None."""
    if not weights:
        return None
    items = []
    for key, w in weights.items():
        try:
            w = float(w)
        except (TypeError, ValueError):
            continue
        if w > 0:
            items.append((key, w))
    if not items:
        return random.choice(list(weights.keys()))
    total = sum(w for _, w in items)
    r = random.uniform(0, total)
    acc = 0.0
    for key, w in items:
        acc += w
        if r <= acc:
            return key
    return items[-1][0]


# ───────────────────────────────────────────────────────────────────────────
#  ЗВУК
# ───────────────────────────────────────────────────────────────────────────
class SoundManager:
    """Процедурные звуки: все имена из SOUND_NAMES синтезируются при старте
    (синус/квадрат/шум/чирпы с огибающими) в array('h'). Если mixer
    недоступен — все методы молча ничего не делают."""

    MASTER = 0.6   # общая громкость

    def __init__(self, enabled=True):
        self.enabled = bool(enabled)
        self.ok = False
        self.sounds = {}
        self.rate = 22050
        self.channels = 1
        try:
            init = pygame.mixer.get_init()
            if init is None or abs(int(init[1])) != 16:
                if init is not None:
                    pygame.mixer.quit()
                pygame.mixer.init(22050, -16, 1, 512)
                init = pygame.mixer.get_init()
            if init:
                self.rate = int(init[0])
                self.channels = max(1, int(init[2]))
                pygame.mixer.set_num_channels(24)
                self.ok = True
        except Exception as e:
            print("[Sound] mixer недоступен, игра без звука:", e)
            self.ok = False
        if self.ok:
            self._build_all()

    # --- публичный API ---
    def play(self, name, volume=1.0):
        """Проиграть звук по имени. Неизвестное имя — молча игнорируем."""
        if not self.ok or not self.enabled:
            return
        snd = self.sounds.get(name)
        if snd is None:
            return
        try:
            snd.set_volume(clamp(float(volume), 0.0, 1.0) * self.MASTER)
            snd.play()
        except Exception:
            pass

    def set_enabled(self, flag):
        """Включить/выключить звук."""
        self.enabled = bool(flag)
        if not self.enabled and self.ok:
            try:
                pygame.mixer.stop()
            except Exception:
                pass

    def toggle(self):
        """Переключить звук, вернуть новое состояние."""
        self.set_enabled(not self.enabled)
        return self.enabled

    # --- сборка всех звуков ---
    def _build_all(self):
        """Собрать все звуки; сбой одного звука не ломает остальные."""
        builders = {
            "jump": lambda: self._tone(0.13, 320, 640, "sine", 0.45, release=0.09),
            "spring": lambda: self._tone(0.32, 220, 980, "tri", 0.5, release=0.15,
                                         vib_rate=30, vib_depth=0.04),
            "rocket": lambda: self._mix((0, self._noise(0.55, 0.45, decay=3.0, lowpass=0.15)),
                                        (0, self._tone(0.55, 90, 420, "saw", 0.3, release=0.25))),
            "crack": lambda: self._mix((0, self._noise(0.14, 0.7, decay=22.0, lowpass=0.6)),
                                       (0, self._clicks(0.14, 5, 0.6))),
            "break": lambda: self._mix((0, self._noise(0.26, 0.6, decay=12.0, lowpass=0.4)),
                                       (0, self._clicks(0.26, 8, 0.5)),
                                       (0, self._tone(0.2, 140, 60, "sine", 0.4, release=0.15))),
            "squish": lambda: self._mix((0, self._noise(0.2, 0.5, decay=14.0, lowpass=0.25)),
                                        (0, self._tone(0.2, 420, 90, "sine", 0.45, release=0.12))),
            "jetpack": lambda: self._mix((0, self._tone(0.5, 180, 1250, "square", 0.22, release=0.2,
                                                        vib_rate=40, vib_depth=0.03)),
                                         (0, self._noise(0.5, 0.25, decay=2.5, lowpass=0.3))),
            "jetpack_end": lambda: self._tone(0.35, 900, 160, "square", 0.22, release=0.2),
            "pickup": lambda: self._seq([523, 659], 0.09, "sine", 0.4, tail=0.1),
            "coin": lambda: self._seq([988, 1319], 0.07, "sine", 0.4, tail=0.15, harmonics=[(2, 0.3)]),
            "hit": lambda: self._mix((0, self._tone(0.28, 160, 70, "square", 0.35, release=0.2)),
                                     (0, self._noise(0.2, 0.4, decay=15.0, lowpass=0.3))),
            "death": lambda: self._tone(0.7, 620, 90, "square", 0.3, release=0.3,
                                        vib_rate=12, vib_depth=0.06),
            "record": lambda: self._seq([523, 659, 784, 1047, 1319], 0.11, "tri", 0.45,
                                        tail=0.45, harmonics=[(2, 0.25)]),
            "combo": lambda: self._seq([660, 880, 1100], 0.06, "sine", 0.4, tail=0.12),
            "ufo": lambda: self._tone(0.7, 500, 500, "sine", 0.35, release=0.2,
                                      vib_rate=6, vib_depth=0.35, harmonics=[(2, 0.3)]),
            "shoot": lambda: self._tone(0.13, 950, 280, "square", 0.25, release=0.08),
            "click": lambda: self._tone(0.045, 1100, 900, "sine", 0.4, release=0.035),
            "case_tick": lambda: self._tone(0.03, 1600, 1400, "square", 0.25, release=0.025),
            "case_open": lambda: self._seq([440, 554, 659], 0.1, "tri", 0.4, tail=0.25),
            "case_epic": lambda: self._mix((0, self._seq([523, 659, 784, 1047], 0.1, "tri", 0.4,
                                                         tail=0.5, harmonics=[(2, 0.3)])),
                                           (0.4, self._tone(0.5, 2093, 2093, "sine", 0.15, release=0.4,
                                                            vib_rate=8, vib_depth=0.01))),
            "case_imba": lambda: self._mix((0, self._seq([523, 659, 784, 1047, 1319, 1568], 0.09, "square",
                                                         0.3, tail=0.6, harmonics=[(2, 0.2)])),
                                           (0.5, self._noise(0.7, 0.6, decay=4.0, lowpass=0.2)),
                                           (0.5, self._tone(0.6, 120, 40, "sine", 0.5, release=0.5))),
            "six_seven": lambda: self._speech([(0.18, 250, 200), (0.24, 200, 150)]),
            "five_two": lambda: self._speech([(0.16, 210, 260), (0.26, 240, 140)]),
            "ding": lambda: self._tone(0.45, 1760, 1760, "sine", 0.4, release=0.42, decay=6.0,
                                       harmonics=[(2.76, 0.35), (5.4, 0.12)]),
            "chirp": lambda: self._mix((0, self._tone(0.06, 2200, 3200, "sine", 0.3, release=0.03)),
                                       (0.09, self._tone(0.07, 2600, 3400, "sine", 0.3, release=0.04))),
            "ad": lambda: self._seq([392, 523], 0.12, "tri", 0.4, tail=0.25),
            "promo": lambda: self._mix((0, self._seq([523, 659, 784], 0.08, "sine", 0.4, tail=0.1)),
                                       (0.24, self._tone(0.4, 1568, 1568, "sine", 0.35, release=0.38,
                                                         decay=6.0, harmonics=[(2.5, 0.3)]))),
            "shield": lambda: self._mix((0, self._tone(0.35, 280, 560, "sine", 0.4, release=0.2,
                                                       harmonics=[(2, 0.3)])),
                                        (0, self._noise(0.3, 0.15, decay=8.0, lowpass=0.1))),
            "star": lambda: self._seq([1047, 1319, 1568, 2093], 0.05, "sine", 0.35, tail=0.3,
                                      harmonics=[(2, 0.3)]),
            "heli": lambda: self._chopper(0.45),
            "magnet": lambda: self._tone(0.35, 110, 260, "saw", 0.3, release=0.15, harmonics=[(2, 0.4)]),
            "caps": lambda: self._tone(0.22, 2500, 2400, "sine", 0.35, release=0.2, decay=14.0,
                                       harmonics=[(1.5, 0.4), (2.2, 0.2)]),
        }
        for name in SOUND_NAMES:
            builder = builders.get(name)
            if builder is None:
                builder = lambda: self._tone(0.1, 600, 600, "sine", 0.3)   # запасной «бип»
            try:
                self.sounds[name] = self._to_sound(builder())
            except Exception as e:
                print(f"[Sound] не удалось собрать звук '{name}':", e)

    # --- синтез (все функции возвращают список float в [-1, 1]) ---
    def _to_sound(self, samples):
        """Список float -> pygame.mixer.Sound (16 бит, каналы как у mixer)."""
        ch = self.channels
        buf = array("h")
        if ch == 1:
            buf.extend(int(clamp(s, -1.0, 1.0) * 32000) for s in samples)
        else:
            for s in samples:
                v = int(clamp(s, -1.0, 1.0) * 32000)
                buf.extend([v] * ch)
        if len(buf) == 0:
            buf.extend([0] * ch)
        return pygame.mixer.Sound(buffer=buf)

    def _tone(self, dur, f0, f1=None, wave="sine", vol=0.5, attack=0.005, release=None,
              vib_rate=0.0, vib_depth=0.0, harmonics=None, decay=0.0):
        """Тон с линейным свипом частоты f0 -> f1, вибрато, обертонами и огибающей."""
        rate = self.rate
        n = max(1, int(dur * rate))
        if f1 is None:
            f1 = f0
        if release is None:
            release = dur * 0.5
        att_n = max(1, int(attack * rate))
        rel_n = max(1, int(release * rate))
        two_pi = math.tau
        out = [0.0] * n
        phase = 0.0
        inv_n = 1.0 / n
        for i in range(n):
            t = i / rate
            f = f0 + (f1 - f0) * (i * inv_n)
            if vib_depth:
                f *= 1.0 + vib_depth * math.sin(two_pi * vib_rate * t)
            phase += two_pi * f / rate
            if wave == "sine":
                s = math.sin(phase)
            elif wave == "square":
                s = 0.6 if math.sin(phase) >= 0.0 else -0.6
            elif wave == "saw":
                s = (2.0 * ((phase / two_pi) % 1.0) - 1.0) * 0.7
            else:   # "tri"
                s = (2.0 * abs(2.0 * ((phase / two_pi) % 1.0) - 1.0) - 1.0) * 0.9
            if harmonics:
                for mult, amp in harmonics:
                    s += amp * math.sin(phase * mult)
            env = 1.0
            if i < att_n:
                env = i / att_n
            rem = n - i
            if rem < rel_n:
                env *= rem / rel_n
            if decay:
                env *= math.exp(-decay * t)
            out[i] = s * vol * env
        return out

    def _noise(self, dur, vol=0.5, decay=8.0, lowpass=0.0):
        """Шум с экспоненциальным затуханием; lowpass в (0, 1] — сглаживание
        (меньше = глуше). 0 — белый шум."""
        rate = self.rate
        n = max(1, int(dur * rate))
        out = [0.0] * n
        last = 0.0
        gain = 1.0
        if lowpass and 0.0 < lowpass < 1.0:
            gain = min(3.0, 1.0 / math.sqrt(lowpass))
        for i in range(n):
            white = random.uniform(-1.0, 1.0)
            if lowpass and 0.0 < lowpass < 1.0:
                last += lowpass * (white - last)
                s = last * gain
            else:
                s = white
            out[i] = s * vol * math.exp(-decay * (i / rate))
        return out

    def _clicks(self, dur, count, vol=0.5):
        """Серия коротких щелчков (для треска ломающихся платформ)."""
        rate = self.rate
        n = max(1, int(dur * rate))
        out = [0.0] * n
        burst = max(8, int(rate * 0.003))
        for _ in range(max(0, int(count))):
            start = random.randint(0, max(0, n - burst - 1))
            for j in range(burst):
                idx = start + j
                if idx >= n:
                    break
                out[idx] += random.uniform(-1.0, 1.0) * vol * (1.0 - j / burst)
        return out

    def _mix(self, *tracks):
        """Смешать дорожки: каждая — (смещение_сек, список сэмплов)."""
        rate = self.rate
        length = 0
        prepared = []
        for offset, samples in tracks:
            off = max(0, int(offset * rate))
            prepared.append((off, samples))
            length = max(length, off + len(samples))
        out = [0.0] * max(1, length)
        for off, samples in prepared:
            for i, s in enumerate(samples):
                out[off + i] += s
        return out

    def _concat(self, *parts):
        """Склеить дорожки последовательно."""
        out = []
        for p in parts:
            out.extend(p)
        return out if out else [0.0]

    def _seq(self, freqs, note_dur, wave="sine", vol=0.4, tail=0.0, harmonics=None):
        """Последовательность нот (арпеджио); последняя нота длиннее на tail."""
        parts = []
        last_i = len(freqs) - 1
        for i, f in enumerate(freqs):
            dur = note_dur + (tail if i == last_i else 0.0)
            rel = dur * 0.6 if i == last_i else note_dur * 0.35
            parts.append(self._tone(dur, f, f, wave, vol, attack=0.004, release=rel,
                                    harmonics=harmonics))
        return self._concat(*parts)

    def _speech(self, syllables):
        """«Речевая» фраза: слоги = (длительность, f0, f1) — гласный тон с
        обертонами (как формантами) и вибрато, перед каждым — шипящий согласный."""
        rate = self.rate
        parts = []
        for dur, f0, f1 in syllables:
            onset = self._noise(0.05, 0.35, decay=40.0, lowpass=0.5)
            vowel = self._tone(dur, f0, f1, "sine", 0.35, attack=0.02, release=dur * 0.4,
                               vib_rate=5.5, vib_depth=0.025,
                               harmonics=[(2, 0.5), (3, 0.35), (4, 0.2), (5, 0.1)])
            parts.append(self._mix((0, onset), (0.02, vowel)))
            parts.append([0.0] * int(0.06 * rate))
        return self._concat(*parts)

    def _chopper(self, dur):
        """Вертолёт: глухой шум с амплитудной модуляцией ~13 Гц + низкий гул."""
        rate = self.rate
        noise = self._noise(dur, 0.5, decay=1.5, lowpass=0.12)
        for i in range(len(noise)):
            t = i / rate
            mod = 0.25 + 0.75 * max(0.0, math.sin(math.tau * 13.0 * t)) ** 2
            noise[i] *= mod
        low = self._tone(dur, 70, 70, "sine", 0.25, release=0.15)
        return self._mix((0, noise), (0, low))


# ───────────────────────────────────────────────────────────────────────────
#  СОХРАНЕНИЯ
# ───────────────────────────────────────────────────────────────────────────
def _is_num(v):
    """Число (не bool, конечное)."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return False
    return math.isfinite(v)


class SaveManager:
    """Надёжные сохранения в saves.json: атомарная запись через временный файл,
    восстановление после битого JSON (файл переименовывается в .broken, .broken1, ... —
    старые копии не затираются), BOM допускается, миграция отсутствующих ключей,
    проверка типов, батч-сохранение по таймеру с откатом при ошибках записи.
    Файл есть, но не читается (занят, нет прав) — это НЕ порча: работаем с defaults
    в памяти в режиме read_only и настоящий файл не перезаписываем."""

    VERSION = 2
    SUM_KEYS = ("games_played", "total_time", "monsters_killed", "platforms_broken",
                "jetpacks_collected", "cases_opened", "caps_earned_total")
    MAX_KEYS = ("max_combo", "max_height")

    def __init__(self, path=SAVE_FILE):
        self.path = path
        self.data = self._defaults()
        self.dirty = False
        self.loaded = False
        self.last_error = None
        self._timer = 0.0
        self.read_only = False              # файл не прочитался: пишем НЕЛЬЗЯ (не затереть настоящий)
        self.prev_launch = ""               # дата прошлого запуска — как была на диске до touch_launch
        self._retry_delay = SAVE_INTERVAL   # пауза батч-сохранения (растёт после ошибок записи)
        self._fail_streak = 0               # неудачных записей подряд (лог — только на первой)

    # --- структура по умолчанию ---
    @staticmethod
    def _default_stats():
        return {"games_played": 0, "total_time": 0.0, "monsters_killed": 0, "platforms_broken": 0,
                "jetpacks_collected": 0, "max_combo": 0, "max_height": 0, "cases_opened": 0,
                "caps_earned_total": 0}

    @classmethod
    def _defaults(cls):
        return {
            "version": cls.VERSION,
            "records": [],
            "stats": cls._default_stats(),
            "settings": {"sound": True, "difficulty": "normal"},
            "last_launch": "",
            "caps": 0,
            "skins_unlocked": [DEFAULT_SKIN],
            "skin_active": DEFAULT_SKIN,
            "skin_dupes": {},
        }

    # --- проверка и миграция загруженных данных ---
    @staticmethod
    def _sanitize_record(rec):
        """Проверить одну запись рекорда; вернуть очищенную или None."""
        if not isinstance(rec, dict) or not _is_num(rec.get("score")):
            return None
        height = rec.get("height", 0)
        monsters = rec.get("monsters", 0)
        date = rec.get("date", "")
        skin = rec.get("skin", DEFAULT_SKIN)
        return {
            "score": int(rec["score"]),
            "height": int(height) if _is_num(height) else 0,
            "monsters": int(monsters) if _is_num(monsters) else 0,
            "date": date if isinstance(date, str) else "",
            "skin": skin if isinstance(skin, str) and skin else DEFAULT_SKIN,
        }

    def _sanitize(self, raw):
        """Собрать корректную структуру из произвольного словаря (миграция + типы)."""
        d = self._defaults()
        if not isinstance(raw, dict):
            return d
        # статистика
        st = raw.get("stats")
        if isinstance(st, dict):
            for k, v in st.items():
                if not _is_num(v):
                    continue
                if k == "total_time":
                    d["stats"][k] = float(v)
                else:
                    d["stats"][k] = int(v)
        # настройки
        se = raw.get("settings")
        if isinstance(se, dict):
            if isinstance(se.get("sound"), bool):
                d["settings"]["sound"] = se["sound"]
            if isinstance(se.get("difficulty"), str):
                d["settings"]["difficulty"] = se["difficulty"]
        # дата последнего запуска
        if isinstance(raw.get("last_launch"), str):
            d["last_launch"] = raw["last_launch"]
        # крышки
        if _is_num(raw.get("caps")):
            d["caps"] = max(0, int(raw["caps"]))
        # скины
        unlocked = raw.get("skins_unlocked")
        if isinstance(unlocked, list):
            clean = []
            for sid in unlocked:
                if isinstance(sid, str) and sid in SKINS_BY_ID and sid not in clean:
                    clean.append(sid)
            if DEFAULT_SKIN not in clean:
                clean.insert(0, DEFAULT_SKIN)
            d["skins_unlocked"] = clean
        active = raw.get("skin_active")
        if isinstance(active, str) and active in SKINS_BY_ID and active in d["skins_unlocked"]:
            d["skin_active"] = active
        dupes = raw.get("skin_dupes")
        if isinstance(dupes, dict):
            for sid, n in dupes.items():
                if isinstance(sid, str) and sid in SKINS_BY_ID and _is_num(n) and int(n) > 0:
                    d["skin_dupes"][sid] = int(n)
        # рекорды
        recs = raw.get("records")
        if isinstance(recs, list):
            clean = [r for r in (self._sanitize_record(x) for x in recs) if r is not None]
            clean.sort(key=lambda r: r["score"], reverse=True)
            d["records"] = clean[:TOP_RECORDS]
        return d

    def _broken_path(self):
        """Свободное имя для копии битого файла: .broken, .broken1, .broken2, ...
        (прежние копии никогда не удаляются и не перезаписываются)."""
        base = self.path + ".broken"
        if not os.path.exists(base):
            return base
        for n in range(1, 1000):
            cand = f"{base}{n}"
            if not os.path.exists(cand):
                return cand
        return base + datetime.datetime.now().strftime("-%Y%m%d-%H%M%S-%f")

    def _quarantine_broken(self, blob=None):
        """Убрать битый файл в копию (см. _broken_path). Если переименовать нельзя
        (файл занят) — записать копию из уже прочитанных байтов blob.
        True — копия битого файла существует и оригинал можно перезаписать."""
        broken = self._broken_path()
        err = None
        try:
            os.rename(self.path, broken)        # rename (не replace): чужую копию не затираем
            print(f"[Save] битый файл сохранён как {broken}")
            return True
        except OSError as e:
            err = e
        if blob is not None:
            try:
                with open(broken, "xb") as f:
                    f.write(blob)
                print(f"[Save] копия битого файла записана в {broken}")
                return True
            except OSError as e:
                err = e
        print("[Save] не удалось сохранить копию битого файла:", err)
        return False

    def _read_bytes(self):
        """Прочитать файл сохранения целиком -> (байты, ошибка).
        (None, None) — файла нет (первый запуск); (None, OSError) — файл есть, но не
        читается. Короткая блокировка (антивирус, OneDrive, вторая копия игры) —
        несколько повторов с паузой, прежде чем сдаться."""
        err = None
        for attempt in range(max(1, LOAD_RETRIES)):
            if attempt:
                time.sleep(LOAD_RETRY_DELAY)
            try:
                with open(self.path, "rb") as f:
                    return f.read(), None
            except FileNotFoundError:
                return None, None
            except OSError as e:
                err = e
        return None, err

    # --- загрузка / запись ---
    def load(self):
        """Загрузить сохранение. Нет файла -> создать; битый (JSON/кодировка/корень не
        объект) -> копия .broken* и новый; не читается (занят, нет прав) -> defaults
        в памяти БЕЗ записи (read_only); неполный -> дозаполнить недостающие ключи."""
        self.loaded = True
        self.read_only = False
        self.prev_launch = ""
        blob, read_err = self._read_bytes()
        if read_err is not None:
            # это не порча: настоящий файл цел, просто сейчас недоступен — не трогаем его
            self.data = self._defaults()
            self.dirty = False
            self.read_only = True
            self.last_error = str(read_err)
            print(f"[Save] не удалось прочитать сохранение ({read_err}); игра идёт без записи, "
                  f"файл {self.path} не тронут")
            return
        if blob is None:
            self.data = self._defaults()
            self.dirty = True
            self.save(force=True)
            return
        try:
            # utf-8-sig: файл, пересохранённый в Блокноте/PowerShell с BOM, — не порча
            raw = json.loads(blob.decode("utf-8-sig"))
            if not isinstance(raw, dict):
                raise ValueError("корень JSON не объект")
        except (ValueError, RecursionError) as e:   # JSONDecodeError и UnicodeDecodeError — это ValueError
            print(f"[Save] файл сохранения повреждён ({e}), создаю новый")
            self.data = self._defaults()
            if not self._quarantine_broken(blob):
                # копию сохранить не удалось — оригинал не перезаписываем
                self.read_only = True
                self.dirty = False
                print("[Save] игра идёт без записи, битый файл оставлен как есть")
                return
            self.dirty = True
            self.save(force=True)
            return
        self.data = self._sanitize(raw)
        self.prev_launch = self.data.get("last_launch", "") or ""
        if self.data != raw:
            # миграция что-то поправила — сразу зафиксировать на диске
            self.dirty = True
            self.save(force=True)

    def save(self, force=False):
        """Записать JSON атомарно (временный файл + os.replace). Возвращает успех.
        В режиме read_only не пишет ничего. После ошибки следующий батч-повтор — не раньше
        SAVE_INTERVAL, затем пауза удваивается до SAVE_RETRY_MAX; в консоль — одна строка
        на серию ошибок."""
        if self.read_only:
            return False
        if not force and not self.dirty:
            return True
        tmp = self.path + ".tmp"
        try:
            folder = os.path.dirname(self.path)
            if folder and not os.path.isdir(folder):
                os.makedirs(folder, exist_ok=True)
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
                f.flush()
                if force:
                    # Важные события (рекорд, покупка кейса, выход) — принудительно на диск.
                    # Фоновые батч-сохранения раз в 5 с fsync не делают: на Windows он
                    # занимает 15-25 мс и давал бы заметный рывок кадра посреди игры.
                    try:
                        os.fsync(f.fileno())
                    except Exception:
                        pass
            # На Windows цель бывает на миг занята (антивирус, индексатор: WinError 5/32):
            # для важных записей — пара коротких повторов; фоновая запись не ждёт
            # (её повторит tick с откатом)
            tries = 3 if force else 1
            for attempt in range(tries):
                try:
                    os.replace(tmp, self.path)
                    break
                except PermissionError:
                    if attempt == tries - 1:
                        raise
                    time.sleep(0.03)
            self.dirty = False
            self._timer = 0.0
            self.last_error = None
            if self._fail_streak:
                print("[Save] запись сохранения снова работает")
            self._fail_streak = 0
            self._retry_delay = SAVE_INTERVAL
            return True
        except Exception as e:
            self.last_error = str(e)
            self._fail_streak += 1
            self._retry_delay = min(SAVE_RETRY_MAX,
                                    SAVE_INTERVAL * 2 ** min(self._fail_streak - 1, 10))
            self._timer = 0.0
            if self._fail_streak == 1:
                print(f"[Save] ошибка записи сохранения: {e} (повтор через {self._retry_delay:.0f} с)")
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass
            return False

    def tick(self, dt):
        """Батч-сохранение: если есть изменения и прошло >= SAVE_INTERVAL
        (после ошибок записи — >= текущей паузы отката, но никогда не каждый кадр)."""
        self._timer += dt
        if self.dirty and not self.read_only and self._timer >= self._retry_delay:
            self._timer = 0.0
            self.save()

    def mark_dirty(self):
        """Пометить, что данные изменились и их нужно сохранить."""
        self.dirty = True

    # --- рекорды и статистика ---
    def add_record(self, score, height, monsters, date=None, skin=DEFAULT_SKIN):
        """Добавить рекорд, отсортировать по очкам, обрезать до TOP_RECORDS,
        сохранить сразу. Возвращает место 1..TOP_RECORDS или 0 (не попал)."""
        try:
            score = int(score)
        except (TypeError, ValueError):
            score = 0
        try:
            height = int(height)
        except (TypeError, ValueError):
            height = 0
        try:
            monsters = int(monsters)
        except (TypeError, ValueError):
            monsters = 0
        rec = {"score": score, "height": height, "monsters": monsters,
               "date": date if isinstance(date, str) and date else today_str(),
               "skin": str(skin) if skin else DEFAULT_SKIN}
        recs = self.data.get("records")
        if not isinstance(recs, list):
            recs = []
            self.data["records"] = recs
        recs.append(rec)
        recs.sort(key=lambda r: r.get("score", 0), reverse=True)   # стабильно: старые при равенстве выше
        del recs[TOP_RECORDS:]
        rank = 0
        for i, r in enumerate(recs):
            if r is rec:
                rank = i + 1
                break
        st = self.stats
        st["max_height"] = max(int(st.get("max_height", 0) or 0), height)
        self.dirty = True
        self.save(force=True)
        return rank

    def update_stats(self, **kwargs):
        """Обновить статистику: суммируемые ключи складываются, max_* — максимум."""
        st = self.stats
        for k, v in kwargs.items():
            if not _is_num(v):
                continue
            if k in self.MAX_KEYS:
                st[k] = max(st.get(k, 0) or 0, v)
            else:
                st[k] = (st.get(k, 0) or 0) + v
            if k != "total_time":
                st[k] = int(st[k])
        self.mark_dirty()

    def reset(self):
        """Сбросить рекорды и статистику (крышки и скины сохраняются)."""
        self.data["records"] = []
        self.data["stats"] = self._default_stats()
        self.dirty = True
        self.save(force=True)

    def reset_all(self):
        """Полный сброс к значениям по умолчанию."""
        self.data = self._defaults()
        self.dirty = True
        self.save(force=True)

    # --- свойства ---
    @property
    def best_score(self):
        recs = self.records
        if not recs:
            return 0
        try:
            return int(recs[0].get("score", 0))
        except (TypeError, ValueError, AttributeError):
            return 0

    @property
    def records(self):
        recs = self.data.get("records")
        if not isinstance(recs, list):
            recs = []
            self.data["records"] = recs
        return recs

    @property
    def stats(self):
        st = self.data.get("stats")
        if not isinstance(st, dict):
            st = self._default_stats()
            self.data["stats"] = st
        return st

    @property
    def settings(self):
        se = self.data.get("settings")
        if not isinstance(se, dict):
            se = {"sound": True, "difficulty": "normal"}
            self.data["settings"] = se
        return se

    @property
    def caps(self):
        v = self.data.get("caps", 0)
        return int(v) if _is_num(v) else 0

    # --- крышки ---
    def add_caps(self, n):
        """Добавить крышки (n может быть отрицательным — тогда просто вычесть)."""
        try:
            n = int(n)
        except (TypeError, ValueError):
            return
        self.data["caps"] = max(0, self.caps + n)
        if n > 0:
            st = self.stats
            st["caps_earned_total"] = int(st.get("caps_earned_total", 0) or 0) + n
        self.mark_dirty()

    def spend_caps(self, n):
        """Потратить крышки; False, если не хватает."""
        try:
            n = int(n)
        except (TypeError, ValueError):
            return False
        if n < 0 or self.caps < n:
            return False
        self.data["caps"] = self.caps - n
        self.mark_dirty()
        return True

    # --- скины ---
    def _unlocked_list(self):
        lst = self.data.get("skins_unlocked")
        if not isinstance(lst, list):
            lst = [DEFAULT_SKIN]
            self.data["skins_unlocked"] = lst
        return lst

    def _dupes_dict(self):
        d = self.data.get("skin_dupes")
        if not isinstance(d, dict):
            d = {}
            self.data["skin_dupes"] = d
        return d

    def is_unlocked(self, skin_id):
        return skin_id in self._unlocked_list()

    def unlock_skin(self, skin_id):
        """Открыть скин. True — новый; False — дубликат (счётчик дубликатов +1)."""
        lst = self._unlocked_list()
        self.mark_dirty()
        if skin_id in lst:
            d = self._dupes_dict()
            d[skin_id] = int(d.get(skin_id, 0) or 0) + 1
            return False
        lst.append(skin_id)
        return True

    def dupes_of(self, skin_id):
        v = self._dupes_dict().get(skin_id, 0)
        return int(v) if _is_num(v) else 0

    def remove_dupes(self, skin_id, n):
        """Убрать n дубликатов скина (например, при продаже)."""
        d = self._dupes_dict()
        try:
            n = int(n)
        except (TypeError, ValueError):
            return
        left = self.dupes_of(skin_id) - n
        if left > 0:
            d[skin_id] = left
        else:
            d.pop(skin_id, None)
        self.mark_dirty()

    def total_dupes(self):
        return sum(int(v) for v in self._dupes_dict().values() if _is_num(v))

    @property
    def skin_active(self):
        sid = self.data.get("skin_active")
        if isinstance(sid, str) and sid in SKINS_BY_ID:
            return sid
        return DEFAULT_SKIN

    def set_skin(self, skin_id):
        """Сделать скин активным (только известный и открытый)."""
        if skin_id in SKINS_BY_ID and self.is_unlocked(skin_id):
            self.data["skin_active"] = skin_id
            self.mark_dirty()

    def touch_launch(self):
        """Записать дату/время текущего запуска (прошлый запуск остаётся в prev_launch)."""
        self.data["last_launch"] = datetime.datetime.now().strftime(DATE_FORMAT + " %H:%M")
        self.mark_dirty()


# ───────────────────────────────────────────────────────────────────────────
#  ЧАСТИЦЫ
# ───────────────────────────────────────────────────────────────────────────
def fire_color(t):
    """Цвет огня по «возрасту» частицы t в [0, 1]: жёлтый -> оранжевый -> красный -> тёмный."""
    if t < 0.4:
        return lerp_color((255, 240, 120), ORANGE, t / 0.4)
    if t < 0.8:
        return lerp_color(ORANGE, (220, 50, 30), (t - 0.4) / 0.4)
    return lerp_color((220, 50, 30), (90, 30, 30), (t - 0.8) / 0.2)


def _particle_sprite(color, radius, alpha):
    """Кэшированный полупрозрачный кружок для частиц (цвет и альфа квантуются)."""
    r = max(1, int(radius))
    a = (int(clamp(alpha, 0, 255)) // 24) * 24 + 15
    col = (color[0] // 8 * 8, color[1] // 8 * 8, color[2] // 8 * 8)
    key = (col, r, a)
    spr = RenderCache.particles.get(key)
    if spr is None:
        spr = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(spr, col + (min(255, a),), (r + 1, r + 1), r)
        RenderCache.particles.put(key, spr)
    return spr


def _as_range(v):
    """(lo, hi) из числа или пары."""
    if isinstance(v, (tuple, list)) and len(v) >= 2:
        return float(v[0]), float(v[1])
    return float(v), float(v)


class Particle:
    """Одна частица: позиция, скорость, жизнь, цвет (или функция цвета от возраста),
    размер, гравитация, форма, вращение. screen=True — экранные координаты."""

    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "color_fn", "size",
                 "gravity", "shape", "rot", "rot_speed", "screen", "text", "fade", "drag")

    def __init__(self, x, y, vx, vy, life, color, size, gravity=600.0, shape="circle",
                 rot=0.0, rot_speed=0.0, screen=False, text=None, fade=True,
                 color_fn=None, drag=0.0):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.life = max(0.01, float(life))
        self.max_life = self.life
        self.color = color
        self.color_fn = color_fn
        self.size = float(size)
        self.gravity = float(gravity)
        self.shape = shape
        self.rot = float(rot)
        self.rot_speed = float(rot_speed)
        self.screen = bool(screen)
        self.text = text
        self.fade = bool(fade)
        self.drag = float(drag)

    @property
    def progress(self):
        """Возраст 0 (родилась) .. 1 (умирает)."""
        if self.max_life <= 0:
            return 1.0
        return clamp(1.0 - self.life / self.max_life, 0.0, 1.0)

    def update(self, dt):
        """Шаг физики; возвращает True, пока частица жива."""
        self.life -= dt
        if self.life <= 0:
            return False
        self.vy += self.gravity * dt
        if self.drag:
            k = max(0.0, 1.0 - self.drag * dt)
            self.vx *= k
            self.vy *= k
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rot += self.rot_speed * dt
        return True

    def current_color(self):
        """Текущий цвет с учётом функции цвета."""
        if self.color_fn is not None:
            try:
                return self.color_fn(self.progress)
            except Exception:
                return self.color
        return self.color


class ParticleSystem:
    """Система частиц с лимитом MAX и набором готовых эмиттеров
    (пыль, искры, конфетти, дым, чернила, огонь, цифры)."""

    MAX = 1500

    def __init__(self):
        self.particles = []

    def __len__(self):
        return len(self.particles)

    def clear(self):
        self.particles.clear()

    def emit(self, x, y, count, color=WHITE, speed=(60, 220), life=(0.3, 0.9), size=(2, 5),
             gravity=600, angle=None, spread=360, shape="circle", screen=False, text=None,
             fade=True, drag=0.0, rot_speed=None):
        """Выпустить count частиц из (x, y).
        color — кортеж, список кортежей (случайный) или callable(t)->цвет.
        angle — направление в градусах (0 — вправо, -90 — вверх), None — во все стороны;
        spread — разброс углов в градусах."""
        count = int(count)
        if count <= 0:
            return
        count = min(count, self.MAX)
        room = self.MAX - len(self.particles)
        if count > room:
            overflow = count - room
            if overflow >= len(self.particles):
                self.particles.clear()
            else:
                del self.particles[:overflow]     # вытесняем самые старые
        color_fn = color if callable(color) else None
        palette = color if isinstance(color, list) and color else None
        base_color = tuple(color) if isinstance(color, tuple) else WHITE
        sp_lo, sp_hi = _as_range(speed)
        lf_lo, lf_hi = _as_range(life)
        sz_lo, sz_hi = _as_range(size)
        half_spread = math.radians(spread) / 2.0
        for _ in range(count):
            if angle is None:
                a = random.uniform(0.0, math.tau)
            else:
                a = math.radians(angle) + random.uniform(-half_spread, half_spread)
            v = random.uniform(sp_lo, sp_hi)
            if palette is not None:
                col = random.choice(palette)
            else:
                col = base_color
            rs = random.uniform(-6.0, 6.0) if rot_speed is None else random.uniform(-rot_speed, rot_speed)
            self.particles.append(Particle(
                x, y, math.cos(a) * v, math.sin(a) * v,
                random.uniform(lf_lo, lf_hi), col, random.uniform(sz_lo, sz_hi),
                gravity=gravity, shape=shape, rot=random.uniform(0.0, math.tau), rot_speed=rs,
                screen=screen, text=text, fade=fade, color_fn=color_fn, drag=drag))

    # --- готовые эмиттеры ---
    def dust(self, x, y, count=12):
        """Серо-бежевое медленное облако пыли."""
        self.emit(x, y, count, color=[(200, 190, 170), (180, 170, 150), (215, 205, 190)],
                  speed=(20, 90), life=(0.5, 1.1), size=(3, 7), gravity=-30,
                  angle=-90, spread=200, shape="circle", drag=2.0)

    def sparks(self, x, y, count=12, color=GOLD):
        """Искры-линии, разлетаются во все стороны."""
        self.emit(x, y, count, color=color, speed=(150, 380), life=(0.25, 0.6), size=(2, 3),
                  gravity=500, shape="spark")

    def confetti(self, x, y, count=40, screen=False):
        """Разноцветные вращающиеся квадратики."""
        self.emit(x, y, count, color=[RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, PINK, CYAN],
                  speed=(120, 360), life=(1.0, 1.8), size=(4, 7), gravity=350,
                  angle=-90, spread=140, shape="square", screen=screen, drag=1.2)

    def smoke(self, x, y, count=1, color=(120, 120, 120)):
        """Дымок: медленно поднимается, расширяется, тает."""
        self.emit(x, y, count, color=color, speed=(10, 40), life=(0.6, 1.2), size=(4, 8),
                  gravity=-80, angle=-90, spread=60, shape="circle", drag=1.5)

    def ink(self, x, y, count=10):
        """Чернильные брызги (тёмно-синие)."""
        self.emit(x, y, count, color=[(20, 30, 90), (30, 40, 120), (15, 20, 60)],
                  speed=(80, 260), life=(0.4, 0.9), size=(3, 6), gravity=700, shape="circle")

    def fire(self, x, y, count=3):
        """Огонь: цвет по жизни жёлтый -> оранжевый -> красный, поднимается вверх."""
        self.emit(x, y, count, color=fire_color, speed=(30, 120), life=(0.25, 0.55), size=(4, 8),
                  gravity=-250, angle=-90, spread=50, shape="circle", drag=1.0)

    def digits(self, x, y, text, count=1, color=WHITE, screen=False):
        """Частицы-цифры («67» / «52»): текст, летящий вверх и вращающийся."""
        self.emit(x, y, count, color=color, speed=(40, 160), life=(0.7, 1.3), size=(16, 26),
                  gravity=300, angle=-90, spread=90, shape="text", screen=screen, text=str(text))

    # --- логика и отрисовка ---
    def update(self, dt):
        if not self.particles:
            return
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, surf, cam_y):
        if not self.particles:
            return
        w, h = surf.get_size()
        for p in self.particles:
            sy = p.y - (0.0 if p.screen else cam_y)
            sx = p.x
            if sy < -40 or sy > h + 40 or sx < -40 or sx > w + 40:
                continue
            frac = 1.0 - p.progress            # 1 в начале, 0 в конце
            col = p.current_color()
            shape = p.shape
            if shape == "circle":
                r = p.size * (0.35 + 0.65 * frac) if p.fade else p.size
                if p.fade:
                    alpha = 255 * math.sqrt(frac)
                    spr = _particle_sprite(col, r, alpha)
                    surf.blit(spr, (int(sx) - spr.get_width() // 2, int(sy) - spr.get_height() // 2))
                else:
                    pygame.draw.circle(surf, col, (int(sx), int(sy)), max(1, int(r)))
            elif shape == "square":
                half = p.size * (0.4 + 0.6 * frac) if p.fade else p.size
                c, s = math.cos(p.rot), math.sin(p.rot)
                pts = [(sx + c * half - s * half, sy + s * half + c * half),
                       (sx - c * half - s * half, sy - s * half + c * half),
                       (sx - c * half + s * half, sy - s * half - c * half),
                       (sx + c * half + s * half, sy + s * half - c * half)]
                pygame.draw.polygon(surf, col, pts)
            elif shape == "spark":
                length = clamp(math.hypot(p.vx, p.vy) * 0.035, 3.0, 22.0) * (0.3 + 0.7 * frac)
                speed = math.hypot(p.vx, p.vy) or 1.0
                ex = sx - p.vx / speed * length
                ey = sy - p.vy / speed * length
                width = max(1, int(p.size * (0.4 + 0.6 * frac)))
                pygame.draw.line(surf, col, (int(sx), int(sy)), (int(ex), int(ey)), width)
            elif shape == "ring":
                r = int(p.size + (1.0 - frac) * p.size * 3.0)
                width = max(1, int(3 * frac))
                pygame.draw.circle(surf, col, (int(sx), int(sy)), max(1, r), width)
            elif shape == "text":
                alpha = 255 * (frac if p.fade else 1.0)
                draw_text(surf, p.text or "", sx, sy, size=int(p.size), color=col, bold=True,
                          outline=BLACK, alpha=int(alpha))
            else:
                pygame.draw.circle(surf, col, (int(sx), int(sy)), max(1, int(p.size)))


# ───────────────────────────────────────────────────────────────────────────
#  ВСПЛЫВАЮЩИЙ ТЕКСТ
# ───────────────────────────────────────────────────────────────────────────
class FloatingText:
    """Всплывающая надпись: появляется с «пружинкой» масштаба, плывёт вверх,
    в конце растворяется. world=True — мировые координаты (с учётом cam_y)."""

    POP_TIME = 0.2

    def __init__(self, text, x, y, color=WHITE, size=26, life=1.2, vy=-60, world=True,
                 bold=True, outline=BLACK, scale_pop=True):
        self.text = "" if text is None else str(text)
        self.x = float(x)
        self.y = float(y)
        self.color = tuple(color[:3])
        self.size = int(size)
        self.life = max(0.05, float(life))
        self.vy = float(vy)
        self.world = bool(world)
        self.bold = bool(bold)
        self.outline = tuple(outline[:3]) if outline else None
        self.scale_pop = bool(scale_pop)
        self.time = 0.0
        self.alive = True
        self._base_w = None        # ширина надписи в базовом размере (лениво, для экранных надписей)

    def update(self, dt):
        if not self.alive:
            return
        self.time += dt
        self.y += self.vy * dt
        if self.time >= self.life:
            self.alive = False

    def _max_pop_scale(self):
        """Экранная надпись при «пружинке» не должна вылезать за края окна."""
        if self._base_w is None:
            try:
                self._base_w = get_font(self.size, self.bold).size(self.text)[0] + 4
            except Exception:
                self._base_w = 0
        if self._base_w <= 0:
            return 1.25
        return max(1.0, (SCREEN_W - 8) / float(self._base_w))

    def draw(self, surf, cam_y):
        if not self.alive or not self.text:
            return
        frac = clamp(self.time / self.life, 0.0, 1.0)
        alpha = 255 if frac < 0.6 else int(255 * (1.0 - (frac - 0.6) / 0.4))
        if alpha <= 0:
            return
        scale = 1.0
        if self.scale_pop and self.time < self.POP_TIME:
            pt = self.time / self.POP_TIME
            if pt < 0.6:
                scale = lerp(0.4, 1.25, pt / 0.6)
            else:
                scale = lerp(1.25, 1.0, (pt - 0.6) / 0.4)
            if scale > 1.0 and not self.world:
                scale = min(scale, self._max_pop_scale())
        sy = self.y - (cam_y if self.world else 0.0)
        size = max(6, int(self.size * scale))
        shadow = None if self.outline else (0, 0, 0)
        draw_text(surf, self.text, self.x, sy, size=size, color=self.color, anchor="center",
                  bold=self.bold, shadow=shadow, outline=self.outline, alpha=alpha)


# ───────────────────────────────────────────────────────────────────────────
#  КНОПКИ
# ───────────────────────────────────────────────────────────────────────────
class Button:
    """Кнопка: закруглённая плашка с тенью и бликом, подсветка при наведении,
    золотая рамка при выборе с клавиатуры, серый вид если недоступна,
    горячая клавиша и вторая (мелкая) строка текста."""

    RADIUS = 12

    def __init__(self, rect, text, callback=None, color=UI_BTN, hover=UI_BTN_HOVER,
                 text_color=WHITE, size=26, hotkey=None, enabled=True, small_text=None):
        self.rect = pygame.Rect(rect)
        self.text = "" if text is None else str(text)
        self.callback = callback
        self.color = tuple(color[:3])
        self.hover_color = tuple(hover[:3])
        self.text_color = tuple(text_color[:3])
        self.size = int(size)
        self.enabled = bool(enabled)
        self.small_text = None if small_text is None else str(small_text)
        self.selected = False
        self.hovered = False
        self.hotkeys = set()
        if hotkey is not None:
            if isinstance(hotkey, (list, tuple, set)):
                self.hotkeys.update(int(k) for k in hotkey)
            else:
                self.hotkeys.add(int(hotkey))
        self.hover_t = 0.0      # плавная подсветка 0..1
        self.press_t = 0.0      # вспышка при нажатии
        self.time = 0.0         # для пульсации рамки
        self.scale = 1.0

    def set_text(self, text, small_text=None):
        """Сменить текст (и вторую строку) кнопки."""
        self.text = "" if text is None else str(text)
        if small_text is not None:
            self.small_text = str(small_text)

    def handle_event(self, event):
        """Клик ЛКМ внутри кнопки или горячая клавиша -> callback(). True, если съедено."""
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and getattr(event, "button", 0) == 1:
            if self.rect.collidepoint(event.pos):
                self.activate()
                return True
        elif event.type == pygame.KEYDOWN and event.key in self.hotkeys:
            self.activate()
            return True
        return False

    def activate(self):
        """Вызвать callback (используется и клавиатурой). Ошибки в callback не роняют игру."""
        if not self.enabled:
            return False
        self.press_t = 0.18
        if self.callback is not None:
            try:
                self.callback()
            except Exception:
                traceback.print_exc()
        return True

    def update(self, dt, mouse_pos):
        """Обновить наведение и анимацию масштаба."""
        self.time += dt
        self.hovered = bool(self.enabled and mouse_pos is not None
                            and self.rect.collidepoint(mouse_pos))
        target = 1.0 if (self.hovered or self.selected) and self.enabled else 0.0
        k = clamp(dt * 12.0, 0.0, 1.0)
        self.hover_t += (target - self.hover_t) * k
        if self.press_t > 0:
            self.press_t = max(0.0, self.press_t - dt)
        bump = 0.0
        if self.press_t > 0:
            bump = -0.06 * math.sin(self.press_t / 0.18 * math.pi)
        self.scale = 1.0 + 0.04 * self.hover_t + bump

    def draw(self, surf):
        r = self.rect
        if abs(self.scale - 1.0) > 0.001:
            grow_w = int(r.w * (self.scale - 1.0))
            grow_h = int(r.h * (self.scale - 1.0))
            r = r.inflate(grow_w, grow_h)
        radius = min(self.RADIUS, r.h // 2)
        if self.enabled:
            body = lerp_color(self.color, self.hover_color, self.hover_t)
            if self.press_t > 0:
                body = lerp_color(body, WHITE, 0.25 * self.press_t / 0.18)
            text_col = self.text_color
            shadow_col = shade_color(self.color, 0.45)
        else:
            body = (95, 100, 112)
            text_col = (175, 178, 190)
            shadow_col = (55, 58, 68)
        # тень
        draw_rounded_rect(surf, r.move(0, 4), shadow_col, radius)
        # тело
        draw_rounded_rect(surf, r, body, radius)
        # блик в верхней половине
        hl = pygame.Rect(r.x + 3, r.y + 3, r.w - 6, max(4, r.h // 2 - 3))
        draw_rounded_rect(surf, hl, (255, 255, 255, 38 if self.enabled else 18), max(2, radius - 3))
        # рамка
        if self.selected and self.enabled:
            pulse = 0.5 + 0.5 * math.sin(self.time * 6.0)
            frame = lerp_color(GOLD, WHITE, 0.35 * pulse)
            pygame.draw.rect(surf, frame, r, 3, border_radius=radius)
        else:
            pygame.draw.rect(surf, shade_color(body, 0.6), r, 2, border_radius=radius)
        # текст
        cx, cy = r.centerx, r.centery
        shadow = (0, 0, 0) if self.enabled else None
        if self.small_text:
            main_size = max(10, int(self.size * 0.92))
            small_size = max(9, int(self.size * 0.6))
            draw_text(surf, self.text, cx, cy - small_size // 2 - 1, size=main_size, color=text_col,
                      anchor="center", bold=True, shadow=shadow)
            # мелкая строка (~10 px): тень в 2 px её «замыливает», а светлый текст
            # на светлой (оранжевой) кнопке не читается — рисуем тёмным тоном кнопки без тени
            small_col = shade_color(body, 0.32) if self.enabled else text_col
            draw_text(surf, self.small_text, cx, cy + main_size // 2, size=small_size,
                      color=small_col, anchor="center", bold=True, shadow=None)
        else:
            draw_text(surf, self.text, cx, cy, size=self.size, color=text_col, anchor="center",
                      bold=True, shadow=shadow)


class ButtonGroup:
    """Группа кнопок с клавиатурной навигацией: Вверх/Вниз (W/S) — выбор,
    Enter/Space — активировать. Мышь обрабатывается кнопками напрямую.

    Наведение мыши забирает выбор только когда мышь реально ДВИГАЛАСЬ:
    неподвижный курсор над кнопкой не перебивает выбор с клавиатуры."""

    def __init__(self, buttons):
        self.buttons = list(buttons)
        self.index = 0
        self.mouse_active = False   # мышь двигалась после последней клавиатурной навигации
        self._last_mouse = None     # позиция мыши на прошлом update (None — нет точки отсчёта)
        self._fix_index()

    @property
    def current(self):
        """Текущая выбранная кнопка или None."""
        if not self.buttons:
            return None
        return self.buttons[self.index]

    def set_index(self, i):
        """Выбрать кнопку i (недоступная — перескакиваем на следующую доступную).
        Сбрасывает «активность» мыши: при входе на экран курсор, оставшийся над
        какой-то кнопкой, не перехватывает выбор, пока мышь не сдвинется."""
        self.mouse_active = False
        self._last_mouse = None
        if not self.buttons:
            self.index = 0
            return
        self.index = int(clamp(int(i), 0, len(self.buttons) - 1))
        self._fix_index()

    def _fix_index(self):
        """Убедиться, что индекс в пределах и указывает на доступную кнопку."""
        if not self.buttons:
            self.index = 0
            return
        self.index = int(clamp(self.index, 0, len(self.buttons) - 1))
        if not self.buttons[self.index].enabled:
            self.move(1)

    def move(self, direction):
        """Сдвинуть выбор на следующую доступную кнопку (по кругу)."""
        n = len(self.buttons)
        if n == 0:
            return
        i = self.index
        for _ in range(n):
            i = (i + direction) % n
            if self.buttons[i].enabled:
                self.index = i
                return

    def _hover_select(self, pos):
        """Мышь сдвинулась: выбор переходит на доступную кнопку под курсором (если есть)."""
        self.mouse_active = True
        if pos is None:
            return
        for i, b in enumerate(self.buttons):
            if b.enabled and b.rect.collidepoint(pos):
                self.index = i
                return

    def handle_event(self, event):
        """Сначала событие получают кнопки (мышь/хоткеи), затем — навигация."""
        if event.type == pygame.MOUSEMOTION:
            self._hover_select(getattr(event, "pos", None))
            return False
        for i, b in enumerate(self.buttons):
            if b.handle_event(event):
                self.index = i
                return True
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.mouse_active = False     # клавиатура главнее, пока мышь не сдвинется
                self.move(-1)
                return True
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.mouse_active = False
                self.move(1)
                return True
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                b = self.current
                if b is not None and b.enabled:
                    b.activate()
                    return True
        return False

    def update(self, dt, mouse_pos):
        """Анимация кнопок. Выбор следует за курсором только если мышь сдвинулась
        с прошлого кадра (pygame.mouse.get_pos() возвращает позицию и неподвижной мыши)."""
        moved = False
        if mouse_pos is not None:
            try:
                mp = (int(mouse_pos[0]), int(mouse_pos[1]))
            except (TypeError, ValueError, IndexError):
                mp = None
            if mp is not None:
                moved = self._last_mouse is not None and mp != self._last_mouse
                self._last_mouse = mp
        if moved:
            self._hover_select(mouse_pos)
        # подсветку наведения показываем, только пока мышь «в деле»
        hover_pos = mouse_pos if self.mouse_active else None
        for b in self.buttons:
            b.update(dt, hover_pos)
        if self.buttons and (not 0 <= self.index < len(self.buttons)
                             or not self.buttons[self.index].enabled):
            self._fix_index()          # кнопка могла стать недоступной (кончились крышки)
        for i, b in enumerate(self.buttons):
            b.selected = (i == self.index) and b.enabled

    def draw(self, surf):
        for b in self.buttons:
            b.draw(surf)


# ═══════════════════════════════════════════════════════════════════════════
# ═══ ЧАСТЬ 2: ПЛАТФОРМЫ И ОСКОЛКИ ═══
# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
#  PART 2: ПЛАТФОРМЫ И ОСКОЛКИ
#  Platform (база) + 6 типов, PlatformDebris (осколок) и DebrisPool (пул).
#  Логика — в update()/on_land(), рисование — в draw(). Всё рисуется примитивами.
# ═══════════════════════════════════════════════════════════════════════════


def _shade(color, k):
    """Затемнить (k<1) или осветлить (k>1) цвет; результат зажат в 0..255."""
    r, g, b = color[0], color[1], color[2]
    return (max(0, min(255, int(r * k))),
            max(0, min(255, int(g * k))),
            max(0, min(255, int(b * k))))


def _draw_plate(surf, rect, color, outline=None):
    """Универсальная «плашка» платформы: тень, тёмный низ, тело, блик сверху, обводка."""
    if rect.w <= 0 or rect.h <= 0:
        return
    radius = max(3, min(8, rect.h // 2))
    # Мягкая тень под плашкой
    shadow = pygame.Rect(rect.x + 1, rect.y + 3, rect.w, rect.h)
    pygame.draw.rect(surf, _shade(color, 0.35), shadow, border_radius=radius)
    # Тёмный низ (вся плашка тёмным, сверху — светлое тело чуть ниже по высоте)
    pygame.draw.rect(surf, _shade(color, 0.62), rect, border_radius=radius)
    body = pygame.Rect(rect.x, rect.y, rect.w, max(4, rect.h - 4))
    pygame.draw.rect(surf, color, body, border_radius=radius)
    # Блик сверху
    hl = pygame.Rect(rect.x + 5, rect.y + 2, max(2, rect.w - 10), 3)
    pygame.draw.rect(surf, _shade(color, 1.35), hl, border_radius=2)
    # Тонкая обводка
    pygame.draw.rect(surf, outline if outline else _shade(color, 0.45), rect, width=1, border_radius=radius)


def _make_crack(w, h, x0, y0, segments, dx_range, dy_range, x_bias=0.0):
    """Сгенерировать ломаную-трещину внутри плашки w×h, начиная с (x0, y0). Возвращает список точек."""
    pts = [(x0, y0)]
    x, y = x0, y0
    for _ in range(segments):
        x = x + random.uniform(*dx_range) + x_bias
        y = y + random.uniform(*dy_range)
        x = max(1, min(w - 1, x))
        y = max(1, min(h - 1, y))
        pts.append((x, y))
    return pts


class Platform:
    """Базовая платформа: закруглённая плашка, на которую можно приземлиться и прыгнуть."""
    kind = "normal"
    color = PLAT_NORMAL
    can_land = True

    def __init__(self, x, y, w=PLATFORM_W):
        # x, y — левый верхний угол в мировых координатах
        self.x = float(x)
        self.y = float(y)
        self.w = int(w)
        self.h = PLATFORM_H
        self.rect = pygame.Rect(int(self.x), int(self.y), self.w, self.h)
        self.alive = True
        self.vx = 0.0
        self.landed = 0
        self.time = 0.0
        self.phase = random.uniform(0.0, 6.28)     # фаза анимации, чтобы платформы не «дышали» синхронно
        self.press = 0.0                           # проседание плашки после приземления (1 -> 0)

    @property
    def top(self):
        """Мировая y верхнего края."""
        return self.y

    @property
    def cx(self):
        """Мировая x центра."""
        return self.x + self.w / 2.0

    def sync_rect(self):
        """Обновить rect по x, y."""
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        self.rect.w = self.w
        self.rect.h = self.h

    def update(self, dt, game):
        """Базовая логика: время, затухание «проседания», синхронизация rect."""
        self.time += dt
        if self.press > 0.0:
            self.press = max(0.0, self.press - dt / PLATFORM_PRESS_TIME)
        self.sync_rect()

    def bounce_power(self):
        """Скорость, которую получает игрок при прыжке с этой платформы."""
        return JUMP_POWER

    def on_land(self, player, game):
        """Игрок приземлился сверху: подбросить его и посчитать приземление."""
        if not self.alive:
            return
        player.jump(self.bounce_power(), game)
        self.landed += 1
        self.press = 1.0

    def break_apart(self, game, cause="jump"):
        """Разрушить платформу: осколки, пыль, тряска, звук, уведомление игры."""
        if not self.alive:
            return
        self.alive = False
        debris = getattr(game, "debris", None)
        if debris is not None:
            debris.spawn(self.rect, self.debris_color())
        particles = getattr(game, "particles", None)
        if particles is not None:
            particles.dust(self.cx, self.top, 12)
        game.shake(*SHAKE_BREAK)
        game.sound.play("crack")
        game.on_platform_broken(self, cause)

    # --- отрисовка -----------------------------------------------------------

    def on_screen(self, cam_y, margin=80):
        """Быстрая проверка видимости по y."""
        sy = self.y - cam_y
        return -margin <= sy <= SCREEN_H + margin

    def plate_rect(self, cam_y):
        """Экранный rect плашки с учётом «проседания» при приземлении."""
        sink = int(round(self.press * 3))
        return pygame.Rect(int(self.x), int(self.y - cam_y) + sink, self.w, max(6, self.h - sink))

    def draw_color(self):
        """Цвет плашки в текущий момент (наследники могут подкрашивать)."""
        return self.color

    def debris_color(self):
        """Цвет осколков при разрушении (по умолчанию — цвет плашки)."""
        return self.color

    def draw(self, surf, cam_y):
        """Нарисовать плашку и декор типа."""
        if not self.alive or not self.on_screen(cam_y):
            return
        rect = self.plate_rect(cam_y)
        self.draw_below(surf, rect)
        _draw_plate(surf, rect, self.draw_color())
        self.draw_decor(surf, rect)
        self.draw_above(surf, rect)

    def draw_below(self, surf, rect):
        """Декор под плашкой (пусто в базе)."""
        pass

    def draw_decor(self, surf, rect):
        """Декор на самой плашке (пусто в базе)."""
        pass

    def draw_above(self, surf, rect):
        """Декор над плашкой: пружина, ракета и т.п. (пусто в базе)."""
        pass


class NormalPlatform(Platform):
    """Обычная зелёная платформа с травкой и иногда цветочком."""
    kind = "normal"
    color = PLAT_NORMAL

    def __init__(self, x, y, w=PLATFORM_W):
        super().__init__(x, y, w)
        # Пучки травы: (смещение по x, высота, наличие цветочка)
        n = max(2, min(6, self.w // 18))
        self.tufts = []
        for i in range(n):
            dx = 8 + (self.w - 16) * (i + random.uniform(0.2, 0.8)) / n
            self.tufts.append((dx, random.uniform(4, 7), random.random() < 0.15))

    def draw_decor(self, surf, rect):
        """Травинки-пучки, покачивающиеся на ветру, и редкие цветочки."""
        grass = _shade(self.color, 1.15)
        dark = _shade(self.color, 0.75)
        top = rect.y
        for dx, height, flower in self.tufts:
            bx = rect.x + dx
            sway = math.sin(self.time * 3.0 + self.phase + dx * 0.1) * 1.5
            # три травинки веером
            for k, (ox, hk) in enumerate(((-3, 0.7), (0, 1.0), (3, 0.75))):
                tip = (bx + ox * 1.6 + sway, top - height * hk)
                pygame.draw.line(surf, dark if k == 1 else grass, (bx + ox, top + 1), tip, 2)
            if flower:
                fx, fy = bx + sway, top - height - 2
                pygame.draw.circle(surf, PINK, (int(fx), int(fy)), 3)
                pygame.draw.circle(surf, YELLOW, (int(fx), int(fy)), 1)


class MovingPlatform(Platform):
    """Синяя движущаяся платформа: ездит влево-вправо, отскакивая от краёв экрана."""
    kind = "moving"
    color = PLAT_MOVING

    def __init__(self, x, y, w=PLATFORM_W):
        super().__init__(x, y, w)
        speed = random.uniform(*MOVING_PLATFORM_SPEED)
        self.vx = speed if random.random() < 0.5 else -speed

    def update(self, dt, game):
        """Движение с отскоком от границ экрана."""
        self.x += self.vx * dt
        if self.x < 0:
            self.x = 0.0
            self.vx = abs(self.vx)
        elif self.x + self.w > SCREEN_W:
            self.x = float(SCREEN_W - self.w)
            self.vx = -abs(self.vx)
        super().update(dt, game)

    def draw_decor(self, surf, rect):
        """Бегущие стрелочки-шевроны в направлении движения."""
        d = 1 if self.vx >= 0 else -1
        cy = rect.y + rect.h // 2 - 1
        light = _shade(self.color, 1.6)
        shift = (self.time * 40.0) % 14.0
        for i in (-1, 0, 1):
            ax = rect.centerx + i * 14 + (shift - 7) * d
            if ax < rect.x + 8 or ax > rect.right - 8:
                continue
            pts = [(ax - 4 * d, cy - 4), (ax, cy), (ax - 4 * d, cy + 4)]
            pygame.draw.lines(surf, light, False, pts, 2)


class BreakingPlatform(Platform):
    """Белая ломающаяся платформа: тонкие трещинки; после прыжка мгновенно разлетается."""
    kind = "breaking"
    color = PLAT_BREAKING

    def __init__(self, x, y, w=PLATFORM_W):
        super().__init__(x, y, w)
        # Волосяные трещинки — 2-3 ломаные, идущие от верхнего края вниз
        self.cracks = []
        for _ in range(random.randint(2, 3)):
            x0 = random.uniform(10, self.w - 10)
            self.cracks.append(_make_crack(self.w, self.h, x0, 0,
                                           random.randint(3, 4), (-6, 6), (2, 4)))
        self.wobble = 0.0                        # дрожание при касании

    def on_land(self, player, game):
        """Сначала прыжок (игрок НЕ падает!), затем разрушение."""
        if not self.alive:
            return
        super().on_land(player, game)
        self.break_apart(game, "jump")

    def draw_decor(self, surf, rect):
        """Трещинки серыми линиями и пара «сколов» по краям."""
        crack_col = (170, 170, 175)
        for pts in self.cracks:
            spts = [(rect.x + px, rect.y + py) for px, py in pts]
            pygame.draw.lines(surf, crack_col, False, spts, 1)
        # маленькие сколы
        pygame.draw.circle(surf, _shade(self.color, 0.8), (rect.x + 6, rect.bottom - 5), 2)
        pygame.draw.circle(surf, _shade(self.color, 0.8), (rect.right - 7, rect.bottom - 4), 2)


class CrumblingPlatform(Platform):
    """Коричневая хрупкая платформа: после касания трескается в 3 стадии, мигает красным и обваливается."""
    kind = "crumbling"
    color = PLAT_CRUMBLING

    def __init__(self, x, y, w=PLATFORM_W):
        super().__init__(x, y, w)
        self.cracking = False
        self.timer = 0.0
        self.stage = 0
        self.blink_phase = 0.0
        self.blink_on = False
        self.jitter_x = 0.0
        self.jitter_y = 0.0
        self.dust_timer = 0.0
        self.chips = []                          # мелкие ямки-щербинки (dx, dy)
        for _ in range(random.randint(3, 5)):
            self.chips.append((random.uniform(6, self.w - 6), random.uniform(4, self.h - 3)))
        self.cracks = self._make_stage_cracks()

    def _make_stage_cracks(self):
        """Трещины по стадиям: [стадия1, стадия2, стадия3] — списки ломаных."""
        w, h = self.w, self.h
        center = random.uniform(w * 0.35, w * 0.65)
        stage1 = [_make_crack(w, h, center, 0, 3, (-5, 5), (3, 5))]
        stage2 = [
            _make_crack(w, h, center, h * 0.4, 3, (-9, -3), (-1, 3), x_bias=-2),
            _make_crack(w, h, center, h * 0.5, 3, (3, 9), (-1, 3), x_bias=2),
        ]
        stage3 = [
            _make_crack(w, h, random.uniform(6, w * 0.3), 0, 3, (-4, 6), (3, 5)),
            _make_crack(w, h, random.uniform(w * 0.7, w - 6), 0, 3, (-6, 4), (3, 5)),
            _make_crack(w, h, center, h - 1, 2, (-8, 8), (-4, -2)),
        ]
        return [stage1, stage2, stage3]

    @property
    def progress(self):
        """Доля пути к обвалу: 0 — целая, 1 — обваливается."""
        if not self.cracking or CRUMBLE_TIME <= 0:
            return 0.0
        return max(0.0, min(1.0, 1.0 - self.timer / CRUMBLE_TIME))

    @property
    def sagging(self):
        """Время трещин вышло: плашка «проваливается» (ещё CRUMBLE_GRACE с держит одно приземление)."""
        return self.cracking and self.timer <= 0.0

    def on_land(self, player, game):
        """Прыжок как обычно; при первом касании запускается таймер обвала.
        Приземление на уже проваливающуюся плашку — последний прыжок: игрок
        отталкивается (НЕ падает), и она тут же рассыпается."""
        if not self.alive:
            return
        super().on_land(player, game)
        if self.sagging:
            self.break_apart(game, "crumble")
            return
        if not self.cracking:
            self.cracking = True
            self.timer = CRUMBLE_TIME
            self.stage = 1                   # первая трещина — сразу, в кадре касания
            game.sound.play("crack", 0.5)
            particles = getattr(game, "particles", None)
            if particles is not None:
                particles.dust(self.cx, self.top + self.h, 5)

    def update(self, dt, game):
        """Таймер обвала, стадии трещин, ускоряющееся мигание, дрожание и крошки."""
        super().update(dt, game)
        if not self.cracking or not self.alive:
            return
        self.timer -= dt
        p = self.progress
        # первая трещина видна сразу при касании, дальше — по времени (1..CRUMBLE_STAGES)
        self.stage = min(CRUMBLE_STAGES, 1 + int(p * CRUMBLE_STAGES))
        # Мигание красным: частота растёт от ~3 Гц до ~16 Гц по мере приближения обвала
        freq = 3.0 + 13.0 * p * p
        self.blink_phase += dt * freq
        self.blink_on = (int(self.blink_phase * 2.0) % 2) == 0
        # Дрожание на поздних стадиях
        if self.stage >= 2:
            amp = 0.6 * self.stage
            self.jitter_x = random.uniform(-amp, amp)
            self.jitter_y = random.uniform(-amp * 0.5, amp * 0.5) + self.stage * 0.7
        else:
            self.jitter_x = 0.0
            self.jitter_y = self.stage * 0.7
        if self.sagging and CRUMBLE_GRACE > 0:
            # «проваливается»: плашка заметно оседает вниз перед тем, как рассыпаться
            self.jitter_y += 7.0 * min(1.0, -self.timer / CRUMBLE_GRACE)
        # Сыплющиеся крошки
        self.dust_timer -= dt
        if self.dust_timer <= 0.0:
            self.dust_timer = max(0.04, 0.18 - 0.14 * p)
            particles = getattr(game, "particles", None)
            if particles is not None:
                particles.dust(self.x + random.uniform(4, self.w - 4), self.top + self.h, 1)
        if self.timer <= -CRUMBLE_GRACE:
            self.break_apart(game, "crumble")

    def draw_color(self):
        """Красная подсветка при мигании (во время «провала» — сплошная)."""
        if self.cracking and (self.blink_on or self.sagging):
            return lerp_color(self.color, RED, 0.55)
        return self.color

    def plate_rect(self, cam_y):
        """Плашка с дрожанием и лёгким проседанием."""
        rect = super().plate_rect(cam_y)
        rect.x += int(round(self.jitter_x))
        rect.y += int(round(self.jitter_y))
        return rect

    def draw_decor(self, surf, rect):
        """Щербинки, трещины по стадиям, красное свечение при мигании."""
        dark = _shade(self.color, 0.55)
        for dx, dy in self.chips:
            pygame.draw.circle(surf, dark, (int(rect.x + dx), int(rect.y + dy)), 2)
        # Пара горизонтальных «слоёв» земли
        pygame.draw.line(surf, _shade(self.color, 0.85), (rect.x + 6, rect.y + 8), (rect.right - 6, rect.y + 8), 1)
        crack_col = DARK_BROWN if not (self.cracking and self.blink_on) else (60, 20, 15)
        for s in range(min(self.stage, len(self.cracks))):
            width = 2 if s < 2 else 3
            for pts in self.cracks[s]:
                spts = [(rect.x + px, rect.y + py) for px, py in pts]
                pygame.draw.lines(surf, crack_col, False, spts, width)
        if self.cracking and self.blink_on:
            # Красная рамка-предупреждение
            pygame.draw.rect(surf, RED, rect, width=2, border_radius=6)


class SpringPlatform(Platform):
    """Жёлтая платформа с пружиной: супер-прыжок x2.5, пружина сжимается при прыжке."""
    kind = "spring"
    color = PLAT_SPRING

    def __init__(self, x, y, w=PLATFORM_W):
        super().__init__(x, y, w)
        self.compress = 0.0                      # 1 — полностью сжата, 0 — в покое
        self.bounce_phase = 0.0                  # фаза «дрожания» пружины после распрямления

    def bounce_power(self):
        """Прыжок в SPRING_MULT раз сильнее обычного."""
        return JUMP_POWER * SPRING_MULT

    def on_land(self, player, game):
        """Супер-прыжок, сжатие пружины, звук, крышка, фраза, искры."""
        if not self.alive:
            return
        super().on_land(player, game)
        self.compress = 1.0
        self.bounce_phase = 0.0
        game.sound.play("spring")
        game.add_caps(1, self.cx, self.top - 20)
        game.say("spring")
        particles = getattr(game, "particles", None)
        if particles is not None:
            particles.sparks(self.cx, self.top - 10, 10, GOLD)

    def update(self, dt, game):
        """Пружина распрямляется за SPRING_COMPRESS_TIME и чуть дрожит после."""
        super().update(dt, game)
        if self.compress > 0.0:
            self.compress = max(0.0, self.compress - dt / SPRING_COMPRESS_TIME)
            self.bounce_phase = 0.0
        elif self.bounce_phase < 1.0:
            self.bounce_phase = min(1.0, self.bounce_phase + dt / 0.5)

    def spring_height(self):
        """Текущая высота пружины (в px) с учётом сжатия и остаточного дрожания."""
        h = SPRING_HEIGHT * (1.0 - 0.75 * self.compress)
        if self.compress <= 0.0 and self.bounce_phase < 1.0:
            h += math.sin(self.bounce_phase * math.pi * 4) * 3 * (1 - self.bounce_phase)
        return max(4.0, h)

    def draw_above(self, surf, rect):
        """Зигзаг пружины и площадка сверху."""
        cx = rect.centerx
        base_y = rect.y + 1
        h = self.spring_height()
        top_y = base_y - h
        # Зигзаг: 5 звеньев
        n = 5
        pts = [(cx, base_y)]
        for i in range(1, n):
            side = 7 if i % 2 else -7
            pts.append((cx + side, base_y - h * i / n))
        pts.append((cx, top_y))
        pygame.draw.lines(surf, _shade(DARK_GRAY, 0.8), False, [(px + 1, py + 1) for px, py in pts], 3)
        pygame.draw.lines(surf, DARK_GRAY, False, pts, 3)
        pygame.draw.lines(surf, LIGHT_GRAY, False, pts, 1)
        # Площадка пружины
        board = pygame.Rect(cx - 15, int(top_y) - 6, 30, 7)
        pygame.draw.rect(surf, _shade(self.color, 0.6), pygame.Rect(board.x, board.y + 2, board.w, board.h), border_radius=3)
        pygame.draw.rect(surf, (90, 90, 100), board, border_radius=3)
        pygame.draw.rect(surf, (170, 170, 185), pygame.Rect(board.x + 3, board.y + 1, board.w - 6, 2), border_radius=1)
        pygame.draw.rect(surf, (50, 50, 60), board, width=1, border_radius=3)

    def draw_decor(self, surf, rect):
        """Болтики по краям плашки."""
        for bx in (rect.x + 8, rect.right - 8):
            pygame.draw.circle(surf, _shade(self.color, 0.6), (bx, rect.y + rect.h // 2), 3)
            pygame.draw.circle(surf, _shade(self.color, 1.3), (bx - 1, rect.y + rect.h // 2 - 1), 1)


class RocketPlatform(Platform):
    """Красная платформа с ракетой: запускает игрока в небо, а затем сгорает."""
    kind = "rocket"
    color = PLAT_ROCKET

    def __init__(self, x, y, w=PLATFORM_W):
        super().__init__(x, y, w)
        self.launched = False
        self.burning = False
        self.burn_timer = 0.0
        self.smoke_timer = random.uniform(0.3, 0.8)
        self.fire_timer = 0.0

    @property
    def burn_progress(self):
        """0 — не горит, 1 — догорела."""
        if not self.burning or ROCKET_BURN_TIME <= 0:
            return 0.0
        return max(0.0, min(1.0, 1.0 - self.burn_timer / ROCKET_BURN_TIME))

    def on_land(self, player, game):
        """Запуск ракеты (если ещё не улетела), иначе обычный прыжок с горящей плашки."""
        if not self.alive:
            return
        if self.launched:
            super().on_land(player, game)
            return
        self.launched = True
        self.landed += 1
        self.press = 1.0
        player.launch_rocket(game)
        game.add_caps(1, self.cx, self.top - 30)
        game.say("rocket")
        self.burning = True
        self.burn_timer = ROCKET_BURN_TIME
        particles = getattr(game, "particles", None)
        if particles is not None:
            particles.fire(self.cx, self.top, 12)
            particles.smoke(self.cx, self.top, 6)

    def update(self, dt, game):
        """Дымок в покое; после запуска — огонь по плашке и сгорание."""
        super().update(dt, game)
        if not self.alive:
            return
        particles = getattr(game, "particles", None)
        if self.burning:
            self.burn_timer -= dt
            self.fire_timer -= dt
            if particles is not None and self.fire_timer <= 0.0:
                self.fire_timer = 0.03
                fx = self.x + random.uniform(4, self.w - 4)
                particles.fire(fx, self.top + random.uniform(0, self.h), 3)
                if random.random() < 0.5:
                    particles.smoke(fx, self.top - 4, 1)
            if self.burn_timer <= 0.0:
                self.break_apart(game, "rocket")
            return
        # Ракета в покое пускает дымок из сопла (только если платформа на экране)
        self.smoke_timer -= dt
        if self.smoke_timer <= 0.0:
            self.smoke_timer = random.uniform(0.35, 0.7)
            cam_y = getattr(game, "cam_y", None)
            if particles is not None and (cam_y is None or self.on_screen(cam_y, 0)):
                particles.smoke(self.cx + random.uniform(-3, 3), self.top - 6, 1, (200, 200, 205))

    def draw_color(self):
        """Плашка чернеет по мере сгорания."""
        if self.burning:
            return lerp_color(self.color, (45, 35, 35), self.burn_progress)
        return self.color

    def debris_color(self):
        """Сгоревшая плашка разлетается тёмными (обугленными) осколками — как нарисована."""
        return self.draw_color()

    def break_apart(self, game, cause="rocket"):
        """Сгоревшая платформа: осколки тёмные, плюс всплеск огня."""
        if not self.alive:
            return
        particles = getattr(game, "particles", None)
        if particles is not None:
            particles.fire(self.cx, self.top, 10)
            particles.smoke(self.cx, self.top, 4)
        super().break_apart(game, cause)

    def draw_decor(self, surf, rect):
        """Жёлтые предупредительные полоски по краям."""
        stripe = _shade(PLAT_SPRING, 0.95) if not self.burning else _shade(self.color, 0.5)
        for bx in (rect.x + 5, rect.right - 11):
            pygame.draw.rect(surf, stripe, pygame.Rect(bx, rect.y + 4, 6, rect.h - 8), border_radius=2)

    def draw_above(self, surf, rect):
        """Ракета: корпус, носовой конус, стабилизаторы, иллюминатор и мерцающее пламя."""
        if self.launched:
            return
        cx = rect.centerx
        base_y = rect.y - 5                       # низ корпуса
        body_w, body_h = 16, 26
        body = pygame.Rect(cx - body_w // 2, base_y - body_h, body_w, body_h)
        # Пламя в покое: мерцает по длине и цвету
        flick = 0.5 + 0.5 * math.sin(self.time * 25.0 + self.phase)
        flame_len = 6 + 6 * flick
        flame_col = lerp_color(ORANGE, YELLOW, flick)
        flame_pts = [(cx - 4, base_y), (cx + 4, base_y), (cx, base_y + flame_len)]
        pygame.draw.polygon(surf, RED, [(cx - 5, base_y), (cx + 5, base_y), (cx, base_y + flame_len + 3)])
        pygame.draw.polygon(surf, flame_col, flame_pts)
        pygame.draw.polygon(surf, WHITE, [(cx - 2, base_y), (cx + 2, base_y), (cx, base_y + flame_len * 0.45)])
        # Стабилизаторы
        fin_col = _shade(self.color, 0.7)
        pygame.draw.polygon(surf, fin_col, [(body.left, base_y - 10), (body.left - 6, base_y + 2), (body.left, base_y)])
        pygame.draw.polygon(surf, fin_col, [(body.right, base_y - 10), (body.right + 6, base_y + 2), (body.right, base_y)])
        # Корпус
        pygame.draw.rect(surf, _shade(self.color, 0.75), body, border_radius=4)
        pygame.draw.rect(surf, self.color, pygame.Rect(body.x, body.y, body.w - 4, body.h), border_radius=4)
        pygame.draw.rect(surf, _shade(self.color, 1.3), pygame.Rect(body.x + 3, body.y + 4, 3, body.h - 8), border_radius=2)
        # Носовой конус
        nose = [(body.left, body.top + 1), (body.right, body.top + 1), (cx, body.top - 10)]
        pygame.draw.polygon(surf, _shade(self.color, 0.8), nose)
        pygame.draw.polygon(surf, WHITE, [(cx - 3, body.top - 4), (cx + 3, body.top - 4), (cx, body.top - 10)])
        # Иллюминатор
        wy = body.top + 10
        pygame.draw.circle(surf, (40, 40, 60), (cx, wy), 5)
        pygame.draw.circle(surf, CYAN, (cx, wy), 4)
        pygame.draw.circle(surf, WHITE, (cx - 1, wy - 1), 1)
        # Сопло
        pygame.draw.rect(surf, DARK_GRAY, pygame.Rect(cx - 5, base_y - 3, 10, 4), border_radius=1)
        # Обводка корпуса
        pygame.draw.rect(surf, _shade(self.color, 0.45), body, width=1, border_radius=4)


class PlatformDebris:
    """Осколок платформы: вращающийся прямоугольник, падает под гравитацией и растворяется."""

    __slots__ = ("x", "y", "vx", "vy", "rot", "rot_speed", "w", "h", "color", "life", "max_life", "active")

    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.rot = 0.0
        self.rot_speed = 0.0
        self.w = 8
        self.h = 6
        self.color = PLAT_NORMAL
        self.life = 0.0
        self.max_life = 1.0
        self.active = False

    def reset(self, x, y, vx, vy, w, h, color, life):
        """Запустить осколок заново из пула."""
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.w = max(2, int(w))
        self.h = max(2, int(h))
        self.color = color
        self.life = max(0.05, float(life))
        self.max_life = self.life
        self.rot = random.uniform(0.0, math.pi * 2)
        self.rot_speed = random.uniform(-9.0, 9.0)
        self.active = True

    def update(self, dt):
        """Полёт: гравитация, сопротивление, вращение, старение."""
        if not self.active:
            return
        self.vy = min(self.vy + GRAVITY * 0.9 * dt, MAX_FALL_SPEED)
        drag = max(0.0, 1.0 - DEBRIS_DRAG * dt)
        self.vx *= drag
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rot += self.rot_speed * dt
        self.life -= dt
        if self.life <= 0.0:
            self.active = False

    def corners(self, sx, sy):
        """Четыре угла повёрнутого прямоугольника в экранных координатах."""
        c, s = math.cos(self.rot), math.sin(self.rot)
        hw, hh = self.w / 2.0, self.h / 2.0
        pts = []
        for dx, dy in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)):
            pts.append((sx + dx * c - dy * s, sy + dx * s + dy * c))
        return pts

    def draw(self, surf, cam_y):
        """Повёрнутый прямоугольник с тёмной обводкой; затухает по life."""
        if not self.active:
            return
        sy = self.y - cam_y
        if sy < -40 or sy > SCREEN_H + 40 or self.x < -40 or self.x > SCREEN_W + 40:
            return
        t = self.life / self.max_life if self.max_life > 0 else 0.0
        alpha = int(255 * min(1.0, t * 2.0))     # последние 50% жизни — растворение
        pts = self.corners(self.x, sy)
        outline = _shade(self.color, 0.45)
        if alpha >= 250:
            pygame.draw.polygon(surf, self.color, pts)
            pygame.draw.polygon(surf, outline, pts, 1)
            return
        # Полупрозрачный осколок через маленькую SRCALPHA-поверхность
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        minx, miny = int(min(xs)) - 1, int(min(ys)) - 1
        bw = int(max(xs)) - minx + 2
        bh = int(max(ys)) - miny + 2
        if bw <= 0 or bh <= 0:
            return
        tmp = pygame.Surface((bw, bh), pygame.SRCALPHA)
        local = [(px - minx, py - miny) for px, py in pts]
        pygame.draw.polygon(tmp, (self.color[0], self.color[1], self.color[2], alpha), local)
        pygame.draw.polygon(tmp, (outline[0], outline[1], outline[2], alpha), local, 1)
        surf.blit(tmp, (minx, miny))


class DebrisPool:
    """Пул заранее созданных осколков: без аллокаций в игровом цикле."""

    def __init__(self, size=DEBRIS_POOL_SIZE):
        self.items = [PlatformDebris() for _ in range(max(1, int(size)))]
        self.cursor = 0

    def _acquire(self):
        """Найти свободный осколок (или переиспользовать самый старый, если пул переполнен)."""
        n = len(self.items)
        for _ in range(n):
            d = self.items[self.cursor]
            self.cursor = (self.cursor + 1) % n
            if not d.active:
                return d
        # Всё занято: забираем осколок с наименьшим остатком жизни
        return min(self.items, key=lambda it: it.life)

    def spawn(self, rect, color, count=None):
        """Разлёт осколков из прямоугольника rect (плашки) цветом color."""
        if rect is None:
            return
        if count is None:
            count = random.randint(*DEBRIS_COUNT)
        count = max(0, int(count))
        cx = rect.x + rect.w / 2.0
        cy = rect.y + rect.h / 2.0
        half_w = max(1.0, rect.w / 2.0)
        # «крупный» кусок для веса картинки входит в общее число осколков (6-10, не 7-11)
        big = count >= 4
        small = count - 1 if big else count
        for i in range(small):
            d = self._acquire()
            # Позиция внутри плашки; осколки у краёв разлетаются наружу
            px = rect.x + random.uniform(4, max(4, rect.w - 4))
            py = rect.y + random.uniform(0, max(1, rect.h))
            side = (px - cx) / half_w                       # -1..1
            vx = side * random.uniform(90, 220) + random.uniform(-70, 70)
            vy = random.uniform(-380, -120)
            w = random.uniform(7, 18)
            h = random.uniform(4, max(5, rect.h * 0.7))
            shade = random.uniform(0.8, 1.12)
            life = random.uniform(0.8, 1.5)
            d.reset(px, py, vx, vy, w, h, _shade(color, shade), life)
        # Один «крупный» кусок для веса картинки
        if big:
            d = self._acquire()
            d.reset(cx + random.uniform(-10, 10), cy, random.uniform(-60, 60), random.uniform(-300, -180),
                    random.uniform(16, 24), rect.h * 0.8, _shade(color, 0.9), random.uniform(1.0, 1.6))

    def update(self, dt):
        """Обновить только активные осколки."""
        for d in self.items:
            if d.active:
                d.update(dt)

    def draw(self, surf, cam_y):
        """Нарисовать активные осколки."""
        for d in self.items:
            if d.active:
                d.draw(surf, cam_y)

    def active_count(self):
        """Сколько осколков сейчас летит."""
        return sum(1 for d in self.items if d.active)

    def clear(self):
        """Погасить все осколки (например, при рестарте)."""
        for d in self.items:
            d.active = False


# ═══════════════════════════════════════════════════════════════════════════
# ═══ ЧАСТЬ 3: ИГРОК, ДЖЕТПАК, БОНУСЫ ═══
# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
#  ЧАСТЬ 3: ИГРОК, ДЖЕТПАК, БОНУСЫ
#  draw_doodler — единая функция отрисовки дудлера во всех 18 скинах
#  (используется игроком, меню, экраном скинов, рулеткой кейсов и HUD).
# ═══════════════════════════════════════════════════════════════════════════


# ───────────────────────────────────────────────────────────────────────────
#  Вспомогательные примитивы с прозрачностью
# ───────────────────────────────────────────────────────────────────────────
def _p3_shade(color, k):
    """Затемнить (k<1) или осветлить (k>1) цвет, с защитой от None."""
    if color is None:
        color = WHITE
    return (int(clamp(color[0] * k, 0, 255)),
            int(clamp(color[1] * k, 0, 255)),
            int(clamp(color[2] * k, 0, 255)))


def _p3_rgba(color, alpha):
    """Собрать RGBA-кортеж из цвета и альфы."""
    return (int(color[0]), int(color[1]), int(color[2]), int(clamp(alpha, 0, 255)))


def _p3_alpha_circle(surf, cx, cy, r, color, alpha, width=0):
    """Полупрозрачный круг через маленькую SRCALPHA-поверхность."""
    r = int(r)
    if r <= 0 or alpha <= 0:
        return
    s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
    pygame.draw.circle(s, _p3_rgba(color, alpha), (r + 1, r + 1), r, int(width))
    surf.blit(s, (int(cx) - r - 1, int(cy) - r - 1))


def _p3_alpha_ellipse(surf, rect, color, alpha, width=0):
    """Полупрозрачный эллипс в прямоугольнике rect (x, y, w, h)."""
    x, y, w, h = rect
    w, h = int(w), int(h)
    if w <= 0 or h <= 0 or alpha <= 0:
        return
    s = pygame.Surface((w + 2, h + 2), pygame.SRCALPHA)
    pygame.draw.ellipse(s, _p3_rgba(color, alpha), (1, 1, w, h), int(width))
    surf.blit(s, (int(x) - 1, int(y) - 1))


def _p3_alpha_polygon(surf, pts, color, alpha, width=0):
    """Полупрозрачный многоугольник (по ограничивающему прямоугольнику)."""
    if len(pts) < 3 or alpha <= 0:
        return
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, y0 = int(min(xs)) - 2, int(min(ys)) - 2
    w, h = int(max(xs)) - x0 + 3, int(max(ys)) - y0 + 3
    if w <= 0 or h <= 0:
        return
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    local = [(int(px - x0), int(py - y0)) for px, py in pts]
    pygame.draw.polygon(s, _p3_rgba(color, alpha), local, int(width))
    surf.blit(s, (x0, y0))


def _p3_star_points(cx, cy, r_out, r_in, n=5, rot=-math.pi / 2):
    """Вершины n-лучевой звезды."""
    pts = []
    for i in range(n * 2):
        r = r_out if i % 2 == 0 else r_in
        a = rot + i * math.pi / n
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def _p3_flame(surf, x, y, w, h, t, seed=0.0, direction=1):
    """Анимированный язык пламени (3 слоя: красный → оранжевый → жёлтый).
    direction=1 — пламя вниз (джетпак), -1 — вверх (огненный скин)."""
    if w <= 1 or h <= 1:
        return
    flick = 0.78 + 0.22 * math.sin(t * 29.0 + seed * 3.1) + 0.08 * math.sin(t * 47.0 + seed)
    sway = math.sin(t * 17.0 + seed * 2.3) * w * 0.25
    for layer, col in enumerate(P3_FLAME_COLORS):
        k = (1.0, 0.68, 0.38)[layer]
        lw = w * k
        lh = h * flick * k
        tip = (x + sway * k, y + direction * lh)
        pts = [(x - lw / 2, y),
               (x - lw * 0.36, y + direction * lh * 0.45),
               tip,
               (x + lw * 0.36, y + direction * lh * 0.45),
               (x + lw / 2, y)]
        pygame.draw.polygon(surf, col, [(int(px), int(py)) for px, py in pts])
        pygame.draw.circle(surf, col, (int(x), int(y)), max(1, int(lw / 2)))


def _p3_jetpack_body(surf, cx, cy, turbo, t, scale=1.0, flame=True, flame_power=1.0):
    """Баллон джетпака (красный / золотой турбо) с нозлом и пламенем снизу.
    Рисуется вертикально, центр баллона в (cx, cy)."""
    s = scale
    col = P3_JET_TURBO_COLOR if turbo else P3_JET_COLOR
    dark = _p3_shade(col, 0.55)
    w, h = 16 * s, 30 * s
    # пламя под нозлом
    if flame and flame_power > 0.02:
        fl_h = (20 if turbo else 16) * s * flame_power
        _p3_flame(surf, cx, cy + h / 2 + 5 * s, 11 * s * flame_power, fl_h, t, seed=cx * 0.01, direction=1)
    # баллон
    rect = pygame.Rect(int(cx - w / 2), int(cy - h / 2), int(w), int(h))
    draw_rounded_rect(surf, rect, col, radius=max(2, int(6 * s)), width=0)
    draw_rounded_rect(surf, rect, dark, radius=max(2, int(6 * s)), width=max(1, int(2 * s)))
    # верхняя «крышка» баллона
    pygame.draw.ellipse(surf, _p3_shade(col, 1.15),
                        (int(cx - w * 0.35), int(cy - h / 2 - 2 * s), int(w * 0.7), int(6 * s)))
    # блик слева
    pygame.draw.line(surf, _p3_shade(col, 1.45),
                     (int(cx - w * 0.28), int(cy - h * 0.35)), (int(cx - w * 0.28), int(cy + h * 0.25)),
                     max(1, int(2 * s)))
    # тёмная полоса посередине
    pygame.draw.rect(surf, dark, (int(cx - w / 2), int(cy - 1 * s), int(w), max(1, int(3 * s))))
    # нозл
    pygame.draw.rect(surf, P3_METAL_DARK,
                     (int(cx - 5 * s), int(cy + h / 2 - 1), int(10 * s), max(1, int(5 * s))))
    pygame.draw.rect(surf, P3_METAL,
                     (int(cx - 4 * s), int(cy + h / 2 + 1 * s), int(8 * s), max(1, int(2 * s))))


def _p3_heli_hat(surf, cx, cy, t, scale=1.0, facing=1):
    """Шапка-вертолёт: кепка с козырьком, стержень и вращающийся пропеллер.
    (cx, cy) — центр нижнего края кепки (макушка головы)."""
    s = scale
    cap_w, cap_h = 30 * s, 14 * s
    # кепка — верхняя половина эллипса
    pts = []
    for i in range(13):
        a = math.pi + i * math.pi / 12
        pts.append((cx + math.cos(a) * cap_w / 2, cy + math.sin(a) * cap_h))
    pygame.draw.polygon(surf, P3_HELI_CAP, [(int(px), int(py)) for px, py in pts])
    pygame.draw.polygon(surf, _p3_shade(P3_HELI_CAP, 0.6), [(int(px), int(py)) for px, py in pts], max(1, int(2 * s)))
    # белая полоска по центру кепки
    pygame.draw.line(surf, WHITE, (int(cx), int(cy - cap_h + 2 * s)), (int(cx), int(cy - 1)), max(1, int(3 * s)))
    # козырёк вперёд
    brim = pygame.Rect(0, 0, int(14 * s), int(5 * s))
    brim.midleft = (int(cx + facing * cap_w * 0.28), int(cy - 1 * s)) if facing > 0 else (int(cx - cap_w * 0.28 - 14 * s), int(cy - 1 * s))
    pygame.draw.ellipse(surf, _p3_shade(P3_HELI_CAP, 0.75), brim)
    # стержень
    pygame.draw.rect(surf, P3_METAL_DARK, (int(cx - 1.5 * s), int(cy - cap_h - 8 * s), max(1, int(3 * s)), int(9 * s)))
    # пропеллер: эллипс, ширина которого «крутится» через cos(t)
    rot_y = cy - cap_h - 8 * s
    spin = math.cos(t * 22.0)
    blade_w = max(3 * s, abs(spin) * 40 * s)
    # размытый диск вращения
    _p3_alpha_ellipse(surf, (cx - 20 * s, rot_y - 2.5 * s, 40 * s, 5 * s), LIGHT_GRAY, 60)
    pygame.draw.ellipse(surf, (240, 240, 245), (int(cx - blade_w / 2), int(rot_y - 2 * s), int(blade_w), max(2, int(4 * s))))
    pygame.draw.circle(surf, P3_METAL_DARK, (int(cx), int(rot_y)), max(1, int(2.5 * s)))


def _p3_bucket(surf, cx, cy, scale=1.0):
    """Перевёрнутое металлическое ведро на голове. (cx, cy) — центр нижнего края (обода)."""
    s = scale
    bot_w, top_w, h = 36 * s, 26 * s, 26 * s
    pts = [(cx - bot_w / 2, cy), (cx - top_w / 2, cy - h), (cx + top_w / 2, cy - h), (cx + bot_w / 2, cy)]
    ipts = [(int(px), int(py)) for px, py in pts]
    pygame.draw.polygon(surf, P3_METAL, ipts)
    # тёмные обручи
    for k in (0.35, 0.7):
        yy = cy - h * k
        ww = bot_w + (top_w - bot_w) * k
        pygame.draw.line(surf, P3_METAL_DARK, (int(cx - ww / 2), int(yy)), (int(cx + ww / 2), int(yy)), max(1, int(2 * s)))
    # блик
    pygame.draw.line(surf, (215, 225, 235), (int(cx - bot_w * 0.3), int(cy - 3 * s)), (int(cx - top_w * 0.3), int(cy - h + 3 * s)), max(1, int(3 * s)))
    pygame.draw.polygon(surf, (60, 68, 75), ipts, max(1, int(2 * s)))
    # обод (внизу — на голове)
    pygame.draw.rect(surf, P3_METAL_DARK, (int(cx - bot_w / 2 - 2 * s), int(cy - 2 * s), int(bot_w + 4 * s), max(2, int(4 * s))))
    # дно ведра (сверху) и ручка-дуга
    pygame.draw.ellipse(surf, _p3_shade(P3_METAL, 1.1), (int(cx - top_w / 2), int(cy - h - 3 * s), int(top_w), int(6 * s)))
    pygame.draw.arc(surf, (60, 68, 75), (int(cx - 9 * s), int(cy - h - 12 * s), int(18 * s), int(16 * s)), 0.15, math.pi - 0.15, max(1, int(2 * s)))


def _p3_crown(surf, cx, cy, scale=1.0, t=0.0):
    """Золотая корона с самоцветами. (cx, cy) — центр нижнего края."""
    s = scale
    w, h = 30 * s, 16 * s
    pts = [(cx - w / 2, cy), (cx - w / 2, cy - h * 0.55)]
    spikes = 5
    for i in range(spikes):
        x0 = cx - w / 2 + w * i / spikes
        x1 = cx - w / 2 + w * (i + 0.5) / spikes
        pts.append((x1, cy - h if i in (0, 2, 4) else cy - h * 0.8))
        pts.append((x0 + w / spikes, cy - h * 0.55))
    pts.append((cx + w / 2, cy))
    ipts = [(int(px), int(py)) for px, py in pts]
    pygame.draw.polygon(surf, GOLD, ipts)
    pygame.draw.polygon(surf, (170, 120, 20), ipts, max(1, int(2 * s)))
    gems = ((RED, -0.3), ((70, 200, 90), 0.0), (BLUE, 0.3))
    for col, off in gems:
        gx = cx + off * w
        pygame.draw.circle(surf, col, (int(gx), int(cy - h * 0.3)), max(1, int(2.5 * s)))
    # блик на короне мерцает
    if int(t * 3) % 3 == 0:
        pygame.draw.circle(surf, WHITE, (int(cx + w * 0.35), int(cy - h * 0.8)), max(1, int(1.5 * s)))


def _p3_sparkle(surf, cx, cy, r, color):
    """Маленькая четырёхлучевая искорка."""
    r = max(1, int(r))
    pygame.draw.line(surf, color, (int(cx - r), int(cy)), (int(cx + r), int(cy)), 1)
    pygame.draw.line(surf, color, (int(cx), int(cy - r)), (int(cx), int(cy + r)), 1)


# ───────────────────────────────────────────────────────────────────────────
#  ГЛАВНАЯ ФУНКЦИЯ: дудлер во всех скинах
# ───────────────────────────────────────────────────────────────────────────
def draw_doodler(surf, cx, cy, skin, t, facing=1, squash=1.0, tilt=0.0, scale=1.0,
                 alpha=255, jetpack=None, heli=False, shield=False, star=False, look=None, dizzy=False):
    """Рисует дудлера по центру (cx, cy) экранных координат в заданном скине.

    Всё рисуется на локальный SRCALPHA-холст в «единичных» координатах
    (тело ~40×46), затем холст поворачивается на tilt и накладывается с alpha.
    squash<1 — сжат (шире и ниже), >1 — растянут (уже и выше).
    """
    if skin is None:
        skin = SKINS_BY_ID.get(DEFAULT_SKIN, SKINS[0])
    facing = 1 if facing >= 0 else -1
    scale = max(0.05, float(scale))
    squash = clamp(float(squash), 0.5, 1.5)
    hf = squash                         # вертикальный коэффициент
    wf = 1.0 + (1.0 - squash) * 0.8     # горизонтальный коэффициент
    special = skin.get("special")
    body_col = skin.get("body") or rainbow(t * 0.6)
    nose_col = skin.get("nose") or rainbow(t * 0.6 + 0.12)
    accent = skin.get("accent") or WHITE
    outline_col = _p3_shade(body_col, 0.55)

    # Локальный холст
    size = int(200 * scale) + 4
    canvas = pygame.Surface((size, size), pygame.SRCALPHA)
    C = size / 2.0

    def P(ux, uy):
        """Единичные координаты -> координаты холста (с учётом squash и scale)."""
        return (C + ux * scale * wf, C + uy * scale * hf)

    def IP(ux, uy):
        px, py = P(ux, uy)
        return (int(px), int(py))

    def RX(r):
        return r * scale * wf

    def RY(r):
        return r * scale * hf

    def LW(w):
        return max(1, int(w * scale))

    f = facing
    # Тело: центр (0, -4), радиусы 20×23 (единичные)
    body_cx, body_cy = 0.0, -4.0
    brx, bry = 20.0, 23.0
    if special == "banana":
        brx, bry = 15.0, 26.0
    elif special == "cucumber":
        brx, bry = 16.0, 25.5
    elif special == "whale":
        brx, bry = 23.0, 21.5
    elif special == "orange":
        brx, bry = 22.0, 22.0
    elif special == "potato":
        brx, bry = 21.0, 22.0

    # ── 1. Свечение звезды (за всем) ──
    if star:
        pulse = 1.0 + 0.08 * math.sin(t * 9.0)
        draw_glow(canvas, C, C, 46 * scale * pulse, GOLD, alpha=80)
        for i in range(6):
            a = t * 2.5 + i * math.pi / 3
            sx_ = C + math.cos(a) * 40 * scale
            sy_ = C + math.sin(a) * 40 * scale * 0.85
            r = (2.0 + 1.5 * math.sin(t * 7 + i)) * scale
            pygame.draw.polygon(canvas, (255, 240, 150), [(int(x), int(y)) for x, y in _p3_star_points(sx_, sy_, r * 2, r * 0.8, 4, t * 3)])

    # Свечение имба-скинов
    if special in ("67", "52"):
        draw_glow(canvas, C, C, 34 * scale, accent, alpha=45)
    elif special == "6752":
        draw_glow(canvas, C, C, 36 * scale, rainbow(t * 1.5), alpha=55)
    elif special == "cyber":
        draw_glow(canvas, C, C, 30 * scale, accent, alpha=30)
    elif special == "fire":
        draw_glow(canvas, C, C - 10 * scale, 32 * scale, ORANGE, alpha=45)

    # ── 2. Задние детали: крылья дракона, хвост кита, хвост дракона ──
    if special == "dragon":
        flap = math.sin(t * 11.0) * 6.0
        wing_col = _p3_shade(body_col, 0.8)
        for side in (-1, 1):
            root = (side * 8, -6)
            pts = [P(*root), P(side * 30, -24 - flap), P(side * 36, -8 - flap * 0.5), P(side * 26, 4), P(side * 12, 6)]
            pygame.draw.polygon(canvas, wing_col, [(int(x), int(y)) for x, y in pts])
            pygame.draw.polygon(canvas, _p3_shade(body_col, 0.45), [(int(x), int(y)) for x, y in pts], LW(1.5))
            # прожилки крыла
            for tip in ((side * 30, -24 - flap), (side * 36, -8 - flap * 0.5), (side * 26, 4)):
                pygame.draw.line(canvas, _p3_shade(body_col, 0.45), IP(*root), IP(*tip), 1)
        # хвост назад
        tail = [P(-f * 14, 10), P(-f * 26, 6 + math.sin(t * 5) * 2), P(-f * 34, -2 + math.sin(t * 5) * 3)]
        pygame.draw.lines(canvas, body_col, False, [(int(x), int(y)) for x, y in tail], LW(4))
        tip_x, tip_y = tail[-1]
        spade = [(tip_x - f * 6 * scale, tip_y - 6 * scale), (tip_x + f * 3 * scale, tip_y), (tip_x - f * 6 * scale, tip_y + 6 * scale)]
        pygame.draw.polygon(canvas, accent, [(int(x), int(y)) for x, y in spade])
    if special == "whale":
        # хвост-плавник сзади
        tx = -f * 24
        fluke = [P(tx, -2), P(tx - f * 12, -12 + math.sin(t * 4) * 2), P(tx - f * 14, 0), P(tx - f * 12, 10 - math.sin(t * 4) * 2)]
        pygame.draw.polygon(canvas, body_col, [(int(x), int(y)) for x, y in fluke])
        pygame.draw.polygon(canvas, outline_col, [(int(x), int(y)) for x, y in fluke], LW(2))

    # ── 3. Джетпак на спине (сторона, противоположная facing) ──
    if jetpack is not None:
        turbo = bool(getattr(jetpack, "turbo", False))
        prog = getattr(jetpack, "progress", 1.0)
        thrust = clamp(getattr(jetpack, "thrust", 1.0), 0, 1)     # пламя гаснет вместе с тягой
        jx, jy = P(-f * 15, -2)
        _p3_jetpack_body(canvas, jx, jy, turbo, t, scale=scale, flame=True,
                         flame_power=(0.6 + 0.4 * clamp(prog, 0, 1)) * (0.3 + 0.7 * thrust))

    # ── 4. Ножки-палочки (четыре) ──
    leg_col = _p3_shade(body_col, 0.7) if special != "skull" else (200, 200, 200)
    bottom_y = body_cy + bry - 3
    dangle = clamp((hf - 1.0) * 3.0, -0.4, 0.6)   # при растяжении ножки вытягиваются
    for i, lx in enumerate((-12, -5, 5, 12)):
        wig = math.sin(t * 9.0 + i * 1.7) * 1.2
        foot_x = lx * 1.25 + wig
        foot_y = bottom_y + 9 + dangle * 4
        pygame.draw.line(canvas, leg_col, IP(lx, bottom_y), IP(foot_x, foot_y), LW(2.5))
        pygame.draw.circle(canvas, leg_col, IP(foot_x + f * 1.5, foot_y), LW(2))

    # ── 5. Тело ──
    body_rect = pygame.Rect(IP(body_cx - brx, body_cy - bry), (max(2, int(RX(brx * 2))), max(2, int(RY(bry * 2)))))
    body_pts = None
    if special in ("potato", "banana", "cucumber"):
        body_pts = []
        n = 36
        for i in range(n):
            a = i * 2 * math.pi / n
            r = 1.0
            ox = 0.0
            if special == "potato":
                r = 1.0 + 0.08 * math.sin(3 * a + 1.0) + 0.05 * math.sin(5 * a + 2.0) + 0.04 * math.cos(7 * a)
            elif special == "cucumber":
                r = 1.0 + 0.03 * math.sin(9 * a)
            elif special == "banana":
                ny = math.sin(a)
                ox = -f * 0.35 * brx * (ny * ny - 0.35)   # изгиб банана
            body_pts.append(P(body_cx + math.cos(a) * brx * r + ox, body_cy + math.sin(a) * bry * r))
        ipts = [(int(x), int(y)) for x, y in body_pts]
        pygame.draw.polygon(canvas, body_col, ipts)
        pygame.draw.polygon(canvas, outline_col, ipts, LW(2))
    else:
        pygame.draw.ellipse(canvas, body_col, body_rect)
        pygame.draw.ellipse(canvas, outline_col, body_rect, LW(2))
    # блик сверху
    hl_x, hl_y = P(body_cx - brx * 0.55, body_cy - bry * 0.75)
    _p3_alpha_ellipse(canvas, (hl_x, hl_y, RX(brx * 0.5), RY(bry * 0.28)), WHITE, 70)

    # ── 6. Декор на теле по скину ──
    if special == "potato":
        for (px, py, rr) in ((-8, 4, 2.2), (6, 10, 1.8), (10, -12, 1.6), (-12, -10, 1.5)):
            pygame.draw.ellipse(canvas, _p3_shade(body_col, 0.6), (*IP(body_cx + px - rr, body_cy + py - rr * 0.7), max(2, int(RX(rr * 2))), max(2, int(RY(rr * 1.4)))))
    elif special == "banana":
        # коричневые кончики
        for ty_, rr in ((body_cy - bry + 1, 3.5), (body_cy + bry - 1, 3.0)):
            pygame.draw.ellipse(canvas, DARK_BROWN, (*IP(body_cx - rr - f * 0.35 * brx * 0.65, ty_ - 2.5), max(2, int(RX(rr * 2))), max(2, int(RY(5)))))
        for (px, py) in ((-5, 8), (4, 14), (-3, -14)):
            pygame.draw.circle(canvas, (150, 110, 30), IP(body_cx + px, body_cy + py), LW(1.5))
    elif special == "cucumber":
        for i in range(14):
            a = i * 2.39996 + 0.5
            rr = 0.25 + 0.6 * ((i * 7) % 10) / 10.0
            px = body_cx + math.cos(a) * brx * rr
            py = body_cy + math.sin(a) * bry * rr
            pygame.draw.circle(canvas, (150, 220, 130), IP(px, py), LW(1.6))
        for k in (-0.5, 0.0, 0.5):
            pygame.draw.line(canvas, _p3_shade(body_col, 0.75), IP(body_cx + k * brx * 0.9, body_cy - bry * 0.7), IP(body_cx + k * brx * 0.9, body_cy + bry * 0.7), 1)
    elif special == "whale":
        # светлое брюшко
        _p3_alpha_ellipse(canvas, (*P(body_cx - brx * 0.7, body_cy + bry * 0.1), RX(brx * 1.4), RY(bry * 0.8)), (200, 225, 255), 130)
    elif special == "orange":
        for i in range(8):
            a = i * math.pi / 4 + 0.2
            pygame.draw.line(canvas, _p3_shade(body_col, 0.8), IP(body_cx, body_cy), IP(body_cx + math.cos(a) * brx * 0.95, body_cy + math.sin(a) * bry * 0.95), 1)
        for i in range(10):
            a = i * 2.39996
            rr = 0.4 + 0.5 * ((i * 3) % 7) / 7.0
            pygame.draw.circle(canvas, _p3_shade(body_col, 0.88), IP(body_cx + math.cos(a) * brx * rr, body_cy + math.sin(a) * bry * rr), 1)
    elif special == "rainbow":
        for i in range(3):
            rr = pygame.Rect(IP(body_cx - brx * (0.8 - i * 0.22), body_cy - bry * (0.8 - i * 0.22)),
                             (max(2, int(RX(brx * 2 * (0.8 - i * 0.22)))), max(2, int(RY(bry * 2 * (0.8 - i * 0.22))))))
            pygame.draw.ellipse(canvas, rainbow(t * 0.6 + 0.2 + i * 0.18), rr, LW(2.5))
    elif special == "cyber":
        # неоновые линии-«схемы» на теле
        for (x0, y0, x1, y1) in ((-10, 4, -10, 14), (-10, 14, -2, 14), (6, 2, 12, 8), (12, 8, 12, 16), (0, 8, 0, 16)):
            pygame.draw.line(canvas, accent, IP(x0, y0), IP(x1, y1), LW(1.5))
        for (nx, ny_) in ((-10, 4), (-2, 14), (12, 16), (0, 8)):
            pygame.draw.circle(canvas, WHITE if int(t * 6 + nx) % 3 == 0 else accent, IP(nx, ny_), LW(1.8))
    elif special == "king":
        # мантия-воротник
        _p3_alpha_ellipse(canvas, (*P(body_cx - brx * 0.9, body_cy + bry * 0.35), RX(brx * 1.8), RY(bry * 0.6)), (200, 40, 60), 150)
        for k in (-0.5, -0.15, 0.2, 0.55):
            pygame.draw.circle(canvas, WHITE, IP(body_cx + k * brx * 1.6, body_cy + bry * 0.75), LW(1.5))
    elif special == "ice":
        for (px, py, rr) in ((-8, 2, 5), (7, 8, 4), (2, -6, 3)):
            pts = [(px, py - rr), (px + rr * 0.7, py), (px, py + rr), (px - rr * 0.7, py)]
            _p3_alpha_polygon(canvas, [P(body_cx + x, body_cy + y) for x, y in pts], WHITE, 120)
    elif special == "skull":
        # трещинка на черепе
        pygame.draw.lines(canvas, (120, 120, 120), False, [IP(-6, -24), IP(-4, -18), IP(-8, -14), IP(-5, -10)], 1)
    elif special in ("67", "52", "6752"):
        if special == "6752":
            text = "67" if int(t * 4) % 2 == 0 else "52"
            col = rainbow(t * 2.0)
            # радужный контур тела
            for i in range(12):
                a0 = i * math.pi / 6
                pygame.draw.arc(canvas, rainbow(t + i / 12.0), body_rect.inflate(LW(4), LW(4)), a0, a0 + math.pi / 6 + 0.05, LW(3))
        else:
            text = special
            col = accent if int(t * 8) % 2 == 0 else WHITE
        tx, ty = P(body_cx, body_cy + 8)
        draw_text(canvas, text, tx, ty, size=max(6, int(17 * scale)), color=col, anchor="center", bold=True, outline=BLACK)

    # ── 7. Нос (в сторону facing) ──
    if special != "skull":
        nose_w, nose_h = (16, 10) if special not in ("alien", "banana") else (11, 7)
        nose_x = body_cx + f * (brx * 0.75)
        nose_y = body_cy - 3
        nr = pygame.Rect(IP(nose_x - nose_w / 2 + f * nose_w * 0.45, nose_y - nose_h / 2), (max(2, int(RX(nose_w))), max(2, int(RY(nose_h)))))
        pygame.draw.ellipse(canvas, nose_col, nr)
        pygame.draw.ellipse(canvas, _p3_shade(nose_col, 0.6), nr, LW(1.5))
        pygame.draw.circle(canvas, _p3_shade(nose_col, 1.4), IP(nose_x + f * nose_w * 0.45 - f * 2, nose_y - nose_h * 0.3), LW(1.5))
    else:
        # носовое отверстие черепа — треугольник
        pts = [P(f * 7, -3), P(f * 10, 3), P(f * 4, 3)]
        pygame.draw.polygon(canvas, (30, 30, 30), [(int(x), int(y)) for x, y in pts])

    # ── 8. Глаза ──
    eye_y = body_cy - 7
    eye_xs = (f * 4 - 6, f * 4 + 6)
    # направление взгляда
    if look is not None:
        ldx, ldy = look[0] - cx, look[1] - cy
        ln = math.hypot(ldx, ldy)
        if ln > 1e-3:
            ldx, ldy = ldx / ln, ldy / ln
        else:
            ldx, ldy = f, 0.0
    else:
        ldx, ldy = f * 0.8, 0.15
    if special == "alien":
        for ex in eye_xs:
            er = pygame.Rect(IP(ex - 4.5, eye_y - 6), (max(2, int(RX(9))), max(2, int(RY(12)))))
            pygame.draw.ellipse(canvas, (15, 15, 20), er)
            pygame.draw.circle(canvas, WHITE, IP(ex + ldx * 1.5 - 1, eye_y - 3 + ldy), LW(1.6))
    elif special == "skull":
        for ex in eye_xs:
            er = pygame.Rect(IP(ex - 4.5, eye_y - 5), (max(2, int(RX(9))), max(2, int(RY(10)))))
            pygame.draw.ellipse(canvas, (25, 25, 25), er)
            glow_col = (255, 90, 60) if int(t * 2) % 2 == 0 else (255, 200, 80)
            pygame.draw.circle(canvas, glow_col, IP(ex + ldx * 2, eye_y + ldy * 2), LW(1.8))
    elif special == "cyber":
        vr = pygame.Rect(IP(f * 4 - 14, eye_y - 4.5), (max(2, int(RX(28))), max(2, int(RY(9)))))
        pygame.draw.rect(canvas, (10, 18, 28), vr, border_radius=LW(3))
        # бегущая световая линия по визору
        scan = (math.sin(t * 5.0) * 0.5 + 0.5)
        sx0 = vr.left + int(vr.w * scan)
        pygame.draw.line(canvas, accent, (sx0, vr.top + 2), (sx0, vr.bottom - 2), LW(2))
        pygame.draw.rect(canvas, accent, vr, LW(1.5), border_radius=LW(3))
        _p3_alpha_ellipse(canvas, (vr.left - 3, vr.top - 3, vr.w + 6, vr.h + 6), accent, 45)
    elif dizzy:
        # спиральки-глаза
        for ex in eye_xs:
            pygame.draw.circle(canvas, WHITE, IP(ex, eye_y), LW(5.5))
            pygame.draw.circle(canvas, BLACK, IP(ex, eye_y), LW(5.5), 1)
            for rr in (4.0, 2.5, 1.0):
                pygame.draw.arc(canvas, BLACK, (*IP(ex - rr * 0.5, eye_y - rr * 0.5), max(2, int(RX(rr))), max(2, int(RY(rr)))), t * 6 + rr, t * 6 + rr + 4.5, 1)
    else:
        for ex in eye_xs:
            pygame.draw.circle(canvas, WHITE, IP(ex, eye_y), LW(5.5))
            pygame.draw.circle(canvas, _p3_shade(body_col, 0.4), IP(ex, eye_y), LW(5.5), 1)
            pygame.draw.circle(canvas, BLACK, IP(ex + ldx * 2.2, eye_y + ldy * 2.2), LW(2.6))
            pygame.draw.circle(canvas, WHITE, IP(ex + ldx * 2.2 - 1, eye_y + ldy * 2.2 - 1), 1)

    # ── 9. Рот ──
    if special == "skull":
        # ряд зубов
        for i in range(4):
            tx_ = f * 3 - 8 + i * 4.5
            tr = pygame.Rect(IP(tx_, body_cy + 6), (max(2, int(RX(3.5))), max(2, int(RY(6)))))
            pygame.draw.rect(canvas, WHITE, tr)
            pygame.draw.rect(canvas, (40, 40, 40), tr, 1)
    else:
        mouth_open = squash < 0.85 or dizzy
        mr = pygame.Rect(IP(f * 8 - 5, body_cy + 3), (max(2, int(RX(10))), max(2, int(RY(7 if mouth_open else 5)))))
        if mouth_open:
            pygame.draw.ellipse(canvas, (60, 20, 30), mr)
        else:
            pygame.draw.arc(canvas, _p3_shade(body_col, 0.35), mr, math.pi, 2 * math.pi, LW(1.5))

    # ── 10. Головные уборы и особенности сверху ──
    top_y = body_cy - bry
    if special == "king":
        _p3_crown(canvas, *P(body_cx + f * 2, top_y + 3), scale=scale * hf, t=t)
    elif special == "trash":
        _p3_bucket(canvas, *P(body_cx, top_y + 9), scale=scale)
    elif special == "dragon":
        for side in (-1, 1):
            base = P(body_cx + side * 9, top_y + 4)
            tip = P(body_cx + side * 16, top_y - 12)
            pts = [(base[0] - 3 * scale, base[1]), (base[0] + 3 * scale, base[1]), tip]
            pygame.draw.polygon(canvas, accent, [(int(x), int(y)) for x, y in pts])
            pygame.draw.polygon(canvas, _p3_shade(accent, 0.6), [(int(x), int(y)) for x, y in pts], 1)
        # дымок из носа
        if int(t * 3) % 4 == 0:
            _p3_alpha_circle(canvas, *P(body_cx + f * 26, body_cy - 6), 3 * scale, LIGHT_GRAY, 120)
    elif special == "fire":
        for i, (fx, fw, fh) in enumerate(((-9, 9, 14), (0, 12, 20), (9, 9, 15))):
            bx, by = P(body_cx + fx, top_y + 4)
            _p3_flame(canvas, bx, by, fw * scale, fh * scale, t, seed=i * 1.7, direction=-1)
    elif special == "ice":
        # кристаллы сверху
        for (fx, fw, fh) in ((-8, 6, 11), (1, 8, 16), (9, 5, 9)):
            pts = [P(body_cx + fx - fw / 2, top_y + 3), P(body_cx + fx, top_y + 3 - fh), P(body_cx + fx + fw / 2, top_y + 3)]
            pygame.draw.polygon(canvas, (215, 245, 255), [(int(x), int(y)) for x, y in pts])
            pygame.draw.polygon(canvas, (120, 190, 240), [(int(x), int(y)) for x, y in pts], 1)
        # сосульки снизу
        for (fx, fh) in ((-10, 7), (-2, 10), (7, 6)):
            pts = [P(body_cx + fx - 2.5, body_cy + bry - 3), P(body_cx + fx + 2.5, body_cy + bry - 3), P(body_cx + fx, body_cy + bry - 3 + fh)]
            pygame.draw.polygon(canvas, (215, 245, 255), [(int(x), int(y)) for x, y in pts])
        # мерцающие искорки
        for i in range(3):
            if int(t * 4 + i * 1.3) % 3 == 0:
                _p3_sparkle(canvas, *P(body_cx + (-14, 12, 0)[i], body_cy + (-10, -14, 10)[i]), 3 * scale, WHITE)
    elif special == "alien":
        for side in (-1, 1):
            base = P(body_cx + side * 7, top_y + 4)
            tip = P(body_cx + side * 13, top_y - 12 + math.sin(t * 3 + side) * 1.5)
            pygame.draw.line(canvas, _p3_shade(body_col, 0.6), (int(base[0]), int(base[1])), (int(tip[0]), int(tip[1])), LW(2))
            pulse = 0.5 + 0.5 * math.sin(t * 6 + side * 1.5)
            _p3_alpha_circle(canvas, tip[0], tip[1], (4 + 3 * pulse) * scale, accent, 80)
            pygame.draw.circle(canvas, lerp_color(accent, WHITE, pulse), (int(tip[0]), int(tip[1])), LW(3))
    elif special == "orange":
        leaf = pygame.Rect(IP(body_cx + f * 2, top_y - 4), (max(2, int(RX(12))), max(2, int(RY(6)))))
        pygame.draw.ellipse(canvas, accent, leaf)
        pygame.draw.ellipse(canvas, _p3_shade(accent, 0.6), leaf, 1)
        pygame.draw.line(canvas, DARK_BROWN, IP(body_cx, top_y + 2), IP(body_cx, top_y - 4), LW(2))
    elif special == "whale":
        # фонтанчик из спины
        base = P(body_cx, top_y + 2)
        for i in range(5):
            ph = (t * 2.2 + i * 0.2) % 1.0
            dx = (i - 2) * 5 * ph * scale
            dy = -(6 + 14 * ph) * scale + ph * ph * 6 * scale
            _p3_alpha_circle(canvas, base[0] + dx, base[1] + dy, (2.5 - ph * 1.2) * scale, (190, 230, 255), int(220 * (1 - ph)))
    elif special == "cyber":
        # антенна с мигающим огоньком
        base = P(body_cx - f * 6, top_y + 3)
        tip = P(body_cx - f * 8, top_y - 9)
        pygame.draw.line(canvas, P3_METAL_DARK, (int(base[0]), int(base[1])), (int(tip[0]), int(tip[1])), LW(2))
        led = (255, 60, 60) if int(t * 4) % 2 == 0 else accent
        pygame.draw.circle(canvas, led, (int(tip[0]), int(tip[1])), LW(2.5))

    # Шапка-вертолёт (поверх любых головных уборов, кроме ведра — тогда над ведром)
    if heli:
        hat_y = top_y + 4 if special != "trash" else top_y - 20
        _p3_heli_hat(canvas, *P(body_cx, hat_y), t, scale=scale, facing=f)

    # ── 11. Щит-пузырь ──
    if shield:
        pulse = 1.0 + 0.04 * math.sin(t * 6.0)
        rr = 36 * scale * pulse
        _p3_alpha_circle(canvas, C, C - 2 * scale, rr, (120, 200, 255), 55)
        _p3_alpha_circle(canvas, C, C - 2 * scale, rr, (190, 235, 255), 170, width=LW(2))
        # блик пузыря
        pygame.draw.arc(canvas, (230, 250, 255), (int(C - rr * 0.8), int(C - 2 * scale - rr * 0.8), int(rr * 1.6), int(rr * 1.6)), math.pi * 0.6, math.pi * 0.95, LW(2))

    # ── 12. Головокружение (звёздочки над головой) ──
    if dizzy:
        for i in range(3):
            a = t * 5.0 + i * 2.094
            sx_ = C + math.cos(a) * 18 * scale
            sy_ = C - 36 * scale * hf + math.sin(a) * 5 * scale
            pts = _p3_star_points(sx_, sy_, 4.5 * scale, 2 * scale, 5, a)
            pygame.draw.polygon(canvas, YELLOW, [(int(x), int(y)) for x, y in pts])
            pygame.draw.polygon(canvas, (170, 130, 20), [(int(x), int(y)) for x, y in pts], 1)

    # ── Наклон и наложение на экран ──
    if abs(tilt) > 0.004:
        canvas = pygame.transform.rotozoom(canvas, -math.degrees(tilt), 1.0)
    if alpha < 255:
        canvas.set_alpha(int(clamp(alpha, 0, 255)))
    surf.blit(canvas, (int(cx - canvas.get_width() / 2), int(cy - canvas.get_height() / 2)))


# ───────────────────────────────────────────────────────────────────────────
#  ДЖЕТПАК (надетый) и ДЖЕТПАК-ПОДБИРАШКА
# ───────────────────────────────────────────────────────────────────────────
class Jetpack:
    """Надетый на спину джетпак: таймер, пламя, дым, лёгкая тряска."""

    def __init__(self, turbo=False):
        self.turbo = bool(turbo)
        self.total = TURBO_JETPACK_TIME if self.turbo else JETPACK_TIME
        self.time_left = self.total
        self.flame_t = 0.0
        self.shake_acc = 0.0
        self.smoke_acc = 0.0
        self.fire_acc = 0.0

    @property
    def progress(self):
        """Остаток заряда 0..1."""
        if self.total <= 0:
            return 0.0
        return clamp(self.time_left / self.total, 0.0, 1.0)

    @property
    def speed(self):
        return TURBO_JETPACK_SPEED if self.turbo else JETPACK_SPEED

    @property
    def thrust(self):
        """Доля тяги 1..0: полная, а последние JETPACK_EASE_TIME сек плавно спадает (smoothstep)."""
        if JETPACK_EASE_TIME <= 0 or self.time_left >= JETPACK_EASE_TIME:
            return 1.0
        u = clamp(self.time_left / JETPACK_EASE_TIME, 0.0, 1.0)
        return u * u * (3.0 - 2.0 * u)

    @property
    def current_speed(self):
        """Скорость подъёма сейчас: от полной (speed) к JETPACK_END_SPEED в конце полёта —
        джетпак не «обрывается», а мягко переходит в обычное падение."""
        return lerp(JETPACK_END_SPEED, self.speed, self.thrust)

    def update(self, dt, player, game):
        """Тикает таймер, испускает огонь и дым за спиной игрока, трясёт экран."""
        self.time_left -= dt
        self.flame_t += dt
        f = getattr(player, "facing", 1)
        nx = player.x - f * 15
        ny = player.y + 16
        # огонь из нозла — по аккумулятору времени (плотность не зависит от FPS и слоу-мо)
        self.fire_acc += dt
        while self.fire_acc >= P3_FIRE_INTERVAL:
            self.fire_acc -= P3_FIRE_INTERVAL
            game.particles.fire(nx, ny, 3 if self.turbo else 2)
            if self.turbo:
                game.particles.sparks(nx, ny + 6, 1, color=GOLD)
        # дымный шлейф
        self.smoke_acc += dt
        while self.smoke_acc >= 0.05:
            self.smoke_acc -= 0.05
            game.particles.smoke(nx + random.uniform(-4, 4), ny + 14, 1)
        # лёгкая тряска раз в 0.1 с
        self.shake_acc += dt
        while self.shake_acc >= 0.1:
            self.shake_acc -= 0.1
            game.shake(3 if self.turbo else 2, 0.1)


class JetpackPickup:
    """Летающий по уровню джетпак: плавает влево-вправо, пульсирует свечением."""

    def __init__(self, x, y, turbo=False):
        self.x = float(x)
        self.y = float(y)
        self.base_y = float(y)
        self.turbo = bool(turbo)
        self.rect = pygame.Rect(0, 0, 28, 40)
        self.rect.center = (int(x), int(y))
        self.alive = True
        self.vx = random.choice((-1, 1)) * random.uniform(60, 90)
        self.bob = random.uniform(0, math.pi * 2)
        self.time = random.uniform(0, 10)
        self.smoke_acc = 0.0

    def update(self, dt, game):
        self.time += dt
        self.bob += dt * 3.0
        self.x += self.vx * dt
        half = self.rect.w / 2 + 6
        if self.x < half:
            self.x = half
            self.vx = abs(self.vx)
        elif self.x > SCREEN_W - half:
            self.x = SCREEN_W - half
            self.vx = -abs(self.vx)
        self.y = self.base_y + math.sin(self.bob) * 8.0
        self.rect.center = (int(self.x), int(self.y))
        # редкий дымок сзади, только если на экране
        sy = self.y - game.cam_y
        if -60 < sy < SCREEN_H + 60:
            self.smoke_acc += dt
            if self.smoke_acc >= 0.25:
                self.smoke_acc = 0.0
                game.particles.smoke(self.x - (1 if self.vx > 0 else -1) * 10, self.y + 22, 1, color=(150, 150, 160))

    def draw(self, surf, cam_y):
        sx, sy = self.x, self.y - cam_y
        if sy < -80 or sy > SCREEN_H + 80:
            return
        pulse = 0.5 + 0.5 * math.sin(self.time * 5.0)
        glow_col = GOLD if self.turbo else (255, 130, 90)
        draw_glow(surf, sx, sy, 24 + 8 * pulse, glow_col, alpha=int(60 + 50 * pulse))
        _p3_jetpack_body(surf, sx, sy - 3, self.turbo, self.time, scale=1.0, flame=True, flame_power=0.55 + 0.15 * pulse)
        if self.turbo:
            # золотые искорки вокруг турбо
            for i in range(3):
                a = self.time * 3.0 + i * 2.094
                _p3_sparkle(surf, sx + math.cos(a) * 22, sy + math.sin(a) * 26, 2 + 2 * pulse, (255, 240, 170))

    def on_pickup(self, player, game):
        """Игрок подобрал: надеть джетпак и исчезнуть."""
        if not self.alive:
            return
        self.alive = False
        player.equip_jetpack(self.turbo, game)
        game.particles.sparks(self.x, self.y, 14, color=GOLD if self.turbo else ORANGE)
        if self.turbo:
            game.particles.confetti(self.x, self.y, 20)


# ───────────────────────────────────────────────────────────────────────────
#  ИГРОК
# ───────────────────────────────────────────────────────────────────────────
class Player:
    """Дудлер: движение с ускорением, телепорт через края, сжатие/растяжение,
    наклон, гравитация, джетпак/ракета/вертолёт, бонусы, след, звуки скина."""

    def __init__(self, skin):
        self.skin = skin if isinstance(skin, dict) else SKINS_BY_ID.get(DEFAULT_SKIN, SKINS[0])
        self.x = SCREEN_W / 2.0
        self.y = float(PLAYER_START_Y)
        self.vx = 0.0
        self.vy = 0.0
        self.rect = pygame.Rect(0, 0, PLAYER_W, PLAYER_H)
        self.rect.center = (int(self.x), int(self.y))
        self.prev_bottom = self.rect.bottom
        self.facing = 1
        self.squash = 1.0
        self.tilt = 0.0
        self.alive = True
        self.dying = False
        self.time = 0.0
        # бонусы и состояния
        self.jetpack = None
        self.rocket_time = 0.0
        self.heli_time = 0.0
        self.magnet_time = 0.0
        self.star_time = 0.0
        self.shield = False
        self.hurt_timer = 0.0
        # след
        self.trail = []             # [(x, y, life, color)]
        self.cap_trail = []         # мини-крышки для скина «Мусорный Дроппер»: [(x, y, life)]
        self.digit_trail = []       # цифры «67»/«52» ИМБА-скинов: [x, y, vx, vy, life, text, color, size]
        self.combo_trail_time = 0.0
        self.trail_acc = 0.0
        # служебное (перезарядку слоу-мо «67×52» ведёт только Game.slow_motion)
        self.jump_count = 0
        self.digits_toggle = False
        self.rocket_smoke_acc = 0.0
        self.rocket_fire_acc = 0.0
        self.star_fx_acc = 0.0
        self.magnet_fx_acc = 0.0
        self.trail_tick = 0         # счётчик точек следа (редкие доп. частицы — каждая N-я)

    # ── свойства ──
    @property
    def feet_rect(self):
        return pygame.Rect(int(self.x - 16), int(self.y + PLAYER_H / 2 - 6), 32, 12)

    @property
    def flying(self):
        return self.jetpack is not None or self.rocket_time > 0 or self.heli_time > 0

    @property
    def invincible(self):
        return self.star_time > 0 or self.jetpack is not None or self.rocket_time > 0 or self.hurt_timer > 0

    @staticmethod
    def wrap_rects(rect):
        """rect игрока и, если он пересекает край экрана, его копия у противоположного края
        (сдвиг на SCREEN_W): столкновения совпадают с тем, что нарисовано."""
        if rect.left < 0:
            return (rect, rect.move(SCREEN_W, 0))
        if rect.right > SCREEN_W:
            return (rect, rect.move(-SCREEN_W, 0))
        return (rect,)

    def draw_xs(self):
        """Экранные x, в которых рисуется дудлер: сам и копия у другого края, пока он
        «перетекает» через край (запас P3_WRAP_DRAW_MARGIN — на нос, крылья, джетпак)."""
        if self.x < P3_WRAP_DRAW_MARGIN:
            return (self.x, self.x + SCREEN_W)
        if self.x > SCREEN_W - P3_WRAP_DRAW_MARGIN:
            return (self.x, self.x - SCREEN_W)
        return (self.x,)

    # ── логика ──
    def _read_input(self, game):
        """Направление -1/0/1 с клавиатуры (стрелки, A/D) либо game.touch_dir."""
        d = 0
        try:
            keys = pygame.key.get_pressed()
            right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
            left = keys[pygame.K_LEFT] or keys[pygame.K_a]
            d = (1 if right else 0) - (1 if left else 0)
        except Exception:
            d = 0
        if d == 0:
            td = getattr(game, "touch_dir", 0)
            try:
                d = int(clamp(td, -1, 1))
            except Exception:
                d = 0
        return d

    def update(self, dt, game):
        # ВАЖНО: нижняя граница до перемещения — Game проверяет приземление по ней
        self.prev_bottom = self.rect.bottom
        self.time += dt
        if dt <= 0:
            return

        if self.dying:
            self._update_dying(dt, game)
            return

        # ── горизонтальное движение ──
        d = self._read_input(game)
        accel = PLAYER_ACCEL_JETPACK if self.jetpack is not None else PLAYER_ACCEL
        target = d * PLAYER_SPEED
        if d != 0:
            if self.vx < target:
                self.vx = min(target, self.vx + accel * dt)
            else:
                self.vx = max(target, self.vx - accel * dt)
        else:
            friction = accel * (0.55 if self.jetpack is not None else 1.0)
            if self.vx > 0:
                self.vx = max(0.0, self.vx - friction * dt)
            else:
                self.vx = min(0.0, self.vx + friction * dt)
        self.x += self.vx * dt

        # ── вертикальное движение ──
        if self.jetpack is not None:
            # сначала таймер, потом скорость: в последнем кадре полёта vy уже почти «обычная»
            self.jetpack.update(dt, self, game)
            self.vy = self.jetpack.current_speed
            if self.jetpack.time_left <= 0:
                self.detach_jetpack(game)
        elif self.rocket_time > 0:
            self.rocket_time -= dt
            # ракета: без гравитации, но тяга плавно спадает
            self.vy = lerp(self.vy, ROCKET_POWER * 0.45, min(1.0, 3.0 * dt))
            self.rocket_fire_acc += dt
            while self.rocket_fire_acc >= P3_FIRE_INTERVAL:
                self.rocket_fire_acc -= P3_FIRE_INTERVAL
                game.particles.fire(self.x - self.facing * 4, self.y + 22, 3)
            self.rocket_smoke_acc += dt
            while self.rocket_smoke_acc >= 0.04:
                self.rocket_smoke_acc -= 0.04
                game.particles.smoke(self.x + random.uniform(-6, 6), self.y + 30, 1)
        elif self.heli_time > 0:
            self.heli_time -= dt
            self.vy = lerp(self.vy, HELI_SPEED, min(1.0, 6.0 * dt))
            if self.heli_time <= 0:
                self.heli_time = 0.0
                game.effects.append(FallingHat(self.x, self.y - 30, self.facing))
        else:
            self.vy = min(self.vy + GRAVITY * dt, MAX_FALL_SPEED)
        self.y += self.vy * dt

        # ── телепорт через края ──
        # Период ровно SCREEN_W: пока тело торчит за край, у противоположного края
        # рисуется (и сталкивается) его копия — дудлер не пропадает с экрана ни на кадр
        if self.x < 0:
            self.x += SCREEN_W
        elif self.x >= SCREEN_W:
            self.x -= SCREEN_W

        # ── поза ──
        if abs(self.vx) > 25:
            self.facing = 1 if self.vx > 0 else -1
        tilt_target = clamp(self.vx / PLAYER_SPEED, -1, 1) * 0.25
        self.tilt = lerp(self.tilt, tilt_target, min(1.0, 10.0 * dt))
        if self.vy < -400:
            sq_target = 1.0 + min(0.15, (-self.vy - 400) / 4000.0)
        elif self.vy > 300:
            sq_target = 1.0 - min(0.08, (self.vy - 300) / 9000.0)
        else:
            sq_target = 1.0
        self.squash = lerp(self.squash, sq_target, min(1.0, 8.0 * dt))

        # ── таймеры бонусов ──
        self.magnet_time = max(0.0, self.magnet_time - dt)
        self.star_time = max(0.0, self.star_time - dt)
        self.hurt_timer = max(0.0, self.hurt_timer - dt)
        self.combo_trail_time = max(0.0, self.combo_trail_time - dt)
        # искры звезды и магнита — по аккумуляторам времени
        if self.star_time > 0:
            self.star_fx_acc += dt
            while self.star_fx_acc >= P3_STAR_SPARK_INTERVAL:
                self.star_fx_acc -= P3_STAR_SPARK_INTERVAL
                game.particles.sparks(self.x + random.uniform(-16, 16), self.y + random.uniform(-20, 20), 1, color=GOLD)
        else:
            self.star_fx_acc = 0.0
        if self.magnet_time > 0:
            self.magnet_fx_acc += dt
            while self.magnet_fx_acc >= P3_MAGNET_FX_INTERVAL:
                self.magnet_fx_acc -= P3_MAGNET_FX_INTERVAL
                game.particles.emit(self.x + random.uniform(-22, 22), self.y + random.uniform(-22, 22), 1,
                                    color=[(255, 80, 80), (80, 120, 255)], speed=(10, 40), life=(0.2, 0.4),
                                    size=(1, 3), gravity=0)
        else:
            self.magnet_fx_acc = 0.0

        # ── след ──
        self._update_trail(dt, game)

        self.rect.center = (int(self.x), int(self.y))

    def _update_dying(self, dt, game):
        """Game over: дудлер улетает вверх и крутится."""
        self.tilt += 7.0 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.squash = lerp(self.squash, 1.0, min(1.0, 5.0 * dt))
        self.rect.center = (int(self.x), int(self.y))
        for lst in (self.trail,):
            for i in range(len(lst)):
                x, y, life, col = lst[i]
                lst[i] = (x, y, life - dt, col)
        self.trail = [p for p in self.trail if p[2] > 0]
        self.cap_trail = [(x, y, life - dt) for (x, y, life) in self.cap_trail if life - dt > 0]
        self._age_digit_trail(dt)

    def _update_trail(self, dt, game):
        """Точки следа по типу скина + радужный след при комбо."""
        # старение
        if self.trail:
            self.trail = [(x, y, life - dt, col) for (x, y, life, col) in self.trail if life - dt > 0]
        if self.cap_trail:
            self.cap_trail = [(x, y, life - dt) for (x, y, life) in self.cap_trail if life - dt > 0]
        self._age_digit_trail(dt)

        trail_type = self.skin.get("trail")
        combo = self.combo_trail_time > 0
        if trail_type is None and not combo:
            return
        moving = abs(self.vy) > 60 or abs(self.vx) > 60
        if not moving:
            return
        self.trail_acc += dt
        if self.trail_acc < P3_TRAIL_INTERVAL:
            return
        self.trail_acc = 0.0
        self.trail_tick += 1
        tick = self.trail_tick
        bx = self.x - self.facing * 6 + random.uniform(-4, 4)
        by = self.y + 12 + random.uniform(-4, 4)
        accent = self.skin.get("accent") or WHITE

        if combo:
            self._add_trail_point(bx, by, rainbow(self.time * 1.5))
            if tick % 3 == 0:
                game.particles.emit(bx, by, 1, color=rainbow(self.time * 1.5 + 0.3), speed=(20, 80), life=(0.3, 0.6), size=(2, 4), gravity=0)
        if trail_type is None:
            return
        if trail_type == "fire":
            game.particles.fire(bx, by + 6, 2)
        elif trail_type == "smoke":
            game.particles.smoke(bx, by, 1, color=(90, 90, 100))
        elif trail_type == "gold":
            self._add_trail_point(bx, by, P3_TRAIL_COLORS["gold"])
            if tick % 4 == 0:
                game.particles.sparks(bx, by, 1, color=GOLD)
        elif trail_type == "bubbles":
            game.particles.emit(bx, by, 1, color=[(170, 215, 255), (220, 240, 255)], speed=(20, 60), life=(0.4, 0.9),
                                size=(2, 5), gravity=-250, shape="ring")
        elif trail_type in ("digits67", "digits52", "digits6752"):
            # реже обычного следа и позади по ходу движения; рисуются под телом —
            # мигающий номер на груди ИМБА-скина всегда виден
            if tick % P3_DIGIT_TRAIL_EVERY == 0:
                if trail_type == "digits6752":
                    self.digits_toggle = not self.digits_toggle
                    self._add_trail_digit("67" if self.digits_toggle else "52", rainbow(self.time * 2))
                else:
                    self._add_trail_digit("67" if trail_type == "digits67" else "52", accent)
        elif trail_type == "caps":
            self.cap_trail.append((bx, by, P3_TRAIL_LIFE * 1.3))
            if len(self.cap_trail) > 24:
                self.cap_trail.pop(0)
        elif trail_type == "rainbow":
            self._add_trail_point(bx, by, rainbow(self.time * 1.3))
        elif trail_type == "ice":
            self._add_trail_point(bx, by, P3_TRAIL_COLORS["ice"])
            if tick % 5 == 0:
                game.particles.emit(bx, by, 1, color=WHITE, speed=(10, 50), life=(0.2, 0.5), size=(1, 3), gravity=100, shape="spark")
        else:
            self._add_trail_point(bx, by, P3_TRAIL_COLORS.get(trail_type, accent))

    def _add_trail_digit(self, text, color):
        """Цифра следа: появляется позади дудлера (против направления движения)
        и медленно отплывает ещё дальше назад, растворяясь."""
        sp = math.hypot(self.vx, self.vy)
        if sp > 1e-3:
            ux, uy = -self.vx / sp, -self.vy / sp
        else:
            ux, uy = 0.0, 1.0
        dist = P3_DIGIT_TRAIL_OFFSET
        x = self.x + ux * dist + random.uniform(-5, 5)
        y = self.y + uy * dist + random.uniform(-5, 5)
        v = random.uniform(20.0, 60.0)
        size = random.randint(15, 22)
        self.digit_trail.append([x, y, ux * v + random.uniform(-15, 15), uy * v, P3_DIGIT_TRAIL_LIFE,
                                 str(text), tuple(color[:3]), size])
        if len(self.digit_trail) > P3_DIGIT_TRAIL_MAX:
            self.digit_trail.pop(0)

    def _age_digit_trail(self, dt):
        """Цифры следа: плывут со своей скоростью (с сопротивлением воздуха) и гаснут."""
        if not self.digit_trail:
            return
        drag = max(0.0, 1.0 - 1.5 * dt)
        for d in self.digit_trail:
            d[0] += d[2] * dt
            d[1] += d[3] * dt
            d[2] *= drag
            d[3] *= drag
            d[4] -= dt
        self.digit_trail = [d for d in self.digit_trail if d[4] > 0]

    def _add_trail_point(self, x, y, color):
        self.trail.append((x, y, P3_TRAIL_LIFE, color))
        if len(self.trail) > P3_TRAIL_MAX:
            self.trail.pop(0)

    # ── действия ──
    def jump(self, power, game):
        """Прыжок с платформы: скорость, сжатие, звук скина, спец-эффекты имба-скинов."""
        self.vy = power
        self.squash = 0.7
        self.jump_count += 1
        # Game мог поставить игрока на платформу прямо перед вызовом — синхронизируем rect
        self.rect.center = (int(self.x), int(self.y))
        special = self.skin.get("special")
        snd = self.skin.get("sound") or "jump"
        if special == "6752":
            snd = "six_seven" if self.jump_count % 2 else "five_two"
            # перезарядку (SLOWMO_COOLDOWN, реальное время) проверяет сам Game.slow_motion —
            # единственный таймер, иначе два расходящихся таймера растягивали паузу до ~21 с
            if hasattr(game, "slow_motion"):
                game.slow_motion()
        game.sound.play(snd)
        # редкие фразы под звук скина
        if special == "trash" and self.jump_count % 6 == 0:
            game.say("ding")
        elif special == "67" and self.jump_count % 7 == 0:
            game.say("six_seven")
        elif special == "52" and self.jump_count % 7 == 0:
            game.say("five_two")
        # пыль под ногами
        game.particles.dust(self.x, self.y + PLAYER_H / 2, 4)
        if special == "trash":
            game.particles.emit(self.x, self.y + PLAYER_H / 2, 3, color=[GRAY, LIGHT_GRAY], speed=(60, 160), life=(0.3, 0.6), size=(2, 4), gravity=700, shape="ring")

    def bounce_on_monster(self, game):
        """Отскок после прыжка на монстра."""
        self.vy = JUMP_POWER * 0.9
        self.squash = 0.75

    def launch_rocket(self, game):
        """Запуск с красной платформы-ракеты."""
        self.vy = ROCKET_POWER
        self.rocket_time = ROCKET_TRAIL_TIME
        self.squash = 1.2
        game.sound.play("rocket")
        game.shake(5, 0.35)
        game.particles.fire(self.x, self.y + 25, 12)
        game.particles.sparks(self.x, self.y + 25, 10, color=ORANGE)

    def equip_jetpack(self, turbo, game):
        """Надеть джетпак (подбор). Джетпак забирает полёт у ракеты целиком: иначе
        после его окончания недогоревшая ракета снова подбросила бы игрока вместо плавного падения."""
        self.jetpack = Jetpack(turbo)
        self.rocket_time = 0.0
        self.rocket_fire_acc = 0.0
        self.rocket_smoke_acc = 0.0
        game.sound.play("jetpack")
        game.shake(*SHAKE_JETPACK)
        game.say("jetpack")
        game.particles.sparks(self.x, self.y, 16, color=GOLD if turbo else ORANGE)

    def detach_jetpack(self, game):
        """Джетпак кончился: слетает со спины, начинается плавное падение.
        Скорость не обрывается: к этому моменту тяга уже плавно спала до JETPACK_END_SPEED
        (Jetpack.current_speed), дальше её гасит обычная гравитация. Недогоревшая ракета
        не возвращается, а короткая неуязвимость не даёт умереть в тот же кадр от монстра."""
        if self.jetpack is None:
            return
        turbo = self.jetpack.turbo
        game.effects.append(DetachedJetpack(self.x - self.facing * 15, self.y, self.facing, turbo))
        self.jetpack = None
        self.vy = max(self.vy, JETPACK_END_SPEED)
        self.rocket_time = 0.0
        self.hurt_timer = max(self.hurt_timer, JETPACK_END_GRACE)
        game.sound.play("jetpack_end")
        game.particles.smoke(self.x, self.y + 10, 4)

    def take_hit(self, game, source=None):
        """Урон от монстра/снаряда. Возвращает True, если игрок погиб."""
        if self.invincible:
            return False
        if self.shield:
            self.shield = False
            self.hurt_timer = SHIELD_INVULN
            # лопнувший пузырь
            game.particles.emit(self.x, self.y, 18, color=[(120, 200, 255), (200, 240, 255)], speed=(120, 260),
                                life=(0.3, 0.6), size=(2, 4), gravity=300, shape="ring")
            game.say("shield_lost")
            game.sound.play("shield")
            game.shake(4, 0.15)
            if source is not None and getattr(source, "killable", False) and hasattr(source, "die"):
                try:
                    source.die(game)
                except Exception:
                    pass
            return False
        game.sound.play("hit")
        game.begin_game_over("monster")
        return True

    def activate_bonus(self, kind, game):
        """Включить бонус: shield / heli / magnet / star."""
        if kind == "shield":
            self.shield = True
            game.sound.play("shield")
            game.particles.emit(self.x, self.y, 10, color=(150, 220, 255), speed=(40, 120), life=(0.3, 0.6), size=(2, 4), gravity=0, shape="ring")
        elif kind == "heli":
            self.heli_time = HELI_TIME
            game.sound.play("heli")
            self.vy = min(self.vy, HELI_SPEED)
        elif kind == "magnet":
            self.magnet_time = MAGNET_TIME
            game.sound.play("magnet")
        elif kind == "star":
            self.star_time = STAR_TIME
            game.sound.play("star")
            game.particles.sparks(self.x, self.y, 20, color=GOLD)
            game.shake(3, 0.2)
        if hasattr(game, "add_text"):
            names = {"shield": "ЩИТ!", "heli": "ВЕРТОЛЁТ!", "magnet": "МАГНИТ!", "star": "ЗВЕЗДА!"}
            if kind in names:
                game.add_text(names[kind], self.x, self.y - 40, color=YELLOW, size=24)

    # ── отрисовка ──
    def draw(self, surf, cam_y):
        sy = self.y - cam_y
        # след (рисуется всегда, даже если тело чуть за экраном)
        for (x, y, life, col) in self.trail:
            k = clamp(life / P3_TRAIL_LIFE, 0, 1)
            py = y - cam_y
            if -20 < py < SCREEN_H + 20:
                _p3_alpha_circle(surf, x, py, 2 + 5 * k, col, int(170 * k))
        for (x, y, life) in self.cap_trail:
            k = clamp(life / (P3_TRAIL_LIFE * 1.3), 0, 1)
            py = y - cam_y
            if -20 < py < SCREEN_H + 20:
                draw_cap_icon(surf, x, py, r=max(2, int(3 + 4 * k)))
        # цифры следа — до тела: дудлер (и номер на груди) всегда поверх них
        for (x, y, _vx, _vy, life, text, col, size) in self.digit_trail:
            k = clamp(life / P3_DIGIT_TRAIL_LIFE, 0, 1)
            py = y - cam_y
            if -30 < py < SCREEN_H + 30:
                draw_text(surf, text, x, py, size=size, color=col, bold=True, outline=BLACK, alpha=int(235 * k))
        if sy < -120 or sy > SCREEN_H + 120:
            return
        alpha = 255
        if self.hurt_timer > 0 and int(self.time * 20) % 2 == 0:
            alpha = 120
        for x in self.draw_xs():
            look = (x + self.facing * 40, sy + clamp(self.vy * 0.03, -20, 20))
            draw_doodler(surf, x, sy, self.skin, self.time, facing=self.facing, squash=self.squash, tilt=self.tilt,
                         scale=1.0, alpha=alpha, jetpack=self.jetpack, heli=self.heli_time > 0, shield=self.shield,
                         star=self.star_time > 0, look=look, dizzy=self.dying)


# ───────────────────────────────────────────────────────────────────────────
#  ЭФФЕКТЫ: слетевший джетпак, улетающая шапка
# ───────────────────────────────────────────────────────────────────────────
class DetachedJetpack:
    """Слетевший джетпак: падает, вращается, дымит, гаснет за 1.5 с."""

    screen = False

    def __init__(self, x, y, facing=1, turbo=False):
        self.x = float(x)
        self.y = float(y)
        self.vx = -facing * random.uniform(90, 150)
        self.vy = -random.uniform(150, 240)
        self.rot = 0.0
        self.rot_speed = -facing * random.uniform(360, 620)
        self.turbo = bool(turbo)
        self.max_life = 1.5
        self.life = self.max_life
        self.alive = True
        self.time = 0.0
        self.smoke_acc = 0.0
        self.fire_acc = 0.0

    def update(self, dt, game):
        self.time += dt
        self.life -= dt
        if self.life <= 0:
            self.alive = False
            return
        self.vy += GRAVITY * 0.8 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rot += self.rot_speed * dt
        self.smoke_acc += dt
        while self.smoke_acc >= 0.06:
            self.smoke_acc -= 0.06
            game.particles.smoke(self.x, self.y, 1)
        if self.life > 0.8:
            self.fire_acc += dt
            while self.fire_acc >= 0.05:          # ~20 огоньков в секунду, пока баллон «догорает»
                self.fire_acc -= 0.05
                game.particles.fire(self.x, self.y, 1)

    def draw(self, surf, cam_y):
        sy = self.y - cam_y
        if sy < -80 or sy > SCREEN_H + 80:
            return
        k = clamp(self.life / self.max_life, 0, 1)
        tmp = pygame.Surface((64, 84), pygame.SRCALPHA)
        _p3_jetpack_body(tmp, 32, 34, self.turbo, self.time, scale=1.0, flame=True, flame_power=max(0.0, (k - 0.4) / 0.6))
        rotated = pygame.transform.rotozoom(tmp, self.rot, 1.0)
        rotated.set_alpha(int(255 * min(1.0, k * 2.5)))
        surf.blit(rotated, (int(self.x - rotated.get_width() / 2), int(sy - rotated.get_height() / 2)))


class FallingHat:
    """Улетающая шапка-вертолёт: плывёт вверх и в сторону, вращается, тает."""

    screen = False

    def __init__(self, x, y, facing=1):
        self.x = float(x)
        self.y = float(y)
        self.facing = facing
        self.vx = facing * random.uniform(40, 90)
        self.vy = -random.uniform(120, 180)
        self.rot = 0.0
        self.rot_speed = -facing * random.uniform(120, 240)
        self.max_life = 1.6
        self.life = self.max_life
        self.alive = True
        self.time = 0.0

    def update(self, dt, game):
        self.time += dt
        self.life -= dt
        if self.life <= 0:
            self.alive = False
            return
        self.vy += 60 * dt          # чуть замедляется, но всё ещё плывёт вверх
        self.x += self.vx * dt + math.sin(self.time * 6) * 30 * dt
        self.y += self.vy * dt
        self.rot += self.rot_speed * dt

    def draw(self, surf, cam_y):
        sy = self.y - cam_y
        if sy < -80 or sy > SCREEN_H + 80:
            return
        k = clamp(self.life / self.max_life, 0, 1)
        tmp = pygame.Surface((72, 60), pygame.SRCALPHA)
        _p3_heli_hat(tmp, 36, 44, self.time, scale=1.0, facing=self.facing)
        rotated = pygame.transform.rotozoom(tmp, self.rot, 1.0)
        rotated.set_alpha(int(255 * min(1.0, k * 2.0)))
        surf.blit(rotated, (int(self.x - rotated.get_width() / 2), int(sy - rotated.get_height() / 2)))


# ───────────────────────────────────────────────────────────────────────────
#  БОНУСЫ
# ───────────────────────────────────────────────────────────────────────────
class Bonus:
    """Базовый бонус: покачивается, притягивается магнитом, светится."""

    kind = "bonus"
    glow_color = WHITE
    pickup_sound = "pickup"

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.rect = pygame.Rect(0, 0, 26, 26)
        self.rect.center = (int(x), int(y))
        self.alive = True
        self.bob = random.uniform(0, math.pi * 2)
        self.time = random.uniform(0, 10)
        self.attracted = False
        self.fx_acc = 0.0
        # платформа, над которой висит бонус (LevelGenerator): бонус едет вместе с ней
        self.platform = None
        self._plat_last_x = None

    def attach_to(self, platform):
        """Привязать бонус к платформе — он будет ездить вместе с движущейся платформой."""
        self.platform = platform
        self._plat_last_x = float(getattr(platform, "x", 0.0)) if platform is not None else None

    def _follow_platform(self):
        """Сдвинуться вместе с платформой (как Monster.follow_platform)."""
        p = self.platform
        if p is None:
            return
        if not getattr(p, "alive", True):
            self.platform = None          # платформа разрушена — бонус остаётся висеть на месте
            return
        try:
            px = float(p.x)
        except (AttributeError, TypeError, ValueError):
            self.platform = None
            return
        if self._plat_last_x is not None:
            self.x += px - self._plat_last_x
        self._plat_last_x = px

    @property
    def draw_y(self):
        """Экранное смещение покачивания (только визуальное)."""
        return math.sin(self.bob) * 4.0

    def update(self, dt, game):
        self.time += dt
        self.bob += dt * 3.0
        self.attracted = False
        player = getattr(game, "player", None)
        if player is not None and getattr(player, "magnet_time", 0) > 0 and not getattr(player, "dying", False):
            dx = player.x - self.x
            dy = player.y - self.y
            dist = math.hypot(dx, dy)
            if 1.0 < dist < MAGNET_RADIUS:
                self.attracted = True
                self.platform = None          # магнит сорвал бонус с платформы
                speed = 320.0 + (MAGNET_RADIUS - dist) * 3.5
                step = min(dist, speed * dt)
                self.x += dx / dist * step
                self.y += dy / dist * step
                # искорки притяжения — по аккумулятору времени (~15 в секунду)
                self.fx_acc += dt
                while self.fx_acc >= 1.0 / 15.0:
                    self.fx_acc -= 1.0 / 15.0
                    game.particles.emit(self.x, self.y, 1, color=self.glow_color, speed=(10, 40), life=(0.15, 0.35), size=(1, 3), gravity=0)
        if not self.attracted:
            self._follow_platform()
        self.rect.center = (int(self.x), int(self.y))

    def draw(self, surf, cam_y):
        sy = self.y - cam_y + self.draw_y
        if sy < -50 or sy > SCREEN_H + 50:
            return
        pulse = 0.5 + 0.5 * math.sin(self.time * 4.0)
        draw_glow(surf, self.x, sy, 16 + 4 * pulse, self.glow_color, alpha=int(45 + 35 * pulse))
        self.draw_icon(surf, self.x, sy)

    def draw_icon(self, surf, sx, sy):
        """Иконка бонуса примитивами — переопределяется в наследниках."""
        pygame.draw.circle(surf, self.glow_color, (int(sx), int(sy)), 10)

    def on_pickup(self, player, game):
        """Подбор: базовая часть — исчезнуть, звук, искры.
        pickup_sound = None — звук играет сам эффект (Player.activate_bonus), без дубля."""
        if not self.alive:
            return
        self.alive = False
        if self.pickup_sound:
            game.sound.play(self.pickup_sound)
        game.particles.sparks(self.x, self.y, 10, color=self.glow_color)
        self.apply(player, game)

    def apply(self, player, game):
        """Эффект бонуса — в наследниках."""
        pass


class CoinBonus(Bonus):
    """Золотая монетка: +10 очков и +1 крышка."""

    kind = "coin"
    glow_color = GOLD
    pickup_sound = "coin"

    def draw_icon(self, surf, sx, sy):
        spin = math.cos(self.time * 4.0)
        w = max(3, int(abs(spin) * 22))
        rect = pygame.Rect(int(sx - w / 2), int(sy - 11), w, 22)
        col = GOLD if spin >= 0 else (225, 170, 30)
        pygame.draw.ellipse(surf, col, rect)
        pygame.draw.ellipse(surf, (170, 120, 20), rect, 2)
        if w > 10:
            inner = rect.inflate(-max(2, int(w * 0.35)), -8)
            pygame.draw.ellipse(surf, (180, 130, 25), inner, 2)
            pygame.draw.line(surf, (255, 245, 200), (int(sx - w * 0.2), int(sy - 6)), (int(sx - w * 0.2), int(sy - 2)), 2)

    def apply(self, player, game):
        # «+10» левее, «+1» с крышкой правее и чуть ниже — две надписи не слипаются в «+10+1»
        tx = clamp(self.x - 16, 22, SCREEN_W - 72)
        game.add_score(10, tx, self.y)
        game.add_caps(1, tx + 30, self.y + 14)


class ShieldBonus(Bonus):
    """Голубой щит-пузырь."""

    kind = "shield"
    glow_color = (120, 200, 255)
    pickup_sound = None             # звук «shield» играет Player.activate_bonus (иначе — дважды в одном кадре)

    def draw_icon(self, surf, sx, sy):
        _p3_alpha_circle(surf, sx, sy, 12, (140, 210, 255), 110)
        pygame.draw.circle(surf, (200, 240, 255), (int(sx), int(sy)), 12, 2)
        # герб-щит внутри
        pts = [(sx - 6, sy - 6), (sx + 6, sy - 6), (sx + 6, sy), (sx, sy + 7), (sx - 6, sy)]
        pygame.draw.polygon(surf, (70, 140, 240), [(int(x), int(y)) for x, y in pts])
        pygame.draw.polygon(surf, WHITE, [(int(x), int(y)) for x, y in pts], 1)
        pygame.draw.line(surf, WHITE, (int(sx), int(sy - 4)), (int(sx), int(sy + 3)), 2)
        pygame.draw.arc(surf, WHITE, (int(sx - 9), int(sy - 9), 18, 18), math.pi * 0.6, math.pi * 0.95, 2)

    def apply(self, player, game):
        player.activate_bonus("shield", game)


class HelicopterBonus(Bonus):
    """Кепка с пропеллером."""

    kind = "heli"
    glow_color = (255, 140, 140)
    pickup_sound = None             # звук «heli» играет Player.activate_bonus (иначе — дважды в одном кадре)

    def draw_icon(self, surf, sx, sy):
        _p3_heli_hat(surf, sx, sy + 8, self.time, scale=0.8, facing=1)

    def apply(self, player, game):
        player.activate_bonus("heli", game)


class MagnetBonus(Bonus):
    """Красно-синий магнит-подкова."""

    kind = "magnet"
    glow_color = (255, 120, 120)
    pickup_sound = None             # звук «magnet» играет Player.activate_bonus (иначе — дважды в одном кадре)

    def draw_icon(self, surf, sx, sy):
        rect = pygame.Rect(int(sx - 10), int(sy - 11), 20, 20)
        # дуга подковы — красная, толстая
        pygame.draw.arc(surf, (220, 50, 50), rect, 0.0, math.pi, 6)
        pygame.draw.arc(surf, (220, 50, 50), rect.inflate(-1, -1), 0.05, math.pi - 0.05, 5)
        # ножки: красная и синяя
        pygame.draw.rect(surf, (220, 50, 50), (int(sx - 10), int(sy - 1), 6, 7))
        pygame.draw.rect(surf, (60, 110, 240), (int(sx + 4), int(sy - 1), 6, 7))
        # серебристые кончики
        pygame.draw.rect(surf, (225, 225, 235), (int(sx - 10), int(sy + 5), 6, 5))
        pygame.draw.rect(surf, (225, 225, 235), (int(sx + 4), int(sy + 5), 6, 5))
        # искорки притяжения
        if int(self.time * 6) % 2 == 0:
            _p3_sparkle(surf, sx - 12, sy + 12, 3, WHITE)
            _p3_sparkle(surf, sx + 12, sy + 12, 3, WHITE)

    def apply(self, player, game):
        player.activate_bonus("magnet", game)


class StarBonus(Bonus):
    """Жёлтая звезда неуязвимости."""

    kind = "star"
    glow_color = GOLD
    pickup_sound = None             # звук «star» играет Player.activate_bonus (иначе — дважды в одном кадре)

    def draw_icon(self, surf, sx, sy):
        rot = -math.pi / 2 + math.sin(self.time * 2.0) * 0.25
        pts = _p3_star_points(sx, sy, 13, 6, 5, rot)
        ipts = [(int(x), int(y)) for x, y in pts]
        pygame.draw.polygon(surf, YELLOW, ipts)
        pygame.draw.polygon(surf, (190, 140, 20), ipts, 2)
        pygame.draw.circle(surf, (255, 250, 210), (int(sx - 3), int(sy - 3)), 2)
        if int(self.time * 5) % 3 == 0:
            _p3_sparkle(surf, sx + 12, sy - 12, 4, WHITE)

    def apply(self, player, game):
        player.activate_bonus("star", game)


class PromoBonus(Bonus):
    """Билетик-промокод MusorDrop: +PROMO_CAPS крышек."""

    kind = "promo"
    glow_color = (255, 200, 120)
    pickup_sound = "promo"

    def draw_icon(self, surf, sx, sy):
        rect = pygame.Rect(int(sx - 22), int(sy - 9), 44, 18)
        tilt = math.sin(self.time * 3.0) * 2
        rect.y += int(tilt)
        draw_rounded_rect(surf, rect, (255, 235, 170), radius=4, width=0)
        draw_rounded_rect(surf, rect, (200, 120, 40), radius=4, width=2)
        # перфорация
        px = rect.left + 7
        for yy in range(rect.top + 3, rect.bottom - 2, 4):
            pygame.draw.circle(surf, (200, 120, 40), (px, yy), 1)
        # надпись — в поле справа от перфорации, размер подбирается, чтобы не вылезать за рамку
        left, right = rect.left + 10, rect.right - 3
        size = fit_text_size("PROMO", right - left, 10, 7, True)
        draw_text(surf, "PROMO", (left + right) // 2, rect.centery, size=size, color=(150, 60, 20),
                  anchor="center", bold=True)

    def apply(self, player, game):
        code = random.choice(PROMO_CODES) if PROMO_CODES else "BIGDROP"
        game.add_caps(PROMO_CAPS, self.x, self.y)
        # две строки: код крупно + «Промокод активирован! +50 крышек!» — обе влезают в 480 px
        game.say(f"ПРОМОКОД {code}!", color=GOLD, size=30)
        game.say(f"Промокод активирован! +{PROMO_CAPS} крышек!", color=YELLOW, size=22)
        game.particles.confetti(self.x, self.y, 24)


# ═══════════════════════════════════════════════════════════════════════════
# ═══ ЧАСТЬ 4: МОНСТРИКИ ═══
# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
#  ЧАСТЬ 4: МОНСТРИКИ
#  Ушастик, Призрак, Осьминожек (+ чернильная капля), Летучая мышь, НЛО и
#  пасхалка Чирик. Все монстры: зрачки следят за игроком (draw_eyes), смерть —
#  «ПЫХ!» со сплющиванием и брызгами, на game over машут лапкой.
#  Монстрик, стоящий на платформе, ломается вместе с ней (by_platform=True).
# ═══════════════════════════════════════════════════════════════════════════


# ───────────────────────────────────────────────────────────────────────────
#  Вспомогательные функции рисования (общие для всех монстров)
# ───────────────────────────────────────────────────────────────────────────
def monster_shade(color, k):
    """Осветлить (k > 0) или затемнить (k < 0) цвет; k в диапазоне [-1, 1]."""
    if k >= 0:
        return lerp_color(color, WHITE, min(1.0, k))
    return lerp_color(color, BLACK, min(1.0, -k))


def draw_rot_ellipse(surf, color, cx, cy, rw, rh, angle, width=0, steps=18):
    """Повёрнутый эллипс (полигон из steps точек). angle — в радианах."""
    ca, sa = math.cos(angle), math.sin(angle)
    pts = []
    for i in range(steps):
        a = 2.0 * math.pi * i / steps
        ex, ey = math.cos(a) * rw, math.sin(a) * rh
        pts.append((cx + ex * ca - ey * sa, cy + ex * sa + ey * ca))
    pygame.draw.polygon(surf, color, pts, width)


def draw_soft_shadow(surf, sx, sy, w, alpha=55):
    """Мягкая тень-овал под ножками монстрика."""
    w = max(6, int(w))
    h = max(4, w // 4)
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (0, 0, 0, alpha), s.get_rect())
    surf.blit(s, (int(sx - w / 2), int(sy - h / 2)))


def draw_blush(surf, sx, sy, spacing=12, r=5, color=(255, 140, 160), alpha=120):
    """Румяные щёчки — два полупрозрачных розовых овала."""
    w = int(spacing * 2 + r * 2 + 4)
    h = int(r * 2 + 2)
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    col = (color[0], color[1], color[2], alpha)
    for side in (-1, 1):
        cx = w / 2 + side * spacing
        pygame.draw.ellipse(s, col, (int(cx - r), 1, int(r * 2), int(r * 1.4)))
    surf.blit(s, (int(sx - w / 2), int(sy - h / 2)))


def draw_little_feet(surf, sx, sy, color, spread=10, size=6, bob=0.0, outline=None):
    """Две ножки-овальчика под телом. bob — «шаг» (одна ножка выше, другая ниже)."""
    for side in (-1, 1):
        fx = sx + side * spread
        fy = sy + bob * side
        rect = pygame.Rect(0, 0, int(size * 2), int(size))
        rect.center = (int(fx), int(fy))
        if outline is not None:
            pygame.draw.ellipse(surf, outline, rect.inflate(2, 2))
        pygame.draw.ellipse(surf, color, rect)


def draw_ufo_saucer(surf, sx, sy, t, look_dir=(0.0, -1.0), alpha=255, waving=False):
    """Летающая тарелка: стеклянный купол с зелёным пилотом, серебристый корпус,
    мигающие огоньки. Рисуется на SRCALPHA-поверхности (для прозрачного купола и
    общего затухания alpha при улёте)."""
    W, H = 80, 64
    g = pygame.Surface((W, H), pygame.SRCALPHA)
    cx, cy = W / 2.0, H / 2.0 + 4
    # свечение снизу
    draw_glow(g, cx, cy + 10, 14, (120, 230, 255), alpha=45)
    # купол
    dome = pygame.Rect(int(cx - 17), int(cy - 22), 34, 28)
    pygame.draw.ellipse(g, (150, 230, 255, 110), dome)
    pygame.draw.ellipse(g, (210, 245, 255, 200), dome, 2)
    # пилот — зелёный инопланетянин с антенной
    pygame.draw.line(g, (90, 190, 90), (cx, cy - 16), (cx + math.sin(t * 5) * 3, cy - 24), 2)
    pygame.draw.circle(g, (255, 120, 200), (int(cx + math.sin(t * 5) * 3), int(cy - 24)), 2)
    pygame.draw.circle(g, (80, 160, 80), (int(cx), int(cy - 9)), 8)
    pygame.draw.circle(g, (120, 220, 120), (int(cx), int(cy - 9)), 7)
    draw_eyes(g, cx, cy - 10, cx + look_dir[0] * 100, cy + look_dir[1] * 100,
              spacing=4, eye_r=3, pupil_r=2, color=WHITE, pupil=BLACK)
    if waving:
        ang = -1.2 + math.sin(t * 10) * 0.5
        hx, hy = cx + 10 + math.cos(ang) * 8, cy - 10 + math.sin(ang) * 8
        pygame.draw.line(g, (120, 220, 120), (cx + 7, cy - 8), (hx, hy), 3)
        pygame.draw.circle(g, (120, 220, 120), (int(hx), int(hy)), 3)
    # корпус
    body = pygame.Rect(int(cx - 28), int(cy - 6), 56, 18)
    pygame.draw.ellipse(g, (110, 115, 130), body.inflate(4, 4))
    pygame.draw.ellipse(g, (205, 210, 220), body)
    pygame.draw.ellipse(g, (150, 155, 172), (int(cx - 22), int(cy + 2), 44, 10))
    pygame.draw.ellipse(g, (240, 242, 248), (int(cx - 16), int(cy - 4), 14, 4))
    # огоньки по ободу — мигают вразнобой
    palette = [(255, 80, 80), (80, 255, 120), (255, 220, 80), (80, 170, 255), (255, 120, 255)]
    for i in range(5):
        lx = cx - 22 + 11 * i
        ly = cy + 3 + (2 if i in (0, 4) else 0)
        on = math.sin(t * 6 + i * 1.3) > 0
        col = palette[i]
        if on:
            draw_glow(g, lx, ly, 7, col, alpha=80)
            pygame.draw.circle(g, col, (int(lx), int(ly)), 3)
        else:
            pygame.draw.circle(g, monster_shade(col, -0.55), (int(lx), int(ly)), 2)
    if alpha < 255:
        g.fill((255, 255, 255, max(0, int(alpha))), special_flags=pygame.BLEND_RGBA_MULT)
    surf.blit(g, (int(sx - cx), int(sy - cy)))


# ───────────────────────────────────────────────────────────────────────────
#  Базовый монстрик
# ───────────────────────────────────────────────────────────────────────────
class Monster:
    """Базовый монстрик: хитбокс, слежение зрачками за игроком, смерть «пых»
    (сплющивание + брызги), гибель вместе с платформой, лапка на game over."""
    kind = "monster"
    killable = True
    friendly = False
    SIZE = (44, 44)              # размер хитбокса (w, h)
    body_color = PINK            # основной цвет (для брызг при смерти)
    splat_colors = None          # цвета брызг (None -> вычисляются из body_color)

    def __init__(self, x, y, platform=None):
        self.x = float(x)
        self.y = float(y)
        self.w, self.h = self.SIZE
        self.rect = pygame.Rect(0, 0, int(self.w), int(self.h))
        self.rect.center = (int(round(self.x)), int(round(self.y)))
        self.alive = True
        self.dying = False
        self.death_timer = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.time = random.uniform(0.0, 100.0)   # фаза анимации у каждого своя
        self.waving = False                       # машет лапкой (game over)
        self.look = (self.x, self.y - 200.0)      # мировая точка, куда смотрят зрачки
        self.platform = platform
        self.facing = random.choice((-1, 1))
        self.squash = 1.0                         # 1 — норма, <1 сжат, >1 растянут
        self.blink = 0.0                          # остаток моргания
        self.blink_timer = random.uniform(1.5, 4.0)
        self._look_dir = (0.0, -1.0)              # нормализованное направление взгляда
        self._plat_last_x = None
        if platform is not None and hasattr(platform, "rect"):
            self._plat_last_x = platform.rect.centerx

    # ── геометрия ──
    def sync_rect(self):
        """Синхронизировать rect с центром (x, y)."""
        self.rect.size = (int(self.w), int(self.h))
        self.rect.center = (int(round(self.x)), int(round(self.y)))

    @property
    def bottom(self):
        """Мировая y нижнего края (ножек)."""
        return self.y + self.h / 2.0

    def is_on_screen(self, cam_y, margin=60):
        """Виден ли монстрик на экране (по y)."""
        sy = self.y - cam_y
        return -margin <= sy <= SCREEN_H + margin

    def platform_top(self):
        """Верх платформы (или None, если платформы нет)."""
        p = self.platform
        if p is None:
            return None
        top = getattr(p, "top", None)
        if top is None and hasattr(p, "rect"):
            top = p.rect.top
        return top

    def follow_platform(self):
        """Ехать вместе с движущейся платформой."""
        p = self.platform
        if p is None or not hasattr(p, "rect"):
            return
        cx = p.rect.centerx
        if self._plat_last_x is not None:
            self.x += cx - self._plat_last_x
        self._plat_last_x = cx

    # ── логика ──
    def update(self, dt, game):
        """Базовое обновление. Наследники вызывают super().update(dt, game),
        затем проверяют self.dying и добавляют своё движение."""
        self.time += dt
        player = getattr(game, "player", None)
        if player is not None:
            self.look = (float(player.x), float(player.y))
        if self.dying:
            self.death_timer -= dt
            if self.death_timer <= 0.0:
                self.alive = False
            self.sync_rect()
            return
        # платформа под нами сломалась — ломаемся вместе с ней (комбо x2)
        if self.platform is not None and not getattr(self.platform, "alive", True):
            self.die(game, by_platform=True)
            self.sync_rect()
            return
        # моргание
        if self.blink > 0.0:
            self.blink -= dt
        else:
            self.blink_timer -= dt
            if self.blink_timer <= 0.0:
                self.blink = MONSTER_BLINK_TIME
                self.blink_timer = random.uniform(1.5, 4.5)
        # плавный возврат формы
        self.squash += (1.0 - self.squash) * min(1.0, dt * 10.0)
        self.sync_rect()

    def on_stomp(self, game):
        """Игрок прыгнул сверху — монстрик погибает."""
        self.die(game)

    def on_touch(self, player, game):
        """Столкновение не сверху — игрок получает удар."""
        player.take_hit(game, self)

    def die(self, game, by_platform=False):
        """Смерть: «ПЫХ!», брызги цветом монстра, звук, уведомление Game."""
        if self.dying or not self.alive:
            return
        self.dying = True
        self.death_timer = MONSTER_DEATH_TIME
        self.vx = 0.0
        self.vy = 0.0
        game.sound.play("squish")
        colors = self.splat_colors or [
            self.body_color,
            monster_shade(self.body_color, 0.45),
            monster_shade(self.body_color, -0.3),
        ]
        game.particles.emit(self.x, self.y, 18, color=colors, speed=(90, 280),
                            life=(0.35, 0.8), size=(3, 7), gravity=800)
        game.particles.emit(self.x, self.y, 5, color=WHITE, speed=(40, 120),
                            life=(0.2, 0.4), size=(2, 4), gravity=0, shape="ring")
        add_text = getattr(game, "add_text", None)
        if add_text is not None:
            add_text("ПЫХ!", self.x, self.y - self.h / 2.0 - 12, color=YELLOW, size=22, life=0.7)
        if random.random() < 0.2:
            game.say("squish")
        game.on_monster_killed(self, by_platform)

    # ── отрисовка ──
    def draw(self, surf, cam_y):
        """Общий каркас: проверка видимости, направление взгляда, сплющивание при смерти."""
        if not self.alive:
            return
        sy = self.y - cam_y
        if sy < -140 or sy > SCREEN_H + 140:
            return
        lx, ly = self.look[0] - self.x, self.look[1] - self.y
        d = math.hypot(lx, ly)
        self._look_dir = (lx / d, ly / d) if d > 1e-6 else (0.0, -1.0)
        if self.dying:
            self._draw_dying(surf, self.x, sy)
        else:
            self.draw_body(surf, self.x, sy)

    def draw_body(self, surf, sx, sy):
        """Рисунок тела по центру (sx, sy) экранных координат — переопределяют наследники."""
        c = self.body_color
        pygame.draw.circle(surf, monster_shade(c, -0.4), (int(sx), int(sy)), int(self.w / 2) + 2)
        pygame.draw.circle(surf, c, (int(sx), int(sy)), int(self.w / 2))
        self.draw_face(surf, sx, sy - 2)

    def _draw_dying(self, surf, sx, sy):
        """«ПЫХ!»: тело сплющивается (y -> 0.2, x -> 1.5) и тает по alpha за 0.4 с."""
        t = clamp(1.0 - self.death_timer / MONSTER_DEATH_TIME, 0.0, 1.0)
        ease = 1.0 - (1.0 - t) ** 2
        scale_x = lerp(1.0, 1.5, ease)
        scale_y = lerp(1.0, 0.2, ease)
        alpha = int(255 * (1.0 - t * t))
        W = int(self.w * 3) + 40
        H = int(self.h * 3) + 40
        temp = pygame.Surface((W, H), pygame.SRCALPHA)
        cx, cy = W / 2.0, H / 2.0
        self.draw_body(temp, cx, cy)
        nw = max(1, int(W * scale_x))
        nh = max(1, int(H * scale_y))
        scaled = pygame.transform.scale(temp, (nw, nh))
        if alpha < 255:
            scaled.fill((255, 255, 255, max(0, alpha)), special_flags=pygame.BLEND_RGBA_MULT)
        # низ тела остаётся на месте (сплющиваемся к ножкам)
        bottom_screen = sy + self.h / 2.0
        top = bottom_screen - (cy + self.h / 2.0) * scale_y
        surf.blit(scaled, (int(sx - nw / 2.0), int(top)))

    def draw_face(self, surf, sx, sy, spacing=10, eye_r=6, pupil_r=3, color=WHITE, pupil=BLACK, skin=None):
        """Глаза через draw_eyes, зрачки смотрят на игрока; иногда моргают."""
        dx, dy = self._look_dir
        if self.blink > 0.0:
            lid = skin if skin is not None else self.body_color
            for side in (-1, 1):
                ex = sx + side * spacing
                pygame.draw.circle(surf, lid, (int(ex), int(sy)), eye_r + 1)
                pygame.draw.line(surf, monster_shade(lid, -0.5),
                                 (int(ex - eye_r + 1), int(sy)), (int(ex + eye_r - 1), int(sy)), 2)
        else:
            draw_eyes(surf, sx, sy, sx + dx * 200.0, sy + dy * 200.0,
                      spacing=spacing, eye_r=eye_r, pupil_r=pupil_r, color=color, pupil=pupil)

    def draw_wave_arm(self, surf, sx, sy, color, length=16, side=None):
        """Поднятая лапка, качается sin(time*10) — «пока-пока» на game over."""
        if side is None:
            side = self.facing if self.facing else 1
        ang = -1.35 + math.sin(self.time * 10.0) * 0.45
        bx, by = sx + side * self.w * 0.42, sy
        ex = bx + math.cos(ang) * length * side
        ey = by + math.sin(ang) * length
        pygame.draw.line(surf, monster_shade(color, -0.4), (bx, by), (ex, ey), 6)
        pygame.draw.line(surf, color, (bx, by), (ex, ey), 4)
        pygame.draw.circle(surf, color, (int(ex), int(ey)), 4)


# ───────────────────────────────────────────────────────────────────────────
#  Ушастик — розово-фиолетовый шарик с большими ушами
# ───────────────────────────────────────────────────────────────────────────
class Ushastik(Monster):
    """Ушастик: стоит на платформе, подпрыгивает и ходит туда-сюда в её пределах.
    Убивается прыжком сверху."""
    kind = "ushastik"
    SIZE = (44, 48)
    body_color = (225, 120, 215)

    def __init__(self, x, y, platform=None):
        super().__init__(x, y, platform)
        self.speed = random.uniform(40.0, 80.0)
        self.vx = self.speed * self.facing
        self.hop_timer = random.uniform(0.5, 1.4)
        self.grounded = True
        self.ear_flop = 0.0
        top = self.platform_top()
        self.floor_y = float(top) if top is not None else self.bottom
        self.y = self.floor_y - self.h / 2.0
        self.sync_rect()

    def _floor(self):
        top = self.platform_top()
        return float(top) if top is not None else self.floor_y

    def _patrol_bounds(self):
        p = self.platform
        if p is not None and hasattr(p, "rect"):
            lo = p.rect.left + self.w * 0.35
            hi = p.rect.right - self.w * 0.35
            if lo > hi:
                lo = hi = p.rect.centerx
            return lo, hi
        return 30.0, SCREEN_W - 30.0

    def update(self, dt, game):
        super().update(dt, game)
        if self.dying or not self.alive:
            return
        self.follow_platform()
        floor = self._floor()
        if not self.waving:
            # патруль в пределах платформы
            self.x += self.vx * dt
            lo, hi = self._patrol_bounds()
            if self.x < lo:
                self.x = lo
                self.vx = abs(self.speed)
                self.facing = 1
            elif self.x > hi:
                self.x = hi
                self.vx = -abs(self.speed)
                self.facing = -1
            # подпрыгивание
            if self.grounded:
                self.hop_timer -= dt
                if self.hop_timer <= 0.0:
                    self.vy = -random.uniform(320.0, 460.0)
                    self.grounded = False
                    self.squash = 1.25
        if not self.grounded:
            self.vy = min(self.vy + GRAVITY * 0.9 * dt, MAX_FALL_SPEED)
            self.y += self.vy * dt
            if self.vy > 0.0 and self.bottom >= floor:
                self.y = floor - self.h / 2.0
                self.vy = 0.0
                self.grounded = True
                self.squash = 0.72
                self.hop_timer = random.uniform(0.5, 1.5)
        else:
            self.y = floor - self.h / 2.0
        # уши откидываются при прыжке
        self.ear_flop += ((-self.vy / 600.0) - self.ear_flop) * min(1.0, dt * 8.0)
        self.sync_rect()

    def draw_body(self, surf, sx, sy):
        c = self.body_color
        dark = monster_shade(c, -0.45)
        light = monster_shade(c, 0.45)
        inner_ear = (255, 190, 235)
        foot_color = (200, 90, 160)
        sqy = clamp(self.squash, 0.5, 1.4)
        sqx = 2.0 - sqy
        ry = 20.0 * sqy
        rx = 20.0 * sqx
        body_bottom = sy + 20.0
        body_cy = body_bottom - ry
        body_top = body_cy - ry
        draw_soft_shadow(surf, sx, sy + self.h / 2.0 + 1, 40 * sqx)
        # ножки
        walking = self.grounded and not self.waving
        bob = math.sin(self.time * 14.0) * 2.0 if walking else 0.0
        draw_little_feet(surf, sx, sy + 21, foot_color, spread=9 * sqx, size=6, bob=bob, outline=dark)
        # уши
        for side in (-1, 1):
            ang = side * (0.32 + self.ear_flop * 0.5) + math.sin(self.time * 3.0 + side) * 0.05
            ex = sx + side * 10.0 * sqx
            ey = body_top + 2.0 - 11.0
            draw_rot_ellipse(surf, dark, ex, ey, 9.5, 17.5, ang)
            draw_rot_ellipse(surf, c, ex, ey, 8.0, 16.0, ang)
            draw_rot_ellipse(surf, inner_ear, ex, ey - 1, 4.0, 10.0, ang)
        # тело
        body_rect = pygame.Rect(int(sx - rx), int(body_cy - ry), int(rx * 2), int(ry * 2))
        pygame.draw.ellipse(surf, dark, body_rect.inflate(4, 4))
        pygame.draw.ellipse(surf, c, body_rect)
        belly = pygame.Rect(int(sx - rx * 0.55), int(body_cy), int(rx * 1.1), int(ry * 0.85))
        pygame.draw.ellipse(surf, monster_shade(c, 0.22), belly)
        pygame.draw.ellipse(surf, light, (int(sx - rx * 0.6), int(body_cy - ry * 0.65), int(rx * 0.5), int(ry * 0.3)))
        # лицо
        face_y = body_cy - 3.0 * sqy
        self.draw_face(surf, sx, face_y, spacing=9, eye_r=6, pupil_r=3)
        draw_blush(surf, sx, face_y + 9, spacing=13, r=4, color=(255, 120, 150), alpha=130)
        # ротик «w»
        my = face_y + 9
        for side in (-1, 1):
            r = pygame.Rect(int(sx + side * 3 - 3), int(my - 2), 7, 6)
            pygame.draw.arc(surf, dark, r, math.pi, 2 * math.pi, 2)
        if self.waving:
            self.draw_wave_arm(surf, sx, body_cy, c)


# ───────────────────────────────────────────────────────────────────────────
#  Призрак — полупрозрачный, летит волной
# ───────────────────────────────────────────────────────────────────────────
class Ghost(Monster):
    """Призрак: белый полупрозрачный, летит по синусоиде, отскакивает от краёв. Убивается."""
    kind = "ghost"
    SIZE = (44, 52)
    body_color = (235, 235, 255)
    splat_colors = [(240, 240, 255), (200, 200, 240), (255, 255, 255)]

    def __init__(self, x, y, platform=None):
        super().__init__(x, y, platform)
        self.base_y = float(y)
        self.speed = random.uniform(60.0, 110.0)
        self.vx = self.speed * self.facing
        self.phase = random.uniform(0.0, math.tau)

    def update(self, dt, game):
        super().update(dt, game)
        if self.dying or not self.alive:
            return
        if not self.waving:
            self.x += self.vx * dt
            if self.x < 24.0:
                self.x = 24.0
                self.vx = abs(self.speed)
                self.facing = 1
            elif self.x > SCREEN_W - 24.0:
                self.x = SCREEN_W - 24.0
                self.vx = -abs(self.speed)
                self.facing = -1
        self.y = self.base_y + math.sin(self.time * 3.0 + self.phase) * 30.0
        self.sync_rect()

    def draw_body(self, surf, sx, sy):
        W, H = int(self.w + 28), int(self.h + 24)
        g = pygame.Surface((W, H), pygame.SRCALPHA)
        cx, cy = W / 2.0, H / 2.0
        r = 21.0
        top = cy - self.h / 2.0 + 2.0
        bottom = cy + self.h / 2.0 - 2.0
        pts = []
        for i in range(17):                       # купол-полукруг
            a = math.pi + math.pi * i / 16.0
            pts.append((cx + math.cos(a) * r, top + r + math.sin(a) * r))
        n = 14
        for i in range(n + 1):                    # волнистый низ (справа налево)
            xx = cx + r - (2.0 * r) * i / n
            yy = bottom - 6.0 + math.sin(xx * 0.45 + self.time * 7.0) * 5.0
            pts.append((xx, yy))
        pygame.draw.polygon(g, (240, 240, 255, 150), pts)
        pygame.draw.polygon(g, (205, 205, 245, 210), pts, 2)
        # ручки-обрубочки
        for side in (-1, 1):
            ay = cy + 2.0 + math.sin(self.time * 5.0 + side) * 3.0
            hand = pygame.Rect(0, 0, 12, 8)
            hand.center = (int(cx + side * (r + 3)), int(ay))
            pygame.draw.ellipse(g, (205, 205, 245, 210), hand.inflate(2, 2))
            pygame.draw.ellipse(g, (240, 240, 255, 170), hand)
        # лицо
        self.draw_face(g, cx, cy - 6, spacing=8, eye_r=6, pupil_r=3,
                       color=(250, 250, 255), pupil=(50, 50, 90), skin=(238, 238, 252))
        pygame.draw.ellipse(g, (70, 70, 120, 230), (int(cx - 4), int(cy + 6), 8, 10))
        draw_blush(g, cx, cy + 4, spacing=12, r=4, color=(255, 170, 205), alpha=110)
        if self.waving:
            self.draw_wave_arm(g, cx, cy, (235, 235, 255))
        surf.blit(g, (int(sx - cx), int(sy - cy)))


# ───────────────────────────────────────────────────────────────────────────
#  Осьминожек — стреляет чернилами
# ───────────────────────────────────────────────────────────────────────────
class Octopus(Monster):
    """Осьминожек: сидит на платформе, шевелит шестью щупальцами и каждые 1.8-2.6 с
    плюётся чернильной каплей в игрока (если тот в пределах 350 px). Убивается."""
    kind = "octopus"
    SIZE = (48, 46)
    body_color = (150, 80, 200)

    def __init__(self, x, y, platform=None):
        super().__init__(x, y, platform)
        self.shoot_timer = random.uniform(*OCTOPUS_SHOOT_INTERVAL)
        self.recoil = 0.0
        self.tentacle_phase = random.uniform(0.0, math.tau)
        self._snap_to_platform()
        self.sync_rect()

    def _snap_to_platform(self):
        top = self.platform_top()
        if top is not None:
            self.y = float(top) - self.h / 2.0 + 6.0

    def update(self, dt, game):
        super().update(dt, game)
        if self.dying or not self.alive:
            return
        self.follow_platform()
        self._snap_to_platform()
        if self.recoil > 0.0:
            self.recoil = max(0.0, self.recoil - dt * 3.0)
        if not self.waving:
            self.shoot_timer -= dt
            if self.shoot_timer <= 0.0:
                if not self._fully_visible(game):
                    # из-за края экрана не стреляем (нечестно), но выстрелим вскоре после появления
                    self.shoot_timer = random.uniform(*OCTOPUS_RETRY_DELAY)
                else:
                    self.shoot_timer = random.uniform(*OCTOPUS_SHOOT_INTERVAL)
                    self.try_shoot(game)
        self.sync_rect()

    def _fully_visible(self, game):
        """Тело осьминожка целиком на экране (по вертикали)."""
        return self.is_on_screen(float(getattr(game, "cam_y", 0.0) or 0.0), margin=-self.h / 2.0)

    def try_shoot(self, game):
        """Выстрелить каплей в игрока, если он в зоне досягаемости и сам осьминожек
        виден на экране. Возвращает True при выстреле."""
        p = getattr(game, "player", None)
        if p is None or not getattr(p, "alive", True) or getattr(p, "dying", False):
            return False
        if not self._fully_visible(game):
            return False
        dx = float(p.x) - self.x
        dy = float(p.y) - self.y
        dist = math.hypot(dx, dy)
        if dist > OCTOPUS_RANGE or dist < 1e-3:
            return False
        if dy < -150.0:                 # игрок слишком высоко над нами — не докинем
            return False
        # упреждение на гравитацию капли
        flight = dist / INK_SPEED
        vx = dx / dist * INK_SPEED
        vy = dy / dist * INK_SPEED - 0.5 * INK_GRAVITY * flight
        drop = InkDrop(self.x, self.y + 6.0, vx, vy)
        projectiles = getattr(game, "projectiles", None)
        if projectiles is not None:
            projectiles.append(drop)
        game.sound.play("shoot")
        game.particles.ink(self.x, self.y + 8.0, 5)
        self.recoil = 1.0
        self.facing = 1 if dx >= 0 else -1
        return True

    def draw_body(self, surf, sx, sy):
        c = self.body_color
        dark = monster_shade(c, -0.45)
        light = monster_shade(c, 0.4)
        draw_soft_shadow(surf, sx, sy + self.h / 2.0 + 2, 44)
        # щупальца (сзади) — волной, с сужением к кончику
        base_y = sy + 6.0
        for i in range(6):
            bx = sx - 17.5 + i * 7.0
            phase = self.time * 4.0 + i * 0.9 + self.tentacle_phase
            spread = (i - 2.5) * 0.9
            prev = None
            for k in range(5):
                yy = base_y + k * 5.5
                xx = bx + math.sin(phase + k * 0.7) * (1.5 + k * 1.5) + spread * k
                rad = max(2, int(6 - k * 0.9))
                if prev is not None:
                    pygame.draw.line(surf, dark, prev, (xx, yy), rad * 2 + 2)
                pygame.draw.circle(surf, dark, (int(xx), int(yy)), rad + 1)
                prev = (xx, yy)
            prev = None
            for k in range(5):
                yy = base_y + k * 5.5
                xx = bx + math.sin(phase + k * 0.7) * (1.5 + k * 1.5) + spread * k
                rad = max(1, int(6 - k * 0.9))
                col = c if k < 3 else monster_shade(c, 0.2)
                if prev is not None:
                    pygame.draw.line(surf, col, prev, (xx, yy), rad * 2)
                pygame.draw.circle(surf, col, (int(xx), int(yy)), rad)
                prev = (xx, yy)
        # голова (пружинит при выстреле)
        hw = 22.0 * (1.0 + self.recoil * 0.15) * (2.0 - clamp(self.squash, 0.5, 1.4))
        hh = 19.0 * (1.0 - self.recoil * 0.15) * clamp(self.squash, 0.5, 1.4)
        head_cy = sy - 6.0 + (19.0 - hh)
        head = pygame.Rect(int(sx - hw), int(head_cy - hh), int(hw * 2), int(hh * 2))
        pygame.draw.ellipse(surf, dark, head.inflate(4, 4))
        pygame.draw.ellipse(surf, c, head)
        for (ox, oy, rr) in ((-12, -8, 4), (13, -4, 3), (4, -14, 3)):
            pygame.draw.circle(surf, light, (int(sx + ox), int(head_cy + oy)), rr)
        pygame.draw.ellipse(surf, monster_shade(c, 0.6), (int(sx - 14), int(head_cy - hh + 4), 10, 5))
        # лицо
        face_y = head_cy - 1.0
        self.draw_face(surf, sx, face_y, spacing=10, eye_r=7, pupil_r=3)
        draw_blush(surf, sx, face_y + 9, spacing=15, r=4, color=(255, 130, 190), alpha=120)
        mw = 4.0 + self.recoil * 4.0
        mh = 3.0 + self.recoil * 3.0
        pygame.draw.ellipse(surf, (35, 25, 70), (int(sx - mw), int(face_y + 9 - mh), int(mw * 2), int(mh * 2)))
        if self.waving:
            self.draw_wave_arm(surf, sx, head_cy + 4, c, length=18)


class InkDrop:
    """Чернильная капля осьминожка — снаряд с лёгкой гравитацией и хвостиком."""
    kind = "ink"
    screen = False

    def __init__(self, x, y, vx, vy):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.rect = pygame.Rect(0, 0, 12, 12)
        self.rect.center = (int(self.x), int(self.y))
        self.alive = True
        self.life = INK_LIFE
        self.time = 0.0
        self.trail = []

    def update(self, dt, game):
        self.time += dt
        self.life -= dt
        self.vy += INK_GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.trail.append((self.x, self.y))
        if len(self.trail) > 5:
            self.trail.pop(0)
        self.rect.center = (int(self.x), int(self.y))
        cam_y = getattr(game, "cam_y", 0.0)
        sy = self.y - cam_y
        if self.life <= 0.0 or self.x < -40 or self.x > SCREEN_W + 40 or sy > SCREEN_H + 60 or sy < -300:
            self.alive = False

    def draw(self, surf, cam_y):
        if not self.alive:
            return
        sy = self.y - cam_y
        if sy < -40 or sy > SCREEN_H + 40:
            return
        for i, (tx, ty) in enumerate(self.trail):
            pygame.draw.circle(surf, (40, 50, 110), (int(tx), int(ty - cam_y)), 1 + int(i * 0.6))
        ang = math.atan2(self.vy, self.vx)
        draw_rot_ellipse(surf, (20, 28, 80), self.x, sy, 8.5, 5.5, ang)
        draw_rot_ellipse(surf, (45, 60, 150), self.x, sy, 7.0, 4.2, ang)
        pygame.draw.circle(surf, (130, 150, 230), (int(self.x - 2), int(sy - 2)), 2)


# ───────────────────────────────────────────────────────────────────────────
#  Летучая мышь — быстрая, неубиваемая
# ───────────────────────────────────────────────────────────────────────────
class Bat(Monster):
    """Летучая мышь: быстро летает, машет крыльями. Прыжком не убивается — любое
    касание = удар по игроку. Гибнет только от звезды/джетпака/ракеты."""
    kind = "bat"
    killable = False
    SIZE = (50, 30)
    body_color = (70, 55, 95)
    splat_colors = [(70, 55, 95), (120, 90, 150), (210, 60, 60)]

    def __init__(self, x, y, platform=None):
        super().__init__(x, y, platform)
        self.speed = random.uniform(260.0, 340.0)
        self.vx = self.speed * self.facing
        self.base_y = float(y)
        self.phase = random.uniform(0.0, math.tau)

    def update(self, dt, game):
        super().update(dt, game)
        if self.dying or not self.alive:
            return
        if not self.waving:
            self.x += self.vx * dt
            if self.x < 26.0:
                self.x = 26.0
                self.vx = abs(self.speed)
                self.facing = 1
            elif self.x > SCREEN_W - 26.0:
                self.x = SCREEN_W - 26.0
                self.vx = -abs(self.speed)
                self.facing = -1
        self.y = self.base_y + math.sin(self.time * 4.0 + self.phase) * 18.0
        self.sync_rect()

    @staticmethod
    def _player_is_armored(player):
        """Звезда / джетпак / ракета — игрок «бронирован», мышь погибает."""
        attrs = ("star_time", "jetpack", "rocket_time")
        if not any(hasattr(player, a) for a in attrs):
            return bool(getattr(player, "invincible", False))
        if getattr(player, "star_time", 0) > 0:
            return True
        if getattr(player, "jetpack", None) is not None:
            return True
        if getattr(player, "rocket_time", 0) > 0:
            return True
        return False

    def on_stomp(self, game):
        """Мышь не раздавить: прыжок сверху — тоже касание."""
        player = getattr(game, "player", None)
        if player is not None:
            self.on_touch(player, game)

    def on_touch(self, player, game):
        if self._player_is_armored(player):
            self.die(game)
            return
        player.take_hit(game, self)

    def draw_body(self, surf, sx, sy):
        c = self.body_color
        dark = monster_shade(c, -0.5)
        light = monster_shade(c, 0.35)
        flap = math.sin(self.time * (10.0 if self.waving else 18.0))
        # крылья
        for side in (-1, 1):
            f = flap
            if self.waving and side == self.facing:
                f = 0.8 + math.sin(self.time * 10.0) * 0.3   # одно крыло поднято — машет
            pts = [
                (sx + side * 7, sy - 2),
                (sx + side * 26, sy - 6 - f * 12),
                (sx + side * 23, sy + 4 - f * 6),
                (sx + side * 16, sy + 1 - f * 4),
                (sx + side * 10, sy + 6),
            ]
            pygame.draw.polygon(surf, dark, pts)
            inner = [(p[0] + (sx - p[0]) * 0.12, p[1] + (sy - p[1]) * 0.12) for p in pts]
            pygame.draw.polygon(surf, c, inner)
        # тело и голова
        body = pygame.Rect(int(sx - 8), int(sy - 8), 16, 22)
        pygame.draw.ellipse(surf, dark, body.inflate(4, 4))
        pygame.draw.ellipse(surf, c, body)
        pygame.draw.ellipse(surf, light, (int(sx - 4), int(sy - 2), 8, 10))
        for side in (-1, 1):
            ears = [(sx + side * 4, sy - 12), (sx + side * 8, sy - 21), (sx + side * 1, sy - 13)]
            pygame.draw.polygon(surf, dark, ears)
        pygame.draw.circle(surf, dark, (int(sx), int(sy - 7)), 10)
        pygame.draw.circle(surf, c, (int(sx), int(sy - 7)), 9)
        # глаза — светятся красным
        self.draw_face(surf, sx, sy - 8, spacing=4, eye_r=4, pupil_r=2,
                       color=(255, 235, 235), pupil=(215, 40, 40))
        # клычки
        for side in (-1, 1):
            pygame.draw.polygon(surf, WHITE, [(sx + side * 3, sy - 2), (sx + side * 1, sy - 2), (sx + side * 2, sy + 2)])


# ───────────────────────────────────────────────────────────────────────────
#  НЛО — телепортирует игрока на +500 м
# ───────────────────────────────────────────────────────────────────────────
class UFO(Monster):
    """НЛО: серебристая тарелка с мигающими огнями, медленно дрейфует.
    Любое касание -> телепорт игрока на UFO_TELEPORT_METERS вверх, тарелка улетает."""
    kind = "ufo"
    killable = False
    SIZE = (56, 30)
    body_color = (200, 205, 215)
    splat_colors = [(200, 205, 215), (120, 230, 255), (255, 220, 80)]

    def __init__(self, x, y, platform=None):
        super().__init__(x, y, platform)
        self.speed = random.uniform(30.0, 60.0)
        self.vx = self.speed * self.facing
        self.base_y = float(y)
        self.phase = random.uniform(0.0, math.tau)

    def update(self, dt, game):
        super().update(dt, game)
        if self.dying or not self.alive:
            return
        if not self.waving:
            self.x += self.vx * dt
            if self.x < 34.0:
                self.x = 34.0
                self.vx = abs(self.speed)
                self.facing = 1
            elif self.x > SCREEN_W - 34.0:
                self.x = SCREEN_W - 34.0
                self.vx = -abs(self.speed)
                self.facing = -1
        self.y = self.base_y + math.sin(self.time * 2.0 + self.phase) * 10.0
        self.sync_rect()

    def on_stomp(self, game):
        player = getattr(game, "player", None)
        if player is not None:
            self.on_touch(player, game)

    def on_touch(self, player, game):
        """Телепорт: звук, искры, эффект улёта тарелки, сдвиг игрока на +500 м."""
        if not self.alive:
            return
        self.alive = False
        cam_y = getattr(game, "cam_y", 0.0)
        game.sound.play("ufo")
        game.particles.emit(self.x, self.y, 24, color=[WHITE, (120, 230, 255), (255, 230, 120)],
                            speed=(120, 360), life=(0.3, 0.7), size=(2, 5), gravity=0, shape="spark")
        effects = getattr(game, "effects", None)
        if effects is not None:
            effects.append(UFOFlyAway(self.x, self.y - cam_y, self.time))
        game.shake(6, 0.25)
        game.teleport_player(UFO_TELEPORT_METERS)

    def draw_body(self, surf, sx, sy):
        draw_ufo_saucer(surf, sx, sy, self.time, self._look_dir, alpha=255, waving=self.waving)


class UFOFlyAway:
    """Эффект: после телепорта тарелка стремительно улетает вверх и тает.
    Работает в ЭКРАННЫХ координатах (cam_y игнорируется), чтобы быть видимой
    после мгновенного сдвига камеры."""
    screen = True

    def __init__(self, sx, sy, t=0.0):
        self.x = float(sx)
        self.y = float(sy)
        self.t0 = float(t)
        self.time = 0.0
        self.life = UFO_FLYAWAY_TIME
        self.vy = -150.0
        self.alive = True

    def update(self, dt, game):
        self.time += dt
        self.vy -= 2600.0 * dt
        self.y += self.vy * dt
        self.x += math.sin(self.time * 25.0) * 60.0 * dt
        if self.time >= self.life or self.y < -80:
            self.alive = False

    def draw(self, surf, cam_y):
        if not self.alive:
            return
        a = clamp(1.0 - self.time / max(1e-6, self.life), 0.0, 1.0)
        draw_ufo_saucer(surf, self.x, self.y, self.t0 + self.time, (0.0, 1.0), alpha=int(255 * a))
        # кольцо-вспышка от места старта
        r = int(10 + self.time * 320)
        if r < 320:
            ring = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
            pygame.draw.circle(ring, (255, 255, 255, int(180 * a)), (r + 4, r + 4), r, 3)
            surf.blit(ring, (int(self.x - r - 4), int(self.y - r - 4)))


# ───────────────────────────────────────────────────────────────────────────
#  Чирик — пасхалка: дружелюбный цыплёнок дарит щит
# ───────────────────────────────────────────────────────────────────────────
class Chirik(Monster):
    """Чирик: жёлтый цыплёнок, сидит на платформе, чирикает раз в ~3 с.
    Любое касание -> одноразовый щит игроку, конфетти, Чирик улетает."""
    kind = "chirik"
    friendly = True
    killable = False
    SIZE = (36, 36)
    body_color = (255, 225, 70)
    splat_colors = [(255, 225, 70), (255, 245, 150), (255, 150, 40)]

    def __init__(self, x, y, platform=None):
        super().__init__(x, y, platform)
        self.chirp_timer = random.uniform(0.8, CHIRP_INTERVAL)
        self.chirp_anim = 0.0
        self.hop_timer = random.uniform(0.8, 2.2)
        self.grounded = True
        top = self.platform_top()
        self.floor_y = float(top) if top is not None else self.bottom
        self.y = self.floor_y - self.h / 2.0
        self.sync_rect()

    def _floor(self):
        top = self.platform_top()
        return float(top) if top is not None else self.floor_y

    def update(self, dt, game):
        super().update(dt, game)
        if self.dying or not self.alive:
            return
        self.follow_platform()
        floor = self._floor()
        if self.chirp_anim > 0.0:
            self.chirp_anim -= dt
        if not self.waving:
            # чирикаем, если на экране
            self.chirp_timer -= dt
            if self.chirp_timer <= 0.0:
                self.chirp_timer = CHIRP_INTERVAL + random.uniform(-0.5, 0.6)
                if self.is_on_screen(getattr(game, "cam_y", 0.0)):
                    game.sound.play("chirp")
                    self.chirp_anim = 0.35
                    game.particles.emit(self.x + self.facing * 12, self.y - 14, 2, color=WHITE,
                                        speed=(20, 50), life=(0.4, 0.7), size=(2, 3),
                                        gravity=-200, shape="ring")
            # маленькие подскоки
            if self.grounded:
                self.hop_timer -= dt
                if self.hop_timer <= 0.0:
                    self.vy = -random.uniform(200.0, 290.0)
                    self.grounded = False
                    self.squash = 1.2
                    if random.random() < 0.4:
                        self.facing = -self.facing
        if not self.grounded:
            self.vy = min(self.vy + GRAVITY * 0.9 * dt, MAX_FALL_SPEED)
            self.y += self.vy * dt
            if self.vy > 0.0 and self.bottom >= floor:
                self.y = floor - self.h / 2.0
                self.vy = 0.0
                self.grounded = True
                self.squash = 0.78
                self.hop_timer = random.uniform(0.8, 2.4)
        else:
            self.y = floor - self.h / 2.0
        self.sync_rect()

    def on_stomp(self, game):
        player = getattr(game, "player", None)
        if player is not None:
            self.on_touch(player, game)

    def die(self, game, by_platform=False):
        """Чирик — друг, а не враг: он не «погибает» и не засчитывается как убитый монстр
        (ни комбо, ни очков, ни статистики). Если платформа под ним исчезла
        (например, сгорела ракета) — он просто упархивает, роняя пёрышки."""
        if self.dying or not self.alive:
            return
        self.alive = False
        if self.is_on_screen(getattr(game, "cam_y", 0.0)):
            game.sound.play("chirp")
            game.particles.emit(self.x, self.y, 10, color=self.splat_colors, speed=(40, 140),
                                life=(0.6, 1.1), size=(2, 4), gravity=-120, shape="ring")
            add_text = getattr(game, "add_text", None)
            if add_text is not None:
                add_text("ФЬЮТЬ!", self.x, self.y - self.h / 2.0 - 10, color=YELLOW, size=18, life=0.8)

    def on_touch(self, player, game):
        """Подарок: щит игроку, фраза, конфетти и пёрышки."""
        if not self.alive:
            return
        self.alive = False
        player.activate_bonus("shield", game)
        game.say("chirik")
        game.sound.play("chirp")
        game.particles.confetti(self.x, self.y, 30)
        game.particles.emit(self.x, self.y, 12, color=self.splat_colors, speed=(60, 200),
                            life=(0.4, 0.9), size=(3, 5), gravity=250)

    def draw_body(self, surf, sx, sy):
        c = self.body_color
        dark = (200, 160, 30)
        light = monster_shade(c, 0.5)
        orange = (255, 150, 40)
        sqy = clamp(self.squash, 0.5, 1.4)
        sqx = 2.0 - sqy
        ry = 15.0 * sqy
        rx = 15.0 * sqx
        body_bottom = sy + 14.0
        body_cy = body_bottom - ry
        f = self.facing if self.facing else 1
        draw_soft_shadow(surf, sx, sy + self.h / 2.0 + 1, 30 * sqx, alpha=45)
        # ножки — палочки с тремя пальчиками
        for side in (-1, 1):
            fx = sx + side * 6
            pygame.draw.line(surf, orange, (fx, body_bottom - 2), (fx, sy + 17), 2)
            for toe in (-1, 0, 1):
                pygame.draw.line(surf, orange, (fx, sy + 17), (fx + toe * 4 + f, sy + 20), 2)
        # хвостик-пёрышки
        for i in range(3):
            tx = sx - f * rx * 0.9
            wig = math.sin(self.time * 6.0 + i) * 1.5
            pygame.draw.line(surf, c, (tx, body_cy + 2), (tx - f * (7 + i * 1.5), body_cy - 3 - i * 3 + wig), 3)
        # тело
        body = pygame.Rect(int(sx - rx), int(body_cy - ry), int(rx * 2), int(ry * 2))
        pygame.draw.ellipse(surf, dark, body.inflate(4, 4))
        pygame.draw.ellipse(surf, c, body)
        pygame.draw.ellipse(surf, light, (int(sx - rx * 0.55), int(body_cy - ry * 0.7), int(rx * 0.5), int(ry * 0.3)))
        # крылышко (машет при прыжке/чирике)
        flap = math.sin(self.time * 20.0) * 0.5 if (not self.grounded or self.chirp_anim > 0) else 0.1
        draw_rot_ellipse(surf, dark, sx - f * rx * 0.55, body_cy + 3, 8, 4.5, -f * (0.5 + flap))
        draw_rot_ellipse(surf, monster_shade(c, -0.08), sx - f * rx * 0.55, body_cy + 3, 6.5, 3.5, -f * (0.5 + flap))
        # хохолок
        for i in (-1, 0, 1):
            top_x = sx + i * 3
            pygame.draw.line(surf, dark, (top_x, body_cy - ry + 2), (top_x + i * 3, body_cy - ry - 6 + abs(i) * 2), 2)
        # лицо
        face_y = body_cy - 3.0 * sqy
        self.draw_face(surf, sx + f * 2, face_y, spacing=6, eye_r=5, pupil_r=2)
        draw_blush(surf, sx + f * 2, face_y + 7, spacing=10, r=3, color=(255, 120, 130), alpha=130)
        # клювик (открывается при чирике)
        bx = sx + f * 8
        by = face_y + 5
        gap = 3.0 if self.chirp_anim > 0 else 0.0
        pygame.draw.polygon(surf, orange, [(bx, by - 2 - gap), (bx + f * 8, by - gap * 0.3), (bx, by + 0.5)])
        pygame.draw.polygon(surf, monster_shade(orange, -0.25), [(bx, by + 0.5), (bx + f * 8, by + 1 + gap * 0.3), (bx, by + 3 + gap)])
        if self.waving:
            self.draw_wave_arm(surf, sx, body_cy, c, length=12, side=-f)


# ═══════════════════════════════════════════════════════════════════════════
# ═══ ЧАСТЬ 5: ЭКРАНЫ, РЕКЛАМА, КЕЙСЫ, СКИНЫ ═══
# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
#  PART 5: ЭКРАНЫ, РЕКЛАМА MUSORDROP, КЕЙСЫ И СКИНЫ
#  (заставка, меню, рекорды, кейсы, скины, мусорный магазин, пауза, game over,
#   менеджер рекламы). Только определения — импорты и константы в part0.
# ═══════════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════════
#  ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ЭКРАНОВ
# ═══════════════════════════════════════════════════════════════════════════
def ui_sound(game, name, volume=1.0):
    """Безопасно проиграть звук через game.sound (терпит отсутствие звука)."""
    try:
        game.sound.play(name, volume)
    except Exception:
        pass


def rrect(surf, rect, color, radius=10, width=0):
    """Закруглённый прямоугольник через pygame.draw.rect (border_radius)."""
    r = pygame.Rect(rect)
    if r.w <= 0 or r.h <= 0:
        return
    rad = max(0, min(int(radius), r.w // 2, r.h // 2))
    pygame.draw.rect(surf, color, r, int(width), border_radius=rad)


def wrap_text(text, size, max_width, bold=False):
    """Разбить строку на строки по словам так, чтобы каждая влезала в max_width px."""
    font = get_font(size, bold)
    words = str(text).split()
    lines = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip()
        if not cur or font.size(trial)[0] <= max_width:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


def fit_text_size(text, max_width, size, min_size=12, bold=False):
    """Подобрать размер шрифта (не меньше min_size), чтобы текст влез в max_width."""
    size = int(size)
    while size > min_size and get_font(size, bold).size(str(text))[0] > max_width:
        size -= 1
    return size


def draw_wrapped_text(surf, text, cx, y, size, color, max_width, bold=False, shadow=None,
                      outline=None, alpha=255, line_gap=4, max_lines=3, anchor="midtop"):
    """Нарисовать текст с переносом строк по центру cx. Возвращает высоту блока."""
    lines = wrap_text(text, size, max_width, bold)[:max_lines]
    lh = get_font(size, bold).get_height() + line_gap
    total = lh * len(lines) - line_gap
    y0 = y - total / 2 if anchor == "center" else y
    for i, line in enumerate(lines):
        draw_text(surf, line, cx, y0 + i * lh, size, color, "midtop", bold, shadow, outline, alpha)
    return total


def rarity_color(rarity, t=0.0):
    """Цвет редкости; ИМБА переливается радугой."""
    if rarity == "imba":
        return rainbow(t * 0.6)
    return RARITY_COLORS.get(rarity, WHITE)


def blink_alpha(t, hz=2.0, lo=90, hi=255):
    """Мигание: альфа по синусу времени."""
    return int(lo + (hi - lo) * (0.5 + 0.5 * math.sin(t * hz * 2 * math.pi)))


def pulse(t, hz=1.0, lo=0.0, hi=1.0):
    """Плавная пульсация lo..hi по синусу."""
    return lo + (hi - lo) * (0.5 + 0.5 * math.sin(t * hz * 2 * math.pi))


def ease_out_cubic(u):
    """Кубическое замедление (быстро -> медленно)."""
    u = clamp(u, 0.0, 1.0)
    return 1.0 - (1.0 - u) ** 3


def ease_out_back(u):
    """«Выскакивание» с небольшим перелётом (для появления карточек)."""
    u = clamp(u, 0.0, 1.0)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (u - 1) ** 3 + c1 * (u - 1) ** 2


def draw_dim(surf, alpha=150, color=BLACK):
    """Полупрозрачное затемнение всего экрана."""
    ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    ov.fill((color[0], color[1], color[2], int(clamp(alpha, 0, 255))))
    surf.blit(ov, (0, 0))


def draw_panel(surf, rect, color=UI_PANEL, border=UI_BORDER, radius=14, shadow=True):
    """Панель с тенью, бликом и рамкой."""
    r = pygame.Rect(rect)
    if shadow:
        rrect(surf, r.move(0, 5), (10, 12, 25), radius)
    rrect(surf, r, color, radius)
    top = pygame.Rect(r.x + 3, r.y + 3, r.w - 6, max(4, r.h // 6))
    if top.w > 0 and top.h > 0:
        hl = pygame.Surface((top.w, top.h), pygame.SRCALPHA)
        pygame.draw.rect(hl, (255, 255, 255, 22), hl.get_rect(), border_radius=max(0, radius - 3))
        surf.blit(hl, top.topleft)
    if border:
        rrect(surf, r, border, radius, 2)


def draw_caps_counter(surf, x, y, n, size=22, anchor="midleft", color=GOLD):
    """Иконка крышки + число (валюта). Возвращает ширину."""
    txt = str(int(n))
    font = get_font(size, True)
    tw = font.size(txt)[0]
    r = size * 0.5
    total = r * 2 + 8 + tw
    if anchor == "midright":
        x0 = x - total
    elif anchor == "center":
        x0 = x - total / 2
    else:
        x0 = x
    draw_cap_icon(surf, int(x0 + r), int(y), int(r))
    draw_text(surf, txt, x0 + r * 2 + 8, y, size, color, "midleft", True, shadow=(0, 0, 0))
    return total


def draw_star(surf, cx, cy, r, color, points=5, rot=0.0, inner=0.45):
    """Звёздочка-многоугольник."""
    pts = []
    for i in range(points * 2):
        ang = rot + i * math.pi / points - math.pi / 2
        rr = r if i % 2 == 0 else r * inner
        pts.append((cx + math.cos(ang) * rr, cy + math.sin(ang) * rr))
    if len(pts) >= 3:
        pygame.draw.polygon(surf, color, pts)


def draw_trash_bin(surf, cx, cy, scale=1.0, t=0.0, lid_lift=0.0, color=(125, 135, 145)):
    """Мусорный бак MusorDrop: корпус-трапеция, полоски, блик, крышка с ручкой."""
    s = scale
    dark = lerp_color(color, BLACK, 0.4)
    light = lerp_color(color, WHITE, 0.35)
    top_w, bot_w, h = 44 * s, 34 * s, 50 * s
    y0 = cy - 16 * s
    body = [(cx - top_w / 2, y0), (cx + top_w / 2, y0),
            (cx + bot_w / 2, y0 + h), (cx - bot_w / 2, y0 + h)]
    pygame.draw.polygon(surf, color, body)
    pygame.draw.polygon(surf, dark, body, max(1, int(2 * s)))
    for k in (-1, 0, 1):
        x_top = cx + k * 12 * s
        x_bot = cx + k * 9 * s
        pygame.draw.line(surf, dark, (x_top, y0 + 6 * s), (x_bot, y0 + h - 6 * s), max(1, int(2 * s)))
    pygame.draw.line(surf, light, (cx - top_w / 2 + 5 * s, y0 + 5 * s),
                     (cx - bot_w / 2 + 5 * s, y0 + h - 6 * s), max(1, int(2 * s)))
    lid_y = y0 - 9 * s - lid_lift
    lid = pygame.Rect(int(cx - top_w / 2 - 4 * s), int(lid_y), int(top_w + 8 * s), max(2, int(10 * s)))
    rrect(surf, lid, light, int(4 * s))
    rrect(surf, lid, dark, int(4 * s), max(1, int(2 * s)))
    handle = pygame.Rect(int(cx - 7 * s), int(lid_y - 6 * s), max(2, int(14 * s)), max(2, int(7 * s)))
    rrect(surf, handle, dark, int(3 * s))


def draw_medal(surf, cx, cy, rank, t=0.0, r=16):
    """Медаль за место 1-3: ленточка + кружок с номером и бегущим бликом."""
    palette = {
        1: ((255, 205, 50), (200, 150, 20)),
        2: ((205, 210, 220), (140, 145, 160)),
        3: ((210, 130, 60), (150, 90, 35)),
    }
    main, dark = palette.get(rank, ((120, 120, 120), (80, 80, 80)))
    pygame.draw.polygon(surf, (210, 60, 70), [(cx - 9, cy - r - 12), (cx - 2, cy - r - 12), (cx + 1, cy - r + 6), (cx - 7, cy - r + 6)])
    pygame.draw.polygon(surf, (60, 90, 200), [(cx + 2, cy - r - 12), (cx + 9, cy - r - 12), (cx + 7, cy - r + 6), (cx - 1, cy - r + 6)])
    pygame.draw.circle(surf, dark, (int(cx), int(cy) + 2), r)
    pygame.draw.circle(surf, main, (int(cx), int(cy)), r)
    pygame.draw.circle(surf, dark, (int(cx), int(cy)), r, 2)
    ang = t * 1.5
    hx = cx + math.cos(ang) * r * 0.45
    hy = cy + math.sin(ang) * r * 0.45
    pygame.draw.circle(surf, lerp_color(main, WHITE, 0.6), (int(hx), int(hy)), max(2, r // 4))
    draw_text(surf, str(rank), cx, cy + 1, int(r * 1.1), lerp_color(dark, BLACK, 0.5), "center", True)


def draw_trophy(surf, cx, cy, scale=1.0, alpha=255):
    """Золотой кубок примитивами (эмодзи-кубок шрифт не рисует): ручки, чаша с бликом и
    звездой, ножка, подставка. (cx, cy) — центр кубка; alpha — общая прозрачность."""
    s = max(0.2, float(scale))
    w, h = int(60 * s) + 2, int(62 * s) + 2
    layer = pygame.Surface((w, h), pygame.SRCALPHA)
    dark = lerp_color(GOLD, BLACK, 0.4)
    light = lerp_color(GOLD, WHITE, 0.55)

    def P(x, y):
        return (int(x * s), int(y * s))

    lw = max(2, int(4 * s))
    # ручки — толстые дуги по бокам (чаша потом перекрывает их внутреннюю половину)
    for hx in (11, 49):
        pygame.draw.circle(layer, dark, P(hx, 17), max(3, int(10 * s)), lw)
    # чаша
    bowl = [P(12, 5), P(48, 5), P(46, 20), P(39, 32), P(30, 37), P(21, 32), P(14, 20)]
    pygame.draw.polygon(layer, GOLD, bowl)
    pygame.draw.polygon(layer, dark, bowl, max(1, int(2 * s)))
    pygame.draw.rect(layer, light, pygame.Rect(P(10, 2), P(40, 5)), border_radius=max(1, int(2 * s)))
    # блик и звезда на чаше
    pygame.draw.line(layer, light, P(19, 10), P(21, 25), max(1, int(3 * s)))
    draw_star(layer, 30 * s, 18 * s, 6 * s, dark)
    # ножка и подставка
    pygame.draw.rect(layer, dark, pygame.Rect(P(27, 36), P(6, 11)))
    pygame.draw.rect(layer, GOLD, pygame.Rect(P(19, 46), P(22, 6)), border_radius=max(1, int(2 * s)))
    pygame.draw.rect(layer, dark, pygame.Rect(P(15, 52), P(30, 8)), border_radius=max(1, int(2 * s)))
    if alpha < 255:
        layer.set_alpha(int(clamp(alpha, 0, 255)))
    surf.blit(layer, (int(cx - w / 2), int(cy - h / 2)))


def draw_case_icon(surf, cx, cy, case, t=0.0, scale=1.0, glow=0.0):
    """Подарочная коробка кейса: цвет по тиру, ленты, бант, надпись 67/52 для имба-кейсов, звёздочки тира."""
    s = scale
    tier = case.get("tier", 1)
    main, dark = CASE_BOX_COLORS.get(tier, CASE_BOX_COLORS[1])
    if tier >= 3:
        main = lerp_color(main, rainbow(t * 0.5), 0.25 + 0.25 * pulse(t, 2))
    light = lerp_color(main, WHITE, 0.4)
    ribbon = lerp_color(dark, BLACK, 0.3) if tier < 4 else (200, 60, 60)
    if glow > 0:
        draw_glow(surf, cx, cy, int(60 * s * (1 + glow)), main, int(60 * glow + 30))
    w, h = 64 * s, 50 * s
    body = pygame.Rect(int(cx - w / 2), int(cy - h / 2 + 8 * s), max(2, int(w)), max(2, int(h)))
    lid = pygame.Rect(int(cx - w / 2 - 4 * s), int(cy - h / 2 - 8 * s), max(2, int(w + 8 * s)), max(2, int(17 * s)))
    rrect(surf, body, main, int(7 * s))
    rrect(surf, body, dark, int(7 * s), max(1, int(2 * s)))
    pygame.draw.rect(surf, ribbon, pygame.Rect(int(cx - 6 * s), body.y, max(1, int(12 * s)), body.h))
    pygame.draw.rect(surf, ribbon, pygame.Rect(body.x, int(body.centery - 5 * s), body.w, max(1, int(10 * s))))
    rrect(surf, lid, light, int(6 * s))
    rrect(surf, lid, dark, int(6 * s), max(1, int(2 * s)))
    pygame.draw.rect(surf, ribbon, pygame.Rect(int(cx - 6 * s), lid.y, max(1, int(12 * s)), lid.h))
    bow_y = lid.y - 2 * s
    pygame.draw.ellipse(surf, ribbon, pygame.Rect(int(cx - 18 * s), int(bow_y - 8 * s), max(2, int(16 * s)), max(2, int(12 * s))))
    pygame.draw.ellipse(surf, ribbon, pygame.Rect(int(cx + 2 * s), int(bow_y - 8 * s), max(2, int(16 * s)), max(2, int(12 * s))))
    pygame.draw.circle(surf, lerp_color(ribbon, WHITE, 0.3), (int(cx), int(bow_y - 2 * s)), max(2, int(4 * s)))
    if tier == 3:
        draw_text(surf, "67", cx, body.centery + 6 * s, max(12, int(16 * s)), WHITE, "center", True, outline=dark)
    elif tier == 4:
        draw_text(surf, "52", cx, body.centery + 6 * s, max(12, int(16 * s)), WHITE, "center", True, outline=dark)
    for i in range(tier):
        sx = cx + (i - (tier - 1) / 2) * 12 * s
        draw_star(surf, sx, body.bottom + 8 * s, 4 * s, GOLD)


def draw_mini_monster(surf, cx, cy, r=7, color=(200, 110, 210)):
    """Мини-иконка монстрика (ушастик) для таблицы рекордов."""
    dark = lerp_color(color, BLACK, 0.4)
    pygame.draw.ellipse(surf, dark, pygame.Rect(int(cx - r - 2), int(cy - r - 8), 6, 10))
    pygame.draw.ellipse(surf, dark, pygame.Rect(int(cx + r - 4), int(cy - r - 8), 6, 10))
    pygame.draw.circle(surf, color, (int(cx), int(cy)), r)
    pygame.draw.circle(surf, WHITE, (int(cx - 3), int(cy - 1)), 3)
    pygame.draw.circle(surf, WHITE, (int(cx + 3), int(cy - 1)), 3)
    pygame.draw.circle(surf, BLACK, (int(cx - 3), int(cy - 1)), 1)
    pygame.draw.circle(surf, BLACK, (int(cx + 3), int(cy - 1)), 1)


def skin_display_name(skin):
    """Имя скина (для None — «???»)."""
    if not skin:
        return "???"
    return str(skin.get("name", skin.get("id", "?")))


class UIBackdrop:
    """Фон экранов меню: градиент + всплывающие крышки-пузырьки + мерцающие звёзды."""

    def __init__(self, seed_count=16):
        self.gradient = None
        self.floaters = []
        self.stars = []
        for _ in range(seed_count):
            self.floaters.append(self._new_floater(random.uniform(0, SCREEN_H)))
        for _ in range(40):
            self.stars.append([random.uniform(0, SCREEN_W), random.uniform(0, SCREEN_H),
                               random.uniform(0.6, 2.0), random.uniform(0, 6.28)])
        self.t = 0.0

    def _new_floater(self, y=None):
        return {"x": random.uniform(10, SCREEN_W - 10),
                "y": SCREEN_H + 20 if y is None else y,
                "vy": random.uniform(14, 40), "r": random.uniform(5, 12),
                "phase": random.uniform(0, 6.28)}

    def _build_gradient(self):
        g = pygame.Surface((SCREEN_W, SCREEN_H))
        steps = 72
        band_h = SCREEN_H / steps
        for i in range(steps):
            c = lerp_color(UI_BG_TOP, UI_BG_BOTTOM, i / max(1, steps - 1))
            pygame.draw.rect(g, c, pygame.Rect(0, int(i * band_h), SCREEN_W, int(band_h) + 1))
        return g

    def update(self, dt):
        self.t += dt
        for f in self.floaters:
            f["y"] -= f["vy"] * dt
            f["x"] += math.sin(self.t * 0.8 + f["phase"]) * 10 * dt
            if f["y"] < -20:
                f.update(self._new_floater())

    def draw(self, surf):
        if self.gradient is None:
            self.gradient = self._build_gradient()
        surf.blit(self.gradient, (0, 0))
        for s in self.stars:
            a = 0.5 + 0.5 * math.sin(self.t * 2 + s[3])
            c = lerp_color(UI_BG_TOP, WHITE, 0.25 + 0.6 * a)
            pygame.draw.circle(surf, c, (int(s[0]), int(s[1])), int(s[2]))
        for f in self.floaters:
            col = lerp_color(UI_BG_BOTTOM, LIGHT_GRAY, 0.35)
            rim = lerp_color(UI_BG_BOTTOM, LIGHT_GRAY, 0.6)
            r = int(f["r"])
            pygame.draw.circle(surf, col, (int(f["x"]), int(f["y"])), r)
            pygame.draw.circle(surf, rim, (int(f["x"]), int(f["y"])), r, 1)
            pygame.draw.circle(surf, rim, (int(f["x"] - r * 0.35), int(f["y"] - r * 0.35)), max(1, r // 4))


class UIParticles:
    """Лёгкие частицы для UI (конфетти, искры) — экранные координаты, не зависят от мира."""
    MAX = 400

    def __init__(self):
        self.items = []

    def confetti(self, x, y, count=60, spread=200):
        """Конфетти: цветные вращающиеся прямоугольники."""
        for _ in range(int(count)):
            if len(self.items) >= self.MAX:
                break
            self.items.append({
                "kind": "rect", "x": x + random.uniform(-spread / 2, spread / 2), "y": y,
                "vx": random.uniform(-280, 280), "vy": random.uniform(-560, -160),
                "w": random.uniform(6, 11), "h": random.uniform(4, 7),
                "rot": random.uniform(0, 6.28), "rs": random.uniform(-9, 9),
                "life": random.uniform(2.0, 3.2), "max_life": 3.2,
                "color": random.choice(CONFETTI_COLORS), "g": 650.0, "drag": 1.4,
            })

    def sparks(self, x, y, count=12, color=GOLD, speed=(120, 360)):
        """Искры-линии, разлетающиеся радиально."""
        for _ in range(int(count)):
            if len(self.items) >= self.MAX:
                break
            ang = random.uniform(0, 6.28)
            sp = random.uniform(speed[0], speed[1])
            self.items.append({
                "kind": "spark", "x": x, "y": y, "vx": math.cos(ang) * sp, "vy": math.sin(ang) * sp,
                "life": random.uniform(0.3, 0.7), "max_life": 0.7, "color": color, "g": 350.0,
                "drag": 0.5, "w": 2, "h": 2, "rot": 0.0, "rs": 0.0,
            })

    def clear(self):
        self.items = []

    def update(self, dt):
        alive = []
        for p in self.items:
            p["life"] -= dt
            if p["life"] <= 0:
                continue
            p["vy"] += p["g"] * dt
            k = max(0.0, 1.0 - p["drag"] * dt)
            p["vx"] *= k
            if p["kind"] == "rect":
                p["vy"] *= max(0.0, 1.0 - 0.9 * dt)
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["rot"] += p["rs"] * dt
            if -40 < p["x"] < SCREEN_W + 40 and p["y"] < SCREEN_H + 40:
                alive.append(p)
        self.items = alive

    def draw(self, surf):
        for p in self.items:
            frac = clamp(p["life"] / max(0.01, p["max_life"]), 0, 1)
            if p["kind"] == "rect":
                col = p["color"] if frac > 0.3 else lerp_color(p["color"], UI_BG_BOTTOM, 1 - frac / 0.3)
                c, s = math.cos(p["rot"]), math.sin(p["rot"])
                hw, hh = p["w"] / 2, p["h"] / 2 * (0.3 + 0.7 * abs(math.sin(p["rot"] * 1.3)))
                pts = [(p["x"] + c * dx - s * dy, p["y"] + s * dx + c * dy)
                       for dx, dy in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]
                pygame.draw.polygon(surf, col, pts)
            else:
                col = lerp_color(p["color"], UI_BG_TOP, 1 - frac)
                ex = p["x"] - p["vx"] * 0.035
                ey = p["y"] - p["vy"] * 0.035
                pygame.draw.line(surf, col, (p["x"], p["y"]), (ex, ey), 2)


# ═══════════════════════════════════════════════════════════════════════════
#  ЛОГИКА КЕЙСОВ
# ═══════════════════════════════════════════════════════════════════════════
def roll_case(case):
    """Ролл кейса: редкость по case["chances"], затем скин (для ИМБА — по IMBA_WEIGHTS). Возвращает dict скина."""
    chances = case.get("chances") or RARITY_CHANCES
    try:
        rarity = weighted_choice(chances)
    except Exception:
        rarity = "common"
    candidates = [s for s in SKINS if s.get("rarity") == rarity]
    if not candidates:
        candidates = [s for s in SKINS if s.get("rarity") in chances] or list(SKINS)
    if rarity == "imba":
        weights = {s["id"]: IMBA_WEIGHTS.get(s["id"], 1) for s in candidates}
        try:
            sid = weighted_choice(weights)
        except Exception:
            sid = candidates[0]["id"]
        return SKINS_BY_ID.get(sid, candidates[0])
    return random.choice(candidates)


# ═══════════════════════════════════════════════════════════════════════════
#  БАЗОВЫЙ ЭКРАН И ОБЩИЕ УТИЛИТЫ ЭКРАНОВ
# ═══════════════════════════════════════════════════════════════════════════
class Screen:
    """Базовый экран: пустые on_enter / handle_event / update / draw."""

    def on_enter(self, game):
        pass

    def handle_event(self, event, game):
        pass

    def update(self, dt, game):
        pass

    def draw(self, surf, game):
        pass


def _is_key(event, *keys):
    """KEYDOWN с одной из указанных клавиш?"""
    return event.type == pygame.KEYDOWN and event.key in keys


def _mouse_pos():
    """Позиция мыши (терпит headless-режим)."""
    try:
        return pygame.mouse.get_pos()
    except Exception:
        return (0, 0)


def _active_skin(game):
    """Словарь активного скина игрока (безопасно)."""
    try:
        return SKINS_BY_ID.get(game.save.skin_active, SKINS_BY_ID[DEFAULT_SKIN])
    except Exception:
        return SKINS_BY_ID[DEFAULT_SKIN]


def _make_button(rect, text, callback, color=UI_BTN, size=22, enabled=True):
    """Кнопка со стандартным цветом подсветки при наведении."""
    return Button(pygame.Rect(rect), text, callback, color=color,
                  hover=lerp_color(color, WHITE, 0.28), size=size, enabled=enabled)


def _unlocked_count(game):
    """Сколько скинов открыто (через API SaveManager)."""
    n = 0
    for s in SKINS:
        try:
            if game.save.is_unlocked(s["id"]):
                n += 1
        except Exception:
            pass
    return n


# ═══════════════════════════════════════════════════════════════════════════
#  ЗАСТАВКА
# ═══════════════════════════════════════════════════════════════════════════
class SplashScreen(Screen):
    """Заставка MusorDrop: тёмный фон, большой мусорный бак, искры, главный слоган. 1.5 с или любая клавиша."""

    def __init__(self):
        self.t = 0.0
        self.timer = 0.0
        self.sparkles = [[random.uniform(80, 400), random.uniform(120, 420), random.uniform(0, 6.28), random.uniform(3, 7)]
                         for _ in range(14)]

    def on_enter(self, game):
        self.timer = 0.0
        self.t = 0.0

    def handle_event(self, event, game):
        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            game.set_state("menu")

    def update(self, dt, game):
        self.t += dt
        self.timer += dt
        if self.timer >= SPLASH_TIME:
            game.set_state("menu")

    def draw(self, surf, game):
        surf.fill((12, 12, 22))
        draw_glow(surf, SCREEN_W / 2, 290, 170, (80, 90, 120), 70)
        for s in self.sparkles:
            a = 0.5 + 0.5 * math.sin(self.t * 4 + s[2])
            col = lerp_color((12, 12, 22), GOLD, a)
            draw_star(surf, s[0], s[1], s[3] * (0.6 + 0.4 * a), col, rot=self.t * 2 + s[2])
        lift = abs(math.sin(self.t * 5)) * 10
        draw_trash_bin(surf, SCREEN_W / 2, 290, 3.2, self.t, lid_lift=lift)
        appear = clamp(self.t / 0.4, 0, 1)
        draw_text(surf, "MUSORDROP", SCREEN_W / 2, 100, 46, GOLD, "center", True,
                  shadow=(60, 40, 0), alpha=int(255 * appear))
        draw_wrapped_text(surf, MUSOR_MAIN_SLOGAN, SCREEN_W / 2, 470, 26, WHITE, 420, True,
                          shadow=(0, 0, 0), alpha=int(255 * appear))
        draw_text(surf, MUSOR_REAL_SLOGAN, SCREEN_W / 2, 560, 16, (160, 160, 180), "center", False)
        draw_text(surf, "реклама-мем, не настоящая", SCREEN_W / 2, 600, 16, (120, 120, 140), "center")
        draw_text(surf, "нажми любую клавишу", SCREEN_W / 2, 670, 16, LIGHT_GRAY, "center",
                  alpha=blink_alpha(self.t, 1.5, 80, 255))
        frac = clamp(self.timer / SPLASH_TIME, 0, 1)
        pygame.draw.rect(surf, (40, 40, 60), pygame.Rect(0, SCREEN_H - 6, SCREEN_W, 6))
        pygame.draw.rect(surf, GOLD, pygame.Rect(0, SCREEN_H - 6, int(SCREEN_W * frac), 6))


# ═══════════════════════════════════════════════════════════════════════════
#  ГЛАВНОЕ МЕНЮ
# ═══════════════════════════════════════════════════════════════════════════
class MenuScreen(Screen):
    """Главное меню: заголовок, прыгающий дудлер-маскот, кнопки, крышки/рекорд, рекламный баннер и попапы."""

    def __init__(self):
        self.game = None
        self.t = 0.0
        self.backdrop = UIBackdrop()
        specs = [
            ("ИГРАТЬ", self._play, UI_BTN_OK),
            ("КЕЙСЫ", lambda: self._go("cases"), UI_BTN),
            ("СКИНЫ", lambda: self._go("skins"), UI_BTN),
            ("РЕКОРДЫ", lambda: self._go("records"), UI_BTN),
            ("MUSORDROP", lambda: self._go("musor"), (200, 120, 40)),
            ("ВЫХОД", self._quit, UI_BTN_DANGER),
        ]
        self.buttons = []
        for i, (text, cb, color) in enumerate(specs):
            self.buttons.append(_make_button((110, 278 + i * 58, 260, 48), text, cb, color, 24))
        # главный слоган — «везде, и на кнопках»: вторая строка кнопки MUSORDROP
        self.buttons[4].small_text = MUSOR_MAIN_SLOGAN.partition("— ")[2] or MUSOR_MAIN_SLOGAN
        self.group = ButtonGroup(self.buttons)

    # --- действия кнопок ---
    def _play(self):
        if self.game is not None:
            self.game.start_game()

    def _go(self, name):
        g = self.game
        if g is None:
            return
        try:
            scr = g.screens.get(name)
            if scr is not None and hasattr(scr, "back_state"):
                scr.back_state = "menu"
        except Exception:
            pass
        ui_sound(g, "click")
        g.set_state(name)

    def _quit(self):
        if self.game is not None:
            self.game.quit()

    # --- интерфейс экрана ---
    def on_enter(self, game):
        self.game = game
        self.group.set_index(0)

    def handle_event(self, event, game):
        self.game = game
        try:
            if game.ads.handle_menu_event(event):
                return
        except AttributeError:
            pass
        if _is_key(event, pygame.K_ESCAPE):
            game.quit()
            return
        self.group.handle_event(event)

    def update(self, dt, game):
        self.game = game
        self.t += dt
        self.backdrop.update(dt)
        self.group.update(dt, _mouse_pos())
        try:
            game.ads.update_menu(dt)
        except AttributeError:
            pass

    def draw(self, surf, game):
        self.game = game
        self.backdrop.draw(surf)
        # заголовок в две строки с тенью
        title_main, _, subtitle = TITLE.partition(":")
        subtitle = subtitle.strip() or "Космическая Котлета"
        wob = math.sin(self.t * 2) * 3
        draw_text(surf, title_main.strip(), SCREEN_W / 2, 66 + wob, 44, GOLD, "center", True, shadow=(70, 40, 0), outline=(50, 30, 0))
        draw_text(surf, subtitle, SCREEN_W / 2, 110 + wob, 27, PINK, "center", True, shadow=(60, 20, 40))
        # крышки и рекорд
        try:
            caps = game.save.caps
            best = game.save.best_score
        except Exception:
            caps, best = 0, 0
        draw_caps_counter(surf, 14, 24, caps, 22, "midleft")
        draw_text(surf, "Рекорд: %d" % best, SCREEN_W - 14, 24, 20, LIGHT_GRAY, "midright", True, shadow=(0, 0, 0))
        # маскот-дудлер прыгает
        phase = (self.t * 1.4) % 1.0
        h = math.sin(math.pi * phase)
        base_y = 222
        cy = base_y - 52 * h
        squash = 0.78 + 0.4 * h          # внизу сжат, наверху растянут
        shadow_w = int(46 * (1.1 - 0.5 * h))
        sh = pygame.Surface((shadow_w * 2, 14), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 80), sh.get_rect())
        surf.blit(sh, (SCREEN_W / 2 - shadow_w, base_y + 30))
        facing = 1 if math.sin(self.t * 0.7) > 0 else -1
        try:
            draw_doodler(surf, SCREEN_W / 2, cy, _active_skin(game), self.t, facing=facing,
                         squash=clamp(squash, 0.7, 1.2), tilt=math.sin(self.t * 1.4) * 0.12, scale=1.3)
        except Exception:
            pass
        # кнопки
        self.group.draw(surf)
        draw_text(surf, "Enter - играть      Esc - выход      M - звук", SCREEN_W / 2, 646, 16, (150, 160, 200), "center")
        # реклама
        try:
            game.ads.draw_menu(surf)
        except AttributeError:
            pass


# ═══════════════════════════════════════════════════════════════════════════
#  РЕКОРДЫ И СТАТИСТИКА
# ═══════════════════════════════════════════════════════════════════════════
class RecordsScreen(Screen):
    """Экран рекордов: вкладки ТОП-5 (медали, золотая мигающая строка нового рекорда) и СТАТИСТИКА; сброс с подтверждением."""

    def __init__(self):
        self.game = None
        self.t = 0.0
        self.tab = 0
        self.back_state = "menu"
        self.confirm_timer = 0.0
        self.message = ""
        self.message_timer = 0.0
        self.backdrop = UIBackdrop()
        self.tab_btns = [
            _make_button((40, 68, 190, 40), "ТОП-5", lambda: self._set_tab(0), UI_BTN, 20),
            _make_button((250, 68, 190, 40), "СТАТИСТИКА", lambda: self._set_tab(1), UI_BTN, 20),
        ]
        self.reset_btn = _make_button((40, 600, 250, 44), "СБРОСИТЬ РЕКОРДЫ", self._reset, (125, 70, 85), 19)
        self.confirm_btn = _make_button((40, 600, 250, 44), "ТОЧНО? НАЖМИ ЕЩЁ", self._reset, UI_BTN_DANGER, 19)
        self.back_btn = _make_button((300, 600, 140, 44), "НАЗАД", self._back, UI_BTN, 20)
        self.group = None
        self._rebuild(0)

    def _rebuild(self, index):
        btns = list(self.tab_btns) + [self.confirm_btn if self.confirm_timer > 0 else self.reset_btn, self.back_btn]
        self.group = ButtonGroup(btns)
        self.group.set_index(int(clamp(index, 0, len(btns) - 1)))

    def _set_tab(self, i):
        self.tab = int(i) % 2
        for k, b in enumerate(self.tab_btns):
            b.selected = (k == self.tab)
            # Активная вкладка — золотая: флаг selected ButtonGroup каждый кадр
            # перезаписывает под фокус клавиатуры, поэтому выделяем цветом
            base = (205, 150, 45) if k == self.tab else UI_BTN
            b.color = base
            b.hover_color = lerp_color(base, WHITE, 0.28)
        if self.game is not None:
            ui_sound(self.game, "click")

    def _reset(self):
        g = self.game
        if self.confirm_timer > 0:
            try:
                g.save.reset()
            except Exception as e:
                print("reset error:", e)
            self.confirm_timer = 0.0
            self.message = "Рекорды и статистика сброшены"
            self.message_timer = 2.5
            if g is not None:
                ui_sound(g, "crack")
                try:
                    # после сброса ни экран рекордов, ни Game Over, ни HUD за ним
                    # не должны показывать место/рекорд из уже стёртого ТОП-5
                    g.last_record_rank = 0
                    g.record_beaten = False
                except Exception:
                    pass
        else:
            self.confirm_timer = RESET_CONFIRM_TIME
            if g is not None:
                ui_sound(g, "click")
        self._rebuild(self.group.index if self.group is not None else 0)

    def _back(self):
        if self.game is not None:
            ui_sound(self.game, "click")
            self.game.set_state(self.back_state)

    def on_enter(self, game):
        self.game = game
        self.confirm_timer = 0.0
        self.message_timer = 0.0
        self.t = 0.0
        self._set_tab(0)
        self._rebuild(0)

    def handle_event(self, event, game):
        self.game = game
        if _is_key(event, pygame.K_ESCAPE):
            self._back()
            return
        if _is_key(event, pygame.K_LEFT, pygame.K_a, pygame.K_TAB, pygame.K_RIGHT, pygame.K_d):
            self._set_tab(self.tab + 1)
            return
        self.group.handle_event(event)

    def update(self, dt, game):
        self.game = game
        self.t += dt
        self.backdrop.update(dt)
        if self.confirm_timer > 0:
            self.confirm_timer -= dt
            if self.confirm_timer <= 0:
                self.confirm_timer = 0.0
                self._rebuild(self.group.index)
        if self.message_timer > 0:
            self.message_timer -= dt
        self.group.update(dt, _mouse_pos())

    # --- отрисовка ---
    def draw(self, surf, game):
        self.game = game
        self.backdrop.draw(surf)
        draw_text(surf, "РЕКОРДЫ", SCREEN_W / 2, 32, 34, GOLD, "center", True, shadow=(60, 40, 0))
        draw_panel(surf, (20, 122, 440, 462))
        if self.tab == 0:
            self._draw_top(surf, game)
        else:
            self._draw_stats(surf, game)
        self.group.draw(surf)
        if self.confirm_timer > 0:
            draw_text(surf, "отмена через %d с" % math.ceil(self.confirm_timer), 165, 660, 16, (255, 150, 150), "center")
        if self.message_timer > 0:
            draw_text(surf, self.message, SCREEN_W / 2, 690, 18, YELLOW, "center", True,
                      alpha=int(255 * clamp(self.message_timer / 0.5, 0, 1)))

    def _draw_top(self, surf, game):
        # колонки сдвинуты влево: справа (x≈432) живёт мини-дудлер скина рекорда,
        # и число «монстров» не должно прятаться под ним
        cols = (62, 138, 218, 300, 378)
        for label, cx in zip(("МЕСТО", "ОЧКИ", "ВЫСОТА", "ДАТА", "МОНСТРЫ"), cols):
            draw_text(surf, label, cx, 142, 15, (160, 170, 210), "center", True)
        pygame.draw.line(surf, UI_BORDER, (32, 156), (448, 156), 1)
        try:
            records = list(game.save.records)
        except Exception:
            records = []
        try:
            new_rank = int(game.last_record_rank)
        except Exception:
            new_rank = 0
        for i in range(TOP_RECORDS):
            rank = i + 1
            row = pygame.Rect(30, 166 + i * 80, 420, 70)
            cy = row.centery
            is_new = (new_rank == rank and i < len(records))
            if is_new:
                a = pulse(self.t, 2.5, 0.35, 1.0)
                fill = lerp_color((70, 60, 40), GOLD, a * 0.55)
                rrect(surf, row, fill, 10)
                rrect(surf, row, lerp_color(GOLD, WHITE, a * 0.4), 10, 3)
            else:
                rrect(surf, row, (52, 60, 98) if i % 2 == 0 else (46, 54, 90), 10)
            if i < len(records) and isinstance(records[i], dict):
                rec = records[i]
                if rank <= 3:
                    draw_medal(surf, cols[0], cy, rank, self.t)
                else:
                    pygame.draw.circle(surf, (80, 90, 130), (cols[0], cy), 15)
                    pygame.draw.circle(surf, (120, 130, 170), (cols[0], cy), 15, 2)
                    draw_text(surf, str(rank), cols[0], cy, 18, WHITE, "center", True)
                score_col = GOLD if is_new else WHITE
                draw_text(surf, str(rec.get("score", 0)), cols[1], cy, 21, score_col, "center", True, shadow=(0, 0, 0))
                draw_text(surf, "%d м" % int(rec.get("height", 0)), cols[2], cy, 18, CYAN, "center", False)
                draw_text(surf, str(rec.get("date", "")), cols[3], cy, 15, LIGHT_GRAY, "center", False)
                draw_mini_monster(surf, cols[4] - 18, cy, 7)
                draw_text(surf, str(rec.get("monsters", 0)), cols[4] + 8, cy, 18, PINK, "center", True)
                # мини-дудлер скина, с которым поставлен рекорд
                skin = SKINS_BY_ID.get(rec.get("skin"))
                if skin is not None:
                    try:
                        draw_doodler(surf, row.right - 18, cy + 2, skin, self.t + i, scale=0.4)
                    except Exception:
                        pass
                if is_new:
                    tag = pygame.Rect(row.right - 66, row.y - 9, 60, 18)
                    rrect(surf, tag, lerp_color(GOLD, WHITE, pulse(self.t, 2.5, 0, 0.5)), 6)
                    draw_text(surf, "НОВЫЙ!", tag.centerx, tag.centery, 13, (60, 40, 0), "center", True)
            else:
                pygame.draw.circle(surf, (60, 68, 105), (cols[0], cy), 15)
                draw_text(surf, str(rank), cols[0], cy, 18, (110, 120, 160), "center", True)
                draw_text(surf, "— пусто —", 285, cy, 20, (120, 130, 170), "center")
        if not records:
            draw_text(surf, "Сыграй — и попади в топ!", SCREEN_W / 2, 570, 17, YELLOW, "center", True,
                      alpha=blink_alpha(self.t, 1.2, 120, 255))

    def _draw_stats(self, surf, game):
        try:
            st = dict(game.save.stats)
        except Exception:
            st = {}
        try:
            caps = game.save.caps
        except Exception:
            caps = 0
        try:
            # touch_launch при старте уже записал ТЕКУЩИЙ запуск — показываем прошлый
            last = getattr(game.save, "prev_launch", "") or "—"
        except Exception:
            last = "—"
        try:
            best = game.save.best_score
        except Exception:
            best = 0
        rows = [
            ("Игр сыграно", str(st.get("games_played", 0))),
            ("Время в игре", format_time(float(st.get("total_time", 0) or 0))),
            ("Лучший результат", str(best)),
            ("Монстров убито", str(st.get("monsters_killed", 0))),
            ("Платформ разбито", str(st.get("platforms_broken", 0))),
            ("Джетпаков подобрано", str(st.get("jetpacks_collected", 0))),
            ("Максимальное комбо", "x%d" % int(st.get("max_combo", 0) or 0)),
            ("Самая высокая точка", "%d м" % int(st.get("max_height", 0) or 0)),
            ("Кейсов открыто", str(st.get("cases_opened", 0))),
            ("Крышек заработано всего", str(st.get("caps_earned_total", 0))),
            ("Крышек сейчас", str(caps)),
            ("Скинов открыто", "%d/%d" % (_unlocked_count(game), len(SKINS))),
            ("Последний запуск", str(last)),
        ]
        draw_text(surf, "ОБЩАЯ СТАТИСТИКА", SCREEN_W / 2, 142, 18, (160, 170, 210), "center", True)
        pygame.draw.line(surf, UI_BORDER, (32, 158), (448, 158), 1)
        y = 176
        for i, (label, value) in enumerate(rows):
            row = pygame.Rect(30, y - 14, 420, 28)
            if i % 2 == 0:
                rrect(surf, row, (52, 60, 98), 6)
            draw_text(surf, label, 42, y, 17, LIGHT_GRAY, "midleft")
            draw_text(surf, value, 438, y, 18, GOLD if i in (2, 10) else WHITE, "midright", True)
            y += 30
        # крышки — иконкой
        draw_cap_icon(surf, 26, 176 + 10 * 30, 7)
        if getattr(game.save, "read_only", False):
            # файл сохранения не прочитался при старте — честно предупреждаем
            draw_text(surf, "Сохранение недоступно: прогресс не записывается", SCREEN_W / 2, y,
                      15, (255, 140, 140), "center", True)


# ═══════════════════════════════════════════════════════════════════════════
#  КЕЙСЫ: АНИМАЦИЯ ОТКРЫТИЯ
# ═══════════════════════════════════════════════════════════════════════════
class CaseOpening:
    """Анимация открытия кейса: shake (кейс трясётся) -> roll (рулетка с замедлением) -> reveal (вспышка, результат)."""

    def __init__(self, case, result, is_new):
        self.case = case
        self.result = result
        self.is_new = is_new
        self.state = "shake"
        self.timer = 0.0
        self.t = 0.0
        self.worn = False
        # карточки рулетки: случайные роллы + гарантированный результат под индексом ROULETTE_TARGET
        self.cards = [roll_case(case) for _ in range(ROULETTE_CARDS)]
        self.cards[ROULETTE_TARGET] = result
        # соседи результата не должны совпадать с ним (чтобы «почти выпало» читалось честно);
        # замену берём только из скинов, которые ЭТОТ кейс реально может выдать
        chances = case.get("chances") or RARITY_CHANCES
        droppable = [s for s in SKINS if chances.get(s.get("rarity"), 0) > 0]
        for k in (ROULETTE_TARGET - 1, ROULETTE_TARGET + 1):
            if 0 <= k < len(self.cards) and self.cards[k] is result:
                alt = [s for s in droppable if s is not result]
                if alt:
                    self.cards[k] = random.choice(alt)
        self.pos = 0.0
        self.end_pos = ROULETTE_TARGET * ROULETTE_PITCH + random.uniform(-0.32, 0.32) * ROULETTE_PITCH
        self.last_index = 0
        self.pointer_bob = 0.0
        self.flash = 0.0
        self.reveal_t = 0.0
        self.spark_acc = 0.0

    @property
    def rarity(self):
        return self.result.get("rarity", "common")

    # --- логика ---
    def update(self, dt, game, particles):
        self.t += dt
        self.timer += dt
        self.pointer_bob = max(0.0, self.pointer_bob - dt * 6)
        if self.state == "shake":
            self.spark_acc += dt
            if self.spark_acc > 0.08:
                self.spark_acc = 0.0
                prog = clamp(self.timer / CASE_SHAKE_TIME, 0, 1)
                particles.sparks(SCREEN_W / 2 + random.uniform(-30, 30), 330 + random.uniform(-30, 30),
                                 int(2 + 6 * prog), GOLD)
            if self.timer >= CASE_SHAKE_TIME:
                self.state = "roll"
                self.timer = 0.0
                particles.sparks(SCREEN_W / 2, 330, 30, WHITE, (200, 500))
                ui_sound(game, "pickup")
        elif self.state == "roll":
            u = clamp(self.timer / CASE_ROLL_TIME, 0, 1)
            self.pos = self.end_pos * ease_out_cubic(u)
            idx = int(round(self.pos / ROULETTE_PITCH))
            if idx != self.last_index:
                self.last_index = idx
                self.pointer_bob = 1.0
                ui_sound(game, "case_tick", 0.8)
            if self.timer >= CASE_ROLL_TIME + CASE_SETTLE_TIME:
                self._enter_reveal(game, particles)
        elif self.state == "reveal":
            self.reveal_t += dt
            self.flash = max(0.0, self.flash - dt * 1.3)
            if self.rarity == "imba" and self.reveal_t < 2.0:
                self.spark_acc += dt
                if self.spark_acc > 0.12:
                    self.spark_acc = 0.0
                    particles.sparks(random.uniform(60, SCREEN_W - 60), random.uniform(120, 420), 6, rainbow(self.t))

    def skip(self, game, particles):
        """Esc в процессе анимации — сразу к результату."""
        if self.state != "reveal":
            self.pos = self.end_pos
            self.last_index = ROULETTE_TARGET
            self._enter_reveal(game, particles)

    def _enter_reveal(self, game, particles):
        self.state = "reveal"
        self.timer = 0.0
        self.reveal_t = 0.0
        self.flash = 1.0
        r = self.rarity
        cx, cy = SCREEN_W / 2, 300
        if r == "imba":
            ui_sound(game, "case_imba")
            particles.confetti(cx, cy, 140, 360)
            particles.sparks(cx, cy, 40, GOLD, (200, 600))
            try:
                game.shake(12, 0.5)
            except Exception:
                pass
        elif r == "legendary":
            ui_sound(game, "case_epic")
            particles.confetti(cx, cy, 80, 300)
            particles.sparks(cx, cy, 24, GOLD)
        elif r == "epic":
            ui_sound(game, "case_open")
            particles.confetti(cx, cy, 50, 260)
        else:
            ui_sound(game, "case_open")
            particles.sparks(cx, cy, 14, rarity_color(r))

    # --- отрисовка ---
    def draw(self, surf, game):
        draw_text(surf, self.case.get("name", "КЕЙС"), SCREEN_W / 2, 40, 26, WHITE, "center", True, shadow=(0, 0, 0))
        if self.state == "shake":
            self._draw_shake(surf)
        elif self.state == "roll":
            self._draw_roll(surf)
        else:
            self._draw_reveal(surf)

    def _draw_shake(self, surf):
        prog = clamp(self.timer / CASE_SHAKE_TIME, 0, 1)
        amp = 2 + 12 * prog
        ox = math.sin(self.t * 45) * amp
        oy = math.cos(self.t * 38) * amp * 0.5
        draw_case_icon(surf, SCREEN_W / 2 + ox, 330 + oy, self.case, self.t, 2.2 + 0.4 * prog, glow=0.3 + prog)
        draw_text(surf, "ОТКРЫВАЕМ...", SCREEN_W / 2, 480, 28, GOLD, "center", True, shadow=(0, 0, 0),
                  alpha=blink_alpha(self.t, 4, 120, 255))
        draw_text(surf, MUSOR_REAL_SLOGAN, SCREEN_W / 2, 530, 16, (170, 180, 220), "center")
        draw_text(surf, "Esc - пропустить", SCREEN_W / 2, 690, 16, (140, 150, 190), "center")

    def _draw_card(self, surf, skin, cx, cy, scale=1.0, highlight=False):
        w = ROULETTE_CARD_W * scale
        h = ROULETTE_CARD_H * scale
        r = pygame.Rect(int(cx - w / 2), int(cy - h / 2), int(w), int(h))
        rc = rarity_color(skin.get("rarity"), self.t)
        rrect(surf, r.move(0, 4), (10, 12, 25), 12)
        rrect(surf, r, lerp_color(UI_PANEL, rc, 0.22 if highlight else 0.1), 12)
        rrect(surf, r, rc, 12, 3 if highlight else 2)
        try:
            draw_doodler(surf, cx, cy - 16 * scale, skin, self.t, scale=0.62 * scale)
        except Exception:
            pass
        name = skin_display_name(skin)
        size = fit_text_size(name, w - 10, int(15 * scale), 11, True)
        draw_text(surf, name, cx, r.bottom - 26 * scale, size, WHITE, "center", True, shadow=(0, 0, 0))
        draw_text(surf, RARITY_NAMES.get(skin.get("rarity"), ""), cx, r.bottom - 10 * scale, max(10, int(11 * scale)), rc, "center", True)

    def _draw_roll(self, surf):
        band = pygame.Rect(0, 230, SCREEN_W, 200)
        rrect(surf, band, (22, 26, 50), 0)
        pygame.draw.line(surf, UI_BORDER, (0, band.y), (SCREEN_W, band.y), 2)
        pygame.draw.line(surf, UI_BORDER, (0, band.bottom), (SCREEN_W, band.bottom), 2)
        cy = band.centery
        center_x = SCREEN_W / 2
        cur = int(round(self.pos / ROULETTE_PITCH))
        for i, skin in enumerate(self.cards):
            x = center_x + i * ROULETTE_PITCH - self.pos
            if x < -ROULETTE_PITCH or x > SCREEN_W + ROULETTE_PITCH:
                continue
            near = 1.0 - clamp(abs(x - center_x) / ROULETTE_PITCH, 0, 1)
            self._draw_card(surf, skin, x, cy, 0.92 + 0.12 * near, highlight=(i == cur))
        # затемнение по краям
        fade = pygame.Surface((90, band.h), pygame.SRCALPHA)
        for k in range(90):
            a = int(200 * (1 - k / 90) ** 1.5)
            pygame.draw.line(fade, (12, 14, 30, a), (k, 0), (k, band.h))
        surf.blit(fade, (0, band.y))
        surf.blit(pygame.transform.flip(fade, True, False), (SCREEN_W - 90, band.y))
        # указатель
        bob = self.pointer_bob * 6
        pygame.draw.polygon(surf, GOLD, [(center_x - 14, band.y - 4 - bob), (center_x + 14, band.y - 4 - bob), (center_x, band.y + 16 - bob)])
        pygame.draw.polygon(surf, GOLD, [(center_x - 14, band.bottom + 4 + bob), (center_x + 14, band.bottom + 4 + bob), (center_x, band.bottom - 16 + bob)])
        pygame.draw.line(surf, (255, 240, 180), (center_x, band.y + 6), (center_x, band.bottom - 6), 2)
        u = clamp(self.timer / CASE_ROLL_TIME, 0, 1)
        label = "КРУТИМ!" if u < 0.7 else ("ЕЩЁ ЧУТЬ-ЧУТЬ..." if u < 1 else "!!!")
        draw_text(surf, label, SCREEN_W / 2, 150, 30, GOLD, "center", True, shadow=(0, 0, 0))
        draw_text(surf, MUSOR_MAIN_SLOGAN, SCREEN_W / 2, 500, 16, (170, 180, 220), "center",
                  alpha=blink_alpha(self.t, 1.5, 100, 255))
        draw_text(surf, "Esc - пропустить", SCREEN_W / 2, 690, 16, (140, 150, 190), "center")

    def _draw_reveal(self, surf):
        skin = self.result
        rar = self.rarity
        rc = rarity_color(rar, self.t)
        cx, cy = SCREEN_W / 2, 290
        # лучи за дудлером
        rays = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        n = 14
        for k in range(n):
            a0 = self.t * 0.6 + k * 2 * math.pi / n
            a1 = a0 + math.pi / n * 0.7
            pts = [(cx, cy), (cx + math.cos(a0) * 600, cy + math.sin(a0) * 600), (cx + math.cos(a1) * 600, cy + math.sin(a1) * 600)]
            pygame.draw.polygon(rays, (rc[0], rc[1], rc[2], 38), pts)
        surf.blit(rays, (0, 0))
        draw_glow(surf, cx, cy, 130, rc, 80)
        pop = ease_out_back(self.reveal_t / 0.6)
        scale = 2.4 * max(0.05, pop)
        try:
            draw_doodler(surf, cx, cy + math.sin(self.t * 3) * 4, skin, self.t, scale=scale,
                         squash=1.0 + 0.05 * math.sin(self.t * 6), star=(rar in ("legendary", "imba")))
        except Exception:
            pass
        if self.reveal_t > 0.25:
            name = skin_display_name(skin)
            size = fit_text_size(name, 440, 40, 24, True)
            draw_text(surf, name, cx, 420, size, WHITE, "center", True, outline=lerp_color(rc, BLACK, 0.5), shadow=(0, 0, 0))
            draw_text(surf, RARITY_NAMES.get(rar, ""), cx, 462, 24, rc, "center", True, shadow=(0, 0, 0))
        if self.reveal_t > 0.5:
            if self.is_new:
                draw_text(surf, "НОВЫЙ СКИН!", cx, 505, 24, GREEN, "center", True, shadow=(0, 0, 0),
                          alpha=blink_alpha(self.t, 2, 150, 255))
            else:
                caps = RARITY_DUPE_CAPS.get(rar, 10)
                draw_wrapped_text(surf, "ДУБЛИКАТ! Продай в Мусорном магазине (+%d крышек)" % caps,
                                  cx, 494, 19, ORANGE, 420, True, shadow=(0, 0, 0))
        if rar == "imba":
            draw_text(surf, "И М Б А !!!", cx, 120, 44, rainbow(self.t * 2), "center", True, outline=BLACK,
                      alpha=blink_alpha(self.t, 5, 150, 255))
            draw_text(surf, MUSOR_REAL_SLOGAN, cx, 165, 17, GOLD, "center", True)
        elif rar == "legendary":
            draw_text(surf, "ЛЕГЕНДА!", cx, 130, 38, GOLD, "center", True, outline=(80, 50, 0))
        elif rar == "epic":
            draw_text(surf, "ЭПИК!", cx, 130, 34, rc, "center", True, outline=(40, 10, 60))
        if self.worn:
            draw_text(surf, "НАДЕТ!", cx, 560, 22, GOLD, "center", True, shadow=(0, 0, 0))
        if self.flash > 0:
            fl = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            fl.fill((rc[0], rc[1], rc[2], int(255 * self.flash)))
            surf.blit(fl, (0, 0))


# ═══════════════════════════════════════════════════════════════════════════
#  КЕЙСЫ: ЭКРАН МАГАЗИНА
# ═══════════════════════════════════════════════════════════════════════════
class CasesScreen(Screen):
    """Магазин кейсов: 4 карточки с ценой и описанием, кнопки ОТКРЫТЬ, анимация открытия внутри экрана."""

    def __init__(self):
        self.game = None
        self.t = 0.0
        self.back_state = "menu"
        self.backdrop = UIBackdrop()
        self.particles = UIParticles()
        self.opening = None
        self.last_case_index = 0
        self.message = ""
        self.message_timer = 0.0
        self.card_rects = [pygame.Rect(20, 92 + i * 126, 440, 114) for i in range(len(CASES))]
        self.open_btns = []
        for i, r in enumerate(self.card_rects):
            self.open_btns.append(_make_button((r.right - 130, r.bottom - 50, 116, 38), "ОТКРЫТЬ",
                                               (lambda i=i: self._open(i)), UI_BTN_OK, 18))
        self.back_btn = _make_button((140, 620, 200, 44), "НАЗАД", self._back, UI_BTN, 22)
        self.list_group = ButtonGroup(self.open_btns + [self.back_btn])
        self.again_btn = _make_button((28, 626, 136, 44), "ЕЩЁ РАЗ", self._again, UI_BTN, 18)
        self.wear_btn = _make_button((172, 626, 136, 44), "НАДЕТЬ", self._wear, UI_BTN_OK, 18)
        self.rback_btn = _make_button((316, 626, 136, 44), "НАЗАД", self._close_opening, UI_BTN, 18)
        self.reveal_group = ButtonGroup([self.again_btn, self.wear_btn, self.rback_btn])

    # --- действия ---
    def _caps(self):
        try:
            return int(self.game.save.caps)
        except Exception:
            return 0

    def _open(self, index):
        g = self.game
        if g is None or self.opening is not None or not (0 <= index < len(CASES)):
            return
        case = CASES[index]
        price = int(case.get("price", 0))
        if self._caps() < price:
            ui_sound(g, "hit")
            self.message = "Не хватает %d крышек. Играй и собирай!" % (price - self._caps())
            self.message_timer = 2.0
            return
        try:
            if not g.save.spend_caps(price):
                ui_sound(g, "hit")
                return
        except Exception as e:
            print("spend_caps error:", e)
            return
        try:
            g.save.update_stats(cases_opened=1)
        except Exception:
            pass
        result = roll_case(case)
        try:
            is_new = bool(g.save.unlock_skin(result["id"]))
        except Exception:
            is_new = False
        try:
            g.save.save(force=True)
        except Exception:
            pass
        self.last_case_index = index
        self.opening = CaseOpening(case, result, is_new)
        self.particles.clear()
        self.wear_btn.text = "НАДЕТЬ"
        self.wear_btn.enabled = True
        # фокус по умолчанию — «НАДЕТЬ» (безопасно), а не «ЕЩЁ РАЗ» (снова тратит крышки)
        self.reveal_group.set_index(1)
        ui_sound(g, "click")

    def _again(self):
        idx = self.last_case_index
        self.opening = None
        self._open(idx)

    def _wear(self):
        g = self.game
        if g is None or self.opening is None:
            return
        try:
            g.save.set_skin(self.opening.result["id"])
            if hasattr(g, "apply_skin"):
                g.apply_skin()
        except Exception as e:
            print("set_skin error:", e)
        self.opening.worn = True
        self.wear_btn.text = "НАДЕТ"
        self.wear_btn.enabled = False
        ui_sound(g, "click")

    def _close_opening(self):
        self.opening = None
        self.particles.clear()
        if self.game is not None:
            ui_sound(self.game, "click")

    def _back(self):
        if self.game is not None:
            ui_sound(self.game, "click")
            self.game.set_state(self.back_state)

    # --- интерфейс экрана ---
    def on_enter(self, game):
        self.game = game
        self.opening = None
        self.particles.clear()
        self.message_timer = 0.0
        self.list_group.set_index(0)

    def handle_event(self, event, game):
        self.game = game
        if self.opening is not None:
            if _is_key(event, pygame.K_ESCAPE):
                if self.opening.state != "reveal":
                    self.opening.skip(game, self.particles)
                else:
                    self._close_opening()
                return
            if self.opening.state != "reveal":
                if _is_key(event, pygame.K_SPACE, pygame.K_RETURN) or event.type == pygame.MOUSEBUTTONDOWN:
                    self.opening.skip(game, self.particles)
                return
            # короткая блокировка после вспышки: повторное нажатие «пропустить»
            # не должно сразу сработать как кнопка результата
            if self.opening.reveal_t < CASE_REVEAL_INPUT_DELAY and event.type != pygame.MOUSEMOTION:
                return
            self.reveal_group.handle_event(event)
            return
        if _is_key(event, pygame.K_ESCAPE):
            self._back()
            return
        self.list_group.handle_event(event)

    def update(self, dt, game):
        self.game = game
        self.t += dt
        self.backdrop.update(dt)
        self.particles.update(dt)
        if self.message_timer > 0:
            self.message_timer -= dt
        caps = self._caps()
        for i, b in enumerate(self.open_btns):
            b.enabled = caps >= int(CASES[i].get("price", 0))
        if self.opening is not None:
            self.opening.update(dt, game, self.particles)
            if self.opening.state == "reveal":
                self.again_btn.enabled = caps >= int(self.opening.case.get("price", 0))
                self.reveal_group.update(dt, _mouse_pos())
        else:
            self.list_group.update(dt, _mouse_pos())

    def draw(self, surf, game):
        self.game = game
        self.backdrop.draw(surf)
        if self.opening is not None:
            self.opening.draw(surf, game)
            self.particles.draw(surf)
            if self.opening.state == "reveal":
                self.reveal_group.draw(surf)
                draw_caps_counter(surf, SCREEN_W - 14, 24, self._caps(), 20, "midright")
            return
        draw_text(surf, "КЕЙСЫ", SCREEN_W / 2, 34, 34, GOLD, "center", True, shadow=(60, 40, 0))
        # подпись — НАД счётчиком: счётчик растёт влево и не наезжает ни на подпись, ни на заголовок
        draw_text(surf, "Твои крышки:", SCREEN_W - 14, 16, 14, LIGHT_GRAY, "midright")
        draw_caps_counter(surf, SCREEN_W - 14, 42, self._caps(), 22, "midright")
        caps = self._caps()
        for i, case in enumerate(CASES):
            r = self.card_rects[i]
            tier = case.get("tier", 1)
            main, dark = CASE_BOX_COLORS.get(tier, CASE_BOX_COLORS[1])
            afford = caps >= int(case.get("price", 0))
            draw_panel(surf, r, lerp_color(UI_PANEL, dark, 0.35), lerp_color(main, WHITE, 0.15) if afford else UI_BORDER, 14)
            bob = math.sin(self.t * 2 + i) * 3 if afford else 0
            draw_case_icon(surf, r.x + 60, r.centery + 4 + bob, case, self.t + i, 1.0, glow=0.25 if afford else 0.0)
            name_col = lerp_color(main, WHITE, 0.45) if tier < 4 else GOLD
            name_size = fit_text_size(case.get("name", ""), 190, 20, 15, True)
            draw_text(surf, case.get("name", ""), r.x + 116, r.y + 20, name_size, name_col, "midleft", True, shadow=(0, 0, 0))
            draw_cap_icon(surf, r.x + 124, r.y + 47, 9)
            draw_text(surf, str(case.get("price", 0)), r.x + 138, r.y + 47, 19, GOLD if afford else (200, 120, 120), "midleft", True)
            draw_wrapped_text(surf, case.get("desc", ""), r.x + 116 + 92, r.y + 64, 15, LIGHT_GRAY, 184, False, max_lines=2, line_gap=1)
            if not afford:
                need = int(case.get("price", 0)) - caps
                b = self.open_btns[i]
                draw_text(surf, "не хватает %d" % need, b.rect.centerx, b.rect.y - 8, 15, (255, 140, 140), "center", True)
        self.list_group.draw(surf)
        if self.message_timer > 0:
            draw_text(surf, self.message, SCREEN_W / 2, 600, 17, YELLOW, "center", True,
                      alpha=int(255 * clamp(self.message_timer / 0.5, 0, 1)))
        draw_text(surf, MUSOR_MAIN_SLOGAN, SCREEN_W / 2, 690, 16, (170, 180, 220), "center",
                  alpha=blink_alpha(self.t, 1.2, 110, 255))


# ═══════════════════════════════════════════════════════════════════════════
#  СКИНЫ
# ═══════════════════════════════════════════════════════════════════════════
class SkinsScreen(Screen):
    """Экран скинов: сетка 3×6, закрытые — серые силуэты с «?», активный — золотая рамка и «НАДЕТ»; стрелки/мышь."""

    def __init__(self):
        self.game = None
        self.t = 0.0
        self.back_state = "menu"
        self.cursor = 0
        self.focus_back = False
        self.message = ""
        self.message_timer = 0.0
        self.backdrop = UIBackdrop()
        self.back_btn = _make_button((140, 656, 200, 44), "НАЗАД", self._back, UI_BTN, 22)
        self.grid_x0 = (SCREEN_W - (SKIN_GRID_COLS * SKIN_CARD_W + (SKIN_GRID_COLS - 1) * 12)) // 2
        self.grid_y0 = 92
        self.pitch_x = SKIN_CARD_W + 12
        self.pitch_y = SKIN_CARD_H + 6

    def card_rect(self, i):
        c = i % SKIN_GRID_COLS
        r = i // SKIN_GRID_COLS
        return pygame.Rect(self.grid_x0 + c * self.pitch_x, self.grid_y0 + r * self.pitch_y, SKIN_CARD_W, SKIN_CARD_H)

    def _back(self):
        g = self.game
        if g is not None:
            ui_sound(g, "click")
            g.set_state(self.back_state)

    def _select(self, i):
        g = self.game
        if g is None or not (0 <= i < len(SKINS)):
            return
        skin = SKINS[i]
        try:
            unlocked = g.save.is_unlocked(skin["id"])
        except Exception:
            unlocked = False
        if unlocked:
            try:
                g.save.set_skin(skin["id"])
                if hasattr(g, "apply_skin"):
                    g.apply_skin()
            except Exception as e:
                print("set_skin error:", e)
            ui_sound(g, skin.get("sound") or "click")
            self.message = "%s - НАДЕТ!" % skin_display_name(skin)
            self.message_timer = 1.6
        else:
            ui_sound(g, "hit")
            self.message = "Скин закрыт. Открой его в КЕЙСАХ!"
            self.message_timer = 1.8

    def on_enter(self, game):
        self.game = game
        self.focus_back = False
        self.message_timer = 0.0
        try:
            ids = [s["id"] for s in SKINS]
            self.cursor = ids.index(game.save.skin_active) if game.save.skin_active in ids else 0
        except Exception:
            self.cursor = 0

    def handle_event(self, event, game):
        self.game = game
        if _is_key(event, pygame.K_ESCAPE):
            self._back()
            return
        n = len(SKINS)
        if event.type == pygame.KEYDOWN:
            k = event.key
            if k in (pygame.K_LEFT, pygame.K_a) and not self.focus_back:
                row = self.cursor // SKIN_GRID_COLS
                col = (self.cursor - 1) % SKIN_GRID_COLS
                self.cursor = min(n - 1, row * SKIN_GRID_COLS + col)
                ui_sound(game, "case_tick", 0.5)
            elif k in (pygame.K_RIGHT, pygame.K_d) and not self.focus_back:
                row = self.cursor // SKIN_GRID_COLS
                col = (self.cursor + 1) % SKIN_GRID_COLS
                self.cursor = min(n - 1, row * SKIN_GRID_COLS + col)
                ui_sound(game, "case_tick", 0.5)
            elif k in (pygame.K_UP, pygame.K_w):
                if self.focus_back:
                    self.focus_back = False
                elif self.cursor - SKIN_GRID_COLS >= 0:
                    self.cursor -= SKIN_GRID_COLS
                ui_sound(game, "case_tick", 0.5)
            elif k in (pygame.K_DOWN, pygame.K_s):
                if self.cursor + SKIN_GRID_COLS < n and not self.focus_back:
                    self.cursor += SKIN_GRID_COLS
                else:
                    self.focus_back = True
                ui_sound(game, "case_tick", 0.5)
            elif k in (pygame.K_RETURN, pygame.K_SPACE):
                if self.focus_back:
                    self._back()
                else:
                    self._select(self.cursor)
            return
        if event.type == pygame.MOUSEMOTION:
            for i in range(n):
                if self.card_rect(i).collidepoint(event.pos):
                    self.cursor = i
                    self.focus_back = False
                    break
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i in range(n):
                if self.card_rect(i).collidepoint(event.pos):
                    self.cursor = i
                    self._select(i)
                    return
        self.back_btn.handle_event(event)

    def update(self, dt, game):
        self.game = game
        self.t += dt
        self.backdrop.update(dt)
        if self.message_timer > 0:
            self.message_timer -= dt
        self.back_btn.selected = self.focus_back
        self.back_btn.update(dt, _mouse_pos())

    def draw(self, surf, game):
        self.game = game
        self.backdrop.draw(surf)
        draw_text(surf, "СКИНЫ", SCREEN_W / 2, 30, 34, GOLD, "center", True, shadow=(60, 40, 0))
        opened = _unlocked_count(game)
        draw_text(surf, "Открыто: %d/%d" % (opened, len(SKINS)), SCREEN_W / 2, 66, 18, LIGHT_GRAY, "center", True)
        try:
            caps = game.save.caps
            active = game.save.skin_active
        except Exception:
            caps, active = 0, DEFAULT_SKIN
        draw_caps_counter(surf, SCREEN_W - 14, 30, caps, 20, "midright")
        for i, skin in enumerate(SKINS):
            self._draw_card(surf, game, i, skin, active)
        self.back_btn.draw(surf)
        if self.message_timer > 0:
            draw_text(surf, self.message, SCREEN_W / 2, 642, 17, YELLOW, "center", True,
                      alpha=int(255 * clamp(self.message_timer / 0.4, 0, 1)))
        else:
            hint = "Стрелки - выбор, Enter - надеть, Esc - назад"
            draw_text(surf, hint, SCREEN_W / 2, 642, 15, (150, 160, 200), "center")

    def _draw_card(self, surf, game, i, skin, active_id):
        r = self.card_rect(i)
        try:
            unlocked = game.save.is_unlocked(skin["id"])
        except Exception:
            unlocked = skin["id"] == DEFAULT_SKIN
        try:
            dupes = int(game.save.dupes_of(skin["id"]))
        except Exception:
            dupes = 0
        rc = rarity_color(skin.get("rarity"), self.t) if unlocked else (95, 100, 120)
        is_active = unlocked and skin["id"] == active_id
        is_cursor = (i == self.cursor and not self.focus_back)
        rrect(surf, r.move(0, 3), (10, 12, 25), 10)
        rrect(surf, r, lerp_color(UI_PANEL, rc, 0.15) if unlocked else (45, 50, 70), 10)
        if is_active:
            rrect(surf, r, GOLD, 10, 4)
        else:
            rrect(surf, r, rc, 10, 2)
        if is_cursor:
            grow = int(2 + 2 * pulse(self.t, 2))
            rrect(surf, r.inflate(grow * 2, grow * 2), lerp_color(WHITE, rc, 0.3), 12, 2)
        cx, cy = r.centerx, r.y + 34
        if unlocked:
            try:
                draw_doodler(surf, cx, cy, skin, self.t + i * 0.7, scale=0.62,
                             squash=1.0 + (0.06 * math.sin(self.t * 5 + i) if is_cursor else 0.0))
            except Exception:
                pass
            name = skin_display_name(skin)
            size = fit_text_size(name, r.w - 10, 15, 11, True)
            draw_text(surf, name, cx, r.bottom - 12, size, WHITE, "center", True, shadow=(0, 0, 0))
        else:
            sil = pygame.Rect(cx - 15, cy - 18, 30, 36)
            pygame.draw.ellipse(surf, (75, 80, 100), sil)
            pygame.draw.ellipse(surf, (95, 100, 125), sil, 2)
            draw_text(surf, "?", cx, cy, 26, (200, 205, 220), "center", True)
            draw_text(surf, "???", cx, r.bottom - 12, 15, (130, 135, 160), "center", True)
        if is_active:
            tag = pygame.Rect(r.right - 54, r.y - 8, 52, 18)
            rrect(surf, tag, GOLD, 6)
            draw_text(surf, "НАДЕТ", tag.centerx, tag.centery, 13, (60, 40, 0), "center", True)
        if dupes > 0:
            badge = pygame.Rect(r.x - 4, r.y - 8, 34, 18)
            rrect(surf, badge, ORANGE, 6)
            draw_text(surf, "x%d" % (dupes + 1), badge.centerx, badge.centery, 13, BLACK, "center", True)


# ═══════════════════════════════════════════════════════════════════════════
#  МУСОРНЫЙ МАГАЗИН
# ═══════════════════════════════════════════════════════════════════════════
class MusorShopScreen(Screen):
    """«Мусорный магазин» MusorDrop: продажа дубликатов, абсурдные сделки (всегда можно ОТКАЗАТЬСЯ), промо дня."""

    def __init__(self):
        self.game = None
        self.t = 0.0
        self.back_state = "menu"
        self.backdrop = UIBackdrop()
        self.promo_used = False          # промо дня — один раз за запуск
        self.soul_sold = False           # душа у дудлера одна — продаётся один раз за запуск
        self.used_deals = set()          # индексы сделок, уже заключённых в этот визит
        self.message = ""
        self.message_color = YELLOW
        self.message_timer = 0.0
        self.deals = []
        self.deal_slots = [pygame.Rect(20, 236 + k * 92, 440, 84) for k in range(3)]
        self.sell_btn = _make_button((290, 130, 158, 40), "ПРОДАТЬ ВСЁ", self._sell_all, UI_BTN_OK, 16)
        self.deal_btns = []
        for k, slot in enumerate(self.deal_slots):
            yes = _make_button((290, slot.y + 8, 158, 32), "СОГЛАСИТЬСЯ", (lambda k=k: self._accept(k)), (200, 120, 40), 16)
            no = _make_button((290, slot.y + 46, 158, 32), "ОТКАЗАТЬСЯ", (lambda k=k: self._decline(k)), UI_BTN, 16)
            self.deal_btns.append((yes, no))
        self.promo_btn = _make_button((20, 544, 440, 40), "ЗАБРАТЬ +%d КРЫШЕК БЕСПЛАТНО" % PROMO_CAPS, self._promo, UI_BTN_OK, 18)
        self.back_btn = _make_button((140, 626, 200, 44), "НАЗАД", self._back, UI_BTN, 22)
        btns = [self.sell_btn]
        for yes, no in self.deal_btns:
            btns += [yes, no]
        btns += [self.promo_btn, self.back_btn]
        self.group = ButtonGroup(btns)

    # --- данные ---
    def _legendary_dupes(self, g):
        n = 0
        for s in SKINS:
            if s.get("rarity") == "legendary":
                try:
                    n += int(g.save.dupes_of(s["id"]))
                except Exception:
                    pass
        return n

    def _remove_legendary_dupes(self, g, count):
        left = count
        for s in SKINS:
            if left <= 0:
                break
            if s.get("rarity") == "legendary":
                try:
                    have = int(g.save.dupes_of(s["id"]))
                except Exception:
                    have = 0
                take = min(have, left)
                if take > 0:
                    g.save.remove_dupes(s["id"], take)
                    left -= take

    def _remove_all_dupes(self, g):
        for s in SKINS:
            try:
                n = int(g.save.dupes_of(s["id"]))
                if n > 0:
                    g.save.remove_dupes(s["id"], n)
            except Exception:
                pass

    def _caps(self):
        try:
            return int(self.game.save.caps)
        except Exception:
            return 0

    def _all_deals(self):
        """Список абсурдных сделок: текст, проверка доступности, действие (возвращает сообщение), подсказка."""
        return [
            {"text": "3 легендарки за 1 крышку?",
             "check": lambda g: self._legendary_dupes(g) >= 3,
             "apply": self._deal_legendaries, "need": "нужно 3 дубликата легендарок"},
            {"text": "Купить 100 крышек за 150 крышек",
             "check": lambda g: g.save.caps >= 150,
             "apply": self._deal_150, "need": "нужно 150 крышек"},
            {"text": "Обменять ВСЕ дубликаты на 1 крышку",
             "check": lambda g: g.save.total_dupes() > 0,
             "apply": self._deal_all_dupes, "need": "нужен хотя бы 1 дубликат"},
            {"text": "Получить 0 крышек бесплатно",
             "check": lambda g: True,
             "apply": self._deal_zero, "need": ""},
            {"text": "Секретный промокод за 200 крышек",
             "check": lambda g: g.save.caps >= 200,
             "apply": self._deal_secret, "need": "нужно 200 крышек"},
            {"text": "Купить воздух за 30 крышек",
             "check": lambda g: g.save.caps >= 30,
             "apply": self._deal_air, "need": "нужно 30 крышек"},
            {"text": "Продать душу дудлера за 1 крышку",
             "check": lambda g: not self.soul_sold,
             "apply": self._deal_soul, "need": "душа уже продана (она была одна)"},
        ]

    def _deal_legendaries(self, g):
        self._remove_legendary_dupes(g, 3)
        g.save.add_caps(1)
        return "СДЕЛКА ВЕКА! +1 крышка. Ты гений бизнеса."

    def _deal_150(self, g):
        if g.save.spend_caps(150):
            g.save.add_caps(100)
            return "Поздравляем! Минус 50 крышек. Это же выгодно?"
        return "Не хватает крышек."

    def _deal_all_dupes(self, g):
        self._remove_all_dupes(g)
        g.save.add_caps(1)
        return "Щедро. Очень щедро. +1 крышка."

    def _deal_zero(self, g):
        g.save.add_caps(0)
        return "СПАСИБО ЗА ПОКУПКУ!"

    def _deal_secret(self, g):
        if g.save.spend_caps(200):
            g.save.add_caps(PROMO_CAPS)
            return "Промокод %s активирован! +%d крышек! (за 200)" % (random.choice(PROMO_CODES), PROMO_CAPS)
        return "Не хватает крышек."

    def _deal_air(self, g):
        if g.save.spend_caps(30):
            return "Воздух доставлен. Дыши глубже."
        return "Не хватает крышек."

    def _deal_soul(self, g):
        if self.soul_sold:
            return "Душа уже продана. Второй нет."
        self.soul_sold = True
        g.save.add_caps(1)
        return "Душа принята. Приятно иметь с тобой дело!"

    def _pick_deals(self):
        deals = self._all_deals()
        self.deals = random.sample(deals, min(3, len(deals)))

    def _say(self, text, color=YELLOW, time=2.6):
        self.message = text
        self.message_color = color
        self.message_timer = time

    # --- действия кнопок ---
    def _dupe_list(self, g):
        items = []
        for s in SKINS:
            try:
                n = int(g.save.dupes_of(s["id"]))
            except Exception:
                n = 0
            if n > 0:
                items.append((s, n, RARITY_DUPE_CAPS.get(s.get("rarity"), 10)))
        return items

    def _sell_total(self, g):
        return sum(n * price for _, n, price in self._dupe_list(g))

    def _sell_all(self):
        g = self.game
        if g is None:
            return
        total = self._sell_total(g)
        if total <= 0:
            ui_sound(g, "hit")
            self._say("Дубликатов нет. Открой пару кейсов!", ORANGE)
            return
        self._remove_all_dupes(g)
        try:
            g.save.add_caps(total)
            g.save.save(force=True)
        except Exception as e:
            print("sell error:", e)
        ui_sound(g, "caps")
        self._say("Продано! +%d крышек. КЭШ ПОДНЯЛ!" % total, GOLD)

    def _accept(self, k):
        g = self.game
        if g is None or not (0 <= k < len(self.deals)):
            return
        deal = self.deals[k]
        if k in self.used_deals:
            ui_sound(g, "hit")
            self._say("Сделка уже заключена. Приходи ещё!", ORANGE)
            return
        try:
            ok = bool(deal["check"](g))
        except Exception:
            ok = False
        if not ok:
            ui_sound(g, "hit")
            self._say("Сделка недоступна: %s" % (deal.get("need") or "нет условий"), ORANGE)
            return
        # сделка одноразовая (в этот визит): повторные клики не «печатают» крышки
        self.used_deals.add(k)
        try:
            msg = deal["apply"](g)
            g.save.save(force=True)
        except Exception as e:
            print("deal error:", e)
            msg = "Что-то пошло не так. Как и всегда."
        ui_sound(g, "caps")
        self._say(msg, GOLD)

    def _decline(self, k):
        if self.game is not None:
            ui_sound(self.game, "click")
        self._say("Мудрое решение.", CYAN)

    def _promo(self):
        g = self.game
        if g is None:
            return
        if self.promo_used:
            ui_sound(g, "hit")
            self._say("Промо дня уже получено. Завтра (после перезапуска)!", ORANGE)
            return
        self.promo_used = True
        try:
            g.save.add_caps(PROMO_CAPS)
            g.save.save(force=True)
        except Exception as e:
            print("promo error:", e)
        ui_sound(g, "promo")
        self._say("ПРОМО ДНЯ активировано! +%d крышек!" % PROMO_CAPS, GOLD)
        self.promo_btn.text = "УЖЕ ПОЛУЧЕНО"
        self.promo_btn.enabled = False

    def _back(self):
        if self.game is not None:
            ui_sound(self.game, "click")
            self.game.set_state(self.back_state)

    # --- интерфейс экрана ---
    def on_enter(self, game):
        self.game = game
        self.t = 0.0
        self.message_timer = 0.0
        self._pick_deals()
        self.used_deals = set()
        self.group.set_index(0)
        if self.promo_used:
            self.promo_btn.text = "УЖЕ ПОЛУЧЕНО"
            self.promo_btn.enabled = False

    def handle_event(self, event, game):
        self.game = game
        if _is_key(event, pygame.K_ESCAPE):
            self._back()
            return
        self.group.handle_event(event)

    def update(self, dt, game):
        self.game = game
        self.t += dt
        self.backdrop.update(dt)
        if self.message_timer > 0:
            self.message_timer -= dt
        total = self._sell_total(game)
        self.sell_btn.text = "ПРОДАТЬ ВСЁ (+%d)" % total
        self.sell_btn.enabled = total > 0
        for k, (yes, no) in enumerate(self.deal_btns):
            if k < len(self.deals) and k not in self.used_deals:
                try:
                    yes.enabled = bool(self.deals[k]["check"](game))
                except Exception:
                    yes.enabled = False
            else:
                yes.enabled = False
        self.group.update(dt, _mouse_pos())

    def draw(self, surf, game):
        self.game = game
        self.backdrop.draw(surf)
        # мигающий главный слоган
        draw_wrapped_text(surf, MUSOR_MAIN_SLOGAN, SCREEN_W / 2 + 26, 12, 22, GOLD, 380, True, shadow=(60, 40, 0),
                          alpha=blink_alpha(self.t, 1.6, 140, 255), max_lines=2)
        draw_trash_bin(surf, 30, 40, 0.8, self.t, lid_lift=abs(math.sin(self.t * 4)) * 3)
        draw_caps_counter(surf, SCREEN_W - 14, 88, self._caps(), 20, "midright")
        # 1) дубликаты
        draw_text(surf, "ПРОДАТЬ ДУБЛИКАТЫ", 24, 88, 18, LIGHT_GRAY, "midleft", True)
        draw_panel(surf, (20, 100, 440, 100), radius=12)
        dupes = self._dupe_list(game)
        if not dupes:
            draw_text(surf, "Дубликатов пока нет.", 32, 128, 16, (150, 160, 200), "midleft")
            draw_text(surf, "Открывай кейсы - они появятся!", 32, 150, 16, (150, 160, 200), "midleft")
        else:
            y = 116
            for s, n, price in dupes[:3]:
                rc = rarity_color(s.get("rarity"), self.t)
                name = skin_display_name(s)
                size = fit_text_size(name, 130, 16, 12, True)
                draw_text(surf, name, 32, y, size, rc, "midleft", True)
                draw_text(surf, "x%d = +%d" % (n, n * price), 272, y, 16, GOLD, "midright", True)
                y += 22
            if len(dupes) > 3:
                draw_text(surf, "...и ещё %d" % (len(dupes) - 3), 32, y, 15, (150, 160, 200), "midleft")
        # 2) абсурдные сделки
        draw_text(surf, "АБСУРДНЫЕ СДЕЛКИ", 24, 222, 18, LIGHT_GRAY, "midleft", True)
        for k, slot in enumerate(self.deal_slots):
            draw_panel(surf, slot, radius=12, shadow=False)
            if k < len(self.deals):
                deal = self.deals[k]
                lines = wrap_text(deal["text"], 17, 250, True)[:2]
                for j, line in enumerate(lines):
                    draw_text(surf, line, 32, slot.y + 20 + j * 22, 17, WHITE, "midleft", True)
                try:
                    ok = bool(deal["check"](game))
                except Exception:
                    ok = False
                if k in self.used_deals:
                    draw_text(surf, "сделка заключена!", 32, slot.bottom - 16, 14, GOLD, "midleft", True)
                elif not ok and deal.get("need"):
                    draw_text(surf, deal["need"], 32, slot.bottom - 16, 14, (255, 150, 150), "midleft")
                else:
                    draw_text(surf, "выгодно? нет.", 32, slot.bottom - 16, 14, (140, 150, 190), "midleft")
        # 3) промо дня
        draw_text(surf, "ПРОМО ДНЯ", 24, 530, 18, LIGHT_GRAY, "midleft", True)
        draw_text(surf, "код: %s" % PROMO_CODES[int(self.t / 2) % len(PROMO_CODES)], SCREEN_W - 24, 530, 15, (150, 160, 200), "midright")
        self.group.draw(surf)
        if self.message_timer > 0:
            draw_wrapped_text(surf, self.message, SCREEN_W / 2, 590, 17, self.message_color, 440, True,
                              shadow=(0, 0, 0), alpha=int(255 * clamp(self.message_timer / 0.5, 0, 1)), max_lines=2, line_gap=1)
        draw_text(surf, MUSOR_REAL_SLOGAN, SCREEN_W / 2, 696, 16, (160, 170, 210), "center", True)


# ═══════════════════════════════════════════════════════════════════════════
#  ПАУЗА
# ═══════════════════════════════════════════════════════════════════════════
class PauseOverlay(Screen):
    """Оверлей паузы поверх мира: ПРОДОЛЖИТЬ / СКИНЫ / ЗВУК: ВКЛ|ВЫКЛ / МЕНЮ."""

    def __init__(self):
        self.game = None
        self.t = 0.0
        self.panel = pygame.Rect(90, 196, 300, 340)
        self.resume_btn = _make_button((120, 282, 240, 48), "ПРОДОЛЖИТЬ", self._resume, UI_BTN_OK, 22)
        self.skins_btn = _make_button((120, 340, 240, 48), "СКИНЫ", self._skins, UI_BTN, 22)
        self.sound_btn = _make_button((120, 398, 240, 48), "ЗВУК: ВКЛ", self._toggle_sound, UI_BTN, 22)
        self.menu_btn = _make_button((120, 456, 240, 48), "МЕНЮ", self._menu, UI_BTN_DANGER, 22)
        self.group = ButtonGroup([self.resume_btn, self.skins_btn, self.sound_btn, self.menu_btn])

    def _sound_on(self):
        try:
            return bool(self.game.sound.enabled)
        except Exception:
            return True

    def _refresh_sound_label(self):
        self.sound_btn.text = "ЗВУК: ВКЛ" if self._sound_on() else "ЗВУК: ВЫКЛ"

    def _resume(self):
        g = self.game
        if g is not None:
            ui_sound(g, "click")
            g.set_state("play")

    def _skins(self):
        g = self.game
        if g is None:
            return
        try:
            g.screens["skins"].back_state = "pause"
        except Exception:
            pass
        ui_sound(g, "click")
        g.set_state("skins")

    def _toggle_sound(self):
        g = self.game
        if g is None:
            return
        try:
            flag = g.sound.toggle()
        except Exception:
            flag = True
        try:
            g.save.settings["sound"] = bool(flag)
            g.save.mark_dirty()
        except Exception:
            pass
        self._refresh_sound_label()
        ui_sound(g, "click")

    def _menu(self):
        g = self.game
        if g is not None:
            ui_sound(g, "click")
            # выход из забега в меню — итог (рекорд, статистика) сохраняется, а не теряется
            abandon = getattr(g, "abandon_run", None)
            if abandon is not None:
                abandon()
            g.set_state("menu")

    def on_enter(self, game):
        self.game = game
        self.t = 0.0
        self._refresh_sound_label()
        self.group.set_index(0)

    def handle_event(self, event, game):
        self.game = game
        if _is_key(event, pygame.K_ESCAPE, pygame.K_p):
            self._resume()
            return
        self.group.handle_event(event)

    def update(self, dt, game):
        self.game = game
        self.t += dt
        self._refresh_sound_label()
        self.group.update(dt, _mouse_pos())

    def draw(self, surf, game):
        self.game = game
        draw_dim(surf, 150)
        draw_panel(surf, self.panel)
        draw_text(surf, "ПАУЗА", SCREEN_W / 2, 236, 38, GOLD, "center", True, shadow=(60, 40, 0))
        # две полоски «пауза» по бокам заголовка
        for dx in (-118, 106):
            pygame.draw.rect(surf, GOLD, pygame.Rect(SCREEN_W / 2 + dx, 224, 5, 24), border_radius=2)
            pygame.draw.rect(surf, GOLD, pygame.Rect(SCREEN_W / 2 + dx + 8, 224, 5, 24), border_radius=2)
        self.group.draw(surf)
        draw_text(surf, "Esc - продолжить", SCREEN_W / 2, 516, 16, (170, 180, 220), "center")
        try:
            draw_text(surf, "Очки: %d   Высота: %d м" % (int(game.score), int(game.height_m)), SCREEN_W / 2, 556, 17, LIGHT_GRAY, "center", True, shadow=(0, 0, 0))
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════════
#  GAME OVER
# ═══════════════════════════════════════════════════════════════════════════
class GameOverOverlay(Screen):
    """Панель конца игры: результат, место в топе, «до рекорда», кнопки ЗАНОВО / МЕНЮ / РЕКОРДЫ."""

    def __init__(self):
        self.game = None
        self.t = 0.0
        self.panel = pygame.Rect(40, 96, 400, 548)
        self.rank = 0
        self.first_record = False
        self.to_record = 0
        self.to_top5 = 0
        self.records_reset = False
        self.info_ready = False
        self.again_btn = _make_button((58, 566, 112, 46), "ЗАНОВО", self._again, UI_BTN_OK, 19)
        self.menu_btn = _make_button((184, 566, 112, 46), "МЕНЮ", self._menu, UI_BTN, 19)
        self.records_btn = _make_button((310, 566, 112, 46), "РЕКОРДЫ", self._records, (200, 150, 40), 18)
        self.group = ButtonGroup([self.again_btn, self.menu_btn, self.records_btn])

    def _compute(self, game):
        try:
            self.rank = int(game.last_record_rank)
        except Exception:
            self.rank = 0
        try:
            records = [r for r in game.save.records if isinstance(r, dict)]
        except Exception:
            records = []
        try:
            score = int(game.score)
        except Exception:
            score = 0
        self.first_record = (self.rank == 1 and len(records) <= 1)
        best = int(records[0].get("score", 0)) if records else 0
        self.to_record = max(0, best - score) if self.rank != 1 else 0
        if self.rank == 0 and records:
            last = int(records[-1].get("score", 0))
            self.to_top5 = max(1, last - score + 1)
        else:
            self.to_top5 = 0
        # место 0 при пустом ТОП-5 бывает только после СБРОСИТЬ РЕКОРДЫ (Game Over -> РЕКОРДЫ):
        # забег туда попадал, так что «В топ-5 не попал» было бы враньём
        self.records_reset = (self.rank == 0 and not records)
        self.info_ready = True

    def _again(self):
        if self.game is not None:
            self.game.start_game()

    def _menu(self):
        g = self.game
        if g is not None:
            ui_sound(g, "click")
            g.set_state("menu")

    def _records(self):
        g = self.game
        if g is None:
            return
        try:
            g.screens["records"].back_state = "gameover"
        except Exception:
            pass
        ui_sound(g, "click")
        g.set_state("records")

    def on_enter(self, game):
        self.game = game
        self.t = 0.0
        self._compute(game)
        self.group.set_index(0)

    def handle_event(self, event, game):
        self.game = game
        if _is_key(event, pygame.K_ESCAPE):
            self._menu()
            return
        if _is_key(event, pygame.K_r):
            self._again()
            return
        self.group.handle_event(event)

    def update(self, dt, game):
        self.game = game
        self.t += dt
        self.group.update(dt, _mouse_pos())

    def draw(self, surf, game):
        self.game = game
        if not self.info_ready:
            self._compute(game)
        draw_dim(surf, 140)
        appear = ease_out_back(self.t / 0.5)
        panel = self.panel.copy()
        panel.y = int(self.panel.y + (1 - appear) * 60)
        draw_panel(surf, panel)
        cx = SCREEN_W / 2
        y = panel.y + 44
        if self.rank == 1:
            title = "ПЕРВЫЙ РЕКОРД!" if self.first_record else "ПОБИТ РЕКОРД!"
            col = lerp_color(GOLD, WHITE, pulse(self.t, 3, 0, 0.6))
            draw_text(surf, title, cx, y, 36, col, "center", True, outline=(90, 60, 0), shadow=(0, 0, 0))
            for k in range(6):
                ang = self.t * 2 + k * math.pi / 3
                draw_star(surf, cx + math.cos(ang) * 190, y + math.sin(ang) * 22, 5 + 2 * math.sin(self.t * 5 + k), GOLD, rot=self.t)
        else:
            draw_text(surf, "ИГРА ОКОНЧЕНА", cx, y, 34, WHITE, "center", True, shadow=(0, 0, 0))
        y += 46
        try:
            score = int(game.score)
            height = int(game.height_m)
        except Exception:
            score, height = 0, 0
        try:
            rs = game.run_stats
            monsters = int(rs.get("monsters", 0))
            caps = int(rs.get("caps", 0))
        except Exception:
            monsters, caps = 0, 0
        draw_text(surf, "ОЧКИ", cx, y, 16, LIGHT_GRAY, "center", True)
        draw_text(surf, str(score), cx, y + 30, 42, GOLD, "center", True, shadow=(60, 40, 0))
        y += 72
        pygame.draw.line(surf, UI_BORDER, (panel.x + 30, y), (panel.right - 30, y), 1)
        y += 22
        draw_text(surf, "Высота", panel.x + 40, y, 18, LIGHT_GRAY, "midleft")
        draw_text(surf, "%d м" % height, panel.right - 40, y, 20, CYAN, "midright", True)
        y += 30
        draw_text(surf, "Монстров", panel.x + 40, y, 18, LIGHT_GRAY, "midleft")
        draw_mini_monster(surf, panel.right - 72, y, 7)
        draw_text(surf, str(monsters), panel.right - 40, y, 20, PINK, "midright", True)
        y += 30
        draw_text(surf, "Крышек за игру", panel.x + 40, y, 18, LIGHT_GRAY, "midleft")
        draw_caps_counter(surf, panel.right - 40, y, caps, 18, "midright")
        y += 40
        if self.rank > 0:
            draw_text(surf, "Ты #%d в топе!" % self.rank, cx, y, 26, GOLD, "center", True, shadow=(0, 0, 0),
                      alpha=blink_alpha(self.t, 1.5, 170, 255) if self.rank == 1 else 255)
            y += 34
            if self.rank > 1 and self.to_record > 0:
                draw_text(surf, "До рекорда: %d очков" % self.to_record, cx, y, 18, LIGHT_GRAY, "center")
                y += 26
        elif self.records_reset:
            draw_text(surf, "Рекорды сброшены", cx, y, 22, LIGHT_GRAY, "center", True)
            y += 30
        else:
            draw_text(surf, "В топ-5 не попал", cx, y, 22, LIGHT_GRAY, "center", True)
            y += 30
            if self.to_top5 > 0:
                draw_text(surf, "До топ-5: %d очков" % self.to_top5, cx, y, 18, LIGHT_GRAY, "center")
                y += 26
            if self.to_record > 0:
                draw_text(surf, "До рекорда: %d очков" % self.to_record, cx, y, 18, LIGHT_GRAY, "center")
                y += 26
        # дудлер с кружащимися звёздочками
        try:
            draw_doodler(surf, cx, panel.y + 430, _active_skin(game), self.t, scale=1.05, dizzy=True,
                          tilt=math.sin(self.t * 2) * 0.15)
        except Exception:
            pass
        # кнопки — двигаем вместе с панелью
        for b, x in ((self.again_btn, 58), (self.menu_btn, 184), (self.records_btn, 310)):
            b.rect.topleft = (x, panel.bottom - 78)
        self.group.draw(surf)
        draw_text(surf, "Enter/R - заново      Esc - меню", cx, panel.bottom - 18, 15, (170, 180, 220), "center")
        draw_text(surf, MUSOR_MAIN_SLOGAN, cx, SCREEN_H - 22, 15, (150, 160, 200), "center",
                  alpha=blink_alpha(self.t, 1.2, 90, 220))


# ═══════════════════════════════════════════════════════════════════════════
#  РЕКЛАМА MUSORDROP
# ═══════════════════════════════════════════════════════════════════════════
class AdManager:
    """Реклама MusorDrop: мигающий баннер в меню, мем-попапы (+крышки за любой ответ), баннер в игре с кнопкой ЗАКРЫТЬ (+5)."""

    def __init__(self, game):
        self.game = game
        self.t = 0.0
        # баннер меню
        self.banner_index = random.randrange(len(MUSOR_MENU_BANNERS)) if MUSOR_MENU_BANNERS else 0
        self.banner_timer = 0.0
        self.banner_rect = pygame.Rect(0, SCREEN_H - 44, SCREEN_W, 44)
        self.banner_hover = False
        # попап меню
        self.popup_open = False
        self.popup_text = ""
        self.popup_timer = random.uniform(MENU_POPUP_INTERVAL[0], MENU_POPUP_INTERVAL[1])
        self.popup_anim = 0.0
        self.popup_rect = pygame.Rect(50, 236, 380, 250)
        self.ok_btn = _make_button((70, 426, 160, 44), "ОК", self._popup_close, UI_BTN_OK, 20)
        self.later_btn = _make_button((250, 426, 160, 44), "НЕ СЕЙЧАС", self._popup_close, UI_BTN, 18)
        self.popup_group = ButtonGroup([self.ok_btn, self.later_btn])
        # экранные «+N крышек» меню — свой список, не мировые effects/texts Game
        self.menu_fx = []
        # баннер в игре
        self.game_timer = AD_FIRST_DELAY
        self.showing = False
        self.show_timer = 0.0
        self.close_delay = 0.0
        self.ingame_text = MUSOR_INGAME_BANNERS[0] if MUSOR_INGAME_BANNERS else MUSOR_MAIN_SLOGAN
        self.slide = 0.0
        # баннер — НИЖЕ ряда иконок бонусов (y≈98..138), чтобы не прятать их таймеры
        self.ingame_rect = pygame.Rect(12, 146, SCREEN_W - 24, 68)
        self.close_btn = _make_button((SCREEN_W - 164, 159, 140, 42), "ЗАКРЫТЬ (+%d)" % AD_CLOSE_CAPS,
                                      self._close_ingame, (200, 120, 40), 18, enabled=False)
        # закрыть можно и с клавиатуры: X (в игре не используется)
        self.close_btn.small_text = "клавиша X"
        self.close_btn.hotkeys.add(pygame.K_x)

    # ---------------- меню: баннер и попап ----------------
    def _popup_close(self):
        g = self.game
        self.popup_open = False
        self.popup_anim = 0.0
        self.popup_timer = random.uniform(MENU_POPUP_INTERVAL[0], MENU_POPUP_INTERVAL[1])
        # крышки — прямо в сохранение: попап меню не относится ни к одному забегу
        # (не трогаем run_stats прошлого забега и мировые списки эффектов)
        try:
            g.save.add_caps(AD_POPUP_CAPS)
        except Exception as exc:
            print("[Ads] popup caps:", exc)
        # «+10» всплывает у счётчика крышек меню (экранные координаты)
        self.menu_fx.append(CapsPopup(AD_POPUP_CAPS, 40, 52, world=False))
        ui_sound(g, "caps")

    def _open_popup(self):
        self.popup_open = True
        self.popup_anim = 0.0
        self.popup_text = random.choice(MUSOR_POPUPS) if MUSOR_POPUPS else MUSOR_MAIN_SLOGAN
        self.popup_group.set_index(0)
        ui_sound(self.game, "ad")

    def update_menu(self, dt):
        self.t += dt
        self.banner_timer += dt
        if self.banner_timer >= MENU_BANNER_SWITCH and MUSOR_MENU_BANNERS:
            self.banner_timer = 0.0
            self.banner_index = (self.banner_index + 1) % len(MUSOR_MENU_BANNERS)
        mouse = _mouse_pos()
        self.banner_hover = self.banner_rect.collidepoint(mouse)
        for fx in self.menu_fx:
            fx.update(dt, self.game)
        self.menu_fx = [fx for fx in self.menu_fx if fx.alive]
        if self.popup_open:
            self.popup_anim = min(1.0, self.popup_anim + dt * 3.5)
            self.popup_group.update(dt, mouse)
        else:
            self.popup_timer -= dt
            if self.popup_timer <= 0:
                self._open_popup()

    def handle_menu_event(self, event):
        """True — событие съедено (попап открыт или клик по баннеру)."""
        if self.popup_open:
            if _is_key(event, pygame.K_ESCAPE):
                self._popup_close()
                return True
            self.popup_group.handle_event(event)
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.banner_rect.collidepoint(event.pos):
            ui_sound(self.game, "click")
            try:
                self.game.set_state("musor")
            except Exception:
                pass
            return True
        return False

    def draw_menu(self, surf):
        self._draw_banner(surf)
        if self.popup_open:
            self._draw_popup(surf)
        for fx in self.menu_fx:
            fx.draw(surf, 0)

    def _draw_banner(self, surf):
        r = self.banner_rect
        base = (55, 35, 20) if not self.banner_hover else (75, 50, 25)
        pygame.draw.rect(surf, base, r)
        pygame.draw.line(surf, ORANGE, (0, r.y), (SCREEN_W, r.y), 2)
        # бегущая полосатая кайма
        stripe = pygame.Surface((SCREEN_W, 4), pygame.SRCALPHA)
        off = int(self.t * 60) % 24
        for x in range(-24, SCREEN_W + 24, 24):
            pygame.draw.rect(stripe, (255, 200, 40, 160), pygame.Rect(x + off, 0, 12, 4))
        surf.blit(stripe, (0, r.y + 2))
        draw_trash_bin(surf, 26, r.centery + 2, 0.55, self.t, lid_lift=abs(math.sin(self.t * 6)) * 2)
        text = MUSOR_MENU_BANNERS[self.banner_index % len(MUSOR_MENU_BANNERS)] if MUSOR_MENU_BANNERS else MUSOR_MAIN_SLOGAN
        alpha = blink_alpha(self.t, 1.4, 150, 255)
        lines = wrap_text(text, 15, SCREEN_W - 70, True)[:2]
        lh = 17
        y0 = r.centery - (len(lines) - 1) * lh / 2
        for i, line in enumerate(lines):
            draw_text(surf, line, 52 + (SCREEN_W - 70) / 2, y0 + i * lh, 15, GOLD, "center", True, shadow=(0, 0, 0), alpha=alpha)
        draw_text(surf, "ad", SCREEN_W - 6, r.y + 6, 11, (200, 160, 100), "topright")

    def _draw_popup(self, surf):
        draw_dim(surf, int(120 * self.popup_anim))
        s = ease_out_back(self.popup_anim)
        w = int(self.popup_rect.w * max(0.05, s))
        h = int(self.popup_rect.h * max(0.05, s))
        r = pygame.Rect(0, 0, w, h)
        r.center = self.popup_rect.center
        draw_panel(surf, r, (60, 40, 30), ORANGE, 16)
        if self.popup_anim < 0.85:
            return
        cx = r.centerx
        draw_trash_bin(surf, r.x + 40, r.y + 44, 1.1, self.t, lid_lift=abs(math.sin(self.t * 5)) * 4)
        draw_text(surf, "MUSORDROP", cx + 16, r.y + 30, 22, ORANGE, "center", True, shadow=(0, 0, 0))
        draw_text(surf, "реклама-мем", cx + 16, r.y + 52, 14, (200, 170, 140), "center")
        block = draw_wrapped_text(surf, self.popup_text, cx, r.y + 84, 22, WHITE, r.w - 40, True,
                                  shadow=(0, 0, 0), max_lines=2)
        caps_y = r.y + 160
        if "ШАНС НА БОЛЬШОЙ ДРОП" not in self.popup_text.upper():
            # в каждой всплывашке — главный слоган (мемная фраза попапа его не содержит)
            slogan_y = r.y + 84 + block + 12
            draw_text(surf, MUSOR_MAIN_SLOGAN, cx, slogan_y, 14, (255, 190, 120), "center", True)
            caps_y = max(caps_y, slogan_y + 22)
        draw_text(surf, "+%d крышек за любой ответ" % AD_POPUP_CAPS, cx, caps_y, 16, GOLD, "center", True,
                  alpha=blink_alpha(self.t, 2, 150, 255))
        self.ok_btn.rect.topleft = (r.x + 20, r.bottom - 60)
        self.later_btn.rect.topleft = (r.right - 180, r.bottom - 60)
        self.popup_group.draw(surf)

    # ---------------- игра: верхний баннер ----------------
    def reset_game_timer(self):
        self.game_timer = AD_FIRST_DELAY
        self.showing = False
        self.slide = 0.0
        self.close_btn.enabled = False

    def _close_ingame(self):
        if not self.showing:
            return
        self.showing = False
        g = self.game
        try:
            g.add_caps(AD_CLOSE_CAPS)
        except Exception:
            try:
                g.save.add_caps(AD_CLOSE_CAPS)
            except Exception:
                pass
        ui_sound(g, "caps")

    def _can_show(self):
        g = self.game
        try:
            if g.state != "play":
                return False
            p = getattr(g, "player", None)
            if p is not None and getattr(p, "dying", False):
                return False
        except Exception:
            return False
        return True

    def update_game(self, dt):
        self.t += dt
        if self.showing:
            self.show_timer -= dt
            self.close_delay -= dt
            self.close_btn.enabled = self.close_delay <= 0
            self.slide = min(1.0, self.slide + dt * 4)
            self.close_btn.update(dt, _mouse_pos())
            if self.show_timer <= 0 or not self._can_show():
                self.showing = False
        else:
            self.slide = max(0.0, self.slide - dt * 4)
            self.game_timer -= dt
            if self.game_timer <= 0:
                self.game_timer = AD_INGAME_INTERVAL
                if self._can_show():
                    self.showing = True
                    self.show_timer = AD_INGAME_DURATION
                    self.close_delay = AD_CLOSE_DELAY
                    self.close_btn.enabled = False
                    self.ingame_text = random.choice(MUSOR_INGAME_BANNERS) if MUSOR_INGAME_BANNERS else MUSOR_MAIN_SLOGAN
                    ui_sound(self.game, "ad", 0.7)

    def handle_game_event(self, event):
        """ЗАКРЫТЬ (+5): клик по кнопке или клавиша X — только когда задержка прошла
        и баннер реально виден (не во время улёта дудлера на game over)."""
        if not self.showing or not self.close_btn.enabled or not self._can_show():
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.close_btn.rect.collidepoint(event.pos):
            self.close_btn.handle_event(event)
            return True
        if event.type == pygame.KEYDOWN and event.key in self.close_btn.hotkeys:
            self.close_btn.handle_event(event)
            return True
        return False

    def draw_game(self, surf):
        if self.slide <= 0.01:
            return
        e = ease_out_cubic(self.slide)
        r = self.ingame_rect.copy()
        r.y = int(-r.h - 10 + (self.ingame_rect.y + r.h + 10) * e)
        draw_panel(surf, r, (60, 40, 30), ORANGE, 12)
        draw_trash_bin(surf, r.x + 30, r.centery + 2, 0.75, self.t, lid_lift=abs(math.sin(self.t * 6)) * 3)
        draw_wrapped_text(surf, self.ingame_text, r.x + 56 + 120, r.y + 10, 15, GOLD, 236, True, shadow=(0, 0, 0),
                          max_lines=2, line_gap=2)
        self.close_btn.rect.topleft = (r.right - 152, r.y + 13)
        if not self.close_btn.enabled and self.showing:
            frac = clamp(1 - self.close_delay / max(0.01, AD_CLOSE_DELAY), 0, 1)
            bar = pygame.Rect(self.close_btn.rect.x, self.close_btn.rect.bottom + 3, self.close_btn.rect.w, 4)
            pygame.draw.rect(surf, (90, 60, 40), bar, border_radius=2)
            pygame.draw.rect(surf, GOLD, pygame.Rect(bar.x, bar.y, int(bar.w * frac), 4), border_radius=2)
        self.close_btn.draw(surf)
        draw_text(surf, "реклама-мем", r.x + 58, r.bottom - 9, 11, (200, 160, 100), "midleft")


# ═══════════════════════════════════════════════════════════════════════════
# ═══ ЧАСТЬ 6: ФОН И ГЕНЕРАТОР УРОВНЯ ═══
# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
#  ЧАСТЬ 6: ФОН (небо, солнце/луна, облака, птички, звёзды, планеты, НЛО)
#           И ГЕНЕРАТОР УРОВНЯ (ряды платформ, монстры, бонусы, джетпаки)
# ═══════════════════════════════════════════════════════════════════════════


def bg_smoothstep(a, b, x):
    """Плавная S-образная интерполяция 0..1 при переходе x от a к b."""
    if b <= a:
        return 1.0 if x >= b else 0.0
    t = clamp((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


class Background:
    """Фон игры: небо по высоте (день -> закат -> ночь -> космос), солнце и луна,
    параллакс-облака, птички, мерцающие звёзды, планеты и фоновое НЛО.
    Все объекты переиспользуются: ушедшие вниз перекладываются наверх."""

    CLOUD_COUNT = 7
    BIRD_COUNT = 5
    STAR_COUNT = 120
    PLANET_COUNT = 3
    GRADIENT_CACHE_MAX = 24
    GRADIENT_STEPS = 96             # высота полоски-градиента до растяжения на экран

    def __init__(self):
        self.time = 0.0                 # аккумулятор времени для анимаций
        self.cam_y = 0.0
        self.last_cam_y = None          # для обнаружения «скачка» камеры (рестарт, телепорт)
        self.height_m = 0.0
        self.factors = (0.0, 0.0, 0.0)  # (закат, ночь, космос) — доли переходов
        self.gradient_cache = {}        # ключ (верх, низ) -> Surface градиента
        # Заранее отрендеренные спрайты (рисуются один раз)
        self.cloud_sprites = [self._make_cloud_sprite(i) for i in range(4)]
        self.planet_sprites = [self._make_planet_sprite(i) for i in range(len(BG_PLANETS))]
        self.sun_glow = self._make_glow(95, (255, 225, 120))
        self.moon_glow = self._make_glow(60, (200, 210, 255))
        # Наборы объектов фона
        self.clouds = []
        self.birds = []
        self.stars = []
        self.planets = []
        self.ufo = {"active": False, "x": 0.0, "y": 120.0, "vx": 40.0, "timer": 6.0, "phase": 0.0}
        self._seed_all(0.0)

    # ─────────────────────────── подготовка спрайтов ───────────────────────────
    @staticmethod
    def _make_glow(radius, color):
        """Мягкое свечение: концентрические круги с растущей к центру прозрачностью."""
        size = radius * 2
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        steps = 7
        for i in range(steps):
            r = int(radius * (1.0 - i / steps))
            alpha = int(14 + i * 9)
            pygame.draw.circle(surf, (color[0], color[1], color[2], alpha), (radius, radius), max(1, r))
        return surf

    @staticmethod
    def _make_cloud_sprite(variant):
        """Облако из нескольких кругов: тень снизу, светлое тело, блики сверху."""
        rnd = random.Random(1234 + variant)
        w, h = 150, 80
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        n = 4 + variant % 3
        puffs = []
        for i in range(n):
            cx = 30 + (w - 60) * i / max(1, n - 1) + rnd.uniform(-8, 8)
            edge = (i == 0 or i == n - 1)
            r = rnd.uniform(14, 21) if edge else rnd.uniform(20, 29)
            cy = h - 24 - r * 0.55 + rnd.uniform(-4, 4)
            puffs.append((cx, cy, r))
        shadow = (200, 212, 235, 255)
        body = (246, 250, 255, 255)
        light = (255, 255, 255, 255)
        # тень (нижняя часть) — те же круги, смещённые вниз
        for cx, cy, r in puffs:
            pygame.draw.circle(surf, shadow, (int(cx), int(cy + 6)), int(r))
        base_y = int(max(p[1] for p in puffs) + 4)
        pygame.draw.rect(surf, shadow, (int(puffs[0][0]), base_y - 6, int(puffs[-1][0] - puffs[0][0]), 12))
        # тело
        for cx, cy, r in puffs:
            pygame.draw.circle(surf, body, (int(cx), int(cy)), int(r))
        pygame.draw.rect(surf, body, (int(puffs[0][0]), base_y - 10, int(puffs[-1][0] - puffs[0][0]), 10))
        # блики
        for cx, cy, r in puffs:
            pygame.draw.circle(surf, light, (int(cx - r * 0.3), int(cy - r * 0.35)), max(2, int(r * 0.45)))
        return surf

    @staticmethod
    def _make_planet_sprite(variant):
        """Планета: диск с полосами, терминатор (тень), блик и, возможно, кольцо."""
        base, dark, ring = BG_PLANETS[variant % len(BG_PLANETS)]
        r = (26, 38, 20)[variant % 3]
        pad = r + 20 if ring else r + 4
        size = pad * 2
        c = pad
        disc = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(disc, base, (c, c), r)
        # полосы (широкие эллипсы), затем маска круга
        light_band = lerp_color(base, WHITE, 0.18)
        for k in range(-2, 3):
            yy = c + k * r * 0.36
            hh = max(3, int(r * 0.17))
            col = dark if k % 2 else light_band
            pygame.draw.ellipse(disc, col, pygame.Rect(c - r, int(yy - hh / 2), 2 * r, hh))
        mask = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255, 255), (c, c), r)
        disc.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        # тень-терминатор: полупрозрачный тёмный круг, смещённый вправо-вниз, обрезанный маской
        shade = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(shade, (0, 0, 30, 110), (int(c + r * 0.38), int(c + r * 0.25)), r)
        shade.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        disc.blit(shade, (0, 0))
        # блик (непрозрачный светлый тон: draw на SRCALPHA не смешивает, а заменяет пиксели)
        pygame.draw.circle(disc, lerp_color(base, WHITE, 0.5), (int(c - r * 0.42), int(c - r * 0.42)), max(2, r // 5))
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        if ring:
            ring_rect = pygame.Rect(c - r - 17, int(c - r * 0.28), 2 * r + 34, max(6, int(r * 0.56)))
            pygame.draw.ellipse(surf, (215, 195, 160, 170), ring_rect, 4)       # задняя часть кольца
            surf.blit(disc, (0, 0))
            front = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.ellipse(front, (235, 215, 175, 230), ring_rect, 4)
            surf.blit(front, (0, c), area=pygame.Rect(0, c, size, size - c))   # передняя половина поверх
        else:
            surf.blit(disc, (0, 0))
        return surf

    # ─────────────────────────── расстановка объектов ───────────────────────────
    def _seed_all(self, cam_y):
        """Расставить все объекты фона заново вокруг текущего положения камеры."""
        self.last_cam_y = cam_y
        self.clouds = [self._new_cloud(cam_y, initial=True) for _ in range(self.CLOUD_COUNT)]
        self.birds = [self._new_bird(cam_y, initial=True) for _ in range(self.BIRD_COUNT)]
        self.stars = [self._new_star(cam_y, initial=True) for _ in range(self.STAR_COUNT)]
        self.planets = [self._new_planet(cam_y, i, initial=True) for i in range(self.PLANET_COUNT)]

    def _new_cloud(self, cam_y, initial=False):
        """Новое облако: случайный спрайт, масштаб, скорость дрейфа; появляется над экраном."""
        sprite = random.choice(self.cloud_sprites)
        scale = random.uniform(0.55, 1.25)
        w = max(20, int(sprite.get_width() * scale))
        h = max(10, int(sprite.get_height() * scale))
        img = pygame.transform.smoothscale(sprite, (w, h))
        base = cam_y * BG_PARALLAX_CLOUDS
        py = base + (random.uniform(-h, SCREEN_H) if initial else -h - random.uniform(30, 260))
        return {"img": img, "w": w, "h": h, "x": random.uniform(-w, SCREEN_W), "py": py,
                "vx": random.uniform(8, 26) * random.choice((-1, 1)),
                "alpha": random.uniform(0.65, 1.0) * (0.7 + 0.3 * scale)}

    def _new_bird(self, cam_y, initial=False):
        """Новая птичка-«галочка»: летит по горизонтали, машет крыльями."""
        base = cam_y * BG_PARALLAX_CLOUDS
        py = base + (random.uniform(0, SCREEN_H * 0.7) if initial else -random.uniform(30, 320))
        direction = random.choice((-1, 1))
        return {"x": random.uniform(0, SCREEN_W), "py": py, "vx": direction * random.uniform(45, 90),
                "phase": random.uniform(0, math.tau), "size": random.uniform(0.7, 1.2)}

    def _new_star(self, cam_y, initial=False):
        """Новая звезда: слой 0 видна ночью и в космосе, слой 1 — только в космосе."""
        layer = 0 if random.random() < 0.55 else 1
        par = BG_PARALLAX_STARS if layer == 0 else BG_PARALLAX_STARS_FAR
        base = cam_y * par
        py = base + (random.uniform(0, SCREEN_H) if initial else -random.uniform(2, 40))
        roll = random.random()
        size = 1 if roll < 0.55 else (2 if roll < 0.88 else 3)
        return {"px": random.uniform(0, SCREEN_W - 3), "py": py, "size": size, "par": par, "layer": layer,
                "phase": random.uniform(0, math.tau), "speed": random.uniform(1.5, 4.5),
                "color": random.choice(BG_STAR_COLORS)}

    def _new_planet(self, cam_y, index, initial=False):
        """Новая планета: спрайт по индексу, медленный параллакс, появляется высоко над экраном."""
        img = self.planet_sprites[index % len(self.planet_sprites)]
        base = cam_y * BG_PARALLAX_PLANETS
        if initial:
            py = base + random.uniform(0, SCREEN_H) - index * 200
        else:
            py = base - img.get_height() - random.uniform(300, 1100)
        return {"img": img, "x": random.uniform(10, SCREEN_W - img.get_width() - 10), "py": py}

    # ─────────────────────────── вычисление неба ───────────────────────────
    @staticmethod
    def _factors(height_m):
        """Доли переходов (закат, ночь, космос) по высоте в метрах."""
        s1 = bg_smoothstep(BG_T_SUNSET[0], BG_T_SUNSET[1], height_m)
        s2 = bg_smoothstep(BG_T_NIGHT[0], BG_T_NIGHT[1], height_m)
        s3 = bg_smoothstep(BG_T_SPACE[0], BG_T_SPACE[1], height_m)
        return s1, s2, s3

    @staticmethod
    def _blend_zone(table, s1, s2, s3):
        """Цепочка lerp по зонам: день -> закат -> ночь -> космос."""
        c = lerp_color(table["day"], table["sunset"], s1)
        c = lerp_color(c, table["night"], s2)
        c = lerp_color(c, table["space"], s3)
        return c

    def _sky_colors(self, s1, s2, s3):
        """Цвет верха и низа неба."""
        return self._blend_zone(BG_SKY_TOP, s1, s2, s3), self._blend_zone(BG_SKY_BOTTOM, s1, s2, s3)

    def _gradient(self, top, bottom):
        """Вертикальный градиент неба. Рендерится ОДИН раз на пару цветов и кэшируется."""
        key = (tuple(int(c) // 4 * 4 for c in top), tuple(int(c) // 4 * 4 for c in bottom))
        grad = self.gradient_cache.get(key)
        if grad is None:
            steps = self.GRADIENT_STEPS
            column = pygame.Surface((1, steps), 0, 32)
            for i in range(steps):
                column.set_at((0, i), lerp_color(key[0], key[1], i / (steps - 1)))
            grad = pygame.transform.smoothscale(column, (SCREEN_W, SCREEN_H))
            try:
                if pygame.display.get_init() and pygame.display.get_surface() is not None:
                    grad = grad.convert()
            except pygame.error:
                pass
            if len(self.gradient_cache) >= self.GRADIENT_CACHE_MAX:
                self.gradient_cache.pop(next(iter(self.gradient_cache)))
            self.gradient_cache[key] = grad
        return grad

    def _sync_camera(self, cam_y):
        """Запомнить камеру; при резком скачке (рестарт, телепорт) переставить объекты фона."""
        if self.last_cam_y is None or abs(cam_y - self.last_cam_y) > SCREEN_H * 2.5:
            self._seed_all(cam_y)
        self.last_cam_y = cam_y
        self.cam_y = cam_y

    # ─────────────────────────── логика ───────────────────────────
    def update(self, dt, game):
        """Двигаем облака/птиц/НЛО, перекладываем ушедшие вниз объекты наверх."""
        self.time += dt
        cam_y = float(getattr(game, "cam_y", 0.0) or 0.0)
        self.height_m = float(getattr(game, "height_m", 0.0) or 0.0)
        self._sync_camera(cam_y)
        s1, s2, s3 = self._factors(self.height_m)
        self.factors = (s1, s2, s3)

        # Облака: дрейф по горизонтали с заворотом, уход вниз -> новое облако сверху
        for i, c in enumerate(self.clouds):
            c["x"] += c["vx"] * dt
            if c["x"] > SCREEN_W + 30:
                c["x"] = -c["w"] - 30
            elif c["x"] < -c["w"] - 30:
                c["x"] = SCREEN_W + 30
            if c["py"] - cam_y * BG_PARALLAX_CLOUDS > SCREEN_H + 40:
                self.clouds[i] = self._new_cloud(cam_y)

        # Птички
        for i, b in enumerate(self.birds):
            b["x"] += b["vx"] * dt
            if b["x"] > SCREEN_W + 30:
                b["x"] = -30
            elif b["x"] < -30:
                b["x"] = SCREEN_W + 30
            if b["py"] - cam_y * BG_PARALLAX_CLOUDS > SCREEN_H + 30:
                self.birds[i] = self._new_bird(cam_y)

        # Звёзды
        for i, st in enumerate(self.stars):
            if st["py"] - cam_y * st["par"] > SCREEN_H + 6:
                self.stars[i] = self._new_star(cam_y)

        # Планеты
        for i, p in enumerate(self.planets):
            if p["py"] - cam_y * BG_PARALLAX_PLANETS > SCREEN_H + 20:
                self.planets[i] = self._new_planet(cam_y, i)

        self._update_ufo(dt, s3)

    def _update_ufo(self, dt, s3):
        """Фоновое НЛО: в космосе изредка медленно пролетает через экран."""
        u = self.ufo
        if u["active"]:
            u["x"] += u["vx"] * dt
            u["phase"] += dt
            if (u["vx"] > 0 and u["x"] > SCREEN_W + 70) or (u["vx"] < 0 and u["x"] < -70):
                u["active"] = False
                u["timer"] = random.uniform(7.0, 15.0)
        elif s3 > 0.3:
            u["timer"] -= dt
            if u["timer"] <= 0:
                direction = random.choice((-1, 1))
                u["active"] = True
                u["x"] = -60.0 if direction > 0 else SCREEN_W + 60.0
                u["vx"] = direction * random.uniform(35.0, 65.0)
                u["y"] = random.uniform(70.0, 330.0)
                u["phase"] = 0.0

    # ─────────────────────────── отрисовка ───────────────────────────
    def draw(self, surf, game):
        """Нарисовать весь фон на surf (экранные координаты)."""
        cam_y = float(getattr(game, "cam_y", 0.0) or 0.0)
        height_m = float(getattr(game, "height_m", 0.0) or 0.0)
        self._sync_camera(cam_y)
        s1, s2, s3 = self._factors(height_m)
        top, bottom = self._sky_colors(s1, s2, s3)
        surf.blit(self._gradient(top, bottom), (0, 0))
        sky_mid = lerp_color(top, bottom, 0.5)

        self._draw_stars(surf, cam_y, s2, s3, sky_mid)
        self._draw_planets(surf, cam_y, s3)
        self._draw_sun(surf, s1, s2, sky_mid)
        self._draw_moon(surf, s2, s3, sky_mid)
        self._draw_ufo(surf, s3, sky_mid)
        self._draw_clouds(surf, cam_y, s2)
        self._draw_birds(surf, cam_y, s2, sky_mid)

    def _draw_stars(self, surf, cam_y, s2, s3, sky_mid):
        """Мерцающие звёзды: яркость по синусу, крупные — с крестиком-искоркой."""
        if s2 <= 0.02:
            return
        t = self.time
        for st in self.stars:
            vis = s2 if st["layer"] == 0 else s3
            if vis <= 0.02:
                continue
            sy = st["py"] - cam_y * st["par"]
            if sy < -4 or sy > SCREEN_H + 4:
                continue
            tw = 0.55 + 0.45 * math.sin(t * st["speed"] + st["phase"])
            col = lerp_color(sky_mid, st["color"], vis * tw)
            size = st["size"]
            x = int(st["px"])
            y = int(sy)
            surf.fill(col, (x, y, size, size))
            if size >= 3 and tw > 0.82:
                cx, cy = x + 1, y + 1
                arm = size + 2
                pygame.draw.line(surf, col, (cx - arm, cy), (cx + arm, cy))
                pygame.draw.line(surf, col, (cx, cy - arm), (cx, cy + arm))

    def _draw_planets(self, surf, cam_y, s3):
        """Планеты проявляются с приходом космоса."""
        if s3 <= 0.02:
            return
        alpha = int(255 * s3)
        for p in self.planets:
            img = p["img"]
            sy = p["py"] - cam_y * BG_PARALLAX_PLANETS
            if sy + img.get_height() < 0 or sy > SCREEN_H:
                continue
            img.set_alpha(alpha)
            surf.blit(img, (int(p["x"]), int(sy)))

    def _draw_sun(self, surf, s1, s2, sky_mid):
        """Солнце: днём высоко и жёлтое, на закате опускается к горизонту и краснеет, ночью уходит."""
        vis = 1.0 - s2
        if vis <= 0.02:
            return
        x = SCREEN_W - 95
        y = lerp(115.0, 470.0, s1) + s2 * 420.0
        r = int(lerp(32, 46, s1))
        color = lerp_color((255, 236, 120), (255, 140, 60), s1)
        color = lerp_color(sky_mid, color, vis)
        # свечение
        glow = self.sun_glow
        glow.set_alpha(int(170 * vis * (0.9 + 0.1 * math.sin(self.time * 1.3))))
        surf.blit(glow, (int(x - glow.get_width() / 2), int(y - glow.get_height() / 2)))
        # лучи, медленно вращаются
        ray_col = lerp_color(sky_mid, color, vis * 0.55)
        for i in range(10):
            ang = self.time * 0.25 + i * math.tau / 10
            r0 = r + 8 + 3 * math.sin(self.time * 2 + i)
            r1 = r0 + 12 + 5 * math.sin(self.time * 3 + i * 1.7)
            pygame.draw.line(surf, ray_col,
                             (int(x + math.cos(ang) * r0), int(y + math.sin(ang) * r0)),
                             (int(x + math.cos(ang) * r1), int(y + math.sin(ang) * r1)), 2)
        pygame.draw.circle(surf, color, (x, int(y)), r)
        pygame.draw.circle(surf, lerp_color(color, WHITE, 0.35), (int(x - r * 0.28), int(y - r * 0.28)), int(r * 0.42))

    def _draw_moon(self, surf, s2, s3, sky_mid):
        """Луна: поднимается с приходом ночи, в космосе становится чуть меньше."""
        vis = s2
        if vis <= 0.02:
            return
        x = 95
        y = lerp(SCREEN_H + 70.0, 130.0, s2) + s3 * 30.0
        r = int(30 - s3 * 6)
        color = lerp_color(sky_mid, (236, 238, 226), vis)
        glow = self.moon_glow
        glow.set_alpha(int(130 * vis))
        surf.blit(glow, (int(x - glow.get_width() / 2), int(y - glow.get_height() / 2)))
        pygame.draw.circle(surf, color, (x, int(y)), r)
        crater = lerp_color(color, (165, 170, 168), 0.55 * vis)
        for dx, dy, cr in ((-0.35, -0.2, 0.22), (0.3, 0.1, 0.16), (-0.05, 0.45, 0.13), (0.35, -0.45, 0.1)):
            pygame.draw.circle(surf, crater, (int(x + dx * r), int(y + dy * r)), max(1, int(cr * r)))
        pygame.draw.circle(surf, lerp_color(color, WHITE, 0.4), (int(x - r * 0.4), int(y - r * 0.5)), max(1, int(r * 0.18)))

    def _draw_ufo(self, surf, s3, sky_mid):
        """Фоновое НЛО: тарелка с куполом и мигающими огнями."""
        u = self.ufo
        if not u["active"] or s3 <= 0.05:
            return
        vis = s3
        x = int(u["x"])
        y = int(u["y"] + math.sin(u["phase"] * 1.7) * 8)
        body = lerp_color(sky_mid, (175, 180, 195), vis)
        dark = lerp_color(sky_mid, (110, 115, 135), vis)
        dome = lerp_color(sky_mid, (140, 220, 240), vis)
        pygame.draw.ellipse(surf, dark, (x - 26, y - 4, 52, 16))
        pygame.draw.ellipse(surf, body, (x - 26, y - 8, 52, 14))
        pygame.draw.ellipse(surf, dome, (x - 11, y - 18, 22, 16))
        pygame.draw.ellipse(surf, lerp_color(dome, WHITE, 0.45), (x - 7, y - 16, 8, 5))
        for i in range(4):
            lx = x - 18 + i * 12
            on = math.sin(u["phase"] * 6 + i * 1.6) > 0
            lc = (255, 230, 80) if on else (200, 80, 80)
            pygame.draw.circle(surf, lerp_color(sky_mid, lc, vis), (lx, y + 3), 2)

    def _draw_clouds(self, surf, cam_y, s2):
        """Облака видны днём и на закате, растворяются к ночи."""
        day = 1.0 - s2
        if day <= 0.02:
            return
        for c in self.clouds:
            sy = c["py"] - cam_y * BG_PARALLAX_CLOUDS
            if sy > SCREEN_H or sy + c["h"] < 0:
                continue
            alpha = int(235 * c["alpha"] * day)
            if alpha <= 3:
                continue
            c["img"].set_alpha(alpha)
            surf.blit(c["img"], (int(c["x"]), int(sy)))

    def _draw_birds(self, surf, cam_y, s2, sky_mid):
        """Птички-«галочки»: две линии-крыла, машут по синусу."""
        vis = 1.0 - s2
        if vis <= 0.05:
            return
        col = lerp_color(sky_mid, (45, 45, 70), vis * 0.85)
        t = self.time
        for b in self.birds:
            sy = b["py"] - cam_y * BG_PARALLAX_CLOUDS + math.sin(t * 2.0 + b["phase"]) * 6
            if sy < -20 or sy > SCREEN_H + 20:
                continue
            flap = math.sin(t * 11.0 + b["phase"])
            w = 7 * b["size"]
            h = 5 * b["size"]
            x = b["x"]
            pygame.draw.lines(surf, col, False,
                              [(int(x - w), int(sy - flap * h)), (int(x), int(sy + 2)), (int(x + w), int(sy - flap * h))], 2)


class LevelGenerator:
    """Генератор бесконечного уровня: ряды платформ с гарантированной проходимостью,
    ломающиеся платформы (не подряд), монстры по высоте, бонусы, джетпаки и уборка
    всего, что ушло ниже экрана.

    Паркур-забег (иногда): PARKOUR_RUN_ROWS рядов подряд с ломающейся «ступенькой»
    в каждом — дорожка почти вертикально вверх с шагом PARKOUR_RUN_GAP, так что путь
    «по умолчанию» идёт по ломающимся подряд (паркур-бонус реально достижим).
    Твёрдая основная платформа есть в КАЖДОМ ряду забега (в стороне от дорожки) —
    это не «лестница смерти»: сорвавшийся игрок всегда может уйти на твёрдую."""

    START_PLATFORM_W = 160      # ширина стартовой площадки
    EXTRA_GAP = 24              # минимальный горизонтальный зазор между платформами ряда
    SIDE_MARGIN = 8             # отступ платформ от краёв экрана
    MAX_ROWS_PER_CALL = 2000    # предохранитель от бесконечного цикла

    def __init__(self, game):
        self.game = game
        self.next_row_y = float(PLAYER_START_Y)
        self.row_index = 0
        self.last_breakable_row = -10
        self.last_monster_row = -10
        self.last_main = None            # основная платформа последнего ряда
        self.last_main_y = float(PLAYER_START_Y)
        # Ряды НИЖЕ этой мировой y (y больше) генерируются без врагов —
        # «зона прибытия» после телепорта НЛО. None — ограничения нет.
        self.monster_free_below_y = None
        self.parkour_left = 0            # сколько рядов паркур-забега ещё впереди
        self.parkour_lane_x = None       # x предыдущей ступеньки забега (None — забег только начинается)

    # ─────────────────────────── вспомогательное ───────────────────────────
    def _difficulty(self):
        """Сложность 0..1 из game.difficulty (с защитой от None)."""
        d = getattr(self.game, "difficulty", 0.0)
        try:
            return clamp(float(d), 0.0, 1.0)
        except (TypeError, ValueError):
            return 0.0

    def _height_m(self):
        """Высота игрока в метрах (с защитой от None)."""
        h = getattr(self.game, "height_m", 0.0)
        try:
            return max(0.0, float(h))
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _row_m(y):
        """Высота РЯДА (мировая y верха платформы) в метрах. Ряды генерируются на экран
        вперёд, поэтому пороги «от N м» сравниваются с высотой самого ряда, а не игрока."""
        try:
            return max(0.0, (PLAYER_START_Y - float(y)) / PIXELS_PER_METER) if PIXELS_PER_METER else 0.0
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _plat_x(p):
        return float(getattr(p, "x", p.rect.x))

    @staticmethod
    def _plat_w(p):
        return float(getattr(p, "w", p.rect.width))

    @staticmethod
    def _plat_top(p):
        top = getattr(p, "top", None)
        if top is None:
            top = getattr(p, "y", p.rect.top)
        return float(top)

    def _in_monster_free_zone(self, y):
        """Ряд на высоте y попадает в зону без врагов (после телепорта)."""
        limit = self.monster_free_below_y
        return limit is not None and y > limit

    def _free_x(self, w, occupied):
        """Случайный x для платформы ширины w, не пересекающейся с occupied (зазор >= EXTRA_GAP).
        Возвращает None, если места нет."""
        lo = self.SIDE_MARGIN
        hi = SCREEN_W - self.SIDE_MARGIN
        blocks = sorted((self._plat_x(o) - self.EXTRA_GAP, self._plat_x(o) + self._plat_w(o) + self.EXTRA_GAP)
                        for o in occupied)
        segments = []
        cur = float(lo)
        for b0, b1 in blocks:
            if b0 - cur >= w:
                segments.append((cur, b0 - w))
            cur = max(cur, b1)
        if hi - cur >= w:
            segments.append((cur, hi - w))
        if not segments:
            return None
        weights = [max(1.0, s1 - s0) for s0, s1 in segments]
        s0, s1 = random.choices(segments, weights=weights)[0]
        return random.randint(int(math.ceil(s0)), int(math.floor(s1)))

    @staticmethod
    def _place_on_platform(monster, plat):
        """Посадить монстра на платформу: y = top - h/2, синхронизировать rect."""
        h = float(getattr(monster, "h", 48) or 48)
        top = LevelGenerator._plat_top(plat)
        monster.y = top - h / 2
        rect = getattr(monster, "rect", None)
        if rect is not None:
            try:
                rect.center = (int(round(monster.x)), int(round(monster.y)))
            except (AttributeError, TypeError):
                pass

    # ─────────────────────────── публичный API ───────────────────────────
    def reset(self):
        """Стартовая широкая площадка под игроком и первые ряды на экран + запас."""
        g = self.game
        player = getattr(g, "player", None)
        px = float(getattr(player, "x", SCREEN_W / 2) or SCREEN_W / 2)
        w = self.START_PLATFORM_W
        x = int(clamp(px - w / 2, self.SIDE_MARGIN, SCREEN_W - w - self.SIDE_MARGIN))
        start_y = int(PLAYER_START_Y + PLAYER_H / 2)
        start = NormalPlatform(x, start_y, w)
        g.platforms.append(start)
        self.last_main = start
        self.last_main_y = float(start_y)
        self.row_index = 0
        self.last_breakable_row = -10
        self.last_monster_row = -10
        self.monster_free_below_y = None
        self.parkour_left = 0
        self.parkour_lane_x = None
        self.next_row_y = start_y - random.uniform(ROW_GAP_MIN, ROW_GAP_MAX_EASY)
        self.generate_until(float(getattr(g, "cam_y", 0.0) or 0.0))

    def generate_until(self, top_y):
        """Генерировать ряды, пока не заполнен экран от top_y плюс один экран запаса сверху."""
        limit = top_y - SCREEN_H
        count = 0
        while self.next_row_y > limit:
            self.spawn_row(self.next_row_y)
            d = self._difficulty()
            if self.parkour_left > 0:
                # впереди ряд паркур-забега: ровный шаг — до следующей ступеньки всегда
                # допрыгнуть, а «перепрыгнуть» её на ряд выше уже нельзя
                gap = random.uniform(*PARKOUR_RUN_GAP)
            else:
                gap_max = lerp(ROW_GAP_MAX_EASY, ROW_GAP_MAX_HARD, d)
                gap = random.uniform(ROW_GAP_MIN, gap_max)
            self.next_row_y -= gap
            count += 1
            if count >= self.MAX_ROWS_PER_CALL:
                # аварийный выход (на практике недостижимо): дальше продолжим с текущей позиции
                break

    def spawn_row(self, y):
        """Один ряд уровня на высоте y: основная платформа + доп. объекты по правилам.
        Все пороги «от N м» — по высоте самого ряда (row_m): ряды создаются на экран
        выше игрока, и первые монстры должны появляться ровно с SAFE_METERS."""
        d = self._difficulty()
        y = int(round(y))
        row_m = self._row_m(y)

        parkour_row = self.parkour_left > 0
        if parkour_row:
            # 0) Ряд паркур-забега: сначала ступенька-дорожка, затем твёрдая основная
            #    в стороне от неё (не движущаяся — она проезжала бы сквозь ступеньку)
            breakable = self._spawn_parkour_breakable(y)
            main = self._spawn_main(y, d, row_m, occupied=[breakable], allow_moving=False)
            occupied = [main, breakable]
            self.last_breakable_row = self.row_index
            self.parkour_left -= 1
            main_moving = False
        else:
            # 1) Основная «твёрдая» платформа — гарантирует проходимость
            main = self._spawn_main(y, d, row_m)
            occupied = [main]
            # движущаяся платформа ездит по всему ряду: соседка в том же ряду оказалась бы
            # у неё на пути (плашки проезжали бы друг сквозь друга), поэтому такой ряд — без соседей
            main_moving = getattr(main, "kind", "") == "moving"
            breakable = None

        # 2) Дополнительная ломающаяся платформа (не в первых рядах и не в соседних рядах)
        if (not parkour_row
                and not main_moving
                and self.row_index >= SAFE_ROWS
                and (self.row_index - self.last_breakable_row) >= 2
                and random.random() < lerp(0.10, 0.45, d)):
            breakable = self._spawn_breakable(y, occupied)
            if breakable is not None:
                self.last_breakable_row = self.row_index
                occupied.append(breakable)

        # 3) Иногда вторая обычная платформа на низкой сложности
        if not parkour_row and not main_moving and breakable is None and d < 0.5 and random.random() < 0.10:
            extra = self._spawn_second_normal(y, occupied)
            if extra is not None:
                occupied.append(extra)

        # 4) Монстр (с SAFE_METERS высоты ряда, не в двух соседних рядах) или пасхалка Чирик.
        #    Паркур-забег — без монстров: это награда за ловкость, а не ловушка
        monster_plat = None
        if (not parkour_row
                and row_m >= SAFE_METERS
                and (self.row_index - self.last_monster_row) >= 2
                and not self._in_monster_free_zone(y)
                and random.random() < lerp(MONSTER_CHANCE_MIN, MONSTER_CHANCE_MAX, d)):
            monster_plat = self._spawn_monster(y, d, row_m, main, breakable)
            self.last_monster_row = self.row_index
        elif (not parkour_row and row_m >= 100 and getattr(main, "kind", "") in ("normal", "moving")
              and random.random() < 0.015):
            # Чирика не сажаем на ракету или пружину: ракета сгорает, пружина подбрасывает
            self._spawn_chirik(main)
            monster_plat = main

        # 5) Бонус на основной платформе (если на ней нет монстра)
        if row_m >= 50 and monster_plat is not main and random.random() < BONUS_SPAWN_CHANCE:
            self._spawn_bonus(main)

        # 6) Летающий джетпак
        if row_m >= 100 and random.random() < JETPACK_SPAWN_CHANCE:
            self._spawn_jetpack(y)

        # 7) Иногда следующий ряд начинает паркур-забег (тоже не в первых рядах и не впритык
        #    к другой ломающейся — вне забегов правило «не подряд» остаётся в силе)
        next_row = self.row_index + 1
        if (not parkour_row
                and next_row >= SAFE_ROWS
                and (next_row - self.last_breakable_row) >= 2
                and random.random() < lerp(PARKOUR_RUN_CHANCE[0], PARKOUR_RUN_CHANCE[1], d)):
            self.parkour_left = random.randint(*PARKOUR_RUN_ROWS)
            self.parkour_lane_x = None

        self.last_main = main
        self.last_main_y = float(y)
        self.row_index += 1

    def cleanup(self):
        """Удалить всё, что ушло ниже экрана или больше не живо."""
        g = self.game
        cam_y = float(getattr(g, "cam_y", 0.0) or 0.0)
        limit = cam_y + SCREEN_H + 120
        for name in ("platforms", "monsters", "bonuses", "jetpacks", "projectiles"):
            lst = getattr(g, name, None)
            if isinstance(lst, list):
                self._prune(lst, limit)

    # ─────────────────────────── спавн объектов ───────────────────────────
    def _spawn_main(self, y, d, hm, occupied=None, allow_moving=True):
        """Основная платформа ряда: normal / moving / spring / rocket по весам.
        occupied — уже стоящие в ряду платформы (x выбирается в стороне от них);
        allow_moving=False — без движущейся (ряд паркур-забега)."""
        weights = {"normal": 1.0, "moving": lerp(0.10, 0.45, d), "spring": 0.08}
        if not allow_moving:
            del weights["moving"]
        if hm >= 200:
            weights["rocket"] = 0.02
        kind = weighted_choice(weights)
        w = PLATFORM_W
        if kind == "normal":
            # на малой сложности платформы чуть шире — легче старт
            w = PLATFORM_W + int(random.uniform(0, 26) * (1.0 - d))
        x = self._free_x(w, occupied) if occupied else None
        if x is None:
            x = random.randint(self.SIDE_MARGIN, max(self.SIDE_MARGIN, SCREEN_W - w - self.SIDE_MARGIN))
        if kind == "moving":
            plat = MovingPlatform(x, y)
        elif kind == "spring":
            plat = SpringPlatform(x, y)
        elif kind == "rocket":
            plat = RocketPlatform(x, y)
        else:
            plat = NormalPlatform(x, y, w)
        self.game.platforms.append(plat)
        return plat

    def _spawn_breakable(self, y, occupied):
        """Ломающаяся (60%) или хрупкая (40%) платформа рядом с основной, y +- 18."""
        x = self._free_x(PLATFORM_W, occupied)
        if x is None:
            return None
        yy = int(round(y + random.uniform(-18, 18)))
        if random.random() < 0.60:
            plat = BreakingPlatform(x, yy)
        else:
            plat = CrumblingPlatform(x, yy)
        self.game.platforms.append(plat)
        return plat

    def _spawn_parkour_breakable(self, y):
        """Ступенька паркур-забега (ломающаяся 60% / хрупкая 40%): первая — над основной
        платформой прошлого ряда, каждая следующая — над предыдущей ступенькой (сдвиг по x
        не больше PARKOUR_LANE_DX) и чуть выше основной платформы своего ряда."""
        w = PLATFORM_W
        lo = self.SIDE_MARGIN
        hi = SCREEN_W - self.SIDE_MARGIN - w
        if self.parkour_lane_x is not None:
            base = self.parkour_lane_x
        elif self.last_main is not None:
            base = self._plat_x(self.last_main) + self._plat_w(self.last_main) / 2.0 - w / 2.0
        else:
            base = (SCREEN_W - w) / 2.0
        x = int(round(clamp(base + random.uniform(-PARKOUR_LANE_DX, PARKOUR_LANE_DX), lo, hi)))
        yy = int(round(y - random.uniform(*PARKOUR_LANE_LIFT)))
        if random.random() < 0.60:
            plat = BreakingPlatform(x, yy)
        else:
            plat = CrumblingPlatform(x, yy)
        self.game.platforms.append(plat)
        self.parkour_lane_x = float(x)
        return plat

    def _spawn_second_normal(self, y, occupied):
        """Вторая обычная платформа в ряду (низкая сложность)."""
        x = self._free_x(PLATFORM_W, occupied)
        if x is None:
            return None
        yy = int(round(y + random.uniform(-14, 14)))
        plat = NormalPlatform(x, yy, PLATFORM_W)
        self.game.platforms.append(plat)
        return plat

    def _spawn_monster(self, y, d, hm, main, breakable):
        """Монстр по высоте. Возвращает платформу, на которой он стоит (или None для летающих)."""
        g = self.game
        # НЛО — редкий, от 1000 м, летает в воздухе
        if hm >= 1000 and random.random() < 0.04:
            ufo = UFO(random.randint(70, SCREEN_W - 70), y - random.randint(35, 70))
            g.monsters.append(ufo)
            return None
        weights = {"ushastik": 1.0, "ghost": 0.8}
        if hm >= 500:
            weights["octopus"] = 0.7
        if hm >= 800:
            weights["bat"] = lerp(0.4, 0.8, d)
        kind = weighted_choice(weights)
        if kind in ("ushastik", "octopus"):
            plat = main
            # 30% — на ломающуюся, чтобы работало «монстрик ломается вместе с платформой»
            if breakable is not None and random.random() < 0.30:
                plat = breakable
            cx = self._plat_x(plat) + self._plat_w(plat) / 2
            top = self._plat_top(plat)
            cls = Ushastik if kind == "ushastik" else Octopus
            m = cls(cx, top - 24, plat)
            self._place_on_platform(m, plat)
            g.monsters.append(m)
            return plat
        x = random.randint(50, SCREEN_W - 50)
        yy = y - random.randint(25, 55)      # в воздухе между рядами
        if kind == "ghost":
            m = Ghost(x, yy)
        else:
            m = Bat(x, yy)
        g.monsters.append(m)
        return None

    def _spawn_chirik(self, plat):
        """Пасхалка Чирик — дружелюбный цыплёнок на платформе (даёт щит)."""
        cx = self._plat_x(plat) + self._plat_w(plat) / 2
        top = self._plat_top(plat)
        chick = Chirik(cx, top - 20, plat)
        self._place_on_platform(chick, plat)
        self.game.monsters.append(chick)

    def _spawn_bonus(self, plat):
        """Бонус над основной платформой: монетки (иногда дугой из трёх), щит, вертолёт, магнит, звезда, промо."""
        g = self.game
        kind = weighted_choice({"coin": 45, "shield": 15, "heli": 12, "magnet": 12, "star": 8, "promo": 8})
        cx = self._plat_x(plat) + self._plat_w(plat) / 2
        by = self._plat_top(plat) - 22
        new = []
        if kind == "coin":
            if random.random() < 0.40:
                # дуга из трёх монеток
                for dx, dy in ((-30, -8), (0, -22), (30, -8)):
                    x = clamp(cx + dx, 16, SCREEN_W - 16)
                    new.append(CoinBonus(x, by + dy))
            else:
                new.append(CoinBonus(cx, by))
        else:
            table = {"shield": ShieldBonus, "heli": HelicopterBonus, "magnet": MagnetBonus,
                     "star": StarBonus, "promo": PromoBonus}
            new.append(table[kind](cx, by))
        for b in new:
            # бонус едет вместе с (движущейся) платформой, а не висит в воздухе
            attach = getattr(b, "attach_to", None)
            if attach is not None:
                attach(plat)
            g.bonuses.append(b)

    def _spawn_jetpack(self, y):
        """Летающий джетпак над рядом; турбо — с долей TURBO_JETPACK_SHARE."""
        x = random.randint(40, SCREEN_W - 40)
        turbo = random.random() < TURBO_JETPACK_SHARE
        self.game.jetpacks.append(JetpackPickup(x, y - 40, turbo))

    # ─────────────────────────── уборка ───────────────────────────
    @staticmethod
    def _obj_y(o):
        """Мировая y объекта (y или rect.top)."""
        y = getattr(o, "y", None)
        if y is None:
            rect = getattr(o, "rect", None)
            y = rect.top if rect is not None else 0
        try:
            return float(y)
        except (TypeError, ValueError):
            return 0.0

    def _prune(self, lst, limit):
        """Оставить в списке только живые объекты выше нижней границы (список — тот же объект)."""
        lst[:] = [o for o in lst if getattr(o, "alive", True) and self._obj_y(o) <= limit]


# ═══════════════════════════════════════════════════════════════════════════
# ═══ ЧАСТЬ 7: ИГРА И ТОЧКА ВХОДА ═══
# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
#  ЧАСТЬ 7: ИГРА (Game) — состояние, цикл, коллизии, HUD — и точка входа main()
# ═══════════════════════════════════════════════════════════════════════════
#  Game — «дирижёр»: владеет всеми списками объектов мира, камерой, счётом,
#  комбо, тряской экрана и машиной состояний экранов. Остальные модули
#  дёргают его публичное API (shake / say / add_caps / on_monster_killed ...).
#  Логика (update_*) строго отделена от отрисовки (draw_*).
# ═══════════════════════════════════════════════════════════════════════════


class CapsPopup:
    """Всплывающая надпись «+N» с нарисованной иконкой мусорной крышки.

    Хлопком появляется, всплывает вверх и тает. Может жить как в мировых
    координатах (над платформой), так и в экранных (world=False).
    """

    def __init__(self, n, x, y, world=True):
        self.n = int(n)
        self.x = float(x)
        self.y = float(y)
        self.world = world
        self.vy = -75.0
        self.max_life = 1.15
        self.life = self.max_life
        self.alive = True

    def update(self, dt, game):
        # Всплываем и постепенно замедляемся
        self.life -= dt
        self.y += self.vy * dt
        self.vy += 45.0 * dt
        if self.life <= 0:
            self.alive = False

    def draw(self, surf, cam_y):
        if not self.alive:
            return
        t = max(0.0, min(1.0, self.life / self.max_life))
        sy = self.y - (cam_y if self.world else 0.0)
        if sy < -40 or sy > SCREEN_H + 40:
            return
        # «хлопок» в первые 20% жизни и плавное растворение в конце
        pop = 1.0 + 0.4 * max(0.0, (t - 0.8) / 0.2)
        alpha = int(255 * min(1.0, t * 2.5))
        tmp = pygame.Surface((120, 36), pygame.SRCALPHA)
        r = max(4, int(8 * pop))
        draw_cap_icon(tmp, 18, 18, r)
        draw_text(tmp, f"+{self.n}", 32, 18, size=max(10, int(20 * pop)), color=WHITE,
                  anchor="midleft", bold=True, outline=BLACK)
        tmp.set_alpha(alpha)
        surf.blit(tmp, (int(self.x) - 18, int(sy) - 18))


class Game:
    """Главный класс игры: окно, мир, состояние, цикл, коллизии и HUD."""

    # ───────────────────────────────────────────────────────────────────────
    #  Инициализация
    # ───────────────────────────────────────────────────────────────────────
    def __init__(self):
        # Микшер настраиваем ДО pygame.init(): моно, 22050 Гц, маленький буфер (меньше задержка)
        try:
            pygame.mixer.pre_init(22050, -16, 1, 512)
        except Exception as exc:       # микшер не обязателен — игра работает и без звука
            print("[Game] mixer.pre_init:", exc)
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        # Мир рисуется на canvas, потом blit на screen со сдвигом тряски
        self.canvas = pygame.Surface((SCREEN_W, SCREEN_H))

        # Сохранения и звук
        self.save = SaveManager()
        self.save.load()
        self.save.touch_launch()
        # дата запуска — сразу на диск (без fsync): если игру убьют в первые секунды,
        # «Последний запуск» всё равно запомнится; в режиме read_only save() ничего не пишет
        self.save.save()
        sound_on = True
        try:
            sound_on = bool(self.save.settings.get("sound", True))
        except Exception:
            pass
        self.sound = SoundManager(sound_on)

        # Общие системы
        self.particles = ParticleSystem()
        self.debris = DebrisPool()
        self.texts = []          # FloatingText (мировые и экранные, флаг .world)
        self.effects = []        # эффекты: update(dt, game) / draw(surf, cam_y) / alive

        # Списки объектов мира (заполняет LevelGenerator)
        self.platforms = []
        self.monsters = []
        self.bonuses = []
        self.projectiles = []
        self.jetpacks = []
        self.player = None

        # Камера / счёт / состояние забега
        self.cam_y = 0.0
        self.height_px = 0.0
        self.bonus_points = 0
        self.combo = 0
        self.combo_timer = 0.0
        self.play_time = 0.0
        self.time_scale = 1.0
        self.run_stats = self._new_run_stats()
        self.last_record_rank = 0
        self.record_beaten = False
        self.parkour_streak = 0
        self.parkour_last = None       # последняя ломающаяся в серии (повторное касание не считается)
        self.phrases_shown = set()
        self.death_cause = ""
        self.run_active = False    # идёт забег, итог которого ещё не записан (см. _commit_run)

        # Таймеры эффектов
        self.shake_intensity = 0.0
        self.shake_timer = 0.0
        self.shake_duration = 0.0
        self.shake_offset = (0, 0)
        self.game_over_timer = 0.0
        self.death_spin = 0.0
        self.slowmo_timer = 0.0
        self.slowmo_cooldown = 0.0
        self.record_flash_timer = 0.0
        self.teleport_flash = 0.0
        self.ui_time = 0.0       # аккумулятор времени для анимаций HUD (не зависит от time_scale)
        self._combo_layer = None  # переиспользуемый слой для радужной надписи комбо

        # Ввод / отладка
        self.touch_dir = 0       # -1/0/1 — «виртуальный» ввод (Player может читать)
        self.show_fps = False
        self.fps = 0.0
        self.frame_time_ms = 0.0
        self.running = True

        # Фон, генератор, реклама
        self.background = Background()
        self.level = LevelGenerator(self)
        self.ads = AdManager(self)

        # Мир создаётся сразу (меню рисует маскота, а тесты — обращаются к игроку),
        # но забег начинается только по start_game()
        self.reset_world()

        # Экраны и машина состояний
        self.screens = {
            "splash": SplashScreen(),
            "menu": MenuScreen(),
            "records": RecordsScreen(),
            "cases": CasesScreen(),
            "skins": SkinsScreen(),
            "musor": MusorShopScreen(),
            "pause": PauseOverlay(),
            "gameover": GameOverOverlay(),
        }
        self.state = "splash"
        self.screens["splash"].on_enter(self)

    @staticmethod
    def _new_run_stats():
        """Пустая статистика одного забега."""
        return {"monsters": 0, "platforms_broken": 0, "jetpacks": 0,
                "max_combo": 0, "caps": 0, "parkour": 0}

    # ───────────────────────────────────────────────────────────────────────
    #  Свойства
    # ───────────────────────────────────────────────────────────────────────
    @property
    def score(self):
        """Очки = высота в пикселях + бонусные очки."""
        return int(self.height_px) + int(self.bonus_points)

    @property
    def height_m(self):
        """Высота в метрах."""
        return self.height_px / PIXELS_PER_METER if PIXELS_PER_METER else 0.0

    @property
    def difficulty(self):
        """Сложность 0..1 по высоте."""
        if DIFFICULTY_METERS <= 0:
            return 1.0
        return clamp(self.height_m / DIFFICULTY_METERS, 0.0, 1.0)

    @property
    def active_skin(self):
        """Словарь активного скина (безопасно, с откатом к классике)."""
        try:
            return SKINS_BY_ID.get(self.save.skin_active, SKINS_BY_ID[DEFAULT_SKIN])
        except Exception:
            return SKINS_BY_ID[DEFAULT_SKIN]

    # ───────────────────────────────────────────────────────────────────────
    #  Публичное API для других модулей
    # ───────────────────────────────────────────────────────────────────────
    def shake(self, intensity, duration):
        """Тряска экрана: берём максимум из текущей и новой."""
        self.shake_intensity = max(self.shake_intensity, float(intensity))
        self.shake_timer = max(self.shake_timer, float(duration))
        self.shake_duration = max(self.shake_duration, float(duration), 0.001)

    def add_text(self, text, x, y, color=WHITE, size=26, life=1.2, world=True, vy=-60):
        """Всплывающий текст (мировые координаты по умолчанию)."""
        try:
            self.texts.append(FloatingText(str(text), x, y, color=color, size=size,
                                           life=life, vy=vy, world=world))
        except Exception as exc:
            print("[Game] add_text:", exc)

    def say(self, key_or_text, color=YELLOW, size=34):
        """Крупная фраза по центру экрана (ключ из PHRASES или готовый текст).
        Размер уменьшается, если фраза не влезает в ширину экрана."""
        text = str(PHRASES.get(key_or_text, key_or_text))
        try:
            size = fit_text_size(text, SCREEN_W - 28, int(size), 12, True)
        except Exception:
            size = int(size)
        # Если несколько фраз подряд — раскладываем их лесенкой, чтобы не слипались
        busy = sum(1 for t in self.texts
                   if getattr(t, "alive", False) and getattr(t, "phrase", False))
        base = SCREEN_H * 0.3
        ads = getattr(self, "ads", None)
        if ads is not None and (ads.showing or ads.slide > 0.01):
            # баннер MusorDrop виден — фразы начинаем под ним, а не поверх кнопки ЗАКРЫТЬ
            base = max(base, ads.ingame_rect.bottom + 40)
        if getattr(self, "record_flash_timer", 0.0) > 0:
            # идёт вспышка «НОВЫЙ РЕКОРД!» с кубком — фразы («КРАК!», «ПАРКУР!») под ней
            base = max(base, RECORD_FLASH_Y + RECORD_FLASH_PHRASE_GAP)
        y = base + (busy % 4) * 40
        self.add_text(text, SCREEN_W / 2, y, color=color, size=size, life=1.5,
                      world=False, vy=-30)
        if self.texts:
            self.texts[-1].phrase = True       # метка «крупная фраза» для раскладки лесенкой

    def add_caps(self, n, x=None, y=None, world=True):
        """Начислить крышки (валюту) с визуальным «+N» и иконкой.
        x, y — где показать «+N» (world=False — экранные координаты, например в меню)."""
        n = int(n)
        if n == 0:
            return
        try:
            self.save.add_caps(n)
        except Exception as exc:
            print("[Game] add_caps:", exc)
        if self.state == "play":
            # в итог забега идут только крышки, заработанные в самом забеге
            self.run_stats["caps"] = self.run_stats.get("caps", 0) + n
        if x is not None and y is not None:
            self.effects.append(CapsPopup(n, x, y, world=bool(world)))
        else:
            # Без координат — показываем у счётчика крышек в HUD
            self.effects.append(CapsPopup(n, SCREEN_W - 150, 46, world=False))

    def add_score(self, points, x=None, y=None, text=None):
        """Бонусные очки со всплывающим текстом."""
        points = int(points)
        self.bonus_points += points
        label = text if text is not None else f"+{points}"
        if x is not None and y is not None:
            self.add_text(label, x, y, color=YELLOW, size=24)
        else:
            self.add_text(label, SCREEN_W / 2, SCREEN_H * 0.42, color=YELLOW, size=28,
                          world=False, vy=-40)

    def _run_over(self):
        """Забег уже закончен (анимация game over или экран) — очки/статистику не трогаем."""
        return self.state != "play" or (self.player is not None and self.player.dying)

    def on_monster_killed(self, monster, by_platform=False):
        """Монстр убит: комбо, очки, крышки, статистика."""
        if self._run_over():
            return                                # мир «доживает» после смерти — не считаем
        if self.combo_timer > 0:
            self.combo += 1
        else:
            self.combo = 1
        if by_platform:
            self.combo += 1                       # «монстрик ломается вместе с платформой» — комбо x2
        self.combo_timer = COMBO_WINDOW
        points = KILL_SCORE * max(1, self.combo)
        mx = getattr(monster, "x", SCREEN_W / 2)
        my = getattr(monster, "y", self.cam_y + SCREEN_H / 2)
        self.add_score(points, mx, my - 10)
        self.add_caps(random.randint(1, 3), mx + 30, my + 10)
        self.run_stats["monsters"] += 1
        self.run_stats["max_combo"] = max(self.run_stats["max_combo"], self.combo)
        try:
            self.save.update_stats(monsters_killed=1)
        except Exception as exc:
            print("[Game] update_stats:", exc)
        if self.combo >= 2:
            color = rainbow(self.ui_time) if self.combo >= COMBO_RAINBOW else ORANGE
            self.add_text(f"x{self.combo} КОМБО!", mx, my - 44, color=color, size=30, life=1.3)
            self.sound.play("combo")
        if self.combo >= COMBO_RAINBOW:
            if self.player is not None:
                self.player.combo_trail_time = max(getattr(self.player, "combo_trail_time", 0.0), 3.0)
            if self.combo == COMBO_RAINBOW or self.combo % 5 == 0:
                self.say("combo", rainbow(self.ui_time + 0.3), 40)

    def on_platform_broken(self, platform, cause):
        """Платформа разрушена (любой причиной)."""
        if self._run_over():
            return
        self.run_stats["platforms_broken"] += 1
        try:
            self.save.update_stats(platforms_broken=1)
        except Exception as exc:
            print("[Game] update_stats:", exc)
        if random.random() < 0.25:
            self.say("crack", ORANGE, 30)

    def on_player_landed(self, platform):
        """Приземление игрока: учёт паркур-серии по ломающимся платформам."""
        kind = getattr(platform, "kind", "normal")
        if kind in ("breaking", "crumbling"):
            if platform is self.parkour_last:
                return                    # второй прыжок с той же хрупкой — серия не растёт и не рвётся
            self.parkour_last = platform
            self.parkour_streak += 1
            if self.parkour_streak == PARKOUR_STREAK:
                self.add_score(PARKOUR_BONUS, text=f"ПАРКУР! +{PARKOUR_BONUS}")
                self.say("parkour", CYAN, 38)
                if self.player is not None:
                    self.player.combo_trail_time = max(getattr(self.player, "combo_trail_time", 0.0), 2.5)
                self.run_stats["parkour"] += 1
                self.particles.confetti(SCREEN_W / 2, SCREEN_H * 0.3, 30, screen=True)
            elif self.parkour_streak > PARKOUR_STREAK:
                # Серия продолжается — небольшой бонус за каждую следующую
                self.add_score(10, getattr(platform, "cx", SCREEN_W / 2), getattr(platform, "top", self.cam_y) - 20)
        else:
            self.parkour_streak = 0
            self.parkour_last = None

    def on_jetpack_collected(self, pickup):
        """Подобран джетпак."""
        self.run_stats["jetpacks"] += 1
        try:
            self.save.update_stats(jetpacks_collected=1)
        except Exception as exc:
            print("[Game] update_stats:", exc)

    def teleport_player(self, meters):
        """Телепорт игрока вверх на meters метров (НЛО): вспышка, сдвиг мира, генерация."""
        if self.player is None:
            return
        dy = float(meters) * PIXELS_PER_METER
        self.player.y -= dy
        # Камера — так, чтобы игрок оказался на «линии камеры» (а не у нижнего края,
        # если НЛО поймало его в падении): после вспышки видно, куда приземляться
        self.cam_y = self.player.y - SCREEN_H * CAMERA_LINE
        try:
            self.player.rect.center = (int(self.player.x), int(self.player.y))
        except Exception:
            pass
        self.player.prev_bottom = self.player.y + PLAYER_H / 2
        self.player.vy = JUMP_POWER * 0.5
        self.height_px = max(self.height_px, PLAYER_START_Y - self.player.y)
        # «Посадочная площадка» прямо под игроком — телепорт это награда, а не ловушка
        pad_w = 110
        pad_x = clamp(self.player.x - pad_w / 2, 8, SCREEN_W - pad_w - 8)
        pad_y = int(self.player.y + PLAYER_H / 2 + 120)
        try:
            self.platforms.append(NormalPlatform(pad_x, pad_y, pad_w))
        except Exception as exc:
            print("[Game] teleport pad:", exc)
        # Ряды между старым и новым экраном не нужны (их сразу уберёт cleanup) —
        # продолжаем генерацию прямо над площадкой
        lvl = self.level
        start_row = pad_y - random.uniform(ROW_GAP_MIN, ROW_GAP_MAX_EASY)
        if getattr(lvl, "next_row_y", None) is not None and lvl.next_row_y > start_row:
            lvl.next_row_y = start_row
        # Зона прибытия без врагов: пока экран залит вспышкой, игрок не должен
        # оказаться рядом с только что созданным монстром
        safe_y = pad_y - TELEPORT_SAFE_ZONE
        lvl.monster_free_below_y = float(safe_y)
        try:
            self.level.generate_until(self.cam_y)
        except Exception as exc:
            print("[Game] generate_until:", exc)
        # Страховка: враги, уже оказавшиеся в зоне прибытия, тихо исчезают (экран всё равно белый)
        for mon in self.monsters:
            if (getattr(mon, "alive", False) and not getattr(mon, "friendly", False)
                    and safe_y < float(getattr(mon, "y", safe_y)) < pad_y + 80):
                mon.alive = False
        # Короткая неуязвимость (игрок мигает): вспышка + время осмотреться
        self.player.hurt_timer = max(float(getattr(self.player, "hurt_timer", 0.0) or 0.0),
                                     TELEPORT_FLASH_TIME + TELEPORT_GRACE)
        self.teleport_flash = 1.0
        self.say("ufo", CYAN, 36)
        self.particles.emit(self.player.x, self.player.y, 40, color=[WHITE, CYAN, (200, 255, 255)],
                            speed=(100, 380), life=(0.4, 1.0), size=(2, 5), gravity=0, shape="spark")
        self.shake(5, 0.25)

    def slow_motion(self, duration=SLOWMO_TIME):
        """Слоу-мо скина «67×52»: замедление времени и экран в цифрах.
        Единственный владелец перезарядки (SLOWMO_COOLDOWN в реальном времени).
        Возвращает True, если слоу-мо запущено."""
        if self.slowmo_cooldown > 0 or self.state != "play":
            return False
        self.time_scale = SLOWMO_SCALE
        self.slowmo_timer = float(duration)
        self.slowmo_cooldown = SLOWMO_COOLDOWN + float(duration)
        for _ in range(45):
            text = random.choice(("67", "52"))
            color = (255, 80, 80) if text == "67" else (90, 140, 255)
            self.particles.digits(random.uniform(10, SCREEN_W - 10), random.uniform(10, SCREEN_H - 10),
                                  text, 1, color=color, screen=True)
        self.shake(4, 0.3)
        return True

    def begin_game_over(self, cause):
        """Старт анимации game over: дудлер улетает вверх, монстрики машут лапками."""
        if self.player is None or self.player.dying:
            return
        self.death_cause = str(cause)
        self.player.dying = True
        self.player.vy = GAME_OVER_FLY_SPEED
        self.player.vx = 0.0
        if cause == "fall":
            # Упавшего игрока «выныриваем» снизу экрана, чтобы улёт был виден
            self.player.y = min(self.player.y, self.cam_y + SCREEN_H + 30)
        self.game_over_timer = GAME_OVER_TIME
        self.death_spin = 0.0
        # Слоу-мо и комбо на game over не нужны
        self.time_scale = 1.0
        self.slowmo_timer = 0.0
        self.combo = 0
        self.combo_timer = 0.0
        for m in self.monsters:
            if getattr(m, "alive", False) and -80 < m.y - self.cam_y < SCREEN_H + 80:
                m.waving = True
        # баннер MusorDrop прячем: его невидимая кнопка не должна платить крышки после смерти
        try:
            self.ads.showing = False
            self.ads.close_btn.enabled = False
        except Exception:
            pass
        self.sound.play("death")
        self.shake(*SHAKE_HIT)
        self.particles.emit(self.player.x, self.player.y, 24, color=[WHITE, YELLOW, (255, 240, 200)],
                            speed=(80, 260), life=(0.4, 1.0), size=(2, 4), gravity=300, shape="spark")
        # Итог забега пишем на диск СРАЗУ (счёт уже окончательный): анимация улёта —
        # только картинка, и закрытие окна во время неё ничего не теряет
        self._commit_run()

    def _commit_run(self, abandoned=False):
        """Записать итог забега (рекорд, статистика, диск) РОВНО один раз.

        Вызывается при гибели (begin_game_over — до анимации и экрана Game Over), а также
        когда забег брошен: пауза -> МЕНЮ, закрытие окна, новый старт поверх забега.
        Возвращает место в ТОП-5 (0 — не попал)."""
        if not self.run_active:
            return self.last_record_rank
        self.run_active = False
        score = self.score
        if abandoned and score <= 0 and self.play_time < 1.0:
            # «пустой» забег (сразу вышли) не засоряет ТОП-5 и счётчик игр; подсветка
            # «НОВЫЙ!» в рекордах от прошлого забега тоже уже не про последнюю игру
            self.last_record_rank = 0
            return 0
        rank = 0
        try:
            rank = int(self.save.add_record(score, int(self.height_m),
                                            self.run_stats.get("monsters", 0),
                                            skin=self.save.skin_active))
        except Exception as exc:
            print("[Game] add_record:", exc)
        try:
            self.save.update_stats(games_played=1, total_time=self.play_time,
                                   max_combo=self.run_stats.get("max_combo", 0),
                                   max_height=int(self.height_m))
        except Exception as exc:
            print("[Game] update_stats:", exc)
        try:
            self.save.save(force=True)
        except Exception as exc:
            print("[Game] save:", exc)
        self.last_record_rank = rank
        return rank

    def abandon_run(self):
        """Забег прерван без game over (пауза -> МЕНЮ, закрытие окна): итог всё равно
        сохраняется — рекорд, «игр сыграно», время. Надписи забега в меню не переносим."""
        if not self.run_active:
            return
        self._commit_run(abandoned=True)
        self.texts = []
        self.effects = []
        try:
            self.ads.showing = False
            self.ads.slide = 0.0
        except Exception:
            pass

    def finish_game_over(self):
        """Конец анимации улёта: итог уже сохранён в begin_game_over (здесь — страховка
        без дублей), затем экран game over."""
        self._commit_run()
        self.set_state("gameover")

    def start_game(self):
        """Начать новый забег (незаписанный текущий забег сначала сохраняется)."""
        if self.run_active:
            self.abandon_run()
        self.reset_world()
        self.run_active = True
        self.set_state("play")
        try:
            self.ads.reset_game_timer()
        except Exception as exc:
            print("[Game] ads.reset_game_timer:", exc)
        self.sound.play("click")

    def reset_world(self):
        """Пересобрать мир: новый игрок, пустые списки, стартовые платформы."""
        self.player = Player(self.active_skin)
        self.player.x = SCREEN_W / 2
        self.player.y = float(PLAYER_START_Y)
        self.player.vx = 0.0
        self.player.vy = 0.0
        try:
            self.player.rect.center = (int(self.player.x), int(self.player.y))
        except Exception:
            pass
        self.player.prev_bottom = self.player.y + PLAYER_H / 2
        self.platforms = []
        self.monsters = []
        self.bonuses = []
        self.projectiles = []
        self.jetpacks = []
        self.texts = []
        self.effects = []
        self.cam_y = 0.0
        self.height_px = 0.0
        self.bonus_points = 0
        self.combo = 0
        self.combo_timer = 0.0
        self.play_time = 0.0
        self.time_scale = 1.0
        self.slowmo_timer = 0.0
        self.slowmo_cooldown = 0.0
        self.run_stats = self._new_run_stats()
        self.record_beaten = False
        self.record_flash_timer = 0.0
        self.teleport_flash = 0.0
        self.game_over_timer = 0.0
        self.death_spin = 0.0
        self.death_cause = ""
        self.parkour_streak = 0
        self.parkour_last = None       # последняя ломающаяся в серии (повторное касание не считается)
        self.phrases_shown = set()
        self.shake_timer = 0.0
        self.shake_intensity = 0.0
        self.shake_offset = (0, 0)
        self.particles.clear()
        try:
            self.debris.clear()
        except Exception:
            pass
        try:
            self.level.reset()
        except Exception as exc:
            print("[Game] level.reset:", exc)
        # На старте генерируем платформы с запасом на экран вверх
        try:
            self.level.generate_until(self.cam_y)
        except Exception as exc:
            print("[Game] generate_until:", exc)

    def apply_skin(self):
        """Применить активный скин к игроку."""
        if self.player is not None:
            self.player.skin = self.active_skin

    def set_state(self, name):
        """Сменить состояние; у нового экрана вызывается on_enter."""
        prev = getattr(self, "state", None)
        self.state = name
        if prev == "menu" and name != "menu" and getattr(self, "ads", None) is not None:
            self.ads.menu_fx = []          # «+10» меню не всплывает снова при возврате в меню
        if prev in WORLD_STATES and name not in WORLD_STATES:
            # экранные фразы забега («КРАК!», «+50») не переносим на экраны меню,
            # где теперь рисуются собственные экранные надписи и «+N крышек»
            self.texts = [t for t in self.texts if not self._is_screen_space(t)]
            self.effects = [e for e in self.effects if not self._is_screen_space(e)]
        scr = self.screens.get(name) if hasattr(self, "screens") else None
        if scr is not None:
            try:
                scr.on_enter(self)
            except Exception as exc:
                print(f"[Game] on_enter({name}):", exc)
                traceback.print_exc()

    def quit(self):
        """Завершить игру (цикл остановится после текущего кадра)."""
        self.running = False

    # ───────────────────────────────────────────────────────────────────────
    #  Главный цикл
    # ───────────────────────────────────────────────────────────────────────
    def run(self):
        """Главный цикл: события -> update -> draw."""
        try:
            while self.running:
                dt = min(self.clock.tick(FPS) / 1000.0, MAX_DT)
                for event in pygame.event.get():
                    self.handle_event(event)
                self.update(dt)
                self.draw()
        finally:
            # При выходе посреди забега — сохранить его итог (рекорд и статистику)
            try:
                self.abandon_run()
            except Exception as exc:
                print("[Game] abandon_run:", exc)
            # и дописать несохранённое (крышки, статистика, настройки)
            try:
                if getattr(self.save, "dirty", False):
                    self.save.save(force=True)
            except Exception as exc:
                print("[Game] final save:", exc)

    def handle_event(self, event):
        """Обработка одного события pygame."""
        if event.type == pygame.QUIT:
            # закрытие окна посреди забега (в т.ч. на паузе или во время улёта) — итог сохраняем
            try:
                self.abandon_run()
            except Exception as exc:
                print("[Game] abandon_run:", exc)
            self.quit()
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F3:
                self.show_fps = not self.show_fps
                return
            if event.key == pygame.K_m and self.state in ("menu", "play", "pause"):
                self._toggle_sound()
                return

        state = self.state
        if state == "play":
            # Реклама (баннер в игре) имеет приоритет на клики
            try:
                if self.ads.handle_game_event(event):
                    return
            except Exception as exc:
                print("[Game] ads.handle_game_event:", exc)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.player is not None and not self.player.dying:
                    self.set_state("pause")
                    self.sound.play("click")
            return

        # Меню само передаёт события в AdManager (MenuScreen.handle_event) — здесь не дублируем
        scr = self.screens.get(state)
        if scr is not None:
            try:
                scr.handle_event(event, self)
            except Exception as exc:
                print(f"[Game] handle_event({state}):", exc)
                traceback.print_exc()

    def _toggle_sound(self):
        """Переключить звук и запомнить настройку в сохранении."""
        enabled = self.sound.toggle()
        try:
            self.save.settings["sound"] = bool(enabled)
            self.save.mark_dirty()
        except Exception as exc:
            print("[Game] settings:", exc)
        label = "ЗВУК: ВКЛ" if enabled else "ЗВУК: ВЫКЛ"
        if self.state in WORLD_STATES:
            self.add_text(label, SCREEN_W / 2, SCREEN_H * 0.5,
                          color=LIGHT_GRAY, size=24, life=0.9, world=False, vy=-20)
        else:
            # в меню — над подсказкой «M - звук», чтобы не закрывать кнопки
            self.add_text(label, SCREEN_W / 2, SCREEN_H - 92,
                          color=YELLOW, size=20, life=1.1, world=False, vy=-8)

    def update(self, dt):
        """Обновление по состоянию. dt — реальное время кадра."""
        self.ui_time += dt
        self.fps = self.clock.get_fps()
        self.frame_time_ms = self.clock.get_rawtime()
        try:
            self.save.tick(dt)
        except Exception as exc:
            print("[Game] save.tick:", exc)

        state = self.state
        if state == "play":
            self.update_play(dt * self.time_scale, dt)
            return

        # Тряска затухает в любом состоянии
        self._update_shake(dt)

        if state == "gameover":
            # Мир продолжает жить «фоном»: монстрики машут, частицы догорают
            self._update_world_ambient(dt)
        else:
            # Меню, пауза и прочие экраны: мир стоит, но экранные надписи и «+N крышек»
            # (звук ВКЛ/ВЫКЛ по M, награда за мем-попап) живут и исчезают
            self._update_screen_space(dt)
        scr = self.screens.get(state)
        if scr is not None:
            try:
                scr.update(dt, self)
            except Exception as exc:
                print(f"[Game] update({state}):", exc)
                traceback.print_exc()
        # Баннеры/попапы меню обновляет сам MenuScreen.update (ads.update_menu) — не дублируем

    def _update_world_ambient(self, dt):
        """Лёгкое обновление мира без игрока (экран game over)."""
        try:
            self.background.update(dt, self)
        except Exception as exc:
            print("[Game] background.update:", exc)
        self._update_list(self.monsters, dt)
        self._update_list(self.platforms, dt)
        # бонусы, джетпаки и чернильные капли тоже «доживают» — иначе они замирают в воздухе
        self._update_list(self.bonuses, dt)
        self._update_list(self.jetpacks, dt)
        self._update_list(self.projectiles, dt)
        self.projectiles = [p for p in self.projectiles if getattr(p, "alive", False)]
        self.debris.update(dt)
        self.particles.update(dt)
        self._update_effects_and_texts(dt)

    def _update_list(self, items, dt):
        """Обновить список объектов с update(dt, game), не падая на ошибке одного объекта."""
        for obj in items:
            if getattr(obj, "alive", True):
                try:
                    obj.update(dt, self)
                except Exception as exc:
                    print(f"[Game] update {type(obj).__name__}:", exc)
                    traceback.print_exc()
                    obj.alive = False

    @staticmethod
    def _is_screen_space(obj):
        """Объект живёт в экранных координатах (надпись/эффект интерфейса, а не мира)."""
        return not getattr(obj, "world", True) or bool(getattr(obj, "screen", False))

    def _update_screen_space(self, dt):
        """Только экранные надписи и эффекты (мир при этом стоит) + удаление отживших."""
        for e in self.effects:
            if getattr(e, "alive", False) and self._is_screen_space(e):
                try:
                    e.update(dt, self)
                except Exception as exc:
                    print("[Game] effect", type(e).__name__, exc)
                    e.alive = False
        self.effects = [e for e in self.effects if getattr(e, "alive", False)]
        for t in self.texts:
            if getattr(t, "alive", False) and self._is_screen_space(t):
                try:
                    t.update(dt)
                except Exception as exc:
                    print("[Game] text:", exc)
                    t.alive = False
        self.texts = [t for t in self.texts if getattr(t, "alive", False)]

    def _draw_screen_space(self, surf):
        """Экранные эффекты и надписи поверх экранов меню (world=False)."""
        for e in self.effects:
            if getattr(e, "alive", False) and self._is_screen_space(e):
                self._safe_draw(e, surf, 0)
        for t in self.texts:
            if getattr(t, "alive", False) and self._is_screen_space(t):
                self._safe_draw(t, surf, 0)

    def _update_effects_and_texts(self, dt, ui_dt=None):
        """Эффекты и всплывающие тексты + удаление мёртвых.

        dt — мировое время (с учётом time_scale); ui_dt — реальное время для
        экранных надписей и эффектов: слоу-мо замедляет только мир, а не интерфейс."""
        if ui_dt is None:
            ui_dt = dt
        for e in self.effects:
            try:
                e.update(ui_dt if self._is_screen_space(e) else dt, self)
            except Exception as exc:
                print(f"[Game] effect {type(e).__name__}:", exc)
                e.alive = False
        self.effects = [e for e in self.effects if getattr(e, "alive", False)]
        for t in self.texts:
            try:
                t.update(ui_dt if self._is_screen_space(t) else dt)
            except Exception as exc:
                print("[Game] text:", exc)
                t.alive = False
        self.texts = [t for t in self.texts if getattr(t, "alive", False)]

    def _update_shake(self, dt):
        """Таймер тряски и случайное смещение кадра."""
        if self.shake_timer > 0:
            self.shake_timer -= dt
            if self.shake_timer <= 0:
                self.shake_timer = 0.0
                self.shake_intensity = 0.0
                self.shake_duration = 0.0
                self.shake_offset = (0, 0)
            else:
                k = self.shake_timer / self.shake_duration if self.shake_duration > 0 else 1.0
                amp = self.shake_intensity * clamp(k, 0.0, 1.0)
                self.shake_offset = (int(random.uniform(-amp, amp)), int(random.uniform(-amp, amp)))
        else:
            self.shake_offset = (0, 0)

    # ───────────────────────────────────────────────────────────────────────
    #  Обновление игрового процесса
    # ───────────────────────────────────────────────────────────────────────
    def update_play(self, dt, raw_dt):
        """Один шаг игры. dt — с учётом time_scale, raw_dt — реальное время."""
        self.play_time += raw_dt
        player = self.player
        if player is None:
            return

        # Таймеры, не зависящие от замедления
        self._update_shake(raw_dt)
        if self.slowmo_timer > 0:
            self.slowmo_timer -= raw_dt
            if self.slowmo_timer <= 0:
                self.slowmo_timer = 0.0
                self.time_scale = 1.0
        if self.slowmo_cooldown > 0:
            self.slowmo_cooldown = max(0.0, self.slowmo_cooldown - raw_dt)
        if self.record_flash_timer > 0:
            self.record_flash_timer = max(0.0, self.record_flash_timer - raw_dt)
        if self.teleport_flash > 0:
            self.teleport_flash = max(0.0, self.teleport_flash - raw_dt / TELEPORT_FLASH_TIME)

        # Фон
        try:
            self.background.update(dt, self)
        except Exception as exc:
            print("[Game] background.update:", exc)

        if player.dying:
            self._update_game_over(dt)
            return

        # --- Игрок и камера ---
        try:
            player.update(dt, self)
        except Exception as exc:
            print("[Game] player.update:", exc)
            traceback.print_exc()
        self._update_camera(dt)
        self.height_px = max(self.height_px, PLAYER_START_Y - player.y)

        # --- Генерация и объекты ---
        try:
            self.level.generate_until(self.cam_y)
        except Exception as exc:
            print("[Game] generate_until:", exc)
        self._update_list(self.platforms, dt)
        self._update_list(self.monsters, dt)
        self._update_list(self.bonuses, dt)
        self._update_list(self.jetpacks, dt)
        self._update_list(self.projectiles, dt)
        self._update_effects_and_texts(dt, raw_dt)
        self.debris.update(dt)
        self.particles.update(dt)

        # --- Коллизии и очистка ---
        self.handle_collisions()
        try:
            self.level.cleanup()
        except Exception as exc:
            print("[Game] cleanup:", exc)
        self.projectiles = [p for p in self.projectiles if getattr(p, "alive", False)]

        # --- Комбо ---
        if self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo_timer = 0.0
                self.combo = 0

        # --- Фразы по высоте (каждая один раз) ---
        h = self.height_m
        for meters, phrase in HEIGHT_PHRASES:
            if h >= meters and meters not in self.phrases_shown:
                self.phrases_shown.add(meters)
                self.say(phrase, YELLOW if meters < 2000 else CYAN, 36)
                break

        # --- Новый рекорд №1 ---
        if not self.record_beaten and not player.dying:
            best = 0
            try:
                best = int(self.save.best_score)
            except Exception:
                pass
            if best > 0 and self.score > best:
                self._trigger_new_record()

        # --- Смерть от падения ---
        if not player.dying and player.y - self.cam_y > SCREEN_H + DEATH_MARGIN:
            self.begin_game_over("fall")

        # --- Реклама в игре ---
        if not player.dying:
            try:
                self.ads.update_game(raw_dt)
            except Exception as exc:
                print("[Game] ads.update_game:", exc)

    def _update_camera(self, dt):
        """Камера едет только вверх, плавно, но игрок никогда не уходит за верх экрана."""
        player = self.player
        target = player.y - SCREEN_H * CAMERA_LINE
        if target < self.cam_y:
            k = clamp(CAMERA_LERP_K * dt, 0.0, 1.0)
            self.cam_y += (target - self.cam_y) * k
        # Жёсткая граница: если игрок слишком быстро взлетел (ракета) — догоняем сразу
        hard = player.y - CAMERA_HARD_MARGIN
        if hard < self.cam_y:
            self.cam_y = hard

    def _update_game_over(self, dt):
        """Анимация game over: дудлер улетает вверх и крутится, мир доживает."""
        player = self.player
        player.y += player.vy * dt
        player.time = getattr(player, "time", 0.0) + dt
        self.death_spin += GAME_OVER_SPIN_SPEED * dt
        try:
            player.rect.center = (int(player.x), int(player.y))
        except Exception:
            pass
        # Дымок/звёздочки за улетающим дудлером
        if random.random() < 0.5:
            self.particles.emit(player.x + random.uniform(-10, 10), player.y + 20, 1,
                                color=[YELLOW, WHITE], speed=(20, 60), life=(0.3, 0.7),
                                size=(2, 4), gravity=0)
        self._update_list(self.platforms, dt)
        self._update_list(self.monsters, dt)
        self._update_list(self.bonuses, dt)
        self._update_list(self.jetpacks, dt)
        self._update_list(self.projectiles, dt)
        self._update_effects_and_texts(dt)
        self.debris.update(dt)
        self.particles.update(dt)
        self.projectiles = [p for p in self.projectiles if getattr(p, "alive", False)]
        self.game_over_timer -= dt
        if self.game_over_timer <= 0:
            self.game_over_timer = 0.0
            self.finish_game_over()

    def _trigger_new_record(self):
        """Вспышка «НОВЫЙ РЕКОРД!» — один раз за забег."""
        self.record_beaten = True
        # надпись рисует только HUD-вспышка (_draw_record_flash): say("record") давал
        # вторую такую же строку выше неё
        self.sound.play("record")
        self.particles.confetti(SCREEN_W / 2, SCREEN_H * 0.25, 60, screen=True)
        for _ in range(3):
            self.particles.emit(random.uniform(60, SCREEN_W - 60), random.uniform(80, SCREEN_H * 0.5), 14,
                                color=[GOLD, YELLOW, WHITE], speed=(120, 320), life=(0.5, 1.1),
                                size=(2, 4), gravity=350, shape="spark", screen=True)
        if self.player is not None:
            self.particles.sparks(self.player.x, self.player.y, 24, GOLD)
        self.add_caps(RECORD_CAPS)
        self.record_flash_timer = RECORD_FLASH_TIME
        # фразы, уже висящие в зоне кубка и надписи (например, фраза высоты в этом же кадре),
        # переезжают под вспышку, чтобы тексты не накладывались друг на друга
        below = RECORD_FLASH_Y + RECORD_FLASH_PHRASE_GAP
        moved = 0
        for txt in self.texts:
            if (getattr(txt, "alive", False) and getattr(txt, "phrase", False)
                    and txt.y >= RECORD_FLASH_Y - 120):
                txt.y = max(txt.y, below + moved * 40)
                moved += 1
        self.shake(4, 0.3)

    # ───────────────────────────────────────────────────────────────────────
    #  Коллизии
    # ───────────────────────────────────────────────────────────────────────
    def handle_collisions(self):
        """Все столкновения игрока: платформы, монстры, бонусы, джетпаки, снаряды."""
        player = self.player
        if player is None or player.dying:
            return
        prect = player.rect
        # Игрок, «перетекающий» через край экрана, нарисован двумя копиями —
        # сталкиваются обе (иначе он проваливался бы сквозь платформу у другого края)
        prects = player.wrap_rects(prect)

        def touches(rect):
            return any(pr.colliderect(rect) for pr in prects)

        # Падал ли игрок В НАЧАЛЕ кадра: приземление на платформу ниже переворачивает vy,
        # а при низком FPS (dt = MAX_DT) ноги за один кадр проходят и голову монстра,
        # и верх его платформы — такой кадр всё равно должен считаться прыжком на монстра
        was_falling = player.vy > 0
        landed_vy = None

        # --- Платформы: приземление только при падении и не в полёте ---
        # «Протяжённая» проверка: на прошлом кадре ноги были выше верха платформы
        # (prev_bottom <= top + 10), а сейчас опустились ниже него — так игрок не
        # проскочит платформу даже при просадке FPS (dt до MAX_DT) и большой скорости.
        if player.vy > 0 and not player.flying:
            feet = player.feet_rect
            feet_copies = player.wrap_rects(feet)
            # Протяжённая проверка допустима только в пределах перемещения за кадр
            # (макс. ~53 px при MAX_DT); при «скачке» позиции — обычное перекрытие
            swept = (feet.bottom - player.prev_bottom) <= 90
            landed_on = None
            for plat in self.platforms:
                if not plat.alive or not plat.can_land:
                    continue
                r = plat.rect
                if not any(f.right > r.left and f.left < r.right for f in feet_copies):
                    continue
                if player.prev_bottom <= r.top + 10 and feet.bottom > r.top \
                        and (swept or any(f.colliderect(r) for f in feet_copies)):
                    # если пересекли сразу несколько — берём самую верхнюю (первую по пути)
                    if landed_on is None or r.top < landed_on.rect.top:
                        landed_on = plat
            if landed_on is not None:
                plat = landed_on
                player.y = plat.rect.top - PLAYER_H / 2 + 6
                try:
                    plat.on_land(player, self)
                except Exception as exc:
                    print(f"[Game] on_land {type(plat).__name__}:", exc)
                    traceback.print_exc()
                landed_vy = player.vy
                self.on_player_landed(plat)

        # --- Турбо-джетпак пробивает ломающиеся платформы ---
        jp = player.jetpack
        if jp is not None and getattr(jp, "turbo", False):
            for plat in self.platforms:
                if plat.alive and getattr(plat, "kind", "") in ("breaking", "crumbling") \
                        and touches(plat.rect):
                    try:
                        plat.break_apart(self, "jetpack")
                    except Exception as exc:
                        print("[Game] break_apart:", exc)
                    self.particles.sparks(plat.cx, plat.top, 16, GOLD)
                    self.particles.emit(plat.cx, plat.top, 10, color=[WHITE, GOLD], speed=(80, 260),
                                        life=(0.3, 0.7), size=(2, 4), gravity=500)

        # --- Монстры ---
        hard_invincible = (getattr(player, "star_time", 0.0) > 0 or player.jetpack is not None
                           or getattr(player, "rocket_time", 0.0) > 0)
        # Копия списка: телепорт НЛО прямо в этом цикле генерирует новые ряды
        # (и монстров) — их нельзя проверять в том же кадре со старыми флагами
        for m in list(self.monsters):
            if not m.alive or m.dying:
                continue
            if not touches(m.rect):
                continue
            m_plat = getattr(m, "platform", None)
            try:
                if getattr(m, "friendly", False) or getattr(m, "kind", "") == "ufo":
                    m.on_touch(player, self)
                elif m_plat is not None and not getattr(m_plat, "alive", True):
                    # платформа под монстриком сломалась в этом же кадре (турбо-джетпак пробил,
                    # игрок оттолкнулся от ломающейся) — он ломается вместе с ней (комбо x2),
                    # а не ждёт следующего кадра, где игрок успел бы убить его «обычно» или получить удар
                    m.die(self, by_platform=True)
                elif hard_invincible:
                    m.die(self)
                elif was_falling and player.prev_bottom <= m.rect.top + 14 and getattr(m, "killable", True):
                    m.on_stomp(self)
                    player.bounce_on_monster(self)
                    if landed_vy is not None:
                        # в этом же кадре сработала платформа (пружина и т.п.) — берём более сильный прыжок
                        player.vy = min(player.vy, landed_vy)
                else:
                    m.on_touch(player, self)
            except Exception as exc:
                print(f"[Game] monster collision {type(m).__name__}:", exc)
                traceback.print_exc()
            if player.dying:
                return

        # --- Бонусы ---
        for b in self.bonuses:
            if b.alive and touches(b.rect):
                try:
                    b.on_pickup(player, self)
                except Exception as exc:
                    print(f"[Game] bonus {type(b).__name__}:", exc)
                    b.alive = False

        # --- Джетпаки ---
        for j in self.jetpacks:
            if j.alive and touches(j.rect):
                try:
                    j.on_pickup(player, self)
                except Exception as exc:
                    print("[Game] jetpack pickup:", exc)
                    j.alive = False
                self.on_jetpack_collected(j)

        # --- Снаряды (чернильные капли) ---
        for p in self.projectiles:
            if p.alive and touches(p.rect):
                p.alive = False
                try:
                    player.take_hit(self, p)
                except Exception as exc:
                    print("[Game] take_hit:", exc)
                self.particles.ink(p.x, p.y, 8)
                if player.dying:
                    return

    # ───────────────────────────────────────────────────────────────────────
    #  Отрисовка
    # ───────────────────────────────────────────────────────────────────────
    def draw(self):
        """Собрать кадр на canvas и вывести на экран со сдвигом тряски."""
        canvas = self.canvas
        canvas.fill(UI_BG)
        state = self.state
        if state in ("play", "pause", "gameover"):
            self.draw_world(canvas)
            self.draw_hud(canvas)
            if state in ("pause", "gameover"):
                scr = self.screens.get(state)
                if scr is not None:
                    self._safe_screen_draw(scr, canvas, state)
        else:
            scr = self.screens.get(state)
            if scr is not None:
                self._safe_screen_draw(scr, canvas, state)
            # Рекламу меню рисует сам MenuScreen.draw (ads.draw_menu).
            # Поверх — экранные «+N крышек» и надписи (например, «ЗВУК: ВЫКЛ»)
            self._draw_screen_space(canvas)

        ox, oy = self.shake_offset
        if ox or oy:
            self.screen.fill(BLACK)
        self.screen.blit(canvas, (ox, oy))
        if self.show_fps:
            self._draw_debug(self.screen)
        pygame.display.flip()

    def _safe_screen_draw(self, scr, surf, state):
        """Отрисовка экрана с защитой от исключений (одна ошибка не роняет игру)."""
        try:
            scr.draw(surf, self)
        except Exception as exc:
            print(f"[Game] draw({state}):", exc)
            traceback.print_exc()

    def _draw_debug(self, surf):
        """Отладочная строка F3: FPS, время кадра, количество объектов."""
        info = (f"FPS {self.fps:5.1f}  {self.frame_time_ms:.0f} мс  "
                f"плт {len(self.platforms)}  мон {len(self.monsters)}  "
                f"част {len(self.particles)}  оск {self.debris.active_count()}  "
                f"cam {int(self.cam_y)}  ts {self.time_scale:.2f}")
        draw_text(surf, info, 6, SCREEN_H - 20, size=14, color=WHITE, anchor="topleft", outline=BLACK)

    def draw_world(self, surf):
        """Мир: фон, платформы, осколки, бонусы, джетпаки, монстры, снаряды, игрок, эффекты, частицы, тексты."""
        cam_y = self.cam_y
        try:
            self.background.draw(surf, self)
        except Exception as exc:
            print("[Game] background.draw:", exc)
            surf.fill(SKY_DAY)

        lo, hi = -120, SCREEN_H + 120
        for p in self.platforms:
            if p.alive and lo < p.y - cam_y < hi:
                self._safe_draw(p, surf, cam_y)
        self.debris.draw(surf, cam_y)
        for b in self.bonuses:
            if b.alive and lo < b.y - cam_y < hi:
                self._safe_draw(b, surf, cam_y)
        for j in self.jetpacks:
            if j.alive and lo < j.y - cam_y < hi:
                self._safe_draw(j, surf, cam_y)
        for m in self.monsters:
            if m.alive and lo < m.y - cam_y < hi:
                self._safe_draw(m, surf, cam_y)
        for pr in self.projectiles:
            if pr.alive and lo < pr.y - cam_y < hi:
                self._safe_draw(pr, surf, cam_y)

        player = self.player
        if player is not None:
            if player.dying:
                self._draw_dying_player(surf, cam_y)
            else:
                self._safe_draw(player, surf, cam_y)

        for e in self.effects:
            self._safe_draw(e, surf, cam_y)
        self.particles.draw(surf, cam_y)
        for t in self.texts:
            if getattr(t, "world", True):
                self._safe_draw(t, surf, cam_y)

    def _safe_draw(self, obj, surf, cam_y):
        """draw(surf, cam_y) с защитой от исключений."""
        try:
            obj.draw(surf, cam_y)
        except Exception as exc:
            print(f"[Game] draw {type(obj).__name__}:", exc)
            traceback.print_exc()
            obj.alive = False

    def _draw_dying_player(self, surf, cam_y):
        """Улетающий вверх дудлер: вращается, над головой звёздочки."""
        player = self.player
        sy = player.y - cam_y
        if sy < -120 or sy > SCREEN_H + 120:
            return
        try:
            # у края экрана — и копия у противоположного края, как при обычной отрисовке
            for sx in player.draw_xs():
                draw_doodler(surf, sx, sy, player.skin, getattr(player, "time", self.ui_time),
                             facing=getattr(player, "facing", 1), squash=1.0, tilt=self.death_spin,
                             scale=1.0, alpha=255, jetpack=None, heli=False, shield=False,
                             star=False, look=None, dizzy=True)
        except Exception as exc:
            print("[Game] draw_doodler:", exc)

    # ───────────────────────────────────────────────────────────────────────
    #  HUD
    # ───────────────────────────────────────────────────────────────────────
    def draw_hud(self, surf):
        """Интерфейс поверх мира."""
        t = self.ui_time
        self._draw_score_panel(surf)
        self._draw_caps_panel(surf, t)
        self._draw_bonus_icons(surf, t)
        self._draw_combo(surf, t)
        self._draw_jetpack_bar(surf, t)
        self._draw_record_flash(surf, t)
        self._draw_teleport_flash(surf)
        if self.state == "play" and self.player is not None and not self.player.dying:
            try:
                self.ads.draw_game(surf)
            except Exception as exc:
                print("[Game] ads.draw_game:", exc)
        # Экранные тексты — поверх всего
        for txt in self.texts:
            if not getattr(txt, "world", True):
                self._safe_draw(txt, surf, 0)

    def _panel(self, surf, rect, alpha=HUD_PANEL_ALPHA, color=(10, 15, 35)):
        """Полупрозрачная закруглённая подложка."""
        rect = pygame.Rect(rect)
        tmp = pygame.Surface(rect.size, pygame.SRCALPHA)
        draw_rounded_rect(tmp, tmp.get_rect(), (*color, alpha), radius=12)
        surf.blit(tmp, rect.topleft)

    def _draw_score_panel(self, surf):
        """Слева сверху: очки, высота, рекорд."""
        self._panel(surf, (8, 8, 190, 84))
        draw_text(surf, f"ОЧКИ {self.score}", 18, 14, size=30, color=WHITE, anchor="topleft",
                  bold=True, shadow=(0, 0, 0))
        draw_text(surf, f"ВЫСОТА {int(self.height_m)} м", 18, 50, size=19, color=LIGHT_GRAY,
                  anchor="topleft", bold=True, shadow=(0, 0, 0))
        best = 0
        try:
            best = int(self.save.best_score)
        except Exception:
            pass
        if self.record_beaten:
            # Рекорд бьётся прямо сейчас — показываем текущий счёт золотом
            draw_text(surf, f"РЕКОРД {max(best, self.score)}", 18, 70, size=19, color=GOLD,
                      anchor="topleft", bold=True, shadow=(0, 0, 0))
        else:
            draw_text(surf, f"РЕКОРД {best}", 18, 70, size=19, color=(255, 230, 150),
                      anchor="topleft", bold=True, shadow=(0, 0, 0))

    def _draw_caps_panel(self, surf, t):
        """Справа сверху: счётчик крышек и мини-дудлер активного скина."""
        self._panel(surf, (SCREEN_W - 178, 8, 170, 56))
        caps = 0
        try:
            caps = int(self.save.caps)
        except Exception:
            pass
        draw_cap_icon(surf, SCREEN_W - 158, 36, 10)
        draw_text(surf, str(caps), SCREEN_W - 142, 36, size=24, color=WHITE, anchor="midleft",
                  bold=True, shadow=(0, 0, 0))
        # Светлая «медалька» под мини-дудлером: тёмные скины («67», «52», кибер)
        # иначе сливаются с тёмной подложкой панели
        pygame.draw.circle(surf, (62, 74, 118), (SCREEN_W - 40, 36), 23)
        pygame.draw.circle(surf, UI_BORDER, (SCREEN_W - 40, 36), 23, 2)
        # Мини-дудлер прыгает на месте
        bob = abs(math.sin(t * 4.0)) * 4
        squash = 1.0 + 0.08 * math.sin(t * 8.0)
        try:
            draw_doodler(surf, SCREEN_W - 40, 38 - bob, self.active_skin, t, facing=-1,
                         squash=squash, scale=0.45)
        except Exception as exc:
            print("[Game] mini doodler:", exc)

    def _draw_bonus_icons(self, surf, t):
        """Иконки активных бонусов с кольцом-таймером под панелью счёта."""
        player = self.player
        if player is None:
            return
        active = []
        if getattr(player, "shield", False):
            active.append(("shield", 1.0))
        heli = getattr(player, "heli_time", 0.0)
        if heli > 0:
            active.append(("heli", clamp(heli / HELI_TIME, 0.0, 1.0) if HELI_TIME else 1.0))
        magnet = getattr(player, "magnet_time", 0.0)
        if magnet > 0:
            active.append(("magnet", clamp(magnet / MAGNET_TIME, 0.0, 1.0) if MAGNET_TIME else 1.0))
        star = getattr(player, "star_time", 0.0)
        if star > 0:
            active.append(("star", clamp(star / STAR_TIME, 0.0, 1.0) if STAR_TIME else 1.0))
        if not active:
            return
        x0, y0, step, r = 30, 118, 44, 17
        for i, (kind, frac) in enumerate(active):
            cx = x0 + i * step
            cy = y0
            # Подложка и кольцо-таймер
            pygame.draw.circle(surf, (15, 20, 40), (cx, cy), r + 3)
            pygame.draw.circle(surf, (60, 70, 100), (cx, cy), r + 3, 2)
            ring_color = self._bonus_color(kind)
            if frac > 0.02:
                rect = pygame.Rect(cx - r - 1, cy - r - 1, 2 * r + 2, 2 * r + 2)
                start = math.pi / 2 - 2 * math.pi * frac
                stop = math.pi / 2
                # мигание в последнюю секунду
                if frac < 0.25 and int(t * 8) % 2 == 0:
                    ring_color = WHITE
                try:
                    pygame.draw.arc(surf, ring_color, rect, start, stop, 4)
                except Exception:
                    pass
            self._draw_bonus_icon(surf, cx, cy, kind, t)

    @staticmethod
    def _bonus_color(kind):
        """Цвет бонуса по типу."""
        return {"shield": CYAN, "heli": RED, "magnet": (255, 90, 90), "star": GOLD}.get(kind, WHITE)

    def _draw_bonus_icon(self, surf, cx, cy, kind, t):
        """Иконка бонуса примитивами (без emoji)."""
        if kind == "shield":
            tmp = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(tmp, (120, 220, 255, 130), (15, 15), 11)
            pygame.draw.circle(tmp, (200, 245, 255, 220), (15, 15), 11, 2)
            pygame.draw.arc(tmp, (255, 255, 255, 230), pygame.Rect(6, 6, 18, 18), 1.8, 2.8, 2)
            surf.blit(tmp, (cx - 15, cy - 15))
        elif kind == "heli":
            # Кепка с пропеллером
            pygame.draw.ellipse(surf, RED, pygame.Rect(cx - 9, cy - 3, 18, 12))
            pygame.draw.rect(surf, (200, 40, 40), pygame.Rect(cx - 11, cy + 5, 22, 4), border_radius=2)
            pygame.draw.line(surf, DARK_GRAY, (cx, cy - 3), (cx, cy - 9), 2)
            span = 11 * abs(math.cos(t * 14))
            pygame.draw.line(surf, LIGHT_GRAY, (cx - span, cy - 9), (cx + span, cy - 9), 3)
        elif kind == "magnet":
            # Магнит-подкова: красная дуга и синие полюса
            rect = pygame.Rect(cx - 9, cy - 9, 18, 18)
            pygame.draw.arc(surf, (230, 60, 60), rect, math.pi, 2 * math.pi, 6)
            pygame.draw.rect(surf, (230, 60, 60), pygame.Rect(cx - 9, cy - 1, 5, 6))
            pygame.draw.rect(surf, (230, 60, 60), pygame.Rect(cx + 4, cy - 1, 5, 6))
            pygame.draw.rect(surf, (80, 140, 240), pygame.Rect(cx - 9, cy + 4, 5, 5))
            pygame.draw.rect(surf, (80, 140, 240), pygame.Rect(cx + 4, cy + 4, 5, 5))
        elif kind == "star":
            pts = self._star_points(cx, cy, 11 + math.sin(t * 6) * 1.5, 5, 5, rot=t * 2)
            pygame.draw.polygon(surf, GOLD, pts)
            pygame.draw.polygon(surf, (255, 240, 180), pts, 2)

    @staticmethod
    def _star_points(cx, cy, r_out, r_in, n=5, rot=0.0):
        """Вершины звезды."""
        pts = []
        for i in range(n * 2):
            ang = rot - math.pi / 2 + i * math.pi / n
            r = r_out if i % 2 == 0 else r_in
            pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
        return pts

    def _draw_combo(self, surf, t):
        """Индикатор комбо по центру сверху: пульсирует, радужный от x5.

        Размер пульсации квантуется (шаг 2 px — всего 5 вариантов в кэше текста),
        а радужный цвет накладывается умножением на белый текст: иначе каждый кадр
        был бы новым рендером и кэш надписей (RenderCache.text) постоянно вытеснялся бы."""
        if self.combo < 2 or self.combo_timer <= 0:
            return
        # Место — под панелью крышек справа: не наезжает ни на панель очков (x <= 198),
        # ни на иконки бонусов (слева), ни на панель крышек (y <= 64), ни на баннер (y >= 146)
        cx, cy = COMBO_HUD_POS
        pulse = 1.0 + 0.12 * math.sin(t * 10.0)
        size = 2 * int(round(15 * pulse))       # 26..34 px
        text = f"x{self.combo} КОМБО"
        # длинное комбо (x100) не вылезает за колонку: размер ограничен её шириной
        size = min(size, 2 * (fit_text_size(text, COMBO_HUD_MAX_W, size, 14, True) // 2))
        if self.combo >= COMBO_RAINBOW:
            color = rainbow(t * 1.5)
            layer_h = 64
            layer = self._combo_layer
            if layer is None or layer.get_size() != (SCREEN_W, layer_h):
                layer = pygame.Surface((SCREEN_W, layer_h), pygame.SRCALPHA)
                self._combo_layer = layer
            layer.fill((0, 0, 0, 0))
            # Белый текст с чёрной обводкой (кэшируется), затем тонируем: чёрное остаётся чёрным
            draw_text(layer, text, cx, layer_h // 2, size=size, color=WHITE,
                      anchor="center", bold=True, outline=BLACK)
            layer.fill(color, special_flags=pygame.BLEND_RGB_MULT)
            surf.blit(layer, (0, cy - layer_h // 2))
        else:
            color = ORANGE
            draw_text(surf, text, cx, cy, size=size, color=color,
                      anchor="center", bold=True, outline=DARK_BROWN)
        # Полоска оставшегося времени комбо
        frac = clamp(self.combo_timer / COMBO_WINDOW, 0.0, 1.0) if COMBO_WINDOW else 0.0
        bar_w = 120
        bx = cx - bar_w / 2
        by = cy + 20
        pygame.draw.rect(surf, (20, 25, 45), pygame.Rect(bx, by, bar_w, 6), border_radius=3)
        if frac > 0:
            pygame.draw.rect(surf, color, pygame.Rect(bx, by, int(bar_w * frac), 6), border_radius=3)

    def _draw_jetpack_bar(self, surf, t):
        """Полоска заряда джетпака внизу по центру."""
        player = self.player
        if player is None or player.jetpack is None:
            return
        jp = player.jetpack
        total = getattr(jp, "total", 1.0) or 1.0
        frac = clamp(getattr(jp, "time_left", 0.0) / total, 0.0, 1.0)
        turbo = getattr(jp, "turbo", False)
        bar_w, bar_h = 220, 18
        bx = SCREEN_W / 2 - bar_w / 2
        by = SCREEN_H - 46
        # Подложка
        self._panel(surf, (bx - 12, by - 30, bar_w + 24, bar_h + 42), alpha=130)
        pygame.draw.rect(surf, (25, 25, 35), pygame.Rect(bx, by, bar_w, bar_h), border_radius=9)
        if frac > 0:
            fill = pygame.Rect(bx, by, max(bar_h, int(bar_w * frac)), bar_h)
            if turbo:
                base = lerp_color(GOLD, (255, 240, 150), 0.5 + 0.5 * math.sin(t * 12))
            else:
                base = lerp_color(RED, ORANGE, 0.5 + 0.5 * math.sin(t * 10))
            pygame.draw.rect(surf, base, fill, border_radius=9)
            # Блик
            hl = pygame.Rect(fill.x + 4, fill.y + 3, max(2, fill.w - 8), 4)
            pygame.draw.rect(surf, (255, 255, 255), hl, border_radius=2)
            # Огонёк на конце
            pygame.draw.circle(surf, WHITE, (fill.right - 6, fill.centery), 4)
        pygame.draw.rect(surf, WHITE if turbo else LIGHT_GRAY, pygame.Rect(bx, by, bar_w, bar_h), 2,
                         border_radius=9)
        label = "ТУРБО" if turbo else "ДЖЕТПАК"
        color = GOLD if turbo else (255, 150, 120)
        draw_text(surf, f"{label}  {max(0.0, getattr(jp, 'time_left', 0.0)):.1f} с", SCREEN_W / 2, by - 16,
                  size=20, color=color, anchor="center", bold=True, outline=BLACK)

    def _draw_record_flash(self, surf, t):
        """Мерцающая вспышка «НОВЫЙ РЕКОРД!» с кубком над надписью (единственная такая надпись)."""
        if self.record_flash_timer <= 0:
            return
        k = clamp(self.record_flash_timer / RECORD_FLASH_TIME, 0.0, 1.0)
        a = 0.5 + 0.5 * math.sin(t * 18)
        alpha = int((110 + 145 * a) * min(1.0, k * 3))
        size = 42 + int(6 * a)
        color = lerp_color(GOLD, WHITE, a * 0.5)
        y = RECORD_FLASH_Y
        try:
            draw_glow(surf, SCREEN_W / 2, y, 150, GOLD, alpha=int(50 * k))
        except Exception:
            pass
        # кубок из требований («кубок НОВЫЙ РЕКОРД!») — над надписью, слегка покачивается
        draw_trophy(surf, SCREEN_W / 2, y - 60 + math.sin(t * 4) * 3, 0.9 + 0.08 * a, alpha)
        draw_text(surf, "НОВЫЙ РЕКОРД!", SCREEN_W / 2, y, size=size, color=color, anchor="center",
                  bold=True, outline=DARK_BROWN, alpha=alpha)
        # Маленькие звёздочки вокруг
        for i in range(6):
            ang = t * 2 + i * math.pi / 3
            sx = SCREEN_W / 2 + math.cos(ang) * 150
            sy = y + math.sin(ang) * 34
            pts = self._star_points(sx, sy, 6 + 2 * a, 2.5, 5, rot=t * 3)
            pygame.draw.polygon(surf, GOLD, pts)

    def _draw_teleport_flash(self, surf):
        """Белая вспышка телепорта (затухает)."""
        if self.teleport_flash <= 0:
            return
        tmp = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        tmp.fill((255, 255, 255, int(255 * clamp(self.teleport_flash, 0.0, 1.0))))
        surf.blit(tmp, (0, 0))


def main():
    """Точка входа: создать игру, запустить цикл, корректно завершить pygame."""
    game = None
    try:
        game = Game()
        game.run()
    except Exception:
        # Любая непредвиденная ошибка — в консоль, окно закрываем аккуратно
        traceback.print_exc()
        if game is not None:
            try:
                game.save.save(force=True)
            except Exception:
                pass
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
