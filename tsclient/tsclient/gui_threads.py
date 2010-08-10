import datetime
import threading
import wx

from tsclient.core import *

EVT_UPLOAD_DONE_ID = wx.NewId()
def EVT_UPLOAD_DONE(win, func):
    """
    An Event that adds stuff to the status window
    """
    
    win.Connect(-1, -1, EVT_UPLOAD_DONE_ID, func)

class UploadDoneEvent(wx.PyEvent):
    """
    Simple event to carry the status window message back to the frame.
    """
    
    def __init__(self, msg, color='black'):
        wx.PyEvent.__init__(self)
        self.msg = msg
        self.color = color
        self.SetEventType(EVT_UPLOAD_DONE_ID)

######

EVT_STATUS_ID = wx.NewId()
def EVT_STATUS(win, func):
    """
    An Event that adds stuff to the status window
    """
    
    win.Connect(-1, -1, EVT_STATUS_ID, func)

class StatusEvent(wx.PyEvent):
    """
    Simple event to carry the status window message back to the frame.
    """
    
    def __init__(self, msg, color='black'):
        wx.PyEvent.__init__(self)
        self.msg = msg
        self.color = color
        self.SetEventType(EVT_STATUS_ID)

##################
##################
     
class UploadThread(threading.Thread):
    """
    A thread that does all the uploading. This is done in a seperate thread
    because otherwise it will make the UI unresponsive.
    """
    
    def __init__(self, frame, data, tmp, url):
        self.frame = frame
        self.data = data
        self.url = url
        self.tmp = tmp
        self.upload_size = tmp.tell()
        
        self.artist = self.data['artist']
        self.album = self.data['album']
        self.password = self.data['password']
        
        super(UploadThread, self).__init__()
    
    def run(self):
        """
        Send the upload to the server, and return how long the upload took
        and the average transfer speed.
        """
        
        result = self.verify()
            
        if result is not True:
            # wrong password or a dupe or an old client version, do not proceed
            wx.PostEvent(self.frame, UploadDoneEvent(result, 'red'))
            return
        
        before = datetime.datetime.now()
        result = send_request(self.tmp, self.data, self.url, interface="GUI")
        after = datetime.datetime.now()
        
        duration = after - before
        secs = duration.seconds + (duration.microseconds / 100000.0)
        kb = (self.upload_size/1024.0) / secs
        speed = "{0:.2f} KB/sec".format(kb)
        
        msg = "Finished upload of: %s - %s" % (self.artist, self.album) + \
              " -- Duration: %s, Avg Speed: %s" % (duration, speed)

        wx.PostEvent(self.frame, UploadDoneEvent(msg, 'green'))

    
    def verify(self):
        """
        Verify that the password and crap are correct before sending the huge
        request
        """
        
        vf = VerifyClient(artist=self.artist, album=self.album,
                          url=self.url, password=self.password)
        
        vf.make_request()
            
        if vf.is_password_match() is False:
            return "Wrong Password"
            
        
        if not vf.is_allowed_client():
            return "Client rejected, upgrade plz."
            
        
        if not vf.is_latest_client():
            msg = "This is not the latest version of this uploader, " + \
                  "the latest vesion is: %s" % vf.get_latest_client_version()
            wx.PostEvent(self.frame, StatusEvent(msg, 'blue'))
             
        if vf.is_dupe() is True:
            msg = "Album already exists in The System. This is a dupe"
            return msg
        
        msg = "Password correct, album not a dupe, and your client appears to be fairly up-to-date"
        wx.PostEvent(self.frame, StatusEvent(msg, 'green'))
        return True















