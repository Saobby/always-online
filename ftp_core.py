import ftplib


class FtpSession:
    def __init__(self, host, username="anonymous", password=""):
        self._ftp_obj = ftplib.FTP(host)
        self._ftp_obj.login(username, password)
        self._username = username
        self._password = password
        self._host = host

    def list_obj(self, path):
        ret = []

        def get_permission_num(permission):
            mapping = {"-": 0, "w": 2, "r": 4, "x": 1}
            num = 0
            for i in permission:
                num += mapping[i]
            return num

        def process(*args):
            for obj in args:
                data = {}
                p = obj.split(" ")
                p = [j for j in p if j != ""]
                if p[0][0] == "-":
                    data["type"] = "file"
                elif p[0][0] == "d":
                    data["type"] = "dir"
                else:
                    data["type"] = p[0][0]
                data["owner_permission"] = get_permission_num(p[0][1:4])
                data["group_permission"] = get_permission_num(p[0][4:7])
                data["user_permission"] = get_permission_num(p[0][7:10])
                data["size"] = int(p[4])
                data["modify_time"] = " ".join(p[5:8])
                data["name"] = " ".join(p[8:])
                ret.append(data)
        try:
            self._ftp_obj.cwd(path)
            self._ftp_obj.dir(process)
        except (ConnectionAbortedError, ConnectionRefusedError):
            self._ftp_obj = ftplib.FTP(self._host)
            self._ftp_obj.login(self._username, self._password)
            ret = []
            self._ftp_obj.cwd(path)
            self._ftp_obj.dir(process)
        return ret

    def get_obj(self, key):
        ret = []

        def process(*args):
            for i in args:
                ret.append(i)

        try:
            self._ftp_obj.retrbinary("RETR {}".format(key), process)
        except (ConnectionAbortedError, ConnectionRefusedError):
            self._ftp_obj = ftplib.FTP(self._host)
            self._ftp_obj.login(self._username, self._password)
            ret = []
            self._ftp_obj.retrbinary("RETR {}".format(key), process)
        return b"".join(ret)

    def close(self):
        self._ftp_obj.close()


if __name__ == "__main__":
    a = FtpSession("localhost")
    print(a.list_obj("/test/"))

