from django.conf.urls.defaults import *

urlpatterns = patterns('storage.views',
    url(r'add_s3/', 'new_s3', name="new_s3"),
    (r'view/', 'view_collection'),
)
