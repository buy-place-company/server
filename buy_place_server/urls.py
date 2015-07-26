from django.conf.urls import patterns, include, url
import subsystems

urlpatterns = patterns('',
    url(r'^', include(subsystems.api.urls)),
    url(r'', include('subsystems.gcm.urls')),
)
