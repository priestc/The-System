from django import template
register = template.Library()

def s3_dl(storage, album):
    """
    Make a link to the album on the S3 storage location if there is
    enough bandwidth. Returns an entire <a> tag.
    """
    
    storage = storage.get_real_storage()
    
    if storage.can_handle(bandwidth=album.size):
        key = storage.get_key(album.filename)
    else:
        return '{name} - out of bandwidth'.format(name=storage.name)
    
    if key:
        url = key.generate_url(60)
        return '<a href="{url}">{name}</a>'.format(name=storage.name, url=url)
    else:
        return '{name} - ERROR: COULD NOT MAKE LINK'.format(name=storage.name)

register.simple_tag(s3_dl)
