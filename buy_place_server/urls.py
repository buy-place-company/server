from django.conf.urls import patterns, include, url
import subsystems

urlpatterns = patterns('',
    #url(r'^test/', include(subsystems.test.urls)),
    url(r'^', include(subsystems.api.urls)),
    url(r'', include('subsystems.gcm.urls')),
)
