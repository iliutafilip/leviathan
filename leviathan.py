import argparse
import atexit
import socket
import threading
import time
from typing import Optional

from client_handling.client_handler import client_handle
from store.user_history_store import UserHistoryStore

title = """
 ██▓    ▓█████ ██▒   █▓ ██▓ ▄▄▄     ▄▄▄█████▓ ██░ ██  ▄▄▄       ███▄    █ 
▓██▒    ▓█   ▀▓██░   █▒▓██▒▒████▄   ▓  ██▒ ▓▒▓██░ ██▒▒████▄     ██ ▀█   █ 
▒██░    ▒███   ▓██  █▒░▒██▒▒██  ▀█▄ ▒ ▓██░ ▒░▒██▀▀██░▒██  ▀█▄  ▓██  ▀█ ██▒
▒██░    ▒▓█  ▄  ▒██ █░░░██░░██▄▄▄▄██░ ▓██▓ ░ ░▓█ ░██ ░██▄▄▄▄██ ▓██▒  ▐▌██▒
░██████▒░▒████▒  ▒▀█░  ░██░ ▓█   ▓██▒ ▒██▒ ░ ░▓█▒░██▓ ▓█   ▓██▒▒██░   ▓██░
░ ▒░▓  ░░░ ▒░ ░  ░ ▐░  ░▓   ▒▒   ▓▒█░ ▒ ░░    ▒ ░░▒░▒ ▒▒   ▓▒█░░ ▒░   ▒ ▒ 
░ ░ ▒  ░ ░ ░  ░  ░ ░░   ▒ ░  ▒   ▒▒ ░   ░     ▒ ░▒░ ░  ▒   ▒▒ ░░ ░░   ░ ▒░
  ░ ░      ░       ░░   ▒ ░  ░   ▒    ░       ░  ░░ ░  ░   ▒      ░   ░ ░ 
    ░  ░   ░  ░     ░   ░        ░  ░         ░  ░  ░      ░  ░         ░ 
                   ░                                                          
"""


def start_server(address, port, config_file: Optional[str] = None):
    socks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socks.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socks.bind((address, port))

    socks.listen(100)
    print(f"[SSH Server] SSH Server listening on {address}:{port}")

    while True:
        try:
            client, address = socks.accept()
            print(f"[SSH Server] Incoming SSH connection from {address[0]}:{address[1]}")

            ssh_thread = threading.Thread(target=client_handle, args=(client, address, config_file))
            ssh_thread.start()

        except Exception as e:
            print(e)


def start_cleanup_loop(store: UserHistoryStore, period: int = 1800):
    '''
    starts a loop which periodically cleans up the user's history
    default period is 30 minutes
    :param store: user history store
    :param period: period length in seconds; default is 1800s = 30min
    '''
    def cleanup_loop():
        while True:
            try:
                store.cleanup()
            except Exception as e:
                print(f"[-] Cleanup error: {e}")
            time.sleep(period)

    thread = threading.Thread(target=cleanup_loop, daemon=True)
    thread.start()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-a', '--address', type=str, required=True)
    parser.add_argument('-p', '--port', type=int, required=True)
    parser.add_argument('-c', '--config', type=str, required=False, help="Path to custom config file")


    args = parser.parse_args()

    try:
        print(title)
        print("Leviathan running...")

        history_store = UserHistoryStore()
        atexit.register(history_store.close)
        
        start_cleanup_loop(history_store)

        start_server(args.address, args.port, args.config)
    except Exception as e:
        print(e)