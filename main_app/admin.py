from django.contrib import admin
from django.utils.html import format_html
# Register your models here
from .models import *
#importar User
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

#ordenar usuario por fecha de creacion
class CustomUserAdmin(UserAdmin):
    # override the default sort column
    ordering = ('-date_joined', )
    # if you want the date they joined or other columns displayed in the list,
    # override list_display too
    list_display = ('username', 'email', 'date_joined', 'last_login', 'is_staff')

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(UserExtra)
class UserExtraAdmin(admin.ModelAdmin):
    list_display = ('user', 'avatar', 'created_at', 'updated_at', 'thirteen_age_coppa_compliant','ban_reason','ban_date', 'ban_admin',)
    list_filter = ('thirteen_age_coppa_compliant',)
    ordering = ['-created_at', '-updated_at']

@admin.register(Genero)
class GeneroAdmin(admin.ModelAdmin):
    list_display = ('id', 'genero', 'slug')
    search_fields = ('genero',)

@admin.register(Tipo)
class TipoAdmin(admin.ModelAdmin):
    list_display = ('id', 'tipo')
    search_fields = ('tipo',)

@admin.register(Anime)
class AnimeAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'tipo', 'idioma', 'temporadas', 'imagen', 'agregado', 'comments_disabled', 'visible', 'estreno', 'prox_episodio', 'estado', 'slug', 'animefenix_slug')
    ordering = ['-agregado']
    list_filter = [
        "comments_disabled",
        "scraping",
        "tipo",
        "agregado",
        "estado",
        "estreno",
        "visible"
    ]
    search_fields = ('nombre','imagen',)

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj=obj, change=change, **kwargs)
        form.base_fields["visible"].help_text = "Desactivar para ocultar el anime"
        form.base_fields["scraping"].help_text = "Si se deberia activar el scraping automatico para este anime"
        form.base_fields["comments_disabled"].help_text = "Si los comentarios estan desactivados para este anime en la aplicación"
        return form

@admin.register(Anime_Genero)
class AnimeGeneroAdmin(admin.ModelAdmin):
    list_display = ('anime', 'genero_nombre')
    search_fields = ('anime',)
    raw_id_fields = ('anime','categoria',)

@admin.register(Episodio)
class EpisodioAdmin(admin.ModelAdmin):
    list_display = ('id', 'anime', 'fecha', 'visible', 'ep_nombre','temporada', 'numero', 'slug')
    ordering = ['-fecha']
    list_filter = ['visible']
    search_fields = ('slug',)
    raw_id_fields = ('anime',)

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj=obj, change=change, **kwargs)
        form.base_fields["visible"].help_text = "Desactivar para ocultar el episodio"
        return form

@admin.register(Embed)
class EmbedAdmin(admin.ModelAdmin):
    list_display = ('embed', 'url', 'episodio')
    ordering = ['-id']
    search_fields = ('url',)
    raw_id_fields = ('episodio',)

@admin.register(Estado)
class EstadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'estado')
    search_fields = ('estado',)

# @admin.register(EmailActualizacion)
# class EmailActualizacionAdmin(admin.ModelAdmin):
#     list_display = ('email', 'asunto', 'fecha', 'numero')
#     ordering = ['-fecha']
#     search_fields = ('email','asunto','fecha',)

# @admin.register(EmailInicioServer)
# class EmailInicioServerAdmin(admin.ModelAdmin):
#     list_display = ('email', 'asunto', 'fecha', 'numero')
#     ordering = ['-fecha']
#     search_fields = ('email','asunto','fecha',)

@admin.register(EmbedsPendiente)
class EmbedsPendienteAdmin(admin.ModelAdmin):
    list_display = ('episodio', 'url', 'fecha', 'intentos')
    ordering = ['-fecha']
    search_fields = ('url',)
    raw_id_fields = ('episodio',)

@admin.register(EpisodiosVisto)
class EpisodiosVistoAdmin(admin.ModelAdmin):
    list_display = ('usuario_email', 'fecha', 'episodio_nombre')
    ordering = ['-fecha']
    search_fields = ('episodio',)
    raw_id_fields = ('episodio',)

@admin.register(AnimesFavorito)
class AnimesFavoritoAdmin(admin.ModelAdmin):
    list_display = ('usuario_email', 'fecha', 'anime_nombre')
    ordering = ['-fecha']
    search_fields = ('anime',)
    raw_id_fields = ('anime',)

@admin.register(Idioma)
class IdiomaAdmin(admin.ModelAdmin):
    list_display = ('idioma', 'thumbnail', 'slug')
    ordering = ['-id']
    search_fields = ('idioma',)

# Sistema de comentarios
@admin.register(ReportKind)
class ReportKindAdmin(admin.ModelAdmin):
    list_display = ('id', 'kind')
    ordering = ['-id']
    search_fields = ('kind',)

@admin.register(AnimeComment)
class AnimeCommentAdmin(admin.ModelAdmin):
    list_display = ('id','anime', 'user', 'comment', 'spoiler', 'notifications', 'created_at', 'updated_at')
    ordering = ['-created_at']
    list_filter = [
        "spoiler",
    ]
    search_fields = ('comment',)
    raw_id_fields = ('anime','user',)

@admin.register(AnimeCommentReport)
class AnimeCommentReportAdmin(admin.ModelAdmin):
    list_display = ('id','comment', 'user', 'kind', 'created_at')
    ordering = ['-created_at']
    search_fields = ('comment','user',)
    raw_id_fields = ('comment','user',)

@admin.register(AnimeCommentsReply)
class AnimeCommentsReplyAdmin(admin.ModelAdmin):
    list_display = ('id','comment', 'user', 'reply', 'created_at')
    ordering = ['-created_at']
    search_fields = ('reply',)
    raw_id_fields = ('comment','user',)

@admin.register(EpisodeComment)
class EpisodeCommentsAdmin(admin.ModelAdmin):
    list_display = ('id','episode', 'user', 'comment', 'spoiler', 'notifications', 'created_at', 'updated_at')
    ordering = ['-created_at']
    list_filter = [
        "spoiler",
    ]
    search_fields = ('comment',)
    raw_id_fields = ('episode','user',)

@admin.register(EpisodeCommentReport)
class EpisodeCommentReportAdmin(admin.ModelAdmin):
    list_display = ('id','comment', 'user', 'kind', 'created_at')
    ordering = ['-created_at']
    search_fields = ('comment','user',)
    raw_id_fields = ('comment','user',)

@admin.register(EpisodeCommentsReply)
class EpisodeCommentsReplyAdmin(admin.ModelAdmin):
    list_display = ('id','comment', 'user', 'created_at', 'reply')
    ordering = ['-created_at']
    search_fields = ('comment','user',)
    raw_id_fields = ('comment','user',)

@admin.register(AnimeReplyReport)
class AnimeReplyReportAdmin(admin.ModelAdmin):
    list_display = ('id','reply', 'user', 'kind', 'created_at')
    ordering = ['-created_at']
    search_fields = ('reply','user',)
    raw_id_fields = ('reply','user',)

@admin.register(EpisodeReplyReport)
class EpisodeReplyReportAdmin(admin.ModelAdmin):
    list_display = ('id','reply', 'user', 'kind', 'created_at')
    ordering = ['-created_at']
    search_fields = ('reply','user',)
    raw_id_fields = ('reply','user',)

@admin.register(UserReport)
class UserReportAdmin(admin.ModelAdmin):
    list_display = ('id','reported_user', 'reporter_user', 'reason', 'created_at', 'updated_at')
    ordering = ['-created_at']
    search_fields = ('reported_user','reporter_user',)
    raw_id_fields = ('reported_user','reporter_user',)

@admin.register(UserBlock)
class UserBlockAdmin(admin.ModelAdmin):
    list_display = ('id','user', 'blocked_user', 'created_at', 'updated_at')
    ordering = ['-created_at']
    search_fields = ('user','blocked_user',)
    raw_id_fields = ('user','blocked_user',)

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('id','headline', 'slug', 'created_at', 'updated_at')
    ordering = ['-created_at']
    search_fields = ('headline','slug',)

@admin.register(SeenEpisodeTime)
class SeenEpisodeTimeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'episode', 'seconds', 'total_seconds', 'created_at', 'updated_at')
    ordering = ['-created_at']
