from multiprocessing.queues import Queue
import jack
import soundfile as sf
from collections import deque
import uuid
from io import BytesIO

import copy 

from gtts import gTTS

from pydub import AudioSegment
import librosa

#queue only used for queue.Empty type
import queue

import multiprocessing

languages = ['af', 'ar', 'bn', 'bs', 'ca', 'cs', 'cy', 'da', 'de', 'el', 'en-au', 'en-ca', 'en-gb', 'en-gh', 'en-ie', 'en-in', 'en-ng', 'en-nz', 'en-ph', 'en-tz', 'en-uk', 'en-us', 'en-za', 'en', 'eo', 'es-es', 'es-us', 'es', 'et', 'fi', 'fr-ca', 'fr-fr', 'fr', 'gu', 'hi', 'hr', 'hu', 'hy', 'id', 'is', 'it', 'ja', 'jw', 'km', 'kn', 'ko', 'la', 'lv', 'mk', 'ml', 'mr', 'my', 'ne', 'nl', 'no', 'pl', 'pt-br', 'pt-pt', 'pt', 'ro', 'ru', 'si', 'sk', 'sq', 'sr', 'su', 'sv', 'sw', 'ta', 'te', 'th', 'tl', 'tr', 'uk', 'ur', 'vi', 'zh-CN', 'zh-cn', 'zh-tw']
audio_data_queue = deque()
audio_data_queue_copy = deque()
is_paused = False

def jack_audio_player_loop(command_queue: multiprocessing.Queue, wav_audio_queue: multiprocessing.Queue):

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

    def write_wav_to_queue(wav_bytes: BytesIO):
        global audio_data_queue
        global audio_data_queue_copy

        wav_bytes.seek(0)
        resampled_audio_stream = BytesIO()
        audio_data_queue_copy.clear()

        #resample audio
        resampled_data = librosa.core.load(wav_bytes, sr=samplerate)
        sf.write(resampled_audio_stream, resampled_data[0], samplerate, format="WAV")
        resampled_audio_stream.seek(0)

        with sf.SoundFile(resampled_audio_stream) as f:
            block_generator = f.blocks(blocksize=blocksize, dtype=resampled_data[0][-1],
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
            audio = wav_audio_queue.get()
            write_wav_to_queue(audio)
        
    