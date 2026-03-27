#include <iostream>
#include <vector>
#include <cmath>

// Ограниченные размеры мира и игрока для "минималок"
const int WORLD_WIDTH = 50;
const int WORLD_HEIGHT = 50;
// Исправлена ошибка: в C++ десятичные числа с плавающей запятой должны начинаться с нуля, если дробная часть отсутствует.
// Также, хотя это не было причиной ошибки, рекомендуется использовать суффикс 'f' для float литералов.
const float PLAYER_SPEED = 0.1f;
const float PLAYER_ROTATION_SPEED = 0.05f;

struct Player {
    float x, y; // Позиция игрока
    float angle; // Направление взгляда игрока
};

struct Wall {
    int x1, y1, x2, y2; // Координаты концов стены
};

std::vector<Wall> world_map;
Player player;

void initialize_game() {
    // Простая карта мира с несколькими стенами
    world_map.push_back({0, 0, WORLD_WIDTH - 1, 0}); // Нижняя стена
    world_map.push_back({0, 0, 0, WORLD_HEIGHT - 1}); // Левая стена
    world_map.push_back({WORLD_WIDTH - 1, 0, WORLD_WIDTH - 1, WORLD_HEIGHT - 1}); // Правая стена
    world_map.push_back({0, WORLD_HEIGHT - 1, WORLD_WIDTH - 1, WORLD_HEIGHT - 1}); // Верхняя стена
    world_map.push_back({25, 25, 25, 35}); // Внутренняя стена

    // Начальная позиция и направление игрока
    player.x = 10.0f;
    player.y = 10.0f;
    player.angle = 0.0f; // Смотрит вправо
}

void move_forward() {
    // Движение вперед с учетом угла взгляда
    player.x += cos(player.angle) * PLAYER_SPEED;
    player.y += sin(player.angle) * PLAYER_SPEED;
}

void rotate_left() {
    // Поворот влево
    player.angle -= PLAYER_ROTATION_SPEED;
}

void rotate_right() {
    // Поворот вправо
    player.angle += PLAYER_ROTATION_SPEED;
}

// Функция отрисовки (упрощенная, без графики, только вывод в консоль)
void render() {
    // Здесь могла бы быть логика рендеринга 3D сцены.
    // Для "минималок" мы можем просто вывести текущее состояние:
    std::cout << "Player Position: (" << player.x << ", " << player.y << "), Angle: " << player.angle << std::endl;
}

int main() {
    initialize_game();

    // Пример основного игрового цикла
    for (int frame = 0; frame < 100; ++frame) { // Ограниченное количество кадров
        // Здесь обрабатываются пользовательские команды (например, ввод с клавиатуры)
        // move_forward();
        // rotate_left();

        render(); // Отрисовка кадра
    }

    return 0;
}
