import json
import re

def obj2dict(obj):
    """
    Transform the object to a dict object, which will be used to dump to json file.
    :param obj:  The object you want to dump
    :return:
    """
    base_class = (str, int, bool, float, unicode, type(None))
    iterable_class = (list, tuple, set)
    if isinstance(obj, base_class):  # Return base value
        return obj
    elif isinstance(obj, dict):
        obj_dict = obj
    elif isinstance(obj, iterable_class):  # Object to list
        obj_list = []
        for item in obj:
            obj_list.append(transform(item))
        return obj_list
    else:  # Object to dict
        obj_dict = obj.__dict__
    for filed, value in obj_dict.items():
        if isinstance(value, base_class):
            pass
        elif isinstance(value, iterable_class):
            obj_dict[filed] = []
            for item in value:
                obj_dict[filed].append(transform(item))
        else:
            obj_dict[filed] = transform(value)
    return obj_dict


def dict2json(obj_dict, json_file=None, replacement_map=None):
    json_string = json.dumps(obj_dict, indent=2)
    # replace the text in json string if need
    if replacement_map is not None:
        for original_string, replacement in replacement_map.items():
            json_string = re.sub(string=json_string, pattern=original_string, repl=replacement)
    if json_file is None:
        return json_string
    else:
        with open(json_file, "w") as json_file_handler:
            json_file_handler.write(json_string)
        return json_file
  
  
  
def xml2obj(node):
    """
    convert xml to python object
    node: xml.etree.ElementTree object
    """
    name = node.tag
    obj_type = type(name, (object,), {})
    obj = obj_type()
    if node.attrib:
        for key, value in node.attrib.items():
            setattr(obj, "--%s" % key, value)
    text = node.text.replace(" ", "").replace("\n", "")
    for sub_node in node:
        sub_obj = xml2obj(sub_node)
        if not hasattr(obj, sub_node.tag):  # if no attr, set the attr
            setattr(obj, sub_node.tag, sub_obj)
        else:  # if the attr exist. it means more than one sub node with same name exist. need to store as a list.
            value = getattr(obj, sub_node.tag)
            if isinstance(value, list):  # add sub node to the list
                value.append(sub_obj)
            else:  # transfer sub node to list
                setattr(obj, sub_node.tag, [value])
    if text:
        if obj.__dict__:  # if a node has both sub node and text. set the text as text field.
            setattr(obj, 'text', text)
        else:  # if a node has only text. set the text as the value.
            obj = text
    return obj
  
  
  def get_field(obj, attr_str):
    list_pattern = r"\[(.*)\]"
    kw_pattern = r"(.*)=(.*)"
    attrs = attr_str.split(".")
    for attr in attrs:
        match_result = re.findall(list_pattern, attr)
        attr = re.sub(list_pattern, "", attr)
        if isinstance(obj, dict):
            obj = obj.get(attr)
        else:
            obj = getattr(obj, attr, None)
        if obj is None:
            return None
        if match_result:
            matched_value = match_result[0]
            if matched_value.isnumeric():
                list_index = int(matched_value)
                obj = obj[list_index]
            else:
                kw_matched_result = re.findall(kw_pattern, matched_value)
                if kw_matched_result:
                    key = kw_matched_result[0][0]
                    value = kw_matched_result[0][1]
                    founded = False
                    for item in obj:
                        if item.get(key, None) == value:
                            obj = item
                            founded = True
                            break
                        else:
                            continue
                    if not founded:
                        print("ERROR: %s:%s is not found in %s" % (key, value, obj))
                        return None
                else:
                    print("ERROR: %s is not key=value format. " % matched_value)
                    return None

    return obj
  
    
def transform(obj):
    """
    Transform the object to a dict object, which will be used to dump to json file.
    :param obj:  The object you want to dump
    :return:
    """
    base_class = (str, int, bool, float, unicode, type(None))
    iterable_class = (list, tuple, set)
    if isinstance(obj, base_class):  # Return base value
        return obj
    elif isinstance(obj, dict):
        obj_dict = obj
    elif isinstance(obj, iterable_class):  # Object to list
        obj_list = []
        for item in obj:
            obj_list.append(transform(item))
        return obj_list
    else:  # Object to dict
        obj_dict = obj.__dict__
    for filed, value in obj_dict.items():
        if isinstance(value, base_class):
            pass
        elif isinstance(value, iterable_class):
            obj_dict[filed] = []
            for item in value:
                obj_dict[filed].append(transform(item))
        else:
            obj_dict[filed] = transform(value)
    return obj_dict
