from django.conf.urls.defaults import *
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^the/', include('the.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    
    url(r'^$', 'main.views.home', name='root'),
        
    (r'^admin/', include(admin.site.urls)),
    (r'^storage/', include('storage.urls')),
    (r'^upload$', 'storage.views.handle_upload'),
)
