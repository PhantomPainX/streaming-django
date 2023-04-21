from django.template.loader import get_template
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from main_app.models import *
import datetime

emails_admin = [
    'manuelgarcia1710@gmail.com'
]

email_mods = []

def enviar_email_actualizacion(animes, capitulos):

    hora_actual = datetime.datetime.now()
    timezone = datetime.timezone(datetime.timedelta(hours=2))

    emails = len(EmailActualizacion.objects.all())

    emails = emails + 1
    asunto = "Nueva Actualización [{}]".format(emails)

    context = {
        "animes": animes,
        "capitulos": capitulos,
        "hora_actual": hora_actual,
        "timezone": timezone
    }
    template = get_template('email_templates/email_actualizacion_animes.html')
    content = template.render(context)

    email = EmailMultiAlternatives(
        asunto,
        '127.0.0.1',
        '127.0.0.1 Servidor <no-responder@127.0.0.1>',
        emails_admin
    )

    email.attach_alternative(content, "text/html")
    email_enviado = email.send()

    if email_enviado:
        print("Email de actualizacion enviado")
        EmailActualizacion.objects.create(email=settings.EMAIL_HOST_USER, asunto=asunto, numero=emails)
    else:
        print("Email de actualizacion no enviado")

def email_server_iniciado():

    if settings.AUTOMATIC_UPDATE:
        actualizacion_automatica = "habilitada"
    else:
        actualizacion_automatica = "deshabilitada"

    hora_actual = datetime.datetime.now()

    emails = len(EmailInicioServer.objects.all())

    emails = emails + 1
    asunto = "Servidor iniciado [{}]".format(emails)
    print(asunto)

    context = {
        "actualizacion_automatica": actualizacion_automatica,
        "hora_actual": hora_actual
    }
    template = get_template('email_templates/email_server_iniciado.html')
    content = template.render(context)

    email = EmailMultiAlternatives(
        asunto,
        '127.0.0.1',
        '127.0.0.1 Servidor <no-responder@127.0.0.1>',
        emails_admin
    )

    email.attach_alternative(content, "text/html")
    email_enviado = email.send()

    if email_enviado:
        print("Email de inicio de servidor enviado")
        EmailInicioServer.objects.create(email=settings.EMAIL_HOST_USER, asunto=asunto, numero=emails)
    else:
        print("Email de inicio de servidor enviado")