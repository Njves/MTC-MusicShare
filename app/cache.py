from app import cache

def cache_html(html):
    if cache_html := cache.get('html'):
        return cache_html
    cache.set('html', html)
    return html

def cache_rooms(rooms):
    if rooms_cache := cache.get('rooms'):
        return rooms_cache
    cache.set('rooms', rooms)
    return rooms