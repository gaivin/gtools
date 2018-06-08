# coding:utf-8
import paramiko
from logger_utils import get_logger

logger = get_logger("SSH_Utils")


class SSHConnection(object):
    def __init__(self, host='192.168.2.103', port=22, username='root', password='123456'):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self._transport = None
        self._ssh_client = None

    def connect(self):
        transport = paramiko.Transport((self.host, self.port))
        try:
            transport.connect(username=self.username, password=self.password)
        except Exception as e:
            logger.error(
                "ERROR: %s Please check your password or username %s@%s" % (e.message, self.username, self.host))
        self._transport = transport

        self._ssh_client = paramiko.SSHClient()
        self._ssh_client._transport = self._transport

    def close(self):
        self._transport.close()

    def upload(self, local_path, target_path):
        # Upload the file to remote host
        sftp = paramiko.SFTPClient.from_transport(self._transport)
        sftp.put(local_path, target_path)

    def download(self, remote_path, local_path):
        # Download the file from remote host
        sftp = paramiko.SFTPClient.from_transport(self._transport)
        sftp.get(remote_path, local_path)

    def cmd(self, command, timeout=None):
        stdin, stdout, stderr = self._ssh_client.exec_command(command, timeout=timeout)
        result = stdout.read()
        logger.debug(str(result))
        return result


if __name__ == '__main__':
    from config.deploy_manager_config import AVAUTOD_REMOTE_DIR
    import os

    ssh_connection = SSHConnection(host="10.98.137.152", username="root", password="!Emily0116")
    ssh_connection.connect()
    # output = ssh_connection.cmd("/tmp/avautod.sh -a forceinstall -smask 255.255.255.0 -sname ave-137-55 -key Supp0rtLau6 -g 10.98.138.1 -ntp 10.254.140.21 -domain datadomain.com -vp Chang3M3Now. -yaml /usr/avautod/config/template_install.yaml -vip 10.110.212.14 -sip 10.98.137.53 -vu fisher -dns 10.24.18.32 -esxi /MCQA-Durham-Fisher/host/10.110.209.160/ -net 10.98.138.51-255 -b latest -ds DS-209-160")
    autod_log_files = ssh_connection.cmd("ls -t %s | grep autoDeploy" % AVAUTOD_REMOTE_DIR).split("\n")
    if autod_log_files:
        autod_log_file = autod_log_files[0]
        # Get the last 10 lines of the auto deploy log
        deploy_log = ssh_connection.cmd("tail -n 10 %s" % os.path.join(AVAUTOD_REMOTE_DIR, autod_log_file))
    else:
        deploy_log = None
        files = ssh_connection.cmd("ls -lt %s" % AVAUTOD_REMOTE_DIR)
        print("Cannot found the deployment log in %s. Please refer to the files info in it: \n%s") % (
            AVAUTOD_REMOTE_DIR, files)
    print deploy_log  #
    ssh_connection.close()
