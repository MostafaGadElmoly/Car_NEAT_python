import pygame
import math
import sys
import neat
import colors
import os

screen_width = 1500
screen_height = 800
table_width = 400
table_height = 200

generation = 0

car_size_X = 80
car_size_Y = 80

border_color = (255, 255, 255, 255)

class Car:
    def __init__(self):
        self.surface = pygame.image.load("car.png")
        self.surface = pygame.transform.scale(self.surface, (car_size_X, car_size_Y))  # Used variable for car size
        self.rotate_surface = self.surface

        self.pos = [700, 650]  # Starting Position
        self.angle = 0
        self.speed = 0

        self.center = [self.pos[0] + car_size_X // 2, self.pos[1] + car_size_Y // 2]  

        self.radars = []
        self.radars_for_draw = []

        self.is_alive = True
        self.goal = False

        self.distance = 0 # Distance Driven
        self.time_spent = 0 # Time Passed

        self.speed_set = False  # Flag for speed later

    def draw(self, screen):
        screen.blit(self.rotate_surface, self.pos)  # Draw Car
        self.draw_radar(screen)  # DRAW SENSORS

    def draw_radar(self, screen):
        for radar in self.radars:
            pos, dist = radar
            pygame.draw.line(screen, (0, 255, 0), self.center, pos, 1)
            pygame.draw.circle(screen, (0, 255, 0), pos, 5)

    def check_collision(self, map):
        self.is_alive = True
        for point in self.four_points:
            if map.get_at((int(point[0]), int(point[1]))) == border_color:
                self.is_alive = False
                break

    def check_radar(self, degree, map):
        len = 0
        x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * len)
        y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * len)

        # While We Don't Hit BORDER AND length < 300 (just a max) -> go further and further
        while not map.get_at((x, y)) == border_color and len < 300:
            len = len + 1
            x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * len)
            y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * len)
        # Calculate Distance To Border And Append To Radars List
        dist = int(math.sqrt(math.pow(x - self.center[0], 2) + math.pow(y - self.center[1], 2)))
        self.radars.append([(x, y), dist])

    def update(self, map):
        # check speed
        # Set The Speed To 20 For The First Time
        # Only When Having 4 Output Nodes With Speed Up and Down, This Can be figured in the Config File.

        if not self.speed_set:
            self.speed = 10
            self.speed_set = True

        # check position
        self.rotate_surface = self.rot_center(self.surface, self.angle)

        self.pos[0] += math.cos(math.radians(360 - self.angle)) * self.speed
        if self.pos[0] < 20:
            self.pos[0] = 20
        elif self.pos[0] > screen_width - 120:
            self.pos[0] = screen_width - 120

        # Increase Distance and Time
        self.distance += self.speed
        self.time_spent += 1

        self.pos[1] += math.sin(math.radians(360 - self.angle)) * self.speed
        if self.pos[1] < 20:
            self.pos[1] = 20
        elif self.pos[1] > screen_height - 120:
            self.pos[1] = screen_height - 120

        # calculate the Center
        self.center = [int(self.pos[0]) + car_size_X // 2, int(self.pos[1]) + car_size_Y // 2]  # Adjusted for car size

        # calculate 4 collision points
        len = 0.5 * car_size_X
        left_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 30))) * len,
                    self.center[1] + math.sin(math.radians(360 - (self.angle + 30))) * len]
        right_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 150))) * len,
                     self.center[1] + math.sin(math.radians(360 - (self.angle + 150))) * len]
        left_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 210))) * len,
                       self.center[1] + math.sin(math.radians(360 - (self.angle + 210))) * len]
        right_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 330))) * len,
                        self.center[1] + math.sin(math.radians(360 - (self.angle + 330))) * len]
        self.four_points = [left_top, right_top, left_bottom, right_bottom]

        # Check Collisions And Clear Radar
        self.check_collision(map)
        self.radars.clear()

        # From -90 To 120 With Step-Size 45 Check Radar
        for d in range(-90, 120, 45):
            self.check_radar(d, map)

    def get_data(self):
        radars = self.radars
        ret = [0, 0, 0, 0, 0]
        for i, r in enumerate(radars):
            ret[i] = int(r[1] / 30)

        return ret

    def get_alive(self):
        return self.is_alive

    # Calculate Reward
    def get_reward(self):
        distance_reward = self.distance / 50.0  # Reward based on distance traveled
        speed_reward = self.speed / 5.0  # Reward based on speed (adjust scaling factor as needed)
        total_reward = distance_reward + speed_reward  # Combine rewards
        return total_reward

    def rot_center(self, image, angle):
        orig_rect = image.get_rect()
        rot_image = pygame.transform.rotate(image, angle)
        rot_rect = orig_rect.copy()
        rot_rect.center = rot_image.get_rect().center
        rot_image = rot_image.subsurface(rot_rect).copy()
        return rot_image

def run_car(genomes, config):

    # Init NEAT as Empty Collections For Nets and Cars
    nets = []
    cars = []

    for id, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        g.fitness = 0

        # Init cars
        cars.append(Car())

    # Init my game
    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))

    # Clock Settings
    # Font Settings & Loading Map
    clock = pygame.time.Clock()
    generation_font = pygame.font.SysFont("Arial", 40)
    font = pygame.font.SysFont("Arial", 20)
    map = pygame.image.load('map2.png')

    # Main loop
    global generation
    generation += 1

    counter = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)

        # Input my data and get result from network
        for index, car in enumerate(cars):
            output = nets[index].activate(car.get_data())
            action = output.index(max(output))
            if action == 0:
                car.angle += 10  # > Go left
            elif action == 1:
                car.angle -= 10  # >> Go Right
            elif action == 2:
                if (car.speed - 2 >= 12):
                    car.speed -= 2  # Slow_Down
            else:
                car.speed += 2  # Speed Up

        # Update car and fitness
        remain_cars = 0
        for i, car in enumerate(cars):
            if car.get_alive():
                remain_cars += 1
                car.update(map)
                genomes[i][1].fitness += car.get_reward()

        # check
        if remain_cars == 0:
            break


        counter += 1
        if counter == 30 * 40:
            break

        # Drawing
        screen.blit(map, (0, 0))
        for car in cars:
            if car.get_alive():
                car.draw(screen)

        text = generation_font.render("Generation : " + str(generation), True, (0, 0, 0))
        text_rect = text.get_rect()
        text_rect.center = (screen_width / 2, 50)
        screen.blit(text, text_rect)

        text = font.render("remain cars : " + str(remain_cars), True, (0, 0, 0))
        text_rect = text.get_rect()
        text_rect.center = (screen_width / 2 +500, 50)
        screen.blit(text, text_rect)

        pygame.display.flip()
        clock.tick(0)

def draw_info_table(info_window, generation, remain_cars, time_passed, cars_not_made_it):
    info_window.fill(colors.white)

    # Render text
    font = pygame.font.SysFont("Arial", 24)
    text_generation = font.render("Generation: " + str(generation), True, colors.black)
    text_remain_cars = font.render("Cars Alive: " + str(remain_cars), True, colors.black)
    text_time_passed = font.render("Time Passed: " + str(time_passed), True, colors.black)
    text_cars_not_made_it = font.render("Cars Didn't Make It: " + str(cars_not_made_it), True, colors.black)

    # Blit text to info window
    info_window.blit(text_generation, (20, 20))
    info_window.blit(text_remain_cars, (20, 50))
    info_window.blit(text_time_passed, (20, 80))
    info_window.blit(text_cars_not_made_it, (20, 110))

    # Update the display
    pygame.display.flip()

if __name__ == "__main__":
    # Set configuration file
    config_path = "./config-feedforward.txt"
    config = neat.config.Config(neat.DefaultGenome,
                                neat.DefaultReproduction,
                                neat.DefaultSpeciesSet,
                                neat.DefaultStagnation, 
                                config_path)

    # Create core evolution algorithm class
    #p = neat.Population(config)
    # Get configuration of the check point
    p = neat.Checkpointer.restore_checkpoint("neat-checkpoint-139")

    # Statistical result
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    #Check Points
    p.add_reporter(neat.Checkpointer(10))

    # Run NEAT
    p.run(run_car, 1000)
