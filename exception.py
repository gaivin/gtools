#!/usr/bin/env python
# encoding: utf-8

"""
@version: v1.0
@author: Gaivin Wang
@license: Apache Licence
@contact: gaivin@outlook.com
@site: https://github.com/gaivin/
@software: PyCharm
@file: exception.py
@time: 6/8/2018 3:43 PM
"""


class BaseException(Exception):
    type = "BASE_ERROR"


class RequestDataError(BaseException):
    def __init__(self, message):
        self.message = message
        self.type = "REQUEST_DATA_ERROR"


class RequestDataFormatError(BaseException):
    def __init__(self, message):
        self.message = message
        self.type = "REQUEST_DATA_FORMAT_ERROR"


class RequestMethodError(BaseException):
    def __init__(self, message):
        self.message = message
        self.type = "REQUEST_METHOD_ERROR"
