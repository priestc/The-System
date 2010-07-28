import os

from celery.decorators import task
from storage.models import GenericStorage
from storage.utils import copy_s3

def upload(album, filepath, storages):
    """
    Find the first storage than can accept the file, and send it there.Each
    storage object is guaranteed to not already have the file since it is a
    generator object created outside of this function.
    """
    
    for storage in storages:
        if storage.can_handle(storage=album.size):
            storage = storage.get_real_storage()
            # if this storage doesn't already have this album,
            # and it can handle the bandwidth, then sent it there!
            storage.upload(filepath)
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
            storage = storage.get_real_storage()
            # if this storage doesn't already have this album,
            # and it can handle the bandwidth, then sent it there!
            copy_s3(orig, storage, album)
            return storage
            
@task
def upload_to_remote_storage(album, filepath):
    """
    Do the actual upload to S3 as well as the mirroring. This is a task
    that is ran asynchronously through celery.
    """
    
    # a generator so all iterations occur without resetting anything
    storages = GenericStorage.objects\
                             .exclude(albums__filename=album.filename)\
                             .order_by('?').iterator()
    
    # find a storage and then send it there, return the storage where we put it 
    st1 = upload(album, filepath, storages)
    
    # find another storage, and copy it from the first location
    st2 = mirror(album, storages, st1)
    
    # mirror again, this time copy it from the second location
    mirror(album, storages, st2)
    
    return


