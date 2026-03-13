import wave
from piper import PiperVoice
from playsound3 import playsound

##syn_config = SynthesisConfig(
##    volume=0.5,  # half as loud
##    length_scale=2.0,  # twice as slow
##    noise_scale=1.0,  # more audio variation
##    noise_w_scale=1.0,  # more speaking variation
##    normalize_audio=False, # use raw audio from voice
##)
##voice.synthesize_wav(..., syn_config=syn_config)

##for chunk in voice.synthesize("This is a test string."):
##    print(chunk.sample_rate, chunk.sample_width, chunk.sample_channels,chunk.audio_int16_bytes)
##    set_audio_format(chunk.sample_rate, chunk.sample_width, chunk.sample_channels)
##    write_raw_data(chunk.audio_int16_bytes)

class SpeechInterface:
    def __init__(self):
        self.voice = PiperVoice.load("./en_US-hfc_male-medium.onnx")

    def say(self,text):
        with wave.open("temp.wav", "wb") as wav_file:
            self.voice.synthesize_wav(text, wav_file)
        playsound("temp.wav")
        

if __name__ == "__main__":
    speech = SpeechInterface()
    speech.say("Welcome to the world of speech synthesis!")
