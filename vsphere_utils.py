#!/usr/bin/env python  
# encoding: utf-8  

""" 
@version: v1.0 
@author: Gaivin Wang 
@license: Apache Licence  
@contact: gaivin@outlook.com
@site:  
@software: PyCharm 
@file: vsphere_utils.py 
@time: 7/16/2019 6:12 PM 
"""

from pysphere import VIServer, vi_snapshot, vi_virtual_machine
from pysphere.vi_task import VITask
import pysphere.resources.VimService_services as VI
from pysphere.resources.vi_exception import VIException, FaultTypes, VIApiException
from fire import Fire
import time

import ssl
import datetime

default_context = ssl._create_default_https_context
ssl._create_default_https_context = ssl._create_unverified_context


class Vcenter(VIServer):

    def create_vm_snapshot(self, snapshot_name, vm_name, vm_datacenter=None, description=None, force=False,
                           sync_run=True, dump_memory=False):
        vm = self.get_vm_by_name(name=vm_name, datacenter=vm_datacenter)
        return self._create_vm_snapshot(virtual_machine=vm, snapshot_name=snapshot_name, description=description,
                                        force=force, sync_run=sync_run, dump_memory=dump_memory)

    def create_vms_snapshot_for_resource_pool(self, snapshot_name, resource_pool_name, description=None, sync_run=False,
                                              **kwargs):
        if not resource_pool_name.startswith("/Resources/"):
            print("ERROR: Resource pool name should start with '/Resources/'")
            return False
        vms_path = self.get_registered_vms(resource_pool=resource_pool_name)
        failed_vms = []
        for vm_path in vms_path:
            vm = self.get_vm_by_path(path=vm_path)
            try:
                self._create_vm_snapshot(virtual_machine=vm, snapshot_name=snapshot_name, description=description,
                                         sync_run=sync_run, **kwargs)
            except Exception as e:
                print("ERROR: %s" % e)
                failed_vms.append(vm.get_property("name"))
        if failed_vms:
            print("These VMs create snapshot failed. %s" % failed_vms)

    def revert_vm_snapshot(self, vm_name, snapshot_name, sync_run=True, vm_datacenter=None):
        vm = self.get_vm_by_name(name=vm_name, datacenter=vm_datacenter)
        return self._revert_vm_snapshot(virtual_machine=vm, snapshot_name=snapshot_name, sync_run=sync_run)

    def delete_vm_snapshot(self, vm_name, snapshot_name, sync_run=True, vm_datacenter=None):
        vm = self.get_vm_by_name(name=vm_name, datacenter=vm_datacenter)
        return self._delete_vm_snapshot(virtual_machine=vm, snapshot_name=snapshot_name, sync_run=sync_run)

    def rename_vm(self, vm_name, new_vm_name, sync_run=True):
        vm = self.get_vm_by_name(name=vm_name)
        result = self._rename_vm(virtual_machine=vm, new_vm_name=new_vm_name, sync_run=sync_run)
        if result is None:
            result = True
            print("INFO: Rename vm '%s' to '%s' successfully." % (vm_name, new_vm_name))
        else:
            info = result.get_info()
            info_obj = info._obj
            print("INFO: %s '%s' with eventChainId '%s' is submitted." % (
                info_obj.Name, info_obj.Task, info_obj.EventChainId))
        return result

    def power_on_vm(self, vm_name, sync_run=True, vm_user=None, vm_password=None, check_timeout_seconds=0):
        vm = self.get_vm_by_name(name=vm_name)
        if vm.get_status() == vi_virtual_machine.VMPowerState.POWERED_ON:
            print("VM '%s' already powered on." % vm_name)
            return True
        result = vm.power_on(sync_run=sync_run)
        if vm_user and vm_password and check_timeout_seconds:
            check_count = 0
            rest_seconds = check_timeout_seconds
            vm_tool_status = vm.get_tools_status()
            while rest_seconds > 0:
                if vm_tool_status == vi_virtual_machine.ToolsStatus.NOT_RUNNING:
                    check_count += 1
                    sleep_time = check_count * 2
                    rest_seconds -= sleep_time
                    print("INFO: Wait %s seconds to check..." % sleep_time)
                    time.sleep(sleep_time)
                    vm_tool_status = vm.get_tools_status()
                elif vm_tool_status == vi_virtual_machine.ToolsStatus.RUNNING:
                    print("INFO: VM tool is running.")
                    return vm
                else:
                    print("ERROR: VM tool status is %s. Please check the vm tool." % vm_tool_status)
                    return False
            if rest_seconds <= 0:
                print("ERROR: VM is not startup in %s seconds. VM tool status is %s" % (
                check_timeout_seconds, vm_tool_status))
                return False

        if result is None:
            result = True
            print("INFO: Poweron vm '%s'  successfully." % vm_name)
        else:
            info = result.get_info()
            info_obj = info._obj
            print("INFO: %s '%s' with eventChainId '%s' is submitted." % (
                info_obj.Name, info_obj.Task, info_obj.EventChainId))
        return result

    def power_off_vm(self, vm_name, sync_run=True):
        vm = self.get_vm_by_name(name=vm_name)
        if vm.get_status() == vi_virtual_machine.VMPowerState.POWERED_OFF:
            print("VM '%s' already powered off." % vm_name)
            return True
        result = vm.power_off(sync_run=sync_run)
        if result is None:
            result = True
            print("INFO: Power off vm '%s'  successfully." % vm_name)
        else:
            info = result.get_info()
            info_obj = info._obj
            print("INFO: %s '%s' with eventChainId '%s' is submitted." % (
                info_obj.Name, info_obj.Task, info_obj.EventChainId))
        return result

    def _rename_vm(self, virtual_machine, new_vm_name, sync_run=True):
        request = VI.Rename_TaskRequestMsg()
        mor_snap = request.new__this(virtual_machine._mor)
        mor_snap.set_attribute_type(virtual_machine._mor.get_attribute_type())
        request.set_element__this(mor_snap)
        request.set_element_newName(new_vm_name)

        task = self._proxy.Rename_Task(request)._returnval
        vi_task = VITask(task, self)
        if sync_run:
            status = vi_task.wait_for_state([vi_task.STATE_SUCCESS, vi_task.STATE_ERROR])
            if status == vi_task.STATE_ERROR:
                raise VIException(vi_task.get_error_message(),
                                  FaultTypes.TASK_ERROR)
            return
        return vi_task

    def _revert_vm_snapshot(self, virtual_machine, snapshot_name, sync_run=True):
        vm_name = virtual_machine.get_property("name")
        print("INFO: Revert vm '%s' to snapshot '%s'..." % (vm_name, snapshot_name))
        exist_snapshots_names = map(vi_snapshot.VISnapshot.get_name, virtual_machine.get_snapshots())
        if snapshot_name not in exist_snapshots_names:
            print("WARNING: Snapshot '%s' is not not exist in vm '%s'." % (snapshot_name, vm_name))
            return False
        result = virtual_machine.revert_to_named_snapshot(name=snapshot_name, sync_run=sync_run)
        if result is None:
            result = True
            print("INFO: Revert vm '%s' to snapshot '%s' successfully." % (vm_name, snapshot_name))
        else:
            info = result.get_info()
            info_obj = info._obj
            print("INFO: %s '%s' with eventChainId '%s' is submitted." % (
                info_obj.Name, info_obj.Task, info_obj.EventChainId))
        return result

    def _delete_vm_snapshot(self, virtual_machine, snapshot_name, sync_run=True):
        vm_name = virtual_machine.get_property("name")
        print("INFO: Remove snapshot '%s' for vm '%s'..." % (snapshot_name, vm_name))
        exist_snapshots_names = map(vi_snapshot.VISnapshot.get_name, virtual_machine.get_snapshots())
        if snapshot_name not in exist_snapshots_names:
            print("WARNING: Snapshot '%s' is not not exist in vm '%s'." % (snapshot_name, vm_name))
            return False
        result = virtual_machine.delete_named_snapshot(name=snapshot_name, sync_run=sync_run)
        if result is None:
            result = True
            print("INFO: Remove snapshot '%s' for vm '%s' successfully." % (snapshot_name, vm_name))
        else:
            info = result.get_info()
            info_obj = info._obj
            print("INFO: %s '%s' with eventChainId '%s' is submitted." % (
                info_obj.Name, info_obj.Task, info_obj.EventChainId))

        return result

    def _create_vm_snapshot(self, virtual_machine, snapshot_name, description=None, force=False, sync_run=True,
                            dump_memory=False):
        vm_name = virtual_machine.get_property("name")
        print("INFO: Create Snapshot for '%s'..." % vm_name)
        exist_snapshots_names = map(vi_snapshot.VISnapshot.get_name, virtual_machine.get_snapshots())
        if snapshot_name in exist_snapshots_names and force is False:
            print("WARNING: '%s' already have snapshot with name '%s'." % (vm_name, snapshot_name))
            return False
        current_time = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        if description is None:
            description = current_time
        else:
            description = "%s: \n %s" % (current_time, description)

        result = virtual_machine.create_snapshot(name=snapshot_name, description=description, sync_run=sync_run,
                                                 memory=dump_memory)
        if result is None:
            result = True
            print("INFO: Create Snapshot for '%s' successfully." % vm_name)
        else:
            info = result.get_info()
            info_obj = info._obj
            print("INFO: %s '%s' with eventChainId '%s' is submitted." % (
                info_obj.Name, info_obj.Task, info_obj.EventChainId))
        return result


if __name__ == "__main__":
    Fire(Vcenter)
