#!/usr/bin/env python  
# encoding: utf-8  

""" 
@version: v1.0 
@author: Gaivin Wang 
@license: Apache Licence  
@contact: gaivin@outlook.com
@site:  
@software: PyCharm 
@file: ssh-copy-id.py 
@time: 7/9/2019 10:37 AM 
"""

import pexpect
import os
import time
from csv import DictReader
import fire


def distribute_ssh_key(hosts_csv):
    for remote in DictReader(open(hosts_csv, "r")):
        remote = dict(remote)
        host = remote.get("host", None)
        if not host:
            print("ERROR: skip %s" % remote)
            continue
        print("Configure for %s..." % host)
        user = remote.get("user", "root")
        password = remote.get("password", "changeme")
        result = ssh_copy_id(host=host, user=user, password=password, chmod_auth_keys=True)
        if result:
            print("Add ssh key for %s successfully." % host)
        else:
            print("Add ssh key for %s Failed." % host)


def ssh_copy_id(host, user, password, local_user="root", pub_key="id_rsa.pub", chmod_auth_keys=False):
    print("Copy the RSA public key to remote server to avoid the password input")
    if chmod_auth_keys:
        if _change_authorized_keys_permission(host, user, password) is False:
            return False
    local_home = _get_home_dir(local_user)
    cmd = "ssh-copy-id -i %s/.ssh/%s %s@%s" % (local_home, pub_key, user, host)
    print(cmd)
    child = pexpect.spawn(cmd)
    try:
        time.sleep(2)
        print(child.before)
        index = child.expect(
            ['[Pp]assword:', "continue connecting (yes/no)?"], timeout=10)
        print(index)
        if index == 0:
            print("Send password '%s'" % password)
            child.sendline(password)
            child.expect(pexpect.EOF)
        elif index == 1:
            print("Send yes ")
            child.sendline("yes\n")
            child.expect('[Pp]assword')
            print("Send password %s" % password)
            child.sendline(password)
            child.expect(pexpect.EOF)
        else:
            print("Not matched")
            print(child.before)
            child.sendline(password)
            child.expect(pexpect.EOF)

        print(child.before)
        child.close()
        return True
    except pexpect.EOF:
        print("ERROR: %s" % child.before)
        child.close()
        return False
    except pexpect.TIMEOUT:
        print("ERROR: %s" % child.before)
        print("Time out.")
        child.close()
        return False


def _change_authorized_keys_permission(host, user="root", password="changeme"):
    print("Update the permission for the authorized_keys file to writeable")
    home = _get_home_dir(user)
    ssh_dir = os.path.join(home, ".ssh")
    authorized_keys = os.path.join(ssh_dir, "authorized_keys")
    cmd = "mkdir %s ; ls %s || touch %s" % (ssh_dir, authorized_keys, authorized_keys)
    execute_command(cmd, host, user, password)
    chmod_cmd = "chmod 600 %s" % authorized_keys
    execute_command(chmod_cmd, host, user, password)


from ssh_utils import SSHConnection


def execute_command(cmd, host, user, password):
    ssh = SSHConnection(host=host, username=user, password=password)
    if not ssh.connect():
        return False
    ssh.cmd(cmd)
    ssh.close()
    return True


def _execute_command(remote_cmd, host, user, password):
    cmd = "ssh %s@%s '%s'" % (user, host, remote_cmd)
    print(cmd)
    child = pexpect.spawn(cmd)
    try:
        index = child.expect(
            ['Password:', "continue connecting (yes/no)?"], timeout=10)
        if index == 0:
            child.sendline(password)
            child.expect(pexpect.EOF)
        elif index == 1:
            child.sendline("yes\n")
            child.expect('[Pp]assword:')
            child.sendline(password)
            child.expect(pexpect.EOF)
        print(child.before)
        child.close()
        return True
    except pexpect.EOF:
        print("ERROR: %s" % child.before)
        child.close()
        return False
    except pexpect.TIMEOUT:
        print("ERROR: %s" % child.before)
        print("Time out.")
        child.close()
        return False


def _get_home_dir(user):
    home = "/home/%s" % user
    if user == "root":
        home = "/root"
    return home


if __name__ == "__main__":
    fire.Fire(distribute_ssh_key)
