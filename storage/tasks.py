import os
import shutil

from celery.decorators import task
from django.conf import settings

from storage.models import GenericStorage
from album.models import Album
from storage.utils import copy_s3

def upload(album, filepath, storages):
    """
    Find the first storage than can accept the file, and send it there.Each
    storage object is guaranteed to not already have the file since it is a
    generator object created outside of this function. Returns a real storage
    object
    """
    
    for storage in storages:
        if storage.can_handle(storage=album.size):
            # if this storage doesn't already have this album,
            # and it can handle the bandwidth, then sent it there!
            storage = storage.get_real_storage()
            storage.upload(filepath, str(album))
            album.storages.add(storage)
            album.save()
            return storage
        
def mirror(album, storages, orig):
    """
    find the first storage than can accept the file, and mirror
    it there from the original storage. Each storage object is guaranteed to
    not already have the file since it is a generator object created outside
    of this function.
    """
    
    for storage in storages:
        if storage.can_handle(storage=album.size):
            # if this storage doesn't already have this album,
            # and it can handle the bandwidth, then sent it there!
            storage = storage.get_real_storage()
            copy_s3(orig, storage, album)
            return storage

#############
#############
          
@task
def upload_to_remote_storage(album_pk, filepath):
    """
    Do the actual upload to S3 as well as the mirroring. This is a task
    that is ran asynchronously through celery.
    """
    
    album = Album.objects.get(pk=album_pk)
    
    # a generator so all iterations occur without resetting anything
    storages = GenericStorage.objects\
                             .exclude(albums__filename=album.filename)\
                             .order_by('?').iterator()
    
    # find a storage and then send it there, return the storage where we put it 
    st1 = upload(album, filepath, storages)
    
#    # find another storage, and copy it from the first location
#    st2 = mirror(album, storages, st1)
#    
#    # mirror again, this time copy it from the second location
#    mirror(album, storages, st2)
    
    shutil.move(filepath, settings.DELETE_PATH)
    
    return
