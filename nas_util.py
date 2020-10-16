import re
import random
import os
from commands import getstatusoutput
from fire import Fire


def execute(cmd, ignore_error=True, verbose=False):
    if verbose:
        print("Execute: %s" % cmd)
    status, output = getstatusoutput(cmd)
    if status != 0:
        print("ERROR: %s" % output)
        if ignore_error:
            return None
        else:
            raise Exception("Execute command in error. %s" % output)
    else:
        if verbose:
            print("Output: %s" % output)
        return output


def get_nas_acl(path, mount_type="cifs", user=None):
    # Get Config

    # Get Acl
    get_acl_tool = "getcifsacl" if mount_type == "cifs" else "nfs4_getfacl"
    user_pattern = "%s:" % user if mount_type == "cifs" else "%s@" % user
    get_acl_cmd = "%s %s" % (get_acl_tool, path) if user is None else "%s %s | grep %s" % (
        get_acl_tool, path, user_pattern)
    output = execute(get_acl_cmd)
    return output


def get_cifs_owner(path):
    owner_string = get_nas_acl(path=path, mount_type="cifs", user="OWNER")

    owner_pattern = "OWNER:(.*)"
    matched_names = re.findall(pattern=owner_pattern, string=owner_string)
    if matched_names:
        return matched_names[0]
    else:
        print("ERROR: Cannot find the owner info in %s" % owner_string)
        exit(-1)


def set_file_cifs_acl(path, user=None, acl=None, allow_deny=None, flags=None, operation=None):
    acl_spec_list = ["READ", "CHANGE", "FULL"]
    allow_deny_list = ["ALLOWED", "DENIED"]
    operation_list = ["a", "M"]
    if user is None:
        owner = get_cifs_owner(path)
        user = owner
    if acl is None:
        acl = random.choice(acl_spec_list)
    if allow_deny is None:
        allow_deny = random.choice(allow_deny_list)
    if operation is None:
        operation = random.choice(operation_list)
    if flags is None:
        dec_flags = random.randint(0, 31)
        hex_flags = hex(dec_flags)
        flags = hex_flags
    set_cifs_acl_cmd = "setcifsacl -%s ACL:%s:%s/%s/%s %s" % (operation, user, allow_deny, flags, acl, path)
    execute(set_cifs_acl_cmd, ignore_error=False)
    acl_string = get_nas_acl(path=path, mount_type="cifs", user=user)
    return acl_string


def set_file_nfs_acl(path, user="fsa", flag=None, acl=None, allow_deny=None, group_or_not=False):
    acl_spec_list = ["R", "W", "X", "RW", "RX", "RWX", "WX"]
    allow_deny_list = ["A", "D"]
    if acl is None:
        acl = random.choice(acl_spec_list)
    if allow_deny is None:
        allow_deny = random.choice(allow_deny_list)
    if flag is None:
        flag = "-a"
    user_group_flag = "g" if group_or_not is True else ""
    set_nfs_acl_cmd = "nfs4_setfacl %s %s:%s:%s:%s %s" % (flag, allow_deny, user_group_flag, user, acl, path)
    execute(set_nfs_acl_cmd, ignore_error=False)
    acl_string = get_nas_acl(path=path, mount_type="nfs", user=user)
    return acl_string


def set_nas_files_acl(files, user=None, mount_type="cifs"):
    files_acl_dict = dict()
    for _file in files:
        if mount_type == "cifs":
            acls = set_file_cifs_acl(path=_file, user=user)
        else:
            acls = set_file_nfs_acl(path=_file, user=user)
        files_acl_dict[_file] = acls
    return files_acl_dict


def set_nas_folder_acl(folder, user=None):
    mount_info = get_mount_type(folder)
    if mount_info:
        mount_type = mount_info["mount_type"]
        set_nas_acl = set_file_cifs_acl if mount_type == "cifs" else set_file_nfs_acl
    else:
        exit(1)
    for root, dirs, files in os.walk(folder):
        for _file in files:
            set_nas_acl(path=os.path.join(root, _file), user=user)
    return True


def get_mount_point(path):
    while True:
        if path == os.path.dirname(path):
            print("ERROR: It is not a mount path.")
            return None
        elif os.path.ismount(path):
            print("DEBUG: Found mount dir: %s" % path)
            if path.endswith(os.path.sep):
                path = path[0:-1]
            return path
        path = os.path.dirname(path)


def get_mount_type(path):
    mount_point = get_mount_point(path)
    if mount_point:
        mount_cmd = "mount | grep %s" % mount_point
        mount_info = execute(mount_cmd, ignore_error=False)
        mount_pattern = "(.*) on (%s) type (.*) \(.*vers=(\d+\.?\d*)," % mount_point
        matches = re.findall(pattern=mount_pattern, string=mount_info)
        if matches:
            return {"mount_source": matches[0][0], "mount_point": matches[0][1], "mount_type": matches[0][2],
                    "version": matches[0][3]}
        else:
            print("ERROR: Could not found the mount info from %s" % mount_info)
            return None
    else:
        print("ERROR: The path %s is not a mount path. " % path)
        return None


def get_cifs_attr(path, attribute="creationtime"):
    attributes = ("dosattrib", "creationtime")
    if attribute not in attributes:
        print("ERROR: %s is not in %s" % (attribute, attributes))
        return None
    if not os.path.exists(path):
        print("ERROR: %s is not exist" % path)
        return None
    mount_info = get_mount_type(path)
    if not mount_info:
        print("ERROR: %s is not a mount path" % path)
        return None
    mount_type = mount_info["mount_type"]
    if mount_type != "cifs":
        print("ERROR: %s is a %s mount. Not a cifs mount" % (path, mount_type))
        return None
    get_attr_cmd = "getfattr  -n user.cifs.%s %s" % (attribute, path)
    output = execute(get_attr_cmd, ignore_error=False)
    return output


if __name__ == "__main__":
    Fire()
