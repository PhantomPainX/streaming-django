from django.apps import AppConfig
from django.conf import settings
# import os

class MainAppConfig(AppConfig):
    name = 'main_app'

    def ready(self):
        from main_app import emails
        from main_app.notifications import android_admin_notification
        from main_app.models import EmailInicioServer
        emails_count = len(EmailInicioServer.objects.all())
        emails_count = emails_count + 1
        
        if settings.AUTOMATIC_UPDATE:
            print("Tienes habilitada la actualizacion automatica de animes")
            from .anime_scheduler import actualizar_animes
            # android_admin_notification(
            #     title="Servidor iniciado [{}]".format(emails_count),
            #     message="Tienes habilitada la actualizacion automatica de animes",
            #     image="",
            #     extra={}
            # )
            actualizar_animes.start()
        else:
            print("No tienes habilitada la actualizacion automatica de animes")
            # android_admin_notification(
            #     title="Servidor iniciado [{}]".format(emails_count),
            #     message="No tienes habilitada la actualizacion automatica de animes",
            #     image="",
            #     extra={}
            # )

        if settings.ENVIO_DE_EMAILS:
            emails.email_server_iniciado()
