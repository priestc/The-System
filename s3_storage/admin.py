from django.contrib import admin
from models import *

class BucketAdmin(admin.ModelAdmin):
    list_display = ('name', 'max_bandwidth',
                    'current_bandwidth', 'current_size',
                    'max_size', 'internal_name')
#    search_fields = ('user__username', 'remarks', 'id')
#    raw_id_fields = ('plane', 'route')
    #filter_horizontal = ('user', )

admin.site.register(Bucket, BucketAdmin)
