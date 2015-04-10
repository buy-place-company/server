from django.conf.urls import url
from . import views

urlpatterns = (
    url(r"signup$", views.test_signup),
    url(r"signin$", views.test_signin),
    url(r"is_auth$", views.test_is_auth),
)