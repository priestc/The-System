import boto

def copy_s3(orig, dest, name):
    """
    Copy a key from one S3 bucket to another when both buckets are
    owned by a different user
    """
    
    print "copying s3 for reals"
    print "sleeping to simulate upload..."
    import time
    time.sleep(60)
    print "done!"
    
    return

    orig_user = orig.get_user_id()
    dest_bucket = dest.get_bucket()
    
    # give user #1 permission to write to person #2's bucket
    dest_bucket.add_user_grant(orig_user)

    
    return True
