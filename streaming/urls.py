from django.conf.urls import handler404,handler500

from django.views.static import serve
from django.views.generic.base import TemplateView
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path
from django.conf.urls import include
from django.conf import settings
from django.conf.urls.static import static
from main_app.sitemaps import AnimeSitemap, EpisodioSitemap, StaticViewSitemap, LatinoSitemap
from main_app.forms import CustomSetPasswordForm
from django.contrib.auth import views as auth_views
from main_app.views import iniciar_sesion

sitemap_animes = {'animes': AnimeSitemap}
sitemap_episodios = {'episodios': EpisodioSitemap}
sitemap_static = {'static': StaticViewSitemap}
sitemap_latino = {'latino': LatinoSitemap}

urlpatterns = [
    path('', include('main_app.urls')),
    path(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),
    path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
    path('admin/', admin.site.urls),
    # path('sitemap_animes.xml', sitemap, {'sitemaps': sitemap_animes}, name='sitemap_animes'),
    # path('sitemap_latino.xml', sitemap, {'sitemaps': sitemap_latino}, name='sitemap_latino'),
    # path('ud89s79d8a8s88d7a6d5a70sd0f9c8s7a/sitemap_episodios.xml', sitemap, {'sitemaps': sitemap_episodios}, name='sitemap_episodios'),
    # path('sitemap_static.xml', sitemap, {'sitemaps': sitemap_static}, name='sitemap_static'),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    # path(
    #     "app-ads.txt",
    #     TemplateView.as_view(template_name="app-ads.txt", content_type="text/plain"),
    # ),
    # path(
    #     "ads.txt",
    #     TemplateView.as_view(template_name="ads.txt", content_type="text/plain"),
    # ),
    # path(
    #     "manifest.json",
    #     TemplateView.as_view(template_name="manifest.json", content_type="text/json"),
    # ),
    # path(
    #     "sw.js",
    #     TemplateView.as_view(template_name="sw.js", content_type="application/javascript"),
    # ),
    # path('cuenta/iniciar-sesion/', iniciar_sesion, name='login'),
    # path('cuenta/cerrar-sesion/', auth_views.LogoutView.as_view(template_name="registration/logout.html"), name='logout'),
    # path('cuenta/password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name="password/password_reset_done.html"), name='password_reset_done'),
    # path('cuenta/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name="password/password_reset_confirm.html", form_class=CustomSetPasswordForm), name='password_reset_confirm'),
    # path('cuenta/reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name="password/password_reset_complete.html"), name='password_reset_complete'),
]

handler404 = 'main_app.views.handle_not_found'
handler500 = 'main_app.views.handle_error'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
