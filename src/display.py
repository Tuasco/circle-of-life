#!/usr/bin/env python3
from multiprocessing import Process, Queue
from env_manager import main as env_main

class Display:
    def __init__(self):
        # Start env process
        self.env_send_queue = Queue()
        self.env_recv_queue = Queue()
        self.env_process = Process(target=env_main, args=(self.env_send_queue, self.env_recv_queue))
        self.env_process.start()
        
def main():
    display = Display()
    
    print("*** Honishell Ready - Parsing Command ***")
    try:
        while True:
            # Wait for command then send it
            command = input("> ")
            display.env_send_queue.put(command)
        
            # Wait for response, then display it
            msg = display.env_recv_queue.get()
            if msg == "quit":
                break
            
            if msg != '\0':
                print(msg)
    except KeyboardInterrupt, EOFError:
        print()
    finally:
        display.env_process.terminate()
        display.env_process.join()
        display.env_send_queue.close()
        display.env_recv_queue.close()
    
if __name__ == "__main__":
    main()