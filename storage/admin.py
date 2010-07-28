from django.contrib import admin
from models import *

class S3BucketAdmin(admin.ModelAdmin):
    list_display = ('name',
                    'allowed_bandwidth',
                    'allowed_storage',
                    'count_albums',
                    'current_bandwidth',
                    'current_storage',
                    'internal_name')
                    
    readonly_fields = ('internal_name', 'user_id')

    def count_albums(self, obj):
        return obj.albums.count()
    count_albums.short_description = '# of Albums'
    
    def allowed_bandwidth(self, obj):
        if obj.max_bandwidth == 0:
            return "Unlimited"
        return obj.max_bandwidth
    allowed_bandwidth.short_description = 'Max Bandwidth'
    allowed_bandwidth.admin_order_field = 'max_bandwidth'

    def allowed_storage(self, obj):
        if obj.max_storage == 0:
            return "Unlimited"
        return obj.max_storage
    allowed_storage.short_description = 'Max Storage'
    allowed_storage.admin_order_field = 'max_storage'

admin.site.register(S3Bucket, S3BucketAdmin)
