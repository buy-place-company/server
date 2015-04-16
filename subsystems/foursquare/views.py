import json
from django.http import HttpResponse
from subsystems.db.model_venue import Venue

LONG = 10.1
ERRORS = {
    '1': json.dumps({'status': 401, 'message': 'unauthorized access'}),
    '2': json.dumps({'status': 101, 'message': 'not enough args: lat and lng'})
}


def objects_near(request):
    if not request.GET.get("access_token"):
        return HttpResponse(ERRORS['1'])
    lat = request.GET.get("lat", None)
    lng = request.GET.get("lng", None)

    if lat and lng:
        return HttpResponse(json.dumps(ERRORS['2']))

    list = [Venue.objects.filter(lat__gt=lat - LONG).filter(lat__lt=lat + LONG).filter(lat__gt=lng - LONG)
                         .filter(lat__lt=lng + LONG).values()[:50]]

    return HttpResponse(json.dumps({'status': 200, 'objects': list}, ensure_ascii=False))