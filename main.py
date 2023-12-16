import json
import toml
import traceback
import os
import time
import random
import threading
import ftp_core

enable_log = True


def ftp_scan(session: ftp_core.FtpSession, path: str, callback=None, onerror_callback=None):
    if path == "":
        path = "/"
    path = path.replace("\\", "/")
    if path[-1] != "/":
        path += "/"
    while True:
        try:
            objs = session.list_obj(path)
        except (ConnectionAbortedError, ConnectionRefusedError):
            if onerror_callback is not None:
                onerror_callback("Failed to connect to the FTP server.")
            time.sleep(5)
        except Exception:
            if onerror_callback is not None:
                onerror_callback(traceback.format_exc())
            objs = []
            break
        else:
            break
    for obj in objs:
        if obj["type"] == "file":
            if callback is not None:
                callback(path+obj["name"], obj)
        elif obj["type"] == "dir":
            ftp_scan(session, path+obj["name"]+"/", callback, onerror_callback)


def create_necessary_folder(path: str):
    path = path.replace("\\", "/")
    if path == "":
        path = "/"
    if path[-1] == "/":
        path = path[:-1]
    folders = path.split("/")
    for i in range(len(folders)):
        p = "/".join(folders[0:i+1])
        if not os.path.isdir(p):
            os.mkdir(p)


def log_error(message):
    global enable_log
    if enable_log:
        with open("error.log", "a", encoding="utf-8") as f:
            f.write("[{}] {}".format(ts2str(time.time(), "%Y/%m/%d %H:%M:%S"), message))


def clean_empty_folder(folder_path, keep_root_folder=False):
    folder_path = folder_path.replace("\\", "/")
    if folder_path[-1] == "/":
        folder_path = folder_path[:-1]
    children_folders = [folder_path + "/" + obj for obj in os.listdir(folder_path) if
                        os.path.isdir(folder_path + "/" + obj)]
    for child in children_folders:
        clean_empty_folder(child)
    if len(os.listdir(folder_path)) == 0 and keep_root_folder is False:
        try:
            os.rmdir(folder_path)
        except PermissionError:
            pass


def ts2str(ts, fmt="%Y年%m月%d日_%H时%M分%S秒"):
    time_array = time.localtime(ts)
    return time.strftime(fmt, time_array)


def gen_random_str(lens=64):
    ret = ""
    for i in range(lens):
        ret += random.choice("1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    return ret


def gen_save_func(session: ftp_core.FtpSession, base_path: str, old_objs: dict, new_objs: dict, archive_path):
    base_path = base_path.replace("\\", "/")
    if base_path[-1] == "/":
        base_path = base_path[:-1]

    def download_and_save(key, obj):
        new_objs[key] = {"size": obj["size"], "modify_time": obj["modify_time"]}
        if key in old_objs and obj["size"] == old_objs[key]["size"] \
                and obj["modify_time"] == old_objs[key]["modify_time"]:
            return
        # print("Found new: {}".format(key))
        while True:
            try:
                file_data = session.get_obj(key)
            except (ConnectionAbortedError, ConnectionRefusedError):
                log_error("Failed to connect to the FTP server to download file.")
                time.sleep(5)
            except:
                log_error("Failed to download file: {}".format(traceback.format_exc()))
                return
            else:
                break
        if key in old_objs:
            archive_file(key, archive_path, base_path)
        path = "/".join((base_path+key).split("/")[:-1])
        create_necessary_folder(path)
        try:
            with open(base_path+key, "wb") as f:
                f.write(file_data)
        except:
            log_error("Failed to copy file: {}".format(traceback.format_exc()))
        # old_objs[key] = {"size": obj["size"], "modify_time": obj["modify_time"]}
    return download_and_save


def archive_file(key, archive_path, backup_path):
    if os.path.isfile(backup_path+key):
        final_archive_path = "/".join((archive_path+key).split("/")[:-1])
        create_necessary_folder(final_archive_path)
        try:
            os.rename(backup_path+key, "{}/{}_{}_{}".format(final_archive_path, ts2str(time.time()),
                                                            gen_random_str(8), key.split("/")[-1]))
        except:
            log_error("Failed to archive file: {}".format(traceback.format_exc()))
        # print("Archived: {}".format(key))


def watch_ftp(host, watch_path, backup_path, archive_path, check_delay, username="anonymous", password="", name=""):
    backup_path = backup_path.replace("\\", "/")
    archive_path = archive_path.replace("\\", "/")
    if backup_path[-1] == "/":
        backup_path = backup_path[:-1]
    if archive_path[-1] == "/":
        archive_path = archive_path[:-1]
    success = False
    session = None
    while not success:
        try:
            session = ftp_core.FtpSession(host, username, password)
        except:
            log_error("Failed to connect to the FTP server: {}".format(host))
            time.sleep(check_delay)
        else:
            success = True
    create_necessary_folder("data")
    data_file_path = "data/{}.dat".format(name)
    if os.path.isfile(data_file_path):
        with open(data_file_path, "r", encoding="utf-8") as f:
            old_objs = json.loads(f.read())
    else:
        old_objs = {}
    new_objs = {}
    while True:
        ftp_scan(session, watch_path, gen_save_func(session, backup_path, old_objs, new_objs, archive_path), log_error)
        # print(old_objs.keys(), new_objs.keys())
        deleted_objs = [key for key, _ in old_objs.items() if key not in new_objs]
        for o in deleted_objs:
            archive_file(o, archive_path, backup_path)
        clean_empty_folder(backup_path, keep_root_folder=True)
        old_objs = new_objs.copy()
        new_objs = {}
        with open(data_file_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(old_objs))
        time.sleep(check_delay)


def run():
    global enable_log
    try:
        with open("config.toml", "r", encoding="utf-8") as f:
            config = toml.loads(f.read())
    except:
        log_error("Failed to read config file: {}".format(traceback.format_exc()))
        return
    enable_log = config["common"]["enable_log"]
    ftp_servers = config["ftp_servers"]
    threads = [threading.Thread(target=watch_ftp, args=(s["ftp_host"], s["watching_path"], s["backup_path"],
                                                        s["archive_path"], s["checking_delay"], s["ftp_username"],
                                                        s["ftp_password"], s["name"]))
               for s in ftp_servers]
    for thread in threads:
        thread.start()


if __name__ == "__main__":
    try:
        run()
    except:
        log_error("An uncaught error occurred while running.\n{}".format(traceback.format_exc()))
    # TODO: 修复文件名中有多个空格会出问题的bug
