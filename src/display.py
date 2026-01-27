#!/usr/bin/env python3
from multiprocessing import Process
from time import sleep

import posix_ipc

from env_manager import main as env_main


class Display:
    def __init__(self):
        # Start env process with POSIX message queues
        self.env_send_queue = posix_ipc.MessageQueue("/env_send", flags=posix_ipc.O_CREAT, max_messages=10, max_message_size=8192)
        self.env_recv_queue = posix_ipc.MessageQueue("/env_recv", flags=posix_ipc.O_CREAT, max_messages=10, max_message_size=8192)
        self.env_process = Process(target=env_main, args=())
        self.env_process.start()
        
def main():
    display = Display()
    
    # ANSI Color Codes
    BOLD_YELLOW = "\033[1;33m"
    GREEN = "\033[92m"
    RESET = "\033[0m"

    print(f"{BOLD_YELLOW}*** Honishell Ready - Parsing Commands ***{RESET}")
    try:
        while True:
            # Wait for command then send it
            command = input(f"{GREEN}>{RESET} ")
            display.env_send_queue.send(command.encode("utf-8"))
        
            # Wait for response, until env is done parsing. This is basically syncing
            msg, _ = display.env_recv_queue.receive()
            msg = msg.decode("utf-8")
            
            # If env tells us to quit, we do. This should only happen when we receive a quit token 
            if msg == "quit":
                break
            
            # If env returns a non-empty message, display it. This is what we do after all 
            if msg != '\0':
                print(msg)
    except (KeyboardInterrupt, EOFError):
        print()
        display.env_send_queue.send("quit".encode("utf-8")) #Tell env to wrap up
        msg, _ = display.env_recv_queue.receive(timeout=5) #Wait env tells us he's done (or timeout)
        sleep(.2) #Wait a bit more for env to actually finish its exit sequence
    finally:
        # Close everything on our end
        display.env_process.terminate()
        display.env_process.join()
        display.env_send_queue.close()
        display.env_recv_queue.close()
        # Clean up message queues
        try:
            display.env_send_queue.unlink()
        except posix_ipc.ExistentialError:
            pass
        try:
            display.env_recv_queue.unlink()
        except posix_ipc.ExistentialError:
            pass
    
if __name__ == "__main__":
    main()