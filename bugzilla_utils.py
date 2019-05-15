#!/usr/bin/env python  
# encoding: utf-8  

""" 
@version: v1.0 
@author: Gaivin Wang 
@license: Apache Licence  
@contact: gaivin@outlook.com
@site:  
@software: PyCharm 
@file: bugzilla_utils.py 
@time: 3/26/2019 9:30 AM 
"""
import requests, json
from csv import DictReader
import urllib3

urllib3.disable_warnings()


class Bugzilla():
    def __init__(self, host="https://bugs.avamar.com"):
        self.host = host

    def login(self, user_name, password):
        self.session = requests.session()
        login_url = "%s/index.cgi" % self.host
        goahead_and_login = [1, "Log+in"]
        data = self._generate_form_data(Bugzilla_login=user_name, Bugzilla_password=password,
                                        Bugzilla_restrictlogin="on",
                                        GoAheadAndLogin=goahead_and_login)
        print("======================")

        response = self.session.post(login_url, files=data, verify=False)
        if response.status_code != 200:
            print("ERROR: Login Bugzilla failed. Please check your user and password (%s/%s). " % (user_name, password))
            print("ERROR: %s" % response.text)
            raise Exception(message="Login failed")
        print("INFO: Login Bugzilla successfully!")
        return self.session

    def _generate_form_data(self, **form_data_kwargs):
        form_data = dict()
        for key, value in form_data_kwargs.items():
            if isinstance(value, str):
                form_data[key] = (None, value)
            else:
                form_data[key] = (None, json.dumps(value))
        return form_data

    def export_bugs_to_csv_by_bug_id(self, bug_ids, fields, csv_file=None):
        print("INFO: Export bugs %s with fields %s" % (bug_ids, fields))
        parameters = dict()
        parameters["j_top"] = "OR"
        parameters["ctype"] = "csv"
        parameters["human"] = "1"
        parameters["query_format"] = "advanced"

        for index, bug_id in enumerate(bug_ids):
            filed = "f%s" % index
            operate = "o%s" % index
            value = "v%s" % index
            parameters[filed] = "bug_id"
            parameters[operate] = "equals"
            parameters[value] = bug_id

        columnlist = ",".join(fields)
        parameters["columnlist"] = columnlist
        self.session.params = parameters
        return self._export_bugs_with_parameters(parameters=parameters, csv_file=csv_file)

    def export_bugs_to_csv_by_list(self, list_id, fields, csv_file=None):
        parameters = dict()
        parameters["ctype"] = "csv"
        parameters["human"] = "1"
        parameters["query_format"] = "advanced"
        parameters["list_id"] = list_id
        parameters["product"] = "File System Agent Boost"
        columnlist = ",".join(fields)
        parameters["columnlist"] = columnlist
        return self._export_bugs_with_parameters(parameters=parameters, csv_file=csv_file)

    def _export_bugs_with_parameters(self, parameters, csv_file=None):
        self.session.params = parameters
        response = self.session.get("%s/buglist.cgi" % self.host)
        if response.status_code != 200:
            print("ERROR: Get bug list failed with parameters" % parameters)
            print(response.text)
            raise Exception(message="Get bugs failed")

        if csv_file is None:
            csv_file = self._get_file_name_from_header(response)

        with open(csv_file, "w") as csvfile:
            csvfile.write(response.text)

        return csv_file

    def _get_file_name_from_header(self, response):
        disposition = response.headers.get("Content-disposition", None)
        csv_file = "NotFound"
        if disposition:
            if "filename=" in disposition:
                csv_file = disposition.replace('"', '').split("filename=")[1]
        return csv_file


if __name__ == "__main__":
    bz = Bugzilla()
    bz.login(user_name="wangg27", password="WEurfn_-+=")
    list_id = "2525477"
    bugs = [305610]
    fields = ["priority", "assigned_to", "reporter", "bug_status", "short_desc", "opendate", "target_milestone",
              "cf_esc_source", "resolution", "cf_build_number", "changeddate", "cf_dev_contact", "qa_contact",
              "cf_resolver", "cf_resolve_date", "bug_severity", "cf_tc_id", "bug_file_loc", "cf_target_date", "product"]

    bugs = bz.export_bugs_to_csv_by_list(list_id=list_id, fields=fields)