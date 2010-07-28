import boto
from boto.s3.key import Key

from django.db import models
from main.utils import make_filename

class Album(models.Model):
    
    artist = models.CharField(max_length=96)
    album = models.CharField(max_length=96)
    meta = models.CharField(max_length=96, blank=True)
    date = models.CharField(max_length=12, blank=False)
    profile = models.CharField(max_length=20, blank=False)
    size = models.FloatField(blank=False)
    
    storages = models.ManyToManyField("storage.GenericStorage", related_name='albums', blank=True)
    filename = models.CharField(max_length=44, unique=True, editable=False)
    
    def __unicode__(self):
        ret = "{0} - ({1}) {2}".format(self.artist, self.date, self.album)
        
        if self.meta:
            ret += " [{0}]".format(self.meta)
            
        return ret
    
    def save(self, *args, **kwargs):
        """
        Overridden to fill in the filename if its not already set
        """
        
        if not self.filename:
            self.filename = make_filename(self.artist, self.album)
        
        return super(Album, self).save(*args, **kwargs)
    
    @models.permalink
    def get_absolute_url(self):
        return ('download_album', [str(self.pk)])
    
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
        k.key = self.filename
        
        return k
    
    def size_mb(self):
        """
        Return the size of this album in megabytes.
        """

        return "{0:.3f} MB".format(self.size * 1024.0)
    size_mb.admin_order_field = 'size'
