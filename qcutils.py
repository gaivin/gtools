#!/usr/bin/env python  
# encoding: utf-8  

""" 
@version: v1.0 
@author: Gaivin Wang 
@license: Apache Licence  
@contact: gaivin@outlook.com
@site:  
@software: PyCharm 
@file: qcutils.py
@time: 2/27/2019 6:17 PM 
"""
import requests
import time
import json
import functools
import fire
from collections import OrderedDict


class ALM_REST_LIB():
    host = None
    session = None

    def __init__(self, host, domain, project, return_type="application/json", accept="application/json"):
        self.host = host
        self.domain = domain
        self.project = project
        self.base_url = "%s/qcbin/rest/domains/%s/projects/%s" % (self.host, self.domain, self.project)
        self.return_type = return_type
        self.accept = accept

        self.get = functools.partial(self._request, method="get")
        self.post = functools.partial(self._request, method="post")
        self.put = functools.partial(self._request, method="put")
        self.delete = functools.partial(self._request, method="delete")

    def _request(self, method, url, data=None, params=None, headers=None, **request_kwargs):
        """
        Sent the request to QC REST server
        :param method:  The request method. Such as: GET, POST, DELETE, PUT...
        :param url:     URL for the request
        :param data:    DATA for post request
        :param params:  Request parameters
        :param headers: Request headers.
        :param request_kwargs:  Other request args.
        :return:
        """
        request_method = method.lower()
        print("DEBUG: Method: %s" % request_method)
        if request_method not in ["get", "post", "put", "delete"]:
            print("ERROR: Method [%s] is not available for ALM class" % method)
            return None
        if hasattr(self.session, request_method):
            request = getattr(self.session, request_method)
        else:
            print("ERROR: Session does not have [%s] attribute." % request_method)
            return None
        if data:
            if isinstance(data, dict):
                data = json.dumps(data)
            print("DEBUG: Data: %s" % data)

        parameters = dict(alt=self.return_type)
        if params:
            params.update(**parameters)

        print("DEBUG: Parameters: %s" % params)

        _headers = dict(Accept=self.accept)
        _headers["Content-Type"] = self.accept
        if headers:
            _headers.update(**headers)
        print("DEBUG: Headers: %s" % _headers)
        print("DEBUG: URL: %s" % url)

        response = request(url=url, data=data, params=params, headers=_headers, **request_kwargs)
        print("DEBUG: Status: %s" % response.status_code)
        return response

    def login(self, user_name, password):
        self.session = requests.session()
        self.session.auth = (user_name, password)
        login_url = "%s/qcbin/api/authentication/sign-in" % self.host
        response = self.session.get(login_url)
        if response.status_code != 200:
            print("ERROR: Login ALM failed. Status Code: %s" % response.status_code)
            print("ERROR: Message: %s" % response.text)
            return False
        else:
            print("Login ALM Successfully. ")
            return True

    def get_entity_fields(self, entity_type, required=True):
        """
        Get all the entities info
        :param entity_type:
        :param required:
        :return:
        """
        url = "%s/customization/entities/%s/fields" % (self.base_url, entity_type)
        parameters = dict(required=required)
        response = self.get(url=url, params=parameters)
        return response.text

    def get_test_configuration_id(self, test_id, only_one=True):
        return self.get_entity_id_by_filter(entity_type="test-configs", only_one=only_one, parent_id=test_id)

    def get_test_set_folder_id(self, name, only_one=True):
        return self.get_entity_id_by_filter(entity_type="test-set-folders", only_one=only_one,
                                            name=name)

    def is_case_id_exist(self, test_id):
        found_id = self.get_entity_id_by_filter(entity_type="tests", id=test_id)
        if found_id:
            return True
        else:
            return False

    def get_test_set_id(self, name, status="Open", only_one=True):
        return self.get_entity_id_by_filter(entity_type="test-sets", only_one=only_one, name=name,
                                            status=status)

    def get_test_instance_id(self, test_set_id, test_id, only_one=True):
        return self.get_entity_id_by_filter(entity_type="test-instances", only_one=only_one, test_id=test_id,
                                            cycle_id=test_set_id)

    def create_test_instance(self, test_id, test_set_id, test_config_id, owner, subtype_id="hp.qc.test-instance.MANUAL",
                             **field_kwargs):
        return self.create_entity(entity_type="test-instances", test_id=test_id, cycle_id=test_set_id,
                                  test_config_id=test_config_id, subtype_id=subtype_id, owner=owner, **field_kwargs)

    def create_test_set(self, name, parent_id, status="Open", subtype_id="hp.qc.test-set.default", **field_kwargs):
        return self.create_entity(entity_type="test-sets", fields="name,id", name=name,
                                  parent_id=parent_id, status=status, subtype_id=subtype_id, **field_kwargs)

    def create_test_run(self, name, test_set_id, test_id, test_instance_id, owner, status="Not Completed",
                        test_instance=1, subtype_id="hp.qc.run.MANUAL"):
        """
        Create a test run with status not completed.
        :param name: Test run name
        :param test_set_id: cycle-id, Test set id
        :param test_id:     Test case id
        :param test_instance_id: testcycl-id, Test instance id
        :param owner: Tester
        :param status: Test result
        :param test_instance: Test instance
        :param subtype_id:  Manually
        :return:  Test run id
        """
        return self.create_entity(entity_type="runs", name=name, cycle_id=test_set_id,
                                  testcycl_id=test_instance_id, test_instance=test_instance, test_id=test_id,
                                  owner=owner, subtype_id=subtype_id, status=status)

    def update_test_run(self, test_run_id, result="Passed", **field_kwargs):
        """
        Update the result for the test run.
        :param test_run_id: Test Run ID
        :param result: Test result
        :param field_kwargs: test-instance, execution-date, ver-stamp, test-config-id, name, has-linkage, testcycl-id,
                        cycle-id, host, test-id, subtype-id, draft, duration, owner
        :return: True: successful, False: Failed
        """
        url = "%s/runs/%s" % (self.base_url, test_run_id)
        execution_date = time.strftime("%Y-%m-%d", time.localtime())
        field_kwargs.update(execution_date=execution_date, status=result)
        data = self._generate_fileds(**field_kwargs)
        parameters = dict(fields="id,name,testcycl-id,owner,test-id,subtype-id")
        response = self.put(url=url, data=data, params=parameters)

        if response.status_code == 200:
            print("INFO: Test run [%s] is updated to %s " % (test_run_id, data))
            return True
        else:
            print("ERROR: [%s] Test run update failed. [%s]" % (response.status_code, response.text))
            return False

    def create_entity(self, entity_type, fields="name,id", retry=0, **field_kwargs):
        """
        Create a QC entity with data
        :param entity_type:  The entity type. Such as: test-sets, runs, test-instances
        :param fields:  Return fields in the response
        :param retry: If creation failed. How many times you want to retry.
        :param field_kwargs:  Fields key value of the data in request.
        :return: New entity id or None for failed creation
        """
        url = "%s/%s" % (self.base_url, entity_type)
        data = self._generate_fileds(**field_kwargs)
        parameters = dict(fields=fields)
        try_count = 0
        while True:
            response = self.post(url=url, data=data, params=parameters)
            if response.status_code == 201:
                entity_id = self._get_entity_id_from_response(response)
                print("INFO: Entity %s [%s] created" % (entity_type, entity_id))
                return entity_id
            else:
                try_count += 1
                if try_count <= retry:
                    print("INFO: Create entity %s failed. Try again..." % entity_type)
                    time.sleep(10)
                else:
                    break

        print("ERROR: [%s] Test set create failed. [%s]" % (response.status_code, response.text))
        return None

    def get_entity_id_by_filter(self, entity_type, fields="name,id", only_one=True, **filter_kwargs):
        """
        Get the entity id by search the field values with filter.
        :param entity_type: The type of the entity
        :param fields:  The return field of the request response.
        :param only_one:  Do you want to get only one result from a result set.
        :param filter_kwargs:  The filters used to narrow the result. If the key name has "-", Use "_" instread.
        :return: entity id or entities id
        """
        url = "%s/%s" % (self.base_url, entity_type)
        query_string = self._generate_query_string(**filter_kwargs)
        parameters = dict(fields=fields, query=query_string)
        response = self.get(url=url, params=parameters)
        entities_id = self._get_entities_id_from_response(response)
        if entities_id:
            if only_one:
                return max(entities_id)  # Use max to get the newest entity
            else:
                return entities_id
        else:
            print("ERROR: Cannot find entity %s with queries %s." % (entity_type, query_string))
            print("ERROR: Logs: [%s]" % response.text)
            return None

    def _generate_query_string(self, **query_kwargs):
        print(query_kwargs.items())
        merged_list = list(
            map(lambda key_value: "%s[%s]" % (key_value[0].replace("_", "-"), key_value[1]), query_kwargs.items()))
        query_string = "; ".join(merged_list)
        return "{%s}" % query_string

    def _get_entity_id_from_response(self, entity_response):
        """
        Parse the entry id from the request response of the entry.  Such as: GET /entities/id  or  POST /entities
        :param entity_response: response for a entity json.
        :return: A ID of the entity
        """
        response_dict = json.loads(entity_response.text)
        entity_id = self._get_entity_id_from_entity_dict(response_dict)
        return entity_id

    def _get_entities_id_from_response(self, entities_response):
        """
        Parse the entries id from the request response of the entities. Such as: GET /entities
        :param entities_response: response for a set of entities json.
        :return: A set of IDs of the entities
        """
        response_dict = json.loads(entities_response.text)
        entities = response_dict.get("entities", [])
        entities_id = []
        for entity in entities:
            entity_id = self._get_entity_id_from_entity_dict(entity_dict=entity)
            if entity_id:
                entities_id.append(entity_id)

        if not entities_id:
            print(
                    "DEBUG: Cannot get entity id from %s. Please check whether this is a response from entities request." % entities)
        return entities_id

    def _get_entity_id_from_entity_dict(self, entity_dict):
        fields = entity_dict.get("Fields", [])
        entity_id = None
        for filed in fields:
            filed_name = filed.get("Name")
            if filed_name == "id":
                values = filed.get("values", None)
                if values:
                    entity_id = int(values[0].get("value", None))
                else:
                    print("ERROR: Cannot get values from %s" % filed)
        if entity_id is None:
            print(
                    "ERROR: Cannot get testrun id from %s. Please check whether this is a response from test run request." % entity_dict)
        else:
            print("DEBUG: Found entity %s from %s" % (entity_id, entity_dict))
        return entity_id

    def _generate_fileds(self, **field_kwargs):
        """
        Generate the json data for the QC POST request.
        :param field_kwargs: Filed and value pair
        :return: The dict of the data
        """
        fields = []
        for key, values in field_kwargs.items():
            value_list = []
            if isinstance(values, list):
                for value in values:
                    value_list.append({"value": str(value)})
            elif type(values) in [str, int, float, unicode]:
                value_list.append({"value": str(values)})
            else:
                print("ERROR: Do not support the values: %s type %s " % (values, type(values)))
            field_dict = OrderedDict()
            field_dict["Name"] = key.replace("_", "-")
            field_dict["values"] = value_list

            fields.append(field_dict)
        return {"Fields": fields}


def post_result_to_qc(qc_host, domain, project, user, password, test_set_name, test_id, result, run_name, test_host,
                      test_set_folder, **test_run_kwargs):
    """
    Post the testing result to QC (ALM)
    :param qc_host:     The QC host url
    :param domain:      QC Domain
    :param project:     QC Project
    :param user:        QC User
    :param password:    QC User's password
    :param test_set_name:    Test Set name.
    :param test_id:     Test case id, Can be found in Test Plan: e.g.: 8313
    :param result:      Test result: Passed, Failed
    :param run_name:      Test run name.
    :param test_host:       Your test machine.
    :param test_set_folder:     The default test set folder name. Will used to test set auto creation
    :param test_run_kwargs:     Other parameters: e.g.:  execution-date, ver-stamp, test-config-id, name, has-linkage, subtype-id, draft, duration
    :return: True: Post result successfully. False： Post result failed
    """
    result = result.lower()
    if result in "passed":
        result = "Passed"
    elif result in "failed":
        result = "Failed"
    elif result in "blocked":
        result = "Blocked"
    else:
        result = "N/A"

    alm = ALM_REST_LIB(host=qc_host, domain=domain, project=project)
    logined = alm.login(user_name=user, password=password)
    if logined is False:
        print("ERROR: Cannot login QC.")
        return False
    case_exist = alm.is_case_id_exist(test_id=test_id)
    if not case_exist:
        print("ERROR: Cannot found the case id %s in QC. Please check it." % test_id)
        return False

    test_set_id = alm.get_test_set_id(name=test_set_name, status="Open", only_one=True)

    if not test_set_id:
        print("INFO: Cannot found test set %s. Create a new one..." % test_set_name)
        test_set_folder_id = alm.get_test_set_folder_id(name=test_set_folder)
        if not test_set_folder_id:
            print("ERROR: Cannot found test set folder %s. Please check whether it is exist in QC. " % test_set_folder)
            return False
        test_set_id = alm.create_test_set(name=test_set_name, parent_id=test_set_folder_id)
        if not test_set_id:
            print("ERROR: Create test set %s failed" % test_set_name)
            return False
    test_instance_id = alm.get_test_instance_id(test_set_id=test_set_id, test_id=test_id)
    if not test_instance_id:
        print("INFO: Test instance is not found, create a new one...")
        test_config_id = alm.get_test_configuration_id(test_id=test_id)
        test_instance_id = alm.create_test_instance(test_id=test_id, test_set_id=test_set_id,
                                                    test_config_id=test_config_id, owner=user)
        if not test_instance_id:
            print("ERROR: Create test instance failed.")
            return False
    print("INFO: Create test run...")
    test_run_id = alm.create_test_run(name=run_name, test_set_id=test_set_id, test_id=test_id,
                                      test_instance_id=test_instance_id,
                                      owner=user)
    if test_run_id:
        updated = alm.update_test_run(test_run_id=test_run_id, result=result, host=test_host, **test_run_kwargs)
        return updated
    else:
        print("ERROR: Post Result failed for %s" % test_id)
        return False


def get_qc_id(tags, tag_name='qcid'):
    for tag in tags:
        if tag.startswith("%s=" % tag_name):
            return tag.replace("%s=" % tag_name, "")
    return None


if __name__ == "__main__":
    fire.Fire(post_result_to_qc)

