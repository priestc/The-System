from types import ListType
import poopagen
from poopagen import id3

ACCEPTABLE_PROFILES = {"--alt-preset extreme": "-ape",
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

def set_tags(paths, tag, value, append=False):
    """
    Edit the mp3 in the paths tags to reflect the new value
    this function works for either ID3 or APE tagged MP3's
    """

    for path in paths:
        data, tag_type = get_tags_object(path)
        
        if tag_type == "APE":
            tags = APETag(data)
        elif tag_type == 'ID3':
            tags = MP3Tag(data)

        tags.set_value(tag, value, append=append)

def get_tags_dict(path):
    """
    Returns a dict of all the tags in the file (if it has any)
    """
    
    data, tag_type = get_tags_object(path)
    
    if tag_type == "APE":
        tags = APETag(data).info
    elif tag_type == 'ID3':
        tags = MP3Tag(data).info

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

def get_tags_object(path):
    """
    Get the tag object. Used for getting and setting tag information
    """
    
    try:
        # just in case the file is corrupted, don't complain
        # (could throw any number of errors)
        data = poopagen.File(path)
    except:
        # (this catches all errors because other filetypes might
        # raise all sorts of crap)
        return None, None
               
    if isinstance(data, poopagen.mp3.MP3):
        try: # check if it has APEv2 tags (these take priority)
            ape_data = poopagen.apev2.APEv2(path)
            setattr(ape_data, "info", data.info)
            return ape_data, "APE"
        except: # otherwise, read ID3v2 followed by ID3v1
            return data, "ID3"

    else:
        return None, None


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
        self.info['preset'] = self.preset_name()
        self.info['Vx'] = self.is_VX()
    
    def is_VX(self):
        """
        Determine if the file was encoded with either -V0, -V1, or -V2, or any
        other appropriate encoding method
        """
	
        return self.info['preset'] in ACCEPTABLE_PROFILES.values()
    
    def preset_name(self):
        """
        Returns a shorthand formatted version of the profile/bitrate.
        """
        
        preset = self.data.info.preset
        
        if preset:
            ret = ACCEPTABLE_PROFILES.get(preset, None)
            if ret:
                return ret #shorthand (allowed VX profiles)
            else:
                return preset #longhand (not allowed profiles [--r3mix, etc])
        else:
            # its a bitrate instead, 192000 -> 192
            return str(int(self.data.info.bitrate) / 1000)
      
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
        
    def has_all_tags(self):
        """
        Does the mp3 have ~all~ the correct tags?
        """
        
        t = self.info
        return bool(t['artist'] and t['album'] and t['track'] and t['date'])

# subclasses of Tags. these just specify what tag names we
# should be looking for depending on context

class MP3Tag(Tags):
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
                
class APETag(Tags):
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
