#!/usr/bin/env python
# encoding: utf-8

"""
@version: v1.0
@author: Gaivin Wang
@license: Apache Licence
@contact: gaivin@outlook.com
@site: https://github.com/gaivin/
@software: PyCharm
@file: json_utils.py
@time: 6/8/2018 3:43 PM
"""
import json
from datetime import datetime, date
from functools import partial

json_loads = json.loads


class CJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime("%Y-%m-%d")
        else:
            return json.JSONEncoder.default(self, obj)


obj_dumps = partial(json.dumps, cls=CJsonEncoder)
