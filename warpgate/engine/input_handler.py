import pygame

class InputHandler:
    def __init__(self):
        self._pressed = set()
        self._just_pressed = set()
        self._just_released = set()

        self.keymap = {
            "up":     [pygame.K_UP,    pygame.K_w],
            "down":   [pygame.K_DOWN,  pygame.K_s],
            "left":   [pygame.K_LEFT,  pygame.K_a],
            "right":  [pygame.K_RIGHT, pygame.K_d],
            "confirm":[pygame.K_RETURN, pygame.K_z, pygame.K_SPACE],
            "cancel": [pygame.K_ESCAPE, pygame.K_x],
            "menu":   [pygame.K_ESCAPE],
            "fast":   [pygame.K_LSHIFT, pygame.K_RSHIFT],
        }

    def update(self, events):
        self._just_pressed.clear()
        self._just_released.clear()
        for event in events:
            if event.type == pygame.KEYDOWN:
                self._just_pressed.add(event.key)
                self._pressed.add(event.key)
            elif event.type == pygame.KEYUP:
                self._just_released.add(event.key)
                self._pressed.discard(event.key)

    def held(self, action):
        return any(k in self._pressed for k in self.keymap.get(action, []))

    def pressed(self, action):
        return any(k in self._just_pressed for k in self.keymap.get(action, []))

    def released(self, action):
        return any(k in self._just_released for k in self.keymap.get(action, []))

    def any_key_pressed(self):
        return bool(self._just_pressed)
