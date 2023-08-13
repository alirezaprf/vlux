import json
from websocket import WebSocketApp
import time
import os
from threading import Thread

MASTER_URL = "vluxm.irsuniversity.space"
WS_PORT = "8000"
CREATE_USER_SUCCESS_MESSAGE = ""
ENABLE_USER_SUCCESS_MESSAGE = ""
DISABLE_USER_SUCCESS_MESSAGE = ""


def add_user_with_password(username, password):
    try:
        os.system(f'useradd -s /usr/sbin/nologin {username}')
        os.system(f'adduser {username} ssh_allowed')
        os.system(f'echo {username}:{password} | chpasswd')
        print(f"User '{username}' added with password successfully.")
    except Exception as e:
        print(f"User '{username}' Failed.")
        print(f"Error: {e}")


def disable_ssh_for_user(username):
    try:
        os.system(f'adduser {username} ssh_denied')
        os.system(f'pkill -u {username}')
        print(f"SSH access disabled for user '{username}'.")
    except Exception as e:
        print(f"Error: {e}")


def enable_ssh_for_user(username):
    try:
        os.system(f'gpasswd -d {username}  ssh_denied')
        print(f"SSH access enabled for user '{username}'.")
    except Exception as e:
        print(f"Error: {e}")


def new_command(cmd: str):
    cmd = json.loads(cmd)

    action = cmd['type']
    data = cmd.get('data')
    user = data.get('username')

    if action == "add-user":
        pasword = data['password']
        add_user_with_password(user, pasword)
        #ws.send(CREATE_USER_SUCCESS_MESSAGE)
    elif action == "disable-user":
        disable_ssh_for_user(user)
        #ws.send(DISABLE_USER_SUCCESS_MESSAGE)
    elif action == 'enable-user':
        enable_ssh_for_user(user)
        #ws.send(ENABLE_USER_SUCCESS_MESSAGE)
    elif action == "fetch-users":
        for U in data["users"]:
            add_user_with_password(U["username"], U["password"])


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
                  header={"Cookie": "session=tokenman"},)
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
        os.system("bash /etc/init.d/ssh start")
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
