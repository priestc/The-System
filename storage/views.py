from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from album.models import Album

from models import *
from forms import *
from annoying.decorators import render_to

@render_to('new_edit.html')
def new_s3(request, name=None):
    
    if request.POST:
        form = S3BucketForm(request.POST)
        form.full_clean()
        
        if form.is_valid():
            form.save()
    else:
        form = S3BucketForm()
        
    return locals()

def view_collection(request):
    pass

@render_to('list_storages.html')
def list_storage(request):
    stores = GenericStorage.objects.all()
    return locals()

@csrf_exempt
def handle_upload(request):

    meta = request.POST.get('meta', None)
    album = request.POST.get('album', None)
    artist = request.POST.get('artist', None)
    
    f = request.FILES['file']

    size = f.size / 1073741824.0
    disp_size = "{0:.3} GB".format(size)
  
    print artist, album, meta, size
    
    obj = Album(artist=artist, album=album, meta=meta, size=size)
    obj.save()
    
    return HttpResponse(disp_size + ' recieved from client!!!', mimetype='text/plain')
