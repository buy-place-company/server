import json
from django.http import HttpResponse
from subsystems.db.model_venue import Venue
from subsystems.db.model_zone import Zone

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

    list_id = Zone.objects.filter(sw_lat__gt=lat).filter(ne_lat__lt=lat)\
                          .filter(sw_lng__gt=lng).filter(ne_lng__lt=lng).get('list_id', None)

    objects = Venue.objects.filter(list_id=list_id).values()[:50]

    return HttpResponse(json.dumps({'status': 200, 'objects': objects}, ensure_ascii=False))