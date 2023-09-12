from threading import Thread
import os
import pandas as pd
import subprocess
import time


def mkdir(folder_name: str):
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)


def tshark(filename):
    subprocess.run("tshark -r " + filename + " -Y \"tcp\" -T fields -e tcp.dstport -e frame.len | awk '{arr[$1]+=$2}END{for(i in arr)print i, arr[i]}' > download",
                   shell=True ,stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, check=True)
    subprocess.run("tshark -r " + filename + " -Y \"tcp\" -T fields -e tcp.srcport -e frame.len | awk '{arr[$1]+=$2}END{for(i in arr)print i, arr[i]}' > upload",
                   shell=True ,stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, check=True)
    download = pd.read_csv('download', delimiter=' ', header=None, names=['port', 'dbyte'])
    upload = pd.read_csv('upload', delimiter=' ', header=None, names=['port', 'ubyte'])
    return {
        "download": download.set_index('port'),
        "upload": upload.set_index('port'),
    }


def read_netstat_file(filename):
    n = pd.read_csv(filename, delimiter=' ', header=None, names=['port', 'user'])
    n['port'] = n.port.apply(lambda x: x.split(":")[-1])
    n = n.drop(n[n.port == 'ssh'].index)
    n.port = n.port.astype(int)
    return n.set_index('port')


def tcpdump(folder_name):
    while True:
        subprocess.run("tcpdump -w %s.d -G 2", check=False, shell=True ,stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, cwd=folder_name)
        time.sleep(0.1)


def netstat(folder_name):
    while True:
        current_time = int(time.time())
        subprocess.run("netstat -te | awk '$6 == \"ESTABLISHED\" {print $4, $9 $7}' > " + f"{current_time}.e", shell=True ,stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
                        check=False, cwd=folder_name)
        time.sleep(0.05)


def to_mgb(d:dict):
    return {k:round(v/1024/1024 , 2) for k,v in d.items() }

def files_analyze(folder_name ,ws_send) :
    while True:
        try:
            time.sleep(60)
            print("analyzing ... ")
            files = os.listdir(folder_name)
            files.sort(key=lambda x: int(x.split('.')[0]))
            download_by_user = {}
            upload_by_user = {}
            last_download = None
            last_upload = None

            # for i , f in enumerate(files):
            #     if f.split('.')[-1] == 'e':
            #         break
            # if i == len(files) - 1 :
            #     continue
            # files = files[:i+1]
            files = files[:100]

            for i , f in enumerate(files):
                # print(i , 'file ' , f)
                file_type = f.split('.')[-1]
                if file_type == 'd':
                    # ----------------------- Extract Traffic from d files ----------------------- #
                    r = tshark(folder_name + f)
                    # ---------------------------------------------------------------------------- #
                    download = r['download']
                    upload = r['upload']
                    # ---------------------------------------------------------------------------- #
                    if last_download is None:
                        last_download = download
                    else:
                        last_download = pd.concat((last_download, download)).groupby('port').aggregate('sum')
                    # ---------------------------------------------------------------------------- #
                    # ---------------------------------------------------------------------------- #
                    if last_upload is None:
                        last_upload = upload
                    else:
                        last_upload = pd.concat((last_upload, upload)).groupby('port').aggregate('sum')
                    # ---------------------------------------------------------------------------- #
                    # ---------------------------------------------------------------------------- #

                else:
                    port_user = read_netstat_file(folder_name + f)
                    # ---------------------------------------------------------------------------- #
                    if last_download is not None:
                        port_user = port_user.join(last_download)
                        last_download = None
                    # ---------------------------------------------------------------------------- #
                    if last_upload is not None:
                        port_user = port_user.join(last_upload)
                        last_upload = None
                    # ---------------------------------------------------------------------------- #
                    port_user.fillna(0, inplace=True)
                    # ---------------------------------------------------------------------------- #

                    # ---------------------------------------------------------------------------- #
                    # ---------------------------------------------------------------------------- #
                    
                    for V in port_user.itertuples():
                        # ---------------------------------------------------------------------------- #
                        try:
                            download_by_user.setdefault(V.user, 0)
                            download_by_user[V.user] += V.dbyte
                        except:
                            pass
                        # ---------------------------------------------------------------------------- #
                        try:
                            upload_by_user.setdefault(V.user, 0)
                            upload_by_user[V.user] += V.ubyte
                        except:
                            pass
                # ---------------------------------------------------------------------------- #
                # ---------------------------------------------------------------------------- #
                # ---------------------------------------------------------------------------- #
                os.remove(folder_name + f)

            print(
                "# ---------------------------------------------------------------------------- #\n",
                f"{to_mgb(download_by_user) = }",
                f"{to_mgb(upload_by_user) = }",
                "\n# ---------------------------------------------------------------------------- #\n"
            )
            
            ws_send(download_by_user , upload_by_user )

        except:
            continue
if __name__ == "__main__":
    folder_name = "tdump/"
    mkdir(folder_name)
    Thread(target=tcpdump, args=(folder_name, )).start()
    Thread(target=netstat, args=(folder_name, )).start()
    time.sleep(3)
    Thread(target=files_analyze, args=(folder_name, )).start()
