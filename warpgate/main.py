import os
import sys

# Add warpgate dir to path so all imports resolve cleanly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from constants import SCREEN_W, SCREEN_H, FPS
from engine.game import Game

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("WARPGATE: CHRONICLES OF THE 41ST MILLENNIUM")
    Game(screen).run()

if __name__ == "__main__":
    main()
