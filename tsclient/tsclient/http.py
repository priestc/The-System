import itertools
import mimetools
import mimetypes
from cStringIO import StringIO
import urllib
import urllib2

VERSION = 0.3
USER_AGENT = 'The Project Command Line Client v%.1f' % VERSION

class MultiPartForm(object):
    """Accumulate the data to be used when posting a form."""

    def __init__(self):
        self.form_fields = []
        self.files = []
        self.boundary = mimetools.choose_boundary()
        return
    
    def get_content_type(self):
        return 'multipart/form-data; boundary=%s' % self.boundary

    def add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name, value))
        return

    def add_file(self, fieldname, filename, fileHandle, mimetype=None):
        """Add a file to be uploaded."""
        body = fileHandle.read()
        if mimetype is None:
            mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        self.files.append((fieldname, filename, mimetype, body))
        return
    
    def __str__(self):
        """Return a string representing the form data, including attached files."""
        # Build a list of lists, each containing "lines" of the
        # request.  Each part is separated by a boundary string.
        # Once the list is built, return a string where each
        # line is separated by '\r\n'.  
        parts = []
        part_boundary = '--' + self.boundary
        
        # Add the form fields
        parts.extend(
            [ part_boundary,
              'Content-Disposition: form-data; name="%s"' % name,
              '',
              value,
            ]
            for name, value in self.form_fields
            )
        
        # Add the files to upload
        parts.extend(
            [ part_boundary,
              'Content-Disposition: file; name="%s"; filename="%s"' % \
                 (field_name, filename),
              'Content-Type: %s' % content_type,
              '',
              body,
            ]
            for field_name, filename, content_type, body in self.files
            )
        
        # Flatten the list and add closing boundary marker,
        # then return CR+LF separated data
        flattened = list(itertools.chain(*parts))
        flattened.append('--' + self.boundary + '--')
        flattened.append('')
        return '\r\n'.join(flattened)

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
    
    try:
        request = urllib2.Request(url + "/album/check_dupe")
        request.add_header('User-agent', USER_AGENT)
        data = urllib.urlencode(dict(album=album, artist=artist))
        result = urllib2.urlopen(request, data=data).read()
    except:
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
