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
    BG_WIDTH, BG_HEIGHT = 1680, 1050
    
    def __init__(self):
        self.think_event = Event()
        self.walk_event = Event()
        self.talk_event = Event()
        self.idle_event = Event()
        events = (self.think_event,self.walk_event,self.talk_event,self.idle_event,)
        self.process = Process(target = self.run, args = events, daemon = True)

    def start(self):
            self.process.start()

    def end(self):
        self.process.terminate()
    
    def run(self,think,walk,talk,idle):
        animations = self.load_animations()
        current_state = BotStates.IDLE
        current_frame_index = 0

        cv2.namedWindow("Box Robot", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("Box Robot", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        while True:
            frames = animations.get(current_state, animations[BotStates.IDLE])
            if frames:
                frame = frames[current_frame_index]
                cv2.imshow("Box Robot", frame)
                current_frame_index = (current_frame_index + 1) % len(frames)
            key = cv2.waitKey(30) & 0xFF
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


    def load_animations(self):
        base_path = "faces"
        states = ["idle", "walking", "thinking", "talking"]
        animations = {}

        for state in states:
            folder = os.path.join(base_path, state)
            animations[state] = []

            if os.path.exists(folder):
                files = sorted([f for f in os.listdir(folder) if f.lower().endswith(".png")])
                for f in files:
                    img = Image.open(os.path.join(folder, f)).resize((self.BG_WIDTH, self.BG_HEIGHT))
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
