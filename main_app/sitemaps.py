from django.urls import reverse
from django.contrib.sitemaps import Sitemap
from main_app.models import Anime, Episodio
from django.db.models.query_utils import Q

class LatinoSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.5

    def items(self):
        return Anime.objects.filter(idioma__idioma="Latino").exclude(visible=False).order_by('-agregado')
    def location(self, item):
        return reverse('latino', kwargs={'slug': item.slug})


class AnimeSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.5

    def items(self):
        return Anime.objects.filter(Q(tipo__tipo='TV') | Q(tipo__tipo='OVA') | Q(tipo__tipo='Película') | Q(tipo__tipo='Especial')).exclude(visible=False).order_by('-agregado')

class EpisodioSitemap(Sitemap):

    changefreq = "monthly"
    priority = 0.3
    limit = 40000

    def items(self):
        return Episodio.objects.all().exclude(visible=False).exclude(anime__visible=False).order_by('-fecha')[:self.limit]
    
class StaticViewSitemap(Sitemap):
    priority = 0.9
    changefreq = 'hourly'

    def items(self):
        return ['home', 'directorio', 'contacto']

    def location(self, item):
        return reverse(item)
