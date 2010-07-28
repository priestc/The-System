from django.contrib import admin
from models import *

class AlbumAdmin(admin.ModelAdmin):
    list_display = ('artist', 'album', 'meta', 'size_mb', 'mirrors')
    readonly_fields = ('filename',)

admin.site.register(Album, AlbumAdmin)
