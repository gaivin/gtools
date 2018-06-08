import json
from datetime import datetime, date
from functools import partial

json_loads = json.loads


class CJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime("%Y-%m-%d")
        else:
            return json.JSONEncoder.default(self, obj)


obj_dumps = partial(json.dumps, cls=CJsonEncoder)
