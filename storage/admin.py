from django.contrib import admin
from models import *

class S3BucketAdmin(admin.ModelAdmin):
    list_display = ('name', 'max_bandwidth',
                    'current_bandwidth', 'current_storage',
                    'max_storage', 'internal_name')
    readonly_fields = ('internal_name', 'user_id')

admin.site.register(S3Bucket, S3BucketAdmin)
