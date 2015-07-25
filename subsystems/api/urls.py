from django.conf.urls import patterns, url
import subsystems.api.receivers

urlpatterns = patterns('subsystems.api.views',
    # TODO: выпилить это, ниже куда структурированней и понятней
    # TODO: разнести в отдельные приложения, а не держать в одном
    url(r'^objects$', 'zone_venues'),
    url(r'^object$', 'venue_info'),
    url(r'^object_action$', 'venue_action'),
    url(r'^user_objects$', 'user_venues'),
    url(r'^rating$', 'user_rating'),
    url(r'^auth/vk$', 'auth_vk'),
    url(r'^profile$', 'user_profile'),
    url(r'^test$', 'test'),

    # V2
    url(r'^zone/venues$', 'zone_venues'),

    url(r'^venues/by_user$', 'user_venues'),

    url(r'^venue/info$', 'venue_info'),
    url(r'^venue/action$', 'venue_action'),

    url(r'^user/profile$', 'user_profile'),
    url(r'^user/venues$', 'user_venues'),
    url(r'^user/deals$', 'user_deals'),
    url(r'^user/rating$', 'user_rating'),

    url(r'^auth/signup$', 'auth_signup'),
    url(r'^auth/vk$', 'auth_vk'),
    url(r'^auth/email$', 'auth_email'),
    url(r'^auth/logout$', 'auth_logout'),

    url(r'^deals/new$', 'deal_new'),
    url(r'^deals/cancel$', 'deal_cancel'),
    url(r'^deals/accept$', 'deal_accept'),
    url(r'^deals/info$', 'deal_info'),

    url(r'^push/reg$', 'push_reg'),
)
