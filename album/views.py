from models import Album
from annoying.decorators import render_to
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

@render_to('list_albums.html')
def view_albums(request):
    albums = Album.objects.order_by('artist', 'date', 'album')
    return locals()

@render_to('download_album.html')
def download_album(request, pk):
    album = Album.objects.get(pk=pk)
    return locals()
    
@csrf_exempt
def check_dupe(request):
    """
    Check to see that the artist/album that is about to be uploaded by the
    client is not already in the system. Also, alert the user if he/she is
    using an old/too old version of the client.
    """
    
    artist = request.POST['artist']
    album = request.POST['album']
    client_ver = float(request.META['HTTP_USER_AGENT'].split(' v')[1])
    
    if client_ver < settings.MIN_CLIENT_VERSION:
        return HttpResponse("Too Old Client", mimetype="text/plain")
    
    ver = ""
    if client_ver < settings.CURRENT_CLIENT_VERSION:
        ver = " %s" % settings.CURRENT_CLIENT_VERSION
    
    if Album.objects.filter(album__iexact=album, artist__iexact=artist).exists():
        return HttpResponse("Yes%s" % ver, mimetype="text/plain")
    else:
        return HttpResponse("No%s" % ver, mimetype="text/plain")
