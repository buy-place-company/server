from django.conf.urls import patterns, include, url

urlpatterns = patterns('subsystems.api.views',
    url(r'objects$', 'objects'),
    url(r'user_objects$', 'user_objects'),
    url(r'object$', 'object_action'),
    url(r'rating$', 'rating'),
    url(r'auth/vk$', 'auth_vk'),
    url(r'objects$', 'point_obj')
)
