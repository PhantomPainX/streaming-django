from django.db import models
from django.urls import reverse
from slugify import slugify
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.utils.translation import gettext_lazy as _
from main_app.webp import WEBPField

from allauth.account.signals import user_signed_up
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import get_template
from django.core.mail import send_mail
from threading import Thread

import uuid

from imagekit.models import ImageSpecField
from imagekit.processors import Thumbnail

# Create your models here.

def user_avatar(instance, filename):
    #Revisar cantidad de archivos en la carpeta portadas
    from django.conf import settings
    import os

    nombre = uuid.uuid4().hex
    while os.path.exists(os.path.join(settings.MEDIA_ROOT, 'users/avatars/{}.webp'.format(nombre))):
        nombre = uuid.uuid4().hex

    filename = "users/avatars/{}.webp".format(nombre)
    return filename

class UserExtra(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = WEBPField(
        verbose_name=_('Image'),
        upload_to=user_avatar,
        default='users/avatars/default.webp',
    )
    thirteen_age_coppa_compliant = models.BooleanField(default=False)
    ban_reason = models.TextField(null=True)
    ban_date = models.DateTimeField(null=True)
    ban_admin = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='ban_admin')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name_plural = "User Extra"
        ordering = ["id"]

class Genero(models.Model):
    genero = models.CharField(max_length=128, unique=True)
    slug = models.SlugField(max_length=128, unique=True)

    def save(self, *args, **kwargs):
        if not self.id:
            # Newly created object, so set slug
            self.slug = slugify(self.genero)

        super(Genero, self).save(*args, **kwargs)

    def __str__(self):
        return self.genero
    
    class Meta:
        verbose_name_plural = "Generos"
        ordering = ["id"]

class Tipo(models.Model):
    tipo = models.CharField(max_length=128, unique=True)
    slug = models.SlugField(max_length=128, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.id:
            # Newly created object, so set slug
            self.slug = slugify(self.tipo)

        super(Tipo, self).save(*args, **kwargs)

    def __str__(self):
        return self.tipo

    class Meta:
        verbose_name_plural = "Tipos"
        ordering = ["id"]

class Estado(models.Model):
    estado = models.CharField(max_length=128, unique=True)
    slug = models.SlugField(max_length=128, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.id:
            # Newly created object, so set slug
            self.slug = slugify(self.estado)

        super(Estado, self).save(*args, **kwargs)

    def __str__(self):
        return self.estado

    class Meta:
        verbose_name_plural = "Estados de Transmision"
        ordering = ["id"]

class Idioma(models.Model):
    idioma = models.CharField(max_length=32)
    thumbnail = models.ImageField(upload_to='icons/banderas', null=True, blank=True)
    slug = models.SlugField(max_length=32, unique=True, null=True, blank=True)

    def __str__(self):
        return self.idioma

    class Meta:
        verbose_name_plural = "Idiomas"
        ordering = ["id"]

def imagen_webp(instance, filename):
    #Revisar cantidad de archivos en la carpeta portadas
    from django.conf import settings
    import os
    import glob
    cant_archivos = len(glob.glob(os.path.join(settings.MEDIA_ROOT, 'portadas/*')))
    #cambiar el nombre de la imagen
    nombre = str(cant_archivos+1)
    filename = "portadas/{}.webp".format(nombre)
    return filename

from main_app.discord.webhooks import DsWebhook, RegistrationSources

class Anime(models.Model):
    nombre = models.CharField(max_length=128)
    tipo = models.ForeignKey(Tipo, null=True, blank=True, on_delete=models.SET_NULL)
    idioma = models.ForeignKey(Idioma, null=True, blank=True, default=1, on_delete=models.SET_NULL)
    imagen = WEBPField(
        verbose_name=_('Image'),
        upload_to=imagen_webp,
        default='portadas/default.webp',
    )
    image_thumbnail = ImageSpecField(source='imagen', processors=[Thumbnail(93)], format='WEBP', options={'quality': 1})
    comments_disabled = models.BooleanField(default=False)
    agregado = models.DateTimeField(auto_now_add=True)
    temporadas = models.IntegerField(default=0)
    prox_episodio = models.CharField(max_length=128, null=True, blank=True)
    generos = models.ManyToManyField(Genero, through='Anime_Genero')
    estreno = models.IntegerField()
    scraping = models.BooleanField(default=True)
    sinopsis = models.TextField()
    estado = models.ForeignKey(Estado, null=True, blank=True, on_delete=models.SET_NULL)
    animefenix_slug = models.SlugField(max_length=128, null=True, blank=True)
    slug = models.SlugField(max_length=128, unique=True)
    visible = models.BooleanField(default=True)

    def get(self):
        #si el anime no esta visible, no se puede acceder a el
        if not self.visible:
            return None
        else:
            return self

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        # if idioma is Japanese then return Japanese url
        if self.idioma.idioma == 'Japonés':
            return reverse('anime', args=[self.slug])
        elif self.idioma.idioma == 'Latino':
            return reverse('latino', args=[self.slug])

    # def get_latino_url(self):
    #     return reverse('latino', args=[self.slug])

    # def image_to_webp(self):
    #     imagen = self.imagen
    #     self.imagen = imagen.with_suffix(".webp")
    #     super(Anime, self).save()

    class Meta:
        verbose_name_plural = "Animes"
        ordering = ["id"]

class Anime_Genero(models.Model):
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE)
    categoria = models.ForeignKey(Genero, on_delete=models.CASCADE)

    def __str__(self):
        return self.anime.nombre + " - " + self.categoria.genero

    def genero_nombre(self):
        return self.categoria.genero

    class Meta:
        verbose_name_plural = "Generos de Animes"
        ordering = ["id"]

class Episodio(models.Model):
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    temporada = models.IntegerField(default=0)
    ep_nombre = models.CharField(max_length=128, null=True, blank=True)
    numero = models.IntegerField()
    slug = models.SlugField(max_length=128, unique=True, null=True, blank=True)
    visible = models.BooleanField(default=True)

    def __str__(self):
        return self.anime.nombre + " - Episodio " + str(self.numero)

    def get_absolute_url(self):
        return reverse('ver', args=[self.slug])

    def get_next_episode(self):
        try:
            #check if next episode exists
            next_episode = Episodio.objects.get(numero=self.numero+1, anime=self.anime)
            if next_episode:
                return next_episode
            else:
                return None
        except:
            return None

    class Meta:
        verbose_name_plural = "Episodios"
        ordering = ["id"]

    
class Embed(models.Model):
    embed = models.CharField(max_length=32)
    url = models.URLField()
    episodio = models.ForeignKey(Episodio, on_delete=models.CASCADE)

    def __str__(self):
        return self.url

    class Meta:
        verbose_name_plural = "Fuentes de Video"
        ordering = ["id"]

class EmailActualizacion(models.Model):
    email = models.EmailField(max_length=128)
    fecha = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    asunto = models.CharField(max_length=128, null=True, blank=True)
    numero = models.IntegerField()

    def __str__(self):
        return self.email

    class Meta:
        ordering = ["id"]

class EmailInicioServer(models.Model):
    email = models.EmailField(max_length=128)
    fecha = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    asunto = models.CharField(max_length=128, null=True, blank=True)
    numero = models.IntegerField()

    def __str__(self):
        return self.email

    class Meta:
        ordering = ["id"]


class EmbedsPendiente(models.Model):
    
    episodio = models.ForeignKey(Episodio, on_delete=models.CASCADE)
    url = models.URLField()
    fecha = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    intentos = models.IntegerField(default=0)

    def __str__(self):
        return self.url

    class Meta:
        verbose_name_plural = "Fuentes de video pendientes"
        ordering = ["id"]

class EpisodiosVisto(models.Model):
    episodio = models.ForeignKey(Episodio, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.episodio.anime.nombre + " Episodio " + str(self.episodio.numero) + " - " + self.usuario.email

    def usuario_email(self):
        return self.usuario.email
    def episodio_nombre(self):
        return self.episodio.anime.nombre + " Episodio " + str(self.episodio.numero)

    class Meta:
        verbose_name_plural = "Episodios Vistos de Usuarios"
        ordering = ["id"]

class AnimesFavorito(models.Model):
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.anime.nombre + " - " + self.usuario.email

    def usuario_email(self):
        return self.usuario.email

    def anime_nombre(self):
        return self.anime.nombre

    class Meta:
        verbose_name_plural = "Favoritos de Usuarios"
        ordering = ["id"]

# Sistema de comentarios

class ReportKind(models.Model):
    kind = models.CharField(max_length=128)
    sensitive = models.BooleanField(default=False)

    def __str__(self):
        return self.kind

    class Meta:
        verbose_name_plural = "Tipos de Reportes"
        ordering = ["id"]


class AnimeComment(models.Model):
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    spoiler = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notifications = models.BooleanField(default=False)
    comment = models.TextField()

    def __str__(self):
        return self.anime.nombre + " - " + self.user.email

    def usuario_email(self):
        return self.user.email

    def anime_nombre(self):
        return self.anime.nombre

    class Meta:
        verbose_name_plural = "Comentarios de Animes"
        ordering = ["id"]

class AnimeCommentReport(models.Model):
    comment = models.ForeignKey(AnimeComment, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    kind = models.ForeignKey(ReportKind, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.comment.anime.nombre + " - " + self.user.email

    def usuario_email(self):
        return self.user.email

    def anime_nombre(self):
        return self.comment.anime.nombre

    class Meta:
        verbose_name_plural = "Reportes de Comentarios de Animes"
        ordering = ["id"]

class AnimeCommentsReply(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(AnimeComment, on_delete=models.CASCADE)
    spoiler = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reply = models.TextField()

    def __str__(self):
        return self.comment.anime.nombre + " - " + self.user.email

    def usuario_email(self):
        return self.user.email

    class Meta:
        verbose_name_plural = "Respuestas de Comentarios de Animes"
        ordering = ["id"]

class AnimeReplyReport(models.Model):
    reply = models.ForeignKey(AnimeCommentsReply, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    kind = models.ForeignKey(ReportKind, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.reply.comment.anime.nombre + " - " + self.user.email

    def usuario_email(self):
        return self.user.email

    def anime_nombre(self):
        return self.reply.comment.episode.anime.nombre

    class Meta:
        verbose_name_plural = "Reportes de Respuestas de Comentarios de Animes"
        ordering = ["id"]

class EpisodeComment(models.Model):
    episode = models.ForeignKey(Episodio, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    spoiler = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notifications = models.BooleanField(default=False)
    comment = models.TextField()

    def __str__(self):
        return self.episode.anime.nombre + " - " + self.user.email

    def usuario_email(self):
        return self.user.email

    def anime_nombre(self):
        return self.episode.anime.nombre

    class Meta:
        verbose_name_plural = "Comentarios de Episodios"
        ordering = ["id"]

class EpisodeCommentReport(models.Model):
    comment = models.ForeignKey(EpisodeComment, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    kind = models.ForeignKey(ReportKind, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.comment.episode.anime.nombre + " - " + self.user.email

    def usuario_email(self):
        return self.user.email

    def anime_nombre(self):
        return self.comment.episode.anime.nombre

    class Meta:
        verbose_name_plural = "Reportes de Comentarios de Episodios"
        ordering = ["id"]

class EpisodeCommentsReply(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(EpisodeComment, on_delete=models.CASCADE)
    spoiler = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reply = models.TextField()

    def __str__(self):
        return self.comment.episode.anime.nombre + " - " + self.user.email

    def usuario_email(self):
        return self.user.email

    def anime_nombre(self):
        return self.comment.episode.anime.nombre

    class Meta:
        verbose_name_plural = "Respuestas de Comentarios de Episodios"
        ordering = ["id"]

class EpisodeReplyReport(models.Model):
    reply = models.ForeignKey(EpisodeCommentsReply, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    kind = models.ForeignKey(ReportKind, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.reply.comment.episode.anime.nombre + " - " + self.user.email

    def usuario_email(self):
        return self.user.email

    def anime_nombre(self):
        return self.reply.comment.episode.anime.nombre

    class Meta:
        verbose_name_plural = "Reportes de Respuestas a Comentarios de Episodios"
        ordering = ["id"]

class UserReport(models.Model):
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE)
    reporter_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reporter_user', default=1)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email

    def usuario_email(self):
        return self.user.email

    class Meta:
        verbose_name_plural = "Reportes de Usuarios"
        ordering = ["id"]

class UserBlock(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    blocked_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_user')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email

    def usuario_email(self):
        return self.user.email

    class Meta:
        verbose_name_plural = "Bloqueos de Usuarios"
        ordering = ["id"]

class SeenEpisodeTime(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    episode = models.ForeignKey(Episodio, on_delete=models.CASCADE)
    seconds = models.FloatField(default=0)
    total_seconds = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email + " - " + self.episode.anime.nombre + " - " + str(self.episode.numero) + " - " + str(self.seconds)
    
    class Meta:
        verbose_name_plural = "Tiempo visto de episodios"
        ordering = ["id"]


class Article(models.Model):
    headline = models.CharField(max_length=256)
    sub_headline = models.CharField(max_length=256, null=True, blank=True)
    slug = models.SlugField(max_length=256, unique=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    affiliate_author = models.CharField(max_length=128, null=True, blank=True)
    content = models.TextField()
    views = models.IntegerField(default=0)
    reading_time = models.CharField(max_length=128, null=True, blank=True)
    image = models.ImageField(upload_to='articles', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published = models.BooleanField(default=False)

    def __str__(self):
        return self.headline

    def get_absolute_url(self):
        return reverse('blog', kwargs={'slug': self.slug})
    
    def get_absolute_image_url(self):
        #get current domain name
        domain = Site.objects.get_current().domain
        return "http://{}{}".format(domain, self.image.url)


from .emails import emails_admin

def send_email_admin(username, email, user):
    from django.conf import settings
    asunto = 'Bienvenido {}'.format(username)
    template = get_template('email_templates/registracion_exitosa.html')
    content = template.render({'username': username})
    emails = [email]

    send_mail(
        asunto,
        content,
        recipient_list=emails,
        from_email='127.0.0.1 <{}>'.format(settings.EMAIL_HOST_USER),
        html_message=content,
        fail_silently=False
    )

    # ds = DsWebhook("")
    # ds.send_new_user(user, RegistrationSources.WEB)
    
    return

@receiver(user_signed_up, dispatch_uid="some.unique.string.id.for.allauth.user_signed_up")
def user_signed_up_(request, user, **kwargs):
    
    username = user.username
    email = user.email

    t = Thread(target=send_email_admin, args=(username, email, user))
    t.start()

@receiver(post_save, sender=Anime)
def anime_post_save(sender, instance, created, **kwargs):
    if created:
        anime = instance
        # ds = DsWebhook("")
        # ds.send_new_anime(anime)

@receiver(post_save, sender=Episodio)
def episodio_post_save(sender, instance, created, **kwargs):
    if created:
        episodio = instance
        # ds = DsWebhook("")
        # ds.send_new_episode(episodio)