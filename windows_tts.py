from io import BytesIO

import time
import pyttsx3

from pydub import AudioSegment

#queue only used for queue.Empty type
import queue

import multiprocessing
tmp_file_path = "tmpFile.wav"

def windows_tts_main_loop(input_queue: multiprocessing.Queue, wav_audio_queue: multiprocessing.Queue):
    engine = pyttsx3.init() # object creation
    engine.setProperty('rate', 125)
    # voices = engine.getProperty('voices')
    # [print(voice.name) for voice in voices]

    def say_text(text: str):
        engine.save_to_file(text, tmp_file_path)
        engine.runAndWait()
        with open(tmp_file_path, 'rb') as fh:
            buf = BytesIO(fh.read())
            output_audio(buf)
        engine.stop() 

    def convert_mp3_to_wav(mp3_bytes: BytesIO) -> BytesIO:
        wav_fp = BytesIO()
        mono = AudioSegment.from_mp3(mp3_bytes)
        
        output = AudioSegment.from_mono_audiosegments(mono, mono)
        output = output.set_frame_rate(48000)
        output.export(wav_fp, format='wav')
        
        return wav_fp

    def output_audio(wav_data: BytesIO):
        wav_audio_queue.put(wav_data)
        print("Wrote Audio!")

    def handle_text(text: str):
        split_text = text.split(' ')
        if (split_text[0] == "!sr" and len(split_text) > 1):
            engine.setProperty('rate', int(split_text[1]))
            # say_text(' '.join(split_text[1:])
        else:
            say_text(text)

    while True:
        (tts_engine, text) = input_queue.get()
        if (tts_engine != "wintts"):
            input_queue.put((tts_engine, text))
            time.sleep(1)
            continue
        print("got text!")
        if len(text) > 0:
            handle_text(text)
            # mp3_bytes = get_tts_mp3(text)
            # wav_bytes = convert_mp3_to_wav(mp3_bytes)
            # output_audio(wav_bytes)
