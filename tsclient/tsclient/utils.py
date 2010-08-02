import re
from colorama import Fore, Back, Style

def bright_green(text):
    return "{color}{style}{text}{reset}"\
                .format(color=Fore.GREEN, style=Style.BRIGHT,
                        text=text, reset=Style.RESET_ALL)

def bright_red(text):
    return "{color}{style}{text}{reset}"\
                .format(color=Fore.RED, style=Style.BRIGHT,
                        text=text, reset=Style.RESET_ALL)

def blue(text):
    return "{color}{text}{reset}"\
                .format(color=Fore.BLUE, text=text, reset=Fore.RESET)

def clean(value):
    """
    Strip out characters that are not allowed in files in some OS's
    """

    return re.sub(r'[*|\/:"<>?]', '', str(value)).encode('ascii','replace')

def is_image(filepath):
    """
    Determine if the file is a proper image file
    """
    
    try:
        import Image
        im = Image.open(filepath)
    except (IOError, ImportError):
        # PIL can't open file, it's not an image
        return False
    else:
        # it's a proper image file!
        return True
