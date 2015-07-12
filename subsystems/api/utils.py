import json
from django.db.models import QuerySet
from django.http import HttpResponse


class JSONResponse:
    @staticmethod
    def serialize(o, **kwargs):
        is_public = kwargs.pop('public', True)
        aas = kwargs.pop('aas', 'data')
        if isinstance(o, dict):
            d = o.copy()
            d = {aas: d}
            d.update(kwargs)
            return HttpResponse(json.dumps(d, ensure_ascii=False))
        if isinstance(o, list) or isinstance(o, QuerySet):
            d = {aas: []}
            for obj in o:
                d[aas].append(obj.serialize(is_public))
                d.update(kwargs)
            a = json.dumps(d, ensure_ascii=False)
        else:
            d = o.serialize(is_public)
            d = {aas: d}
            d.update(kwargs)
            a = json.dumps(d, ensure_ascii=False)
        return HttpResponse(a)
