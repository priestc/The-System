from annoying.decorators import render_to
from django.contrib.auth.decorators import login_required

@login_required
@render_to('home.html')
def home(request): 
    return locals()

@login_required
@render_to('script_instructions.html')
def script(request):
    return locals()

@login_required
def script_download(request):
    return locals()
