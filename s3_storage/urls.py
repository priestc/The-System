from django.conf.urls.defaults import *

urlpatterns = patterns('s3_storage.views',
    (r'add/', 'edit_new'),
    (r'view/', 'view_collection'),
)
