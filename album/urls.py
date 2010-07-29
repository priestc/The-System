from django.conf.urls.defaults import *

urlpatterns = patterns('album.views',
    url(r'list/', 'view_albums', name="view_albums"),
    url(r'download-(?P<pk>\d+)', 'download_album', name='download_album'),
)
