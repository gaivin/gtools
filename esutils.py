#!/usr/bin/env python  
# encoding: utf-8  

""" 
@version: v1.0 
@author: Gaivin Wang 
@license: Apache Licence  
@contact: gaivin@outlook.com
@site:  
@software: PyCharm 
@file: esutils.py 
@time: 5/13/2019 3:59 PM 
"""

from csv import DictReader
import datetime, os
from elasticsearch import Elasticsearch
from elasticsearch import helpers
import re
import fire
from logger_utils import get_logger

logger = get_logger(logger_name="ESUtils")


class ESUtils:
    def __init__(self, hosts):
        self.es = Elasticsearch(hosts=hosts)

    def import_from_dict(self, doc_dict, index_name, **addition_kwargs):
        doc_dict.update(**addition_kwargs)
        response = self.es.index(index=index_name, body=doc_dict)
        return response

    def import_from_csv(self, csv_file, index_name, timestamp=None, filed_format=None, **addition_kwargs):
        if not os.path.exists(csv_file):
            logger.error("%s file not found" % csv_file)
            raise Exception("Cannot find the csv file %s" % csv_file)
        actions = []
        if not self.es.indices.exists(index=index_name, allow_no_indices=True):
            logger.warn("Index is not found")
            self.es.indices.create(index=index_name, body={}, ignore=400)
        if timestamp is None:
            timestamp = datetime.datetime.now()
        elif not isinstance(timestamp, datetime.datetime):
            raise Exception("timestamp should be datetime.datetime class, but %s provided." % type(timestamp))

        for item in DictReader(open(csv_file, "r")):
            source = item if filed_format is None else filed_format(item)
            source.update(**addition_kwargs)
            source["timestamp"] = timestamp
            actions.append({"_index": index_name, "_source": source})
        helpers.bulk(self.es, actions, chunk_size=100)
        self.es.indices.flush(index=[index_name])
        return len(actions)

    def item_format(self, body_dict):
        body_dict = dict(body_dict)
        remove_keys = []
        for key in body_dict:
            try:
                if not body_dict[key]:  # Remove the key if the value of it is empty
                    remove_keys.append(key)
                    continue
                match_result = re.findall(r"^\d\d\d\d-\d\d-\d\d\s\d\d:\d\d:\d\d$", body_dict[key])
                if match_result:
                    body_dict[key] = datetime.datetime.strptime(match_result[0], r"%Y-%m-%d %H:%M:%S")
                    continue
                match_result = re.findall(r"^\d\d\d\d-\d\d-\d\d$", body_dict[key])
                if match_result:
                    body_dict[key] = datetime.datetime.strptime(match_result[0], r"%Y-%m-%d")
                    continue
                match_result = re.findall(r"^\d+/\d+/\d{4}$", body_dict[key])
                if match_result:
                    body_dict[key] = datetime.datetime.strptime(match_result[0], r"%m/%d/%Y")
                    continue
                match_result = re.findall(r"^\d+$", body_dict[key])
                if match_result:
                    body_dict[key] = int(match_result[0])
                    continue
                body_dict[key] = str(body_dict[key]).encode('utf-8')
            except ValueError as e:
                logger.warn("%s for %s" % (str(e), body_dict))
                remove_keys.append(key)
        for key in remove_keys:
            body_dict.pop(key)
        return body_dict


def dict2es(host, index_name, doc_dict, **addition_kwargs):
    esu = ESUtils(hosts=host)
    addition_kwargs.update(timestamp=datetime.datetime.utcnow())
    response = esu.import_from_dict(doc_dict=doc_dict, index_name=index_name, **addition_kwargs)
    print(response)


def csv2es(host, index_name, csv_file):
    esu = ESUtils(hosts=host)
    number = esu.import_from_csv(csv_file=csv_file, index_name=index_name,
                                 timestamp=datetime.datetime.utcnow(),
                                 filed_format=esu.item_format)
    print("Imported %s items." % number)


if __name__ == "__main__":
    fire.Fire(csv2es)
