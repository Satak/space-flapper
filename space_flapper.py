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
DARK_YELLOW = (50, 50, 0)
DARK_PURPLE = (50, 0, 50)
DARK_GREEN = (0, 20, 0)
DARK_BLUE = (0, 0, 20)
DARK_RED = (50, 0, 0)

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

        # Draw active nuke and its trail
        if self.active_nuke:
            self.active_nuke.draw(screen)

        # Draw explosion if active
        if self.explosion:
            self.explosion.draw(screen)
            self.explosion.update()
            if self.explosion.is_finished:
                self.explosion = None

        # Draw ammo bar if not using default weapon
        if self.weapon.type != WeaponType.DEFAULT:
            # Bar dimensions
            bar_width = 50
            bar_height = 4
            bar_x = self.x - bar_width // 2
            bar_y = self.y + self.radius + 10  # Position below bird

            # Draw background (empty bar)
            pygame.draw.rect(screen, (50, 50, 50),
                           (bar_x, bar_y, bar_width, bar_height))

            # Calculate filled portion
            if self.weapon.ammo != float('inf'):
                # Get max ammo based on weapon type
                max_ammo = {
                    WeaponType.SPREAD: 30,
                    WeaponType.LASER: 50,
                    WeaponType.CHARGE: 20,
                    WeaponType.NUKE: 3
                }.get(self.weapon.type, 0)

                fill_width = int(bar_width * (self.weapon.ammo / max_ammo))

                # Color based on weapon type
                bar_colors = {
                    WeaponType.SPREAD: (255, 0, 255),    # Purple
                    WeaponType.LASER: (0, 128, 255),     # Blue
                    WeaponType.CHARGE: (255, 255, 0),    # Yellow
                    WeaponType.NUKE: (255, 165, 0)       # Orange
                }
                bar_color = bar_colors.get(self.weapon.type, (255, 255, 255))

                # Draw filled portion
                pygame.draw.rect(screen, bar_color,
                               (bar_x, bar_y, fill_width, bar_height))

                # Add glow effect
                glow_surface = pygame.Surface((bar_width, bar_height), pygame.SRCALPHA)
                glow_color = (*bar_color, 100)  # Semi-transparent version of bar color
                pygame.draw.rect(glow_surface, glow_color,
                               (0, 0, fill_width, bar_height))
                screen.blit(glow_surface, (bar_x, bar_y - 1))  # Slight offset for glow

    def shoot(self, current_time):
        if current_time - self.weapon.last_shot_time >= self.weapon.cooldown:
            self.weapon.last_shot_time = current_time
            bullets = []

            if self.weapon.ammo > 0:
                if self.weapon.type == WeaponType.NUKE and not self.active_nuke:
                    nuke = Bullet(self.x + self.radius * 2, self.y, WeaponType.NUKE, velocity=3)
                    self.active_nuke = nuke
                    bullets.append(nuke)
                    self.weapon.ammo -= 1  # Decrease ammo when shooting nuke
                    return bullets, False  # Never reset here, wait for detonation
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

                if self.weapon.type != WeaponType.DEFAULT and self.weapon.type != WeaponType.NUKE:
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

    def detonate_nuke(self, enemies, bullets, screen, ufos, gates, blobs):
        """Detonate the nuke, destroying all enemies on screen"""
        if not self.active_nuke:
            return False, 0

        # Create explosion at nuke position
        self.explosion = Explosion(self.active_nuke.x, self.active_nuke.y)
        explosion_sound.play()

        # Remove the nuke from bullets
        if self.active_nuke in bullets:
            bullets.remove(self.active_nuke)
        self.active_nuke = None

        # Count enemies killed
        enemies_killed = len(enemies) + len(ufos) + len(blobs)

        # Clear all enemies
        enemies.clear()
        if len(ufos) > 0:
            ufos.clear()
            ufo_presence_sound.stop()  # Stop UFO sound when all UFOs are destroyed
        blobs.clear()

        # Destroy all gates
        for gate in gates:
            gate.destroyed = True

        # Return True only if this was the last nuke AND it's detonated
        return self.weapon.ammo <= 0, enemies_killed

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

class TentacleBlob:
    def __init__(self, x=None, y=None):
        self.x = x if x is not None else SCREEN_WIDTH + 20
        self.y = y if y is not None else random.randint(50, SCREEN_HEIGHT - 50)
        self.radius = 15
        self.health = 3
        self.color = (255, 0, 255)  # Changed from green to purple
        self.glow_color = (255, 128, 255)  # Changed to light purple glow

        # Movement parameters
        self.speed = 3
        self.movement_timer = 0
        self.direction_change_delay = random.randint(30, 60)
        self.dx = -self.speed
        self.dy = random.choice([-1, 1]) * self.speed
        self.moving_right = False  # Track direction

        # Tentacle parameters
        self.num_tentacles = 8
        self.base_tentacle_length = 100  # Base length
        self.tentacle_length = self.base_tentacle_length
        self.tentacle_segments = 15
        self.tentacles = []
        self.tentacle_wiggle_speed = 0.08
        self.tentacle_phase = 0
        self.tentacle_thickness = 5

        # Tentacle growth parameters
        self.length_modifiers = [1.0] * self.num_tentacles  # Individual length modifiers
        self.growth_speeds = [random.uniform(0.02, 0.04) for _ in range(self.num_tentacles)]
        self.growth_phases = [random.uniform(0, 2 * math.pi) for _ in range(self.num_tentacles)]
        self.min_length_factor = 0.7  # Minimum length is 70% of base
        self.max_length_factor = 1.3  # Maximum length is 130% of base

        # Initialize tentacles with evenly spaced angles
        angle_step = (2 * math.pi) / self.num_tentacles  # Evenly space tentacles
        for i in range(self.num_tentacles):
            angle = i * angle_step  # This will space them evenly around the circle
            self.tentacles.append({
                'angle': angle,
                'segments': [(self.x, self.y) for _ in range(self.tentacle_segments)]
            })

        # Sound parameters
        self.last_sound_time = pygame.time.get_ticks()
        self.sound_interval = 2000  # Play sound every 2 seconds
        self.sound_started = False  # Track if we've started playing sounds

        # Flash effect parameters
        self.flash_timer = 0
        self.flash_duration = 5  # Frames to show flash
        self.is_flashing = False

    def update(self):
        current_time = pygame.time.get_ticks()

        # Play periodic sound when on screen
        if not self.sound_started and self.x < SCREEN_WIDTH - self.radius:
            blob_sound.play()
            self.sound_started = True
            self.last_sound_time = current_time
        elif self.sound_started and current_time - self.last_sound_time >= self.sound_interval:
            blob_sound.play()
            self.last_sound_time = current_time

        # Change direction at screen edges
        if self.x < self.radius and not self.moving_right:
            self.dx = self.speed  # Move right
            self.moving_right = True
            blob_sound.play()  # Play sound when changing direction
        elif self.x > SCREEN_WIDTH - self.radius and self.moving_right:
            self.dx = -self.speed  # Move left
            self.moving_right = False
            blob_sound.play()  # Play sound when changing direction

        # Update position
        self.x += self.dx
        self.y += self.dy

        # Keep in bounds
        if self.y < self.radius:
            self.y = self.radius
            self.dy *= -1
        elif self.y > SCREEN_HEIGHT - self.radius:
            self.y = SCREEN_HEIGHT - self.radius
            self.dy *= -1

        # Update tentacle lengths
        for i in range(self.num_tentacles):
            # Use sine wave to smoothly vary length
            self.growth_phases[i] += self.growth_speeds[i]
            self.length_modifiers[i] = (
                ((self.max_length_factor - self.min_length_factor) / 2) *
                math.sin(self.growth_phases[i]) +
                ((self.max_length_factor + self.min_length_factor) / 2)
            )

        # Update tentacle physics
        self.tentacle_phase += self.tentacle_wiggle_speed
        for i, tentacle in enumerate(self.tentacles):
            # Update tentacle base position
            tentacle['segments'][0] = (self.x, self.y)

            # Calculate current tentacle length
            current_length = self.base_tentacle_length * self.length_modifiers[i]
            segment_length = current_length / self.tentacle_segments

            # Update each segment with wave motion
            for j in range(1, self.tentacle_segments):
                prev_x, prev_y = tentacle['segments'][j-1]
                angle = tentacle['angle'] + math.sin(self.tentacle_phase + j * 0.5) * 0.3
                new_x = prev_x + math.cos(angle) * segment_length
                new_y = prev_y + math.sin(angle) * segment_length
                tentacle['segments'][j] = (new_x, new_y)

            # Rotate tentacle base angle for next frame
            tentacle['angle'] += 0.02

    def flash(self):
        """Start flash effect"""
        self.is_flashing = True
        self.flash_timer = self.flash_duration

    def draw(self, screen):
        # Get current color based on flash state
        current_color = (255, 255, 255) if self.is_flashing else self.color
        current_glow = (255, 255, 255) if self.is_flashing else self.glow_color

        # Draw glow
        pygame.draw.circle(screen, current_glow, (int(self.x), int(self.y)), self.radius + 2)

        # Draw main body
        pygame.draw.circle(screen, current_color, (int(self.x), int(self.y)), self.radius)

        # Draw tentacles
        for tentacle in self.tentacles:
            for i in range(1, len(tentacle['segments'])):
                start = tentacle['segments'][i-1]
                end = tentacle['segments'][i]
                # Gradient color from body to tip
                if self.is_flashing:
                    segment_color = (255, 255, 255)  # White when flashing
                else:
                    color_factor = 1 - (i / self.tentacle_segments)
                    segment_color = (
                        int(self.color[0] * color_factor),
                        int(self.color[1] * color_factor),
                        int(self.color[2] * color_factor)
                    )
                pygame.draw.line(screen, segment_color, start, end, self.tentacle_thickness)

        # Update flash timer
        if self.is_flashing:
            self.flash_timer -= 1
            if self.flash_timer <= 0:
                self.is_flashing = False

    def get_rect(self):
        # Return rect for main body collision
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                         self.radius * 2, self.radius * 2)

    def get_tentacle_rects(self):
        # Return list of rects for tentacle segment collisions
        tentacle_rects = []
        for tentacle in self.tentacles:
            for i in range(1, len(tentacle['segments'])):
                x1, y1 = tentacle['segments'][i-1]
                x2, y2 = tentacle['segments'][i]
                # Create a small rect for each segment
                rect_x = min(x1, x2)
                rect_y = min(y1, y2)
                rect_w = abs(x2 - x1) + 4  # Add some padding
                rect_h = abs(y2 - y1) + 4
                tentacle_rects.append(pygame.Rect(rect_x, rect_y, rect_w, rect_h))
        return tentacle_rects

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

        # Pupil animation properties
        self.pupil_offset = 0
        self.pupil_direction = 1  # 1 for right, -1 for left
        self.pupil_max_offset = 2  # Maximum pixels to move left/right
        self.pupil_speed = 0.05  # Speed of pupil movement

    def update(self):
        self.x -= self.speed

        # Update pupil animation
        self.pupil_offset += self.pupil_speed * self.pupil_direction
        if abs(self.pupil_offset) >= self.pupil_max_offset:
            self.pupil_direction *= -1  # Reverse direction at max offset

    def draw(self, screen):
        # Draw the main body
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)

        # Draw eyes
        eye_spacing = 8
        pygame.draw.circle(screen, self.eye_color, (int(self.x - eye_spacing), int(self.y - 2)), self.eye_size)
        pygame.draw.circle(screen, self.eye_color, (int(self.x + eye_spacing), int(self.y - 2)), self.eye_size)

        # Draw animated pupils
        pygame.draw.circle(screen, self.pupil_color,
                         (int(self.x - eye_spacing + self.pupil_offset), int(self.y - 2)), self.pupil_size)
        pygame.draw.circle(screen, self.pupil_color,
                         (int(self.x + eye_spacing + self.pupil_offset), int(self.y - 2)), self.pupil_size)

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
        # Start position should be off-screen
        self.x = SCREEN_WIDTH + 40
        self.y = random.randint(50, SCREEN_HEIGHT//3)
        self.radius = 20
        self.health = 3
        self.bullets = []
        self.last_shot = pygame.time.get_ticks()
        self.shot_delay = 2000
        self.flash_timer = 0
        self.flash_interval = 30

        # Movement parameters
        self.movement_timer = 0
        self.target_x = SCREEN_WIDTH * 0.7  # Target center position
        self.target_y = SCREEN_HEIGHT * 0.5
        self.movement_speed = 0.02
        self.entrance_speed = 2  # Constant entrance speed

    def update(self):
        current_time = pygame.time.get_ticks()

        # Move towards play area while doing pattern movement
        if self.x > self.target_x:
            self.x -= self.entrance_speed

        # Always do pattern movement
        self.movement_timer += self.movement_speed

        # Calculate pattern offsets
        offset_x = math.sin(self.movement_timer) * 100
        offset_y = math.sin(self.movement_timer * 1.5) * 80

        # Apply pattern movement
        pattern_x = self.target_x + offset_x
        pattern_y = self.target_y + offset_y

        # Blend between entrance and pattern positions
        blend_factor = min(1.0, (SCREEN_WIDTH - self.x) / (SCREEN_WIDTH - self.target_x))
        self.y = self.y * (1 - blend_factor) + pattern_y * blend_factor

        # Keep UFO in bounds
        self.x = max(self.radius, min(self.x, SCREEN_WIDTH - self.radius))
        self.y = max(self.radius, min(self.y, SCREEN_HEIGHT - self.radius))

        # Shoot at intervals once partially in screen
        if self.x < SCREEN_WIDTH - self.radius and current_time - self.last_shot > self.shot_delay:
            self.shoot(50, SCREEN_HEIGHT // 2)
            self.last_shot = current_time

        # Update bullets
        for bullet in self.bullets[:]:
            bullet.update()
            if bullet.is_off_screen():
                self.bullets.remove(bullet)

    def shoot(self, target_x, target_y):
        """Create a new bullet aimed at the target"""
        bullet = UFOBullet(self.x, self.y, target_x, target_y)
        self.bullets.append(bullet)
        ufo_shoot_sound.play()

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

        # Draw horizontal visor line (full width of UFO)
        visor_width = self.radius * 2  # Full width of UFO
        visor_height = 2  # 2 pixels thick
        visor_x = self.x - visor_width // 2
        visor_y = self.y - visor_height // 2
        pygame.draw.rect(screen, (0, 128, 255),  # Blue visor
                        (visor_x, visor_y, visor_width, visor_height))

        # Add visor glow (full width)
        glow_height = 1  # 1 pixel glow above and below
        pygame.draw.rect(screen, (128, 200, 255),  # Light blue glow
                        (visor_x, visor_y - glow_height, visor_width, glow_height))
        pygame.draw.rect(screen, (128, 200, 255),  # Light blue glow
                        (visor_x, visor_y + visor_height, visor_width, glow_height))

        # Draw small mouth (frowning curve) - lower and inverted
        mouth_width = self.radius * 0.3
        mouth_y = self.y + self.radius * 0.4  # Moved down from 0.2 to 0.4
        mouth_points = [
            (self.x - mouth_width//2, mouth_y),
            (self.x, mouth_y - 2),  # Center point slightly higher for frown
            (self.x + mouth_width//2, mouth_y)
        ]
        pygame.draw.lines(screen, (50, 50, 50), False, mouth_points, 2)

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
            bullet.draw(screen)

class UFOBullet:
    def __init__(self, x, y, target_x, target_y):
        self.x = x
        self.y = y
        # Calculate direction towards target
        angle = math.atan2(target_y - y, target_x - x)
        speed = 5
        self.dx = math.cos(angle) * speed
        self.dy = math.sin(angle) * speed
        self.radius = 3
        self.color = (255, 0, 0)  # Red bullets

    def update(self):
        self.x += self.dx
        self.y += self.dy

    def is_off_screen(self):
        return (self.x < 0 or self.x > SCREEN_WIDTH or
                self.y < 0 or self.y > SCREEN_HEIGHT)

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

    def get_rect(self):
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
        bg_color = DARK_YELLOW
    elif level == 4:
        bg_color = DARK_PURPLE
    else:
        bg_color = DARK_RED

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
    blobs = []  # Add to reset_game() too
    last_blob = pygame.time.get_ticks()
    blob_frequency = 20000  # Increased from 5000 to 20000 (20 seconds base frequency)
    return bird, pipes, enemies, bullets, powerups, gates, ufos, stars, score, last_pipe, last_enemy, last_powerup, last_gate, last_ufo, blobs, last_blob, blob_frequency

def draw_message(screen, text, y_offset=0):
    """Draw centered text message"""
    font = pygame.font.Font(None, 36)
    text_surface = font.render(text, True, WHITE)
    text_rect = text_surface.get_rect()
    text_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + y_offset)
    screen.blit(text_surface, text_rect)

def load_sounds():
    """Load all game sounds"""
    sounds = {}
    sound_files = [
        'shoot', 'laser', 'spread', 'hit', 'game_over', 'power_up',
        'enemy_death', 'charge', 'shield_recharge', 'ufo_hit',
        'ufo_death', 'ufo_shoot', 'title_music', 'ufo_presence',
        'explosion', 'blob'  # Add blob to sound files
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
        ufo = UFO()  # Use default initialization
        return ufo, current_time
    return None, last_ufo

def main():
    global shoot_sound, laser_sound, spread_sound, hit_sound, shield_up_sound, power_up_sound, game_over_sound, enemy_death_sound, charge_sound, shield_recharge_sound, ufo_hit_sound, ufo_death_sound, ufo_shoot_sound, title_music, ufo_presence_sound, explosion_sound, blob_sound

    pygame.init()
    pygame.mixer.quit()
    pygame.mixer.pre_init(44100, -16, 2, 1024)
    pygame.mixer.init()

    print("Sound system status:")
    print(f"Mixer initialized: {pygame.mixer.get_init()}")
    print(f"Sound enabled: {pygame.mixer.get_num_channels() > 0}")

    empty_sound = pygame.mixer.Sound(buffer=b'')

    try:
        # Load all sounds
        sounds = load_sounds()

        # Assign sounds from the dictionary
        shoot_sound = sounds.get('shoot', empty_sound)
        laser_sound = sounds.get('laser', empty_sound)
        spread_sound = sounds.get('spread', empty_sound)
        hit_sound = sounds.get('hit', empty_sound)
        power_up_sound = sounds.get('power_up', empty_sound)
        game_over_sound = sounds.get('game_over', empty_sound)
        enemy_death_sound = sounds.get('enemy_death', empty_sound)
        charge_sound = sounds.get('charge', empty_sound)
        shield_recharge_sound = sounds.get('shield_recharge', empty_sound)
        ufo_hit_sound = sounds.get('ufo_hit', empty_sound)
        ufo_death_sound = sounds.get('ufo_death', empty_sound)
        ufo_shoot_sound = sounds.get('ufo_shoot', empty_sound)
        title_music = sounds.get('title_music', empty_sound)
        ufo_presence_sound = sounds.get('ufo_presence', empty_sound)
        explosion_sound = sounds.get('explosion', empty_sound)
        blob_sound = sounds.get('blob', empty_sound)

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
        ufo_presence_sound.set_volume(0.2)
        explosion_sound.set_volume(0.5)
        blob_sound.set_volume(0.4)

        shield_up_sound = power_up_sound

    except Exception as e:
        print(f"Error loading sounds: {str(e)}")
        print("Running without sound.")
        # Assign empty sound to all sound variables if loading fails
        shoot_sound = laser_sound = spread_sound = hit_sound = shield_up_sound = \
        power_up_sound = game_over_sound = enemy_death_sound = charge_sound = \
        shield_recharge_sound = ufo_hit_sound = ufo_death_sound = ufo_shoot_sound = \
        title_music = ufo_presence_sound = explosion_sound = blob_sound = empty_sound

    game_state = MENU
    bird, pipes, enemies, bullets, powerups, gates, ufos, stars, score, last_pipe, last_enemy, last_powerup, last_gate, last_ufo, blobs, last_blob, blob_frequency = reset_game()
    enemy_frequency = 2000
    powerup_frequency = 8000
    font = pygame.font.Font(None, 36)
    high_score = 0

    running = True
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('Space Flapper')
    clock = pygame.time.Clock()
    charging_started = False

    # Start playing title music right away in menu
    title_music.play(-1)  # Loop the music

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
                        bird, pipes, enemies, bullets, powerups, gates, ufos, stars, score, last_pipe, last_enemy, last_powerup, last_gate, last_ufo, blobs, last_blob, blob_frequency = reset_game()
                        game_state = PLAYING
                elif event.key == pygame.K_x and game_state == PLAYING:
                    if bird.weapon.type == WeaponType.CHARGE:
                        bird.start_charging(current_time)
                        charging_started = True
                    elif bird.weapon.type == WeaponType.NUKE and bird.active_nuke:
                        # Only handle detonation on key press
                        should_reset, enemies_killed = bird.detonate_nuke(enemies, bullets, screen, ufos, gates, blobs)
                        score += enemies_killed * 5  # Add 5 points per enemy killed
                        if should_reset and bird.weapon.ammo <= 0:  # Only reset if out of ammo and after detonation
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

            # Spawn new blobs
            if len(blobs) == 0:  # Only spawn if no blobs exist
                if current_time - last_blob > blob_frequency:
                    # Only spawn after score 50 and with 20% chance
                    if score > 50 and random.random() < 0.2:
                        blobs.append(TentacleBlob())
                        last_blob = current_time
                    else:
                        last_blob = current_time - blob_frequency * 0.8  # Try again soon if didn't spawn

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

            # Update UFOs and their bullets
            for ufo in ufos[:]:
                ufo.update()
                if ufo.x + ufo.radius < 0:
                    ufos.remove(ufo)
                    if len(ufos) == 0:
                        ufo_presence_sound.stop()

                # Update UFO bullets and check collisions with player
                for bullet in ufo.bullets[:]:
                    bullet.update()
                    # Remove bullets that go off screen
                    if bullet.x < 0:
                        ufo.bullets.remove(bullet)
                        continue

                    # Check collision with player
                    bullet_rect = pygame.Rect(bullet.x - 3, bullet.y - 3, 6, 6)  # UFO bullet size
                    bird_rect = bird.get_rect()
                    if bullet_rect.colliderect(bird_rect):
                        if bird.take_hit(current_time):
                            game_over_sound.play()
                            ufo_presence_sound.stop()
                            high_score = max(score, high_score)
                            game_state = GAME_OVER
                        ufo.bullets.remove(bullet)

                # Check collision with bird bullets
                for bullet in bullets[:]:
                    dx = bullet.x - ufo.x
                    dy = bullet.y - ufo.y
                    distance = math.sqrt(dx * dx + dy * dy)
                    if distance < ufo.radius + 5:
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
                            powerup_type = random.choice([PowerUpType.SHIELD, PowerUpType.SPREAD,
                                                        PowerUpType.LASER, PowerUpType.CHARGE])
                            powerups.append(PowerUp(powerup_type, ufo.x, ufo.y))
                            break

            # Check gate collisions
            for bullet in bullets[:]:
                for gate in gates:
                    if not gate.destroyed and bullet.get_rect().colliderect(gate.get_rect()):
                        if bullet.weapon_type == WeaponType.NUKE and bullet == bird.active_nuke:
                            # Auto-detonate nuke on gate collision
                            should_reset, enemies_killed = bird.detonate_nuke(enemies, bullets, screen, ufos, gates, blobs)
                            score += enemies_killed * 5  # Add points for kills
                            if should_reset:
                                bird.weapon = Weapon()
                            break
                        else:
                            # Normal bullet collision
                            if gate.hit(bullet.damage, current_time):
                                score += 5  # Bonus points for destroying a gate
                            if bullet in bullets:
                                bullets.remove(bullet)
                            break

                # Check enemy collisions if bullet didn't hit a gate
                for enemy in enemies[:]:
                    if bullet.get_rect().colliderect(enemy.get_rect()):
                        if bullet.weapon_type == WeaponType.NUKE and bullet == bird.active_nuke:
                            # Auto-detonate nuke on enemy collision
                            should_reset, enemies_killed = bird.detonate_nuke(enemies, bullets, screen, ufos, gates, blobs)
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

            # Update blobs
            for blob in blobs[:]:
                blob.update()

                # Check collision with player
                if bird.get_rect().colliderect(blob.get_rect()):
                    blob.flash()  # Flash when hitting player
                    if bird.take_hit(current_time):
                        game_over_sound.play()
                        game_state = GAME_OVER
                    continue

                # Check tentacle collisions with player
                for tentacle_rect in blob.get_tentacle_rects():
                    if bird.get_rect().colliderect(tentacle_rect):
                        blob.flash()  # Flash when hitting player with tentacles
                        if bird.take_hit(current_time):
                            game_over_sound.play()
                            game_state = GAME_OVER
                        break

                # Check bullet collisions
                for bullet in bullets[:]:
                    if bullet.get_rect().colliderect(blob.get_rect()):
                        blob.flash()  # Flash when hit by bullet
                        if bullet.weapon_type == WeaponType.NUKE and bullet == bird.active_nuke:
                            should_reset, enemies_killed = bird.detonate_nuke(enemies, bullets, screen, ufos, gates, blobs)
                            score += enemies_killed * 5
                            if should_reset:
                                bird.weapon = Weapon()
                        else:
                            blob.health -= bullet.damage
                            ufo_hit_sound.play()
                            if blob.health <= 0:
                                blobs.remove(blob)
                                score += 10
                                ufo_death_sound.play()
                                # Spawn powerup when blob dies
                                powerup_type = random.choice([
                                    PowerUpType.SHIELD,
                                    PowerUpType.SPREAD,
                                    PowerUpType.LASER,
                                    PowerUpType.CHARGE,
                                    PowerUpType.NUKE  # Include NUKE in blob's drops
                                ])
                                powerups.append(PowerUp(powerup_type, blob.x, blob.y))
                            bullets.remove(bullet)
                        break

        # Draw
        screen.fill(bg_color)  # Use level background color

        # Draw stars first (before everything else)
        for star in stars:
            star.update()
            star.draw(screen)

        if game_state == MENU:
            draw_message(screen, "Space Flapper", -80)
            draw_message(screen, "Press SPACE to Start", -40)
            draw_message(screen, "X to Shoot, SPACE to Flap", 0)
        else:
            # Draw game elements
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

            # Draw blobs
            for blob in blobs:
                blob.draw(screen)

            # Draw UI elements last so they're always on top
            font = pygame.font.Font(None, 36)

            # Draw score in top left
            score_text = font.render(f'Score: {score}', True, WHITE)
            screen.blit(score_text, (10, 10))

            # Draw high score in top right
            high_score_text = font.render(f'High Score: {high_score}', True, WHITE)
            high_score_rect = high_score_text.get_rect()
            high_score_rect.topright = (SCREEN_WIDTH - 10, 10)
            screen.blit(high_score_text, high_score_rect)

            # Draw weapon info if not using default weapon
            if bird.weapon.type != WeaponType.DEFAULT:
                font = pygame.font.Font(None, 24)
                # Draw ammo count
                ammo_text = f"Ammo: {bird.weapon.ammo}"
                ammo_surface = font.render(ammo_text, True, WHITE)
                screen.blit(ammo_surface, (10, 40))

                # Draw weapon type
                weapon_text = f"Weapon: {bird.weapon.type.name}"
                weapon_surface = font.render(weapon_text, True, WHITE)
                screen.blit(weapon_surface, (10, 70))

            if game_state == GAME_OVER:
                draw_message(screen, "Game Over!", -20)
                draw_message(screen, "Press SPACE to Play Again", 20)

        pygame.display.flip()
        clock.tick(60)

        # Add music handling for game state changes
        if game_state == PLAYING and pygame.mixer.get_busy():
            title_music.stop()  # Stop title music when game starts

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
