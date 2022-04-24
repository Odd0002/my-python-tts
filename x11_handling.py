from Xlib.display import Display
from Xlib import X
from Xlib.ext import record
from Xlib.protocol import rq

from multiprocessing import Queue

def X11_watcher_loop(command_queue: Queue):
    disp = None
    
    def handler(reply):
        """ This function is called when a xlib event is fired """
        data = reply.data
        while len(data):
            event, data = rq.EventField(None).parse_binary_value(data, disp.display, None, None)
           
            if event.type == X.KeyRelease:
                
                if event.detail == 127:
                    # PAUSE/BREAK PUSHED
                    command_queue.put("TOGGLE_PAUSE")
                elif event.detail == 119:
                    command_queue.put("CLEAR")
                elif event.detail == 112:
                    command_queue.put("REPEAT")
    
    # get current display
    disp = Display()
        
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