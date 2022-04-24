from Xlib.display import Display
from Xlib import X
from Xlib.ext import record
from Xlib.protocol import rq

import multiprocessing
from multiprocessing import Queue
import time

def queue_loop(q: Queue):
    disp = None
    
    def handler(reply):
        """ This function is called when a xlib event is fired """
        data = reply.data
        while len(data):
            event, data = rq.EventField(None).parse_binary_value(data, disp.display, None, None)
            
            # KEYCODE IS FOUND USING event.detail
            print(event.detail)
            
            if event.type == X.KeyPress:
                # BUTTON PRESSED
                # print("pressed")
                pass
            elif event.type == X.KeyRelease:
                # BUTTON RELEASED
                # print("released")
                if event.detail == 127:
                    print("PUSHED")
                    print(q)
                    q.put("PAUSE")
                    print(q.qsize())
    
    # get current display
    disp = Display()
    root = disp.screen().root
        
    # Monitor keypress and button press
    ctx = disp.record_create_context(
                0,
                [record.AllClients],
                [{
                        'core_requests': (0, 0),
                        'core_replies': (0, 0),
                        'ext_requests': (0, 0, 0, 0),
                        'ext_replies': (0, 0, 0, 0),
                        'delivered_events': (0, 0),
                        'device_events': (X.KeyReleaseMask, X.ButtonReleaseMask),
                        'errors': (0, 0),
                        'client_started': False,
                        'client_died': False,
                }])
    disp.record_enable_context(ctx, handler)
    disp.record_free_context(ctx)
    
def reader_loop(q: Queue):
    print(q)
    while (True):    
        print(q.qsize())
        time.sleep(1)
        # if not q.empty():
        #     print("queue not empty!")
        #     q.get_nowait()
def main():
    q = Queue()
    p1 = multiprocessing.Process(target=queue_loop, args=((q),))
    p2 = multiprocessing.Process(target=reader_loop, args=((q),))
    print("starting")
    p1.daemon = True
    p2.daemon = True
    p1.start()
    p2.start()
    print("done!")
    p1.join()
    p2.join()
    

if __name__ == '__main__':
    main()