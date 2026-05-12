import pygame as pg
from settings import *

class Map:
    def __init__(self):
        self.scroll = 0
        self.speed = 2
        # Create a simple starfield or grid
        self.bg_color = BLACK

    def update(self):
        self.scroll += self.speed
        if self.scroll >= HEIGHT:
            self.scroll = 0

    def draw(self, screen):
        screen.fill(self.bg_color)
        # Draw two lines/rects to simulate scrolling
        pg.draw.line(screen, (40, 40, 40), (0, self.scroll), (WIDTH, self.scroll))
        pg.draw.line(screen, (40, 40, 40), (0, self.scroll - HEIGHT), (WIDTH, self.scroll - HEIGHT))