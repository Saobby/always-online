import ftputil
import ftputil.error
import traceback


class FtpConnectionError(Exception):
    def __init__(self, msg):
        self.message = msg

    def __str__(self):
        return self.message


class FtpSession:
    def __init__(self, host, username="anonymous", password="", encoding="gbk"):
        try:
            self._ftp_obj = ftputil.FTPHost(host, username, password, encoding=encoding)
        except ftputil.error.FTPOSError:
            raise FtpConnectionError(traceback.format_exc())
        self._username = username
        self._password = password
        self._host = host
        self._encoding = encoding

    def list_obj(self, path: str, retry=True):
        path = path.replace("\\", "")
        if path == "":
            path = "/"
        if path[-1] != "/":
            path += "/"
        try:
            ret = [{"type": {True: "dir", False: "file"}[self._ftp_obj.path.isdir(path+obj)],
                    "name": obj, "modify_time": self._ftp_obj.path.getmtime(path+obj),
                    "size": self._ftp_obj.path.getsize(path+obj)}
                   for obj in self._ftp_obj.listdir(path)]
        except ftputil.error.FTPOSError:
            if retry:
                try:
                    self._ftp_obj = ftputil.FTPHost(self._host, self._username, self._password, encoding=self._encoding)
                    return self.list_obj(path, retry=False)
                except ftputil.error.FTPOSError:
                    raise FtpConnectionError(traceback.format_exc())
            else:
                raise FtpConnectionError(traceback.format_exc())
        return ret

    def get_obj(self, path, retry=True):
        try:
            with self._ftp_obj.open(path, "rb") as s:
                return s.read()
        except ftputil.error.FTPOSError:
            if retry:
                try:
                    self._ftp_obj = ftputil.FTPHost(self._host, self._username, self._password, encoding=self._encoding)
                    return self.get_obj(path, False)
                except ftputil.error.FTPOSError:
                    raise FtpConnectionError(traceback.format_exc())
            else:
                raise FtpConnectionError(traceback.format_exc())

    def close(self):
        self._ftp_obj.close()


if __name__ == "__main__":
    a = FtpSession("localhost")
    print(a.list_obj("/"))
    print(a.get_obj("/test.txt"))

