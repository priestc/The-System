import os

from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt

from album.models import Album
from models import *
from forms import *
from tasks import upload_to_remote_storage
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

@render_to('list_storages.html')
def list_storage(request):
    stores = GenericStorage.objects.all()
    return locals()

@csrf_exempt
def handle_upload(request):
    """
    All uploads are handled by this view. It takes the file, saves it to the
    local filesystem, then adds the S3 upload to the upload queue.
    """
    
    if not request.META['HTTP_USER_AGENT']\
                .startswith("The Project Command Line Client"):
        raise Http404

    meta = request.POST.get('meta', None)
    album = request.POST.get('album', None)
    artist = request.POST.get('artist', None)
    
    f = request.FILES['file']
    size = f.size / 1073741824.0
    disp_size = "{0:.3} GB".format(size)
    
    album_obj = Album(artist=artist, album=album, meta=meta, size=size)
    album_obj.save()
    
    save_location = os.path.join(settings.UPLOAD_PATH, album_obj.filename)
    destination = open(save_location, 'wb+')
    
    for chunk in f.chunks():
        destination.write(chunk)
    destination.close()
    
    upload_to_remote_storage.delay(album_obj.pk, destination.name)
    
    return HttpResponse(disp_size + ' recieved from client!!!', mimetype='text/plain')
