from django.conf.urls import patterns, include, url
from dev_center import views
from rest_framework import routers
from django.contrib import admin

admin.autodiscover()

router = routers.DefaultRouter()
router.register(r'devs', views.DevViewSet)

urlpatterns = patterns('',
	url(r'^devs/', include('dev_center.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include(router.urls)),
    # url(r'^api/', include('rest_framework.urls', namespace='rest_framework')),

)

# if settings.DEBUG:
#         urlpatterns += patterns(
#                 'django.views.static',
#                 (r'media/(?P<path>.*)',
#                 'serve',
#                 {'document_root': settings.MEDIA_ROOT}), )
