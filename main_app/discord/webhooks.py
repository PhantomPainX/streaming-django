from discord_webhook import DiscordWebhook, DiscordEmbed
from main_app.models import *
from enum import Enum

class RegistrationSources(Enum):
    WEB = 1
    MOBILE = 2

class DsWebhook:
    def __init__(self, url):
        self.url = url

    def send_new_anime(self, anime):
        webhook = DiscordWebhook(url=self.url, rate_limit_retry=True)

        if anime.sinopsis:
            embed = DiscordEmbed(title=anime.nombre, description=anime.sinopsis, color='ffd000')
        else:
            embed = DiscordEmbed(title=anime.nombre, color='ffd000')

        name = ""
        if anime.tipo.tipo == "OVA":
            name = "¡Nueva OVA por ScraperBOT!"
        elif anime.tipo.tipo == "Película":
            name = "¡Nueva Película por ScraperBOT!"
        elif anime.tipo.tipo == "Especial":
            name = "¡Nuevo Especial por ScraperBOT!"
        elif anime.tipo.tipo == "TV":
            name = "¡Nuevo Anime por ScraperBOT!"
        elif anime.tipo.tipo == "Serie":
            name = "¡Nueva Serie por ScraperBOT!"
        elif anime.tipo.tipo == "Dorama":
            name = "¡Nuevo Dorama por ScraperBOT!"

        direct_url = 'http://127.0.0.1' + anime.get_absolute_url()
        embed.set_author(name=name, url=direct_url, icon_url="https://www.ecured.cu/images/f/f5/Bot.jpg")

        # set image
        # embed.set_image(url='http://127.0.0.1/media/portadas/3736.webp')

        embed.set_thumbnail(url="http://127.0.0.1/media/" + str(anime.imagen))

        # set footer
        # embed.set_footer(text='Embed Footer Text', icon_url='http://127.0.0.1/media/portadas/3780.webp')
        embed.set_timestamp()

        embed.add_embed_field(name='Año', value=anime.estreno)
        embed.add_embed_field(name='Idioma', value=anime.idioma.idioma)
        embed.add_embed_field(name='Estado', value=anime.estado.estado)
        embed.add_embed_field(name='Tipo', value=anime.tipo.tipo)
        if anime.generos:
            generos = ', '.join([str(genero) for genero in anime.generos.all()])
            embed.add_embed_field(name='Géneros', value=generos, inline=False)

        embed.add_embed_field(name="URL", value=direct_url, inline=False)

        # add embed object to webhook
        webhook.add_embed(embed)
        webhook.execute()

    def send_new_episode(self, episode):
        webhook = DiscordWebhook(url=self.url, rate_limit_retry=True)

        embed = DiscordEmbed(title=episode.anime.nombre + " Episodio "+ str(episode.numero), color='009dff')

        name = "¡Nuevo episodio por ScraperBOT!"

        direct_url = 'http://127.0.0.1' + episode.get_absolute_url()
        embed.set_author(name=name, url=direct_url, icon_url="https://www.ecured.cu/images/f/f5/Bot.jpg")

        # set image
        # embed.set_image(url='http://127.0.0.1/media/portadas/3736.webp')

        embed.set_thumbnail(url="http://127.0.0.1/media/" + str(episode.anime.imagen))

        # set footer
        # embed.set_footer(text='Embed Footer Text', icon_url='http://127.0.0.1/media/portadas/3780.webp')
        embed.set_timestamp()

        embed.add_embed_field(name="URL", value=direct_url, inline=False)

        webhook.add_embed(embed)
        webhook.execute()

    def send_new_user(self, user, registration_type):
        webhook = DiscordWebhook(url=self.url, rate_limit_retry=True)

        embed = DiscordEmbed(title="¡Nuevo usuario registrado!", color='ffd000')

        user_extra = UserExtra.objects.get(user=user)
        embed.set_thumbnail(url="http://127.0.0.1/media/" + str(user_extra.avatar))

        embed.set_timestamp()

        embed.add_embed_field(name="Nombre de usuario", value=user.username, inline=False)
        # if user.first_name:
        #     embed.add_embed_field(name="Nombre", value=user.first_name, inline=False)
        # if user.last_name:
        #     embed.add_embed_field(name="Apellido", value=user.last_name, inline=False)

        # if registration_type == RegistrationSources.WEB:
        #     embed.add_embed_field(name="Registrado desde", value="Página web", inline=False)
        # elif registration_type == RegistrationSources.MOBILE:
        #     embed.add_embed_field(name="Registrado desde", value="Aplicación móvil", inline=False)

        webhook.add_embed(embed)
        webhook.execute()