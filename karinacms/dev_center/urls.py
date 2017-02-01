from django.conf.urls import patterns, include, url

from django.contrib import admin
from dev_center import views
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'dev_center.views.index', name='index'),
    # url(r'^about/', 'dev_center.views.about', name='about'),
    url(r'^add_dev/(?P<campaign_name>.+)?', 'dev_center.views.dev_form', name='add_dev'),
    url(r'^edit_dev/(?P<dev_id>\d+)/$', 'dev_center.views.dev_edit_form', name='edit_dev'),
    url(r'^dev_page/(?P<dev_name>.+)?', 'dev_center.views.dev_page', name='dev_page'),
    url(r'^products/', 'dev_center.views.product_list', name='product_list'),
    url(r'^campaigns/', 'dev_center.views.campaign_list', name='campaign_list'),
    url(r'^statuses/', 'dev_center.views.status_list', name='status_list'),
    url(r'^hours/', 'dev_center.views.hours_list', name='hours_list'),
    # url(r'^blog/', includedev_center('blog.urls')),
    url(r'^register/', 'dev_center.views.register', name='register'),#TODO: remove those paths to the root urls.py
    url(r'^login/', 'dev_center.views.user_login', name='login'),
    url(r'^logout/', 'dev_center.views.user_logout', name='logout'),
    url(r'^search_list/$', 'dev_center.views.search_list', name='search_list'),
    url(r'^edit/(?P<obj_type>.+)/(?P<obj_id>\d+)$', 'dev_center.views.edit_obj', name='edit_obj'),   #url(r'^admin/', include(admin.site.urls)),
    url(r'^delete/(?P<obj_type>.+)/(?P<obj_id>\d+)$', 'dev_center.views.delete_obj', name='delete_obj'),
)