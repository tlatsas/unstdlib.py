import os.path
import hashlib
import time

from unstdlib.standard.functools_ import memoized
from unstdlib.standard.list_ import iterate_items


__all__ = [
    'get_cache_buster', 'html_tag', 'html_javascript_link', 'html_stylesheet_link',
]


@memoized
def _cache_key_by_md5(src_path, chunk_size=65536):
    hash = hashlib.md5()
    with open(src_path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), ''):
            hash.update(chunk)
    return hash.hexdigest()


@memoized
def _cache_key_by_mtime(src_path):
    return str(int(os.path.getmtime(src_path)))


_IMPORT_TIME = str(int(time.time()))

_BUST_METHODS = {
    'mtime': _cache_key_by_mtime,
    'md5': _cache_key_by_md5,
    'importtime': lambda src_path: _IMPORT_TIME,
}


def get_cache_buster(src_path, method='importtime'):
    """ Return a string that can be used as a parameter for cache-busting URLs
    for this asset.

    :param src_path:
        Filesystem path to the file we're generating a cache-busting value for.

    :param method:
        Method for cache-busting. Supported values: importtime, mtime, md5
        The default is 'importtime', because it requires the least processing.

    Note that the mtime and md5 cache busting methods' results are cached on
    the src_path.

    Example::

        >>> SRC_PATH = os.path.join(os.path.dirname(__file__), 'html.py')
        >>> get_cache_buster(SRC_PATH) is _IMPORT_TIME
        True
        >>> get_cache_buster(SRC_PATH, method='mtime') == _cache_key_by_mtime(SRC_PATH)
        True
        >>> get_cache_buster(SRC_PATH, method='md5') == _cache_key_by_md5(SRC_PATH)
        True
    """
    try:
        fn = _BUST_METHODS[method]
    except KeyError:
        raise KeyError('Unsupported busting method value: %s' % method)

    return fn(src_path)


def _generate_dom_attrs(attrs, allow_no_value=True):
    """ Yield compiled DOM attribute key-value strings.

    If the value is `True`, then it is treated as no-value."""
    for attr in iterate_items(attrs):
        if isinstance(attr, basestring):
            attr = (attr, True)
        key, value = attr
        if value is True and not allow_no_value:
            value = key  # E.g. <option checked="true" />
        if value is True:
            yield True  # E.g. <option checked />
        else:
            yield '%s="%s"' % (key, value.replace('"', '\\"'))


def html_tag(tagname, content='', attrs=None):
    """ Helper for programmatically building HTML tags.

    Note that this barely does any escaping, and will happily spit out
    dangerous user input if used as such.

    :param tagname:
        Tag name of the DOM element we want to return.

    :param content:
        Optional content of the DOM element. If `None`, then the element is
        self-closed. By default, the content is an empty string.

    :param attrs:
        Optional dictionary-like collection of attributes for the DOM element.

    Example::

        >>> html_tag('div', content='Hello, world.')
        '<div>Hello, world.</div>'
        >>> html_tag('script', attrs={'src': '/static/js/core.js'})
        '<script src="/static/js/core.js"></script>'
        >>> html_tag('script', attrs=[('src', '/static/js/core.js'), ('type', 'text/javascript')])
        '<script src="/static/js/core.js" type="text/javascript"></script>'
        >>> html_tag('meta', content=None, attrs=dict(content='"quotedquotes"'))
        '<meta content="\\\\"quotedquotes\\\\"" />'
    """
    attrs_str = attrs and ' '.join(_generate_dom_attrs(attrs))
    open_tag = tagname
    if attrs_str:
        open_tag += ' ' + attrs_str
    if content or isinstance(content, basestring):
        return '<%s>%s</%s>' % (open_tag, content, tagname)
    return '<%s />' % open_tag


def html_javascript_link(src_url, src_path=None, cache_bust=None, content='', extra_attrs=None):
    """ Helper for programmatically building HTML JavaScript source include
    links, with optional cache busting.

    :param src_url:
        Goes into the `src` attribute of the `<script src="...">` tag.

    :param src_path:
        Optional filesystem path to the source file, used when `cache_bust` is
        enabled.

    :param content:
        Optional content of the DOM element. If `None`, then the element is
        self-closed.

    :param cache_bust:
        Optional method to use for cache busting. Can be one of: importtime,
        md5, or mtime. If the value is md5 or mtime, then `src_path` must be
        supplied.


    Example::

        >>> html_javascript_link('/static/js/core.js')
        '<script src="/static/js/core.js" type="text/javascript"></script>'
    """
    if cache_bust:
        append_suffix = get_cache_buster(src_path=src_path, method=cache_bust)
        delim = '&' if '?' in src_url else '?'
        src_url += delim + append_suffix

    attrs = {
        'src': src_url,
        'type': 'text/javascript',
    }
    if extra_attrs:
        attrs.update(extra_attrs)

    return html_tag('script', content=content, attrs=attrs)


def html_stylesheet_link(src_url, src_path=None, cache_bust=None, content='', extra_attrs=None):
    """ Helper for programmatically building HTML StyleSheet source include
    links, with optional cache busting.

    :param src_url:
        Goes into the `src` attribute of the `<link src="...">` tag.

    :param src_path:
        Optional filesystem path to the source file, used when `cache_bust` is
        enabled.

    :param content:
        Optional content of the DOM element. If `None`, then the element is
        self-closed.

    :param cache_bust:
        Optional method to use for cache busting. Can be one of: importtime,
        md5, or mtime. If the value is md5 or mtime, then `src_path` must be
        supplied.


    Example::

        >>> html_stylesheet_link('/static/css/media.css')
        '<link href="/static/css/media.css" rel="stylesheet"></link>'
    """
    if cache_bust:
        append_suffix = get_cache_buster(src_path=src_path, method=cache_bust)
        delim = '&' if '?' in src_url else '?'
        src_url += delim + append_suffix

    attrs = {
        'href': src_url,
        'rel': 'stylesheet',
    }
    if extra_attrs:
        attrs.update(extra_attrs)

    return html_tag('link', content=content, attrs=attrs)


if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)