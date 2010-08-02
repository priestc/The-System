from annoying.decorators import render_to

from django.http import HttpResponse, Http404
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from album.models import Album

@render_to('home.html')
def home(request): 
    return locals()

@render_to('script_instructions.html')
def script(request):
    return locals()

def script_download(request):
    return locals()

@csrf_exempt
def pre_upload(request):
    """
    Before an upload is sent, the client hits this URL to see if:
        1. The file is not a dupe
        2. The user is not using an acient banned client
        3. The password is correct
        4. The latest version of the client is what the user is using
    """
    
    # determine if the album is a dupe
    artist = request.POST['artist']
    album = request.POST['album']
    dupe = Album.objects.filter(album__iexact=album, artist__iexact=artist).exists()
    dupe = "Yes" if dupe else "No"
    
    # determine if the client version is too old to accept
    client_ver = float(request.META['HTTP_USER_AGENT'].split(' v')[1])
    client_reject = (client_ver <= settings.MIN_CLIENT_VERSION)
    client_reject = "Yes" if client_reject else "No"
    
    # get the latest version of the client, if the latest version is
    # the version the user is using, return "Latest"
    latest_client = settings.CURRENT_CLIENT_VERSION
    is_latest_client = (client_ver == latest_client)
    latest_client = "Latest" if is_latest_client else str(latest_client)
    
    # determine if the password is correct
    user_password = request.POST['password']
    password = (user_password == settings.CLIENT_PASS)
    password_match = "Yes" if password else "No"
    
    #######################
    
    st = "{dupe},{client_reject},{latest_client},{password_match}".format(**locals())
    return HttpResponse(st, mimetype="text/plain")
