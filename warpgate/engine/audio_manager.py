import pygame
import os

class AudioManager:
    def __init__(self):
        self.enabled = True
        self.music_vol = 0.6
        self.sfx_vol = 0.8
        self._current_track = None
        self._sfx = {}
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        except Exception:
            self.enabled = False

    def play_music(self, track_id, loops=-1):
        if not self.enabled:
            return
        if track_id == self._current_track:
            return
        self._current_track = track_id
        # Procedurally generate a simple tone-based "music" loop
        self._play_generated_music(track_id, loops)

    def _play_generated_music(self, track_id, loops):
        try:
            import numpy as np
            sr = 44100
            dur = 4.0
            t = np.linspace(0, dur, int(sr * dur), endpoint=False)

            configs = {
                "title":    ([110, 138, 165], [0.3, 0.2, 0.15], 80),
                "worldmap": ([130, 173, 195], [0.25, 0.2, 0.15], 100),
                "town":     ([98,  123, 147], [0.2, 0.15, 0.1], 60),
                "battle":   ([220, 277, 330], [0.3, 0.25, 0.2], 140),
                "boss":     ([110, 146, 184], [0.35, 0.3, 0.25], 160),
                "dungeon":  ([73,  92,  110], [0.2, 0.15, 0.1], 70),
                "victory":  ([196, 246, 293], [0.3, 0.2, 0.15], 90),
                "gameover": ([65,  82,   98], [0.25, 0.15, 0.1], 50),
            }
            freqs, amps, bpm = configs.get(track_id, ([130, 196], [0.25, 0.2], 100))

            wave = np.zeros_like(t)
            for freq, amp in zip(freqs, amps):
                wave += amp * np.sin(2 * np.pi * freq * t)
            beat = bpm / 60.0
            envelope = 0.5 + 0.5 * np.sin(2 * np.pi * beat * t)
            wave *= envelope
            wave = (wave * 32767 / max(abs(wave).max(), 1)).astype(np.int16)
            stereo = np.column_stack([wave, wave])
            sound = pygame.sndarray.make_sound(stereo)
            pygame.mixer.music.stop()
            sound.set_volume(self.music_vol)
            sound.play(loops=loops)
        except Exception:
            pass

    def play_sfx(self, sfx_id):
        if not self.enabled:
            return
        try:
            import numpy as np
            sr = 44100
            configs = {
                "hit":      (440, 0.05, 0.4),
                "crit":     (880, 0.08, 0.3),
                "miss":     (200, 0.05, 0.2),
                "heal":     (660, 0.06, 0.5),
                "death":    (110, 0.10, 0.6),
                "cursor":   (330, 0.03, 0.1),
                "confirm":  (550, 0.04, 0.15),
                "cancel":   (220, 0.04, 0.15),
                "levelup":  (880, 0.08, 0.8),
                "chest":    (440, 0.05, 0.4),
                "door":     (150, 0.06, 0.3),
                "status":   (300, 0.05, 0.4),
                "perils":   (100, 0.12, 0.8),
                "fanfare":  (660, 0.1, 1.0),
            }
            freq, vol, dur = configs.get(sfx_id, (330, 0.05, 0.2))
            t = np.linspace(0, dur, int(sr * dur), endpoint=False)
            wave = vol * np.sin(2 * np.pi * freq * t)
            decay = np.exp(-3 * t / dur)
            wave *= decay
            wave = (wave * 32767).astype(np.int16)
            stereo = np.column_stack([wave, wave])
            sound = pygame.sndarray.make_sound(stereo)
            sound.set_volume(self.sfx_vol)
            sound.play()
        except Exception:
            pass

    def stop_music(self):
        if self.enabled:
            try:
                pygame.mixer.stop()
            except Exception:
                pass

    def stop_all(self):
        self.stop_music()
