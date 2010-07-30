from django.conf.urls.defaults import *

urlpatterns = patterns('storage.views',
    url(r'add_s3/', 'new_s3', name="new_s3"),
    url(r'list_storage/', 'list_storage', name='list_storage'),
    (r'set_bandwidth/', 'set_bandwidth'),
)
