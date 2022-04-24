import sys

import multiprocessing

# from x11_handling import X11_watcher_loop
# from jack_utils import jack_audio_player_loop
# from rtvc.tts_cli import real_time_voice_cloning_loop
from gTTS_client import gtts_main_loop
from sapi4_client import sapi4_tts_main_loop
from windows_tts import windows_tts_main_loop
from windows_player import main_winsound_loop

def main():
    # command_queue = multiprocessing.Queue()
    input_queue = multiprocessing.Queue()
    audio_queue = multiprocessing.Queue()
    
    # p1 = multiprocessing.Process(target=main_loop, args=(command_queue,input_queue))
    # p2 = multiprocessing.Process(target=X11_watcher_loop, args=((command_queue),))
    # p3 = multiprocessing.Process(target=jack_audio_player_loop, args=(command_queue, audio_queue))

    # p4 = multiprocessing.Process(target=real_time_voice_cloning_loop, args=("./source_audio.ogg", input_queue, audio_queue))

    p5 = multiprocessing.Process(target=gtts_main_loop, args=(input_queue, audio_queue))
    p6 = multiprocessing.Process(target=windows_tts_main_loop, args=(input_queue, audio_queue))
    p7 = multiprocessing.Process(target=sapi4_tts_main_loop, args=(input_queue, audio_queue))
    p8 = multiprocessing.Process(target=main_winsound_loop, args=(audio_queue,))

    # p1.start()
    # p2.start()
    # p3.start()
    # p4.start()

    p5.start()
    p6.start()
    p7.start()
    p8.start()

    #Main input loop
    print('Press Ctrl+C to stop')
    # curr_engine = "gtts"
    curr_engine = "gtts"
    while(True):
        try:
            text = input()
            if (text.split(' ')[0] == "!se"):
                curr_engine = text.split(' ')[1]
                print("switching engine to " + curr_engine)
                continue
            else:
                input_queue.put((curr_engine, text))
        except KeyboardInterrupt:
            print("Stopping...")
            return

if __name__ == '__main__':
    main()