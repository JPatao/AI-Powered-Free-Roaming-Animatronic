import assemblyai as aai
from threading import Thread
from face_recog import FaceRecognition
from assemblyai.streaming.v3 import (
     BeginEvent,
    StreamingClient,
    StreamingClientOptions,
    StreamingError,
    StreamingEvents,
    StreamingParameters,
    StreamingSessionParameters,
    TerminationEvent,
    TurnEvent,
)
import logging
from typing import Type
import time

class ListenInterface:

    last_statement = ""
    interim_stmt = ""
    
    def __init__(self):
        self.api_key = "ca7dba3ab4c5408fb843ed43228ec057"
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def begin_listen(self):
        self.client = StreamingClient(
            StreamingClientOptions(
                api_key=self.api_key,
                api_host="streaming.assemblyai.com",
            )
        )
        self.client.on(StreamingEvents.Begin, self.on_begin)
        self.client.on(StreamingEvents.Turn, self.on_turn)
        self.client.on(StreamingEvents.Termination, self.on_terminated)
        self.client.on(StreamingEvents.Error, self.on_error)
        self.client.connect(
            StreamingParameters(
                sample_rate=16000,
                format_turns=True,
                auto_highlights=True
            )
        )
        # Start streaming in a background thread
        def start_streaming():
            try:
                self.client.stream(aai.extras.MicrophoneStream(sample_rate=16000))
            finally:
                self.client.disconnect(terminate=True)
        self.streaming_thread = Thread(target=start_streaming,daemon=True)
        self.streaming_thread.start()

    def clear(self):
        self.last_statement = ""

    def get_statement(self):
        return self.last_statement

    def get_interim(self):
        return self.interim_stmt

    def close(self):
        self.client.disconnect(terminate=True)
    
    def on_begin(self, client: Type[StreamingClient], event: BeginEvent):
        print(f"Session started: {event.id}")

    def on_turn(self, client: Type[StreamingClient], event: TurnEvent):
        print(f"{event.transcript} ({event.end_of_turn})")
        self.interim_stmt = event.transcript
        if event.end_of_turn and not event.turn_is_formatted:
            self.last_statement = event.transcript

    def on_terminated(self, client: Type[StreamingClient], event: TerminationEvent):
        print(
            f"Session terminated: {event.audio_duration_seconds} seconds of audio processed"
        )

    def on_error(self, client: Type[StreamingClient], error: StreamingError):
        print(f"Error occurred: {error}")


def main():
    listener = ListenInterface()
    listener.begin_listen();

if __name__ == "__main__":
    main()
