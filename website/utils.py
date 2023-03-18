from hashids import Hashids
from django.conf import settings

hashids = Hashids(settings.HASHID_FIELD_SALT, min_length=8)
import requests
import bs4
from django.utils.text import slugify


def h_encode(id):
    return hashids.encode(id)


def h_decode(h):
    z = hashids.decode(h)
    if z:
        return z[0]


class HashIdConverter:
    regex = "[a-zA-Z0-9]{8,}"

    def to_python(self, value):
        return h_decode(value)

    def to_url(self, value):
        return h_encode(value)


def get_website_title(external_sites_url):
    try:
        r = requests.get("http://" + external_sites_url)
        html = bs4.BeautifulSoup(r.text)
        return html.title
    except Exception as e:
        return str(e)
