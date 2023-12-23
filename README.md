# always-online
 FTP备份机，在FTP服务器在线时下载其中文件，以备FTP服务器下线时使用

## 功能
当FTP服务器在线时，将FTP服务器中存储的文件下载到本地，并通过增量更新的方式使本地文件与FTP服务器文件保持一致，以备FTP服务器下线时使用。

同时，本程序在发现FTP服务器中的文件被更改或删除时，会自动备份文件更改前的版本。

## 配置文件设置
* `common`
  + `enable_log`: 是否启用错误日志记录
* `ftp_servers`: 要备份的FTP服务器，可以有多个
  + `name`: 服务器名，可以随便填，但是要保证唯一
  + `ftp_host`: FTP服务器IP或域名
  + `ftp_username`: 登录FTP服务器所需的用户名，匿名登录填`anonymous`
  + `ftp_password`: 登录FTP服务器所需的密码
  + `watching_path`: 要备份FTP服务器中的哪个目录
  + `backup_path`: 备份的文件放在哪里
  + `archive_path`: 备份的文件的历史版本放在哪里
  + `checking_delay`: 每遍历完一次FTP服务器延时几秒
  + `encoding`: 解码时所用的字符集，填错会导致文件名乱码，程序异常等问题

## 其它
![](https://gp0.saobby.com/i/YDWiYODJMHNFr3vP.PNG)
