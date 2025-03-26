import json
import os
import shutil
import sys
from datetime import datetime

LOG_DIR = "logs"
BASE_LOG_FILE_NAME = "leviathan"
LOG_FILE = os.path.join(LOG_DIR, f"{BASE_LOG_FILE_NAME}.log")
MAX_LOG_SIZE = 1024 * 1024 * 40 # 40MB

os.makedirs(LOG_DIR, exist_ok=True)

def rotate_log():
    """
    Rotates the existing log file when it exceeds the size limit.
    """
    if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > MAX_LOG_SIZE:
        timestamp = datetime.now().strftime("%Y/%m/%d_%H:%M:%S")
        new_log_name = f"{BASE_LOG_FILE_NAME}_{timestamp}.log"

        shutil.move(LOG_FILE, new_log_name)


def log_event(event_type: str,
              session_id: str,
              src_ip: str = None,
              src_port: int = None,
              protocol: str = None,
              username: str = None,
              password: str = None,
              command: str = None,
              response: str = None,
              success: bool = None,
              ) -> None:
    """
    Logs an event in JSON format.

    :param event_type: event type, (e.g.: "session_start", "login_attempt")
    :param session_id: session ID
    :param src_ip: source IP address
    :param src_port: source port
    :param protocol: used protocol (e.g.: "ssh", "telnet")
    :param username: username used for logger in
    :param password: password used for logger in
    :param command: input command
    :param response: leviathan's response
    :param success: True/False
    """

    rotate_log()

    log_entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "event_type": event_type,
        "session_id": session_id,
        "src_ip": src_ip
    }

    if src_port is not None:
        log_entry["src_port"] = src_port
    if protocol is not None:
        log_entry["protocol"] = protocol
    if username is not None:
        log_entry["username"] = username
    if password is not None:
        log_entry["password"] = password
    if command is not None:
        log_entry["command"] = command
    if response is not None:
        log_entry["response"] = response
    if success is not None:
        log_entry["success"] = success

    log_json = json.dumps(log_entry)

    # Write to log file
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_json + "\n")

    print(log_json, file=sys.stdout)


def clear_log_file():
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
