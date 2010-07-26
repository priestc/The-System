from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

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

@csrf_exempt
def handle_upload(request):
    if request.POST:
        print "POST!!"

    print request.POST
    print request.FILES
    
    return HttpResponse('response from server!!!', mimetype='text/plain')