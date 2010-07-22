import boto
from boto.s3.key import Key

from django.db import models
from main.utils import make_filename

class Album(models.Model):
    
    artist = models.CharField(max_length=96)
    album = models.CharField(max_length=96)
    album_extra = models.CharField(max_length=32, blank=True)
    
    size = models.FloatField(blank=False)
    
    storages = models.ManyToManyField("s3_storage.Bucket", related_name='albums')
    filename = models.CharField(max_length=40, unique=True, editable=False)
    
    def __unicode__(self):
        ret = "{0} - {1}".format(self.artist, self.album)
        
        if self.album_extra:
            ret += " [{0}]".format(self.album_extra)
            
        return ret
    
    def save(self, *a, **k):
        """
        Overridden to fill in the filename if its not already set
        """
        
        if not self.filename:
            self.filename = make_filename(self.artist, self.album)
        
        return super(Album, self).save(*a, **k)
    
    def get_a_bucket(self):
        """
        Returns a Bucket object where this album is stored. Only returns
        buckets that are not expired or about to be expired.
        """
    
        for storage in self.storages.order_by("?"):
            if storage.can_handle(bandwidth=self.size):
                return storage
    
    def get_key_object(self):
        
        bucket = self.get_a_bucket()
        k = boto.s3.key.Key(bucket)
        k.key = self.filename + ".zip"
        
        return k
        
    def get_absolute_url(self):
        key = self.get_key_object()
        return key.generate_url()
