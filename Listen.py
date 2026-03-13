import logging
import numpy as np
import pyaudio
import assemblyai as aai
from threading import Thread, Event
from queue import Queue, Empty
from assemblyai.streaming.v3 import (
    BeginEvent,
    StreamingClient,
    StreamingClientOptions,
    StreamingError,
    StreamingEvents,
    StreamingParameters,
    TerminationEvent,
    TurnEvent,
)
from typing import Type

SAMPLE_RATE = 16000
CHUNK_SIZE = 3200  # 200ms chunks


class ListenInterface:
    last_statement = ""
    interim_stmt = ""

    def __init__(self, energy_threshold=100):
        self.api_key = "ca7dba3ab4c5408fb843ed43228ec057"
        self.energy_threshold = energy_threshold
        self._stop_event = Event()
        self._audio_queue = Queue(maxsize=5)  # small max size - old chunks get dropped
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _mic_capture_thread(self):
        """Runs in its own thread - just captures mic and puts in queue."""
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
            input_device_index=2,
        )
        try:
            while not self._stop_event.is_set():
                raw_audio = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                if self._audio_queue.full():
                    try:
                        self._audio_queue.get_nowait()  # discard oldest chunk
                    except Empty:
                        pass
                self._audio_queue.put(raw_audio)
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

    def _processed_audio_stream(self):
        """Generator that drains the queue and applies energy gating."""
        silence = np.zeros(CHUNK_SIZE, dtype=np.int16).tobytes()
        while not self._stop_event.is_set():
            try:
                raw_audio = self._audio_queue.get(timeout=0.5)
            except Empty:
                continue

            audio_data = np.frombuffer(raw_audio, dtype=np.int16)
            energy = np.abs(audio_data).mean()
            #print(f"energy: {energy:.1f}")

            if energy > self.energy_threshold:
                yield raw_audio
            else:
                yield silence

    def begin_listen(self):
        self._stop_event.clear()

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
                sample_rate=SAMPLE_RATE,
                format_turns=True,
            )
        )

        # Thread 1: captures mic into queue
        self.mic_thread = Thread(target=self._mic_capture_thread, daemon=True)
        self.mic_thread.start()

        # Thread 2: drains queue and streams to AssemblyAI
        def start_streaming():
            try:
                self.client.stream(self._processed_audio_stream())
            finally:
                self.client.disconnect(terminate=True)

        self.streaming_thread = Thread(target=start_streaming, daemon=True)
        self.streaming_thread.start()

    def clear(self):
        self.last_statement = ""

    def get_statement(self):
        return self.last_statement

    def get_interim(self):
        return self.interim_stmt

    def close(self):
        self._stop_event.set()
        self.mic_thread.join(timeout=3)
        self.streaming_thread.join(timeout=3)

    def on_begin(self, client: Type[StreamingClient], event: BeginEvent):
        print(f"Session started: {event.id}")

    def on_turn(self, client: Type[StreamingClient], event: TurnEvent):
        print(f"{event.transcript} ({event.end_of_turn})")
        self.interim_stmt = event.transcript
        if event.end_of_turn and not event.turn_is_formatted:
            self.last_statement = event.transcript

    def on_terminated(self, client: Type[StreamingClient], event: TerminationEvent):
        print(f"Session terminated: {event.audio_duration_seconds} seconds of audio processed")

    def on_error(self, client: Type[StreamingClient], error: StreamingError):
        print(f"Error occurred: {error}")


def main():
    listener = ListenInterface(energy_threshold=500)
    listener.begin_listen()

    try:
        while True:
            statement = listener.get_statement()
            if statement:
                print(f"Heard: {statement}")
                listener.clear()
    except KeyboardInterrupt:
        pass
    finally:
        listener.close()
        print("closed")


if __name__ == "__main__":
    main()
