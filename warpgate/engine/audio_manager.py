import pygame
import os

MUSIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "assets", "data", "audio", "music")


class AudioManager:
    """Music + SFX. Real audio files take priority; procedural tones are the
    universal fallback so the game is never silent.

    Drop OGG/MP3/WAV files into assets/data/audio/music/ named by track:
        title.ogg  worldmap.ogg  town.ogg  dungeon.ogg  boss.ogg
        victory.ogg  gameover.ogg
        battle.ogg  battle_2.ogg  battle_3.ogg ...
    Multiple files sharing a prefix (battle, battle_2, ...) form a playlist —
    battle music rotates through them, a different track each fight."""

    def __init__(self):
        self.enabled = True
        self.music_vol = 0.6
        self.sfx_vol = 0.8
        self._current_track = None
        self._current_sound = None   # generated-music Sound handle
        self._sfx = {}
        self._music_files = {}       # track_id -> [paths]
        self._battle_rotation = 0
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        except Exception:
            self.enabled = False
        self._scan_music_files()

    def _scan_music_files(self):
        if not os.path.isdir(MUSIC_DIR):
            return
        for f in sorted(os.listdir(MUSIC_DIR)):
            if not f.lower().endswith((".ogg", ".mp3", ".wav")):
                continue
            base = os.path.splitext(f)[0].lower()
            track = base.rstrip("0123456789").rstrip("_-")
            self._music_files.setdefault(track, []).append(os.path.join(MUSIC_DIR, f))

    # ── Music ────────────────────────────────────────────────────────────────

    def play_music(self, track_id, loops=-1):
        if not self.enabled:
            return
        # Battle music always (re)starts and rotates through its playlist;
        # every other track is left alone if it is already playing.
        if track_id != "battle" and track_id == self._current_track:
            return

        self._stop_current()
        self._current_track = track_id

        files = self._music_files.get(track_id)
        if files:
            if track_id == "battle":
                path = files[self._battle_rotation % len(files)]
                self._battle_rotation += 1
            else:
                path = files[0]
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(self.music_vol)
                pygame.mixer.music.play(loops)
                return
            except Exception:
                pass

        # Procedural fallback — battle rotates three generated themes
        gen_id = track_id
        if track_id == "battle":
            gen_id = f"battle{self._battle_rotation % 3}"
            self._battle_rotation += 1
        self._play_generated_music(gen_id, loops)

    def _stop_current(self):
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        if self._current_sound is not None:
            try:
                self._current_sound.stop()
            except Exception:
                pass
            self._current_sound = None

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
                # Three rotating battle themes: driving, martial, frantic
                "battle0":  ([220, 277, 330], [0.3, 0.25, 0.2], 140),
                "battle1":  ([196, 247, 294, 370], [0.28, 0.22, 0.18, 0.12], 152),
                "battle2":  ([165, 208, 262, 311], [0.32, 0.24, 0.16, 0.12], 128),
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
            sound.set_volume(self.music_vol)
            sound.play(loops=loops)
            self._current_sound = sound
        except Exception:
            pass

    # ── SFX ──────────────────────────────────────────────────────────────────

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
            self._stop_current()
            self._current_track = None

    def stop_all(self):
        self.stop_music()
        try:
            pygame.mixer.stop()
        except Exception:
            pass
