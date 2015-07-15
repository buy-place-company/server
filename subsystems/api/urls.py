from django.conf.urls import patterns, url

urlpatterns = patterns('subsystems.api.views',
    # TODO: выпилить это, ниже куда структурированней и понятней
    # TODO: разнести в отдельные приложения, а не держать в одном
    url(r'objects$', 'zone_venues'),
    url(r'object$', 'venue_info'),
    url(r'object_action$', 'venue_action'),
    url(r'user_objects$', 'user_venues'),
    url(r'rating$', 'user_rating'),
    url(r'auth/vk$', 'auth_vk'),
    url(r'profile$', 'user_profile'),
    url(r'test$', 'test'),

    url(r'zone/venues$', 'zone_venues'),
    url(r'venue/info$', 'venue_info'),
    url(r'venue/action$', 'venue_action'),
    url(r'user/profile', 'user_profile'),
    url(r'user/venues$', 'user_venues'),
    url(r'user/deals', 'user_deals'),
    url(r'user/rating$', 'user_rating'),
    url(r'auth/vk', 'auth_vk'),
    url(r'auth/logout', 'auth_logout'),
    url(r'deals/new', 'deal_new'),
    url(r'deals/cancel', 'deal_cancel'),
    url(r'deals/accept', 'deal_accept'),
)
