from django.conf.urls import patterns, include, url
from django.contrib import admin
import subsystems

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'buy_place_server.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    # url(r'^admin/', include(admin.site.urls)),

    url(r'^test/', include(subsystems.test.urls)),
    url(r'', include(subsystems.api.urls))
)
