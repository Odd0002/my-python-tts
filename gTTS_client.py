import random
from io import BytesIO

import time

from gtts import gTTS, lang

from pydub import AudioSegment

#queue only used for queue.Empty type
import queue

import multiprocessing

languages = ['af', 'ar', 'bn', 'bs', 'ca', 'cs', 'cy', 'da', 'de', 'el', 'en-au', 'en-ca', 'en-gb', 'en-gh', 'en-ie', 'en-in', 'en-ng', 'en-nz', 'en-ph', 'en-tz', 'en-uk', 'en-us', 'en-za', 'en', 'eo', 'es-es', 'es-us', 'es', 'et', 'fi', 'fr-ca', 'fr-fr', 'fr', 'gu', 'hi', 'hr', 'hu', 'hy', 'id', 'is', 'it', 'ja', 'jw', 'km', 'kn', 'ko', 'la', 'lv', 'mk', 'ml', 'mr', 'my', 'ne', 'nl', 'no', 'pl', 'pt-br', 'pt-pt', 'pt', 'ro', 'ru', 'si', 'sk', 'sq', 'sr', 'su', 'sv', 'sw', 'ta', 'te', 'th', 'tl', 'tr', 'uk', 'ur', 'vi', 'zh-CN', 'zh-cn', 'zh-tw']
is_paused = False
current_lang = 'en'
current_tld = 'com'


def gtts_main_loop(input_queue: multiprocessing.Queue, wav_audio_queue: multiprocessing.Queue):
    global current_lang
    global current_tld
    def parse_text(text: str) -> bool:
        global current_lang
        global current_tld
        words = text.split(' ')
        if (words[0] == '!r'):
            for current_word in words[1:]:
                random_lang = random.choice(languages)
                print(random_lang)
                tmp_mp3 = get_tts_mp3(current_word, random_lang)
                tmp_wav = convert_mp3_to_wav(tmp_mp3)
                output_audio(tmp_wav)
            return True
        elif (words[0] == '!sl'):
            current_lang = words[1]
            return True
        elif (words[0] == '!stld'):
            current_tld = words[1]
            return True
        else:
            return False

    def get_tts_mp3(text: str, language: str = None) -> BytesIO:
        global current_lang
        if (language is None):
            language = current_lang

        print(current_lang)
        print(current_tld)

        mp3_fp = BytesIO()

        tts = gTTS(text, lang=language, tld=current_tld)
        tts.write_to_fp(mp3_fp)

        mp3_fp.seek(0)
        return mp3_fp


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

    # def write_wav_to_queue(wav_bytes: BytesIO):
    #     global audio_data_queue
    #     global audio_data_queue_copy
        
    #     audio_data_queue_copy.clear()
    #     with sf.SoundFile(wav_bytes) as f:
    #         block_generator = f.blocks(blocksize=blocksize, dtype='float32',
    #                                 always_2d=True, fill_value=0)
    #         for data in block_generator:
    #             audio_data_queue.appendleft(data)
    #             audio_data_queue_copy.appendleft(data)

    while True:
        try:
            (engine, text) = input_queue.get()
            if (engine != "gtts"):
                input_queue.put((engine, text))
                time.sleep(1)
                continue
            print("got text!")
            if len(text) > 0:
                if not parse_text(text):
                    mp3_bytes = get_tts_mp3(text)
                    wav_bytes = convert_mp3_to_wav(mp3_bytes)
                    output_audio(wav_bytes)
        except:
            pass
