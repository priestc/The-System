#!/usr/bin/env python

"""This script does the following:
    
First it takes all files in either the current directory, or the passed in path
and copies them into a temp folder.

Then it looks at each file and determines if it should be added to the archive
based on the filename, LAME encoding and tags present.

it then takes all eligible files and adds them to a zip archive. The zip archive
is then uploaded to the project's master server

"""
# enter the default password below
password = ''


# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

import os
import shutil
import tempfile
import zipfile

from utils import *

from optparse import OptionParser
from types import ListType

from collections import defaultdict

import mutagen
from multipart import send_request, check_dupe

from colorama import init as colorinit
colorinit(autoreset=True)

############################

url = 'http://thesystem.chickenkiller.com'

############################

parser = OptionParser(usage="%prog [PATH] [options]", version="0.1")

parser.add_option('-p', "--password",
                  dest="password",
                  metavar="PASS",
                  default=None,
                  help="The password for the whole thing to work (gotten from you-know-where)")

parser.add_option('-v', "--verify",
                  dest="verify",
                  action="store_true",
                  help="Verify before uploading")
                  
parser.add_option('-a', "--artist",
                  dest="artist",
                  metavar="ARTIST",
                  help="Manually set the artist name (ignore ID3 tags)")
                  
parser.add_option('-b', "--album",
                  dest="album",
                  metavar="ALBUM",
                  help="Manually set the album name (ignore ID3 tags)")

parser.add_option('-m', "--meta",
                  dest="meta",
                  metavar="META",
                  help="Album meta data (such as 'remastered 2003')")

parser.add_option("--archive-only",
                  dest="archive",
                  action="store_true",
                  default=False,
                  help="Outputs archive to the current working directory for inspection, and skips upload")

parser.add_option("--bootleg",
                  dest="bootleg",
                  action="store_true",
                  default=False,
                  help="This album is a bootleg (disables bitrate checks)")

parser.add_option("-q", "--silent",
                  dest="silent",
                  action="store_true",
                  default=False,
                  help="No output except for the server response")

parser.add_option("--local",
                  dest="local",
                  action="store_true",
                  default=False,
                  help="Use local dev server (testing only)")
            
(options, args) = parser.parse_args()

if options.password:
    password = options.password

if (not options.archive) and password == '':
    print "Password Required"
    raise SystemExit

if options.local:
    url = 'http://localhost:8000'

# get the path to the directory to upload.
try:
    path = args[0]
except IndexError:
    # if no path was specified, then use the current working directory
    path = os.getcwd()

############################
############################

# all mp3 presets that are allowed. Also, mappings to a shorthand name
# use a defaultdict to handle when the preset is actually a bitrate

acceptable_profiles = {"--alt-preset extreme": "-ape",
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

def profile_name(profile):
    """
    Returns a shorthand formatted version of the profile/bitrate.
    """
    
    if profile in acceptable_profiles.keys():
        return acceptable_profiles[profile]
    else:
        # its a bitrate instead, 192000 -> 192
        return str(int(profile) / 1000)

############################
############################

def is_VX(f):
    """
    Determine if the file was encoded with either -V0, -V1, or -V2
    """
    
    return f.info.preset in acceptable_profiles.keys()

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

def set_tag(path, tag, value, append=False):
    """
    Edit the mp3 in the path's tags to reflect the new value
    this function works for either ID3 or APE tagged MP3's
    """

    data, tag_type = get_tags_object(path)
    
    if tag_type == "APE":
        tags = APE(data)
    elif tag_type == 'ID3':
        tags = MP3(data)

    tags.set_value(tag, value, append=append)

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

    # doggone tag libraries alwaystrying to be cute

    if tags['track'] and ("/" in tags['track']):
        t = tags['track']
        index = t.find('/')
        tags['track'] = t[:index]
        
    if tags['disc'] and ("/" in tags['disc']):
        t = tags['disc']
        index = t.find('/')
        tags['disc'] = t[:index]
        
    return tags
         
############################
############################

# create temp dirs
base_tmp = tempfile.mkdtemp()
tmp_mp3 = os.path.join(base_tmp, 'mp3')
tmp_other = os.path.join(base_tmp, 'other')

os.mkdir(tmp_mp3)
os.mkdir(tmp_other)

def clean_and_exit():
    shutil.rmtree(base_tmp)
    raise SystemExit

if __name__ == '__main__':
    
    # move all files to the temp directory
    
    for root, dirs, files in os.walk(path):
        for f in files:
            full_path = os.path.join(root, f)
            if os.stat(full_path).st_size < 104857600:
                if full_path.endswith('.mp3'):
                    tmp = tmp_mp3
                elif full_path.endswith('.log') or\
                      (f.startswith('folder.') and is_image(f)):
                    tmp = tmp_other
                else:
                    tmp = None
                    if not options.silent: print blue("IGNORE:"), full_path
                    
                if tmp:
                    temp_path = os.path.join(tmp, f)
                    shutil.copyfile(full_path, temp_path)
                
            else:
                # ignore any file larger than 100 MiB
                if not options.silent: print blue("TOO BIG, IGNORING:"), full_path
                
    
    # list of all files that will be added to the zip
    mp3_to_upload = []
    
    # get all filenames in the mp3 temp dir
    # (where we have already copied all files to)
    for filename in sorted(os.listdir(tmp_mp3)):
        filepath = os.path.join(tmp_mp3, filename)
        
        if options.artist:
            set_tag(filepath, 'artist', options.artist)
            
        if options.album:
            set_tag(filepath, 'album', options.album)
            
        if options.meta:
            set_tag(filepath, 'comment', options.meta, append=True)
            
        ret = is_appropriate(filepath, options.bootleg)
        
        if ret == 'ADD':
            mp3_to_upload.append(filepath)
                  
        else:
            if not options.silent: print bright_red('reject'),\
                                         filename,\
                                         bright_red(ret)
            clean_and_exit()
        
    # if the archive option is ~not~ used, the temp file will automatically
    # delete itself when the script terminates
    delete = not options.archive
    tmpzip = tempfile.NamedTemporaryFile(delete=delete)
    z = zipfile.ZipFile(tmpzip, 'w', zipfile.ZIP_STORED)
    
    # add all mp3 files to the zip archive
    
    for f in mp3_to_upload:
        tags = get_tags_dict(f)
        album = clean(tags['album'])
        artist = clean(tags['artist'])
        preset = profile_name(tags['preset'])
        date = clean(str(tags['date']))
        
        path_in_zip = "{artist} - ({date}) {album} [{preset}]"\
        .format(album=album, artist=artist, date=date, preset=preset)
        
        track = tags.get('track', 0)
        disc = tags.get('disc', "")
        title = clean(tags.get('title', 'title'))
        
        track = "{track:02d}".format(track=int(track))
        
        if disc:
            track = "{disc}{track}".format(disc=int(disc), track=track)
        
        file_on_zip = "{track} - {title}.mp3".format(title=title, track=track)
            
        s = os.path.join(path_in_zip, file_on_zip)
        if not options.silent:
            print bright_green("add:"), os.path.join(path_in_zip, file_on_zip)
        z.write(f, s)
            
    # now go through all non-mp3 files and add them to the zip
    
    for f in os.listdir(tmp_other):
        file_on_zip = os.path.basename(f)
        s = os.path.join(path_in_zip, file_on_zip)
        if not options.silent:
            print bright_green("add:"), os.path.join(path_in_zip, file_on_zip)
        z.write(f, s)
    
    if not options.silent: print "------------"
    
    ################ check that this album hasnt already been uploaded
    
    result = check_dupe(artist, album, url)

    if result == 'Yes':
        print bright_red("This album has already been uploaded")
        clean_and_exit()
    elif result == 'No':
        pass
    else:
        print bright_red("Error occured when checking for dupe")
        clean_and_exit()
    
    ################ now do the upload
    
    if options.verify:
        answer = raw_input("Does the above look all right? Y/n?")
        if answer.upper() == 'N':
            clean_and_exit()
        
    if mp3_to_upload and not options.archive:
        data = dict(artist=artist, album=album, meta=options.meta,
                    profile=preset, date=date, password=password)
        send_request(tmpzip, data, url, options.silent)
    elif options.archive:
        if not options.silent: print "No upload, archive only"
    else:
        if not options.silent: print "nothing to upload, all files rejected"
        clean_and_exit()
        
    ############### cleanup

    z.close()

    if options.archive:
        #if the archive option is used, we have to manually delete the temp file
        tmpzip.seek(0)
        f = open('archive.zip', 'w')
        f.writelines(tmpzip.readlines())
        os.remove(tmpzip.name)

    clean_and_exit()





