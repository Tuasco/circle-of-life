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
    
    # ANSI Color Codes
    BOLD_YELLOW = "\033[1;33m"
    GREEN = "\033[92m"
    RESET = "\033[0m"

    print(f"{BOLD_YELLOW}*** Honishell Ready - Parsing Command ***{RESET}")
    try:
        while True:
            # Wait for command then send it
            command = input(f"{GREEN}> {RESET}")
            display.env_send_queue.put(command)
        
            # Wait for response, until env is done parsing. This is basically syncing
            msg = display.env_recv_queue.get()
            
            # For some reason if env tells us to quit, we do. This should never happen tho
            if msg == "quit":
                break
            
            # If env returns a non-empty message, display it. This is what we do after all 
            if msg != '\0':
                print(msg)
    except (KeyboardInterrupt, EOFError):
        print()
        display.env_send_queue.put("quit") #Tell env to wrap up
        display.env_recv_queue.get(timeout=5) #Wait env tells us he's done (or timeout)
    finally:
        # Close everything on our end
        display.env_process.terminate()
        display.env_process.join()
        display.env_send_queue.close()
        display.env_recv_queue.close()
    
if __name__ == "__main__":
    main()