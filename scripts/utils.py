import Image
import re

from types import ListType

def clean(value):
    """
    Strip out characters that are not allowed in some filesystems
    """
    #print value
    return re.sub(r'[*|\/:"<>?]', '', value)

def is_image(filepath):
    """
    Determine if the file is a proper image file
    """
    
    try:
        im = Image.open(filepath)
    except IOError:
        # PIL can't open file, it's not an image
        return False
    else:
        # it's a proper image file!
        return True
    
# abstract tag class. find the tags we need given a tag list from mutagen
class Tags(object):
    info = {}
    def __init__(self, data):
        self.data = data
        self.info['title'] = self.find(self.title)
        self.info['track'] = self.find(self.track)
        self.info['artist'] = self.find(self.artist)
        self.info['album'] = self.find(self.album)
        self.info['date'] = self.find(self.date)
        self.info['disc'] = self.find(self.disc)
        self.info['preset'] = self.preset()
        
    def preset(self):
        return self.data.info.preset or self.data.info.bitrate
       
    def find(self, list):
        for tag in list:
            try:
                if isinstance(self.data[tag], ListType):
                    return self.data[tag][0]
                elif type(self.data[tag]) is unicode:
                    return self.data[tag]
                else:
                    return self.data[tag][0]
            except: pass
        return None

# subclasses of Tags. these just specify what tag names we
# should be looking for depending on context

class MP3(Tags):
	artist = ['TPE1', 'TP1']
	album = ['TALB', 'TAL']
	date = ['TYER','TYE', 'TDOR', 'TDRC', 'TXXX:date']
	track = ['TRCK']
	title = ['TIT2']
	disc = ['TPOS']
	
	def __init__(self,data):
		Tags.__init__(self,data)

class APE(Tags):
	artist = ['Artist']
	album = ['Album']
	date = ['Year', 'Date']
	track = ['Track']
	title = ['Title']
	disc = ['Disc', 'Disk']
	
	def __init__(self,data):
		Tags.__init__(self, data)






