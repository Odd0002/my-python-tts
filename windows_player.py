import multiprocessing
import simpleaudio as sa
from pydub import AudioSegment
from pydub.playback import play


def main_winsound_loop(wav_audio_queue: multiprocessing.Queue):
    while True:
        audio = wav_audio_queue.get()
        audio_segment = AudioSegment.from_wav(audio)
        play(audio_segment)
        # wave_obj = sa.WaveObject.from_wave_read(audio)
        # wave_obj.play()
        