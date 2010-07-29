from models import Album
from annoying.decorators import render_to

@render_to('list_albums.html')
def view_albums(request):
    albums = Album.objects.order_by('artist', 'date', 'album')
    return locals()

@render_to('download_album.html')
def download_album(request, pk):
    album = Album.objects.get(pk=pk)
    return locals()
