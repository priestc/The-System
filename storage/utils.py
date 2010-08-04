import boto

def copy_s3(real_orig, real_dest, album):
    """
    Copy a key from one S3 bucket to another when both buckets are
    owned by a different user. real_* == S3Bucket model, not GenericStorage
    """
    
    dest_user_id = real_dest.get_user_id()
    
    # get the key object from the original storage location
    orig_key = album.get_key_object(real_orig.name)
    
    # get a copy of the original acl so we can restore it later
    orig_key_policy = orig_key.get_acl()
    
    # allow the destination to get a copy of the key by adding the permission
    orig_key.add_user_grant("READ", dest_user_id)
    
    # copy the key into the destination bucket
    real_dest.get_bucket().copy_key(album.filename, real_orig.internal_name,
                            album.filename)
    
    # restore the permission object
    orig_key.set_acl(orig_key_policy)
    
    # make a record of the mirror on the database
    album.storages.add(real_dest)
    album.save()
    
    return True

def match(st1, st3):
    """
    Returns the class of the two storage engines if they are the same,
    otherwise, return None. If the two storage engines are the same, we can
    mirror by copying the file remotely, instead of uploading it another time,
    hence saving bandwidth. 
    """
    
    if type(st1) == type(st2):
        return type(st2)
