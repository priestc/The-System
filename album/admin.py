from django.contrib import admin
from models import *

class AlbumAdmin(admin.ModelAdmin):
    list_display = ('artist', 'album', 'meta')
#    search_fields = ('user__username', 'remarks', 'id')
#    raw_id_fields = ('plane', 'route')
    #filter_horizontal = ('user', )

admin.site.register(Album, AlbumAdmin)
