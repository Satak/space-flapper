import pygame
import random
import sys
import math
from enum import Enum, auto

# Constants
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
GRAVITY = 0.25
FLAP_STRENGTH = -7
PIPE_SPEED = 3
PIPE_GAP = 200
PIPE_FREQUENCY = 1500  # milliseconds
INITIAL_GAP_SIZE = 220  # Initial gap between pipes
MIN_GAP_SIZE = 100     # Minimum gap size
GAP_DECREASE_RATE = 20  # How much to decrease gap per level
PIPE_WIDTH = 50

# Game States
MENU = 0
PLAYING = 1
GAME_OVER = 2

# Weapon Types
class WeaponType(Enum):
    DEFAULT = auto()
    SPREAD = auto()
    LASER = auto()
    CHARGE = auto()
    SHIELD = auto()
    NUKE = auto()  # Add NUKE type

# Power-up Types
class PowerUpType(Enum):
    SHIELD = auto()
    SPREAD = auto()
    LASER = auto()
    CHARGE = auto()
    NUKE = auto()  # Add NUKE type

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
GREY = (128, 128, 128)  # Color for pipes
YELLOW = (255, 255, 0)
DARK_GREEN = (0, 20, 0)
DARK_BLUE = (0, 0, 20)

class Weapon:
    def __init__(self, type=WeaponType.DEFAULT):
        self.type = type
        self.charge_level = 0  # For charge weapon
        self.is_charging = False
        self.last_charge_sound = 0
        self.charge_sound_interval = 100  # Play sound every 100ms while charging
        if type == WeaponType.DEFAULT:
            self.ammo = float('inf')
            self.cooldown = 500
        elif type == WeaponType.SPREAD:
            self.ammo = 30
            self.cooldown = 700
        elif type == WeaponType.LASER:
            self.ammo = 50
            self.cooldown = 100
        elif type == WeaponType.CHARGE:
            self.ammo = 20
            self.cooldown = 800
        elif type == WeaponType.NUKE:
            self.ammo = 3  # Start with 3 nukes
            self.cooldown = 1000  # Longer cooldown for nukes
        self.last_shot_time = 0

    def start_charging(self, current_time):
        if not self.is_charging and self.type == WeaponType.CHARGE:
            self.is_charging = True
            self.charge_level = 0
            self.last_charge_sound = current_time

    def update_charge(self, current_time):
        if self.is_charging and self.type == WeaponType.CHARGE:
            # Increase charge level
            self.charge_level = min(100, self.charge_level + 2)

            # Play charge sound at intervals
            if current_time - self.last_charge_sound >= self.charge_sound_interval:
                charge_sound.play()
                self.last_charge_sound = current_time

    def draw_charge_indicator(self, screen, x, y):
        if self.type == WeaponType.CHARGE and self.is_charging:
            # Draw charge meter background
            meter_width = 100
            meter_height = 10
            meter_x = x - meter_width // 2
            meter_y = y + 20

            # Background
            pygame.draw.rect(screen, (50, 50, 50),
                           (meter_x, meter_y, meter_width, meter_height))

            # Charge level bar
            charge_width = int(meter_width * (self.charge_level / 100))

            # Color changes from yellow to orange as charge increases
            if self.charge_level >= 80:
                color = (255, 165, 0)  # Orange for super charge
            else:
                color = (255, 255, 0)  # Yellow for normal charge

            pygame.draw.rect(screen, color,
                           (meter_x, meter_y, charge_width, meter_height))

            # Draw percentage text
            font = pygame.font.Font(None, 24)
            charge_text = f"{self.charge_level}%"
            text_surface = font.render(charge_text, True, (255, 255, 255))
            text_rect = text_surface.get_rect(midtop=(x, meter_y + meter_height + 5))
            screen.blit(text_surface, text_rect)

            # Draw "SUPER" text when fully charged
            if self.charge_level >= 80:
                super_text = font.render("SUPER!", True, (255, 165, 0))
                super_rect = super_text.get_rect(midtop=(x, meter_y - 20))
                screen.blit(super_text, super_rect)

    def release_charge(self, x, y, current_time):
        """Release charge weapon in Weapon class"""
        if not self.is_charging:
            return [], False

        self.is_charging = False
        if self.charge_level < 20:  # Minimum charge required
            self.charge_level = 0
            return [], False

        if self.ammo > 0 and current_time - self.last_shot_time >= self.cooldown:
            self.last_shot_time = current_time
            bullets = []

            # Super charge creates a circular blast pattern
            if self.charge_level >= 80:
                laser_sound.play()  # Strong charge uses laser sound
                num_bullets = 16  # Number of bullets in the circle
                for i in range(num_bullets):
                    angle = (360 / num_bullets) * i  # Evenly space bullets in a circle
                    bullet = Bullet(x, y, WeaponType.CHARGE, charge_level=self.charge_level, angle=angle)
                    bullets.append(bullet)
            else:
                # Normal charge just shoots forward
                shoot_sound.play()
                bullet = Bullet(x, y, WeaponType.CHARGE, charge_level=self.charge_level)
                bullets.append(bullet)

            self.ammo -= 1
            self.charge_level = 0
            return bullets, self.ammo <= 0

        return [], False

    def shoot(self, x, y, current_time):
        if self.type == WeaponType.CHARGE:
            return [], False  # Charge weapon only shoots on release

        if self.ammo > 0 and current_time - self.last_shot_time >= self.cooldown:
            self.last_shot_time = current_time
            self.ammo -= 1

            if self.type == WeaponType.SPREAD:
                spread_sound.play()
                bullets = []
                angles = [-30, -15, 0, 15, 30]  # 5 bullets at different angles
                for angle in angles:
                    bullets.append(Bullet(x, y, self.type, angle=angle))
                if self.ammo is not None:
                    self.ammo -= 1
                    if self.ammo <= 0:
                        self.type = WeaponType.DEFAULT
                return bullets, self.ammo == 0
            elif self.type == WeaponType.LASER:
                laser_sound.play()
                return [Bullet(x, y, self.type)], self.ammo == 0
            else:  # Default weapon
                shoot_sound.play()
                return [Bullet(x, y, self.type)], self.ammo == 0

        return [], False

class Bullet:
    def __init__(self, x, y, weapon_type, charge_level=0, angle=0, velocity=None):
        self.x = x
        self.y = y
        self.weapon_type = weapon_type
        self.angle = math.radians(angle)

        # Set bullet properties based on weapon type
        if weapon_type == WeaponType.NUKE:
            self.velocity = 3 if velocity is None else velocity
            self.radius = 5
            self.damage = 100
            self.color = (255, 0, 0)
            self.trail_color = (255, 165, 0)
        elif weapon_type == WeaponType.CHARGE:
            self.velocity = 8 if velocity is None else velocity
            self.radius = 10 + int((charge_level / 100) * 10)
            self.damage = 2 + int((charge_level / 100) * 4)
            self.color = (255, 255, 0)  # Yellow
            self.glow_color = (255, 255, 200)  # Light yellow for glow
        elif weapon_type == WeaponType.SPREAD:
            self.velocity = 8 if velocity is None else velocity
            self.radius = 8  # Medium size
            self.damage = 2
            self.color = (255, 0, 255)  # Purple
            self.glow_color = (255, 128, 255)  # Light purple for glow
        elif weapon_type == WeaponType.LASER:
            self.velocity = 12 if velocity is None else velocity  # Faster for laser
            self.width = 20  # Longer rectangle
            self.height = 4  # Thinner rectangle
            self.damage = 1
            self.color = (0, 128, 255)  # Blue
            self.glow_color = (128, 200, 255)  # Light blue for glow
        else:  # DEFAULT
            self.velocity = 10 if velocity is None else velocity
            self.width = 10
            self.height = 5
            self.damage = 1
            self.color = (0, 255, 0)  # Green

    def update(self):
        self.x += self.velocity * math.cos(self.angle)
        self.y += self.velocity * math.sin(self.angle)

    def draw(self, screen):
        if self.weapon_type == WeaponType.NUKE:
            # Draw nuke missile with trail
            pygame.draw.circle(screen, self.color,
                             (int(self.x), int(self.y)), self.radius)
            # Add orange trail
            for i in range(3):
                trail_x = self.x - (i * 5)
                trail_radius = self.radius - (i * 1)
                if trail_radius > 0:
                    pygame.draw.circle(screen, self.trail_color,
                                     (int(trail_x), int(self.y)), trail_radius)
        elif self.weapon_type == WeaponType.CHARGE:
            # Draw charge bullet with glow effect
            # Draw outer glow
            pygame.draw.circle(screen, self.glow_color,
                             (int(self.x), int(self.y)), self.radius + 2)
            # Draw main bullet
            pygame.draw.circle(screen, self.color,
                             (int(self.x), int(self.y)), self.radius)
        elif self.weapon_type == WeaponType.SPREAD:
            # Spread bullet with glow
            pygame.draw.circle(screen, self.glow_color,
                             (int(self.x), int(self.y)), self.radius + 2)
            pygame.draw.circle(screen, self.color,
                             (int(self.x), int(self.y)), self.radius)
        elif self.weapon_type == WeaponType.LASER:
            # Laser bullet with glow effect
            pygame.draw.rect(screen, self.glow_color,
                           (int(self.x), int(self.y - self.height//2 - 1),
                            self.width + 2, self.height + 2))
            pygame.draw.rect(screen, self.color,
                           (int(self.x), int(self.y - self.height//2),
                            self.width, self.height))
        else:  # DEFAULT
            pygame.draw.rect(screen, self.color,
                           (int(self.x), int(self.y), self.width, self.height))

    def is_off_screen(self):
        return self.x > 400 or self.x < 0 or self.y > 600 or self.y < 0

    def get_rect(self):
        """Get bullet's collision rectangle"""
        if self.weapon_type == WeaponType.NUKE:
            return pygame.Rect(self.x - self.radius, self.y - self.radius,
                             self.radius * 2, self.radius * 2)
        elif self.weapon_type == WeaponType.SPREAD:
            radius = 10  # Define spread bullet radius
            return pygame.Rect(self.x - radius, self.y - radius,
                             radius * 2, radius * 2)
        elif self.weapon_type == WeaponType.CHARGE:
            radius = 10  # Define charge bullet radius
            return pygame.Rect(self.x - radius, self.y - radius,
                             radius * 2, radius * 2)
        else:  # DEFAULT and LASER
            return pygame.Rect(self.x, self.y - self.height//2,
                             self.width, self.height)

class Bird:
    def __init__(self):
        self.x = 50
        self.y = SCREEN_HEIGHT // 2
        self.velocity = 0
        self.gravity = 0.5
        self.flap_strength = -8
        self.radius = 15  # Increased from 10 to 15
        self.shields = 3
        self.max_shields = 3
        self.last_hit_time = 0
        self.invincible_duration = 1000  # 1 second of invincibility after hit
        self.weapon = Weapon()
        self.active_nuke = None
        self.explosion = None  # Add this line

        # Invincibility attributes
        self.invincible = False
        self.invincible_start = 0
        self.flash_interval = 100  # Flash every 100ms

        # Eye properties
        self.eye_color = (255, 255, 255)  # White
        self.pupil_color = (0, 0, 0)  # Black
        self.eye_size = 8  # Increased from 6 to 8
        self.pupil_size = 5  # Increased from 4 to 5

        # Ear properties
        self.ear_color = self.get_color()  # Get initial color based on shields
        self.ear_size = 6  # Increased from 4 to 6
        self.ear_spacing = 12  # Increased from 8 to 12

        # Set initial color based on shields
        self.color = self.get_color()

        # Shield box properties
        self.shield_box_size = 8
        self.shield_box_spacing = 4
        self.shield_colors = {
            3: (0, 255, 0),      # Green for 3 shields
            2: (255, 255, 0),    # Yellow for 2 shields
            1: (255, 165, 0)     # Orange for 1 shield (matching player color)
        }

        self.nuke_ammo = 3  # Start with 3 nukes

    def reset(self):
        self.x = 50
        self.y = SCREEN_HEIGHT // 2
        self.velocity = 0
        self.shields = 3
        self.weapon = Weapon()
        self.invincible = False
        self.invincible_start = 0
        self.invincible_duration = 1000  # 1 second of invincibility
        # Reset color when game restarts
        self.color = self.get_color()
        self.ear_color = self.color
        self.active_nuke = None
        self.explosion = None  # Reset explosion

    def flap(self):
        self.velocity = -8  # Negative velocity makes the bird go up

    def update(self, current_time):
        # Apply gravity
        self.velocity += 0.5  # Gravity
        self.y += self.velocity

        # Keep bird on screen
        if self.y < 0:
            self.y = 0
            self.velocity = 0
        elif self.y > SCREEN_HEIGHT - self.radius:
            self.y = SCREEN_HEIGHT - self.radius
            self.velocity = 0

        # Update invincibility
        if self.invincible and current_time - self.invincible_start >= self.invincible_duration:
            self.invincible = False

    def take_hit(self, current_time):
        # If invincible, ignore the hit
        if self.invincible:
            return False

        # Play hit sound
        hit_sound.play()

        # If already at 0 shields, die
        if self.shields <= 0:
            game_over_sound.play()
            ufo_presence_sound.stop()  # Stop UFO sound when player dies
            return True

        # Take damage and become invincible
        self.shields -= 1
        self.invincible = True
        self.invincible_start = current_time

        # Update color based on new shield count
        self.color = self.get_color()
        self.ear_color = self.color

        return False

    def get_color(self):
        """Get the current color based on shield count"""
        if self.shields == 3:
            return (0, 255, 0)      # Green
        elif self.shields == 2:
            return (255, 255, 0)    # Yellow
        elif self.shields == 1:
            return (255, 165, 0)    # Orange
        else:
            return (255, 0, 0)      # Red when no shields

    def update_color(self):
        """Update the bird's color based on shield count"""
        self.color = self.get_color()
        self.ear_color = self.color  # Update ear color to match body

    def draw_shield_boxes(self, screen):
        if self.shields <= 0:
            return

        # Calculate starting position for the first box
        total_width = (self.shield_box_size * self.shields) + (self.shield_box_spacing * (self.shields - 1))
        start_x = self.x - total_width // 2
        box_y = self.y - self.radius - 20  # Position above the bird

        # Draw boxes
        for i in range(self.shields):
            box_x = start_x + (self.shield_box_size + self.shield_box_spacing) * i
            color = self.shield_colors[self.shields]
            pygame.draw.rect(screen, color,
                           (box_x, box_y, self.shield_box_size, self.shield_box_size))
            # Draw white border
            pygame.draw.rect(screen, (255, 255, 255),
                           (box_x, box_y, self.shield_box_size, self.shield_box_size), 1)

    def draw(self, screen, current_time, score):
        should_draw_bird = True
        if self.invincible:
            time_since_hit = current_time - self.invincible_start
            should_draw_bird = (time_since_hit // self.flash_interval) % 2 == 1

        if should_draw_bird:
            # Draw the ears
            left_ear_x = self.x - self.ear_spacing//2
            right_ear_x = self.x + self.ear_spacing//2
            ear_y = self.y - self.radius - self.ear_size//2

            # Draw triangular ears
            for ear_x in [left_ear_x, right_ear_x]:
                points = [
                    (ear_x, ear_y),  # Top point
                    (ear_x - self.ear_size//2, ear_y + self.ear_size),  # Bottom left
                    (ear_x + self.ear_size//2, ear_y + self.ear_size)   # Bottom right
                ]
                pygame.draw.polygon(screen, self.ear_color, points)

            # Draw the body
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

            # Draw the eye
            eye_y = self.y - 2  # Slightly above center for cute look

            # Draw white part of eye
            pygame.draw.circle(screen, self.eye_color, (int(self.x), int(eye_y)), self.eye_size)

            # Draw pupil (black part)
            # Make pupils look slightly towards the bird (left)
            pupil_offset = 2
            pygame.draw.circle(screen, self.pupil_color,
                             (int(self.x + pupil_offset), int(eye_y)), self.pupil_size)

        # Always draw UI elements
        # Draw shield boxes
        self.draw_shield_boxes(screen)
        # Draw weapon charge indicator
        self.weapon.draw_charge_indicator(screen, int(self.x), int(self.y))

        # Draw ammo count if not using default weapon
        if self.weapon.type != WeaponType.DEFAULT:
            font = pygame.font.Font(None, 24)
            ammo_text = f"Ammo: {self.weapon.ammo}"
            ammo_surface = font.render(ammo_text, True, (255, 255, 255))
            screen.blit(ammo_surface, (10, 40))

            # Draw weapon type
            weapon_text = f"Weapon: {self.weapon.type.name}"
            weapon_surface = font.render(weapon_text, True, (255, 255, 255))
            screen.blit(weapon_surface, (10, 70))

        # Draw score
        font = pygame.font.Font(None, 36)
        score_text = f"Score: {score}"
        score_surface = font.render(score_text, True, (255, 255, 255))
        screen.blit(score_surface, (10, 10))

        # Remove the standalone nuke counter since it's now part of the weapon system
        # Only show nuke ammo if we have the nuke weapon
        if self.weapon.type == WeaponType.NUKE:
            nuke_text = font.render(f"Nukes: {self.weapon.ammo}", True, (255, 255, 255))
            screen.blit(nuke_text, (10, 50))

        # Draw active nuke and its trail
        if self.active_nuke:
            self.active_nuke.draw(screen)

        # Draw explosion if active
        if self.explosion:
            self.explosion.draw(screen)
            self.explosion.update()
            if self.explosion.is_finished:
                self.explosion = None

    def shoot(self, current_time):
        if current_time - self.weapon.last_shot_time >= self.weapon.cooldown:
            self.weapon.last_shot_time = current_time
            bullets = []

            if self.weapon.ammo > 0:
                if self.weapon.type == WeaponType.NUKE and not self.active_nuke:
                    nuke = Bullet(self.x + self.radius * 2, self.y, WeaponType.NUKE, velocity=3)
                    self.active_nuke = nuke
                    bullets.append(nuke)
                    return bullets, False
                elif self.weapon.type == WeaponType.DEFAULT:
                    bullets.append(Bullet(self.x, self.y, self.weapon.type))
                    shoot_sound.play()
                elif self.weapon.type == WeaponType.SPREAD:
                    for angle in [-15, 0, 15]:
                        bullets.append(Bullet(self.x, self.y, self.weapon.type, angle=angle))
                    spread_sound.play()
                elif self.weapon.type == WeaponType.LASER:
                    bullets.append(Bullet(self.x, self.y, self.weapon.type))
                    laser_sound.play()

                if self.weapon.type != WeaponType.DEFAULT:
                    self.weapon.ammo -= 1
                    should_reset = self.weapon.ammo <= 0
                    if should_reset:
                        power_up_sound.play()
                    return bullets, should_reset

            return bullets, False
        return [], False

    def start_charging(self, current_time):
        self.weapon.start_charging(current_time)

    def update_charge(self, current_time):
        return self.weapon.update_charge(current_time)

    def release_charge(self, current_time):
        """Release charge weapon in Bird class"""
        if self.weapon.type == WeaponType.CHARGE:
            new_bullets, should_reset = self.weapon.release_charge(self.x, self.y, current_time)
            if should_reset:
                self.weapon = Weapon()  # Reset to default weapon
            return new_bullets, should_reset
        return [], False  # Return empty list and False if not charge weapon

    def get_rect(self):
        """Get bird's collision rectangle, slightly smaller than visual size for better gameplay"""
        collision_radius = self.radius * 0.8  # Make collision box 80% of visual size
        return pygame.Rect(self.x - collision_radius, self.y - collision_radius,
                         collision_radius * 2, collision_radius * 2)

    def launch_nuke(self):
        if not self.active_nuke and self.weapon.ammo > 0:
            nuke = Bullet(self.x + self.radius * 2, self.y, WeaponType.NUKE, velocity=3)
            self.active_nuke = nuke

    def detonate_nuke(self, enemies, bullets, screen, ufos, gates):
        if self.active_nuke and self.active_nuke in bullets:
            # Create explosion animation
            self.explosion = Explosion(self.active_nuke.x, self.active_nuke.y)
            explosion_sound.play()

            # Apply damage to everything in explosion radius
            nuke_pos = (self.active_nuke.x, self.active_nuke.y)
            enemies_killed = 0

            # Kill ALL enemies within the massive blast radius
            for enemy in enemies[:]:
                distance = math.sqrt((enemy.x - nuke_pos[0])**2 +
                                   (enemy.y - nuke_pos[1])**2)
                if distance <= self.explosion.radius:
                    enemies.remove(enemy)
                    enemies_killed += 1
                    enemy_death_sound.play()

            # Destroy UFOs in blast radius
            for ufo in ufos[:]:
                distance = math.sqrt((ufo.x - nuke_pos[0])**2 +
                                   (ufo.y - nuke_pos[1])**2)
                if distance <= self.explosion.radius:
                    ufos.remove(ufo)
                    enemies_killed += 2  # More points for UFO kills
                    ufo_death_sound.play()
                    if len(ufos) == 0:
                        ufo_presence_sound.stop()

            # Destroy gates in blast radius
            for gate in gates[:]:
                if abs(gate.x - nuke_pos[0]) <= self.explosion.radius:
                    if not gate.destroyed:
                        gate.destroyed = True
                        enemies_killed += 1  # Points for destroying gates

            # Remove the nuke
            bullets.remove(self.active_nuke)
            self.active_nuke = None

            # Decrease ammo after successful detonation
            self.weapon.ammo -= 1
            if self.weapon.ammo <= 0:
                return True, enemies_killed
            return False, enemies_killed
        return False, 0

class PowerUp:
    def __init__(self, type, x, y):
        self.type = type
        self.x = x
        self.y = y
        self.size = 20
        self.collected = False
        self.scroll_speed = 2  # Same speed as pipes

        # Set color based on type
        if self.type == PowerUpType.SHIELD:
            self.color = (0, 255, 0)      # Green for shield
        elif self.type == PowerUpType.SPREAD:
            self.color = (255, 0, 255)    # Magenta for spread gun
        elif self.type == PowerUpType.LASER:
            self.color = (0, 255, 255)    # Cyan for fast laser
        elif self.type == PowerUpType.CHARGE:
            self.color = (255, 255, 0)    # Yellow for charge
        elif self.type == PowerUpType.NUKE:
            self.color = (255, 165, 0)    # Orange for nuke

    def update(self):
        # Move with scroll speed like pipes
        if not self.collected:
            self.x -= self.scroll_speed
            return self.x < -self.size  # Return True if powerup is off screen to the left
        return False

    def draw(self, screen):
        if not self.collected:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)
            # Draw a white border
            pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), self.size, 2)

    def get_rect(self):
        """Get powerup's collision rectangle"""
        collision_size = self.size * 0.8  # Make collision box 80% of visual size
        return pygame.Rect(self.x - collision_size, self.y - collision_size,
                         collision_size * 2, collision_size * 2)

    def collect(self, bird):
        power_up_sound.play()
        if self.type == PowerUpType.SHIELD:
            if bird.shields < bird.max_shields:
                bird.shields += 1
                shield_recharge_sound.play()
                bird.update_color()
        else:
            weapon_type = WeaponType[self.type.name]
            bird.weapon = Weapon(weapon_type)

class Enemy:
    def __init__(self):
        self.x = SCREEN_WIDTH
        self.y = random.randint(50, SCREEN_HEIGHT - 50)
        self.speed = random.randint(2, 5)
        self.size = 20
        self.color = (255, 0, 0)  # Red
        self.eye_color = (255, 255, 255)  # White
        self.pupil_color = (0, 0, 0)  # Black
        self.eye_size = 6  # Size of the white part
        self.pupil_size = 4  # Size of the black pupil
        self.eye_spacing = 8  # Distance between eyes

    def update(self):
        self.x -= self.speed

    def draw(self, screen):
        # Draw the main body
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)

        # Draw eyes
        eye_spacing = 8 if self.color == (255, 0, 0) else 4  # Wider spacing for red enemies
        pygame.draw.circle(screen, self.eye_color, (int(self.x - eye_spacing), int(self.y - 2)), self.eye_size)
        pygame.draw.circle(screen, self.eye_color, (int(self.x + eye_spacing), int(self.y - 2)), self.eye_size)

        # Draw pupils (black part)
        # Make pupils look slightly towards the bird (left)
        pupil_offset = 1
        pygame.draw.circle(screen, self.pupil_color,
                         (int(self.x - eye_spacing - pupil_offset), int(self.y - 2)), self.pupil_size)
        pygame.draw.circle(screen, self.pupil_color,
                         (int(self.x + eye_spacing - pupil_offset), int(self.y - 2)), self.pupil_size)

    def get_rect(self):
        """Get enemy's collision rectangle, slightly smaller than visual size"""
        collision_size = self.size * 0.8  # Make collision box 80% of visual size
        return pygame.Rect(self.x - collision_size, self.y - collision_size,
                         collision_size * 2, collision_size * 2)

class Gate:
    def __init__(self):
        self.width = 30
        self.height = 100
        self.x = SCREEN_WIDTH
        self.y = random.randint(self.height, SCREEN_HEIGHT - self.height)
        self.speed = 3
        self.health = 4  # Takes 4 hits to destroy
        self.max_health = 4
        self.destroyed = False
        self.flash_start = 0
        self.flash_duration = 200  # Flash for 200ms when hit

    def hit(self, damage, current_time):
        self.health -= damage
        self.flash_start = current_time
        if self.health <= 0:
            self.destroyed = True
            enemy_death_sound.play()  # Play explosion sound when destroyed
            return True
        hit_sound.play()  # Play hit sound when damaged but not destroyed
        return False

    def update(self):
        self.x -= self.speed

    def draw(self, screen, current_time):
        if not self.destroyed:
            # Calculate color based on health
            health_percentage = self.health / self.max_health
            if current_time - self.flash_start < self.flash_duration:
                # Flash white when hit
                color = WHITE
            else:
                # Color goes from red (low health) to orange (full health)
                red = 255
                green = int(165 * health_percentage)
                color = (red, green, 0)

            # Draw the gate with a metallic effect
            pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
            # Draw health bars
            for i in range(self.health):
                bar_height = 5
                bar_width = 20
                bar_x = self.x + 5
                bar_y = self.y + self.height - (i + 1) * (bar_height + 2) - 5
                pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

class Pipe:
    def __init__(self):
        self.width = PIPE_WIDTH
        self.x = SCREEN_WIDTH
        self.passed = False
        self.gap_size = INITIAL_GAP_SIZE // 2  # Start with initial gap size
        self.gap_y = random.randint(self.gap_size + 50, SCREEN_HEIGHT - self.gap_size - 50)

    def update(self):
        self.x -= PIPE_SPEED

    def draw(self, screen):
        # Draw top pipe
        pygame.draw.rect(screen, GREY,
                        (self.x, 0, self.width, self.gap_y - self.gap_size))
        # Draw bottom pipe
        pygame.draw.rect(screen, GREY,
                        (self.x, self.gap_y + self.gap_size,
                         self.width, SCREEN_HEIGHT - (self.gap_y + self.gap_size)))

class UFO:
    def __init__(self, x=None, y=None):
        self.radius = 20
        self.x = x if x is not None else SCREEN_WIDTH + self.radius
        self.y = y if y is not None else random.randint(50, SCREEN_HEIGHT - 50)
        self.dx = -2  # Initial movement to left to enter screen
        self.dy = 0
        self.health = 3
        self.bullets = []
        self.shoot_timer = 0
        self.shoot_interval = 60  # Frames between shots
        self.movement_timer = 0
        self.entered_screen = False  # Track if UFO has entered the play area
        self.flash_timer = 0
        self.flash_interval = 10  # Lower = faster flashing
        self.base_y = self.y  # Store initial y position for vertical movement

    def update(self):
        # Move UFO
        self.x += self.dx
        self.y += self.dy

        # Check if UFO has entered the screen
        if not self.entered_screen and self.x <= SCREEN_WIDTH - self.radius * 2:
            self.entered_screen = True
            self.dx = 1  # Start moving right
            self.base_y = self.y

        # If in screen, do Lissajous movement pattern
        if self.entered_screen:
            self.movement_timer += 0.02
            # Lissajous pattern with different frequencies for more interesting movement
            self.dx = math.sin(self.movement_timer) * 3
            # Larger vertical movement range
            self.dy = math.sin(1.5 * self.movement_timer) * 2.5

            # Center point for the movement
            center_x = SCREEN_WIDTH * 0.7  # Keep UFO more towards the right side
            center_y = SCREEN_HEIGHT * 0.5  # Center vertically

            # Update position with bounded movement
            target_x = center_x + math.sin(self.movement_timer) * (SCREEN_WIDTH * 0.2)
            target_y = center_y + math.sin(1.5 * self.movement_timer) * (SCREEN_HEIGHT * 0.35)

            # Smooth movement towards target
            self.x += (target_x - self.x) * 0.05
            self.y += (target_y - self.y) * 0.05

            # Keep UFO in bounds
            if self.x < self.radius:
                self.x = self.radius
            elif self.x > SCREEN_WIDTH - self.radius:
                self.x = SCREEN_WIDTH - self.radius
            if self.y < self.radius:
                self.y = self.radius
            elif self.y > SCREEN_HEIGHT - self.radius:
                self.y = SCREEN_HEIGHT - self.radius

        # Update bullets with slower scroll speed
        for bullet in self.bullets[:]:
            # Bullets move left at half the pipe scroll speed
            bullet['x'] += bullet['dx'] - PIPE_SPEED * 0.5
            bullet['y'] += bullet['dy']
            # Remove bullets that are off screen
            if (bullet['x'] < -10 or bullet['x'] > SCREEN_WIDTH + 10 or
                bullet['y'] < -10 or bullet['y'] > SCREEN_HEIGHT + 10):
                self.bullets.remove(bullet)

        # Shoot timer
        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_interval:
            self.shoot_timer = 0
            # Shoot two bullets with adjusted speeds
            self.bullets.append({
                'x': self.x,
                'y': self.y,
                'dx': -2,  # Slower left movement
                'dy': 0
            })
            self.bullets.append({
                'x': self.x,
                'y': self.y,
                'dx': -1,  # Slight left drift for down bullet
                'dy': 3  # Down
            })

    def draw(self, screen):
        # Flash effect
        self.flash_timer = (self.flash_timer + 1) % self.flash_interval
        flash_color = (192, 192, 192)  # Base silver color
        if self.flash_timer < self.flash_interval // 2:
            flash_color = (255, 255, 200)  # Bright yellow-white flash

        # Draw UFO body
        pygame.draw.circle(screen, flash_color, (int(self.x), int(self.y)), self.radius)

        # Draw UFO dome
        dome_height = self.radius // 2
        dome_rect = pygame.Rect(self.x - self.radius//2, self.y - dome_height,
                              self.radius, dome_height)
        pygame.draw.ellipse(screen, flash_color, dome_rect)

        # Draw UFO lights with flashing effect
        light_radius = 3
        light_color = (255, 255, 0) if self.flash_timer < self.flash_interval // 2 else (255, 150, 0)
        for i in range(4):
            angle = i * math.pi / 2
            light_x = self.x + (self.radius - light_radius) * math.cos(angle)
            light_y = self.y + (self.radius - light_radius) * math.sin(angle)
            pygame.draw.circle(screen, light_color, (int(light_x), int(light_y)), light_radius)

        # Draw bullets
        for bullet in self.bullets:
            pygame.draw.circle(screen, (255, 0, 0),
                             (int(bullet['x']), int(bullet['y'])), 3)

    def get_rect(self):
        """Get UFO's collision rectangle"""
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                         self.radius * 2, self.radius * 2)

class Explosion:
    def __init__(self, x, y, radius=400):  # Doubled the radius from 200 to 400
        self.x = x
        self.y = y
        self.radius = radius
        self.current_radius = 0
        self.max_alpha = 200  # Increased alpha for more visible explosion
        self.current_alpha = self.max_alpha
        self.growth_speed = 20  # Faster growth
        self.fade_speed = 3  # Slower fade for longer lasting explosion
        self.is_finished = False

    def update(self):
        # Grow explosion
        if self.current_radius < self.radius:
            self.current_radius += self.growth_speed
        else:
            # Start fading
            self.current_alpha -= self.fade_speed
            if self.current_alpha <= 0:
                self.is_finished = True

    def draw(self, screen):
        # Draw outer explosion circle (orange)
        outer_surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(outer_surface, (255, 165, 0, self.current_alpha),
                         (self.radius, self.radius), self.current_radius)

        # Draw inner explosion circle (bright yellow)
        inner_radius = self.current_radius * 0.7
        pygame.draw.circle(outer_surface, (255, 255, 200, self.current_alpha),
                         (self.radius, self.radius), inner_radius)

        # Draw core (white)
        core_radius = self.current_radius * 0.3
        pygame.draw.circle(outer_surface, (255, 255, 255, self.current_alpha),
                         (self.radius, self.radius), core_radius)

        # Draw to screen
        screen.blit(outer_surface,
                   (self.x - self.radius, self.y - self.radius))

class Star:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        # Fainter stars: brightness between 50 and 150 (darker grey to light grey)
        brightness = random.randint(50, 150)
        self.color = (brightness, brightness, brightness)
        # Smaller stars: size between 1 and 2 pixels only
        self.size = random.randint(1, 2)
        # Even slower movement
        self.speed = random.uniform(0.1, 0.3)

    def update(self):
        self.x -= self.speed
        if self.x < 0:
            self.x = SCREEN_WIDTH
            self.y = random.randint(0, SCREEN_HEIGHT)
            # New random brightness when recycling star
            brightness = random.randint(50, 150)
            self.color = (brightness, brightness, brightness)

    def draw(self, screen):
        # For smallest stars, just set a pixel
        if self.size == 1:
            screen.set_at((int(self.x), int(self.y)), self.color)
        else:
            # For size 2, draw a small circle
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 1)

def get_level_info(score):
    """Get level info based on score"""
    level = score // 100

    # Calculate gap size
    gap_size = max(INITIAL_GAP_SIZE - (level * GAP_DECREASE_RATE), MIN_GAP_SIZE)

    # Set background color based on level
    if level == 0:
        bg_color = BLACK
    elif level == 1:
        bg_color = DARK_GREEN
    elif level == 2:
        bg_color = DARK_BLUE
    elif level == 3:
        bg_color = YELLOW
    elif level == 4:
        bg_color = PURPLE
    else:
        bg_color = RED

    return gap_size, bg_color

def spawn_pipe(pipes, score):
    """Spawn a new pipe with gap size based on score"""
    gap_size, _ = get_level_info(score)
    pipe = Pipe()
    pipe.gap_size = gap_size // 2  # Half the gap size since we add it both up and down
    pipe.gap_y = random.randint(pipe.gap_size + 50, SCREEN_HEIGHT - pipe.gap_size - 50)
    pipes.append(pipe)

def check_collision(bird, pipe):
    """Check collision between bird and pipe with more forgiving hitbox"""
    bird_rect = bird.get_rect()
    # Top pipe
    if bird_rect.colliderect(pygame.Rect(pipe.x, 0,
                                       pipe.width, pipe.gap_y - pipe.gap_size)):
        return True
    # Bottom pipe
    if bird_rect.colliderect(pygame.Rect(pipe.x, pipe.gap_y + pipe.gap_size,
                                       pipe.width, SCREEN_HEIGHT)):
        return True
    return False

def reset_game():
    bird = Bird()
    pipes = []
    enemies = []
    bullets = []
    powerups = []
    gates = []
    ufos = []
    stars = [Star() for _ in range(50)]  # Reduced from 100 to 50 stars
    score = 0
    last_pipe = pygame.time.get_ticks()
    last_enemy = pygame.time.get_ticks()
    last_powerup = pygame.time.get_ticks()
    last_gate = pygame.time.get_ticks()
    last_ufo = pygame.time.get_ticks()
    return bird, pipes, enemies, bullets, powerups, gates, ufos, stars, score, last_pipe, last_enemy, last_powerup, last_gate, last_ufo

def draw_message(screen, text, y_offset=0):
    """Draw centered text message"""
    font = pygame.font.Font(None, 36)
    text_surface = font.render(text, True, WHITE)
    text_rect = text_surface.get_rect()
    text_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + y_offset)
    screen.blit(text_surface, text_rect)

def show_title_screen(screen, sounds):
    """Show title screen with all instructions"""
    # Start playing title music
    if 'title_music' in sounds:
        sounds['title_music'].play(-1)  # -1 means loop indefinitely

    # Fonts
    title_font = pygame.font.Font(None, 74)
    subtitle_font = pygame.font.Font(None, 48)
    instruction_font = pygame.font.Font(None, 36)

    # Title
    title_text = title_font.render('Space Flapper', True, (255, 255, 255))
    title_rect = title_text.get_rect(center=(400, 150))

    # Instructions list
    instructions = [
        ('Controls:', None),
        ('SPACE', 'Flap & Shoot'),
        ('X', 'Change Weapon'),
        ('Power-ups:', None),
        ('Green', 'Shield'),
        ('Magenta', 'Spread Gun'),
        ('Cyan', 'Fast Laser'),
        ('Yellow', 'Charge Shot')
    ]

    # Render instructions
    instruction_surfaces = []
    y_pos = 250
    for text, desc in instructions:
        if desc is None:  # Header
            rendered_text = instruction_font.render(text, True, (255, 255, 0))  # Yellow headers
        else:  # Regular instruction
            rendered_text = instruction_font.render(f"{text} - {desc}", True, (255, 255, 255))
        rect = rendered_text.get_rect(center=(400, y_pos))
        instruction_surfaces.append((rendered_text, rect))
        y_pos += 40

    # Start prompt
    start_text = subtitle_font.render('Press SPACE to Start!', True, (255, 255, 0))
    start_rect = start_text.get_rect(center=(400, 520))

    # Main loop
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                waiting = False
                if 'title_music' in sounds:
                    sounds['title_music'].stop()

        # Draw everything
        screen.fill((0, 0, 0))
        screen.blit(title_text, title_rect)
        for text, rect in instruction_surfaces:
            screen.blit(text, rect)
        screen.blit(start_text, start_rect)
        pygame.display.flip()

def load_sounds():
    """Load all game sounds"""
    sounds = {}
    sound_files = [
        'shoot', 'laser', 'spread', 'hit', 'game_over', 'power_up',
        'enemy_death', 'charge', 'shield_recharge', 'ufo_hit',
        'ufo_death', 'ufo_shoot', 'title_music', 'ufo_presence',
        'explosion'  # Add explosion sound to the list
    ]
    for file in sound_files:
        try:
            sound = pygame.mixer.Sound(f"sounds/{file}.wav")
            sound.set_volume(0.5)
            sounds[file] = sound
        except Exception as e:
            print(f"Error loading sound: {file} - {str(e)}")
    return sounds

def spawn_powerup(last_powerup, current_time):
    if current_time - last_powerup >= 8000:  # Spawn every 8 seconds
        x = SCREEN_WIDTH
        y = random.randint(50, SCREEN_HEIGHT - 50)
        powerup_type = random.choice([
            PowerUpType.SHIELD,
            PowerUpType.SPREAD,
            PowerUpType.LASER,
            PowerUpType.CHARGE,
            PowerUpType.NUKE,
        ])
        return PowerUp(powerup_type, x, y), current_time
    return None, last_powerup

def spawn_ufo(last_ufo, current_time):
    # 30% chance to spawn UFO every 10 seconds
    if current_time - last_ufo >= 10000 and random.random() < 0.3:
        ufo = UFO()
        ufo.x = 400 + ufo.radius  # Start off screen to the right
        ufo.y = random.randint(50, 200)  # Start higher up
        ufo.dx = -2  # Move left
        ufo.dy = 1   # Add constant downward movement
        return ufo, current_time
    return None, last_ufo

def main():
    global shoot_sound, laser_sound, spread_sound, hit_sound, shield_up_sound, power_up_sound, game_over_sound, enemy_death_sound, charge_sound, shield_recharge_sound, ufo_hit_sound, ufo_death_sound, ufo_shoot_sound, title_music, ufo_presence_sound, explosion_sound

    pygame.init()

    pygame.mixer.quit()  # Quit any existing mixer
    pygame.mixer.pre_init(44100, -16, 2, 1024)  # Increased buffer size
    pygame.mixer.init()

    print("Sound system status:")
    print(f"Mixer initialized: {pygame.mixer.get_init()}")
    print(f"Sound enabled: {pygame.mixer.get_num_channels() > 0}")

    empty_sound = pygame.mixer.Sound(buffer=b'')

    try:
        # Load all sounds without testing them
        sounds = load_sounds()
        shoot_sound = sounds['shoot']
        laser_sound = sounds['laser']
        spread_sound = sounds['spread']
        hit_sound = sounds['hit']
        power_up_sound = sounds['power_up']
        game_over_sound = sounds['game_over']
        enemy_death_sound = sounds['enemy_death']
        charge_sound = sounds['charge']
        shield_recharge_sound = sounds['shield_recharge']
        ufo_hit_sound = sounds['ufo_hit']
        ufo_death_sound = sounds['ufo_death']
        ufo_shoot_sound = sounds['ufo_shoot']
        title_music = sounds['title_music']
        ufo_presence_sound = sounds['ufo_presence']
        explosion_sound = sounds['explosion']

        # Set volumes
        shoot_sound.set_volume(0.4)
        laser_sound.set_volume(0.4)
        spread_sound.set_volume(0.4)
        hit_sound.set_volume(0.4)
        power_up_sound.set_volume(0.5)
        game_over_sound.set_volume(0.5)
        enemy_death_sound.set_volume(0.5)
        charge_sound.set_volume(0.4)
        shield_recharge_sound.set_volume(0.5)
        ufo_hit_sound.set_volume(0.4)
        ufo_death_sound.set_volume(0.5)
        ufo_shoot_sound.set_volume(0.3)
        title_music.set_volume(0.5)
        ufo_presence_sound.set_volume(0.2)  # Keep UFO presence sound subtle

        shield_up_sound = power_up_sound

    except Exception as e:
        print(f"Error loading sounds: {str(e)}")
        print("Running without sound.")
        shoot_sound = laser_sound = spread_sound = hit_sound = shield_up_sound = power_up_sound = game_over_sound = enemy_death_sound = charge_sound = shield_recharge_sound = ufo_hit_sound = ufo_death_sound = ufo_shoot_sound = title_music = ufo_presence_sound = empty_sound

    game_state = MENU
    bird, pipes, enemies, bullets, powerups, gates, ufos, stars, score, last_pipe, last_enemy, last_powerup, last_gate, last_ufo = reset_game()
    enemy_frequency = 2000  # milliseconds
    powerup_frequency = 8000  # Increased frequency for power-ups
    font = pygame.font.Font(None, 36)
    high_score = 0

    running = True
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('Space Flapper')
    clock = pygame.time.Clock()
    charging_started = False

    show_title_screen(screen, {
        'title_music': title_music
    })

    while running:
        current_time = pygame.time.get_ticks()

        # Get current level info for background and gap size
        gap_size, bg_color = get_level_info(score)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if game_state == MENU:
                        game_state = PLAYING
                    elif game_state == PLAYING:
                        bird.flap()
                    elif game_state == GAME_OVER:
                        bird, pipes, enemies, bullets, powerups, gates, ufos, stars, score, last_pipe, last_enemy, last_powerup, last_gate, last_ufo = reset_game()
                        game_state = PLAYING
                elif event.key == pygame.K_x and game_state == PLAYING:
                    if bird.weapon.type == WeaponType.CHARGE:
                        bird.start_charging(current_time)
                        charging_started = True
                    elif bird.weapon.type == WeaponType.NUKE and bird.active_nuke:
                        # Only handle detonation on key press
                        should_reset, enemies_killed = bird.detonate_nuke(enemies, bullets, screen, ufos, gates)
                        score += enemies_killed * 5  # Add 5 points per enemy killed
                        if should_reset:
                            bird.weapon = Weapon()
                    else:
                        # Handle all other weapons including nuke launch
                        new_bullets, should_reset = bird.shoot(current_time)
                        bullets.extend(new_bullets)
                        if should_reset:
                            bird.weapon = Weapon()

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_x and charging_started:
                    new_bullets, should_reset = bird.release_charge(current_time)
                    bullets.extend(new_bullets)
                    if should_reset:
                        bird.weapon = Weapon()
                    charging_started = False

        if game_state == PLAYING:
            # Get pressed keys
            keys = pygame.key.get_pressed()

            # Handle shooting
            if keys[pygame.K_x]:
                if bird.weapon.type == WeaponType.CHARGE and not charging_started:
                    bird.start_charging(current_time)
                    charging_started = True
                elif not charging_started and bird.weapon.type != WeaponType.NUKE:
                    new_bullets, should_reset = bird.shoot(current_time)
                    bullets.extend(new_bullets)
                    if should_reset:
                        bird.weapon = Weapon()

            # Update charge weapon
            if charging_started:
                bird.update_charge(current_time)

            # Spawn new pipes
            if current_time - last_pipe > PIPE_FREQUENCY:
                pipe = Pipe()
                pipe.gap_size = gap_size // 2  # Half the gap size since we add it both up and down
                pipe.gap_y = random.randint(pipe.gap_size + 50, SCREEN_HEIGHT - pipe.gap_size - 50)
                pipes.append(pipe)
                last_pipe = current_time

            # Spawn new enemies
            if current_time - last_enemy > enemy_frequency:
                enemies.append(Enemy())
                last_enemy = current_time

            # Spawn new powerups
            powerup, last_powerup = spawn_powerup(last_powerup, current_time)
            if powerup:
                powerups.append(powerup)

            # Spawn new gates
            if current_time - last_gate > 6000:  # Spawn gate every 6 seconds
                gates.append(Gate())
                last_gate = current_time

            # Spawn new UFOs
            if len(ufos) == 0 and score > 5:  # Only spawn after score 5
                if random.random() < 0.002:  # Reduced from higher value to make UFOs more rare
                    ufo = UFO(SCREEN_WIDTH + 20, random.randint(50, SCREEN_HEIGHT - 50))
                    ufos.append(ufo)
                    ufo_presence_sound.play(-1)  # Loop the sound
            last_ufo = current_time

            # Update
            bird.update(current_time)

            # Update pipes and check for score
            for pipe in pipes[:]:
                pipe.update()
                if pipe.x + pipe.width < 0:
                    pipes.remove(pipe)
                if not pipe.passed and pipe.x < bird.x:
                    score += 1
                    pipe.passed = True

            # Update enemies
            for enemy in enemies[:]:
                enemy.update()
                if enemy.x + enemy.size < 0:
                    enemies.remove(enemy)

            # Update powerups
            for powerup in powerups[:]:
                powerup.update()
                if powerup.x + powerup.size < 0:
                    powerups.remove(powerup)
                # Check collision with bird
                bird_rect = pygame.Rect(bird.x, bird.y, bird.radius*2, bird.radius*2)
                if bird_rect.colliderect(powerup.get_rect()):
                    powerup.collect(bird)
                    powerups.remove(powerup)

            # Update gates
            for gate in gates[:]:
                gate.update()
                if gate.x + gate.width < 0:
                    gates.remove(gate)
                elif not gate.destroyed:
                    # Check collision with bird
                    if bird.get_rect().colliderect(gate.get_rect()):
                        if bird.take_hit(current_time):
                            game_over_sound.play()
                            ufo_presence_sound.stop()  # Stop UFO sound when player dies
                            high_score = max(score, high_score)
                            game_state = GAME_OVER

            # Update UFOs
            for ufo in ufos[:]:
                ufo.update()
                if ufo.x + ufo.radius < 0:
                    ufos.remove(ufo)
                    if len(ufos) == 0:  # Stop presence sound when no UFOs left
                        ufo_presence_sound.stop()
                # Check collision with bird bullets
                for bullet in bullets[:]:
                    # Fix: Use bullet object attributes instead of dictionary access
                    dx = bullet.x - ufo.x
                    dy = bullet.y - ufo.y
                    distance = math.sqrt(dx * dx + dy * dy)
                    if distance < ufo.radius + 5:  # 5 is bullet radius
                        bullets.remove(bullet)
                        ufo.health -= 1
                        ufo_hit_sound.play()
                        if ufo.health <= 0:
                            ufos.remove(ufo)
                            score += 10
                            ufo_death_sound.play()
                            if len(ufos) == 0:
                                ufo_presence_sound.stop()
                            # Spawn powerup
                            powerup_type = random.choice([PowerUpType.SHIELD, PowerUpType.SPREAD, PowerUpType.LASER, PowerUpType.CHARGE])
                            powerups.append(PowerUp(powerup_type, ufo.x, ufo.y))
                            break

            # Add back the collision checks that were removed
            # Check gate collisions
            for bullet in bullets[:]:
                for gate in gates:
                    if not gate.destroyed and bullet.get_rect().colliderect(gate.get_rect()):
                        if gate.hit(bullet.damage, current_time):
                            score += 5  # Bonus points for destroying a gate
                        if bullet in bullets:
                            bullets.remove(bullet)
                        break
                else:
                    # Check enemy collisions if bullet didn't hit a gate
                    for bullet in bullets[:]:
                        for enemy in enemies[:]:
                            if bullet.get_rect().colliderect(enemy.get_rect()):
                                if bullet.weapon_type == WeaponType.NUKE and bullet == bird.active_nuke:
                                    # Auto-detonate nuke on enemy collision
                                    should_reset, enemies_killed = bird.detonate_nuke(enemies, bullets, screen, ufos, gates)
                                    score += enemies_killed * 5  # Add points for kills
                                    if should_reset:
                                        bird.weapon = Weapon()
                                    break
                                else:
                                    # Normal bullet collision
                                    enemy_death_sound.play()
                                    score += bullet.damage * 2
                                    if bullet in bullets:
                                        bullets.remove(bullet)
                                    if enemy in enemies:
                                        enemies.remove(enemy)
                                    break

            # Check collisions with pipes
            for pipe in pipes:
                if check_collision(bird, pipe):
                    if bird.take_hit(current_time):
                        game_over_sound.play()
                        ufo_presence_sound.stop()
                        high_score = max(score, high_score)
                        game_state = GAME_OVER

            # Check collisions with enemies
            for enemy in enemies[:]:
                bird_rect = pygame.Rect(bird.x, bird.y, bird.radius*2, bird.radius*2)
                if bird_rect.colliderect(enemy.get_rect()):
                    if bird.take_hit(current_time):
                        game_over_sound.play()
                        ufo_presence_sound.stop()
                        high_score = max(score, high_score)
                        game_state = GAME_OVER

            # Update bullets
            for bullet in bullets[:]:  # Use slice copy to safely modify list while iterating
                bullet.update()  # Move bullets
                # Only remove non-nuke bullets that go off screen
                if bullet.x > SCREEN_WIDTH and bullet != bird.active_nuke:
                    bullets.remove(bullet)

        # Draw
        screen.fill(bg_color)  # Use level background color

        # Draw stars first (before everything else)
        for star in stars:
            star.update()
            star.draw(screen)

        if game_state == MENU:
            draw_message(screen, "Flappy Bird", -80)
            draw_message(screen, "Press SPACE to Start", -40)
            draw_message(screen, "X to Shoot, SPACE to Flap", 0)
            draw_message(screen, "Collect purple (spread) and cyan (laser) power-ups!", 40)
            draw_message(screen, "Collect green shield power-ups to gain shields!", 80)
        else:
            bird.draw(screen, current_time, score)
            for pipe in pipes:
                pipe.draw(screen)
            for enemy in enemies:
                enemy.draw(screen)
            for bullet in bullets:
                bullet.draw(screen)
            for powerup in powerups:
                powerup.draw(screen)
            for gate in gates:
                gate.draw(screen, current_time)
            for ufo in ufos:
                ufo.draw(screen)

            # Draw high score in top right corner
            high_score_text = font.render(f'High Score: {high_score}', True, WHITE)
            high_score_rect = high_score_text.get_rect()
            high_score_rect.topright = (SCREEN_WIDTH - 10, 10)  # 10px padding from right and top
            screen.blit(high_score_text, high_score_rect)

            if game_state == GAME_OVER:
                draw_message(screen, "Game Over!", -20)
                draw_message(screen, "Press SPACE to Play Again", 20)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
