from apscheduler.schedulers.background import BackgroundScheduler
import json, requests, os
from bs4 import BeautifulSoup
from main_app.models import *
from django.conf import settings
from main_app import emails
from main_app.notifications import android_all_notification

embeds_intentos_maximos = 10
embeds_minimos = 3
embeds_maximos = 6
page_root = "https://tioanime.com"
first_page = "/directorio"
carpeta_portadas = settings.MEDIA_ROOT + '/portadas/'

def str_fix(s):
    return s.replace('\n', '')

def obtener_info_anime(animes):
    animes_id = []
    for anime in animes:
        response = requests.get(anime)
        soup = BeautifulSoup(response.text, 'html.parser')

        #titulo
        anime_title = str_fix(soup.find('h1', class_='title').text)
        #print(anime_title)

        div_thumb = soup.find('div', class_='thumb')
        url_foto = str_fix(page_root + div_thumb.img.get('src'))

        
        totalFiles = 0
        if os.path.exists(carpeta_portadas):
            for base, dirs, files in os.walk(carpeta_portadas):
                for Files in files:
                    totalFiles += 1
        else:
            print("No existe la carpeta de portadas")


        foto = requests.get(url_foto)
        foto_anime = open(carpeta_portadas+"{}".format(totalFiles+1)+".webp", 'wb')
        foto_anime.write(foto.content)
        foto_anime.close()

        #print("Fue agregada la foto {}.png" .format(totalFiles+1))
        imagen = "portadas/{}.webp" .format(totalFiles+1)

        anime_tipo = str_fix(soup.find('span', class_='anime-type-peli').text)

        validar_anime_tipo = Tipo.objects.filter(tipo=anime_tipo).exists()
        if not validar_anime_tipo:
            tipo = Tipo(tipo=anime_tipo)
            tipo.save()


        try:
            anime_estreno = str_fix(soup.find('span', class_='year').text)
        except:
            anime_estreno = "1900"

        anime_sinopsis = str_fix(soup.find('p', class_='sinopsis').text)

        estado = str_fix(soup.find('a', class_='status').text)
        validar_estado = Estado.objects.filter(estado=estado).exists()
        if not validar_estado:
            estado = Estado(estado=estado)
            estado.save()

        slug = str(response.url)
        slug = slug.replace("https://tioanime.com/anime/", "")

        try:
            proximo_capitulo = str_fix(soup.find('span', class_='next-episode').text)
            proximo_capitulo = proximo_capitulo.replace('Proximo episodio: ', '')
        except:
            proximo_capitulo = ""

        Anime.objects.create(nombre=anime_title,tipo=Tipo.objects.get(tipo=anime_tipo), prox_episodio=proximo_capitulo,imagen=imagen,estreno=int(anime_estreno),sinopsis=anime_sinopsis,estado=Estado.objects.get(estado=estado),slug=slug)

        anime_id = Anime.objects.get(nombre=anime_title, sinopsis=anime_sinopsis)
        #Generos
        generos = list()
        p_generos = soup.find('p', class_='genres')
        gens = p_generos.find_all('span')

        for genero in gens:
            # generos.append(str_fix(genero.text))
            validar_genero = Genero.objects.filter(genero=str_fix(genero.text)).exists()
            if not validar_genero:
                genero_nuevo = Genero(genero=str_fix(genero.text))
                genero_nuevo.save()
            
            genero_id = Genero.objects.get(genero=str_fix(genero.text))
            Anime_Genero.objects.create(anime=anime_id,categoria=genero_id)

        #No se crearan capitulos en esta parte

        try:
            scripts = soup.find_all('script')
            episodes_script = str(scripts[-1]).split()

            for episode in range(len(episodes_script)):
                if "1];" in episodes_script[episode]:
                    ep_n_script = episodes_script[episode]

            ep_script_fix = ep_n_script.replace(';', '').replace('[', '').replace(']', '')
            ep_script_fix = ep_script_fix.split(',')
            ep_script_fix.reverse()

            n_ep = len(ep_script_fix)+1

            
            anime_url = str(response.url)

            url_for_episodes = anime_url.replace('/anime/', '/ver/') + '-'

            for it in range(1,n_ep):
                episodio = url_for_episodes + str(it)
                
                response_ep = requests.get(episodio)
                soup_ep = BeautifulSoup(response_ep.text, 'html.parser')

                Episodio.objects.create(anime=anime_id,numero=it, slug=slug+"-"+str(it))
                episodio_id = Episodio.objects.get(anime=anime_id, numero=it)
                #print("Episodio {} Agregado Correctamente" .format(it))


                try:
                    scripts = soup_ep.find_all('script')

                    for script in scripts:
                        if "var videos" in str(script):
                            embed_script = str(script)
                            break

                    script_embeds = embed_script.replace('<script>', '').replace('</script>', '').replace(' ','').replace('\t','')
                    #print(response.url)
                    script_embeds = script_embeds.replace(';tEpisode();ady(function(){', '')
                    script_embeds = '{' + '"embeds"' + ':' + script_embeds[12:script_embeds.find('];')] + ']' + '}'
                    #print(script_embeds)
                    json_embeds = json.loads(script_embeds)

                    for embed in range(len(json_embeds['embeds'])):
                        
                        video = json_embeds['embeds'][embed][1]

                        if "fembed" in video:
                            embed = "Fembed"
                        elif "mega" in video:
                            embed = "Mega"
                        elif "ok.ru" in video:
                            embed = "Okru"
                        elif "yourupload" in video:
                            embed = "YourUpload"
                        elif "mail.ru" in video:
                            embed = "MailRu"
                        elif "hqq" in video:
                            embed = "HQQ"
                        else:
                            embed = "Unknown"

                        Embed.objects.create(embed=embed,url=video,episodio=episodio_id)
                        #print("Embed Agregado Correctamente")
                except:
                    pass

        except:
            print("No hay episodios")

        animes_id.append(anime_id)

    return animes_id

def obtener_animes_faltantes():
    url = page_root + first_page
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    articulos = soup.find_all('article', class_='anime')
    animes = []
    #Se validan los animes que ya estan en la base de datos
    for articulo in articulos:
        #Se valida si el anime ya esta en la base de datos
        titulo_anime = articulo.find('h3', class_='title').text
        validacion = Anime.objects.filter(nombre=titulo_anime).exists()
        if validacion:
            anime = Anime.objects.get(nombre=titulo_anime)
            if not anime.scraping:
                print("El anime {} no esta activo para scraping" .format(anime.nombre))
                continue
        #Si no esta en la base de datos se agrega
        if not validacion:
            animes.append(page_root + articulo.find('a')['href'])

    #Se da vuelta la lista de links para que agregue del ultimo al primero
    animes.reverse()
    return animes

def obtener_estado_anime(url_anime):
    response = requests.get(url_anime)
    soup = BeautifulSoup(response.text, 'html.parser')
    estado = str_fix(soup.find('a', class_='status').text)

    try:
        proximo_capitulo = str_fix(soup.find('span', class_='next-episode').text)
        proximo_capitulo = proximo_capitulo.replace('Proximo episodio: ', '')
    except:
        proximo_capitulo = ""

    validar_estado = Estado.objects.filter(estado=estado).exists()
    if not validar_estado:
        estado = Estado(estado=estado)
        estado.save()

    anime_id = Anime.objects.get(slug=url_anime.replace("https://tioanime.com/anime/", ""))
    estado_id = Estado.objects.get(estado=estado)
    if anime_id.estado != estado_id:
        print("{} cambio de estado a {}" .format(anime_id.nombre, estado_id.estado))
        anime_id.estado = estado_id
        anime_id.save()

    #Activar esto cuando el atributo proximo capitulo este disponible
    anime_id.prox_episodio = proximo_capitulo
    anime_id.estado = estado_id
    anime_id.save()


def obtener_capitulos_faltantes():
    url = page_root
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    articulos = soup.find_all('article', class_='episode')
    episodios = []
    #Se validan los animes que ya estan en la base de datos

    for articulo in articulos:
        #Se valida si el anime ya esta en la base de datos
        slug_capitulo = articulo.find('a')['href'].replace('/ver/', '')
        last_index = slug_capitulo.rfind('-')
        numero_capitulo = int(slug_capitulo[last_index+1:])
        slug_anime = slug_capitulo[:last_index]

        validar_anime = Anime.objects.filter(slug=slug_anime).exists()

        if validar_anime:
            anime = Anime.objects.get(slug=slug_anime)
            if not anime.scraping:
                print("El anime {} no esta activo para scraping" .format(anime.nombre))
                continue
            
            verificar_estado_anime = False
            anime_id = Anime.objects.get(slug=slug_anime)

            for i in range(1,numero_capitulo+1):
                validar_episodio = Episodio.objects.filter(anime=anime_id, numero=i).exists()
                if not validar_episodio:
                    url_del_episodio = page_root + '/ver/' + slug_anime + "-" + str(i)
                    if url_del_episodio not in episodios:
                        episodios.append(url_del_episodio)
                        verificar_estado_anime = True

            #Se verifica el estado del anime y la fecha del proximo capitulo
            if verificar_estado_anime:
                # print("Se esta verificando el estado del anime {}" .format(anime_id.nombre))
                obtener_estado_anime(page_root+'/anime/'+slug_anime)
            verificar_estado_anime = False

            # validacion = Episodio.objects.filter(slug=slug_capitulo).exists()
            # #Si no esta en la base de datos se agrega
            # if not validacion:
            #     episodios.append(page_root + articulo.find('a')['href'])
    # print(episodios)
    return episodios

def agregar_capitulos_faltantes(episodios):
    capitulos_id = []
    for episodio in episodios:
        response = requests.get(episodio)
        soup = BeautifulSoup(response.text, 'html.parser')

        try:

            #print(str(response.url))

            scripts = soup.find_all('script')

            for script in scripts:
                if "var videos" in str(script):
                    embed_script = str(script)
                    break

            script_embeds = embed_script.replace('<script>', '').replace('</script>', '').replace(' ','').replace('\t','')
            #print(response.url)
            script_embeds = script_embeds.replace(';tEpisode();ady(function(){', '')
            script_embeds = '{' + '"embeds"' + ':' + script_embeds[12:script_embeds.find('];')] + ']' + '}'
            #print(script_embeds)
            json_embeds = json.loads(script_embeds)

            #Si tiene mas de 5 embed links
            if len(json_embeds['embeds']) >= embeds_minimos:

                slug_capitulo = episodio.replace(page_root+'/ver/', '')
                last_index = slug_capitulo.rfind('-')
                numero_capitulo = int(slug_capitulo[last_index+1:])
                slug_anime = slug_capitulo[:last_index]

                anime_id = Anime.objects.get(slug=slug_anime)
                Episodio.objects.create(anime=anime_id,numero=numero_capitulo, slug=slug_capitulo)
                episodio_id = Episodio.objects.get(anime=anime_id, numero=numero_capitulo)
                #print("{} EP {} Agregado Correctamente".format(anime_id.nombre, numero_capitulo))

                #print("Este capitulo tiene {} embeds" .format(len(json_embeds['embeds'])))

                for embed in range(len(json_embeds['embeds'])):
                    
                    video = json_embeds['embeds'][embed][1]

                    if "fembed" in video:
                        embed = "Fembed"
                    elif "mega" in video:
                        embed = "Mega"
                    elif "ok.ru" in video:
                        embed = "Okru"
                    elif "yourupload" in video:
                        embed = "YourUpload"
                    elif "mail.ru" in video:
                        embed = "MailRu"
                    elif "hqq" in video:
                        embed = "HQQ"
                    elif "streamtape" in video:
                        embed = "StreamTape"
                    elif "mp4upload" in video:
                        embed = "Mp4Upload"

                    else:
                        embed = "Unknown"

                    Embed.objects.create(embed=embed,url=video,episodio=episodio_id)
                
                capitulos_id.append(episodio_id)

                embeds_del_episodio = Embed.objects.filter(episodio=episodio_id).count()
                if embeds_del_episodio < embeds_maximos:
                    EmbedsPendiente.objects.create(episodio=episodio_id, url=response.url, intentos=0)
                    #print("{} EP {} Agregado a la lista de embeds pendientes".format(anime_id.nombre, numero_capitulo))

            else:
                print("Este capitulo no tiene mas de 5 embeds, saltando...")

        except(Exception) as e:
            print("Error al agregar el capitulo {}".format(episodio))
            print(e)
    return capitulos_id

def obtener_embeds_pendientes():
    #Se obtienen todos los embeds pendientes
    embeds_pendientes = EmbedsPendiente.objects.all()
    #Se recorren esos embeds
    for embed_pendiente in embeds_pendientes:
        #print(embed_pendiente.episodio)
        #Si los intentos del embed son menores a los intentos maximos, se intentara obtener el embed
        if embed_pendiente.intentos < embeds_intentos_maximos:
            #Usamos try para ver si hay un error al obtener los embeds
            try:
                #Se obtiene la pagina del embed y se guarda su html en soup con bs4
                response = requests.get(embed_pendiente.url)
                soup = BeautifulSoup(response.text, 'html.parser')

                #Comienzo de la obtencion de los embeds en el script que hay en la pagina
                scripts = soup.find_all('script')

                for script in scripts:
                    if "var videos" in str(script):
                        embed_script = str(script)
                        break

                script_embeds = embed_script.replace('<script>', '').replace('</script>', '').replace(' ','').replace('\t','')
                
                script_embeds = script_embeds.replace(';tEpisode();ady(function(){', '')
                script_embeds = '{' + '"embeds"' + ':' + script_embeds[12:script_embeds.find('];')] + ']' + '}'
                
                json_embeds = json.loads(script_embeds)
                #Fin de la obtencion de los embeds, json_embeds lo contiene como un diccionario con la llave ['embeds']

                #Se cuentan los embeds que tiene el episodio
                #print("embeds del episodio, linea 373")
                embeds_del_episodio = Embed.objects.filter(episodio=embed_pendiente.episodio).count()

                #Si el numero de embeds sacados de la pagina es mayor a los embeds que tiene el episodio en la BD
                #Se ejecuta el codigo para agregar los embeds
                if len(json_embeds['embeds']) > embeds_del_episodio:

                    #Se recorre la lista de los links
                    for embed in range(len(json_embeds['embeds'])):
                        
                        #Aqui se obtiene la url del embed
                        video = json_embeds['embeds'][embed][1]

                        #Se obtiene el nombre del embed
                        if "fembed" in video:
                            embed = "Fembed"
                        elif "mega" in video:
                            embed = "Mega"
                        elif "ok.ru" in video:
                            embed = "Okru"
                        elif "yourupload" in video:
                            embed = "YourUpload"
                        elif "mail.ru" in video:
                            embed = "MailRu"
                        elif "hqq" in video:
                            embed = "HQQ"
                        elif "streamtape" in video:
                            embed = "StreamTape"
                        elif "mp4upload" in video:
                            embed = "Mp4Upload"
                        else:
                            embed = "Unknown"

                        #Se comprueba de que el embed ya no este en la BD, si no esta se agrega
                        #print("if embed no existe linea 307")
                        if not Embed.objects.filter(episodio=embed_pendiente.episodio, url=video).exists():
                            Embed.objects.create(embed=embed,url=video,episodio=embed_pendiente.episodio)
                    
                #Ahora cuenta denuevo los embeds del episodio
                #print("embeds del episodio, linea 412")
                embeds_del_episodio = Embed.objects.filter(episodio=embed_pendiente.episodio).count()
                #Si los embeds del episodio son iguales o mayores a los embeds maximos, 
                # se elimina los embeds pendientes del episodio
                if embeds_del_episodio >= embeds_maximos:
                    embed_pendiente.delete()
                #Si por el contrario son menores, se aumenta el intento a 1 en el embed pendiente
                else:
                    embed_pendiente.intentos = embed_pendiente.intentos + 1
                    embed_pendiente.save()

            except(Exception) as e:
                print(e)

        #Si los intentos son mayores o igual a los intentos maximos, se elimina el embed pendiente
        elif embed_pendiente.intentos >= embeds_intentos_maximos:
            embed_pendiente.delete()
            
            

def inicio_actualizacion():
    animes_id = []
    capitulos_id = []
    #Primero se ejecuta la funcion para ver si hay animes nuevos
    #Se obtienen los animes que no estan en la base de datos
    animes = obtener_animes_faltantes()

    #Si hay hay animes que no estan en la base de datos se agregaran los animes
    if animes:
        print("Hay {} animes faltantes, agregando...".format(len(animes)))
        animes_id = obtener_info_anime(animes)
        print("Actualizacion completada")
    else:
        print("No hay animes faltantes")

    episodios = obtener_capitulos_faltantes()
    if episodios:
        print("Hay {} episodios faltantes, agregando...".format(len(episodios)))
        capitulos_id = agregar_capitulos_faltantes(episodios)
        print("Actualizacion completada")
    else:
        print("No hay episodios faltantes")

    obtener_embeds_pendientes()

    # if animes_id:
    #     #si hay 1 anime agregado, envia notificacion push a todos los usuarios
    #     if len(animes_id) == 1:
    #         image = "http://127.0.0.1/media/" + str(animes_id[0].imagen)
    #         print(image)
    #         android_all_notification(
    #             title="¡Nuevo en el catalogo!",
    #             message="Se ha agregado {}".format(animes_id[0].nombre),
    #             image=image,
    #             extra={
    #                 "type": "anime",
    #                 "id": animes_id[0].id,
    #                 "image": animes_id[0].imagen
    #             }
    #         )
    #     #si hay mas de 1 anime agregado, envia notificacion push a todos los usuarios
    #     else:

    #         #crea un string con los nombres de los animes agregados
    #         image = "http://127.0.0.1/media/" + str(animes_id[0].imagen)
    #         animes_string = ""
    #         for anime in animes_id:
    #             animes_string += anime.nombre + ", "

    #         animes_string = animes_string[:-2]

    #         android_all_notification(
    #             title="¡Nuevos en el catalogo!",
    #             message=animes_string,
    #             image=image,
    #             extra={
    #                 "type": "animes"
    #             }
    #         )

    # if capitulos_id:
    #     #si hay 1 episodio agregado, envia notificacion push a todos los usuarios
    #     if len(capitulos_id) == 1:
    #         image = "http://127.0.0.1/media/" + str(capitulos_id[0].anime.imagen)
    #         android_all_notification(
    #             title="¡Nuevo Episodio!",
    #             message="Se ha agregado el episodio {} de {}".format(capitulos_id[0].numero, capitulos_id[0].anime.nombre),
    #             image=image,
    #             extra={
    #                 "type": "episode",
    #                 "id": capitulos_id[0].id,
    #                 "image": image
    #             }
    #         )
    #     #si hay mas de 1 episodio agregado, envia notificacion push a todos los usuarios
    #     else:

    #         #crea un string con los nombres de los episodios agregados
    #         image = "http://127.0.0.1/media/" + str(capitulos_id[0].anime.imagen)
    #         capitulos_string = ""
    #         for capitulo in capitulos_id:
    #             capitulos_string += "Episodio {} de {}, ".format(capitulo.numero, capitulo.anime.nombre)

    #         capitulos_string = capitulos_string[:-2]

    #         android_all_notification(
    #             title="¡Nuevos Episodios!",
    #             message=capitulos_string,
    #             image=image,
    #             extra={
    #                 "type": "episode"
    #             }
    #         )

    if settings.ENVIO_DE_EMAILS:
        if animes_id or capitulos_id:
            emails.enviar_email_actualizacion(animes_id,capitulos_id)

    print("Se termino la actualizacion")

    

def start():
    #inicio_actualizacion()
    print("Iniciando Scheluder...")
    scheduler = BackgroundScheduler(timezone='America/Argentina/Buenos_Aires')
    scheduler.add_job(inicio_actualizacion, 'interval', minutes=30, id="inicio_actualizacion", replace_existing=True)
    scheduler.start()
