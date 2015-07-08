from django.conf.urls import patterns, include, url

urlpatterns = patterns('subsystems.api.views',
    url(r'objects$', 'objects'),
    url(r'object$', 'obj'),
    url(r'object_action$', 'object_action'),
    url(r'user_objects$', 'user_objects'),
    url(r'rating$', 'rating'),
    url(r'auth/vk$', 'auth_vk'),
    url(r'profile$', 'profile'),
    url(r'test', 'test')
)
