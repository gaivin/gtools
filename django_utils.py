from django.http import HttpResponse
from json_utils import obj_dumps, json_loads
import inspect
from .exception import BaseException, RequestDataError, RequestDataFormatError, RequestMethodError


def validate_request(types=("POST",), view_return="object"):
    """
    Validate the parameters and request method for a view
    :param view_return: the return value type of the decorated view object, json or html
    :param types: Specified the method of the request
    """

    def wrapper(view_foo):
        view_foo_parameters_info = get_parameters(view_foo)
        mandatory_parameter = view_foo_parameters_info["mandatory_parameter"]
        if mandatory_parameter[0] == "request":
            mandatory_parameter.pop(0)
        optional_parameters = view_foo_parameters_info["optional_parameters"]

        def wrapped(request):
            try:
                request_dict = {}
                if request.method in types:
                    if request.method in ["POST", "PUT", "DELETE"]:
                        try:
                            request_dict = json_loads(request.body)
                            if isinstance(request_dict, dict) is False:
                                error_message = "The request body %s is not a dict." % request.body
                                # for key, value in request.POST.items():
                                #     request_dict.update(key=value)
                                raise RequestDataFormatError(error_message)
                        except Exception as e:
                            error_message = "The request body %s is not json format. %s" % (request.body, e.message)
                            raise RequestDataFormatError(error_message)

                    else:
                        request_dict = request.GET.dict()
                else:
                    error_message = "Your request method: %s. Expected request method: %s" % (request.method, types)
                    raise RequestMethodError(error_message)

                try:
                    result = view_foo(request, **request_dict)
                except TypeError as e:
                    error_message = "Your parameters: %s. \n" \
                                    "Expected parameters: " \
                                    "Mandatory parameters: %s, Optional Parameters: %s. Exception: %s " % (
                                        request_dict.keys(), mandatory_parameter, optional_parameters, e.message)
                    raise RequestDataError(error_message)
            except BaseException as e:
                result = {"status": e.type, "comments": e.message}
                response = HttpResponse(obj_dumps(result), content_type="application/json")
                return response

            if view_return.lower() == "object":
                response = HttpResponse(obj_dumps(result), content_type="application/json")
            elif view_return.lower() == "json":
                response = HttpResponse(result, content_type="application/json")
            else:
                response = HttpResponse(result)
            return response

        return wrapped

    return wrapper


def json_response(foo):
    """ Return the response as json, and return a 500 error code if an error exists """

    def wrapped(*args, **kwargs):
        result = foo(*args, **kwargs)
        response = HttpResponse(obj_dumps(result), content_type="application/json")
        if type(result) == dict and 'error' in result:
            response.status_code = 500
        return response

    return wrapped


def get_parameters(foo):
    foo_spec = inspect.getargspec(foo)
    if foo_spec.args:
        len_args = len(foo_spec.args)
    else:
        args_info = {"mandatory_parameter": None,
                     "optional_parameters": None}
        return args_info
    if foo_spec.defaults:
        defaults_len = len(foo_spec.defaults)
    else:
        defaults_len = 0
    args_info = {"mandatory_parameter": foo_spec.args[0:len_args - defaults_len],
                 "optional_parameters": foo_spec.args[len_args - defaults_len:len_args]}
    return args_info
