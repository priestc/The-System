import Image
import re

from types import ListType
from poopagen import id3
from colorama import Fore, Back, Style

def bright_green(text):
    return "{color}{style}{text}{reset}"\
                .format(color=Fore.GREEN, style=Style.BRIGHT,
                        text=text, reset=Style.RESET_ALL)

def bright_red(text):
    return "{color}{style}{text}{reset}"\
                .format(color=Fore.RED, style=Style.BRIGHT,
                        text=text, reset=Style.RESET_ALL)

def blue(text):
    return "{color}{text}{reset}"\
                .format(color=Fore.BLUE, text=text, reset=Fore.RESET)

def clean(value):
    """
    Strip out characters that are not allowed in some filesystems
    """
    #print value
    return re.sub(r'[*|\/:"<>?]', '', value).encode('ascii','replace')

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
    
# abstract tag class. find the tags we need given a tag list from poopagen
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
       
    def find(self, tag_list):
        for tag in tag_list:
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
    comment = ["COMM::'eng'"]
	
    def set_value(self, tag, value, append):
        """
        Writing ID3 tags is hard
        """
	    
        tag_list = getattr(self, tag)

        for tag in tag_list:
            try:
                old = self.data[tag].text[0] #may raise KeyError
                #import ipdb; ipdb.set_trace()
                import_tag = tag.replace("::'eng'", '') # dirty hack
                
                #get proper ID3 tag class, TIT2, COMM, TPE, etc
                Obj = getattr(id3, import_tag)
                
                if append:
                    self.data[tag] = Obj(encoding=3, text=old + " [%s]" % value)
                    self.data.save()
                else:
                    self.data[tag] = Obj(encoding=3, text=value)
                    self.data.save()
            except KeyError:
                pass




                
class APE(Tags):
    artist = ['Artist']
    album = ['Album']
    date = ['Year', 'Date']
    track = ['Track']
    title = ['Title']
    disc = ['Disc', 'Disk']
    comment = ['Comment']

    def set_value(self, tag, value, append):
        """
        Writing APE tags is easy
        """
        
        tag_list = getattr(self, tag)
        
        for tag in tag_list:
            try:
                old = self.data[tag] #may raise KeyError
                if append:
                    self.data[tag] = str(old[0]) + (" [%s]" % value)
                    self.data.save()
                else:
                    self.data[tag] = value
                    self.data.save()
            except KeyError:
                pass




