import json
from django.http import HttpResponse


class JSONResponse:
    @staticmethod
    def serialize(o, **kwargs):
        is_public = kwargs.pop('public', True)
        aas = kwargs.pop('as', 'data')
        if isinstance(o, dict):
            d = o.copy()
            d.update(kwargs)
            return HttpResponse(json.dumps(d, ensure_ascii=False))
        if isinstance(o, list):
            lst = []
            for obj in o:
                d = {aas: obj.serialize(is_public)}
                d.update(kwargs)
                lst.append(json.dumps(d, ensure_ascii=False))
            a = "[" + ",".join(lst) + "]"
        else:
            a = json.dumps(o.serialize(is_public).update(kwargs), ensure_ascii=False)
        return HttpResponse(a)