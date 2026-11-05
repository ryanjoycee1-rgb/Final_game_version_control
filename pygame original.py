import pygame
import random
import sys

# Fixed Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

PADDLE_WIDTH = 15
PADDLE_HEIGHT = 100
PADDLE_SPEED = 7
AI_SPEED = 5

BALL_SIZE = 15
BALL_SPEED = 12

WINNING_SCORE = 5

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)

# Class 1: Paddle

class Paddle:
    def __init__(self, x, y, speed=PADDLE_SPEED):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)  #stores paddle position (creates rectangle)
        self.speed = speed # pixels per frame (movement rate)

    def move(self, direction):
        self.rect.y += direction * self.speed #modifies vertical coordinates (-1 for up and 1 for down)

        if self.rect.top < 0:      # to make sure ball doesnt go out of the top of the frame wnidow
            self.rect.top = 0

        if self.rect.bottom > SCREEN_HEIGHT:   # so that it doesnt go past the bottom of the game window
            self.rect.bottom = SCREEN_HEIGHT

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, self.rect)


# Class 2: AI Paddle (Inheritance)

class AIPaddle(Paddle):
    def update(self, ball, ball2):
        paddle_center = self.rect.centery  # to keep the computer paddle's y coordinate the same as the controlled paddle in the middle
        
        if ball.rect.centery < paddle_center - 10:    #ball tracking where center of paddle compared to ball center
            self.move(-1)
        elif ball.rect.centery > paddle_center + 10:
            self.move(1)

# Class 3: Ball

class Ball:
    def __init__(self):
        self.rect = pygame.Rect(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, BALL_SIZE, BALL_SIZE) #to define position and size of ball
        self.reset()

    def reset(self):
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2) # center of screen

        self.velocity_x = random.choice([-1, 1]) * BALL_SPEED  #velocity in terms of pixel speed and random initial velocity in x direction
        self.velocity_y = random.choice([-1, 1]) * random.randint(3, BALL_SPEED) #random initial velocity in y direction in the range of 3 and the speed of the ball

    def update(self, player, ai, game_engine):  # changes position according to the velocity
        self.rect.x += self.velocity_x  
        self.rect.y += self.velocity_y

        # Wall collisions
        if self.rect.top <= 0 or self.rect.bottom >= SCREEN_HEIGHT:  # reverses velocity in y direction if it touches top or bottom of the main game window
            self.velocity_y *= -1
            # NEW: Spawn wall impact particles
            game_engine.spawn_particles(self.rect.centerx, self.rect.centery) #particle effects at collision point

        # Paddle collisions
        if self.rect.colliderect(player.rect) and self.velocity_x < 0: # when paddle overlaps the ball the x velocity of the ball reverses
            self.velocity_x *= -1
            self.rect.left = player.rect.right #coded so that ball and paddle dont get stuck together as they could get trapped due to pixel movement

            # Adding some angle deflections
            angle = (self.rect.centery - player.rect.centery) / (PADDLE_HEIGHT / 2) #calculation made in a way if it ball and paddle centers collide, ball bounces back horizontally with no vertical change in direction
            self.velocity_y = int(angle * BALL_SPEED)
            # NEW: Spawn player paddle hit particles
            game_engine.spawn_particles(self.rect.left, self.rect.centery)

        if self.rect.colliderect(ai.rect) and self.velocity_x > 0: # if x of ball close to computer paddle, and the ball overlaps with paddle
            self.velocity_x *= -1
            self.rect.right = ai.rect.left # so that the paddle and ball dont get stuck

            angle = (self.rect.centery - ai.rect.centery) / (PADDLE_HEIGHT / 2)
            self.velocity_y = int(angle * BALL_SPEED)
            # NEW: Spawn AI paddle hit particles
            game_engine.spawn_particles(self.rect.right, self.rect.centery)

        # Scoring
        if self.rect.left <= 0:  # purpose is to check if the ball passes behind the respective paddles to give points 
            return "ai"

        if self.rect.right >= SCREEN_WIDTH:
            return "player"

        return None

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, self.rect) #white rectangle ball

#Class 4: TrailEffect

class TrailEffect:
    def __init__(self, x, y):
        # Simply records a position point and fades down with each frame
        self.x = x #floating points of the particle
        self.y = y
        self.size = BALL_SIZE // 2  #size of the 'particle'
        self.lifetime = 10  # pixel frames until it disappears 

    def update(self):
        # Fade and age the trail effect
        self.size = max(0, self.size - 0.5) #decreases size 0.5 pixels each frame 
        self.lifetime -= 1 #reduces per 1 frame

    def draw(self, screen):
        # Simple brightness calculation based on remaining frames
        fade_color = int(255 * (self.lifetime / 10)) #starts with 255 as first trail colour is white
        color = (fade_color, fade_color, fade_color) #same values for all RGB values
        if self.size > 0:
            pygame.draw.circle(screen, color, (int(self.x), int(self.y)), int(self.size)) #(surface, colour, center, radius)

# Class 5: Main Game Class

class AirHockey:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT)) #display surface returned
        pygame.display.set_caption("Air Hockey")
        self.clock = pygame.time.Clock() #helps to mainatain or control the frame rates
        self.font = pygame.font.SysFont(None, 48)
        self.small_font = pygame.font.SysFont(None, 32)
        self.reset_game()

    def reset_game(self):  #main reset settings when a game is over
        self.player = Paddle(30, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2)
        self.ai = AIPaddle(SCREEN_WIDTH - 30 - PADDLE_WIDTH, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, AI_SPEED)
        self.ball = Ball()
        self.ball2 = Ball()
        self.particles, self.player_score, self.ai_score = [], 0, 0
        self.game_over, self.winner = False, ""

    def spawn_particles(self, x, y, count=12):
        self.particles.extend(TrailEffect(x, y) for _ in range(count))

    def update(self): #basic key controls so that you can move your paddle up or down
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]: self.player.move(-1)
        if keys[pygame.K_s]: self.player.move(1)

        self.ai.update(self.ball, self.ball2) #updates the computer position with the ball position
        for p in self.particles[:]:
            p.update()
            if p.lifetime <= 0: self.particles.remove(p) #once particle finish their 10 frames, theyre removed 

        result1 = self.ball.update(self.player, self.ai, self) #updates ball state
        if result1:
            scoring_side = 1 if result1 == "player" else 0 #adds points in 1 increments as player scores one past the AIpaddle
            if scoring_side: self.player_score += 1
            else: self.ai_score += 1
            self.spawn_particles(SCREEN_WIDTH - 10 if scoring_side else 10, self.ball.rect.centery, 35)
            self.ball.reset() #resets ball to center after each round is over

        result2 = self.ball2.update(self.player, self.ai, self) #updates ball state
        if result2:
                 scoring_side = 1 if result2 == "player" else 0 #adds points in 1 increments as player scores one past the AIpaddle
                 if scoring_side: self.player_score += 1
                 else: self.ai_score += 1
                 self.spawn_particles(SCREEN_WIDTH - 10 if scoring_side else 10, self.ball.rect.centery, 35)
                 self.ball2.reset() #resets ball to center after each round is over

        if self.player_score >= WINNING_SCORE or self.ai_score >= WINNING_SCORE: #whoever reaches the total score first wins
            self.game_over = True
            self.winner = "You Win!" if self.player_score >= WINNING_SCORE else "Computer Wins!"

    def draw(self):
        self.screen.fill(BLACK) #background is fully kept black
        for y in range(0, SCREEN_HEIGHT, 30): #after research, the range function has 3 attributes
            pygame.draw.rect(self.screen, GRAY, (SCREEN_WIDTH // 2 - 2, y, 4, 20)) #middle line kept in center, y is the top edge of the line, each dash is 4 pixels wide and 20 pixels long. as each step is 30 pixels, it creates a 10 pixel gap between each.

        for entity in (self.player, self.ai, *self.particles, self.ball, self.ball2):
            entity.draw(self.screen) #so that all these objects exist together at the same as played

        p_txt = self.font.render(str(self.player_score), True, WHITE) # font render converts string into something htat can be drawn on the pygame surface. set of code to create text on the pygame window
        ai_txt = self.font.render(str(self.ai_score), True, WHITE)
        self.screen.blit(p_txt, (SCREEN_WIDTH // 4, 30)) #pixels are being converted from the text to main screen surface at a position from the source which are the 2 attributes.
        self.screen.blit(ai_txt, (SCREEN_WIDTH * 3 // 4, 30)) # block image transfer

        if self.game_over:
            w_txt = self.font.render(self.winner, True, WHITE)
            r_txt = self.small_font.render("Press R to Restart", True, WHITE)
            self.screen.blit(w_txt, w_txt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))) #Helper method returning a rectangle centered exactly around specific coordinates for easy UI alignment
            self.screen.blit(r_txt, r_txt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20)))

        pygame.display.flip() # updates the entire display

    def run(self):
        while True:
            self.clock.tick(FPS) # keeps game window within this fps
            for event in pygame.event.get(): # get wtvr events that are queued such as any mouse or keyboard action,etc
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit() # set of code for when the player closes teh game window
                if self.game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    self.reset_game() # if the player wants to restart the game and presses r, the game starts again or'resets'

            if not self.game_over:
                self.update()
            self.draw() #continues teh game as normal as the game has not ended yet

if __name__ == "__main__": # runs the whole code 
    game = AirHockey()
    game.run() 