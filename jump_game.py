import pygame
import pygame.freetype
import pygame_textinput
from pygame.sprite import Sprite
from enum import Enum
from random import randrange
import db_configurations as db

# CREATE TABLE IF FIRST TIME RUNNING
conn = db.create_connection(db.db_file)
db.create_table(conn, db.create_table_sql)

# COLORS
BLUE = (17, 50, 87)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# BACKGROUND MUSIC AND SOUND EFFECTS
pygame.mixer.init()
pygame.mixer.music.load('sounds/bg_music_alt.mp3')
pygame.mixer.music.set_volume(0.5)

jump_sound = pygame.mixer.Sound('sounds/jump_sound.mp3')
click_sound = pygame.mixer.Sound('sounds/click_sound.mp3')
game_over_sound = pygame.mixer.Sound('sounds/game_over_sound.mp3')
hit_sound_effect = pygame.mixer.Sound('sounds/hit_sound_effect.mp3')

# FUNCTION USED BY UI ELEMENT Class
def create_surface_with_text(text, font_size, text_rgb, bg_rgb):
    """ Returns surface with text written on """
    font = pygame.freetype.SysFont("courier", font_size, bold=True)
    surface, _ = font.render(text=text, fgcolor=text_rgb, bgcolor=bg_rgb)
    return surface.convert_alpha()

# UI ELEMENT Class
class UIElement(Sprite):
    """ A user interface element that can be added to a surface """

    def __init__(self, center_position, text, font_size, bg_rgb, text_rgb, action=None):
        """
        Args:
            center_position - tuple (x, y)
            text - string of text to write
            font_size - int
            bg_rgb (background colour) - tuple (r, g, b)
            text_rgb (text colour) - tuple (r, g, b)
        """
        self.mouse_over = False  # indicates if the mouse is over the element

        # create the default image
        default_image = create_surface_with_text(
            text=text, font_size=font_size, text_rgb=text_rgb, bg_rgb=bg_rgb
        )

        # create the image that shows when mouse is over the element
        highlighted_image = create_surface_with_text(
            text=text, font_size=font_size * 1.25, text_rgb=text_rgb, bg_rgb=bg_rgb
        )

        # add both images and their rects to lists
        self.images = [default_image, highlighted_image]
        self.rects = [
            default_image.get_rect(center=center_position),
            highlighted_image.get_rect(center=center_position),
        ]

        self.action = action
        # calls the init method of the parent sprite class
        super().__init__()

    # properties that vary the image and its rect when the mouse is over the element
    @property
    def image(self):
        return self.images[1] if self.mouse_over else self.images[0]

    @property
    def rect(self):
        return self.rects[1] if self.mouse_over else self.rects[0]

    def update(self, mouse_pos, mouse_up):
        """ Updates the element's appearance depending on the mouse position
            and returns the button's action if clicked
        """
        if self.rect.collidepoint(mouse_pos):
            self.mouse_over = True
            if mouse_up:
                return self.action
        else:
            self.mouse_over = False

    def draw(self, surface):
        """ Draws element onto a surface """
        surface.blit(self.image, self.rect)

# GAME Class
class Game():
    # GAME CONSTANTS
    FLOOR = 400
    GRAVITY = 0.4
    SCREEN_RESOLUTION = (750, 500)
    FPS = 60
    CLOCK = pygame.time.Clock()
    SCREEN = pygame.display.set_mode(SCREEN_RESOLUTION)

    # GAME VARIABLES
    game_speed = 3
    game_music = True
    game_sounds = True
    game_diff_hard = False
    game_control_arrow_keys = False
    mob_list = []
    player_type = 1
    pause = False

    def __init__(self, player):
        self.player = player
        self.running = True

        self.move_left = False
        self.move_right = False
        self.points = 0
        self.level = 1
        self.floor_pos = 0

        self.BLACK = (0, 0, 0)

        self.font = pygame.font.SysFont('courier', 20)
        self.background = 1

    def score(self):
        """ Increase score """
        if Game.game_diff_hard:
            self.points += 2
        else:
            self.points += 1

        if self.points % 750 == 0:
            self.level += 1
            self.background += 1
            if Game.game_diff_hard:
                Game.game_speed += 2.5
            else:
                Game.game_speed += 2

        if self.level > 7 and self.background > 7:
            self.background = 1

        level_text = self.font.render("Level: " + str(self.level), True, (0, 0, 0))
        level_text_rect = level_text.get_rect()
        level_text_rect.center = (450, 40)
        text = self.font.render("Points: " + str(self.points), True, (0, 0, 0))
        text_rect = text.get_rect()
        text_rect.center = (600, 40)
        Game.SCREEN.blit(level_text, level_text_rect)
        Game.SCREEN.blit(text, text_rect)

    def reset(self):
        """ Resets the game"""
        Game.mob_list = []
        self.level = 1
        if Game.game_diff_hard:
            Game.game_speed = 8
        else:
            Game.game_speed = 3

    def draw_background(self):
        """ Displays background """
        self.bg_surface = pygame.image.load(f'img/bg/{self.background}.png')
        self.floor_surface = pygame.image.load('img/floor.png')

        Game.SCREEN.fill(BLACK)
        Game.SCREEN.blit(self.bg_surface, (0, 0))
        Game.SCREEN.blit(self.floor_surface, (self.floor_pos, 400))
        Game.SCREEN.blit(self.floor_surface, (self.floor_pos + 500, 400))

    def game_loop(self):
        """ Heart of the game - the game loop """
        while self.running:
            Game.CLOCK.tick(Game.FPS)

            self.floor_pos -= Game.game_speed
            self.draw_background()

            if self.floor_pos <= -500:
                self.floor_pos = 0

            self.player.draw()
            self.player.move(self.move_left, self.move_right)

            mob_type = randrange(1, 8)
            if len(Game.mob_list) == 0:
                monster_img = pygame.image.load(f'img/enemy/{mob_type}.png')
                Game.mob_list.append(Mob(monster_img, mob_type))

            # COLLISION
            for mob in Game.mob_list:
                mob.draw(Game.SCREEN)
                mob.update()
                if self.player.rect.colliderect(mob.rect):
                    if Game.game_sounds:
                        hit_sound_effect.play()
                        
                    pygame.time.delay(2000)
                    self.running = False
                    level = self.level
                    self.reset()
                    return [level, self.points]

            self.score()

            for event in pygame.event.get():
                if not Game.game_control_arrow_keys:
                    # KEYBOARD INPUT (WASD Keys)
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_a:
                            self.move_left = True
                        if event.key == pygame.K_d:
                            self.move_right = True
                        if event.key == pygame.K_w:
                            self.player.move_up = True
                            if Game.game_sounds:
                                jump_sound.play()
                        if event.key == pygame.K_s:
                            self.player.move_down = True
                        if event.key == pygame.K_ESCAPE:
                            Game.pause = True
                            game_state = pause_screen(Game.SCREEN)

                            if game_state == GameState.TITLE:
                                self.reset()
                                return

                    # KEYBOARD INPUT RELEASE
                    if event.type == pygame.KEYUP:
                        if event.key == pygame.K_a:
                            self.move_left = False
                        if event.key == pygame.K_d:
                            self.move_right = False
                        if event.key == pygame.K_s:
                            self.player.move_down = False
                else:
                    # KEYBOARD INPUT (Arrow Keys)
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_LEFT:
                            self.move_left = True
                        if event.key == pygame.K_RIGHT:
                            self.move_right = True
                        if event.key == pygame.K_UP:
                            self.player.move_up = True
                            if Game.game_sounds:
                                jump_sound.play()
                        if event.key == pygame.K_DOWN:
                            self.player.move_down = True
                        if event.key == pygame.K_ESCAPE:
                            Game.pause = True
                            game_state = pause_screen(Game.SCREEN)

                            if game_state == GameState.TITLE:
                                self.reset()
                                return

                    # KEYBOARD INPUT RELEASE
                    if event.type == pygame.KEYUP:
                        if event.key == pygame.K_LEFT:
                            self.move_left = False
                        if event.key == pygame.K_RIGHT:
                            self.move_right = False
                        if event.key == pygame.K_DOWN:
                            self.player.move_down = False

            pygame.display.update()

        pygame.quit()

# PLAYER Class
class Player(pygame.sprite.Sprite):
    def __init__(self, char_type):
        pygame.sprite.Sprite.__init__(self)
        self.char_type = char_type
        self.speed = 10

        self.move_up = False
        self.vel_y = 0
        self.jumping = True

        self.move_down = False

        self.direction = 1
        self.flip = False

        self.img = pygame.image.load(f'img/player/{self.char_type}.png')
        self.rect = self.img.get_rect()
        self.rect.center = (75, Game.FLOOR)
    
    # MOVEMENTS
    def move(self, moving_left, moving_right):
        # CHANGE IN X AND Y
        dx = 0
        dy = 0

        # MOVE LEFT AND RIGHT
        if moving_left and self.rect.x > 0:
            dx = -self.speed
            self.flip = True
            self.direction = -1
        if moving_right and self.rect.x <= 718:
            dx = self.speed
            self.flip = False
            self.direction = 1
        # MOVING DOWN
        if self.move_down:
            dy = self.speed

        # JUMP MOVEMENT
        if self.move_up == True and self.jumping == False:
            self.vel_y = -11
            self.move_up = False
            self.jumping = True
        
        # GRAVITY
        self.vel_y += Game.GRAVITY
        if self.vel_y > 10:
            self.vel_y
        dy += self.vel_y

        # CHECK FLOOR COLLISION
        if self.rect.bottom + dy > Game.FLOOR:
            dy = Game.FLOOR - self.rect.bottom
            self.jumping = False

        # UPDATE RECTANGLE POSITION
        self.rect.x += dx
        self.rect.y += dy
    
    # DRAW UNIT ON SCREEN
    def draw(self):
        Game.SCREEN.blit(pygame.transform.flip(self.img, self.flip, False), self.rect)

# MOB Class
class Mob():
    def __init__(self, image, type):
        self.image = image
        self.rect = self.image.get_rect()
        self.type = type

        self.rect.x = Game.SCREEN_RESOLUTION[0]

        rand_height = randrange(150, 200)

        if self.type in [6, 7]:
            self.rect.y = self.image.get_size()[1] + rand_height
        else:
            self.rect.y = Game.FLOOR - self.image.get_size()[1]
         
    def update(self):
        self.rect.x -= Game.game_speed
        if self.rect.x <= -self.rect.width:
            Game.mob_list.pop()

    def draw(self, screen):
        screen.blit(self.image, self.rect)

# GAME STATES Class
class GameState(Enum):
    CONFIRM_QUIT = -2
    QUIT = -1
    TITLE = 0
    NEWGAME = 1
    OPTIONS = 2
    VIEWSCORES = 3
    PREV = 4
    NEXT = 5
    MUSIC = 6
    SOUND = 7
    DIFF = 8
    CONTROLS = 9
    ABOUT = 10

""" GAME SCREEN-RELATED FUNCTIONS """

# TITLE SCREEN
def title_screen(screen):
    music_ongoing = pygame.mixer.music.get_busy()

    if music_ongoing == False and Game.game_music == True:
        pygame.mixer.music.play(-1)
    
    logo = pygame.image.load('img/logo.png')
    logo_rect = logo.get_rect()
    center_x = Game.SCREEN_RESOLUTION[0]/2
    center_y = Game.SCREEN_RESOLUTION[1]/2

    logo_rect.center = (center_x, center_y - 30)

    prev_char_btn = UIElement(
        center_position=(200, 100),
        font_size=40,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="<",
        action=GameState.PREV,
    )
    next_char_btn = UIElement(
        center_position=(550, 100),
        font_size=40,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text=">",
        action=GameState.NEXT,
    )
    start_btn = UIElement(
        center_position=(375, 300),
        font_size=25,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="Start",
        action=GameState.NEWGAME,
    )
    optn_btn = UIElement(
        center_position=(375, 337.5),
        font_size=25,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="Options",
        action=GameState.OPTIONS,
    )
    view_btn = UIElement(
        center_position=(375, 375),
        font_size=25,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="View High Scores",
        action=GameState.VIEWSCORES,
    )
    about_btn = UIElement(
        center_position=(375, 412.5),
        font_size=25,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="About us",
        action=GameState.ABOUT,
    )
    quit_btn = UIElement(
        center_position=(375, 450),
        font_size=25,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="Quit",
        action=GameState.CONFIRM_QUIT,
    )

    buttons = [prev_char_btn, next_char_btn, start_btn, optn_btn, view_btn, about_btn, quit_btn]

    player_icon = pygame.image.load(f'img/player_icons/{Game.player_type}.png')
    player_icon_rect = player_icon.get_rect()
    player_icon_rect.center = (center_x, 100)

    while True:
        mouse_up = False
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mouse_up = True

        screen.fill(BLUE)
        screen.blit(logo, logo_rect)

        for button in buttons:
            ui_action = button.update(pygame.mouse.get_pos(), mouse_up)
            if ui_action is not None:
                if Game.game_sounds:
                    click_sound.play()

                return ui_action
            button.draw(screen)

        Game.SCREEN.blit(player_icon, player_icon_rect)
        pygame.display.flip()

# PLAY SCREEN
def play_game(screen):
    return_btn = UIElement(
        center_position=(150, 450),
        font_size=20,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="Return to main menu",
        action=GameState.TITLE,
    )

    # GAME INSTANCE
    player = Player(Game.player_type)
    game = Game(player)

    # RUN GAME LOOP AND GET STATISTICS
    stats = game.game_loop()

    # GAME OVER SECTION
    if stats is not None:
        if Game.game_music:
            pygame.mixer.music.stop()
        if Game.game_sounds:
            game_over_sound.play()
        
        # INPUT PLAYER NAME
        text_input = pygame_textinput.TextInput()
        
        saved = False
        while True:
            mouse_up = False
            events = pygame.event.get()

            for event in events:
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    mouse_up = True

            screen.fill(BLUE)

            # ENTERING THE PLAYER NAME
            if text_input.update(events):
                player_name = text_input.get_text()
                if player_name == "":
                    player_name = "Anonymous"

                # SAVE TO DATABASE
                record = (player_name, stats[0], stats[1])
                db.insert_score(conn, record)
                saved = True
                

            display_end_game_result(stats, screen, saved)

            screen.blit(text_input.get_surface(), (300, 143))
            
            pygame.draw.rect(screen, WHITE, pygame.Rect(200, 130, 350, 50), 2)

            ui_action = return_btn.update(pygame.mouse.get_pos(), mouse_up)
            if ui_action is not None:
                if Game.game_sounds:
                    click_sound.play()

                return ui_action
            return_btn.draw(screen)

            pygame.display.flip()
    else:
        return GameState.TITLE

# PAUSE SCREEN
def pause_screen(screen):
    large_font = pygame.font.SysFont("courier", 80)
    small_font = pygame.font.SysFont("courier", 15)

    center_x = Game.SCREEN_RESOLUTION[0]/2
    center_y = Game.SCREEN_RESOLUTION[1]/2

    pause_text = large_font.render("Paused", True, WHITE)
    pause_text_rect = pause_text.get_rect()
    pause_text_rect.center = (center_x, center_y)

    tip_text = small_font.render("Press ESC again to Continue", True, WHITE)
    tip_text_rect = tip_text.get_rect()
    tip_text_rect.center = (center_x, center_y + 50)

    return_btn = UIElement(
        center_position=(150, 450),
        font_size=20,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="Return to main menu",
        action=GameState.TITLE,
    )

    while Game.pause:
        mouse_up = False
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mouse_up = True

            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    Game.pause = False
                    return      
                    
        screen.fill(BLUE)  
        screen.blit(pause_text, pause_text_rect)
        screen.blit(tip_text, tip_text_rect)

        ui_action = return_btn.update(pygame.mouse.get_pos(), mouse_up)
        if ui_action is not None:
            if Game.game_sounds:
                click_sound.play()

            return ui_action
        return_btn.draw(screen)

        pygame.display.update()
        pygame.display.flip()

# VIEW OPTIONS SCREEN
def options_screen(screen, music_toggle, sounds_toggle, diff_toggle, controls_toggle):
    font = pygame.font.SysFont('courier', 30)
    
    options_text = font.render("Options", True, WHITE)
    options_text_rect = options_text.get_rect()
    options_text_rect.center = (Game.SCREEN_RESOLUTION[0]/2, 50)

    music = "Music: ON"
    sounds = "Sounds: ON"
    diff = "Difficulty: EASY"
    controls = "Controls: WASD keys"

    if music_toggle:
        music = "Music: ON"
    else:
        music = "Music: OFF"

    if sounds_toggle:
        sounds = "Sounds: ON"
    else:
        sounds = "Sounds: OFF"
    
    if diff_toggle:
        diff = "Difficulty: HARD"
    else:
        diff = "Difficulty: EASY"

    if controls_toggle:
        controls = "Controls: ARROW keys"
    else:
        controls = "Controls: WASD keys"

    return_btn = UIElement(
        center_position=(150, 450),
        font_size=20,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="Return to main menu",
        action=GameState.TITLE,
    )
    sounds_btn = UIElement(
        center_position=(380, 150),
        font_size=20,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text=sounds,
        action=GameState.SOUND,
    )
    music_btn = UIElement(
        center_position=(380, 200),
        font_size=20,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text=music,
        action=GameState.MUSIC,
    )
    diff_btn = UIElement(
        center_position=(380, 250),
        font_size=20,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text=diff,
        action=GameState.DIFF,
    )
    controls_btn = UIElement(
        center_position=(380, 300),
        font_size=20,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text=controls,
        action=GameState.CONTROLS,
    )

    buttons = [sounds_btn, music_btn, diff_btn, controls_btn, return_btn]

    while True:
        mouse_up = False
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mouse_up = True

        screen.fill(BLUE)
        screen.blit(options_text, options_text_rect)

        for button in buttons:
            ui_action = button.update(pygame.mouse.get_pos(), mouse_up)
            if ui_action is not None:
                if Game.game_sounds:
                    click_sound.play()

                return ui_action
            button.draw(screen)

        pygame.display.flip()

# VIEW HIGH SCORE SCREEN
def view_high_score_screen(screen):
    small_font = pygame.font.SysFont('courier', 15)
    semi_small_font = pygame.font.SysFont('courier', 20)
    medium_font = pygame.font.SysFont('courier', 30)

    center = Game.SCREEN_RESOLUTION[0]/2

    view_scores_text = medium_font.render("Top 10 High Scores", True, WHITE)
    view_scores_text_rect = view_scores_text.get_rect()
    view_scores_text_rect.center = (center, 50)

    records = db.query_scores(conn)
    records_length = len(records)

    # (Surface, Rect)
    names = []
    levels = []
    scores = []

    distance = 170
    
    # PLAYER NAME
    player_name_label = semi_small_font.render("Player", True, WHITE)
    player_name_label_rect = player_name_label.get_rect()
    player_name_label_rect.center = (center - 200, 125)

    # LEVEL
    level_label = semi_small_font.render("Level", True, WHITE)
    level_label_rect = level_label.get_rect()
    level_label_rect.center = (center, 125)

    # SCORE
    score_label = semi_small_font.render("Score", True, WHITE)
    score_label_rect = score_label.get_rect()
    score_label_rect.center = (center + 200, 125)

    # CROWNS
    crown_1 = pygame.image.load('img/crown.png')
    crown_1_rect = crown_1.get_rect()
    crown_1_rect.center = (50, distance)

    crown_2 = pygame.image.load('img/crown_2.png')
    crown_2_rect = crown_2.get_rect()
    crown_2_rect.center = (50, distance + 25)

    crown_3 = pygame.image.load('img/crown_3.png')
    crown_3_rect = crown_3.get_rect()
    crown_3_rect.center = (50, distance + 50)

    for record in records:
        # PLAYER NAME SURFACES AND RECT
        player_name = small_font.render(record[0], True, WHITE)
        player_name_rect = player_name.get_rect()
        player_name_rect.center = (center - 200, distance)
        
        # LEVEELS SURFACES AND RECT
        level = small_font.render(str(record[1]), True, WHITE)
        level_rect = level.get_rect()
        level_rect.center = (center, distance)

        # SCORE SURFACES AND RECT
        score = small_font.render(str(record[2]), True, WHITE)
        score_rect = score.get_rect()
        score_rect.center = (center + 200, distance)

        distance += 25

        names.append((player_name, player_name_rect))
        levels.append((level, level_rect))
        scores.append((score, score_rect))
    
    return_btn = UIElement(
        center_position=(150, 450),
        font_size=20,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="Return to main menu",
        action=GameState.TITLE,
    )

    while True:
        mouse_up = False
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mouse_up = True

        screen.fill(BLUE)
        screen.blit(view_scores_text, view_scores_text_rect)
        
        screen.blit(player_name_label, player_name_label_rect)
        screen.blit(level_label, level_label_rect)
        screen.blit(score_label, score_label_rect)

        if records_length >= 1:
            screen.blit(crown_1, crown_1_rect)
        if records_length >= 2:
            screen.blit(crown_2, crown_2_rect)
        if records_length >= 3:
            screen.blit(crown_3, crown_3_rect)

        # DISPLAY TOP 5 SCORES
        for i in range(records_length):
            screen.blit(names[i][0], names[i][1])
            screen.blit(levels[i][0], levels[i][1])
            screen.blit(scores[i][0], scores[i][1])

        ui_action = return_btn.update(pygame.mouse.get_pos(), mouse_up)
        if ui_action is not None:
            if Game.game_sounds:
                click_sound.play()

            return ui_action
        return_btn.draw(screen)

        pygame.display.flip()

# TOGGLE MUSIC
def toggle_music(game_music):
    if not game_music:
        pygame.mixer.music.pause()
    else:
        pygame.mixer.music.unpause()

# WINDOW PROPERTIES
def set_window_properties():
    pygame.display.set_caption("Dodge me Not")
    icon = pygame.image.load('img/player/1.png')
    pygame.display.set_icon(icon)

# SHOW FINAL GAME RESULTS
def display_end_game_result(stats, screen, saved):
    score_font = pygame.font.SysFont('courier', 30)
    user_text_font = pygame.font.SysFont('courier', 15)
    save_text_font = pygame.font.SysFont('courier', 20)

    game_over_text = score_font.render("GAME OVER", True, WHITE)
    game_over_text_rect = game_over_text.get_rect()
    game_over_text_rect.center = (380, 50)

    user_text = user_text_font.render("Type your name and press Enter to Save", True, WHITE)
    user_text_rect = user_text.get_rect()
    user_text_rect.center = (380, 100)
    
    player_level = score_font.render("Level: " + str(stats[0]), True, WHITE)
    player_level_rect = player_level.get_rect()
    player_level_rect.center = (380, 250)

    player_score = score_font.render("Score: " + str(stats[1]), True, WHITE)
    player_score_rect = player_score.get_rect()
    player_score_rect.center = (380, 290)
    
    saved_text = save_text_font.render("Saved", True, WHITE)
    saved_text_rect = saved_text.get_rect()
    saved_text_rect.center = (380, 350)

    if saved:
        screen.blit(saved_text, saved_text_rect)

    screen.blit(game_over_text, game_over_text_rect)
    screen.blit(user_text, user_text_rect)
    screen.blit(player_level, player_level_rect)
    screen.blit(player_score, player_score_rect)

# CONFIRM EXIT SCREEN
def confirm_quit_screen(screen):
    font = pygame.font.SysFont('courier', 50)
    center_x = Game.SCREEN_RESOLUTION[0]/2

    exit_text = font.render("Confirm Exit?", True, WHITE)
    exit_text_rect = exit_text.get_rect()
    exit_text_rect.center = (center_x, 200)

    yes_btn = UIElement(
        center_position=(center_x - 100, 300),
        font_size=30,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="Yes",
        action=GameState.QUIT,
    )

    no_btn = UIElement(
        center_position=(center_x + 100, 300),
        font_size=30,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="No",
        action=GameState.TITLE,
    )

    buttons = [yes_btn, no_btn]

    while True:
        mouse_up = False
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mouse_up = True

        screen.fill(BLUE)
        screen.blit(exit_text, exit_text_rect)

        for button in buttons:
            ui_action = button.update(pygame.mouse.get_pos(), mouse_up)
            if ui_action is not None:
                if Game.game_sounds:
                    click_sound.play()

                return ui_action
            button.draw(screen)

        pygame.display.flip()

# CREDITS
def about_screen(screen):
    small_font = pygame.font.SysFont('courier', 20)
    smaller_font = pygame.font.SysFont('courier', 15)
    medium_font = pygame.font.SysFont('courier', 30)
    center_x = Game.SCREEN_RESOLUTION[0]/2

    about_text = medium_font.render("About us", True, WHITE)
    about_text_rect = about_text.get_rect()
    about_text_rect.center = (center_x, 50)

    sentence_1_text = small_font.render("This game is developed by", True, WHITE)
    sentence_1_text_rect = sentence_1_text.get_rect()
    sentence_1_text_rect.center = (center_x, 130)

    group_logo = pygame.image.load("img/group_logo.png")
    group_logo_rect = group_logo.get_rect()
    group_logo_rect.center = (center_x, 230)

    sentence_2_text = smaller_font.render("Game icons generated in: https://www.flaticon.com", True, WHITE)
    sentence_2_text_rect = sentence_2_text.get_rect()
    sentence_2_text_rect.center = (center_x, 340)

    sentence_3_text = smaller_font.render("Game music credits: 8 Bit Universe (YouTube)", True, WHITE)
    sentence_3_text_rect = sentence_3_text.get_rect()
    sentence_3_text_rect.center = (center_x, 370)

    sentence_4_text = smaller_font.render("Background image credits: https://www.pinterest.com (Pinterest)", True, WHITE)
    sentence_4_text_rect = sentence_4_text.get_rect()
    sentence_4_text_rect.center = (center_x, 400)

    return_btn = UIElement(
        center_position=(150, 450),
        font_size=20,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="Return to main menu",
        action=GameState.TITLE,
    )

    while True:
        mouse_up = False
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mouse_up = True

        screen.fill(BLUE)
        screen.blit(about_text, about_text_rect)
        screen.blit(sentence_1_text, sentence_1_text_rect)
        screen.blit(group_logo, group_logo_rect)
        screen.blit(sentence_2_text, sentence_2_text_rect)
        screen.blit(sentence_3_text, sentence_3_text_rect)
        screen.blit(sentence_4_text, sentence_4_text_rect)
        
        ui_action = return_btn.update(pygame.mouse.get_pos(), mouse_up)
        if ui_action is not None:
            if Game.game_sounds:
                click_sound.play()

            return ui_action
        return_btn.draw(screen)

        pygame.display.flip()

""" MAIN DRIVER """
def main():
    pygame.init()

    set_window_properties()

    # INITIAL GAME STATE
    game_state = GameState.TITLE

    # MAIN LOOP
    running = True
    while running:
        if game_state == GameState.TITLE:
            game_state = title_screen(Game.SCREEN)

        if game_state == GameState.NEWGAME:
            game_state = play_game(Game.SCREEN)

        if game_state == GameState.OPTIONS:
            game_state = options_screen(Game.SCREEN, Game.game_music, Game.game_sounds, 
                                        Game.game_diff_hard, Game.game_control_arrow_keys)

        if game_state == GameState.VIEWSCORES:
            game_state = view_high_score_screen(Game.SCREEN)

        if game_state == GameState.ABOUT:
            game_state = about_screen(Game.SCREEN)

        if game_state == GameState.PREV:
            if Game.player_type == 1:
                Game.player_type = 5
                game_state = GameState.TITLE
            else:
                Game.player_type -= 1
                game_state = GameState.TITLE

        if game_state == GameState.NEXT:
            if Game.player_type == 5:
                Game.player_type = 1
                game_state = GameState.TITLE
            else:
                Game.player_type += 1
                game_state = GameState.TITLE

        if game_state == GameState.SOUND:
            Game.game_sounds = not Game.game_sounds
            game_state = GameState.OPTIONS

        if game_state == GameState.MUSIC:
            toggle_music(not Game.game_music)
            Game.game_music = not Game.game_music
            game_state = GameState.OPTIONS
        
        if game_state == GameState.DIFF:
            Game.game_diff_hard = not Game.game_diff_hard
            if Game.game_diff_hard:
                Game.game_speed = 8
            else:
                Game.game_speed = 3
            game_state = GameState.OPTIONS

        if game_state == GameState.CONTROLS:
            Game.game_control_arrow_keys = not Game.game_control_arrow_keys
            game_state = GameState.OPTIONS

        if game_state == GameState.CONFIRM_QUIT:
            game_state = confirm_quit_screen(Game.SCREEN)

        if game_state == GameState.QUIT:
            pygame.quit()
            return

# CALL MAIN WHEN SCRIPT IS RUNNING
if __name__ == "__main__":
    main()