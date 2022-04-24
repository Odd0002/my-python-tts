from io import BytesIO

import time

from pydub import AudioSegment

#queue only used for queue.Empty type
import queue

import multiprocessing
# tmp_file_path = "tmpFile.wav"
import socket
import struct

voice_pitch = 100
voice_speed = 150
# voice = "Sam"

HOST = '127.0.0.1'
PORT = 10250

def sapi4_tts_main_loop(input_queue: multiprocessing.Queue, wav_audio_queue: multiprocessing.Queue):
    def recvall(sock, n):
        # Helper function to recv n bytes or return None if EOF is hit
        data = bytearray()
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data


    def request_audio(text: str):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sam_socket:
                sam_socket.connect((HOST, PORT))
                # Not sure what this is for, just read it and discard it
                '''	WORD toSend[3];
                    toSend[0] = defPitch;
                    toSend[1] = minPitch;
                    toSend[2] = maxPitch;
                '''
                recvall(sam_socket, 6)

                #not sure what this is either, ignore it
                ''' DWORD toSend2[3];
                    toSend2[0] = defSpeed;
                    toSend2[1] = minSpeed;
                    toSend2[2] = maxSpeed;
                '''
                print(recvall(sam_socket, 12))

                length = len(text)
                packet = struct.pack(
                    #I HAVE NO IDEA WHY THIS IS LITTLE ENDIAN
                    '<HHL'+ str(length) + 's',
                    length,
                    voice_pitch,
                    voice_speed,
                    text.encode('ascii'),
                    )

                sam_socket.sendall(packet)



                #data length
                length_data = recvall(sam_socket, 4)
                print(length_data)
                file_length = struct.unpack('<i', length_data)[0]
                print("Length:", file_length)
                data = recvall(sam_socket, file_length)
                if (file_length < 1024):
                    print("Error on Microsoft Sam's side, didn't work for some reason.")
                    return

                output_audio(BytesIO(data))


        except Exception as e:
            print("couldn't send: ", e)

    def output_audio(wav_data: BytesIO):
        wav_audio_queue.put(wav_data)
        print("Wrote Audio!")

    def handle_text(text: str):
        request_audio(text)
        pass

    while True:
        (tts_engine, text) = input_queue.get()
        if (tts_engine != "sapi4"):
            input_queue.put((tts_engine, text))
            time.sleep(1)
            continue
        print("got text!")
        if len(text) > 0:
            handle_text(text)
            # mp3_bytes = get_tts_mp3(text)
            # wav_bytes = convert_mp3_to_wav(mp3_bytes)
            # output_audio(wav_bytes)
