import random
import hashlib

def make_filename(artist, album):
    r = random.randint(100,999)
    key = "{0}{1}{2}".format(artist, album, r)
    return hashlib.sha1(key).hexdigest()
