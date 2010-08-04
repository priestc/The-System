import boto

def copy_s3(real_orig, real_dest, album):
    """
    Copy a key from one S3 bucket to another when both buckets are
    owned by a different user. real_* == S3Bucket model, not GenericStorage
    """
    
    # get the key object for the original storage location
    orig_key = real_orig.get_bucket().get_key(album.filename)
    
    # allow the destination to get a copy of the key by adding the permission
    orig_key.add_user_grant("READ", real_dest.get_user_id())

    # copy the key into the new bucket
    key.copy(real_dest.internal_name, album.filename)
    
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
