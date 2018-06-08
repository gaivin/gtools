#!/usr/bin/env python
# encoding: utf-8

"""
@version: v1.0
@author: Gaivin Wang
@license: Apache Licence
@contact: gaivin@outlook.com
@site: https://github.com/gaivin/
@software: PyCharm
@file: http_utils.py
@time: 6/8/2018 3:43 PM
"""
import re
import sys
from string import upper, Template
import json
import requests
from logger_utils import get_logger
from django.http import HttpResponse
from functools import partial

HttpResponseJsonContext = partial(HttpResponse, content_type="application/json")

HTTP_DEFAULT_TIMEOUT = 60

logger = get_logger("Http_lib")

reload(sys)
sys.setdefaultencoding('utf-8')


class HttpHelper:
    '''
    classdocs
    '''

    def __init__(self, url, request_type, params_data_dic={}, headers_dic={}, auth=(), cookies_dic={},
                 timeout=HTTP_DEFAULT_TIMEOUT, **kwargs):
        self.url = url
        self.request_type = request_type
        self.params_data = params_data_dic
        self.headers = headers_dic
        self.auth = auth
        self.cookies = cookies_dic
        self.timeout = timeout
        self.regex_url = re.compile(
            "^(?:(?P<scheme>https?|ftps?):\/\/)?(?:(?:(?P<username>[\w\.\-\+%!$&'\(\)*\+,;=]+):*(?P<password>[\w\.\-\+%!$&'\(\)*\+,;=]+))@)?(?P<host>[a-z0-9-]+(?:\.[a-z0-9-]+)*(?:\.[a-z\.]{2,6})+)(?:\:(?P<port>[0-9]+))?(?P<path>\/(?:[\w_ \/\-\.~%!\$&\'\(\)\*\+,;=:@]+)?)?(?:\?(?P<query>[\w_ \-\.~%!\$&\'\(\)\*\+,;=:@\/]*))?(?:(?P<fragment>#[\w_ \-\.~%!\$&\'\(\)\*\+,;=:@\/]*))?$",
            re.IGNORECASE)

    def _parse_url(self, url):
        match_reg = re.match(self.regex_url, url)
        if match_reg is None:
            return False
        return match_reg.groupdict()

    def set_headers(self, **kwargs):
        for key, value in kwargs.items():
            self.headers[key] = value

    def set_cookies(self, **kwargs):
        for key, value in kwargs.items():
            self.cookies[key] = value

    def set_params_data(self, **kwargs):
        for key, value in kwargs.items():
            self.params_data[key] = value

    def set_auth(self, user_name, password):
        self.auth = (user_name, password)

    def send_request(self, **kwargs):
        logger.debug("%s-%s-%s" % (self.url, self.request_type, self.params_data))
        session = requests.Session()
        timeout = kwargs.get('timeout', None)
        if self.auth != ():
            session.auth = self.auth
        try:
            if upper(self.request_type) == 'GET':
                response = session.get(self.url, params=self.params_data, headers=self.headers, cookies=self.cookies,
                                       timeout=timeout)

            elif upper(self.request_type) == 'POST':
                response = session.post(self.url, data=json.dumps(self.params_data), headers=self.headers,
                                        cookies=self.cookies,
                                        timeout=timeout)

            elif upper(self.request_type) == 'PUT':
                print(self.params_data)
                response = session.put(self.url,
                                       data=json.dumps(self.params_data),
                                       headers=self.headers,
                                       cookies=self.cookies,
                                       timeout=timeout)
            else:
                logger.error('Please provide the right type: GET or POST or PUT!')
                return None
        except requests.exceptions.RequestException as ex:
            logger.error('Exception:%s' % ex.message)
            return None
        response.encoding = 'UTF-8'
        return response


def phase_api_config(api_name, api_info):
    logger.info("Get api [%s] url info..." % (api_name))
    host = api_info.get("host", None)
    if host is None:
        logger.error("Host is not been specified in %s" % api_info)
        return None, None
    port = api_info.get("port", "")
    protocol = api_info.get("protocol", "http")
    apis = api_info.get("apis", None)
    if apis is None:
        logger.error("No API is defined in %s" % api_info)
        return None, None
    api = apis.get(api_name, None)
    if api is None:
        logger.error("API [%s] is not defined in %s" % (api_name, api_info))
        return None, None
    method = api.get("method", "get")
    url = api.get("url", None)
    formatted_url = format_url(protocol, host, port, url)
    logger.info("API info getted: method: %s, url: %s" % (method, formatted_url))
    return formatted_url, method


def format_url(protocol, host, port, url):
    if url.startswith("/"):
        url = url.replace("/", "", 1)
    if port:
        port_str = ":%s" % port
    else:
        port_str = ""
    return "%s://%s%s/%s" % (protocol, host, port_str, url)


def rest_request(url, method, parameter_data_dic={}, result_type="DJANGO_REST_FRAMEWORK", only_one=True, **kwargs):
    http_helper = HttpHelper(url=url, request_type=method, params_data_dic=parameter_data_dic, **kwargs)
    response = http_helper.send_request()
    if response:
        logger.debug(response.text)
        if response.status_code == 200:
            response_obj = json.loads(response.text)
            if "DJANGO_REST_FRAMEWORK" in upper(
                    str(result_type)):  # Check whether the request is Django framework request.
                result = response_obj.get("results", None)
                if result:  # Check whether result is existing in the response
                    if only_one:  # Check if user only need one result
                        return result[0]
                    else:
                        return result
                else:
                    logger.error("No result found in the request: %s" % (response_obj))
                    return None

            else:
                return response_obj
        else:
            logger.error("Status: %s %s" % (response.status_code, response.text))
            return None
    else:
        logger.error("Response Error.")
        return None


def send_rest_request(api_name, api_info, result_type=None, parameter_data_dic={}, url_replacement={}, **kwargs):
    api_url, api_method = phase_api_config(api_name=api_name, api_info=api_info)
    if api_url:
        if url_replacement:
            t = Template(api_url)
            api_url = t.safe_substitute(**url_replacement)
        result = rest_request(url=api_url, method=api_method, result_type=result_type,
                              parameter_data_dic=parameter_data_dic, **kwargs)
        return result
    else:
        logger.error("API info phase failed. Please check the configuration [%s]" % api_info)
        return None


def validate_request(request, methods=None, keys=None):
    if methods is None:
        methods = ["POST"]
    if keys is None:
        keys = []
    if request.method in methods:

        if request.method in ["POST", "PUT", "DELETE"]:
            try:
                request_dict = json.loads(request.body)
            except Exception as e:
                response = {"status": "REQUEST_DATA_FORMAT_ERROR",
                            "comments": "The request body is not correct. Refer to %s" % e.message}
                return response
        else:
            request_dict = request.GET.dict()
        missed_key = []
        for key in keys:
            if key not in request_dict:
                missed_key.append(key)
        if missed_key:
            response = {"status": "REQUEST_DATA_ERROR",
                        "comments": "The request data/parameters is not correct. %s are missing." % missed_key}
            return response
        else:
            return True
    else:
        return {"status": "REQUEST_METHOD_ERROR",
                "comments": "Please use %s methods for this api" % methods}


# ===================================================================================
from config.api_config import RESOURCE_MANAGER_API_INFO


def test_rest_request():
    result = send_rest_request(api_name="getpool", api_info=RESOURCE_MANAGER_API_INFO,
                               result_type="DJANGO_REST_FRAMEWORK", parameter_data_dic={"type": "VM"})
    print(result)


def test_rest_put_pool_request():
    result = send_rest_request(api_name="updatepool", api_info=RESOURCE_MANAGER_API_INFO,
                               result_type=None, parameter_data_dic={"id": '3', "status": "still busy"})
    print(result)


def test_request():
    hh = HttpHelper(url='http://127.0.0.1:8000/resource/getpool', request_type="get", params_data_dic={"type": "AV"})
    response = hh.send_request()
    print(response.text)


if __name__ == "__main__":
    test_rest_request()
    test_rest_put_pool_request()
