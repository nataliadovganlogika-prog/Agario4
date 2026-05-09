import pygame
from socket import *
from threading import Thread
from random import randint
from math import hypot

sock = socket(AF_INET, SOCK_STREAM)
sock.connect(("localhost", 8080))

pygame.init()

WIDTH = 1000
HEIGHT = 800

win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mini Agar.io")

clock = pygame.time.Clock()

font = pygame.font.Font(None, 30)
big_font = pygame.font.Font(None, 80)

MENU = "menu"
GAME = "game"
LOSE = "lose"

game_state = MENU

nickname = ""
input_active = True

my_id = 0
my_player = [0, 0, 50]

all_players = []

lose = False
running = True

buffer = ""

class Food:
    def __init__(self):
        self.x = randint(-3000, 3000)
        self.y = randint(-3000, 3000)
        self.radius = randint(5, 12)

        self.color = (
            randint(50, 255),
            randint(50, 255),
            randint(50, 255)
        )

    def draw(self, cam_x, cam_y, scale):
        sx = int((self.x - cam_x) * scale + WIDTH // 2)
        sy = int((self.y - cam_y) * scale + HEIGHT // 2)

        pygame.draw.circle(
            win,
            self.color,
            (sx, sy),
            max(2, int(self.radius * scale))
        )

    def collision(self, px, py, pr):
        return hypot(self.x - px, self.y - py) < pr


foods = [Food() for _ in range(250)]

def connect_to_server(name):
    global my_id, my_player, buffer

    sock.send((name + "\n").encode())

    while True:
        buffer += sock.recv(64).decode()

        if '\n' in buffer:
            line, buffer = buffer.split('\n', 1)

            data = line.split(',')

            if len(data) >= 4:
                my_id = int(data[0])
                my_player = list(map(int, data[1:4]))
                break

    sock.setblocking(False)

def receive():
    global all_players, lose, running, buffer

    while running:

        try:
            chunk = sock.recv(4096).decode()

            if not chunk:
                continue

            buffer += chunk

            while '\n' in buffer:

                line, buffer = buffer.split('\n', 1)

                line = line.strip()

                if line == "LOSE":
                    lose = True
                    continue

                players = []

                for p in line.split('|'):

                    d = p.split(',')

                    if len(d) == 5:

                        try:
                            players.append([
                                int(d[0]),
                                int(d[1]),
                                int(d[2]),
                                int(d[3]),
                                d[4]
                            ])

                        except:
                            pass

                if players:
                    all_players = players

        except:
            pass

def draw_grid(scale, cam_x, cam_y):

    grid_size = int(80 * scale)

    offset_x = int(cam_x * scale) % grid_size
    offset_y = int(cam_y * scale) % grid_size

    for x in range(-grid_size, WIDTH + grid_size, grid_size):

        pygame.draw.line(
            win,
            (230, 230, 230),
            (x - offset_x, 0),
            (x - offset_x, HEIGHT)
        )

    for y in range(-grid_size, HEIGHT + grid_size, grid_size):

        pygame.draw.line(
            win,
            (230, 230, 230),
            (0, y - offset_y),
            (WIDTH, y - offset_y)
        )

def draw_menu():

    win.fill((35, 35, 45))

    title = big_font.render("AGAR.IO", True, (255, 255, 255))
    win.blit(title, (WIDTH // 2 - title.get_width() // 2, 120))

    text = font.render("Введіть ваш нікнейм:", True, (255, 255, 255))
    win.blit(text, (WIDTH // 2 - 120, 320))

    pygame.draw.rect(win, (255, 255, 255),
                     (WIDTH // 2 - 150, 360, 300, 50), 2)

    nick_surface = font.render(nickname, True, (255, 255, 255))

    win.blit(nick_surface, (WIDTH // 2 - 130, 373))

    play = font.render("Натисніть Enter щоб розпочати", True, (100, 255, 100))
    win.blit(play, (WIDTH // 2 - play.get_width() // 2, 460))

def draw_lose():

    win.fill((20, 20, 20))

    txt = big_font.render("ВИ ПРОГРАЛИ", True, (255, 0, 0))
    win.blit(txt, (WIDTH // 2 - txt.get_width() // 2, 260))

    score = font.render(
        f"Final size: {my_player[2]}",
        True,
        (255, 255, 255)
    )

    win.blit(score, (WIDTH // 2 - score.get_width() // 2, 380))

    restart = font.render(
        "Натисніть R щоб перезавантажити",
        True,
        (255, 255, 255)
    )

    win.blit(restart, (WIDTH // 2 - restart.get_width() // 2, 450))

thread_started = False

while running:

    clock.tick(60)

    for e in pygame.event.get():

        if e.type == pygame.QUIT:
            running = False

        if game_state == MENU:

            if e.type == pygame.KEYDOWN:

                if e.key == pygame.K_BACKSPACE:
                    nickname = nickname[:-1]

                elif e.key == pygame.K_RETURN:

                    if nickname.strip() != "":

                        connect_to_server(nickname)

                        if not thread_started:
                            Thread(target=receive, daemon=True).start()
                            thread_started = True

                        game_state = GAME

                else:

                    if len(nickname) < 15:
                        nickname += e.unicode

        if game_state == LOSE:

            if e.type == pygame.KEYDOWN:

                if e.key == pygame.K_r:

                    lose = False

                    my_player = [0, 0, 50]

                    foods = [Food() for _ in range(250)]

                    game_state = GAME

    if game_state == MENU:

        draw_menu()

    elif game_state == GAME:

        if lose:
            game_state = LOSE

        keys = pygame.key.get_pressed()

        speed = max(4, int(15 - my_player[2] / 20))

        if keys[pygame.K_w]:
            my_player[1] -= speed

        if keys[pygame.K_s]:
            my_player[1] += speed

        if keys[pygame.K_a]:
            my_player[0] -= speed

        if keys[pygame.K_d]:
            my_player[0] += speed

        scale = max(0.25, min(60 / my_player[2], 1.5))

        win.fill((245, 245, 245))

        draw_grid(scale, my_player[0], my_player[1])

        remove_food = []

        for food in foods:

            if food.collision(
                my_player[0],
                my_player[1],
                my_player[2]
            ):

                remove_food.append(food)

                my_player[2] += 1

            else:

                food.draw(
                    my_player[0],
                    my_player[1],
                    scale
                )

        for food in remove_food:

            foods.remove(food)

            foods.append(Food())

        for p in all_players:

            if p[0] == my_id:
                continue

            sx = int((p[1] - my_player[0]) * scale + WIDTH // 2)
            sy = int((p[2] - my_player[1]) * scale + HEIGHT // 2)

            radius = int(p[3] * scale)

            pygame.draw.circle(
                win,
                (0, 120, 0),
                (sx, sy),
                radius
            )

            name = font.render(
                p[4],
                True,
                (0, 0, 0)
            )

            win.blit(
                name,
                (
                    sx - name.get_width() // 2,
                    sy - radius - 25
                )
            )

        pygame.draw.circle(
            win,
            (50, 220, 100),
            (WIDTH // 2, HEIGHT // 2),
            int(my_player[2] * scale)
        )

        name = font.render(
            nickname,True,(0, 0, 0)
        )

        win.blit(
            name,
            (
                WIDTH // 2 - name.get_width() // 2,
                HEIGHT // 2 - int(my_player[2] * scale) - 25
            )
        )


        leaderboard = sorted(
            all_players,
            key=lambda x: x[3],
            reverse=True
        )

        pygame.draw.rect(win, (0, 0, 180),
                         (10, 10, 220, 180))

        title = font.render("Таблиця лідера", True, (190, 190, 0))
        win.blit(title, (20, 20))

        for i, p in enumerate(leaderboard[:5]):

            txt = font.render(
                f"{i + 1}. {p[4]} ({p[3]})",
                True,
                (190, 190, 0)
            )

            win.blit(txt, (20, 55 + i * 25))


        fps = int(clock.get_fps())

        fps_text = font.render(
            f"FPS: {fps}",
            True,
            (150, 0, 0)
        )

        win.blit(fps_text, (WIDTH - 120, 20))


        try:

            sock.send(
                f"{my_id},{my_player[0]},"
                f"{my_player[1]},{my_player[2]}\n".encode()
            )

        except:
            pass


    elif game_state == LOSE:

        draw_lose()

    pygame.display.update()

sock.close()
pygame.quit()