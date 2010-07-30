from models import Album
from annoying.decorators import render_to
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

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
    
    artist = request.POST['artist']
    album = request.POST['album']
    
    if Album.objects.filter(album__iexact=album, artist__iexact=artist).exists():
        return HttpResponse("Yes", mimetype="text/plain")
    else:
        return HttpResponse("No", mimetype="text/plain")
