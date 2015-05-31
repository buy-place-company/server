import json
from django.http import HttpResponse


class JSONResponse:
    def serialize(self, o, **kwargs):
        is_public = kwargs.pop('public', True)
        if isinstance(o, list):
            a = ""
            for obj in o:
                a += json.dumps(obj.serialize(is_public).update(kwargs), ensure_ascii=False)
        else:
            a = json.dumps(o.serialize(is_public).update(kwargs), ensure_ascii=False)
        return HttpResponse(a)