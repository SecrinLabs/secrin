import threading

def run_in_thread(target, *args, **kwargs):
    thread = threading.Thread(target=target, args=args, kwargs=kwargs)
    thread.start()
