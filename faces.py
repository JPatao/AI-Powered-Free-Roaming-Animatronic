import cv2
import os
import time
from multiprocessing import Process, Event
from PIL import Image
import numpy as np

class BotStates:
    IDLE = "idle"
    WALKING = "walking"
    THINKING = "thinking"
    TALKING = "talking"

class Face():
    def __init__(self):
        self.think_event = Event()
        self.walk_event = Event()
        self.talk_event = Event()
        self.idle_event = Event()
        events = (self.think_event, self.walk_event, self.talk_event, self.idle_event)
        self.process = Process(target=self.run, args=events, daemon=True)

    def start(self):
        self.process.start()

    def end(self):
        self.process.terminate()

    def get_screen_resolution(self):
        """Detect actual screen resolution at runtime."""
        try:
            # Try to get resolution from xrandr
            import subprocess
            output = subprocess.check_output(['xrandr']).decode()
            for line in output.splitlines():
                if '*' in line:  # current resolution has asterisk
                    res = line.strip().split()[0]
                    w, h = res.split('x')
                    return int(w), int(h)
        except Exception:
            pass
        # Fallback: open a temp window to detect screen size
        try:
            tmp = cv2.namedWindow("tmp", cv2.WINDOW_NORMAL)
            cv2.setWindowProperty("tmp", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            w = cv2.getWindowImageRect("tmp")[2]
            h = cv2.getWindowImageRect("tmp")[3]
            cv2.destroyWindow("tmp")
            if w > 0 and h > 0:
                return w, h
        except Exception:
            pass
        return 1920, 1080  # safe default

    def run(self, think, walk, talk, idle):
        # Fix: ensure DISPLAY is set for the subprocess on Linux
        if 'DISPLAY' not in os.environ:
            os.environ['DISPLAY'] = ':0'

        # Detect real screen size instead of hardcoding
        BG_WIDTH, BG_HEIGHT = self.get_screen_resolution()
        print(f"[Face] Using resolution: {BG_WIDTH}x{BG_HEIGHT}")

        animations = self.load_animations(BG_WIDTH, BG_HEIGHT)
        current_state = BotStates.IDLE
        current_frame_index = 0

        # Fix: create window BEFORE setting fullscreen property
        cv2.namedWindow("Box Robot", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("Box Robot", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        while True:
            frames = animations.get(current_state, animations[BotStates.IDLE])
            if frames:
                frame = frames[current_frame_index % len(frames)]
                cv2.imshow("Box Robot", frame)
                current_frame_index = (current_frame_index + 1) % len(frames)

            cv2.waitKey(1)  # Must be called to pump GUI events; keep it short

            if think.is_set():
                current_state = BotStates.THINKING
                current_frame_index = 0
                think.clear()
            elif walk.is_set():
                current_state = BotStates.WALKING
                current_frame_index = 0
                walk.clear()
            elif talk.is_set():
                current_state = BotStates.TALKING
                current_frame_index = 0
                talk.clear()
            elif idle.is_set():
                current_state = BotStates.IDLE
                current_frame_index = 0
                idle.clear()

            delay = 0.25 if current_state == BotStates.TALKING else 0.5
            time.sleep(delay)

        cv2.destroyAllWindows()

    def load_animations(self, bg_width, bg_height):
        base_path = "faces"
        states = ["idle", "walking", "thinking", "talking"]
        animations = {}
        for state in states:
            folder = os.path.join(base_path, state)
            animations[state] = []
            if os.path.exists(folder):
                files = sorted([f for f in os.listdir(folder) if f.lower().endswith(".png")])
                for f in files:
                    img = Image.open(os.path.join(folder, f)).resize((bg_width, bg_height))
                    frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                    animations[state].append(frame)
        return animations

if __name__ == "__main__":
    face = Face()
    face.start()
    while True:
        res = input()
        if res == "exit":
            face.end()
            break
        elif res == "think":
            face.think_event.set()
        elif res == "walk":
            face.walk_event.set()
        elif res == "talk":
            face.talk_event.set()
        elif res == "idle":
            face.idle_event.set()
        print("mainloop")