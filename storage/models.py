import re
import boto

from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import models

chars_validator = RegexValidator(r'^[\w\d]+$', message="Invalid Characters")

class GenericStorage(models.Model):
    name = models.CharField(max_length=32, validators=[chars_validator])
    internal_name = models.CharField(max_length=64, editable=False, blank=True)
    max_size = models.FloatField(help_text="In Gigabytes (0=unlimited)", default=0)
    max_bandwidth = models.FloatField(help_text="In Gigabytes per month (0=unlimited)", default=0)
    current_bandwidth = models.FloatField(default=0, editable=False)
    
    def __unicode__(self):
        
        ret = "{0} ({1} GB".format(self.name, str(self.current_size))
        
        if self.max_size > 0:
            ret += " / {0} GB)".format(str(self.max_size))
        else:
            ret += ")"
    
        return ret
    
    def clean(self):
        if not self.test():
            raise ValidationError('Keys are not correct')
    
    def save(self, *args, **kwargs):
        super(GenericStorage, self).save(*args, **kwargs)
        
        if not self.internal_name:
            self.set_up()
       
    @property
    def unlimited_bandwidth(self):
        return self.max_bandwidth == 0
    
    @property
    def unlimited_size(self):
        return self.max_size == 0

    def can_handle(self, bandwidth=None, size=None):
        """
        Does this bucket have enough bandwidth to handle the download?
        Does this bucket have enough storage space to handle the upload?
        """
        
        if size and not self.unlimited_size:
            return self.size_left > size
        
        if bandwidth and not self.unlimited_bandwidth:
            return self.bandwidth_left > bandwidth
    
        # either unlimited bandwidth or unlimited storage space, can
        # always handle everything no matter what
        return True 
    
    @property
    def bandwidth_left(self):
        """
        Return how much bandwidth this bucket has left in GB
        if this node is unlimited, return a really big number
        """
        
        if self.unlimited_bandwidth:
            return 99999999
          
        left = self.max_bandwidth - self.current_bandwidth
        
        if left < 0:
            return 0
        
        return left
    
    @property
    def size_left(self):
        """
        Return how much space this storage node has left in GB
        if this node is unlimited, return a really big number
        """
        
        if self.unlimited_size:
            return 99999999
            
        left = self.max_size - self.current_size
        
        if left < 0:
            return 0
        
        return left
    
    @property
    def current_size(self):
        """
        Returns the total size of all albums stored in this bucket in Gigabytes
        """
        
        if not self.pk:
            # self.albums is not availiable until a pk is set
            # (when the model has been saved)
            return "--"
        
        val = 0
        for album in self.albums.all():
            val += album.size
            
        return val

class S3Bucket(GenericStorage):
    access_key = models.CharField(max_length=20, unique=True)
    secret_key = models.CharField(max_length=40)
    
    def test(self):
        """
        Test to see if the credentials are correct
        """
        
        try:
            conn = self.get_connection()
            conn.get_all_buckets()

        except:
            return False
            
        else:
            return True
    
    def set_up(self, prefix_index=0):
        """
        Set up the bucket on S3 if it isn't already. Called once when the
        S3 account is added. If the bucket name is not available, then append
        a letter to it until a valid one is found
        """
        
        chars = '_abcdefghijklmnopqrstuvwxyz'
        conn = self.get_connection()
        prefix = ""
        
        if prefix_index > 0:
            # (index==0 means use no prefix)
            prefix = chars[prefix_index]
            
        bucket_name = '{0}_{1}{2}'.format(settings.STORAGE_PREFIX, self.pk, prefix)
        
        try:
            conn.create_bucket(bucket_name)
        except boto.exception.S3CreateError:
            self.set_up(prefix_index + 1) # recursion
        else:
            self.internal_name = bucket_name
            self.save()
    
    def get_connection(self):
        """
        Create the connection to the bucket
        """        
        
        return boto.connect_s3(str(self.access_key), str(self.secret_key))


###################
## signals below ##
###################

#def set_up_bucket(sender, **kwargs):
#    print "setup storage"

#    bucket = kwargs['instance']
#    bucket.set_up()
#    
#models.signals.post_save.connect(set_up_bucket, sender=GenericStorage)







