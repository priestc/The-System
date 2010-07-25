#!/usr/bin/env python

"""This script does the following:
    
First it takes all files in either the current directory, or the passed in path
and copies them into a temp folder.

Then it looks at each file and determines if it should be added to the archive
based on the filename, LAME encoding and tags present.

it then takes all eligible files and adds them to a zip archive. The zip archive
is then uploaded to the project's master server

"""

import os
import shutil
import sys
import tempfile
import zipfile

from utils import *

from optparse import OptionParser
from types import ListType

import mutagen
from multipart import send_request

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

parser.add_option("--test",
                  dest="test",
                  action="store_true",
                  default=False,
                  help="Test archive")

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
    # if no path was specified, then use the current working directory
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
            
    return "IGNORE"

def set_tag(path, tag, value):
    raise NotImplementedError


def append_tag(f, tag, value):
    raise NotImplementedError

def get_tags_object(path):
    """
    Get the tag object. Used for getting and setting tag information
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
            return ape_data, "APE"
        except: # otherwise, read ID3v2 followed by ID3v1
            return data, "ID3"

    else:
        return None

def get_tags_dict(path):
    """
    Returns a dict of all the tags in the file (if it has any)
    """
    
    data, tag_type = get_tags_object(path)
    
    if tag_type == "APE":
        tags = APE(data).info
    elif tag_type == 'ID3':
        tags = MP3(data).info

    if "/" in (tags['track'] or ""):
        t = tags['track']
        index = t.find('/')
        tags['track'] = t[:index]
        
    if "/" in (tags['disc'] or ""):
        t = tags['disc']
        index = t.find('/')
        tags['disc'] = t[:index]
        
    return tags
         
############################
############################

if __name__ == '__main__':

    # move all files to the temp directory

    base_tmp = tempfile.mkdtemp()
    tmp_mp3 = os.path.join(base_tmp, 'mp3')
    tmp_other = os.path.join(base_tmp, 'other')
    
    os.mkdir(tmp_mp3)
    os.mkdir(tmp_other)
    
    for root, dirs, files in os.walk(path):
        for f in files:
            full_path = os.path.join(root, f)
            if os.stat(full_path).st_size < 104857600:
                if full_path.endswith('.mp3'):
                    tmp = tmp_mp3
                elif full_path.endswith('.log') or f.startswith('folder.'):
                    tmp = tmp_other
                else:
                    print full_path
                temp_path = os.path.join(tmp, f)
                shutil.copyfile(full_path, temp_path)
    
    # list of all files that will be added to the zip
    mp3_to_upload = []
    other_to_upload = []
    
    # get all filenames in the mp3 temp dir
    # (where we have already copied all files to)
    for filename in os.listdir(tmp_mp3):
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
            mp3_to_upload.append(filepath)
            
        elif ret == 'IGNORE':
            print "ignore:", filename
                  
        else:
            print "rejected:", filename, ret
            sys.exit()
            
    print "------------"
    
    # if the test option is not used, the temp file will automatically
    # delete itself when the script terminates
    delete = not options.test
    tmpzip = tempfile.NamedTemporaryFile(delete=delete)
    z = zipfile.ZipFile(tmpzip, 'w', zipfile.ZIP_STORED)
    
    # iterate until we get a MP3 file and read it's album/date/artist values
    # so we know what to name the folder on the zip file
    
    for f in mp3_to_upload:
        tags = get_tags_dict(f)
        print tags
        album = clean(tags['album']).encode('ascii','replace')
        artist = clean(tags['artist']).encode('ascii','replace')
        preset = acceptable[tags['preset']]
        date = clean(str(tags['date'])).encode('ascii','replace')
        
        path_in_zip = "{artist} - ({date}) {album} [{preset}]"\
        .format(album=album, artist=artist, date=date, preset=preset)
        
        track = tags.get('track', 0).encode('ascii','replace')
        disc = tags.get('disc', "")
        title = clean(tags.get('title', 'title')).encode('ascii','replace')
        
        track = "{track:02d}".format(track=int(track))
        
        if disc:
            track = "{disc}{track}".format(disc=int(disc), track=track)
        
        file_on_zip = "{track} - {title}.mp3".format(title=title, track=track)
            
        s = os.path.join(path_in_zip, file_on_zip)
        z.write(f, s)
            
    # now go through all non-mp3 files and add them to the zip
    
    for f in other_to_upload:
        file_on_zip = os.path.basename(f)
        s = os.path.join(path_in_zip, file_on_zip)
        z.write(f, s)

    #z.setpassword('nmp3s')
    
    ################ now do the upload
    
    if mp3_to_upload and not options.test:
        send_request(tmpzip, artist, album, options.album_meta, url)
    elif options.test:
        print "No upload, testing only"
    else:
        print "nothing to upload, all files rejected"
        sys.exit()
        
    ############### cleanup

    z.close()
    
    if options.test:
        tmpzip.seek(0)
        f = open('test.zip', 'w')
        f.writelines(tmpzip.readlines())
        os.remove(tmpzip.name)
    
    shutil.rmtree(base_tmp)









