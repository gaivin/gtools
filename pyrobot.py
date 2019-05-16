#!/usr/bin/env python
# encoding: utf-8
"""
@version: v1.0
@author: Gaivin Wang
@license: Apache Licence
@contact: gaivin@outlook.com
@site: https://github.com/gaivin/
@software: PyCharm
@file: pyrobot.py
@time: 5/13/2019 10:00 AM
"""

import subprocess
import os
import fire
import sys
from logger_utils import get_logger

logger = get_logger("pyrobot")


def robot(test, include=None, exclude=None, variable=None, debug=None, rerun_failed=False, robot_executor="pybot",
          rebot_executor="rebot", **robot_kwargs):
    output = "output.xml"
    outputdir = os.path.abspath(os.path.curdir)
    cmd = robot_executor
    if exclude:
        cmd += _generate_options(option_type="exclude", values=exclude)
    if variable:
        cmd += _generate_options(option_type="variable", values=variable)
    if include:
        cmd += _generate_options(option_type="include", values=include)
    if debug:
        cmd += _generate_options(option_type="debug", values=debug)
    for option, values in robot_kwargs.items():
        if option == "outputdir":
            outputdir = values

        if option == "output":
            output = values
        cmd += _generate_options(option_type=option, values=values)
    cmd += test
    robot_status = execute(cmd)
    if robot_status != 0:
        logger.error("Run test %s failed." % test)
    else:
        logger.info("Run test %s passed." % test)

    if rerun_failed and robot_status:
        first_run_output_dir = os.path.join(outputdir, "first_run")
        logger.info("Move the first output to first_run folder")
        execute("mkdir -p %s" % first_run_output_dir)
        mv_cmd = "mv %s/*.* %s/" % (outputdir, first_run_output_dir)
        execute(mv_cmd)
        rerun_output_dir = os.path.join(outputdir, "rerun")
        first_run_result_xml = os.path.join(first_run_output_dir, output)
        rerun_cmd = "%s --rerunfailed %s" % (robot_executor, first_run_result_xml) \
                    + _generate_options(option_type="variable", values=variable) \
                    + _generate_options(option_type="output", values=output) \
                    + _generate_options(option_type="outputdir", values=rerun_output_dir) \
                    + test
        logger.debug("rerun_cmd: %s" % rerun_cmd)

        robot_status = execute(rerun_cmd)
        if robot_status != 0:
            logger.error("Re Run test %s failed." % test)
        else:
            logger.info("Re Run test %s passed." % test)

        logger.info("Start Merge the results...")
        rerun_result_xml = os.path.join(rerun_output_dir, output)
        merge_result_cmd = "%s " % rebot_executor \
                           + _generate_options(option_type="outputdir", values=outputdir) \
                           + _generate_options(option_type="output", values=output) \
                           + " --merge %s %s" % (first_run_result_xml, rerun_result_xml)
        merge_status = execute(merge_result_cmd)
        if merge_status != 0:
            logger.error("Merge rerun result %s with original result %s failed." % (
                rerun_result_xml, first_run_result_xml))
        else:
            logger.info("Rerun result has been merged to %s successfully." % outputdir)

    return robot_status


def execute(cmd):
    logger.info("Execute command  '%s'" % cmd)
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for c in iter(lambda: process.stdout.read(1), ''):
        sys.stdout.write(c)
    process.communicate()
    status = process.returncode
    return status


def _generate_options(option_type, values=list()):
    result = ""
    if isinstance(values, str):
        values = values.replace(";", ",").replace(" ", ",").split(",")
    elif not isinstance(values, list):
        logger.error("The options value should be string or list, not %s." % type(values))
        return None
    for value in values:
        result += " --%s %s " % (option_type, value)
    return result


if __name__ == "__main__":
    fire.Fire(robot)
