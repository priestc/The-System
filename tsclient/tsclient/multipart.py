import itertools
import mimetools
import mimetypes
from cStringIO import StringIO
import urllib
import urllib2

USER_AGENT = 'The Project Command Line Client v0.1'

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

def send_request(tmpzip, data, url, silent=False):
    
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
    
    if not silent: print tmpzip.tell(), "bytes being sent to server..."
    try:
        print urllib2.urlopen(request).read()
    except Exception, e:
        print e.read()

def check_dupe(artist, album, url):
    data = urllib.urlencode(dict(album=album, artist=artist))
    return urllib2.urlopen(url + "/album/check_dupe", data=data).read()




