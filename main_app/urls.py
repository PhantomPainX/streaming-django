from email.mime import base
from django.urls import path, include
from main_app.views import *
from django.conf import settings

from rest_framework import routers
from main_app import api_views

router = routers.DefaultRouter()
router.register(r'users', api_views.UserViewSet)
router.register(r'animes', api_views.AnimeViewSet, basename='animes')
router.register(r'episodes', api_views.EpisodeViewSet, basename='episodios')
router.register(r'fav_animes', api_views.FavAnimeViewSet, basename='fav_animes')
router.register(r'episodios_vistos', api_views.EpisodiosVistoViewSet, basename='episodios_vistos')
router.register(r'anime-comments', api_views.AnimeCommentsViewSet, basename='anime-comments')
router.register(r'episode-comments', api_views.EpisodeCommentsViewSet, basename='episode-comments')
router.register(r'anime-comment-reports', api_views.AnimeCommentReportsViewSet, basename='anime-comment-reports')
router.register(r'anime-comment-replies-reports', api_views.AnimeCommentReplyReportsViewSet, basename='anime-comment-replies-reports')
router.register(r'episode-comment-reports', api_views.EpisodeCommentReportsViewSet, basename='episode-comment-reports')
router.register(r'episode-comment-replies-reports', api_views.EpisodeCommentReplyReportsViewSet, basename='episode-comment-replies-reports')
router.register(r'anime-comments-replies', api_views.AnimeCommentRepliesViewSet, basename='anime-comments-replies')
router.register(r'episode-comments-replies', api_views.EpisodeCommentRepliesViewSet, basename='episode-comments-replies')
router.register(r'report-kinds', api_views.ReportKindsViewSet, basename='report-kinds')
router.register(r'embeds', api_views.EmbedViewSet, basename='embeds')
router.register(r'users-extra', api_views.UserExtraViewSet, basename='users-extra')
router.register(r'gcmdevices', api_views.GCMDeviceViewSet, basename='gcmdevices')
router.register(r'genres', api_views.GenreViewSet, basename='genres')
router.register(r'types', api_views.TypeViewSet, basename='types')
router.register(r'status', api_views.StatusViewSet, basename='status')
router.register(r'languages', api_views.LanguageViewSet, basename='languages')
router.register(r'user-reports', api_views.UserReportViewSet, basename='user-reports')
router.register(r'user-blocks', api_views.UserBlockViewSet, basename='user-blocks')
router.register(r'seen-episode-time', api_views.SeenEpisodeTimeViewSet, basename='seen-episode-time')

urlpatterns = [
    # Urls Principales
    # path('',home, name='home'),
    path('accounts/', include('allauth.urls')),
    # path('anime/<slug:slug>', anime, name='anime'),
    # path('random', random_anime, name='random_anime'),
    # path('latino/<slug:slug>', latino, name='latino'),
    # path('ver/<slug:slug>', episodio, name='ver'),
    # path('episodio/<slug:slug>', episodio_redirect, name='episodio'),
    # path('blog/<slug:slug>', article, name='blog'),
    # path('directorio/', directorio, name='directorio'),
    # path('reporte/', reporte, name='reporte'),
    # path('ultimos-episodios/', ultimos_episodios, name='ultimos-episodios'),
    # path("contacto/", contacto, name="contacto"),
    # path("politica-de-privacidad/", politica_privacidad, name="politica-de-privacidad"),
    # path("condiciones-del-servicio/", condiciones_del_servicio, name="condiciones-del-servicio"),
    # path("iframe/", iframe_proxy, name="iframe-proxy"),
    # path("player/", jwplayer, name="jwplayer"),
    # Sistema de usuarios
    # path('cuenta/registro/', registro, name='registro'),
    # path("cuenta/password_reset/", password_reset_request, name="password_reset"),
    # path("cuenta/misfavoritos", mis_favoritos, name="misfavoritos"),
    # path("cuenta/perfil/", perfil, name="perfil"),
    #Sistema de Animes Favoritos (AJAX)
    path("fav-sis/ver-ep/", ver_episodio, name="ver_episodio"),
    path("fav-sis/revisar-eps/", revisar_episodios, name="revisar_episodios"),
    path("fav-sis/rev-anime-fav/", revisar_anime_favorito, name="revisar_anime_favorito"),
    path("fav-sis/agregar-anime-fav/", agregar_anime_favorito, name="agregar_anime_favorito"),
    path("fav-sis/listar_animes_episodios/", listar_animes_episodios, name="listar_animes_episodios"),
    path("fav-sis/reiniciar_anime_fav/", reiniciar_anime_fav, name="reiniciar_anime_fav"),
    path("api/obtener_episodios_x_temporada/", obtener_eps_x_temporada, name="obtener_eps_x_temporada"),
    # Api Rest
    path('api/search/<str:query>', api_search, name='api_search'),
    path('api/cors/', cors_everywhere, name='cors'),
    # Urls de utilidades
    path('redirect/', redirect_page, name='redirect'),
    # APP MOBILE
    path('mobile/api/v1/3415432348869182/get-latest-episodes/', mobile_get_latest_episodes, name='mobile_get_latest_episodes'),
    path('mobile/api/v1/3415432348869182/get-latest-animes/', mobile_get_latest_animes, name='mobile_get_latest_animes'),
    path('mobile/api/v1/3415432348869182/find-animes/<str:query>', mobile_find_animes, name='mobile_find_animes'),
    path('mobile/api/v1/3415432348869182/anime-detail/<str:slug>', mobile_anime_detail, name='mobile_anime_detail'),
    path('mobile/api/v1/3415432348869182/episode-detail/<str:slug>', mobile_episode_detail, name='mobile_episode_detail'),
    path('mobile/api/v1/3415432348869182/signin/', mobile_signin, name='mobile_signin'),
    path('mobile/api/v1/3415432348869182/signup/', post_register, name='post_register'),
    path('mobile/api/v1/3415432348869182/forgot-password/', post_password_reset_request, name='post_password_reset_request'),

    # ADS
    # path('ps/mHv6tt.js', ads_ps, name='ads_ps'),

    # REST FRAMEWORK
    path('api/v1/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    path('google_one_tap_login/',api_views.google_one_tap_login, name='google-one-tap-login' ), # 
    path('rest-auth/google/', api_views.GoogleLogin.as_view(), name='redirect'), #borrar
    
    path('api/v1/rest-auth/google/', api_views.GoogleRealLogin.as_view(), name='rest-google-login'), #borrar
    path('api/v1/signin/', api_views.signin, name='signin'),
    path('api/v1/signup/', api_views.signup, name='signup'),
    path('api/v1/change-coppa-compliance/', api_views.change_coppa_compliance, name='change_coppa_compliance'),
    path('api/v1/users-private-detail/<int:pk>/', api_views.UserPrivateDetail.as_view()),
    path('api/v1/send-push-notification/', api_views.send_push_notification, name='send_push_notification'),
    path('api/v1/eval-unpack/', api_views.eval_unpack, name='eval_unpack'),
    path('api/v1/banuser/', api_views.ban_user, name='banuser'),
    path('api/v1/unbanuser/', api_views.unban_user, name='unbanuser'),
    # path('api/v1/cloudflare-bypass/', api_views.cloudflare_bypass, name='cloudflare_bypass'),
    path('api/v1/next-to-see/', api_views.get_user_episodes_next, name='next_to_see'),
    path('api/v1/ds/', api_views.discord, name='discord'),
    path('api/v1/poe/', api_views.poe_api, name='poe'),
]

# if settings.ENVIO_DE_EMAILS:
#     emails.email_server_iniciado()

# if settings.AUTOMATIC_UPDATE:
#     print("Tienes habilitada la actualizacion automatica de animes")
#     from .anime_scheduler import actualizar_animes
#     actualizar_animes.start()
# else:
#     print("No tienes habilitada la actualizacion automatica de animes")