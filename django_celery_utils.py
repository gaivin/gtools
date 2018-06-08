#!/usr/bin/env python
# encoding: utf-8

"""
@version: v1.0
@author: Gaivin Wang
@license: Apache Licence
@contact: gaivin@outlook.com
@site: https://github.com/gaivin/
@software: PyCharm
@file: django_celery_utils.py
@time: 6/8/2018 3:43 PM
"""

from celery import states
from djcelery.models import TaskState, TaskMeta
from django.forms.models import model_to_dict
from django.core.exceptions import ObjectDoesNotExist
from .logger import get_logger

logger = get_logger(__name__)


def get_task_info(task_id):
    try:
        tasks_status = TaskState.objects.get(task_id=task_id)
        status_fields = ['state', 'task_id', 'name', 'args', 'kwargs','result',
                         'eta', 'runtime', 'worker', 'tstamp', 'traceback']
        task_status_dict = model_to_dict(tasks_status, fields=status_fields)
    except ObjectDoesNotExist as ex:
        logger.error("Cannot found the task [%s] in TaskState table. Error; %s" % (task_id, ex.message))
        task_status_dict = {}

    return task_status_dict

def get_task_details_by_id(task_id, task_details=None, with_sub_task=True, update_parent_task_status=True):
    if task_details is None:
        task_details = []
    children = None
    try:
        tasks_status = TaskState.objects.get(task_id=task_id)
        status_fields = ['state', 'task_id', 'name', 'args', 'kwargs',
                         'eta', 'runtime', 'worker', 'tstamp']
        task_status_dict = model_to_dict(tasks_status, fields=status_fields)
        if task_details:
            task_status_dict["type"] = "sub_task"
        else:
            task_status_dict["type"] = "main_task"
    except ObjectDoesNotExist as ex:
        logger.error("Cannot found the task [%s] in TaskState table. Error; %s" % (task_id, ex.message))
        task_status_dict = {}

    try:
        tasks_meta = TaskMeta.objects.get(task_id=task_id)
        task_meta_dict = _get_task_meta_dic(tasks_meta)
        children = _get_task_child_from_task_dic(task_meta_dict)
        task_meta_dict["children"] = children
    except ObjectDoesNotExist as ex:
        logger.warn("Task should be running. Cannot found the task [%s] in TaskMeta table. %s" % (task_id, ex.message))
        task_meta_dict = {}

    task_status_dict.update(task_meta_dict)
    if task_status_dict:
        status = task_status_dict.pop("state", None)
        if status:
            task_status_dict["status"] = status
        task_details.append(task_status_dict)
    else:
        logger.error("No info found for task [%s]" % task_id)
        return None
    logger.debug("TaskDetails: %s" % task_details)
    if update_parent_task_status:
        task_details[0]["status"] = _get_status(parent_task_status=task_details[0]["status"],
                                                children_task_status=task_status_dict["status"])
    if children and with_sub_task:
        return get_task_details_by_id(children, task_details, with_sub_task)
    else:
        return task_details


def _get_task_child_from_task_dic(task_dic):
    children = task_dic.get("children", [])
    if children:
        return children[0][0][0]
    else:
        logger.warning("No children task found for the task %s" % task_dic)
        return None


def _get_status(parent_task_status, children_task_status):
    print("Parentask: %s" % parent_task_status)
    print("Childrentask: %s" % children_task_status)
    if parent_task_status == states.SUCCESS:
        return children_task_status
    else:
        return parent_task_status


def _get_task_meta_dic(task_meta_object):
    """

    :rtype: A dict of the task meta =
    """
    return task_meta_object.to_dict()


def _get_task_status_dic(task_status_object):
    """

    :rtype: A dict of the task status
    """

    return task_status_object
