import os
import json
import logging
import subprocess
import time
from threading import Thread
from datetime import datetime as dt
import pandas as pd
import traffic

import requests
from websocket import WebSocketApp

logging.basicConfig(
    level=logging.INFO,
    filename='slave.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

MASTER_URL = "vluxm.irsuniversity.space"
PORT = "8000"
WS_TOKEN = ""

logger = logging.getLogger(__name__)


def add_user_with_password(username, password):
    try:
        subprocess.run(['useradd', '-M', '-s', '/bin/false', username], check=True)
        log_text = f"User `{username}` created successfully."
        logger.info(log_text)
        # print(log_text)
        change_password_for_user(username, password)
    except subprocess.CalledProcessError as e:
        error_text = f"Error occurred on creating user `{username}`. {e}"
        logger.error(error_text)
        # print(error_text)


def disable_ssh_for_user(username):
    try:
        subprocess.run(['adduser', username, 'disabled_users'], check=True)
        log_text = f"User {username} added to disabled_users group."
        logger.info(log_text)
        # print(log_text)
        subprocess.run(['pkill', '-u', username], check=True)
        log_text = f"SSH access disabled for user `{username}`."
        logger.info(log_text)
        # print(log_text)
    except subprocess.CalledProcessError as e:
        error_text = f"Error occurred on disabling user `{username}`. {e}"
        logger.error(error_text)
        print(error_text)


def enable_ssh_for_user(username):
    try:
        subprocess.run(['gpasswd', '-d', username, 'disabled_users'], check=True)
        log_text = f"User `{username}` removed from disabled_users group."
        logger.info(log_text)
        # print(log_text)
    except subprocess.CalledProcessError as e:
        error_text = f"Error occurred on enabling user `{username}`. {e}"
        logger.error(error_text)
        print(error_text)


def delete_user(username):
    try:
        subprocess.run(['userdel', username], check=True)
        log_text = f"User `{username}` deleted."
        logger.info(log_text)
        # print(log_text)
    except subprocess.CalledProcessError as e:
        error_text = f"Error occurred on deleting user `{username}`. {e}"
        logger.error(error_text)
        # print(error_text)


def change_password_for_user(username, new_password):
    try:
        subprocess.run(f'echo {username}:{new_password} | chpasswd', shell=True, check=True)
        log_text = f"Changed user `{username}` password to `{new_password}`."
        logger.info(log_text)
        # print(log_text)
    except subprocess.CalledProcessError as e:
        error_text = f"Error occurred on changing password of user `{username}`. {e}"
        logger.error(error_text)
        # print(error_text)


def new_command(cmd: str):
    cmd = json.loads(cmd)

    action = cmd['type']
    data = cmd.get('data')
    user = data.get('username')

    if action == "add-user":
        password = data['password']
        add_user_with_password(user, password)
    elif action == "disable-user":
        disable_ssh_for_user(user)
    elif action == 'enable-user':
        enable_ssh_for_user(user)
    elif action == "fetch-users":
        for U in data["users"]:
            add_user_with_password(U["username"], U["password"])
    elif action == "delete-user":
        delete_user(user)
    elif action == "change-password":
        new_password = data["new-password"]
        change_password_for_user(user, new_password)


def on_message(ws, message):
    new_command(message)


def on_error(ws, error):
    logger.error(f"Error occurred on websocket. {error}")
    print(f"Error occurred : {error}")


def on_close(ws: WebSocketApp, close_status_code, close_msg):
    logger.info(f"Websocket connection closed. {close_status_code}. {close_msg}")
    print(f"Websocket connection closed. {close_status_code}. {close_msg}")
    start_websocket()


def on_open(ws: WebSocketApp):
    logger.info(f"Opened connection to master. {ws.url}")
    print("Opened connection ")


def start_websocket():
    global ws
    websocket = WebSocketApp(f"ws://{MASTER_URL}:{PORT}/ws/",
                             on_open=on_open,
                             on_message=on_message,
                             on_error=on_error,
                             on_close=on_close,
                             header={"Cookie": f"session={WS_TOKEN}"}, )

    ws_thread = Thread(target=websocket.run_forever)
    ws_thread.start()
    ws = websocket
    return websocket


def get_ws_token():
    response = requests.post(f"http://{MASTER_URL}:{PORT}/ws/auth/").json()
    return response["access_token"]


def send_ws_traffic(download_byuser: dict, upload_byuser: dict):
    all_keys = set(list(download_byuser.keys()) + list(upload_byuser.keys()))
    data = []
    for k in all_keys:
        data.append(
            {
                "username": k,
                "download": download_byuser.get(k, 0),
                "upload": upload_byuser.get(k, 0),
            }
        )
    for _ in range(5):
        try:
            ws.send(
                json.dumps(
                    {"type": "add-traffic", "data": data}
                )
            )
        except:
            time.sleep(1)
            continue
        

if __name__ == "__main__":
    while True:
        try:
            WS_TOKEN = get_ws_token()
            if WS_TOKEN == "":
                logger.error("Token not valid")
                print("Token not valid")
                raise Exception("Token not valid")
            ws = start_websocket()
            time.sleep(1)
            ws.send(json.dumps({"type": "fetch-users"}))
            logger.info("Slave started successfully.")
            print("__SLAVE__ Started Successfully")

            folder_name = "tdump/"
            traffic.mkdir(folder_name)
            Thread(target=traffic.tcpdump, args=(folder_name, )).start()
            Thread(target=traffic.netstat, args=(folder_name, )).start()
            time.sleep(3)
            Thread(target=traffic.files_analyze, args=(folder_name, send_ws_traffic)).start()
            break
        except:
            time.sleep(60 * 5)

# master_stats_thread = Thread(target=send_stats_mto_master, args=(ws,))
# master_stats_thread.start()
