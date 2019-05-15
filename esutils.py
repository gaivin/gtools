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


class ESUtils():
    def __init__(self, hosts):
        self.es = Elasticsearch(hosts=hosts)

    def import_from_csv(self, csv_file, index_name, timestamp=None, filed_format=None, **addition_kwargs):
        if not os.path.exists(csv_file):
            print("ERROR: %s file not found" % csv_file)
            raise Exception("Cannot find the csv file %s" % csv_file)
        actions = []
        if not self.es.indices.exists(index=index_name, allow_no_indices=True):
            print("Warning: Index is not found")
            self.es.indices.create(index=index_name, body={}, ignore=400)
        if timestamp is None:
            timestamp = datetime.datetime.now()
        elif not isinstance(timestamp, datetime.datetime):
            raise Exception("timestamp should be datetime.datetime class, but %s provided." % type(timestamp))

        for item in DictReader(open(csv_file, 'rU')):
            source = item if filed_format is None else filed_format(item)
            source.update(**addition_kwargs)
            source["timestamp"] = timestamp
            actions.append({"_index": index_name, "_source": source})
        response = helpers.bulk(self.es, actions, chunk_size=100)
        print("DEBUG: Bulk result %s" % list(response))
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
                    body_dict[key] = datetime.datetime.strptime(match_result[0], "%Y-%m-%d %H:%M:%S")
                    continue
                match_result = re.findall(r"^\d\d\d\d-\d\d-\d\d$", body_dict[key])
                if match_result:
                    body_dict[key] = datetime.datetime.strptime(match_result[0], "%Y-%m-%d")
                    continue
                body_dict[key] = str(body_dict[key]).encode('utf-8')
            except ValueError as e:
                print("Warning: %s for %s" % (str(e), body_dict))
                remove_keys.append(key)
        for key in remove_keys:
            body_dict.pop(key)
        return body_dict


if __name__ == "__main__":
    esu = ESUtils(hosts="http://vm-hrgods-61-46.asl.lab.emc.com:9200")
    number = esu.import_from_csv(csv_file="bugs-2019-05-14.csv", index_name="fsa-test",
                                 timestamp=datetime.datetime(2019, 5, 12),
                                 filed_format=esu.item_format)
    print(number)
