from annoying.decorators import render_to

@render_to('home.html')
def home(request): 
    return locals()

@render_to('script_instructions.html')
def script(request):
    return locals()


def script_download(request):
    return locals()
