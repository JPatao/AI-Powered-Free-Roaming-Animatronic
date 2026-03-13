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

BG_WIDTH, BG_HEIGHT = 2160, 1620 #1920, 1080

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

    def run(self, think, walk, talk, idle):
        # Fix: ensure DISPLAY is set for the subprocess on Linux
        if 'DISPLAY' not in os.environ:
            os.environ['DISPLAY'] = ':0'

        # Detect real screen size instead of hardcoding
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
                    img = Image.open(os.path.join(folder, f)).convert("RGB")

                    # Scale to fit screen (both up and down) preserving aspect ratio
                    scale = min(bg_width / img.width, bg_height / img.height)
                    new_w = int(img.width * scale)
                    new_h = int(img.height * scale)
                    img = img.resize((new_w, new_h), Image.LANCZOS)

                    # Paste centered on black canvas
                    background = Image.new("RGB", (bg_width, bg_height), (0, 0, 0))
                    offset_x = (bg_width - new_w) // 2
                    offset_y = (bg_height - new_h) // 2
                    background.paste(img, (offset_x, offset_y))

                    frame = cv2.cvtColor(np.array(background), cv2.COLOR_RGB2BGR)
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
