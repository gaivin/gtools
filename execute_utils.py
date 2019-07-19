#!/usr/bin/env python  
# encoding: utf-8  

""" 
@version: v1.0 
@author: Gaivin Wang 
@license: Apache Licence  
@contact: gaivin@outlook.com
@site:  
@software: PyCharm 
@file: execute_utils.py 
@time: 7/9/2019 10:39 AM 
"""
import subprocess
from logger_utils import get_logger
import fire

logger = get_logger("executor")


def execute(cmd, ignore_error=False):
    print("INFO: Execute command  '%s'" % cmd)
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = "".join(process.stdout.readlines())
    process.communicate()
    status = process.returncode
    if status != 0:
        log = logger.warning if ignore_error else logger.error
        log("Run command '%s' failed." % cmd)
        log("ERROR code: %s. OUTPUT: %s" % (status, output))
    else:
        logger.info("Run command '%s' successful." % cmd)
        logger.info("%s" % output)
    return status, output
