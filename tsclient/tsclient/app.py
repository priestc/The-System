import os
import shutil
import tempfile
import zipfile

import poopagen
from utils import *
from tags import *

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
        return {'mp3s': self.mp3s, 'other': self.other}
    
def copy_to_temp(mp3s, other, tmp_dir):
    tmp_mp3 = os.path.join(tmp_dir, 'mp3')
    tmp_other = os.path.join(tmp_dir, 'other')
    os.mkdir(tmp_mp3)
    os.mkdir(tmp_other)
    
    for path in mp3s:
        temp_path = os.path.join(tmp_mp3, os.path.basename(path))
        shutil.copyfile(path, temp_path)
        
    for path in other:
        temp_path = os.path.join(tmp_other, os.path.basename(path))
        shutil.copyfile(path, temp_path)
    
    
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
            
    
    

