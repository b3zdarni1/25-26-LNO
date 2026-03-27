from ursina import *
from random import randint, choice, seed

seed(7)
sign = lambda x: (x > 0) - (x < 0)
app = Ursina()
window.title = "Ursina Platformer"
window.color = color.rgb(135, 206, 235)
window.fps_counter.enabled = True
window.exit_button.visible = False

sky = Sky()
sun = DirectionalLight()
sun.look_at(Vec3(1, -1, -1))
ambient = AmbientLight(color=color.rgba(120, 120, 120, 255))

# -----------------------------------------------------------------------------
# Настройки
# -----------------------------------------------------------------------------
LEVEL_LENGTH = 60
LEVEL_HALF_WIDTH = 5

GRAVITY = 24
MOVE_SPEED = 6.5
JUMP_SPEED = 9
FALL_LIMIT = -15

# -----------------------------------------------------------------------------
# Списки объектов уровня
# -----------------------------------------------------------------------------
solid_entities = []  # всё, с чем нужно сталкиваться
coin_entities = []  # монеты
enemy_entities = []  # враги

game_state = "playing"
score = 0


def destroy_list(items):
    """Полностью уничтожает все Entity из списка."""
    while items:
        destroy(items.pop())


def add_solid(position, scale=(1, 1, 1), model="cube", texture="white_cube", col=color.white):
    """Создаёт блок уровня и добавляет его в список коллизий."""
    e = Entity(
        model=model,
        texture=texture,
        color=col,
        position=position,
        scale=scale,
        collider="box",
    )
    solid_entities.append(e)
    return e


def clear_level():
    """Удаляет все прошлые объекты уровня перед новой генерацией."""
    destroy_list(solid_entities)
    destroy_list(coin_entities)
    destroy_list(enemy_entities)


def build_level():
    """Процедурно создаёт новый уровень."""
    clear_level()

    # Пол
    for x in range(LEVEL_LENGTH):
        for z in range(-LEVEL_HALF_WIDTH, LEVEL_HALF_WIDTH + 1):
            add_solid((x, 0, z), texture="grass", col=color.white)

    # Бортики
    for x in range(LEVEL_LENGTH):
        add_solid((x, 1, -LEVEL_HALF_WIDTH - 1), col=color.dark_gray)
        add_solid((x, 1, LEVEL_HALF_WIDTH + 1), col=color.dark_gray)

    # Препятствия
    for _ in range(16):
        x = randint(4, LEVEL_LENGTH - 6)
        z = randint(-LEVEL_HALF_WIDTH + 1, LEVEL_HALF_WIDTH - 1)
        h = randint(1, 4)
        model = choice(["cube", "cylinder"])
        add_solid(
            (x, h / 2 + 0.5, z),
            scale=(1, h, 1),
            model=model,
            texture="white_cube",
            col=color.rgb(randint(80, 220), randint(80, 220), randint(80, 220)),
        )

    # Небольшие платформы
    for x in range(8, LEVEL_LENGTH, 11):
        platform_y = randint(2, 4)
        for i in range(3):
            add_solid((x + i, platform_y, randint(-2, 2)), col=color.orange)

    # Финиш
    global goal
    goal = Entity(
        model="cube",
        texture="white_cube",
        color=color.lime,
        scale=(2, 0.35, 2),
        position=(LEVEL_LENGTH - 4, 1.2, 0),
        collider="box",
    )
    solid_entities.append(goal)

    # Монеты
    for _ in range(18):
        coin = Entity(
            model="sphere",
            color=color.yellow,
            scale=0.35,
            position=(randint(3, LEVEL_LENGTH - 6), randint(2, 5), randint(-3, 3)),
        )
        coin.base_y = coin.y
        coin.phase = randint(0, 100) / 10
        coin_entities.append(coin)

    # Враги
    for x in range(12, LEVEL_LENGTH - 8, 13):
        e = Entity(
            model="cube",
            color=color.red,
            scale=(1, 1, 1),
            position=(x, 1.0, randint(-2, 2)),
        )
        e.direction = choice([-1, 1])
        e.speed = randint(2, 4)
        enemy_entities.append(e)


# -----------------------------------------------------------------------------
# Игрок и скины
# -----------------------------------------------------------------------------
skin_variants = [
    {"name": "Классический", "texture": "brick", "color": color.white},
    {"name": "Неоновый", "texture": "white_cube", "color": color.azure},
    {"name": "Огненный", "texture": "white_cube", "color": color.orange},
]

class Player(Entity):
    def __init__(self, **kwargs):
        super().__init__(
            model="cube",
            scale=(1, 2, 1),
            collider="box",
            position=(1, 4, 0),
            **kwargs
        )
        self.velocity = Vec3(0, 0, 0)
        self.grounded = False
        self.jump_requested = False
        self.spawn_point = Vec3(self.position)
        self.skin_index = 0
        self.apply_skin(0)

    def apply_skin(self, index: int):
        self.skin_index = index % len(skin_variants)
        skin = skin_variants[self.skin_index]
        self.texture = skin["texture"]
        self.color = skin["color"]

    def respawn(self):
        self.position = self.spawn_point
        self.velocity = Vec3(0, 0, 0)
        self.grounded = False
        self.jump_requested = False


player = Player()

# -----------------------------------------------------------------------------
# UI
# -----------------------------------------------------------------------------
score_text = Text(
    text="Монеты: 0",
    position=(-0.86, 0.46),
    scale=1.5,
    origin=(0, 0),
)
skin_text = Text(
    text="Скин: Классический | 1-3 — смена скина | R — рестарт",
    position=(-0.86, 0.41),
    scale=1.1,
    origin=(0, 0),
)
win_text = Text(
    text="Победа! Нажми R для рестарта.",
    origin=(0, 0),
    scale=2,
    y=0.2,
    enabled=False,
)

camera_offset = Vec3(0, 7, -12)


def update_camera():
    target = player.position + camera_offset
    camera.position = lerp(camera.position, target, 6 * time.dt)
    camera.look_at(player.position + Vec3(0, 1, 0))


def blocked_in_direction(direction: Vec3, distance_to_check: float) -> bool:
    """
    Проверяем, не упирается ли игрок в стену по направлению движения.
    Лучи пускаем на нескольких высотах, чтобы не проходить сквозь блоки.
    """
    for y_off in (-0.8, 0.0, 0.8):
        hit = raycast(
            player.world_position + Vec3(0, y_off, 0),
            direction,
            distance=distance_to_check,
            ignore=(player,),
        )
        if hit.hit and hit.entity in solid_entities:
            return True
    return False


def collect_coins():
    global score
    for coin in coin_entities[:]:
        coin.rotation_y += 180 * time.dt
        coin.phase += time.dt * 3
        coin.y = coin.base_y + sin(coin.phase) * 0.15

        if distance(player.position, coin.position) < 1.0:
            coin_entities.remove(coin)
            destroy(coin)
            score += 1
            score_text.text = f"Монеты: {score}"


def update_enemies():
    for enemy in enemy_entities:
        # Движение врага
        enemy.x += enemy.direction * enemy.speed * time.dt

        # Разворот, если впереди нет земли
        front = enemy.world_position + Vec3(enemy.direction * 0.6, 0.2, 0)
        ground_ahead = raycast(front, Vec3(0, -1, 0), distance=1.3, ignore=(enemy,))
        if not ground_ahead.hit:
            enemy.direction *= -1

        # Столкновение с игроком
        if distance(enemy.position, player.position) < 1.0:
            player.respawn()


def reset_game():
    global score, game_state
    score = 0
    game_state = "playing"
    score_text.text = "Монеты: 0"
    win_text.enabled = False
    player.respawn()
    build_level()


def update():
    """
    update() вызывается каждый кадр.
    Здесь двигаем игрока, применяем гравитацию, обновляем камеру,
    монеты и врагов.
    """
    global game_state  # ← ДОБАВЬТЕ ЭТУ СТРОКУ

    if game_state != "playing":
        update_camera()
        return

    dt = time.dt

    # ---------------------------------
    # Горизонтальное движение
    # ---------------------------------
    x_input = held_keys["d"] - held_keys["a"]
    z_input = held_keys["w"] - held_keys["s"]

    move = Vec3(x_input, 0, z_input)
    if move.length() > 0:
        move = move.normalized()
        step = move * MOVE_SPEED * dt

        if step.x != 0 and not blocked_in_direction(Vec3(sign(step.x), 0, 0), abs(step.x) + 0.55):
            player.x += step.x

        if step.z != 0 and not blocked_in_direction(Vec3(0, 0, sign(step.z)), abs(step.z) + 0.55):
            player.z += step.z  # ← также исправьте эту строку (было player.z + = step.z)

    # ---------------------------------
    # Прыжок
    # ---------------------------------
    if player.jump_requested and player.grounded:
        player.velocity.y = JUMP_SPEED
        player.grounded = False
    player.jump_requested = False

    # ---------------------------------
    # Гравитация
    # ---------------------------------
    player.velocity.y -= GRAVITY * dt

    # Если летим вверх — проверяем потолок
    if player.velocity.y > 0:
        head = player.world_position + Vec3(0, player.scale_y * 0.5 - 0.1, 0)
        ceiling = raycast(head, Vec3(0, 1, 0), distance=player.velocity.y * dt + 0.1, ignore=(player,))
        if ceiling.hit and ceiling.entity in solid_entities:
            player.y = ceiling.world_point.y - player.scale_y * 0.5
            player.velocity.y = 0

    # Двигаем по Y
    player.y += player.velocity.y * dt

    # Проверяем землю
    feet = player.world_position + Vec3(0, -player.scale_y * 0.5 + 0.1, 0)
    ground = raycast(feet, Vec3(0, -1, 0), distance=0.3, ignore=(player,))

    if ground.hit and player.velocity.y <= 0:
        player.y = ground.world_point.y + player.scale_y * 0.5
        player.velocity.y = 0
        player.grounded = True
    else:
        player.grounded = False

    # Падение вниз
    if player.y < FALL_LIMIT:
        reset_game()
        return

    # Монеты и враги
    collect_coins()
    update_enemies()

    # Победа
    if distance(player.position, goal.position) < 1.5:
        game_state = "win"
        win_text.enabled = True

    update_camera()

def input(key):
    """
    input() вызывается при отдельных событиях ввода:
    нажатии клавиши, отпускании мыши и т.п.
    Здесь удобно ловить прыжок, рестарт и выбор скина.
    """
    global game_state

    if key == "space":
        player.jump_requested = True

    elif key == "1":
        player.apply_skin(0)
        skin_text.text = "Скин: Классический | 1-3 — смена скина | R — рестарт"
    elif key == "2":
        player.apply_skin(1)
        skin_text.text = "Скин: Неоновый | 1-3 — смена скина | R — рестарт"
    elif key == "3":
        player.apply_skin(2)
        skin_text.text = "Скин: Огненный | 1-3 — смена скина | R — рестарт"

    elif key == "r":
        reset_game()

    elif key == "escape":
        application.quit()

build_level()
app.run()

