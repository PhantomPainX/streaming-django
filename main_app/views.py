"""
Vistas de la aplicación main_app del proyecto 127.0.0.1

@Autor Manuel García Marín

Última Modificación: 02-04-2022
"""

import json, requests, re, arrow
from datetime import datetime
from bs4 import BeautifulSoup
from pydoc import resolve
from django import http
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from main_app.models import *
from django.core.paginator import Paginator
from django.core.mail import send_mail, BadHeaderError, EmailMessage
from django.contrib.auth import login, authenticate
from main_app.forms import *
from django.template.loader import get_template, render_to_string
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib.auth.models import User
from django.db.models.query_utils import Q
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from main_app.functions.cipher import encrypt_pass
from django.http import StreamingHttpResponse
from threading import Thread

from rest_framework.authtoken.models import Token
from main_app.discord.webhooks import DsWebhook, RegistrationSources

# import asyncio
# from asgiref.sync import sync_to_async

#======================= Configuraciónes ===========================#
root_url = 'http://127.0.0.1'

def estrenos():
    return [
        1900,
        1967,
        1969,
        1970,
        1976,
        1977,
        1978,
        1979,
        1981,
        1982,
        1983,
        1984,
        1985,
        1986,
        1987,
        1988,
        1989,
        1990,
        1991,
        1992,
        1993,
        1994,
        1995,
        1996,
        1997,
        1998,
        1999,
        2000,
        2001,
        2002,
        2003,
        2004,
        2005,
        2006,
        2007,
        2008,
        2009,
        2010,
        2011,
        2012,
        2013,
        2014,
        2015,
        2016,
        2017,
        2018,
        2019,
        2020,
        2021,
        2022
    ]

#======================= Vistas para los codigos de error ===========================#

"""
@autor Manuel García Marín
Última Modificación: 29-03-2022 | 16:25

Descripción: esta función sirve para devolver la pagina de error 404

return: devuelve la plantilla de error con un titulo, mensaje y codigo.
"""
def handle_not_found(request, exception):

    titulo = "¿Te perdiste?"
    mensaje = "Parece que no encontramos esta pagina :("
    codigo = 404
    context = {
        'titulo': titulo,
        'mensaje': mensaje,
        'codigo': codigo
    }
    return render(request, 'not_found.html', context)

"""
@autor Manuel García Marín
Última Modificación: 29-03-2022 | 16:25

Descripción: esta función sirve para devolver la pagina de error 500

return: devuelve la plantilla de error con un titulo, mensaje y codigo.

"""
def handle_error(request):

    titulo = "Oops! Algo salió mal"
    mensaje = "Ocurrio un error inesperado, por favor intenta nuevamente."
    codigo = 500
    context = {
        'titulo': titulo,
        'mensaje': mensaje,
        'codigo': codigo
    }
    return render(request, 'not_found.html', context)

#======================= Vistas Principales (Home, Anime, Latino, Episodio, Directorio, etc) ===========================#

"""
@autor Manuel García Marín
Última Modificación: 13-04-2022 | 16:46

Función: home
Descripción: devuelve un render de la página home

--Contexto del render--

animes: los últimos 12 animes (Idioma Japones) (Lista)
series: las últimas 12 series, las cuales sean en idioma latino. (Lista)
ultimos_en_emision: últimos 22 animes (japones) que esten con el estado En Emisión.
ultimos_episodios: últimos 12 episodios (japones) + la cantidad de episodios por cada anime. (objeto zip)
finalizado: objeto estado finalizado (Es inutil, lo se...)
episodios_count: la cantidad de episodios de los animes que se muestran en ultimos_episodios
animes_aleatorios: 12 animes o series aleatorios con limite de 12
tipos: devuelve los tipos que hay en la base de datos
body_img: devuelve la ruta de la imagen del primer episodio mostrado
generos: devuelve los generos que hay en la base de datos
estados: devuelve los estados que hay en la base de datos
estrenos: devuelve los estrenos que hay en la funcion estrenos()

return: devuelve el render de la plantilla home.html + el contexto
"""

from django.db import connection

def home(request):

    #CRSF-TOKEN

    #filtrar ultimos episodios por tipos de anime

    #si el usuario es admin, mostrar todos los animes
    if request.user.is_staff:
        first18 = Anime.objects.filter(idioma=1).order_by('-agregado')[:20]
        ultimos_en_emision = Anime.objects.filter(estado=2).order_by('-agregado')[:22]
        series = Anime.objects.filter(idioma=2)[:20]
    else:
        first18 = Anime.objects.filter(idioma=1).order_by('-agregado').exclude(visible=False)[:20]
        ultimos_en_emision = Anime.objects.filter(estado=2).order_by('-agregado').exclude(visible=False)[:22]
        series = Anime.objects.filter(idioma=2).exclude(visible=False)[:20]
        
    ultimos_episodios = Episodio.objects.filter(anime__idioma=1).order_by('-fecha')[:20]
    finalizado = Estado.objects.get(id=1)

    context = {
        'animes': first18,
        'series': series,
        'ultimos_en_emision': ultimos_en_emision,
        'ultimos_episodios': ultimos_episodios,
        'finalizado': finalizado,
    }
    return render(request,'home.html', context)


def random_anime(request):
    if request.user.is_staff:
        random_anime = Anime.objects.filter().order_by('?')[0]
    else:
        random_anime = Anime.objects.exclude(visible=False).order_by('?')[0]

    if (random_anime.idioma.idioma == "Japonés"):
        return redirect('anime', random_anime.slug)
    else:
        return redirect('latino', random_anime.slug)

"""
@Manuel García Marín
Última Modificación: 29-03-2022 | 16:58

Función: anime(request, slug)

---Parametros---

slug {String}: el slug del anime que se desea devolver
----------------
Descripción: devuelve la página que muestra el ANIME (tipos: TV, OVA, PELÍCULA, ESPECIAL) deseado.

--Contexto del render--

anime: 1 objeto Anime (diccionario con la información del anime) {}
episodios: devuelve los objetos Episodio del anime [{},{}]
relacionados: 4 animes relacionados al anime del slug filtrados por sus géneros [{},{}]
ultimos_episodios: tupla de objetos Episodios de los ultimos episodios + la cantidad de los episodios de cada anime
total_episodios: la cantidad total de episodios del anime
--------------------------------------------------------

return: devuelve el render de la plantilla anime.html + el contexto (dict) con los datos
"""

def anime(request,slug):

    if slug == 'anime-random':
        anime = Anime.objects.filter(idioma__idioma="Japonés").order_by('?')[0]
        # Si el anime esta oculto, se redirige a la pagina principal
        if not anime.visible and not request.user.is_staff:
            return redirect('home')
    else:
        anime_exists = Anime.objects.filter(slug=slug).exists()
        if anime_exists:
            anime = Anime.objects.get(slug=slug)
            # Si el anime esta oculto, se redirige a la pagina principal
            if not anime.visible and not request.user.is_staff:
                return redirect('home')
        else:
            return handle_not_found(request, 404)
    
    if anime:
        if anime.idioma.idioma == "Japonés":
            if request.user.is_staff:
                relacionados = Anime.objects.filter(generos__in=anime.generos.all()).exclude(slug=anime.slug).order_by('?')[:4]
            else:
                relacionados = Anime.objects.filter(generos__in=anime.generos.all()).exclude(slug=anime.slug).exclude(visible=False).order_by('?')[:4]

            ultimos_episodios = Episodio.objects.filter(anime__idioma__idioma="Japonés").order_by('-fecha')[:12]
            episodios_count = []
            for episodio in ultimos_episodios:
                count_anime_episodes = Episodio.objects.filter(anime=episodio.anime).count() 
                episodios_count.append(count_anime_episodes)

            #Aqui se unen las dos listas para que sean de la misma longitud, para poder iterar sobre ambas.
            #Es como unir las dos listas en una y que luego se puedan iterar juntas en el mismo for en el template.
            zipped = zip(ultimos_episodios, episodios_count)

            episodios = Episodio.objects.filter(anime=anime).values().reverse()
            total_episodios = episodios.count()


            for episodio in episodios:
                episodio['fecha'] = arrow.get(episodio['fecha']).humanize(locale='es')

            if anime.prox_episodio:
                prox_date = datetime.strptime(anime.prox_episodio, '%Y-%m-%d').date()
                today = datetime.today().date()
                human_date = arrow.get(prox_date).humanize(locale='es')

                if today == prox_date:
                    anime.human_prox_episodio = "hoy"
                elif today < prox_date:
                    anime.human_prox_episodio = human_date + ' más'
                else:
                    anime.human_prox_episodio = human_date

            context = {
                'anime': anime,
                'episodios': episodios,
                'relacionados': relacionados,
                'ultimos_episodios': zipped,
                "total_episodios": total_episodios
            }
            
                

            # local = arrow.get(episodios[0]['fecha'])

            # print(local.humanize(locale='es'))

            return render(request,'anime.html', context)
        else:
            return handle_not_found(request, 404)
    else:
        return handle_not_found(request, 404)


"""
@Manuel García Marín
Última Modificación: 29-03-2022 | 16:58

Función: latino(request, slug)

---Parametros---

slug {String}: el slug de la serie en latino que se desea devolver
----------------
Descripción: devuelve la página que muestra cualquier show en latino cuyos tipos no sean TV, OVA, PELÍCULA, ESPECIAL.

--Contexto del render--

anime: 1 objeto Latino (diccionario con la información del show en Latino) {}
episodios: devuelve los objetos Episodio del show en latino [{},{}]
relacionados: 4 animes relacionados al show en latino del slug filtrados por sus géneros [{},{}]
ultimos_episodios: tupla de objetos Episodios de los ultimos episodios + la cantidad de los episodios de cada show en latino
total_episodios: la cantidad total de episodios del show en latino
--------------------------------------------------------

return: devuelve el render de la plantilla show.html + el contexto (dict) con los datos
"""
@ensure_csrf_cookie
def latino(request, slug):
    anime_exists = Anime.objects.filter(slug=slug).exists()
    if anime_exists:
        anime = Anime.objects.get(slug=slug)
        if anime.idioma.idioma != 'Latino':
            return handle_not_found(request, 404)
        
        # Si el anime esta oculto, se redirige a la pagina principal a menos que el usuario sea staff
        if not anime.visible and not request.user.is_staff:
            return redirect('home')
    else:
        return handle_not_found(request, 404)

    if request.user.is_staff:
        relacionados = Anime.objects.filter(generos__in=anime.generos.all()).exclude(slug=anime.slug).order_by('?')[:4]
    else:
        relacionados = Anime.objects.filter(generos__in=anime.generos.all()).exclude(slug=anime.slug).exclude(visible=False).order_by('?')[:4]

    ultimos_episodios = Episodio.objects.filter(anime__idioma__idioma="Japonés").order_by('-fecha')[:12]
    episodios_count = []
    for episodio in ultimos_episodios:
        count_anime_episodes = Episodio.objects.filter(anime=episodio.anime).count() 
        episodios_count.append(count_anime_episodes)

    #Aqui se unen las dos listas para que sean de la misma longitud, para poder iterar sobre ambas.
    #Es como unir las dos listas en una y que luego se puedan iterar juntas en el mismo for en el template.
    zipped = zip(ultimos_episodios, episodios_count)

    episodios = Episodio.objects.filter(Q(anime=anime) & (Q(temporada=1) | Q(temporada=0))).values().reverse()
    total_episodios_temporadas = Episodio.objects.filter(anime=anime).count()
    total_episodios = episodios.count()

    for episodio in episodios:
        episodio['fecha'] = arrow.get(episodio['fecha']).humanize(locale='es')

    context = {
        'anime': anime,
        'episodios': episodios,
        'relacionados': relacionados,
        'total_episodios_temporadas': total_episodios_temporadas,
        'ultimos_episodios': zipped,
        "total_episodios": total_episodios
    }

    return render(request,'show.html', context)


"""
@Manuel García Marín
Última Modificación: 29-03-2022 | 16:58

Función: latino(request, slug)

---Parametros---

slug {String}: el slug del episodio
----------------

---Descripción---
Devuelve la página que muestra los videos del episodio en cuestion.
Muestra los embed del episodio, información del anime/show latino, animes relacionados

return: devuelve el render de la plantilla episodio.html + el contexto (dict) con los datos
"""
def episodio(request,slug):

    episodio_exists = Episodio.objects.filter(slug=slug).exists()
    if episodio_exists:
        episodio = Episodio.objects.get(slug=slug)

        # Si el episodio esta deshabilitado por el anime o por el mismo episodio, se rediriige a la home a menos que el usuario sea staff
        if not episodio.anime.visible and not request.user.is_staff:
            return redirect('home')
        if not episodio.visible and not request.user.is_staff:
            return redirect('home')

        episodio.fecha = arrow.get(episodio.fecha).humanize(locale='es')
        
        if episodio.anime.prox_episodio:
            prox_date = datetime.strptime(episodio.anime.prox_episodio, '%Y-%m-%d').date()
            today = datetime.today().date()
            human_date = arrow.get(prox_date).humanize(locale='es')

            if today == prox_date:
                episodio.next_date = "hoy"
            elif today < prox_date:
                episodio.next_date = human_date + ' más'
            else:
                episodio.next_date = human_date
    else:
        return handle_not_found(request, 404)
    episodios = Episodio.objects.filter(anime=episodio.anime)
    ultimo_episodio = episodios.order_by('-id')[0]
    siguiente_episodio = episodio.numero + 1
    anterior_episodio = episodio.numero - 1

    total_episodios = episodios.count()
    
    embeds_list = []
    embeds = Embed.objects.filter(episodio=episodio)
    embeds = embeds.exclude(url__contains="v.tioanime")
    downloads_exists = False
    downloads_links = []
    for embed in embeds:
        if "mega.nz" in embed.url or "fembed" in embed.url or "yourupload" in embed.url:
            downloads_exists = True
        
        if "mega.nz" in embed.url:
            download_link = embed.url.replace('embed#','')
            downloads_links.append(download_link)
        elif "fembed" in embed.url:
            download_link = embed.url.replace('/v/','/f/')
            downloads_links.append(download_link)
        elif "yourupload" in embed.url:
            download_link = embed.url.replace('/embed/','/watch/')
            downloads_links.append(download_link)
    
        embeds_list.append(embed.url)

    if request.user.is_staff:
        relacionados = Anime.objects.filter(generos__in=episodio.anime.generos.all()).exclude(slug=episodio.anime.slug).order_by('?')[:4]
    else:
        relacionados = Anime.objects.filter(generos__in=episodio.anime.generos.all()).exclude(slug=episodio.anime.slug, visible=False).order_by('?')[:4]

    ultimos_episodios = Episodio.objects.filter(anime__idioma__idioma="Japonés").order_by('-fecha')[:12]

    episodios_count = []
    for capitulo in ultimos_episodios:
        count_anime_episodes = Episodio.objects.filter(anime=episodio.anime).count() 
        episodios_count.append(count_anime_episodes)

    #Aqui se unen las dos listas para que sean de la misma longitud, para poder iterar sobre ambas.
    #Es como unir las dos listas en una y que luego se puedan iterar juntas en el mismo for en el template.
    zipped = zip(ultimos_episodios, episodios_count)

    context = {
        'episodios': episodios,
        'episodio': episodio,
        'ultimo_episodio': ultimo_episodio,
        'siguiente_episodio': siguiente_episodio,
        'anterior_episodio': anterior_episodio,
        'relacionados': relacionados,
        'ultimos_episodios': zipped,
        'embeds_objects': embeds,
        'embeds': embeds_list,
        'total_episodios': total_episodios,
        'downloads_exists': downloads_exists,
        'downloads_links': downloads_links
    }

    return render(request,'episodio.html', context)


"""
@Manuel García Marín
Última Modificación: 29-03-2022 | 16:58

Función: directorio(request)

---Descripción---
Devuelve la página que muestra una lista de 20 animes, 
puede aceptar filtro de tipos, estados, generos, estreno y nombre del anime.

Funciona tambien con un paginador que detecta y limita los animes mostrados automaticamente.

return: devuelve el render de la plantilla directorio.html + el contexto (dict) con los datos
"""
def directorio(request):

    get_data_list = []
    nom_estado = ""
    nom_tipo = ""
    nom_genero = ""
    nom_estreno = ""
    nom_idioma = ""
    if request.method == 'GET':
        query = request.GET.get('q')
        estado = request.GET.get('estado')
        tipo = request.GET.get('tipo')
        genero = request.GET.get('genero')
        estreno = request.GET.get('estreno')
        idioma = request.GET.get('idioma')

        get_data_list = []

        if query:
            get_data_list.append('&q='+query)
        if estado:
            get_data_list.append('&estado='+estado)
            nom_estado = Estado.objects.get(id=estado).estado
        if tipo:
            get_data_list.append('&tipo='+tipo)
            nom_tipo = Tipo.objects.get(id=tipo).tipo
        if genero:
            get_data_list.append('&genero='+genero)
            nom_genero = Genero.objects.get(id=genero).genero
        if estreno:
            get_data_list.append('&estreno='+estreno)
            nom_estreno = estreno
        if idioma:
            get_data_list.append('&idioma='+idioma)
            nom_idioma = Idioma.objects.get(id=idioma).idioma

        if request.user.is_staff:
            animes = Anime.objects.all().order_by('-agregado')
        else:
            animes = Anime.objects.all().order_by('-agregado').exclude(visible=False)

        if genero:
            generoo = Genero.objects.filter(id=genero)

            if request.user.is_staff:
                animes = Anime.objects.filter(generos__in=generoo).order_by('-agregado')
            else:
                animes = Anime.objects.filter(generos__in=generoo).order_by('-agregado').exclude(visible=False)

            if query:
                animes = animes.filter(nombre__icontains=query).order_by('-agregado')
                if estado:
                    animes = animes.filter(estado_id=estado).order_by('-agregado')
                if tipo:
                    animes = animes.filter(tipo_id=tipo).order_by('-agregado')
                if estreno:
                    animes = animes.filter(estreno=estreno).order_by('-agregado')
                if idioma:
                    animes = animes.filter(idioma=idioma).order_by('-agregado')
            else:
                if estado:
                    animes = animes.filter(estado_id=estado).order_by('-agregado')
                if tipo:
                    animes = animes.filter(tipo_id=tipo).order_by('-agregado')
                if estreno:
                    animes = animes.filter(estreno=estreno).order_by('-agregado')
                if idioma:
                    animes = animes.filter(idioma=idioma).order_by('-agregado')
        else:
            if query:
                if request.user.is_staff:
                    animes = Anime.objects.filter(nombre__icontains=query).order_by('-agregado')
                else:
                    animes = Anime.objects.filter(nombre__icontains=query).order_by('-agregado').exclude(visible=False)

                if estado:
                    animes = animes.filter(estado_id=estado).order_by('-agregado')
                if tipo:
                    animes = animes.filter(tipo_id=tipo).order_by('-agregado')
                if estreno:
                    animes = animes.filter(estreno=estreno).order_by('-agregado')
                if idioma:
                    animes = animes.filter(idioma=idioma).order_by('-agregado')
            else:
                if estado:
                    animes = animes.filter(estado_id=estado).order_by('-agregado')
                if tipo:
                    animes = animes.filter(tipo_id=tipo).order_by('-agregado')
                if estreno:
                    animes = animes.filter(estreno=estreno).order_by('-agregado')
                if idioma:
                    animes = animes.filter(idioma=idioma).order_by('-agregado')
    else:
        if request.user.is_staff:
            animes = Anime.objects.all().order_by('-agregado')
        else:
            animes = Anime.objects.all().order_by('-agregado').exclude(visible=False)
    try:
        body_img = animes.filter().order_by('?')[0].imagen
    except IndexError:
        body_img = 'icons/red-space.jpg'

    paginator = Paginator(animes, 20)
    pagina = request.GET.get('p') or 1
    animes = paginator.get_page(pagina)
    pagina_actual = int(pagina)
    paginas = range(1, animes.paginator.num_pages + 1)
    
    tipos = Tipo.objects.all().order_by('id')
    generos = Genero.objects.all().order_by('id')
    estados = Estado.objects.all().order_by('id')
    idiomas = Idioma.objects.all().order_by('id')

    context = {
        'body_img': body_img,
        'animes': animes,
        "paginas": paginas,
        "tipos": tipos,
        "generos": generos,
        "estados": estados,
        "estrenos": estrenos(),
        "idiomas": idiomas,
        "pagina_actual": pagina_actual,
        "nom_estado": nom_estado,
        "nom_tipo": nom_tipo,
        "nom_genero": nom_genero,
        "nom_estreno": nom_estreno,
        "nom_idioma": nom_idioma,
        "data_list": get_data_list
    }

    return render(request,'directorio.html',context)


"""
@Manuel García Marín
Última Modificación: 29-03-2022 | 16:58

Función: reporte(request)

---Descripción---
Sirve para enviar un reporte de un embed que no sirva a la lista de correos de administrador.

Si se abre sin enviar ningun formulario abre la pagina para enviar un reporte con la información de un episodio. (embeds, nombre del anime y numero del episodio)
Si se envia un formulario deberia enviar el correo con la informacion del embed reportado a los admins y mostrar una pagina informandole al usuario que su correo fue enviado

--Comportamiento normal--
Envia el correo del reporte a los admins y mostrar un mensaje de enviado al usuario
-------------------------

---Comportamiento anormal---
Podia pasar que el servidor de correo falle, si ese fuera el caso al usuario de le mostrara la pagina con error 500 del lado del servidor.
----------------------------


return: 
si no se envia el formulario, devuelve el render de la plantilla reporte.html + el contexto
si se envia el formulario, entonces devuelve el mismo render, nada mas que se controla el mensaje directo en la plantilla
"""
def reporte(request):
    if request.method == 'GET':
        episodio_id = request.GET.get('epid')
        validar = Episodio.objects.filter(id=episodio_id).exists()

        if validar:
            episodio = Episodio.objects.get(id=episodio_id)
            embeds = Embed.objects.filter(episodio=episodio)
            embeds = embeds.exclude(url__contains="v.tioanime")
            context = {
                'episodio': episodio,
                'embeds': embeds
            }
            return render(request,'reporte.html',context)
        else:
            return handle_not_found(request, 404)

    elif request.method == 'POST':
        embed_id = request.POST.get('embed')
        validacion = Embed.objects.filter(id=embed_id).exists()
        if validacion:
            embed = Embed.objects.get(id=embed_id)
            episodio = embed.episodio

            #Enviar correo electronico
            asunto = 'Reporte de Fuente de Video (id: {}) - 127.0.0.1'.format(embed_id)
            mensaje = """
            Se ha reportado que el episodio {} del show {} no funciona.\n\n
            Show: {}\n
            Episodio: {}\n
            Nombre del la fuente de video: {} (id: {})\n
            Link de la fuente de video: {}\n
            Admin Link: {}/admin/main_app/embed/{}/change/\n
            IP del usuario que envio el reporte: {}\n
            """.format(episodio.numero, episodio.anime.nombre, episodio.anime.nombre, episodio.numero, embed.embed, embed.id, embed.url, root_url, embed.id, request.META['REMOTE_ADDR'])

            from main_app.emails import emails_admin
            from django.conf.global_settings import EMAIL_HOST_USER

            send_mail(
                asunto,
                mensaje,
                EMAIL_HOST_USER,
                emails_admin,
                fail_silently=False
            )

            context = {
                'episodio': episodio,
                'embed': embed
            }
            return render(request,'reporte.html', context)
        else:
            return handle_not_found(request, 404)
    else:
        return handle_not_found(request, 404)


def ultimos_episodios(request):

    ultimos_episodios = Episodio.objects.filter(anime__idioma__idioma="Japonés").order_by('-fecha')[:48]
    episodios_count = []
    for episodio in ultimos_episodios:
        count_anime_episodes = Episodio.objects.filter(anime=episodio.anime).count() 
        episodios_count.append(count_anime_episodes)

    zipped = zip(ultimos_episodios, episodios_count)

    context = {
        'ultimos_episodios': zipped,
        'episodios_count': episodios_count
    }
    return render(request,'ultimos_episodios.html', context)


def contacto(request):
    if request.method == 'GET':
        form = ContactoForm()
        return render(request,'contacto.html', {'form': form})
    elif request.method == 'POST':
        form = ContactoForm(request.POST)
        if form.is_valid():
            nombre_completo = form.cleaned_data['nombre_completo']
            email = form.cleaned_data['email']
            asunto = form.cleaned_data['asunto']
            mensaje = form.cleaned_data['mensaje']
            
            #Enviar correo electronico
            e_asunto = 'Mensaje de {} - 127.0.0.1'.format(nombre_completo)
            plantilla = "email_templates/email_formulario_contacto.txt"
            ctx = {
                'nombre_completo': nombre_completo,
                'email': email,
                'asunto': asunto,
                'mensaje': mensaje
            }

            cuerpo = render_to_string(plantilla, ctx)
            correo = EmailMessage(
                e_asunto,
                cuerpo,
                '127.0.0.1 <no-responder@127.0.0.1>',
                ['contacto@127.0.0.1', 'manuel@127.0.0.1'],
                reply_to=[email]
            )
            correo.send()
            
            return render(request, 'contacto.html')
        else:
            return render(request,'contacto.html', {'form': form})


#============================== Redirecciones ======================================#

def episodio_redirect(request, slug):
    return redirect('/ver/{}'.format(slug), permanent=True)

def redirect_page(request):
    if request.method == 'GET':
        page = request.GET.get('p')
        if page:
            return HttpResponseRedirect(page)
        else:
            return handle_not_found(request, 404)


#============================== API Rest ======================================#

def api_search(request, query):
    json_response = []
    if len(query) >= 3:

        if request.user.is_staff:
            animes = Anime.objects.filter(nombre__icontains=query).order_by('-agregado')[:20]
        else:
            animes = Anime.objects.filter(nombre__icontains=query).exclude(visible=False).order_by('-agregado')[:20]

        if animes:
            for anime in animes:
                if (anime.idioma.idioma == "Latino"):
                    link = "/latino/" + anime.slug
                else:
                    link = "/anime/" + anime.slug

                json_response.append({
                    'id': anime.id,
                    'nombre': anime.nombre,
                    'tipo': anime.tipo.tipo,
                    'estreno': anime.estreno,
                    'estado': anime.estado.estado,
                    'sinopsis': anime.sinopsis,
                    'link': link,
                    'imagen': "/media/" + str(anime.imagen)
                })
        else:
            json_response.append({
                'error': 'No se encontraron resultados'
            })
    else:
        json_response.append({
            'error': 'La búsqueda debe tener al menos 3 caracteres'
        })
    return JsonResponse(json_response, safe=False, json_dumps_params={'ensure_ascii': False})

@csrf_exempt
def cors_everywhere(request):
    if request.method == 'POST':
            
        raw_data = json.loads(request.body)
        url = raw_data['url']
        response = requests.get(url, headers={'Referer': url})

        return HttpResponse(response.text)
    else:
        return handle_not_found(request, 404)


#============================== Sistema de Cuenta ======================================#
def iniciar_sesion(request):
    if request.user.is_authenticated:
        return redirect('/')
    else:

        if request.method == 'POST':
            #obtiene los datos del formulario
            username = request.POST['user_email']
            password = request.POST['password']

            if "@" in username:
                try:
                    username = User.objects.get(email=username).username
                except User.DoesNotExist:
                    return render(request, 'registration/login.html', {'error': 'Usuario/Email o contraseña incorrectos'})

            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    if request.GET.get('next'):
                        return redirect(request.GET.get('next'))
                    else:
                        return redirect('/')
                else:
                    return render(request, 'registration/login.html', {'error': 'Tu cuenta esta desactivada'})
            else:
                return render(request, 'registration/login.html', {'error': 'Usuario/Email o contraseña incorrectos'})

        return render(request,'registration/login.html')

from .emails import emails_admin

def send_email_admin(username, email):
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

    #Se envia el correo al administrador
    # asunto = 'Nuevo usuario registrado - 127.0.0.1'
    # template = get_template('email_templates/registro_nuevo_usuario.html')
    # content = template.render({
    #     'username': username,
    #     'email': email,
    # })
    # emails = emails_admin
    # send_mail(
    #     asunto,
    #     content,
    #     recipient_list=emails,
    #     from_email='127.0.0.1 <{}>'.format(settings.EMAIL_HOST_USER),
    #     html_message=content,
    #     fail_silently=False
    # )
    
    return

def registro(request):
    #si el usuario esta autenticado
    if request.user.is_authenticated:
        return redirect('/')
    else:
        if request.method == 'POST':
            form = RegistroForm(request.POST)
            if form.is_valid():
                form.save()
                username = form.cleaned_data.get('username')
                email = form.cleaned_data.get('email')
                raw_password = form.cleaned_data.get('password1')
                user = authenticate(username=username, password=raw_password)
                UserExtra.objects.create(user=user)
                login(request, user)
                t = Thread(target=send_email_admin, args=(username, email))
                t.start()

                # ds = DsWebhook("")
                # ds.send_new_user(user, RegistrationSources.WEB)

                return redirect('home')
        else:
            form = RegistroForm()
        return render(request, 'registration/registro.html', {'form': form})

@csrf_exempt
def post_register(request):
    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        username = body['username']
        email = body['email']
        raw_password = body['password1']
        
        if username and email and raw_password:

            user_exists = User.objects.filter(username=username).exists()
            email_exists = User.objects.filter(email=email).exists()

            if user_exists:
                return JsonResponse({'result': 'Username already exists'})
            elif email_exists:
                return JsonResponse({'result': 'Email already exists'})

            user = User.objects.create_user(username, email, raw_password)
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            
            t = Thread(target=send_email_admin, args=(username, email))
            t.start()

            return JsonResponse({
                'result': 'registered'
            })
        else:
            return JsonResponse({
                'result': 'Form is not valid'
            })
    else:
        return JsonResponse({
            'result': 'Method not allowed'
        })

def password_reset_request(request):
	if request.method == "POST":
		password_reset_form = CustomPasswordResetForm(request.POST)
		if password_reset_form.is_valid():
			data = password_reset_form.cleaned_data['email']
			associated_users = User.objects.filter(Q(email=data))
			if associated_users.exists():
				for user in associated_users:
					subject = "Restablecimiento de contraseña"
					email_template_name = "password/password_reset_email.txt"
					c = {
					"email":user.email,
					'domain':'127.0.0.1',
					'site_name': '127.0.0.1',
					"uid": urlsafe_base64_encode(force_bytes(user.pk)),
					"user": user,
					'token': default_token_generator.make_token(user),
					'protocol': 'https',
					}
					email = render_to_string(email_template_name, c)
					try:
						send_mail(subject, email, '127.0.0.1 <no-responder@127.0.0.1>' , [user.email], fail_silently=False)
					except BadHeaderError:
						return HttpResponse('Invalid header found.')
			return render(request, 'password/password_reset_done.html')
	password_reset_form = CustomPasswordResetForm()
	return render(request=request, template_name="password/password_reset.html", context={"password_reset_form":password_reset_form})

@csrf_exempt
def post_password_reset_request(request):
    if request.method == "POST":
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        email = body['email']
        if email:
            if "@" in email and "." in email:
                associated_users = User.objects.filter(Q(email=email))
                if associated_users.exists():
                    for user in associated_users:
                        subject = "Restablecimiento de contraseña"
                        email_template_name = "password/password_reset_email.txt"
                        c = {
                            "email":user.email,
                            'domain':'127.0.0.1',
                            'site_name': '127.0.0.1',
                            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                            "user": user,
                            'token': default_token_generator.make_token(user),
                            'protocol': 'https',
                        }
                        email = render_to_string(email_template_name, c)
                        try:
                            send_mail(subject, email, '127.0.0.1 <no-responder@127.0.0.1>' , [user.email], fail_silently=False)
                        except BadHeaderError:
                            return JsonResponse({
                                'result': 'Invalid header found'
                            })
                    return JsonResponse({
                        'result': 'success'
                    })
                else:
                    return JsonResponse({
                        'result': 'No user found'
                    })
            else:
                return JsonResponse({
                    'result': 'Invalid email'
                })
        else:
            return JsonResponse({
                'result': 'No email sent to server'
            })
    else:
        return JsonResponse({
            'result': 'Method not allowed'
        })



@login_required
def mis_favoritos(request):
    if AnimesFavorito.objects.filter(usuario=request.user).exists():
        animes = AnimesFavorito.objects.filter(usuario=request.user)
        body_img = animes.order_by('?')[0].anime.imagen
    else:
        body_img = Anime.objects.filter().order_by('?')[0].imagen
        
    if request.user.is_staff:
        animes_aleatorios = Anime.objects.filter().order_by('?')[:12]
    else:
        animes_aleatorios = Anime.objects.filter().exclude(visible=False).order_by('?')[:12]
    return render(request, 'mis_favoritos.html', {'animes_aleatorios': animes_aleatorios, 'body_img': body_img})

@login_required
def perfil(request):
    title = 'Perfil'
    description = 'Aqui podras editar tus detalles y contraseña.'
    context = {
        'title': title,
        'description': description
    }
    return render(request, 'en_construccion.html', context)


#============================== API Ajax/Fetch Sistema Async de Cuenta ======================================#

def obtener_eps_x_temporada(request):
    if request.method == 'POST':

        #Si el usuario esta autenticado
        if request.user.is_authenticated:
            autenticado = True
        else:
            autenticado = False

        raw_data = json.loads(request.body)
        temporada = raw_data['temporada']
        show = raw_data['show']
        show = Anime.objects.get(id=show)
        episodios = Episodio.objects.filter(Q(anime=show) & Q(temporada=temporada)).order_by('numero')
        json_response = []
        for episodio in episodios:
            episodio.fecha = arrow.get(episodio.fecha).humanize(locale='es')
            if autenticado:
                episodio_visto = EpisodiosVisto.objects.filter(Q(usuario=request.user) & Q(episodio=episodio)).exists()
                json_response.append({
                    'id': episodio.id,
                    'visto': episodio_visto,
                    'ep_nombre': episodio.ep_nombre,
                    'url': episodio.get_absolute_url(),
                    'fecha': episodio.fecha
                })
            else:
                json_response.append({
                    'id': episodio.id,
                    'ep_nombre': episodio.ep_nombre,
                    'url': episodio.get_absolute_url(),
                    'fecha': episodio.fecha
                })
        json_response.reverse()
        json_final = {
            'autenticado': autenticado,
            'episodios': json_response
        }
        return JsonResponse(json_final, safe=False, json_dumps_params={'ensure_ascii': False})

# Sistema de animes favoritos
    
@login_required
def ver_episodio(request):
    if request.method == 'POST':
        user = request.user
        raw_data = json.loads(request.body)
        automatico = raw_data['automatico']
        ep_id = raw_data['ep_id']
        episodio = Episodio.objects.get(id=ep_id)
        usuario_ya_lo_vio = EpisodiosVisto.objects.filter(episodio=episodio, usuario=user)

        #Si es automatico, o sea que se agrega con el timer de javascript
        if automatico:
            if not usuario_ya_lo_vio:
                EpisodiosVisto.objects.create(episodio=episodio, usuario=user)
                return JsonResponse({
                    'estado': 'agregado'
                })
            else:
                return JsonResponse({
                    'estado': 'ya_agregado'
                })

        #Si es manual, o sea que se agrega con el boton de agregar
        else:
            if usuario_ya_lo_vio:
                usuario_ya_lo_vio.delete()
                return JsonResponse({
                    'estado': 'eliminado'
                })
            else:
                EpisodiosVisto.objects.create(episodio=episodio, usuario=user)
                return JsonResponse({
                    'estado': 'agregado'
                })

@login_required
def revisar_episodios(request):
    if request.method == 'POST':
        user = request.user
        json_data = json.loads(request.body)
        episodios = json_data['ep_id_lista']
        anime_id = 309

        episodios_vistos = list(EpisodiosVisto.objects.filter(usuario=user, episodio__in=episodios).values_list('episodio_id', flat=True))
        # print(episodios)
        # print(episodios_vistos)

        # episodios_response_list = []
        # for episodio in episodios:
        #     if int(episodio) in episodios_vistos:
        #         episodios_response_list.append({
        #             'id': episodio,
        #             'agregado': True
        #         })
        #     else:
        #         episodios_response_list.append({
        #             'id': episodio,
        #             'agregado': False
        #         })
        # for episodio in episodios:
        #     # ep_exists = EpisodiosVisto.objects.filter(episodio=episodio, usuario=user).exists()
        #     ep_exists = EpisodiosVisto.objects.raw('SELECT id FROM main_app_episodiosvisto WHERE episodio_id = {} AND usuario_id = {}'.format(episodio, user.id))[:]
        #     if ep_exists:
        #         episodios_response_list.append({
        #             'id': episodio,
        #             'agregado': True
        #         })
        #     else:
        #         episodios_response_list.append({
        #             'id': episodio,
        #             'agregado': False
        #         })

        return JsonResponse({'episodios_check': episodios_vistos})

@login_required
def agregar_anime_favorito(request):
    if request.method == 'POST':
        user = request.user
        json_data = json.loads(request.body)
        anime_id = json_data['anime_id']
        anime = Anime.objects.get(id=anime_id)

        anime_ya_favorito = AnimesFavorito.objects.filter(anime=anime, usuario=user)
        if anime_ya_favorito:
            anime_ya_favorito.delete()
            return JsonResponse({
                'estado': 'eliminado',
                'restantes': AnimesFavorito.objects.filter(usuario=user).count()
            })
        else:
            AnimesFavorito.objects.create(anime=anime, usuario=user)
            return JsonResponse({
                'estado': 'agregado'
            })

@login_required
def revisar_anime_favorito(request):
    if request.method == 'POST':
        user = request.user
        json_data = json.loads(request.body)
        anime_id = json_data['anime_id']
        anime = Anime.objects.get(id=anime_id)
        anime_exists = AnimesFavorito.objects.filter(anime=anime, usuario=user).exists()
        if anime_exists:
            return JsonResponse({
                'estado': 'agregado'
            })
        else:
            return JsonResponse({
                'estado': 'no_agregado'
            })

@login_required
def reiniciar_anime_fav(request):
    if request.method == 'POST':
        user = request.user
        json_data = json.loads(request.body)
        anime_id = json_data['anime_id']
        #eps = EpisodiosVisto.objects.filter(usuario=user)
        EpisodiosVisto.objects.filter(usuario=user, episodio__anime_id=anime_id).delete()
        # for ep in eps:
        #     if ep.episodio.anime.id == int(anime_id):
        #         ep.delete()

        return JsonResponse({
            'estado': 'reiniciado',
            'url_redirect': '/ver/' + Anime.objects.get(id=anime_id).slug + '-' + str(1)
        })

@login_required
def listar_animes_episodios(request):
    if request.method == 'POST':
        user = request.user
        animes_favoritos = AnimesFavorito.objects.filter(usuario=user)
        cant_animes = len(animes_favoritos)
        cant_episodios = EpisodiosVisto.objects.filter(usuario=user).count()
        paginator = Paginator(animes_favoritos.reverse(), 10)
        json_data = json.loads(request.body)
        pagina = json_data['pagina']
        animes = paginator.get_page(pagina)
        pagina_actual = int(pagina)
        paginas = animes.paginator.num_pages
        #si animes_favoritos divido en 8 da un entero, es porque no hay mas paginas

        if animes_favoritos:
            animes_favoritos_list = []
            for anime_favorito in animes:
                eps = EpisodiosVisto.objects.filter(usuario=user, episodio__anime__id=anime_favorito.anime.id)
                # anime_eps = []
                # for ep in eps:
                #     if ep.episodio.anime.id == anime_favorito.anime.id:
                #         anime_eps.append(ep)

                n_ultimo_visto = 0
                sig_ep = 0
                if eps:
                    eps = sorted(eps, key=lambda x: x.episodio.numero)
                    eps = eps[::-1]
                    n_ultimo_visto = eps[0].episodio.numero

                    episodios_de_anime_fav = Episodio.objects.filter(anime=anime_favorito.anime).order_by('numero').last()

                    estado_anime = Anime.objects.get(id=anime_favorito.anime.id).estado.estado
                    
                    if n_ultimo_visto == episodios_de_anime_fav.numero and estado_anime == 'Finalizado':
                        estado = "finalizado"
                        ep_url = '/ver/' + anime_favorito.anime.slug + '-' + str(1)
                    elif n_ultimo_visto == episodios_de_anime_fav.numero and estado_anime == 'En emision':
                        estado = "esperar"
                        ep_url = anime_favorito.anime.get_absolute_url()
                    else:
                        estado = "resumir"
                        ep_url = '/ver/' + anime_favorito.anime.slug + '-' + str(n_ultimo_visto+1)
                        sig_ep = n_ultimo_visto + 1
                    
                else:
                    estado = "empezar"
                    ep_url = '/ver/' + anime_favorito.anime.slug + '-' + str(1)

                url = anime_favorito.anime.get_absolute_url()

                animes_favoritos_list.append({
                    'id': anime_favorito.anime.id,
                    'nombre': anime_favorito.anime.nombre,
                    'tipo': anime_favorito.anime.tipo.tipo,
                    'imagen': str(anime_favorito.anime.imagen),
                    'estreno': anime_favorito.anime.estreno,
                    'estado': anime_favorito.anime.estado.estado,
                    'idioma': anime_favorito.anime.idioma.idioma,
                    'idioma_thumbnail': str(anime_favorito.anime.idioma.thumbnail),
                    'url': url,
                    'prox_episodio': anime_favorito.anime.prox_episodio,
                    'ultimo_visto': n_ultimo_visto,
                    'ep_url': ep_url,
                    'estado_anime_fav': estado,
                    'sig_ep': sig_ep
                })

            animes_favoritos_list.reverse()
            return JsonResponse({
                'tiene_favoritos': True,
                'animes_favoritos': animes_favoritos_list,
                'cant_animes': cant_animes,
                'cant_episodios': cant_episodios,
                'pagina_actual': pagina_actual,
                'paginas': paginas,
                'pagina_tiene_siguiente': animes.has_next(),
                'pagina_tiene_anterior': animes.has_previous()
            })
        else:
            return JsonResponse({
                'tiene_favoritos': False,
                'animes_favoritos': [],
                'cant_animes': cant_animes,
                'cant_episodios': cant_episodios,
            })








#---------------------------- MOBILE APP ---------------------------#

def mobile_get_latest_episodes(request):

    ultimos_episodios_obj = Episodio.objects.filter(anime__idioma=1).order_by('-fecha').values('anime__nombre', 'anime__imagen', 'slug', 'numero')
    paginator = Paginator(ultimos_episodios_obj, 20)

    request_page = request.GET.get('page')

    page = paginator.get_page(request_page)
    if not request_page:
        return HttpResponseRedirect(reverse('mobile_get_latest_episodes') + '?page=1')

    ultimos_episodios = {
        'latest_episodes': list(page),
        'actual_page': int(request_page),
        'total_pages': page.paginator.num_pages,
        'page_has_previous': page.has_previous(),
        'page_has_next': page.has_next()
    }
    
    return JsonResponse(ultimos_episodios, safe=False, json_dumps_params={'ensure_ascii': False})

def mobile_get_latest_animes(request):

    ultimos_animes_japones_obj = list(Anime.objects.filter(idioma=1).order_by('-agregado').values(
        'nombre',
        'tipo__tipo',
        'idioma__idioma',
        'imagen',
        'prox_episodio',
        'estreno',
        'sinopsis',
        'estado__estado',
        'slug'
    ))
    paginator = Paginator(ultimos_animes_japones_obj, 20)
    request_page = request.GET.get('page')
    page = paginator.get_page(request_page)
    if not request_page:
        return HttpResponseRedirect(reverse('mobile_get_latest_animes') + '?page=1')

    ultimos_animes_japones = {
        'latest_japan_animes': list(page),
        'actual_page': int(request_page),
        'total_pages': page.paginator.num_pages,
        'page_has_previous': page.has_previous(),
        'page_has_next': page.has_next()
    }

    return JsonResponse(ultimos_animes_japones, safe=False, json_dumps_params={'ensure_ascii': False})

def mobile_find_animes(request, query):
    json_response = []
    if len(query) >= 3:
        animes = Anime.objects.filter(nombre__icontains=query).order_by('-agregado')
        if animes:
            paginator = Paginator(animes, 10)
            request_page = request.GET.get('page')
            if not request_page:
                return HttpResponseRedirect(reverse('mobile_find_animes', args=[query]) + '?page=1')

            page = paginator.get_page(request_page)
            for anime in page:
                json_response.append({
                    'id': anime.id,
                    'nombre': anime.nombre,
                    'tipo': anime.tipo.tipo,
                    'estreno': anime.estreno,
                    'estado': anime.estado.estado,
                    'sinopsis': anime.sinopsis,
                    'link': anime.slug,
                    'imagen': str(anime.imagen)
                })
            json_response = {
                'animes': json_response,
                'actual_page': int(request_page),
                'total_pages': page.paginator.num_pages,
                'page_has_previous': page.has_previous(),
                'page_has_next': page.has_next()
            }
        else:
            json_response = {
                'animes': [],
                'actual_page': 0,
                'total_pages': 0,
                'page_has_previous': False,
                'page_has_next': False,
                'error': 'No se encontraron resultados'
            }
    else:
        json_response = {
                'animes': [],
                'actual_page': 0,
                'total_pages': 0,
                'page_has_previous': False,
                'page_has_next': False,
                'error': 'No se encontraron resultados'
            }
    return JsonResponse(json_response, safe=False, json_dumps_params={'ensure_ascii': False})

def mobile_anime_detail(request, slug):
    anime = Anime.objects.filter(slug=slug)

    if anime:
        episodios = Episodio.objects.filter(anime=anime[0]).order_by('numero')

        anime = list(anime.values(
            'nombre',
            'tipo__tipo',
            'idioma__idioma',
            'imagen',
            'agregado',
            'temporadas',
            'prox_episodio',
            'estreno',
            'sinopsis',
            'estado__estado',
            'slug'
        ))
        anime[0]['episodios'] = list(episodios.values(
            'numero',
            'slug',
            'fecha',
            'temporada',
            'ep_nombre'
        ))

        return JsonResponse(anime, safe=False, json_dumps_params={'ensure_ascii': False})
    else:
        return JsonResponse({'error': 'Anime no encontrado'})

def mobile_episode_detail(request, slug):
    episode = Episodio.objects.filter(slug=slug)

    if episode:

        embeds = list(Embed.objects.filter(episodio=episode[0]).values(
            'embed',
            'url'
        ))
        return JsonResponse(embeds, safe=False, json_dumps_params={'ensure_ascii': False})
    else:
        return JsonResponse({'error': 'Episodio no encontrado'})

def mobile_signin(request):
    username = request.GET.get('username')
    password = request.GET.get('password')
    if "@" in username:
        try:
            username = User.objects.get(email=username).username
        except User.DoesNotExist:
            return JsonResponse({'logged': False})

    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        if user.is_active:
            login(request, user)
            
            username = user.username
            email = user.email
            isAdmin = user.is_superuser
            token = Token.objects.get_or_create(user=user)
            tokenKey = token[0].key

            return JsonResponse({
                'logged': True,
                'user': {
                    'username': username,
                    'email': email,
                    'isAdmin': isAdmin,
                    'token': tokenKey
                }
            })
        else:
            return JsonResponse({
                'logged': False,
                'user': {
                    'username': "",
                    'email': "",
                    'isAdmin': "",
                    'token': ""
                }
            })
    else:
        return JsonResponse({
                'logged': False,
                'user': {
                    'username': "",
                    'email': "",
                    'isAdmin': "",
                    'token': ""
                }
            })

def streamLiveVideo(request):
    fembed_url = "https://www.fembed.com/v/xgmqxh57lrz10nd"

    fembed_url = fembed_url.replace("https://www.fembed.com/v/", "https://vanfem.com/api/source/")
    #make a post request to get the video url
    # response = requests.post(fembed_url, 
    #     headers= {
    #         'Content-Type': 'application/json',
    #         'Referer': fembed_url,
    #     }
    # )
    response = requests.post(fembed_url, 
        headers= {
            'Content-Type': 'application/json',
            'Referer': fembed_url,
        }
    )


    #obtain json from response
    json_response = response.json()
    videos = json_response['data']

    raw_video = videos[1]['file']
    #don't block the main thread while the video is being streamed

    # r = requests.get(raw_video, stream=True)
    # resp = StreamingHttpResponse(streaming_content=r, content_type="video/mp4")
    # resp['Content-Length'] = r.headers['Content-Length']
    # #allow the browser to cache the video
    # resp['Cache-Control'] = 'public, max-age=31536000'

    ## don't block the main thread while the video is being streamed
    r = requests.get(raw_video, stream=True)

    resp = StreamingHttpResponse(streaming_content=r, content_type="video/mp4")
    resp['Content-Length'] = r.headers['Content-Length']
    # #allow the browser to cache the video
    resp['Cache-Control'] = 'public, max-age=31536000'
    #allow the user to fast forward and rewind the video
    resp['Access-Control-Allow-Range'] = 'bytes'
    

    return resp

def ads_ps(request):
    return render(request, 'ps/mHv6tt.js', content_type='text/javascript')

def politica_privacidad(request):
    return render(request, 'politicas/politica_privacidad.html')

def condiciones_del_servicio(request):
    return render(request, 'politicas/condiciones.html')

def iframe_proxy(request):
    url = request.GET.get('url')
    if url:
        #bypass X-Frame-Options
        response = render(request, 'iframe_proxy.html', {'url': url})
        response['Referer'] = url
        response['X-Frame-Options'] = 'ALLOWALL'
        return response

    else:
        return HttpResponse('')

def jwplayer(request):
    url = request.GET.get('url')
    original_url = request.GET.get('url')
    player = int(request.GET.get('player'))

    if player == 1:
        response = requests.get(url)
        #parse the page
        soup = BeautifulSoup(response.text, 'html.parser')
        print(soup)
        url = re.findall('file\s*:\s*(?:\'|\")(.+?)(?:\'|\")', response.text)
        print(url[0])

        videos = [
            {
                'file': url[0],
                'label': 'HD',
                'type': 'video/mp4',
                'referer': original_url
            }
        ]
    
        if videos:
            return render(request, 'jwplayer.html', {'videos': videos})

    return HttpResponse('')


def article(request, slug):
    article = Article.objects.filter(slug=slug)
    if article:
        article = article[0]
        article.views += 1
        article.save()

        human_created = arrow.get(article.created_at).format('DD/MM/YYYY HH:mm')
        paragraphs = article.content.split('\r\n\r\n')
        
        article.paragraphs = paragraphs
        article.human_created = human_created

        return render(request, 'article.html', {'article': article})
    else:
        return handle_not_found(request, 404)