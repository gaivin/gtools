import commands, re, time, copy, datetime
from django.utils.dateformat import DateFormat
from logger_utils import get_logger

logger = get_logger("utils")


def execute_cmd(cmd, show_log=False):
    logger.info("Execute: [%s]" % cmd)
    (status, output) = commands.getstatusoutput(cmd)
    if status != 0:
        logger.info("[%s] execute failed! Exit code: [%s]. Please refer to: \n %s" % (cmd, status, output))
    else:
        if show_log:
            print"%s\n%s\n%s" % (
                (cmd + "====log=start").center(160, "="), output, (cmd + "====log=end").center(160, "="))
        logger.info("Execute: [%s] successful." % cmd)
    return status, output


def get_current_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))


def get_current_time_string():
    return time.strftime("%Y%m%d%H%M%S", time.localtime(time.time()))


def get_current_date():
    return time.strftime("%d %B, %Y", time.localtime(time.time()))


def get_year():
    return time.localtime()[0]


def get_max_from_list(orignal_list, pattern, compare_type=int):
    max_match_value = None
    max_item = ""
    for item in orignal_list:
        match_result = re.findall(pattern, item)
        logger.debug(match_result)
        if match_result:
            tem_value = compare_type(match_result[0])
            if max_match_value and max_match_value > tem_value:
                pass
            else:
                max_match_value = tem_value
                max_item = item
    logger.info("%s is the largest item." % max_item)
    return max_item, max_match_value


DEFAULT_VALUE = "DEFAULT_VALUE2_GET_PARAMETER@REQUEST"


def filter_objects_from_request(model, serializer, request):
    queryset = model.objects.all()
    filter_kwargs = {}
    for arg in serializer.Meta.fields:
        arg_value = request.query_params.get(arg, DEFAULT_VALUE)
        if arg_value != DEFAULT_VALUE:
            filter_kwargs[arg] = arg_value
    if filter_kwargs:
        queryset = queryset.filter(**filter_kwargs)
    return queryset


def transport_parameters(parameter_mapping, **parameters):
    '''
    This function is used to transport the parameter keys.
    :param parameter_mapping: The parameter key mapping
    :param parameters: The original parameters key value.
    :return: The formatted parameters
    '''
    formatted_parameters = copy.deepcopy(parameters)
    for key in parameters:
        if key in parameter_mapping:
            formatted_parameters[parameter_mapping[key]] = formatted_parameters.pop(key)
        else:
            logger.debug("%s is not in mapping %s" % (key, parameter_mapping))
    return formatted_parameters


def update_parameters(parameters_temp_dict, expand=False, **kwargs):
    '''
    :param parameters_temp_dict: The parameter template
    :param expand: Whether expand the parameters_temp_dict if parameter is not exist
    :param kwargs: The parameter which you want to update from template
    :return: The updated parameters
    '''
    if expand is True:
        parameters_temp_dict.update(kwargs)
    else:
        for key in kwargs:
            if key in parameters_temp_dict:
                parameters_temp_dict[key] = kwargs[key]
                logger.debug("Update '%s' to '%s' in %s" % (key, kwargs[key], parameters_temp_dict))
            else:
                logger.debug("DEBUG: %s is not in %s" % (key, parameters_temp_dict.keys()))
    return parameters_temp_dict


if __name__ == "__main__":
    # print get_max_from_list(["dpnmcs-7.4.0-0001.sles11_64.x86_64.rpm", "dpnmcs-7.4.0-200.sles11_64.x86_64.rpm",
    #                          "dpnmcs-7.4.0-10.sles11_64.x86_64.rpm", "dpnmcs-7.4.0-100.sles11_64.x86_64.rpm"],
    #                         "dpnmcs-7.4.0-(\d+).sles11_64.x86_64.rpm", int)
    print get_current_date()
