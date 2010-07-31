from django.contrib import admin
from models import *

class AlbumAdmin(admin.ModelAdmin):
    list_display = ('artist', 'album', 'meta', 'size_mb', 'mirrors')

    def mirrors(self, obj):
        return ", ".join(obj.storages.values_list('name', flat=True))

admin.site.register(Album, AlbumAdmin)
