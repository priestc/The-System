import os
import shutil
import tempfile
import zipfile
import urllib
import urllib2

from collections import defaultdict

import poopagen
from utils import *
from multipart import MultiPartForm
from tags import *

VERSION = 0.5
USER_AGENT = 'The Project {interface} Client v%.1f' % VERSION

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
        ret = []
        for info in self.get_zip().infolist():
            ret.append(info.filename)
        
        return "\n".join(ret)
        
    def make_folder_name(self):
        """
        Construct the name of the file on the cip based on the file's tags
        """
        
        path = self.mp3_paths[0]
        tags = get_tags_dict(path)
        
        album = clean(tags['album'])
        artist = clean(tags['artist'])
        preset = clean(tags['preset'])
        date = clean(tags['date'])
        
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
                    msg = "IGNORING (%s): %s" % (move, path)
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
    
    def get_temp_lists(self, tmp_dir):
        return self.copy_to_temp(self.mp3s, self.other, tmp_dir)
    
    def copy_to_temp(self, mp3s, other, tmp_dir):
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

def is_sequencial(l):
    """
    Is the list sequencial? Takes a list of ints.
    """
    
    for i,t in enumerate(l):
        i = i+1 ## enumerate starts at zero, tracknumbers should start at one
        if not t == i: return False
    
    return True

def overwrite_tags(mp3s, artist, album, date, meta):
    """
    given a list of mp3s, change the tags if and only if the value is not None.
    """
    
    if artist:
        set_tags(mp3s, 'artist', artist)
    if album:
        set_tags(mp3s, 'album', album)
    if date:
        set_tags(mp3s, 'date', date)   
    if meta:
        set_tags(mp3s, 'comment', meta, append=True)
    
    
def validate_mp3s(mp3s):
    """
    Make sure ~all~ mp3's have the exact same value for date, album and artist
    also make sure the tracknumbers are sequencial. Returns a dict with the
    artist, and album if it passed
    """
    
    if len(mp3s) == 0:
        raise ImproperMP3Error("NO FILES")
    
    tags = get_tags_dict(mp3s[0])
    album = tags['album']
    artist = tags['artist']
    date = tags['date']
    preset = tags['preset']
    
    discs = defaultdict(list)
    for path in mp3s:
        tags = get_tags_dict(path)
        disc = tags.get('disc', 1)
        tracks = discs[disc]
        tracks.append(tags['track'])
        if not artist == tags['artist']: raise ImproperMP3Error("ARTIST")
        if not album == tags['album']: raise ImproperMP3Error("ALBUM")
        if not date == tags['date']: raise ImproperMP3Error("DATE")
        if not preset == tags['preset']: raise ImproperMP3Error("ENCODING")
    
    for (disc, items) in discs.items():
        tracks = sorted(int(t) for t in tracks)
        if not is_sequencial(tracks):
            raise ImproperMP3Error("NON SEQUENCIAL TRACKS")
                
    return {'artist': clean(artist), 'album': clean(album),
            'preset': clean(preset), "date": clean(date)}
            
def send_request(tmpzip, data, url, interface="Command Line"):
    """
    Encodes all the data into a Http request where the album will be uploaded
    it returns the response as a string. If there is a server error, it will
    return the HTML of that error. If it's a success, the server returns
    "#### bytes recieved from server"
    """
    
    tmpzip.seek(0)
    
    mpform = MultiPartForm()
    mpform.add_field('artist', str(data['artist']))
    mpform.add_field('album', str(data['album']))
    mpform.add_field('meta', str(data['meta'] or ""))
    mpform.add_field('date', str(data['date']))
    mpform.add_field('password', str(data['password']))
    mpform.add_field('profile', str(data['profile']))
    mpform.add_file('file', 'album.zip', tmpzip)

    body = str(mpform)
    
    request = urllib2.Request(url + "/upload")
    
    ua = USER_AGENT.format(interface=interface)
    request.add_header('User-agent', ua)
    request.add_header('Content-type', mpform.get_content_type())
    request.add_header('Content-length', len(body))
    request.add_data(body)
    
    try:
        return urllib2.urlopen(request).read()
    except Exception, e:
        return e.read()

class VerifyClient(object):
    """
    a class that handles verification of the upload before the actual upload
    happens. It...
    1. makes sure the client is the latest version,
    2. makes sure the password is correct
    3. makes sure the client is not such an old version
    4. makes sure the album+artist has not already been uploaded
    """
    
    def __init__(self, password, url, artist=None,
                        album=None, interface="Command Line"):
        
        self.artist = artist
        self.album = album
        self.url = url + "/pre_upload"
        self.password = password
        self.ua = USER_AGENT.format(interface=interface)
        
        self.dupe = False
        self.client_reject = False
        self.latest_client = None
        self.password_match = False
        
        self.made_request = False
        
    def make_request(self):
        """
        Makes the request to the server to get all the information to verify
        the information
        """
        
        request = urllib2.Request(self.url)
        request.add_header('User-agent', self.ua)
        data = urllib.urlencode(dict(album=self.album, 
                                     artist=self.artist,
                                     password=self.password))
            
        #try:
        self.result = urllib2.urlopen(request, data=data).read()
        #except Exception, error:
            #return error.read()
        
        self.made_request = True
        
        try:
            (self.dupe, self.min_client, self.latest_client,
                self.password_match) = self.result.split(',')
        except ValueError:
            raise RuntimeError('Invalid Response')
        
        self.min_client = float(self.min_client)
        self.latest_client = float(self.latest_client)
        
    
    def is_dupe(self):
        if not self.made_request: self.make_request()
        
        if self.dupe == "Yes":
            return True
        
        if self.dupe == "No":
            return False
        
    def is_password_match(self):
        if not self.made_request: self.make_request()
        
        if self.password_match == "Yes":
            return True
        
        if self.password_match == "No":
            return False
        
    def is_allowed_client(self):
        """
        is the client version greater than the minimum client version
        supplied by the server?
        """
        
        if not self.made_request: self.make_request()
        return VERSION >= self.min_client
    
    def is_latest_client(self):
        """
        Is there a greater version of the client available?
        """
        
        if not self.made_request: self.make_request()
        return VERSION >= float(self.latest_client)

    def get_latest_client_version(self):
        if not self.made_request: self.make_request()
        return self.latest_client



































        
    
        
    
