import argparse

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

    parser.add_argument('-s', '--ssh', action='store_true')

    args = parser.parse_args()

    try:
        if args.ssh:
            print(title)
            print("[-] Leviathan running...")

            history_store = UserHistoryStore()
            start_cleanup_loop(history_store, period=600)

            start_server(args.address, args.port)
    except Exception as e:
        print(e)