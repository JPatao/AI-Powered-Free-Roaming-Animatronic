import threading
from enum import Enum
from AI import AI_Interface
from Listen import ListenInterface
from faces import Face
from Speak import SpeechInterface
from Movement import walk
import bot_move
import squat_test
import random


ACTIVATION_PHRASES = ["hello robot"]
SHUTDOWN_PHRASES = ["stop robot"]


THINK_PHRASES = ["Hmmm", "Let me check!", "One moment, please.", "Good question."]

class States(Enum):
    IDLE = 0
    RECOGNIZE = 1
    LISTEN = 2
    THINK = 3
    SPEAK = 4
    GOODBYE = 5

class Animatronic:
    def __init__(self):
        self.state = States.IDLE
        self.ai = AI_Interface()
        self.listen = ListenInterface(energy_threshold = 2000)
        self.face = Face()
        self.face.start()
        self.listen.begin_listen()
        self.speak = SpeechInterface()

    def shutdown(self):
        self.face.end()
        self.listen.close()
    
    def process(self):
        self.cur_stmt = self.listen.get_statement()
        #print(self.statements)
        for shutdown in SHUTDOWN_PHRASES:
            if shutdown in self.cur_stmt:
                self.shutdown()
                return True
        
        match self.state:
            case States.IDLE:
                return self.process_idle()
            case States.LISTEN:
                return self.process_listen()
            case States.THINK:
                return self.process_think()
            case States.SPEAK:
                return self.process_speak()
            case States.GOODBYE:
                return self.process_goodbye()
            case _:
                print("default state")

    def process_idle(self):
        #print("idle")
        for activation in ACTIVATION_PHRASES:
            if activation in self.listen.get_interim():
                self.response = "Greetings! I’m Boxley. It’s lovely to meet you. Do you need assistance finding something today?"
                self.state = States.SPEAK
                self.face.talk_event.set()
                #bot_move.run_walk(steps = 4)
                squat_test.squat()

        
    def process_listen(self):
        print("listen")
        if "goodbye" in self.cur_stmt.lower():
            self.state = States.GOODBYE
        elif self.cur_stmt != "":
            self.last_statement = self.cur_stmt
            self.think_stmt = self.cur_stmt
            self.state = States.THINK
            self.face.think_event.set()
        #listen to statement, wait on end of sentence -> think
        
    def process_think(self):
        print("think")
        self.speak.say(random.choice(THINK_PHRASES))
        self.response = self.ai.prompt(self.think_stmt)
        self.state = States.SPEAK
        self.face.talk_event.set()
        #send statement to ai, wait on response -> speak or goodbye
        
    def process_speak(self):
        print("speak")
        self.speak.say(self.response)
        self.state = States.LISTEN
        self.listen.clear()
        self.face.idle_event.set()
        #Text to voice response, wait finish -> listen
        
    def process_goodbye(self):
        print("goodbye")
        self.speak.say("Goodbye! Have a great day!")
        self.ai.clear_history()
        self.state = States.IDLE
        self.face.walk_event.set()
        #say goodbye -> idle


if __name__ == "__main__":
    anim = Animatronic()
    try:
        while(True):
            if anim.process():
                break
    finally:
        anim.shutdown()
