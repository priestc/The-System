#!/usr/bin/env python

import os
import shutil
import tempfile
import urllib
import urllib2
import zipfile

from utils import *

from optparse import OptionParser
from types import ListType

import mutagen
from multipart import MultiPartForm

############################

url = 'http://localhost:8000/upload'

############################

parser = OptionParser(usage="%prog [PATH] [options]", version="0.01")

parser.add_option('-a', "--artist",
                  dest="artist",
                  help="Manually set the artist name (ignore ID3 tags)")
                  
parser.add_option('-b', "--album",
                  dest="album",
                  help="Manually set the album name (ignore ID3 tags)")

parser.add_option('-m', "--album_meta",
                  dest="album_meta",
                  help="Manually set the album neta value (ignore ID3 tags)")

parser.add_option("--bootleg",
                  dest="bootleg",
                  action="store_true",
                  default=False,
                  help="This album is a bootleg (disables bitrate checks)")
                  
(options, args) = parser.parse_args()


# get the path to the directory to upload.
try:
    path = args[0]
except IndexError:
    path = None

# if no path was specified, then use the current working directory
if not path:
    path = os.getcwd()

############################
############################

# all mp3 presets that are allowed. Also, mappings to a shorthand name
acceptable = {"--alt-preset extreme": "-ape",
	          "--alt-preset standard": "-aps",
	          "--alt-preset fast standard": "-apfs",
	          "--alt-preset fast extreme": "-apfe",
	          "--alt-preset insane": "-api",
	          "-V 0": "-V0",
	          "-V 0 --vbr-new": "-V0",
	          "-V 1": "-V1",
	          "-V 1 --vbr-new": "-V1",
	          "-V 2": "-V2",
              "-V 2 --vbr-new": "-V2",
}


############################
############################

tmp = tempfile.mkdtemp()
    
# only files less than 100MB and no directories
files = [f for f in os.listdir(path)
            if os.path.isfile(f) and os.stat(path).st_size < 104857600]

for f in files[:500]:
    # move all files to the subdirectory
    # (limit to 500 incase of a user error)
    subdir_path = os.path.join(tmp, os.path.basename(f))
    shutil.copyfile(f, subdir_path)

############################
############################

def is_VX(f):
    """
    Determine if the file was encoded with either -V0, -V1, or -V2
    """
    
    return f.info.preset in acceptable.keys()

def has_tags(filepath):
    """
    Does the mp3 have all the correct tags?
    """
    
    t = get_tags_dict(filepath)
    if t:
        return bool(t['artist'] and t['album'] and t['track'] and t['date'])
    
    return False

def is_appropriate(filepath, is_bootleg):
    """
    If the file is appropriate (lame mp3 with proper tags), return 'ADD'
    so the file gets added to the zip archive. If the file is a log file or
    other white listed file, it gets added too. MP3 files that are not LAME VX
    or are not tagged properly return 'REJECTED'. Anything else returns
    'IGNORE' to be silently ignored. If the file is a bootleg, ignore the
    checks for it being Vx.
    """
 
    f = mutagen.File(filepath)
    filename = os.path.basename(filepath)
    
    if isinstance(f, mutagen.mp3.MP3):
        if is_VX(f) or is_bootleg:
            if has_tags(filepath):      
                return "ADD" # add to archive!
            else:
                return "MISSING TAGS"
        else:
            return "NOT VX"
        
    else:
        if filename.endswith(".log"):
            # Logfiles get included
            return "ADD"
        
        elif filename.startswith("folder."):
            if is_image(filepath):
                # is a correct image
                return "ADD"
            else:
                return "NOT VALID IMAGE"
            
    return "IGNORE"

def set_tag(path, tag, value):
    pass


def append_tag(f, tag, value):
    return None

def get_tags_dict(path):
    """
    Returns a dict of all the tags in the file (if it has any)
    """
    
    try:
        # just in case the file is corrupted, don't complain
        # (could throw any number of errors)
        data = mutagen.File(path)
    except:
	    # (this catches all errors because other filetypes might
	    # raise all sorts of crap)
		return None
               
    if isinstance(data, mutagen.mp3.MP3):
		try: # check if it has APEv2 tags (these take priority)
			ape_data = mutagen.apev2.APEv2(path)
			setattr(ape_data, "info", data.info)
			tags = APE(ape_data).info
		except: # otherwise, read ID3v2 followed by ID3v1
			tags = MP3(data).info
			
    else:
        return None
    

    if "/" in tags['track']:
        t = tags['track']
        index = t.find('/')
        tags['track'] = t[:index]
        
    return tags
         
############################
############################

if __name__ == '__main__':

    # list of all files that will be added to the zip then uploaded
    to_upload = []

    #files that do not pass the validation (not MP3 or not -V2, -V1 or -V0)
    failed = []
    
    # get all filenames in the temp dir (where we have already copied all files to)
    for filename in os.listdir(tmp):
        filepath = os.path.join(tmp, filename)
        
        if options.artist:
            set_tag(filename, 'artist', options.artist)
            
        if options.album:
            set_tag(filename, 'album', options.album)
            
        if options.album_meta:
            append_tag(filename, 'comment', options.album_meta)
            
        ret = is_appropriate(filepath, options.bootleg)
        
        if ret == 'ADD':
            print 'add:', filename
            to_upload.append(filepath)
            
        elif ret == 'IGNORE':
            print "ignore:", filename
                  
        else:
            print "rejected:", filename, ret
            failed.append(filename)
            
    print "------------"
    
    tmpzip = tempfile.TemporaryFile()
    z = zipfile.ZipFile(tmpzip, 'w', zipfile.ZIP_STORED)
    
    # iterate until we get a MP3 file and read it's album/date/artist values
    # so we know what to name the folder on the zip file
    # this extra iteration is required because not all files will necessairly
    # be MP3 files
    
    for f in to_upload:
        tags = get_tags_dict(f)
        if tags:
            album = clean(tags['album']).encode('ascii','replace')
            artist = clean(tags['artist']).encode('ascii','replace')
            preset = acceptable[tags['preset']]
            date = clean(str(tags['date'])).encode('ascii','replace')
            
            path_in_zip = "{artist} - ({date}) {album} [{preset}]"\
            .format(album=album, artist=artist, date=date, preset=preset)
            break
    
    # now go through all appropriate files and add them to a zip, maning them
    # according to their tags
    
    for f in to_upload:
        tags = get_tags_dict(f)
        if tags:
            track = tags.get('track', 0).encode('ascii','replace')
            disc = tags.get('disc', "")
            title = clean(tags.get('title', 'title')).encode('ascii','replace')
            
            track = "{track:02d}".format(track=int(track))
            
            if disc:
                track = "{disc}{track}".format(disc=int(disc), track=track)
            
            file_on_zip = "{track} - {title}.mp3".format(title=title, track=track)

            
        else:
            # not an MP3, use original filename on zip
            file_on_zip = os.path.basename(f)
        
        s = os.path.join(path_in_zip, file_on_zip)
        z.write(f, s)
    
    ################ now do the upload
    
    if to_upload:
        mpform = MultiPartForm()
        mpform.add_field('artist', artist)
        mpform.add_field('album', album)
        mpform.add_field('album_meta', options.album_meta or "")
        mpform.add_file('file', 'album.zip', tmpzip)
        
        body = str(mpform)
        
        request = urllib2.Request(url)
        request.add_header('User-agent', 'The Project Command Line Client')
        request.add_header('Content-type', form.get_content_type())
        request.add_header('Content-length', len(body))
        request.add_data(body)
        
        print urllib2.urlopen(request).read()
    else:
        print "nothing to upload, all files rejected"
        
    ############### cleanup

    z.close()
    shutil.rmtree(tmp)
    
    
    
    
        

