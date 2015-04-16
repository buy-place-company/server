from django.conf.urls import patterns, include, url

urlpatterns = patterns('subsystems.api.views',
    url(r'^objects_near', 'objects_near'),
    url(r'^user_objects', 'user_objects'),
    url(r'^object', 'object_action'),
    url(r'^rating', 'rating')
)
