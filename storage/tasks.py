import os

from celery.decorators import task
from storage.models import GenericStorage
from storage.utils import copy_s3

@task
def upload_to_remote_storage(album, filepath):
    """
    Do the actual upload to S3 as well as the mirroring
    """
    
    while True:
        #a random storage location
        st1 = GenericStorage.objects.order_by('?')[0]
    
        if st.can_handle(storage=album.size):
            st1.get_real_storage().upload(filepath)
            break
    
    #now do the mirrors
    
    while True:
        st2 = GenericStorage.objects.exclude(albums__filename=album.filename)\
                                    .order_by('?')[0]
    
        if st2.can_handle(storage=album.size):
            copy_s3(st1, st2, album.filename)
            break
        
    while True:
        st3 = GenericStorage.objects.exclude(albums__filename=album.filename)\
                                    .order_by('?')[0]
    
        if st3.can_handle(storage=album.size):
            copy_s3(st2, st3, album.filename)
            break
    
