import os
import shutil
import tempfile
import zipfile
import urllib
import urllib2

import poopagen
from utils import *
from multipart import MultiPartForm
from tags import *

VERSION = 0.3
USER_AGENT = 'The Project Command Line Client v%.1f' % VERSION

class ImproperMP3Error(Exception): pass

class ZipFile(object):
    """
    In: a list of absolute file paths
    Out: A zipfile of all those files
    """
    
    def __init__(self, save_to_file, mp3_paths, other_paths):
        self.mp3_paths = mp3_paths
        self.other_paths = other_paths
        self.save_to_file = save_to_file
        self.z = None
    
    def _write(self):
        """
        Turn the list of paths into files and put them into a zip
        """
        
        folder_on_zip = self.make_folder_name()
        
        # render all the filenames so we can write them sorted
        files_on_zip = []
        for path in self.mp3_paths:
            files_on_zip.append((path, self.make_filename(path)))
        
        # sort by the rendered filename
        sort = sorted(files_on_zip, key=lambda x: x[1])
        
        for (path, file_on_zip) in sort:
            zippath = os.path.join(folder_on_zip, file_on_zip)
            self.z.write(path, zippath)
            
        for path in self.other_paths:
            file_on_zip = os.path.basename(path)
            zippath = os.path.join(folder_on_zip, file_on_zip)
            self.z.write(path, zippath)
            
    def show_contents(self):
        """
        Prints out all the files in the archive
        """
        
        for info in self.get_zip().infolist():
            print info.filename
        
    def make_folder_name(self):
        path = self.mp3_paths[0]
        tags = get_tags_dict(path)
        album = clean(tags['album'])
        artist = clean(tags['artist'])
        preset = tags['preset']
        date = clean(str(tags['date']))
        
        return "{artist} - ({date}) {album} [{preset}]"\
        .format(album=album, artist=artist, date=date, preset=preset)
        
    def make_filename(self, path):
        """
        Construct the file name of each MP3 file on the archive
        """
        
        tags = get_tags_dict(path)
        track = tags.get('track', 0)
        disc = tags.get('disc', "")
        title = clean(tags.get('title', 'title'))
        
        track = "{track:02d}".format(track=int(track))
        
        if disc:
            track = "{disc}{track}".format(disc=int(disc), track=track)
        
        return "{track} - {title}.mp3".format(title=title, track=track)
      
    def get_zip(self):
        if not self.z:
            self.z = zipfile.ZipFile(self.save_to_file, 'w', zipfile.ZIP_STORED)
            self._write()
            self.z.close()
            
        return self.z

class FileList(object):
    IMAGE_EXTENSIONS = ['jpg', 'png']
    GENERAL_EXTENSIONS = ['mp3', 'log']
    
    def __init__(self, path, bootleg):
        self.path = path
        self.bootleg = bootleg
        self.other = []
        self.mp3s = []
        self.warnings = []
        
        self.sort()
        
    def sort(self):
        """
        Sort all files under the path into either Other or MP3 lists
        """
        
        for (root, dirs, files) in os.walk(self.path):
            for path in (os.path.join(root, f) for f in files):
            
                move = self.move_acceptable(path)
                
                if move is True:
                    if self.mp3_acceptable(path):
                        self.mp3s.append(path)
                    else:
                        self.other.append(path)
                    
                else:
                    msg = blue("IGNORING (%s): %s" % (move, path))
                    self.warnings.append(msg)
    
    def move_acceptable(self, path):
        """
        Returns True if the file is eligible to be moved to the temp directory
        based on it's filename and filesystem stats. If it doesn't qualify, it
        returns a string explaining why.
        """
        
        exts = self.IMAGE_EXTENSIONS + self.GENERAL_EXTENSIONS
        ext = path[-3:].lower()
        
        if os.stat(path).st_size > 104857600:
            return "TOO BIG"
        
        if ext not in exts:
            return "FILE EXTENSION"
        
        return True

    def mp3_acceptable(self, path):
        """
        Is the MP3 file correct? Is it Vx? Does it have all the tags?
        """
        
        if not path.endswith('.mp3'): return False
        data, tag_type = get_tags_object(path)
        
        if not data:
            raise ImproperMP3Error("%s is a corrupt MP3 file" % path)
        
        if tag_type == "APE":
            tags = APETag(data)
        elif tag_type == 'ID3':
            tags = MP3Tag(data)
        
        if not tags.has_all_tags():
            raise ImproperMP3Error("%s is missing some tags" % path)
        
        if not self.bootleg:
            if not tags.is_VX(): raise ImproperMP3Error("%s is not Vx" % path)
        
        return True
    
    def get_lists(self):
        return {'mp3s': self.mp3s, 'others': self.other}
    
def copy_to_temp(mp3s, other, tmp_dir):
    tmp_mp3 = os.path.join(tmp_dir, 'mp3')
    tmp_other = os.path.join(tmp_dir, 'other')
    os.mkdir(tmp_mp3)
    os.mkdir(tmp_other)
    
    new_mp3_list = []
    for path in mp3s:
        temp_path = os.path.join(tmp_mp3, os.path.basename(path))
        new_mp3_list.append(temp_path)
        shutil.copyfile(path, temp_path)
    
    new_other_list = []
    for path in other:
        temp_path = os.path.join(tmp_other, os.path.basename(path))
        new_other_list.append(temp_path)
        shutil.copyfile(path, temp_path)
    
    return {'mp3s': new_mp3_list, 'others': new_other_list}
    
def validate_mp3s(mp3s):
    """
    Make sure ~all~ mp3's have the exact same value for date, album and artist
    also make sure the tracknumbers are sequencial. Returns a dict with the
    artist, and album if it passed
    """
    
    tags = get_tags_dict(mp3s[0])
    album = tags['album']
    artist = tags['artist']
    date = tags['date']
    preset = tags['preset']
    
    tracks = []
    for path in mp3s:
        tags = get_tags_dict(path)
        tracks.append(tags['track'])
        if not artist == tags['artist']: return "ARTIST"
        if not album == tags['album']: return "ALBUM"
        if not date == tags['date']: return "DATE"
        if not preset == tags['preset']: return "ENCODING"
    
    for i,t in enumerate(sorted(int(t) for t in tracks)):
        i = i+1 ## enumerate starts at zero, tracknumbers should start at one
        if not t == i: return "NON SEQUENCIAL TRACKS"
                
    return {'artist': clean(artist), 'album': clean(album),
            'preset': clean(preset), "date": clean(date)}
            
def send_request(tmpzip, data, url):
    """
    Encodes all the data into a Http request where the album will be uploaded
    it returns the response as a string. If there is a server error, it will
    return the HTML of that error. If it's a success, the server returns
    "#### bytes recieved from server"
    """
    
    tmpzip.seek(0)
    
    mpform = MultiPartForm()
    mpform.add_field('artist', data['artist'])
    mpform.add_field('album', data['album'])
    mpform.add_field('meta', data['meta'] or "")
    mpform.add_field('date', data['date'])
    mpform.add_field('password', data['password'])
    mpform.add_field('profile', data['profile'])
    mpform.add_file('file', 'album.zip', tmpzip)

    body = str(mpform)
    
    request = urllib2.Request(url + "/upload")
    request.add_header('User-agent', USER_AGENT)
    request.add_header('Content-type', mpform.get_content_type())
    request.add_header('Content-length', len(body))
    request.add_data(body)
    
    try:
        return urllib2.urlopen(request).read()
    except Exception, e:
        return e.read()

def check_dupe(artist, album, url):
    """
    Check that this album/artist combo does not already exist in the system.
    It also checks to see if this client version is a valid version.
    """
    
    ver = None
    dupe = True
    request = urllib2.Request(url + "/album/check_dupe")
    request.add_header('User-agent', USER_AGENT)
    data = urllib.urlencode(dict(album=album, artist=artist))
        
    try:
        result = urllib2.urlopen(request, data=data).read()
    except Exception:
        result = ""

    if result.startswith('Yes'):
        dupe = True
        l = 3
    
    elif result.startswith('No'):
        dupe = False
        l = 2
    
    elif result == "Too Old Client":
        # the client is too old, who cares is it's a dupe
        return (None, None, True)
       
    else:
        # some error occured, who knows
        return (None, None, None)

    if len(result) > l:
        # if the response is bigger than 3 or 2 letters, the 4th (or 3rd) 
        # to the end will be the current latest version of the client script
        # announce to the user that he/she may want to upgrade
        ver = result[l+1:]
        
    return (dupe, ver, False)
