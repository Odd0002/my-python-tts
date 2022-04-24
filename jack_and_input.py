import jack
import soundfile as sf
from collections import deque
import uuid
import random
from io import BytesIO

import copy 

from gtts import gTTS

from pydub import AudioSegment

#queue only used for queue.Empty type
import queue

import multiprocessing

languages = ['af', 'ar', 'bn', 'bs', 'ca', 'cs', 'cy', 'da', 'de', 'el', 'en-au', 'en-ca', 'en-gb', 'en-gh', 'en-ie', 'en-in', 'en-ng', 'en-nz', 'en-ph', 'en-tz', 'en-uk', 'en-us', 'en-za', 'en', 'eo', 'es-es', 'es-us', 'es', 'et', 'fi', 'fr-ca', 'fr-fr', 'fr', 'gu', 'hi', 'hr', 'hu', 'hy', 'id', 'is', 'it', 'ja', 'jw', 'km', 'kn', 'ko', 'la', 'lv', 'mk', 'ml', 'mr', 'my', 'ne', 'nl', 'no', 'pl', 'pt-br', 'pt-pt', 'pt', 'ro', 'ru', 'si', 'sk', 'sq', 'sr', 'su', 'sv', 'sw', 'ta', 'te', 'th', 'tl', 'tr', 'uk', 'ur', 'vi', 'zh-CN', 'zh-cn', 'zh-tw']
audio_data_queue = deque()
audio_data_queue_copy = deque()
is_paused = False

def main_loop(command_queue: multiprocessing.Queue, input_queue: multiprocessing.Queue):

    def xrun(delay):
        print("An xrun occured, increase JACK's period size?")

    def stop_callback(msg=''):
        if msg:
            print(msg)
        for port in client.outports:
            port.get_array().fill(0)
        raise jack.CallbackExit

    def clear_audio_buffer():
        for port in client.outports:
            port.get_array().fill(0)

    def process(frames):
        global is_paused
        global audio_data_queue
        if frames != blocksize:
            stop_callback('blocksize must not be changed, I quit!')

        # Command handling
        try:
            command = command_queue.get_nowait()

            if command == "TOGGLE_PAUSE":
                is_paused = not is_paused

            elif command == "CLEAR":
                audio_data_queue.clear()
                clear_audio_buffer()
                return

            elif command == "REPEAT":
                audio_data_queue.clear()
                clear_audio_buffer()
                audio_data_queue = copy.deepcopy(audio_data_queue_copy)

        except queue.Empty:
            pass


        if is_paused:
            clear_audio_buffer()
            return

        try:
            data = audio_data_queue.pop()
        except IndexError:
            return

        # handle output
        client.outports[0].get_array()[:] = data.T[0]
        client.outports[1].get_array()[:] = data.T[0] * 0.25
        
        # for channel, port in zip(data.T, client.outports):
        #     port.get_array()[:] = channel






    def parse_text(text: str) -> bool:
        words = text.split(' ')
        if (words[0] == '!r'):
            for current_word in words[1:]:
                random_lang = random.choice(languages)
                print(random_lang)
                tmp_mp3 = get_tts_mp3(current_word, random_lang)
                tmp_wav = convert_mp3_to_wav(tmp_mp3)
                write_wav_to_queue(tmp_wav)
            return True
        else:
            return False

    def get_tts_mp3(text: str, language: str = 'en-gb') -> BytesIO:
        mp3_fp = BytesIO()

        tts = gTTS(text, lang=language)
        tts.write_to_fp(mp3_fp)

        mp3_fp.seek(0)
        return mp3_fp


    def convert_mp3_to_wav(mp3_bytes: BytesIO) -> BytesIO:
        wav_fp = BytesIO()
        mono = AudioSegment.from_mp3(mp3_bytes)
        
        output = AudioSegment.from_mono_audiosegments(mono, mono)
        output = output.set_frame_rate(samplerate)
        output.export(wav_fp, format='wav')
        
        wav_fp.seek(0)
        return wav_fp


    def write_wav_to_queue(wav_bytes: BytesIO):
        global audio_data_queue
        global audio_data_queue_copy
        
        audio_data_queue_copy.clear()
        with sf.SoundFile(wav_bytes) as f:
            block_generator = f.blocks(blocksize=blocksize, dtype='float32',
                                    always_2d=True, fill_value=0)
            for data in block_generator:
                audio_data_queue.appendleft(data)
                audio_data_queue_copy.appendleft(data)

    #random name for client, helps prevent bug
    client = jack.Client('TTS-JACK-{0}'.format(str(uuid.uuid4())[0:8]))

    blocksize, samplerate = client.blocksize, client.samplerate

    client.set_process_callback(process)
    client.set_xrun_callback(xrun)

    client.outports.register('output')
    client.outports.register('feedback')

    with client:
        pulse_source = client.get_ports("PulseAudio JACK Source")
        client.connect(client.outports[0], pulse_source[0])
        client.connect(client.outports[0], pulse_source[1])

        headphones = client.get_ports(is_input=True)
        client.connect(client.outports[1], headphones[0])
        client.connect(client.outports[1], headphones[1])

        while True:
            text = input_queue.get()
            if len(text) > 0:
                if not parse_text(text):
                    mp3_bytes = get_tts_mp3(text)
                    wav_bytes = convert_mp3_to_wav(mp3_bytes)
                    write_wav_to_queue(wav_bytes)
