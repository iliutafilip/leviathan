import argparse
import atexit
from client_handling.client_handler import start_server
from store.user_history_store import UserHistoryStore, start_cleanup_loop

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

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-a', '--address', type=str, required=True)
    parser.add_argument('-p', '--port', type=int, required=True)
    parser.add_argument('-c', '--config', type=str, required=False)

    args = parser.parse_args()

    try:
        print(title)
        print("[-] Leviathan running...")

        history_store = UserHistoryStore()
        atexit.register(history_store.close)
        start_cleanup_loop(history_store, period=600)

        start_server(args.address, args.port, args.config)
    except Exception as e:
        print(e)