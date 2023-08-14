import json
import subprocess

from websocket import WebSocketApp
import time
import os
from threading import Thread

MASTER_URL = "vluxm.irsuniversity.space"
WS_PORT = "8000"


def add_user_with_password(username, password):
    try:
        subprocess.run(['useradd', '-M', '-s', '/bin/false', username], check=True)
        print(f"User `{username}` created successfully.")
        change_password_for_user(username, password)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred on creating user `{username}`. {e}")


def disable_ssh_for_user(username):
    try:
        subprocess.run(['adduser', username, 'disabled_users'], check=True)
        print(f"User {username} added to disabled_users group.")
        subprocess.run(['pkill', '-u', username], check=True)
        print(f"SSH access disabled for user `{username}`.")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred on disabling user `{username}`. {e}")


def enable_ssh_for_user(username):
    try:
        subprocess.run(['gpasswd', '-d', username, 'disabled_users'], check=True)
        print(f"User `{username}` removed from disabled_users group.")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred on enabling user `{username}`. {e}")


def delete_user(username):
    try:
        subprocess.run(['userdel', username], check=True)
        print(f"User `{username}` deleted.")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred on deleting user `{username}`. {e}")


def change_password_for_user(username, new_password):
    try:
        subprocess.run(f'echo {username}:{new_password} | chpasswd', shell=True, check=True)
        print(f"Changed user `{username}` password to `{new_password}`.")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred on changing password of user `{username}`. {e}")


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
    print(error)


def on_close(ws: WebSocketApp, close_status_code, close_msg):
    ws_new = WebSocketApp(f"ws://{MASTER_URL}:{WS_PORT}/ws/",
                          on_open=on_open,
                          on_message=on_message,
                          on_error=on_error,
                          on_close=on_close,
                          header={"Cookie": f"session={os.getenv('SLAVE_SESSION_KEY')}"}, )
    ws_thread = Thread(target=ws_new.run_forever)
    ws_thread.start()


def on_open(ws: WebSocketApp):
    print("Opened connection ")


def read_nethogs():
    fp = open('./logs/nethogs')
    lines = fp.readlines()
    fp.close()
    users = []
    for L in lines:
        user, recv, sent = L.split(',')
        users.append((user, sent + recv))
    return users


def send_stats_mto_master(ws: WebSocketApp):
    while True:
        try:
            for user, traffic in read_nethogs():
                ws.send(json.dumps(
                    {
                        "type": "add-traffic",
                        "date": {
                            "username": user,
                            "size": traffic
                        }
                    }
                ))
            time.sleep(2 * 60)
        except:
            pass


while True:
    try:
        ws = WebSocketApp(f"ws://{MASTER_URL}:{WS_PORT}/ws/",
                        on_open=on_open,
                        on_message=on_message,
                        on_error=on_error,
                        on_close=on_close,
                        header={"Cookie": "session=tokenman"},)
        ws_thread = Thread(target=ws.run_forever)
        ws_thread.start()
        time.sleep(1)
        ws.send(json.dumps({"type": "fetch-users"}))
        break
    except:
        time.sleep(2)

# master_stats_thread = Thread(target=send_stats_mto_master, args=(ws,))
# master_stats_thread.start()
