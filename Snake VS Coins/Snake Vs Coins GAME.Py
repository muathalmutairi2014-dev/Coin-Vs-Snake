import os
import pygame
import random

# 1. Setup
pygame.init()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Snake vs Birds - Freeze Edition")
clock = pygame.time.Clock()


class AnimatedSprite:
    def __init__(self, filename, size, fallback_color):
        self.frames = []
        self.index = 0
        self.last_update = pygame.time.get_ticks()
        filepath = os.path.join(BASE_DIR, filename)
        try:
            raw_frames = pygame.image.load_animation(filepath)
            for surf, duration in raw_frames:
                scaled = pygame.transform.scale(surf.convert_alpha(), size)
                self.frames.append((scaled, duration if duration > 0 else 100))
        except Exception:
            surf = pygame.Surface(size)
            surf.fill(fallback_color)
            self.frames = [(surf, 100)]

    def get_image(self, now):
        image, duration = self.frames[self.index]
        if len(self.frames) > 1 and now - self.last_update >= duration:
            self.index = (self.index + 1) % len(self.frames)
            self.last_update = now
            image, _ = self.frames[self.index]
        return image


class MultiFileSprite:
    def __init__(self, filenames, size, delay_ms, fallback_color):
        self.frames = []
        self.index = 0
        self.delay = delay_ms
        self.last_update = pygame.time.get_ticks()

        for file in filenames:
            filepath = os.path.join(BASE_DIR, file)
            try:
                img = pygame.image.load(filepath).convert_alpha()
                self.frames.append(pygame.transform.scale(img, size))
            except Exception:
                pass

        if not self.frames:
            surf = pygame.Surface(size)
            surf.fill(fallback_color)
            self.frames.append(surf)

    def get_image(self, now):
        if len(self.frames) > 1 and now - self.last_update >= self.delay:
            self.index = (self.index + 1) % len(self.frames)
            self.last_update = now
        return self.frames[self.index]


# Load Sprites
player_anim = AnimatedSprite("Snake.gif", (110, 110), (0, 200, 150))
enemy_anim = MultiFileSprite(
    ["birdfly1.png", "birdfly2.png", "birdfly3.png", "birdfly4.png"],
    (110, 110),
    120,
    (255, 0, 0),
)
coin_anim = AnimatedSprite("coin.gif", (110, 110), (255, 215, 0))

player = pygame.Rect(WIDTH // 2 - 55, HEIGHT // 2 - 55, 110, 110)
player_speed = 7
move_x, move_y = -1, 0
last_dir = (-1, 0)

# Dash settings
dash_speed = 18
dash_duration = 400
dash_cooldown = 4000
last_dash_time = -4000

# Freeze Power-Up settings
freeze_orb = pygame.Rect(-200, -200, 55, 55)
freeze_active_on_map = False
freeze_end_time = 0
freeze_duration = 3000

# Score, High Score & Game State
score = 0
high_score = 0
game_state = "menu"
font = pygame.font.SysFont(None, 48)
title_font = pygame.font.SysFont(None, 84)

coin = pygame.Rect(WIDTH // 4, HEIGHT // 4, 110, 110)
enemies = []
enemy_positions = []
enemy_speed = 3.0
max_enemy_speed = 6.25  # Slightly slower than player_speed (7)
# Main Game Loop
running = True
while running:
    # 2. Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    # 3. Update
    keys = pygame.key.get_pressed()
    current_time = pygame.time.get_ticks()

    if game_state == "menu":
        if keys[pygame.K_1]:
            enemies = [pygame.Rect(80, 80, 110, 110)]
            enemy_positions = [pygame.Vector2(80, 80)]
            enemy_speed = 3.0
            score = 0
            last_dir = (-1, 0)
            player.center = (WIDTH // 2, HEIGHT // 2)
            coin.center = (WIDTH // 4, HEIGHT // 4)
            last_dash_time = -4000
            freeze_active_on_map = False
            freeze_end_time = 0
            game_state = "playing"

        elif keys[pygame.K_2]:
            enemies = [
                pygame.Rect(80, 80, 110, 110),
                pygame.Rect(WIDTH - 190, HEIGHT - 190, 110, 110),
            ]
            enemy_positions = [
                pygame.Vector2(80, 80),
                pygame.Vector2(WIDTH - 190, HEIGHT - 190),
            ]
            enemy_speed = 3.0
            score = 0
            last_dir = (-1, 0)
            player.center = (WIDTH // 2, HEIGHT // 2)
            coin.center = (WIDTH // 4, HEIGHT // 4)
            last_dash_time = -4000
            freeze_active_on_map = False
            freeze_end_time = 0
            game_state = "playing"

    elif game_state == "playing":
        if keys[pygame.K_SPACE] and current_time - last_dash_time >= dash_cooldown:
            last_dash_time = current_time

        is_dashing = current_time - last_dash_time < dash_duration
        current_speed = dash_speed if is_dashing else player_speed

        move_x = 0
        move_y = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_x -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_x += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            move_y -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            move_y += 1

        if move_x != 0 or move_y != 0:
            last_dir = (move_x, move_y)

        player.x += move_x * current_speed
        player.y += move_y * current_speed
        player.clamp_ip(screen.get_rect())

        # Coin pickup
        if player.colliderect(coin):
            score += 1
            coin.x = random.randint(60, WIDTH - 170)
            coin.y = random.randint(60, HEIGHT - 170)
            if score > high_score:
                high_score = score
            if score % 5 == 0:
                enemy_speed = min(enemy_speed + 0.010, max_enemy_speed)
                if not freeze_active_on_map:
                    freeze_orb.x = random.randint(80, WIDTH - 140)
                    freeze_orb.y = random.randint(80, HEIGHT - 140)
                    freeze_active_on_map = True

        # Freeze Orb pickup
        if freeze_active_on_map and player.colliderect(freeze_orb):
            freeze_active_on_map = False
            freeze_end_time = current_time + freeze_duration

        birds_frozen = current_time < freeze_end_time
        player_hitbox = player.inflate(-30, -30)

        for i in range(len(enemies)):
            e = enemies[i]
            pos = enemy_positions[i]

            if not birds_frozen:
                if pos.x < player.x:
                    pos.x += enemy_speed
                elif pos.x > player.x:
                    pos.x -= enemy_speed

                if pos.y < player.y:
                    pos.y += enemy_speed
                elif pos.y > player.y:
                    pos.y -= enemy_speed

                e.topleft = (round(pos.x), round(pos.y))

                for j in range(len(enemies)):
                    if i != j and e.colliderect(enemies[j]):
                        if pos.x < enemy_positions[j].x:
                            pos.x -= enemy_speed
                        else:
                            pos.x += enemy_speed
                        if pos.y < enemy_positions[j].y:
                            pos.y -= enemy_speed
                        else:
                            pos.y += enemy_speed
                        e.topleft = (round(pos.x), round(pos.y))

                e.clamp_ip(screen.get_rect())
                pos.x, pos.y = e.topleft

                bird_hitbox = e.inflate(-45, -45)
                if player_hitbox.colliderect(bird_hitbox):
                    game_state = "game_over"

    elif game_state == "game_over":
        if keys[pygame.K_r]:
            game_state = "menu"

    # 4. Draw
    screen.fill((30, 30, 40))

    if game_state == "menu":
        title_text = title_font.render("SNAKE VS BIRDS", True, (255, 215, 0))
        easy_text = font.render("Press 1 for EASY (1 Bird)", True, (0, 200, 150))
        hard_text = font.render("Press 2 for HARD (2 Birds)", True, (255, 80, 80))

        screen.blit(title_text, title_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 120)))
        screen.blit(easy_text, easy_text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        screen.blit(hard_text, hard_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70)))

    else:
        if freeze_active_on_map:
            pygame.draw.ellipse(screen, (80, 200, 255), freeze_orb)
            pygame.draw.ellipse(screen, (220, 245, 255), freeze_orb.inflate(-18, -18))

        if game_state == "playing" and (current_time - last_dash_time < dash_duration):
            pygame.draw.ellipse(screen, (0, 255, 255), player.inflate(16, 16), 4)

        base_snake = player_anim.get_image(current_time)
        dx, dy = last_dir

        if dx > 0:
            flipped_snake = pygame.transform.flip(base_snake, True, False)
            if dy == -1:
                final_snake = pygame.transform.rotate(flipped_snake, 45)
            elif dy == 1:
                final_snake = pygame.transform.rotate(flipped_snake, -45)
            else:
                final_snake = flipped_snake
        else:
            if dx == -1 and dy == -1:
                final_snake = pygame.transform.rotate(base_snake, -45)
            elif dx == -1 and dy == 1:
                final_snake = pygame.transform.rotate(base_snake, 45)
            elif dx == 0 and dy == -1:
                final_snake = pygame.transform.rotate(base_snake, -90)
            elif dx == 0 and dy == 1:
                final_snake = pygame.transform.rotate(base_snake, 90)
            else:
                final_snake = base_snake

        snake_rect = final_snake.get_rect(center=player.center)
        screen.blit(final_snake, snake_rect)

        screen.blit(coin_anim.get_image(current_time), coin)

        birds_frozen = current_time < freeze_end_time
        bird_img = enemy_anim.get_image(current_time)
        for e in enemies:
            if e.x > player.x:
                screen.blit(pygame.transform.flip(bird_img, True, False), e)
            else:
                screen.blit(bird_img, e)
            if birds_frozen:
                pygame.draw.ellipse(screen, (100, 220, 255), e.inflate(10, 10), 4)

        score_text = font.render(f"Score: {score}", True, (255, 255, 255))
        screen.blit(score_text, (30, 25))

        high_score_text = font.render(f"High Score: {high_score}", True, (255, 215, 0))
        screen.blit(high_score_text, (30, 115))

        if current_time - last_dash_time >= dash_cooldown:
            dash_status = "Dash: READY"
            dash_color = (0, 255, 255)
        else:
            dash_status = "Dash: Charging..."
            dash_color = (150, 150, 150)

        dash_text = font.render(dash_status, True, dash_color)
        screen.blit(dash_text, (30, 70))

        if birds_frozen and game_state == "playing":
            secs_left = (freeze_end_time - current_time) / 1000
            freeze_text = font.render(f"FROZEN: {secs_left:.1f}s", True, (100, 220, 255))
            screen.blit(freeze_text, (30, 160))

        if game_state == "game_over":
            over_text = title_font.render("GAME OVER! Press R for Menu", True, (255, 80, 80))
            screen.blit(over_text, over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
