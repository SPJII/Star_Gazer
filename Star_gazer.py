import pygame
import math
import random
import sys
import sqlite3
import os

# Initialize pygame
pygame.init()

# Set the application icon
try:
    icon_image = pygame.image.load('gfx/icon/Star_gaver_icon.ico')  # Ensure the path is correct
    pygame.display.set_icon(icon_image)
except pygame.error:
    print("Warning: Icon image not found. Continuing without setting an icon.")

# Get the display information
display_info = pygame.display.Info()
monitor_width = display_info.current_w
monitor_height = display_info.current_h


# Define screen size to fit the monitor (leave space for taskbar and window decorations)
taskbar_space = 80  # Leave some space at the bottom and top
screen_width = monitor_width
screen_height = monitor_height - taskbar_space

# Set up the screen
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Star Gazer")

# Delete menu variables
delete_menu_active = False
delete_menu_rect = pygame.Rect(400, 150, 400, 500)  # Similar to load_menu_rect
delete_menu_scroll = 0
delete_menu_scroll_max = 0
delete_menu_scroll_speed = 20
delete_files = []
confirming_delete = False
file_to_delete = None  # Holds the file to delete

# Yes/No buttons for delete confirmation
yes_button = pygame.Rect(400, 660, 100, 50)
no_button = pygame.Rect(700, 660, 100, 50)

# Function to delete a file safely
def delete_file(filename):
    try:
        os.remove(filename)
        print(f"Deleted file '{filename}'.")
        update_load_files()
        update_delete_files()
        update_save_files()
    except Exception as e:
        print(f"Error deleting file {filename}: {e}")

# Define colors
black = (0, 0, 0)
yellow = (255, 255, 0)  # Sun color
white = (255, 255, 255)
dark_navy = (10, 10, 50)  # Dark navy background color
light_gray = (200, 200, 200)
dark_gray = (50, 50, 50)
red = (255, 0, 0)
dark_red = (150, 0, 0)
green = (0, 255, 0)

# Star colors for starfield
star_colors = [
    (255, 240, 240),  # white-pink
    (240, 151, 231),  # white-blue
    (250, 225, 100),  # white-yellow
    (95, 255, 255)    # white-cyan
]

# Get the sun position (mutable for camera movement)
sun_pos = [screen_width // 2, screen_height // 2]

# Define stars for the starfield background
num_stars = 30000  # Larger starfield
starfield_width = screen_width * 12
starfield_height = screen_height * 12 # Expand farther south
stars = []
for _ in range(num_stars):
    x = random.randint(-starfield_width, starfield_width)
    y = random.randint(-starfield_height, starfield_height)
    speed = random.uniform(0.1, 0.3)  # Slow-moving stars
    color = random.choice(star_colors)  # Randomly choose a star color
    stars.append([x, y, speed, color])

# Moon class
class Moon:
    def __init__(self, planet_x, planet_y, moon_distance, moon_size, moon_speed, color):
        self.planet_x = planet_x
        self.planet_y = planet_y
        self.moon_distance = moon_distance
        self.moon_size = moon_size
        self.moon_speed = moon_speed
        self.moon_angle = random.uniform(0, 2 * math.pi)  # Random initial angle
        self.color = color

    def update(self, planet_x, planet_y, paused):
        # Update the moon's position based on the planet's position
        self.planet_x = planet_x
        self.planet_y = planet_y
        if not paused:
            self.moon_angle += self.moon_speed

    def draw(self, surface, zoom_factor):
        # Only show moons if zoom factor is sufficiently zoomed in
        if zoom_factor >= 0.02:
            # Calculate moon position using circular orbit
            moon_x = self.planet_x + int(math.cos(self.moon_angle) * self.moon_distance * zoom_factor)
            moon_y = self.planet_y + int(math.sin(self.moon_angle) * self.moon_distance * zoom_factor)
            moon_size = max(1, int(self.moon_size * zoom_factor))  # Ensure moons are visible, but smaller
            pygame.draw.circle(surface, self.color, (moon_x, moon_y), moon_size)

# Asteroid class
class Asteroid:
    def __init__(self, belt_id, belt_radius_inner, belt_radius_outer, belt_speed_min, belt_speed_max, color):
        self.belt_id = belt_id
        self.angle = random.uniform(0, 2 * math.pi)
        self.distance = random.uniform(belt_radius_inner, belt_radius_outer)
        self.speed = random.uniform(belt_speed_min, belt_speed_max)
        self.color = color
        self.size = random.randint(1, 3)

    def update(self, paused):
        if not paused:
            self.angle += self.speed

    def draw(self, surface, zoom_factor, camera_x, camera_y):
        asteroid_x = sun_pos[0] + int(math.cos(self.angle) * self.distance * zoom_factor) + camera_x
        asteroid_y = sun_pos[1] + int(math.sin(self.angle) * self.distance * zoom_factor) + camera_y
        pygame.draw.circle(surface, self.color, (asteroid_x, asteroid_y), max(1, int(self.size * zoom_factor)))

# Darker color function for rings
def darker_shade(color):
    return tuple(max(0, int(c * 0.6)) for c in color)

# Lighter color function for the space between the planet and the ring system
def lighter_shade(color):
    return tuple(min(255, int(c * 1.2)) for c in color)

# Fill the space between the planet and the ring system with a translucent lighter color
def fill_translucent_space_between_planet_and_ring(surface, planet_x, planet_y, planet_size, farthest_moon_distance, planet_color, zoom_factor):
    # Create a surface for translucent drawing
    translucent_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    lighter_color = lighter_shade(planet_color)
    # Draw the translucent filled circle for the space between the planet and the start of the ring
    pygame.draw.circle(translucent_surface, (*lighter_color, 100), (planet_x, planet_y), int(farthest_moon_distance * zoom_factor))
    surface.blit(translucent_surface, (0, 0))  # Blit the translucent surface to the main surface

# Ring system as thick as the farthest moon from the planet
def draw_ring_system(surface, planet_x, planet_y, farthest_moon_distance, planet_color, zoom_factor):
    # Draw a ring system around the planet with thickness equal to the farthest moon's distance
    ring_color = darker_shade(planet_color)
    pygame.draw.circle(surface, ring_color, (planet_x, planet_y), int(farthest_moon_distance * zoom_factor), 10)

# Global variables for celestial bodies
planet_radius = []
planet_colors = []
planet_sizes = []
planet_orbital_speeds = []
planet_angles = []
moons = []
has_rings = []
farthest_moons = []
main_belt_asteroids = []
kuiper_belt_asteroids = []
asteroid_belts = []
sun_radius = 0

# Function to generate our solar system
def generate_our_solar_system():
    global planet_radius, planet_colors, planet_sizes, planet_orbital_speeds, planet_angles
    global moons, has_rings, farthest_moons, main_belt_asteroids, kuiper_belt_asteroids, sun_radius, asteroid_belts

    # Clear existing celestial bodies
    planet_radius = []
    planet_colors = []
    planet_sizes = []
    planet_orbital_speeds = []
    planet_angles = []
    moons = []
    has_rings = []
    farthest_moons = []
    main_belt_asteroids = []
    kuiper_belt_asteroids = []
    asteroid_belts = []
    asteroid_id_counter = 0

    # Define real solar system data (simplified and scaled for visualization)
    earth_radius = 27  # Base size for Earth's radius
    sun_radius = 109 * earth_radius  # Sun is about 109 times Earth's radius

    # Planetary data (name, size relative to Earth, distance in AU, color, number of moons)
    planets_data = [
        # (Name, Size, Distance, Color, Number of Moons)
        ("Mercury", 0.38, 0.39, (169, 169, 169), 0),
        ("Venus", 0.95, 0.72, (245, 245, 160), 0),
        ("Earth", 1.0, 1.0, (70, 130, 180), 1),
        ("Mars", 0.53, 1.52, (188, 39, 50), 2),
        ("Jupiter", 11.21, 5.2, (210, 105, 30), 79),
        ("Saturn", 9.45, 9.58, (248, 222, 126), 62),
        ("Uranus", 4.01, 19.2, (173, 216, 230), 27),
        ("Neptune", 3.88, 30.05, (0, 0, 139), 14),
    ]

    # Orbit scaling factor
    orbit_scaling_factor = 10000

    for data in planets_data:
        name, size_factor, au, color, num_moons = data
        planet_radius.append(int(au * orbit_scaling_factor))
        planet_sizes.append(size_factor * earth_radius)
        planet_colors.append(color)
        orbital_speed = 0.02 / math.sqrt(au)
        planet_orbital_speeds.append(orbital_speed)
        planet_angles.append(random.uniform(0, 2 * math.pi))

        # Moons
        planet_moons = []
        moon_distances = []
        has_rings.append(False)  # We'll set rings separately
        planet_size = size_factor * earth_radius

        # Assign moons based on planet name
        if name in ["Jupiter", "Saturn"]:
            num_moons_assigned = random.randint(60, 100)
        elif name in ["Uranus", "Neptune"]:
            num_moons_assigned = random.randint(5, 20)
        elif name in ["Mars"]:
            num_moons_assigned = 2
        elif name in ["Earth"]:
            num_moons_assigned = 1
        else:  # Mercury and Venus
            num_moons_assigned = 0

        for _ in range(min(num_moons_assigned, 100)):  # Limit to 100 for performance
            moon_size = random.randint(2, int(planet_size * 0.2))
            if num_moons_assigned > 0:
                min_safe_distance = planet_size + 10
                upper_bound = max(int(min_safe_distance) + 50, 150)
                moon_distance = max(moon_distances[-1] + 20 if moon_distances else min_safe_distance,
                                    random.randint(int(min_safe_distance), upper_bound))
                moon_distances.append(moon_distance)
                moon_speed = random.uniform(0.02, 0.05)
                moon_color = white
                moon = Moon(0, 0, moon_distance, moon_size, moon_speed, moon_color)
                planet_moons.append(moon)
        moons.append(planet_moons)
        farthest_moons.append(max(moon_distances) if moon_distances else 0)

    # Add rings to Saturn
    has_rings[5] = True  # Saturn has rings

    # Main Asteroid Belt between Mars and Jupiter
    num_main_belt_asteroids = 500
    belt_radius_inner = planet_radius[3] + 5000
    belt_radius_outer = planet_radius[4] - 5000
    belt_speed_min = 0.004
    belt_speed_max = 0.008
    asteroid_color = (169, 169, 169)

    asteroid_belts.append({
        'belt_id': 0,
        'belt_radius_inner': belt_radius_inner,
        'belt_radius_outer': belt_radius_outer,
        'belt_speed_min': belt_speed_min,
        'belt_speed_max': belt_speed_max,
        'color': asteroid_color
    })

    for _ in range(num_main_belt_asteroids):
        asteroid = Asteroid(0, belt_radius_inner, belt_radius_outer, belt_speed_min, belt_speed_max, asteroid_color)
        main_belt_asteroids.append(asteroid)

    # Kuiper Belt beyond Neptune
    num_kuiper_belt_asteroids = 1000
    kuiper_belt_radius_inner = planet_radius[-1] + 10000
    kuiper_belt_radius_outer = kuiper_belt_radius_inner + 50000
    kuiper_belt_speed_min = 0.002
    kuiper_belt_speed_max = 0.004
    kuiper_asteroid_color = (200, 200, 200)

    asteroid_belts.append({
        'belt_id': 1,
        'belt_radius_inner': kuiper_belt_radius_inner,
        'belt_radius_outer': kuiper_belt_radius_outer,
        'belt_speed_min': kuiper_belt_speed_min,
        'belt_speed_max': kuiper_belt_speed_max,
        'color': kuiper_asteroid_color
    })

    for _ in range(num_kuiper_belt_asteroids):
        asteroid = Asteroid(1, kuiper_belt_radius_inner, kuiper_belt_radius_outer, kuiper_belt_speed_min, kuiper_belt_speed_max, kuiper_asteroid_color)
        kuiper_belt_asteroids.append(asteroid)

# Function to generate a random solar system
def generate_solar_system():
    global planet_radius, planet_colors, planet_sizes, planet_orbital_speeds, planet_angles
    global moons, has_rings, farthest_moons, main_belt_asteroids, kuiper_belt_asteroids, sun_radius, asteroid_belts

    # Clear existing celestial bodies
    planet_radius = []
    planet_colors = []
    planet_sizes = []
    planet_orbital_speeds = []
    planet_angles = []
    moons = []
    has_rings = []
    farthest_moons = []
    main_belt_asteroids = []
    kuiper_belt_asteroids = []
    asteroid_belts = []

    # Base sizes
    earth_radius = random.randint(20, 30)  # Random base size for Earth-like planet
    sun_radius = random.randint(90, 120) * earth_radius  # Sun is 90-120 times Earth's radius

    # Generate a random number of planets between 3 and 11
    num_planets = random.randint(3, 11)

    # Generate planet properties
    # Use realistic values scaled for visualization
    orbit_scaling_factor = 12000  # Adjust for better visualization
    base_au = 0.4  # Starting point for the first planet
    au_increment = 0.3  # Increment of AU for each subsequent planet

    for i in range(num_planets):
        # Distance from the sun
        au = base_au + au_increment * i + random.uniform(-0.1, 0.1)  # Add some randomness
        planet_radius.append(int(au * orbit_scaling_factor))

        # Planet size proportional to Earth's size
        size_factor = random.uniform(0.5, 11.0)  # Size factor from 0.5 to 11 times Earth
        planet_sizes.append(size_factor * earth_radius)

        # Planet color
        color = (
            random.randint(50, 255),
            random.randint(50, 255),
            random.randint(50, 255)
        )
        planet_colors.append(color)

        # Orbital speed inversely proportional to distance
        orbital_speed = 0.02 / math.sqrt(au)
        planet_orbital_speeds.append(orbital_speed)

        # Initial angle
        planet_angles.append(random.uniform(0, 2 * math.pi))

    # Generate moons for each planet based on size
    for i in range(num_planets):
        planet_moons = []
        moon_distances = []

        # Assign moons based on planet size
        size_factor = planet_sizes[i] / earth_radius  # Relative to Earth
        if size_factor >= 8:
            num_moons_assigned = random.randint(60, 100)
        elif 5 <= size_factor < 8:
            num_moons_assigned = random.randint(5, 20)
        elif 1 <= size_factor < 5:
            num_moons_assigned = random.randint(0, 2)
        else:
            num_moons_assigned = 0

        # Determine if the planet has rings (larger planets more likely)
        if size_factor > 5 and random.random() < 0.7:
            has_rings.append(True)
        else:
            has_rings.append(False)

        planet_size = planet_sizes[i]
        for _ in range(num_moons_assigned):
            moon_size = random.randint(2, int(planet_size * 0.2))
            if num_moons_assigned > 0:
                min_safe_distance = planet_size + 10
                upper_bound = max(int(min_safe_distance) + 50, 150)
                moon_distance = max(moon_distances[-1] + 20 if moon_distances else min_safe_distance,
                                    random.randint(int(min_safe_distance), upper_bound))
                moon_distances.append(moon_distance)
                moon_speed = random.uniform(0.02, 0.05)
                moon_color = white
                moon = Moon(0, 0, moon_distance, moon_size, moon_speed, moon_color)
                planet_moons.append(moon)
        moons.append(planet_moons)
        farthest_moons.append(max(moon_distances) if moon_distances else 0)

    # Generate asteroid belts if applicable
    if num_planets >= 5:
        # Main Asteroid Belt between planets 3 and 4
        num_main_belt_asteroids = 500
        belt_radius_inner = planet_radius[2] + 5000
        belt_radius_outer = planet_radius[3] - 5000
        belt_speed_min = 0.004
        belt_speed_max = 0.008
        asteroid_color = (169, 169, 169)

        asteroid_belts.append({
            'belt_id': 0,
            'belt_radius_inner': belt_radius_inner,
            'belt_radius_outer': belt_radius_outer,
            'belt_speed_min': belt_speed_min,
            'belt_speed_max': belt_speed_max,
            'color': asteroid_color
        })

        for _ in range(num_main_belt_asteroids):
            asteroid = Asteroid(0, belt_radius_inner, belt_radius_outer, belt_speed_min, belt_speed_max, asteroid_color)
            main_belt_asteroids.append(asteroid)

    if num_planets >= 8:
        # Kuiper Belt beyond the last planet
        num_kuiper_belt_asteroids = 1000
        kuiper_belt_radius_inner = planet_radius[-1] + 10000
        kuiper_belt_radius_outer = kuiper_belt_radius_inner + 50000
        kuiper_belt_speed_min = 0.002
        kuiper_belt_speed_max = 0.004
        kuiper_asteroid_color = (200, 200, 200)

        asteroid_belts.append({
            'belt_id': 1,
            'belt_radius_inner': kuiper_belt_radius_inner,
            'belt_radius_outer': kuiper_belt_radius_outer,
            'belt_speed_min': kuiper_belt_speed_min,
            'belt_speed_max': kuiper_belt_speed_max,
            'color': kuiper_asteroid_color
        })

        for _ in range(num_kuiper_belt_asteroids):
            asteroid = Asteroid(1, kuiper_belt_radius_inner, kuiper_belt_radius_outer, kuiper_belt_speed_min, kuiper_belt_speed_max, kuiper_asteroid_color)
            kuiper_belt_asteroids.append(asteroid)

# Function to save the solar system
def save_solar_system(filename):
    try:
        conn = sqlite3.connect(filename)
        c = conn.cursor()

        # Create tables
        c.execute('''CREATE TABLE IF NOT EXISTS planets
                     (id INTEGER PRIMARY KEY, size REAL, distance REAL, color TEXT, angle REAL, orbital_speed REAL, has_rings INTEGER)''')
        c.execute('''CREATE TABLE IF NOT EXISTS moons
                     (planet_id INTEGER, size REAL, distance REAL, speed REAL, color TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS asteroid_belts
                     (belt_id INTEGER PRIMARY KEY, belt_radius_inner REAL, belt_radius_outer REAL, belt_speed_min REAL, belt_speed_max REAL, color TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS asteroids
                     (belt_id INTEGER, angle REAL, distance REAL, speed REAL, color TEXT, size INTEGER)''')

        # Clear existing data
        c.execute('DELETE FROM planets')
        c.execute('DELETE FROM moons')
        c.execute('DELETE FROM asteroid_belts')
        c.execute('DELETE FROM asteroids')

        # Save planets
        for i in range(len(planet_radius)):
            color_str = ','.join(map(str, planet_colors[i]))
            c.execute('INSERT INTO planets VALUES (?, ?, ?, ?, ?, ?, ?)', (
                i, planet_sizes[i], planet_radius[i], color_str, planet_angles[i], planet_orbital_speeds[i], int(has_rings[i])))

            # Save moons
            for moon in moons[i]:
                moon_color_str = ','.join(map(str, moon.color))
                c.execute('INSERT INTO moons VALUES (?, ?, ?, ?, ?)', (
                    i, moon.moon_size, moon.moon_distance, moon.moon_speed, moon_color_str))

        # Save asteroid belts
        for belt in asteroid_belts:
            color_str = ','.join(map(str, belt['color']))
            c.execute('INSERT INTO asteroid_belts VALUES (?, ?, ?, ?, ?, ?)', (
                belt['belt_id'], belt['belt_radius_inner'], belt['belt_radius_outer'], belt['belt_speed_min'], belt['belt_speed_max'], color_str))

        # Save asteroids
        for asteroid in main_belt_asteroids + kuiper_belt_asteroids:
            color_str = ','.join(map(str, asteroid.color))
            c.execute('INSERT INTO asteroids VALUES (?, ?, ?, ?, ?, ?)', (
                asteroid.belt_id, asteroid.angle, asteroid.distance, asteroid.speed, color_str, asteroid.size))

        conn.commit()
        conn.close()
        print(f"Solar system saved successfully to '{filename}'.")
    except Exception as e:
        print(f"Error saving solar system: {e}")

# Function to load the solar system
def load_solar_system(filename):
    try:
        conn = sqlite3.connect(filename)
        c = conn.cursor()

        # Load planets
        c.execute('SELECT * FROM planets')
        planet_data = c.fetchall()

        # Clear existing celestial bodies
        planet_radius.clear()
        planet_colors.clear()
        planet_sizes.clear()
        planet_orbital_speeds.clear()
        planet_angles.clear()
        moons.clear()
        has_rings.clear()
        farthest_moons.clear()
        main_belt_asteroids.clear()
        kuiper_belt_asteroids.clear()
        asteroid_belts.clear()

        for data in planet_data:
            i, size, distance, color_str, angle, orbital_speed, ring_flag = data
            color = tuple(map(int, color_str.split(',')))
            planet_sizes.append(size)
            planet_radius.append(distance)
            planet_colors.append(color)
            planet_angles.append(angle)
            planet_orbital_speeds.append(orbital_speed)
            has_rings.append(bool(ring_flag))
            moons.append([])
            farthest_moons.append(0)

        # Load moons
        c.execute('SELECT * FROM moons')
        moon_data = c.fetchall()
        for data in moon_data:
            planet_id, size, distance, speed, color_str = data
            color = tuple(map(int, color_str.split(',')))
            moon = Moon(0, 0, distance, size, speed, color)
            moons[planet_id].append(moon)
            if distance > farthest_moons[planet_id]:
                farthest_moons[planet_id] = distance

        # Load asteroid belts
        c.execute('SELECT * FROM asteroid_belts')
        belt_data = c.fetchall()
        for data in belt_data:
            belt_id, belt_radius_inner, belt_radius_outer, belt_speed_min, belt_speed_max, color_str = data
            color = tuple(map(int, color_str.split(',')))
            belt = {
                'belt_id': belt_id,
                'belt_radius_inner': belt_radius_inner,
                'belt_radius_outer': belt_radius_outer,
                'belt_speed_min': belt_speed_min,
                'belt_speed_max': belt_speed_max,
                'color': color
            }
            asteroid_belts.append(belt)

        # Load asteroids
        c.execute('SELECT * FROM asteroids')
        asteroid_data = c.fetchall()
        for data in asteroid_data:
            belt_id, angle, distance, speed, color_str, size = data
            color = tuple(map(int, color_str.split(',')))
            asteroid = Asteroid(belt_id, 0, 0, 0, 0, color)
            asteroid.angle = angle
            asteroid.distance = distance
            asteroid.speed = speed
            asteroid.size = size
            if belt_id == 0:
                main_belt_asteroids.append(asteroid)
            elif belt_id == 1:
                kuiper_belt_asteroids.append(asteroid)

        conn.close()
        print(f"Solar system loaded successfully from '{filename}'.")
    except Exception as e:
        print(f"Error loading solar system: {e}")

# Function to center text on a button
def center_text(text, button_rect, font, color):
    text_surf = font.render(text, True, color)
    text_rect = text_surf.get_rect(center=button_rect.center)
    return text_surf, text_rect

# Function to check if the user clicked on a planet
def check_object_clicked(mouse_x, mouse_y, object_x, object_y, object_radius):
    distance = math.hypot(mouse_x - object_x, mouse_y - object_y)
    return distance <= object_radius

# Function to reset camera to default position and zoom
def reset_camera():
    global camera_x, camera_y, zoom_factor, zoom_target, camera_locked, locked_object
    camera_x, camera_y = default_camera_x, default_camera_y
    zoom_factor = default_zoom
    zoom_target = default_zoom
    camera_locked = False
    locked_object = None

# Initial solar system generation
generate_our_solar_system()

# Zoom functionality
default_zoom = 0.002  # Default zoom level
zoom_factor = default_zoom
zoom_target = zoom_factor  # Target zoom for smooth transitions
zoom_min = 0.001  # Minimum zoom level (allows zooming in much closer)
zoom_max = 0.25    # Maximum zoom level (prevents excessive zooming out)

# Camera movement variables
default_camera_x, default_camera_y = 0, 0  # Default camera position
camera_x, camera_y = default_camera_x, default_camera_y  # Track camera position
camera_speed = 15  # Increased speed for faster movement
camera_boundary = 250000  # Increased camera boundary to accommodate Kuiper Belt

# Mouse control variables
mouse_dragging = False
mouse_last_x, mouse_last_y = None, None

# Zoom control variables
mouse_zoom_position = None

# Camera locking variables
camera_locked = False
locked_object = None  # Track which object (planet) the camera is locked on

# Buttons for pausing and playing
pause_play_button = pygame.Rect(50, 50, 200, 50)  # Play/Pause toggle button
icon_button = pygame.Rect(270, 50, 300, 50)  # Wider button for toggling icons
reset_button = pygame.Rect(590, 50, 200, 50)  # Reset Camera button
generate_button = pygame.Rect(810, 50, 400, 50)  # Generate Solar System button (wider)

# Buttons for saving, loading, and deleting
save_button = pygame.Rect(1220, 50, 100, 50)  # Save button
load_button = pygame.Rect(1330, 50, 100, 50)  # Load button
delete_button = pygame.Rect(1440, 50, 100, 50)  # Delete button

font = pygame.font.SysFont(None, 40)

# Toggle for planet icons and play/pause state
planet_icons_enabled = True  # Start with icons enabled
is_paused = False  # Initial state of movement (not paused)

# Reset button feedback timer
reset_button_clicked = False
reset_click_time = 0

# Input box for filenames
input_active = False
input_text = ''
input_box = pygame.Rect(400, 300, 400, 50)
input_action = None  # 'save', 'load', or 'delete'

# Load menu variables
load_menu_active = False
load_menu_rect = pygame.Rect(400, 150, 400, 500)  # Increased height
load_menu_scroll = 0
load_menu_scroll_max = 0
load_menu_scroll_speed = 20
load_files = []

# Delete menu variables
delete_menu_active = False
delete_menu_rect = pygame.Rect(400, 150, 400, 500)  # Similar to load_menu_rect
delete_menu_scroll = 0
delete_menu_scroll_max = 0
delete_menu_scroll_speed = 20
delete_files = []

# Save menu variables
save_menu_active = False
save_menu_rect = pygame.Rect(400, 150, 400, 500)  # Similar to other menus
save_menu_scroll = 0
save_menu_scroll_max = 0
save_menu_scroll_speed = 20
save_files = []

# Cursor variables for blinking
cursor_visible = True
cursor_timer = 0
cursor_interval = 500  # milliseconds
last_cursor_toggle = pygame.time.get_ticks()

# Function to update the list of .db files for the load menu
def update_load_files():
    global load_files, load_menu_scroll, load_menu_scroll_max
    load_files = [f for f in os.listdir('.') if f.endswith('.db')]
    load_menu_scroll = 0
    load_menu_scroll_max = max(0, (len(load_files) * 60) - (load_menu_rect.height - 60))  # 60 is the height per file entry

# Function to update the list of .db files for the delete menu
def update_delete_files():
    global delete_files, delete_menu_scroll, delete_menu_scroll_max
    delete_files = [f for f in os.listdir('.') if f.endswith('.db')]
    delete_menu_scroll = 0
    delete_menu_scroll_max = max(0, (len(delete_files) * 60) - (delete_menu_rect.height - 60))  # 60 is the height per file entry

# Function to update the list of .db files for the save menu
def update_save_files():
    global save_files, save_menu_scroll, save_menu_scroll_max
    save_files = [f for f in os.listdir('.') if f.endswith('.db')]
    save_menu_scroll = 0
    save_menu_scroll_max = max(0, (len(save_files) * 60) - (save_menu_rect.height - 160))  # Adjusted for input box

# Function to delete a file safely
def delete_file(filename):
    try:
        os.remove(filename)
        print(f"Deleted file '{filename}'.")
        update_load_files()
        update_delete_files()
        update_save_files()
    except Exception as e:
        print(f"Error deleting file {filename}: {e}")

# Function to center text on a button
def center_text(text, button_rect, font, color):
    text_surf = font.render(text, True, color)
    text_rect = text_surf.get_rect(center=button_rect.center)
    return text_surf, text_rect

# Function to check if the user clicked on a planet
def check_object_clicked(mouse_x, mouse_y, object_x, object_y, object_radius):
    distance = math.hypot(mouse_x - object_x, mouse_y - object_y)
    return distance <= object_radius

# Function to reset camera to default position and zoom
def reset_camera():
    global camera_x, camera_y, zoom_factor, zoom_target, camera_locked, locked_object
    camera_x, camera_y = default_camera_x, default_camera_y
    zoom_factor = default_zoom
    zoom_target = default_zoom
    camera_locked = False
    locked_object = None

# Initialize load, delete, and save files
update_load_files()
update_delete_files()
update_save_files()

# Initialize delete confirmation variables
confirming_delete = False
file_to_delete = None

# Define Yes and No buttons for delete confirmation
yes_button = pygame.Rect(delete_menu_rect.x + 100, delete_menu_rect.y + delete_menu_rect.height - 100, 100, 50)
no_button = pygame.Rect(delete_menu_rect.x + delete_menu_rect.width - 200, delete_menu_rect.y + delete_menu_rect.height - 100, 100, 50)

# Main loop
running = True
clock = pygame.time.Clock()
while running:
    screen.fill(dark_navy)  # Fill the screen with dark navy background

    # Adaptive zoom control
    if camera_locked:
        zoom_delta_in = 0.02  # Slower zooming in when locked onto an object
        zoom_delta_out = 0.02  # Faster zooming out when locked onto an object
    else:
        zoom_delta_in = 0.002  # Default zooming in rate
        zoom_delta_out = 0.001  # Default zooming out rate

    # Smooth zooming towards target
    zoom_factor += (zoom_target - zoom_factor) * 0.1
    zoom_factor = max(zoom_min, min(zoom_factor, zoom_max))  # Clamp zoom_factor within limits

    # Handle events (zoom, camera movement, and button clicks)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if input_active:
                if event.key == pygame.K_RETURN:
                    filename = input_text.strip()
                    if input_action == 'save':
                        if filename:
                            full_filename = filename + '.db' if not filename.endswith('.db') else filename
                            if os.path.exists(full_filename):
                                # Open a confirmation menu within the main loop
                                confirming_delete = False  # Not deleting, just saving
                                save_confirmation = True  # Flag for save confirmation if needed
                                # For simplicity, proceed with saving without confirmation
                                save_solar_system(full_filename)
                            else:
                                save_solar_system(full_filename)
                        else:
                            print("Please enter a valid filename.")
                    input_active = False
                    input_text = ''
                    input_action = None
                    save_menu_active = False
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    input_active = False
                    input_text = ''
                    input_action = None
                    save_menu_active = False
                else:
                    input_text += event.unicode
            else:
                if event.key == pygame.K_SPACE:
                    is_paused = not is_paused  # Toggle pause/play with spacebar
                elif event.key == pygame.K_ESCAPE:
                    # Close any active menu when Esc is pressed
                    if save_menu_active:
                        save_menu_active = False
                        input_active = False
                        input_action = None
                    if load_menu_active:
                        load_menu_active = False
                    if delete_menu_active:
                        delete_menu_active = False
                    if confirming_delete:
                        confirming_delete = False
                        file_to_delete = None

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos

            if input_active:
                # Ignore other clicks when input is active
                if not input_box.collidepoint(mouse_x, mouse_y):
                    input_active = False  # Allow deselecting input box by clicking outside
                continue

            # Check if the mouse click is on any button
            if pause_play_button.collidepoint(mouse_x, mouse_y):
                is_paused = not is_paused  # Toggle play/pause, doesn't break camera lock
            elif icon_button.collidepoint(mouse_x, mouse_y):
                planet_icons_enabled = not planet_icons_enabled  # Toggle planet icons, doesn't break camera lock
            elif reset_button.collidepoint(mouse_x, mouse_y):
                reset_camera()  # Reset camera to default position and zoom
                reset_button_clicked = True
                reset_click_time = pygame.time.get_ticks()
            elif generate_button.collidepoint(mouse_x, mouse_y):
                generate_solar_system()  # Generate a new solar system
                reset_camera()  # Reset camera after generation
                # Flash the button for 1/4th second to indicate the action
                pygame.draw.rect(screen, white, generate_button, border_radius=15)
                generate_text, generate_rect = center_text("Generate Solar System", generate_button, font, black)
                screen.blit(generate_text, generate_rect)
                pygame.display.flip()
                pygame.time.wait(250)  # Wait for 1/4th second
            elif save_button.collidepoint(mouse_x, mouse_y):
                if save_menu_active:
                    # Close the save menu if it's already open
                    save_menu_active = False
                    input_active = False
                    input_action = None
                else:
                    save_menu_active = True
                    load_menu_active = False  # Ensure only one menu is active at a time
                    delete_menu_active = False
                    input_active = True
                    input_action = 'save'
                    input_text = ''
                    update_save_files()
            elif load_button.collidepoint(mouse_x, mouse_y):
                if load_menu_active:
                    load_menu_active = False
                else:
                    load_menu_active = True
                    save_menu_active = False  # Ensure only one menu is active at a time
                    delete_menu_active = False
                    update_load_files()
            elif delete_button.collidepoint(mouse_x, mouse_y):
                if delete_menu_active:
                    delete_menu_active = False
                else:
                    delete_menu_active = True
                    save_menu_active = False
                    load_menu_active = False
                    confirming_delete = False
                    file_to_delete = None
                    update_delete_files()
            elif save_menu_active and save_menu_rect.collidepoint(mouse_x, mouse_y):
                # Check if the click is on the input box
                if save_menu_rect.x + 20 <= mouse_x <= save_menu_rect.x + 20 + save_menu_rect.width - 40 and \
                   save_menu_rect.y + 60 <= mouse_y <= save_menu_rect.y + 60 + 50:
                    input_active = True
                    input_action = 'save'
                else:
                    # Calculate relative position inside the file list
                    relative_y = mouse_y - (save_menu_rect.y + 120) + save_menu_scroll
                    index = relative_y // 60  # 60 is the height per file entry
                    if 0 <= index < len(save_files):
                        # Load the selected solar system
                        filename = save_files[index]
                        try:
                            load_solar_system(filename)
                            reset_camera()
                            save_menu_active = False
                        except Exception as e:
                            print("Error loading solar system:", e)
            elif load_menu_active and load_menu_rect.collidepoint(mouse_x, mouse_y):
                # Calculate relative position inside the inner list
                relative_y = mouse_y - (load_menu_rect.y + 60) + load_menu_scroll
                index = relative_y // 60  # 60 is the height per file entry
                if 0 <= index < len(load_files):
                    # Load the selected solar system
                    filename = load_files[index]
                    try:
                        load_solar_system(filename)
                        reset_camera()
                        load_menu_active = False
                    except Exception as e:
                        print("Error loading solar system:", e)
            elif delete_menu_active and delete_menu_rect.collidepoint(mouse_x, mouse_y):
                if confirming_delete:
                    # Check if Yes or No button is clicked
                    if yes_button.collidepoint(mouse_x, mouse_y):
                        delete_file(file_to_delete)  # Proceed with the deletion
                        confirming_delete = False
                        file_to_delete = None
                    elif no_button.collidepoint(mouse_x, mouse_y):
                        confirming_delete = False  # Cancel the delete operation
                        file_to_delete = None
                else:
                    # Calculate relative position inside the inner list
                    relative_y = mouse_y - (delete_menu_rect.y + 60) + delete_menu_scroll
                    index = relative_y // 60  # 60 is the height per file entry
                    if 0 <= index < len(delete_files):
                        # Set the file to delete and activate confirmation
                        file_to_delete = delete_files[index]
                        confirming_delete = True
            else:
                if event.button == 1:  # Left mouse button starts dragging or selects an object
                    # Only check for planets
                    clicked_on_planet = False
                    for i in range(len(planet_radius)):
                        planet_x = sun_pos[0] + int(math.cos(planet_angles[i]) * planet_radius[i] * zoom_factor) + camera_x
                        planet_y = sun_pos[1] + int(math.sin(planet_angles[i]) * planet_radius[i] * zoom_factor) + camera_y

                        # Allow clicking on planet icons
                        if (zoom_factor <= 0.02 and planet_icons_enabled and
                                check_object_clicked(mouse_x, mouse_y, planet_x, planet_y, 5)):
                            camera_locked = True
                            locked_object = i
                            clicked_on_planet = True
                            break
                        elif check_object_clicked(mouse_x, mouse_y, planet_x, planet_y, planet_sizes[i] * zoom_factor):
                            camera_locked = True
                            locked_object = i  # Lock camera to this planet
                            clicked_on_planet = True
                            break
                    if not clicked_on_planet:
                        # Unlock camera if user clicks on empty space
                        camera_locked = False
                        locked_object = None
                        # Start dragging
                        mouse_dragging = True
                        mouse_last_x, mouse_last_y = event.pos

                # Check for zoom events (scroll)
                if event.button == 4:  # Scroll up (zoom in)
                    if load_menu_active:
                        load_menu_scroll = max(0, load_menu_scroll - load_menu_scroll_speed)
                    elif delete_menu_active and not confirming_delete:
                        delete_menu_scroll = max(0, delete_menu_scroll - delete_menu_scroll_speed)
                    elif save_menu_active:
                        save_menu_scroll = max(0, save_menu_scroll - save_menu_scroll_speed)
                    else:
                        zoom_target = max(zoom_min, zoom_target - zoom_delta_in)
                elif event.button == 5:  # Scroll down (zoom out)
                    if load_menu_active:
                        load_menu_scroll = min(load_menu_scroll_max, load_menu_scroll + load_menu_scroll_speed)
                    elif delete_menu_active and not confirming_delete:
                        delete_menu_scroll = min(delete_menu_scroll_max, delete_menu_scroll + delete_menu_scroll_speed)
                    elif save_menu_active:
                        save_menu_scroll = min(save_menu_scroll_max, save_menu_scroll + save_menu_scroll_speed)
                    else:
                        zoom_target = min(zoom_max, zoom_target + zoom_delta_out)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Stop dragging on mouse button release
                mouse_dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if mouse_dragging and not camera_locked:  # Move camera with mouse drag only if not locked
                dx, dy = event.pos[0] - mouse_last_x, event.pos[1] - mouse_last_y
                camera_x += dx
                camera_y += dy
                mouse_last_x, mouse_last_y = event.pos

    keys = pygame.key.get_pressed()
    if not camera_locked and not input_active and not load_menu_active and not delete_menu_active and not save_menu_active:
        # Allow camera movement if no menu is active
        if keys[pygame.K_w] and camera_y < camera_boundary:  # Move camera down
            camera_y += camera_speed
        if keys[pygame.K_s] and camera_y > -camera_boundary:  # Move camera up
            camera_y -= camera_speed
        if keys[pygame.K_a] and camera_x < camera_boundary:  # Move camera right
            camera_x += camera_speed
        if keys[pygame.K_d] and camera_x > - camera_boundary:  # Move camera left
            camera_x -= camera_speed

    # Lock the camera on a planet if selected
    if camera_locked and locked_object is not None:
        planet_x = sun_pos[0] + int(math.cos(planet_angles[locked_object]) * planet_radius[locked_object] * zoom_factor)
        planet_y = sun_pos[1] + int(math.sin(planet_angles[locked_object]) * planet_radius[locked_object] * zoom_factor)
        camera_x = -(planet_x - screen_width // 2)
        camera_y = -(planet_y - screen_height // 2)

    # Draw the starfield
    for star in stars:
        pygame.draw.circle(screen, star[3], (int(star[0]) + camera_x, int(star[1]) + camera_y), 2)
        star[0] += star[2]  # Move stars horizontally for visual effect

    # Draw orbit rings with transparency
    orbit_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)  # Surface for transparent orbits
    for distance_from_sun in planet_radius:
        pygame.draw.circle(orbit_surface, (255, 255, 255, 50), (sun_pos[0] + camera_x, sun_pos[1] + camera_y),
                           int(distance_from_sun * zoom_factor), 1)
    screen.blit(orbit_surface, (0, 0))

    # Draw the sun
    pygame.draw.circle(screen, yellow, (sun_pos[0] + camera_x, sun_pos[1] + camera_y),
                       max(1, int(sun_radius * zoom_factor)))

    # Draw asteroid belts
    for asteroid in main_belt_asteroids:
        asteroid.update(is_paused)
        asteroid.draw(screen, zoom_factor, camera_x, camera_y)

    for asteroid in kuiper_belt_asteroids:
        asteroid.update(is_paused)
        asteroid.draw(screen, zoom_factor, camera_x, camera_y)

    # Draw planets, update their position, and draw moons
    for i in range(len(planet_radius)):
        planet_angle = planet_angles[i]
        distance_from_sun = planet_radius[i]

        # Calculate planet position using circular orbit (cosine and sine)
        planet_x = sun_pos[0] + int(math.cos(planet_angle) * distance_from_sun * zoom_factor) + camera_x
        planet_y = sun_pos[1] + int(math.sin(planet_angle) * distance_from_sun * zoom_factor) + camera_y

        # Planet icons override normal zoom behavior
        if zoom_factor <= 0.02 and planet_icons_enabled:
            pygame.draw.circle(screen, planet_colors[i], (planet_x, planet_y), 5)  # Draw colored icon for planet
        else:
            # Fill the translucent space between planet and ring system first
            if has_rings[i] and farthest_moons[i] > 0:
                fill_translucent_space_between_planet_and_ring(screen, planet_x, planet_y, planet_sizes[i],
                                                               farthest_moons[i], planet_colors[i], zoom_factor)

            # Draw the planet with size scaling based on distance from the sun
            planet_size = planet_sizes[i]
            pygame.draw.circle(screen, planet_colors[i], (planet_x, planet_y),
                               max(1, int(planet_size * zoom_factor)))

            # Draw ring system after the planet (to ensure it's on top)
            if has_rings[i] and farthest_moons[i] > 0:
                draw_ring_system(screen, planet_x, planet_y, farthest_moons[i], planet_colors[i], zoom_factor)

        # Update the angle for the next frame (orbiting)
        if not is_paused:
            planet_angles[i] += planet_orbital_speeds[i]

        # Update and draw moons
        for moon in moons[i]:
            moon.update(planet_x, planet_y, is_paused)
            moon.draw(screen, zoom_factor)

    # Draw play/pause button
    if is_paused:
        pygame.draw.rect(screen, white, pause_play_button, border_radius=15)
        play_pause_text, play_pause_rect = center_text("Play", pause_play_button, font, black)
    else:
        pygame.draw.rect(screen, black, pause_play_button, border_radius=15)
        play_pause_text, play_pause_rect = center_text("Pause", pause_play_button, font, white)
    screen.blit(play_pause_text, play_pause_rect)

    # Draw the icon toggle button with updated colors
    if planet_icons_enabled:
        pygame.draw.rect(screen, black, icon_button, border_radius=15)
        icon_text, icon_rect = center_text("Disable Planet Icons", icon_button, font, white)
    else:
        pygame.draw.rect(screen, white, icon_button, border_radius=15)
        icon_text, icon_rect = center_text("Enable Planet Icons", icon_button, font, black)
    screen.blit(icon_text, icon_rect)

    # Handle reset button visual feedback
    if reset_button_clicked:
        elapsed_time = pygame.time.get_ticks() - reset_click_time
        if elapsed_time <= 500:  # Half a second
            pygame.draw.rect(screen, white, reset_button, border_radius=15)
            reset_text, reset_rect = center_text("Reset Camera", reset_button, font, black)
        else:
            reset_button_clicked = False
            pygame.draw.rect(screen, black, reset_button, border_radius=15)
            reset_text, reset_rect = center_text("Reset Camera", reset_button, font, white)
    else:
        pygame.draw.rect(screen, black, reset_button, border_radius=15)
        reset_text, reset_rect = center_text("Reset Camera", reset_button, font, white)
    screen.blit(reset_text, reset_rect)

    # Draw the generate solar system button
    pygame.draw.rect(screen, black, generate_button, border_radius=15)
    generate_text, generate_rect = center_text("Generate Solar System", generate_button, font, white)
    screen.blit(generate_text, generate_rect)

    # Draw the save button
    if save_menu_active:
        pygame.draw.rect(screen, white, save_button, border_radius=15)
        save_text, save_rect = center_text("Save", save_button, font, black)
    else:
        pygame.draw.rect(screen, black, save_button, border_radius=15)
        save_text, save_rect = center_text("Save", save_button, font, white)
    screen.blit(save_text, save_rect)

    # Draw the load button
    if load_menu_active:
        pygame.draw.rect(screen, white, load_button, border_radius=15)
        load_text, load_rect = center_text("Load", load_button, font, black)
    else:
        pygame.draw.rect(screen, black, load_button, border_radius=15)
        load_text, load_rect = center_text("Load", load_button, font, white)
    screen.blit(load_text, load_rect)

    # Draw the delete button
    if delete_menu_active and not confirming_delete:
        pygame.draw.rect(screen, white, delete_button, border_radius=15)
        delete_text, delete_rect = center_text("Delete", delete_button, font, black)
    else:
        pygame.draw.rect(screen, black, delete_button, border_radius=15)
        delete_text, delete_rect = center_text("Delete", delete_button, font, white)
    screen.blit(delete_text, delete_rect)

    # Draw save menu if active
    if save_menu_active:
        # Draw outer rectangle with rounded corners
        pygame.draw.rect(screen, black, save_menu_rect, border_radius=20)

        # Draw title centered
        title_surface = font.render("Save Game", True, white)
        title_rect = title_surface.get_rect(center=(save_menu_rect.centerx, save_menu_rect.y + 30))
        screen.blit(title_surface, title_rect)

        # Draw input box
        input_box_rect = pygame.Rect(save_menu_rect.x + 20, save_menu_rect.y + 60, save_menu_rect.width - 40, 50)
        pygame.draw.rect(screen, white, input_box_rect, border_radius=10)
        input_text_surface = font.render(input_text, True, black)
        screen.blit(input_text_surface, (input_box_rect.x + 10, input_box_rect.y + 10))

        # Calculate cursor position
        cursor_x = input_box_rect.x + 10 + input_text_surface.get_width() + 2
        cursor_y = input_box_rect.y + 10
        cursor_height = input_text_surface.get_height()

        # Toggle cursor visibility based on timer
        current_time = pygame.time.get_ticks()
        if current_time - last_cursor_toggle >= cursor_interval:
            cursor_visible = not cursor_visible
            last_cursor_toggle = current_time

        if cursor_visible and input_active:
            pygame.draw.line(screen, black, (cursor_x, cursor_y), (cursor_x, cursor_y + cursor_height), 2)

        # Draw existing files
        inner_rect = pygame.Rect(save_menu_rect.x + 20, save_menu_rect.y + 120, save_menu_rect.width - 40, save_menu_rect.height - 140)
        pygame.draw.rect(screen, dark_gray, inner_rect, border_radius=10)

        # Clip the drawing area to the inner rectangle
        clip_rect = inner_rect.copy()
        screen.set_clip(clip_rect)

        # Draw files
        for idx, filename in enumerate(save_files):
            y = inner_rect.y + idx * 60 - save_menu_scroll
            file_rect = pygame.Rect(inner_rect.x + 20, y + 10, inner_rect.width - 40, 40)
            if file_rect.bottom < inner_rect.y or file_rect.top > inner_rect.y + inner_rect.height:
                continue  # Skip drawing files outside the visible area

            # Draw the file rectangle
            pygame.draw.rect(screen, black, file_rect, border_radius=5)

            # Draw the filename text
            filename_text = font.render(filename, True, white)
            screen.blit(filename_text, (file_rect.x + 10, file_rect.y + 5))

        # Remove clipping
        screen.set_clip(None)

        # Draw scrollbar if needed
        if save_menu_scroll_max > 0:
            scrollbar_height = inner_rect.height * inner_rect.height / (inner_rect.height + save_menu_scroll_max)
            scrollbar_y = inner_rect.y + (inner_rect.height - scrollbar_height) * save_menu_scroll / save_menu_scroll_max
            scrollbar_rect = pygame.Rect(inner_rect.x + inner_rect.width - 10, scrollbar_y, 10, scrollbar_height)
            pygame.draw.rect(screen, white, scrollbar_rect)

    # Draw load menu if active
    if load_menu_active:
        # Draw outer rectangle with rounded corners
        pygame.draw.rect(screen, black, load_menu_rect, border_radius=20)

        # Draw title centered
        title_surface = font.render("Load Game", True, white)
        title_rect = title_surface.get_rect(center=(load_menu_rect.centerx, load_menu_rect.y + 30))
        screen.blit(title_surface, title_rect)

        # Draw inner rectangle for file list
        inner_rect = pygame.Rect(load_menu_rect.x + 20, load_menu_rect.y + 60, load_menu_rect.width - 40, load_menu_rect.height - 80)
        pygame.draw.rect(screen, dark_gray, inner_rect, border_radius=10)

        # Clip the drawing area to the inner rectangle
        clip_rect = inner_rect.copy()
        screen.set_clip(clip_rect)

        # Draw files
        for idx, filename in enumerate(load_files):
            y = inner_rect.y + idx * 60 - load_menu_scroll
            file_rect = pygame.Rect(inner_rect.x + 20, y + 10, inner_rect.width - 40, 40)
            if file_rect.bottom < inner_rect.y or file_rect.top > inner_rect.y + inner_rect.height:
                continue  # Skip drawing files outside the visible area

            # Draw the file rectangle
            pygame.draw.rect(screen, black, file_rect, border_radius=5)

            # Draw the filename text
            filename_text = font.render(filename, True, white)
            screen.blit(filename_text, (file_rect.x + 10, file_rect.y + 5))

        # Remove clipping
        screen.set_clip(None)

        # Draw scrollbar if needed
        if load_menu_scroll_max > 0:
            scrollbar_height = inner_rect.height * inner_rect.height / (inner_rect.height + load_menu_scroll_max)
            scrollbar_y = inner_rect.y + (inner_rect.height - scrollbar_height) * load_menu_scroll / load_menu_scroll_max
            scrollbar_rect = pygame.Rect(inner_rect.x + inner_rect.width - 10, scrollbar_y, 10, scrollbar_height)
            pygame.draw.rect(screen, white, scrollbar_rect)

    # Draw delete menu if active
    if delete_menu_active:
        # Draw outer rectangle with rounded corners
        pygame.draw.rect(screen, black, delete_menu_rect, border_radius=20)

        # Draw title centered
        title_surface = font.render("Delete Game", True, white)
        title_rect = title_surface.get_rect(center=(delete_menu_rect.centerx, delete_menu_rect.y + 30))
        screen.blit(title_surface, title_rect)

        # Draw inner rectangle for file list
        inner_rect = pygame.Rect(delete_menu_rect.x + 20, delete_menu_rect.y + 60, delete_menu_rect.width - 40, delete_menu_rect.height - 160)
        pygame.draw.rect(screen, dark_gray, inner_rect, border_radius=10)

        # Clip the drawing area to the inner rectangle
        clip_rect = inner_rect.copy()
        screen.set_clip(clip_rect)

        # Draw files
        for idx, filename in enumerate(delete_files):
            y = inner_rect.y + idx * 60 - delete_menu_scroll
            file_rect = pygame.Rect(inner_rect.x + 20, y + 10, inner_rect.width - 40, 40)
            if file_rect.bottom < inner_rect.y or file_rect.top > inner_rect.y + inner_rect.height:
                continue  # Skip drawing files outside the visible area

            # Draw the file rectangle
            pygame.draw.rect(screen, black, file_rect, border_radius=5)

            # Draw the filename text
            filename_text = font.render(filename, True, white)
            screen.blit(filename_text, (file_rect.x + 10, file_rect.y + 5))

        # Remove clipping
        screen.set_clip(None)

        # Draw scrollbar if needed
        if delete_menu_scroll_max > 0:
            scrollbar_height = inner_rect.height * inner_rect.height / (inner_rect.height + delete_menu_scroll_max)
            scrollbar_y = inner_rect.y + (inner_rect.height - scrollbar_height) * delete_menu_scroll / delete_menu_scroll_max
            scrollbar_rect = pygame.Rect(inner_rect.x + inner_rect.width - 10, scrollbar_y, 10, scrollbar_height)
            pygame.draw.rect(screen, white, scrollbar_rect)

        # Draw confirmation buttons if a file is selected for deletion
        if confirming_delete and file_to_delete:
            # Draw Yes button
            if yes_button.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(screen, white, yes_button, border_radius=15)
                yes_text, yes_rect = center_text("Yes", yes_button, font, black)
            else:
                pygame.draw.rect(screen, black, yes_button, border_radius=15)
                yes_text, yes_rect = center_text("Yes", yes_button, font, white)
            screen.blit(yes_text, yes_rect)

            # Draw No button
            if no_button.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(screen, white, no_button, border_radius=15)
                no_text, no_rect = center_text("No", no_button, font, black)
            else:
                pygame.draw.rect(screen, black, no_button, border_radius=15)
                no_text, no_rect = center_text("No", no_button, font, white)
            screen.blit(no_text, no_rect)

    # Update the display
    pygame.display.flip()

    # Frame rate
    clock.tick(60)

# Quit pygame
pygame.quit()
sys.exit()