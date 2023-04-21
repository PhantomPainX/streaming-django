from django.contrib.auth.models import User, Group
from .models import *
from rest_framework import serializers
from spanlp.palabrota import Palabrota
from rest_framework.authtoken.models import Token
#Import allauth models
from allauth.account.models import EmailAddress
#Notifications
from push_notifications.models import GCMDevice

palabrota = Palabrota()


class PublicUserSerializer(serializers.ModelSerializer):

    user_extra = serializers.SerializerMethodField()

    def get_user_extra(self, obj):
        user_extra, created = UserExtra.objects.get_or_create(user=obj)
        return UserExtraSerializer(user_extra).data

    groups = serializers.SerializerMethodField()

    def get_groups(self, obj):
        return obj.groups.values_list('name', flat=True)

    reports = serializers.SerializerMethodField()
    def get_reports(self, obj):
        return UserReport.objects.filter(reported_user=obj).count()

    created_with_google = serializers.SerializerMethodField()
    def get_created_with_google(self, obj):
        #check if user id is in google user id list
        google_user_id_list = EmailAddress.objects.filter(user=obj).values_list('user_id', flat=True)
        if obj.id in google_user_id_list:
            return True
        else:
            return False

    class Meta:
        model = User
        fields = [
            'id', 
            'username',
            'email',
            'first_name',
            'last_name',
            'is_active',
            'is_staff',
            'is_superuser',
            'date_joined',
            'last_login',
            'groups',
            'user_extra',
            'reports',
            'created_with_google'
        ]


class UserExtraSerializer(serializers.ModelSerializer):

    #user has read only
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    ban_admin = PublicUserSerializer(read_only=True)

    class Meta:
        model = UserExtra
        fields = (
            'id', 
            'user', 
            'avatar', 
            'created_at', 
            'updated_at', 
            'thirteen_age_coppa_compliant', 
            'ban_reason',
            'ban_date',
            'ban_admin'
        )

class PrivateUserSerializer(serializers.ModelSerializer):

    token = serializers.SerializerMethodField()

    def get_token(self, obj):
        token, created = Token.objects.get_or_create(user=obj)
        return token.key

    user_extra = serializers.SerializerMethodField()

    def get_user_extra(self, obj):
        user_extra, created = UserExtra.objects.get_or_create(user=obj)
        return UserExtraSerializer(user_extra).data

    groups = serializers.SerializerMethodField()
    def get_groups(self, obj):
        return obj.groups.values_list('name', flat=True)

    created_with_google = serializers.SerializerMethodField()
    def get_created_with_google(self, obj):
        #check if user id is in google user id list
        google_user_id_list = EmailAddress.objects.filter(user=obj).values_list('user_id', flat=True)
        if obj.id in google_user_id_list:
            return True
        else:
            return False

    reports = serializers.SerializerMethodField()
    def get_reports(self, obj):
        return UserReport.objects.filter(reported_user=obj).count()

    class Meta:
        model = User
        fields = [
            'id', 
            'username',  
            'email', 
            'first_name',
            'last_name',
            'token',
            'is_active',
            'is_staff',
            'is_superuser',
            'date_joined',
            'last_login',
            'created_with_google',
            'groups',
            'user_extra',
            'reports'
        ]


class AnimeSimpleSerializer(serializers.ModelSerializer):

    tipo = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field='tipo'
    )

    idioma = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field='idioma'
    )

    generos = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='genero'
    )

    class Meta:
        model = Anime
        fields = [
            'id',
            'nombre',
            'tipo',
            'idioma',
            'imagen',
            'comments_disabled',
            'agregado',
            'temporadas',
            'prox_episodio',
            'generos',
            'estreno',
            'sinopsis',
            'estado',
            'slug',
            'animefenix_slug',
        ]

class AnimeSerializer(serializers.ModelSerializer):

    tipo = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field='tipo'
    )

    idioma = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field='idioma'
    )

    generos = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='genero'
    )

    id = serializers.IntegerField(read_only=True)

    estado = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field='estado'
    )

    # agrega el campo del total de episodios
    episodios = serializers.SerializerMethodField(read_only=True)

    def get_episodios(self, obj):
        objects = Episodio.objects.filter(anime=obj.id).values()
        user = self.context['request'].user
        for object in objects:
            object['comments_disabled'] = obj.comments_disabled
            if user.is_authenticated:
                try:
                    time_seen = SeenEpisodeTime.objects.get(user=user, episode__id=object['id'])
                    object['seconds_seen'] = {
                        "seconds": time_seen.seconds,
                        "total_seconds": time_seen.total_seconds,
                        "created_at": time_seen.created_at,
                        "updated_at": time_seen.updated_at
                    }
                except:
                    object['seconds_seen'] = None
            else:
                object['seconds_seen'] = None
        return objects

    image_thumbnail = serializers.SerializerMethodField(read_only=True)
    def get_image_thumbnail(self, obj):
        return obj.image_thumbnail.url
 
    nombre = serializers.CharField(read_only=True)
    imagen = serializers.ImageField(read_only=True)
    temporadas = serializers.IntegerField(read_only=True)
    prox_episodio = serializers.CharField(read_only=True)
    estreno = serializers.CharField(read_only=True)
    sinopsis = serializers.CharField(read_only=True)
    slug = serializers.CharField(read_only=True)
    animefenix_slug = serializers.CharField(read_only=True)

    class Meta:
        model = Anime
        fields = [
            'id',
            'nombre',
            'tipo',
            'idioma',
            'imagen',
            'image_thumbnail',
            'comments_disabled',
            'agregado',
            'temporadas',
            'prox_episodio',
            'generos',
            'estreno',
            'sinopsis',
            'estado',
            'slug',
            'animefenix_slug',
            'episodios',
        ]

class EpisodeSerializer(serializers.ModelSerializer):

    anime = AnimeSerializer(read_only=True)
    temporada = serializers.CharField(read_only=True)
    ep_nombre = serializers.CharField(read_only=True)
    numero = serializers.IntegerField(read_only=True)
    slug = serializers.CharField(read_only=True)

    comments_disabled = serializers.SerializerMethodField(read_only=True)

    def get_comments_disabled(self, obj):
        return obj.anime.comments_disabled
    
    seconds_seen = serializers.SerializerMethodField(read_only=True)
    def get_seconds_seen(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            try:
                time_seen = SeenEpisodeTime.objects.get(user=user, episode=obj)
                return {
                    'seconds': time_seen.seconds,
                    'total_seconds': time_seen.total_seconds,
                    'created_at': time_seen.created_at,
                    'updated_at': time_seen.updated_at
                }
            except:
                return None
        else:
            return None

    class Meta:
        model = Episodio
        fields = [
            'id',
            'anime',
            'fecha',
            'temporada',
            'ep_nombre',
            'numero',
            'comments_disabled',
            'slug',
            'seconds_seen'
        ]

class EmbedSerializer(serializers.ModelSerializer):
    
        class Meta:
            model = Embed
            fields = [
                'id',
                'episodio',
                'embed',
                'url'
            ]

class EpisodeSimpleSerializer(serializers.ModelSerializer):
    anime = AnimeSimpleSerializer(read_only=True)
    temporada = serializers.CharField(read_only=True)
    ep_nombre = serializers.CharField(read_only=True)
    numero = serializers.IntegerField(read_only=True)
    slug = serializers.CharField(read_only=True)

    comments_disabled = serializers.SerializerMethodField(read_only=True)

    def get_comments_disabled(self, obj):
        return obj.anime.comments_disabled

    class Meta:
        model = Episodio
        fields = [
            'id',
            'anime',
            'fecha',
            'temporada',
            'ep_nombre',
            'numero',
            'comments_disabled',
            'slug'
        ]

class AnimesFavoritosSerializer(serializers.ModelSerializer):

    #trae el objeto del anime completo, tambien se podra hacer con el id
    anime = AnimeSerializer(read_only=True)

    usuario = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field='username'
    )

    class Meta:
        model = AnimesFavorito
        fields = [
            'id',
            'anime',
            'usuario',
            'fecha'
        ]

    def create(self, validated_data):
        anime = validated_data['anime']
        usuario = self.context['request'].user
        animes_favoritos, created = AnimesFavorito.objects.get_or_create(
            anime=anime,
            usuario=usuario
        )
        return animes_favoritos


class EpisodiosVistosSerializer(serializers.ModelSerializer):

    numero = serializers.SerializerMethodField(read_only=True)

    def get_numero(self, obj):
        return int(Episodio.objects.filter(id=obj.episodio.id).values('numero')[0]['numero'])

    class Meta:
        model = EpisodiosVisto
        fields = [
            'id',
            'episodio',
            'usuario',
            'fecha',
            'numero'
        ]

class AnimeCommentsSerializer(serializers.ModelSerializer):

    user = PublicUserSerializer(read_only=True)
    anime_detail = serializers.SerializerMethodField(read_only=True)
    def get_anime_detail(self, obj):
        return AnimeSimpleSerializer(obj.anime).data
    reports = serializers.SerializerMethodField(read_only=True)
    def get_reports(self, obj):
        return AnimeCommentReport.objects.filter(comment=obj.id).count()

    replies = serializers.SerializerMethodField(read_only=True)
    def get_replies(self, obj):
        return AnimeCommentsReply.objects.filter(comment=obj.id).count()
        
    class Meta:
        model = AnimeComment
        fields = [
            'id',
            'anime',
            'anime_detail',
            'user',
            'spoiler',
            'reports',
            'created_at',
            'updated_at',
            'comment',
            'replies',
            'notifications'
        ]

class AnimeCommentRepliesSerializer(serializers.ModelSerializer):

    user = PublicUserSerializer(read_only=True)
    reports = serializers.SerializerMethodField(read_only=True)

    def get_reports(self, obj):
        return AnimeReplyReport.objects.filter(reply=obj.id).count()
        
    class Meta:
        model = AnimeCommentsReply
        fields = [
            'id',
            # 'anime_detail',
            'user',
            'comment',
            'spoiler',
            'reports',
            'created_at',
            'updated_at',
            'reply'
        ]

class EpisodeCommentsSerializer(serializers.ModelSerializer):

    user = PublicUserSerializer(read_only=True)

    episode_detail = serializers.SerializerMethodField(read_only=True)

    def get_episode_detail(self, obj):
        return EpisodeSimpleSerializer(obj.episode).data

    reports = serializers.SerializerMethodField(read_only=True)

    def get_reports(self, obj):
        return EpisodeCommentReport.objects.filter(comment=obj.id).count()

    replies = serializers.SerializerMethodField(read_only=True)
    def get_replies(self, obj):
        return EpisodeCommentsReply.objects.filter(comment=obj.id).count()
        
    class Meta:
        model = EpisodeComment
        fields = [
            'id',
            'episode',
            'episode_detail',
            'user',
            'spoiler',
            'reports',   
            'created_at',
            'updated_at',
            'comment',
            'replies',
            'notifications' # Si el usuario recibe notificaciones por este comentario
        ]

class EpisodeCommentRepliesSerializer(serializers.ModelSerializer):

    user = PublicUserSerializer(read_only=True)
    reports = serializers.SerializerMethodField(read_only=True)

    def get_reports(self, obj):
        return EpisodeReplyReport.objects.filter(reply=obj.id).count()
        
    class Meta:
        model = EpisodeCommentsReply
        fields = [
            'id',
            # 'anime_detail',
            'user',
            'comment',
            'spoiler',
            'reports',
            'created_at',
            'updated_at',
            'reply'
        ]


class AnimeCommentReportSerializer(serializers.ModelSerializer):

    user = PublicUserSerializer(read_only=True)

    class Meta:
        model = AnimeCommentReport
        fields = [
            'id',
            'comment',
            'user',
            'kind',
            'created_at'
        ]

class AnimeCommentReplyReportSerializer(serializers.ModelSerializer):

    user = PublicUserSerializer(read_only=True)

    class Meta:
        model = AnimeReplyReport
        fields = [
            'id',
            'reply',
            'user',
            'kind',
            'created_at'
        ]

class EpisodeCommentReportSerializer(serializers.ModelSerializer):

    user = PublicUserSerializer(read_only=True)

    class Meta:
        model = EpisodeCommentReport
        fields = [
            'id',
            'comment',
            'user',
            'kind',
            'created_at'
        ]

class EpisodeCommentReplyReportSerializer(serializers.ModelSerializer):

    user = PublicUserSerializer(read_only=True)

    class Meta:
        model = EpisodeReplyReport
        fields = [
            'id',
            'reply',
            'user',
            'kind',
            'created_at'
        ]

class ReportKindSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReportKind
        fields = [
            'id',
            'kind',
            'sensitive'
        ]

class GCMDeviceSerializer(serializers.ModelSerializer):

    user = PublicUserSerializer(read_only=True)

    class Meta:
        model = GCMDevice
        fields = [
            'id',
            'name',
            'user',
            'device_id',
            'registration_id',
            'cloud_message_type',
            'active'
        ]

class GenreSerializer(serializers.ModelSerializer):

    class Meta:
        model = Genero
        fields = [
            'id',
            'genero',
            'slug'
        ]

class TypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tipo
        fields = [
            'id',
            'tipo',
            'slug'
        ]

class StatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = Estado
        fields = [
            'id',
            'estado',
            'slug'
        ]

class LanguageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Idioma
        fields = [
            'id',
            'idioma',
            'thumbnail',
            'slug'
        ]

class UserReportSerializer(serializers.ModelSerializer):

    reporter_user = PublicUserSerializer(read_only=True)

    class Meta:
        model = UserReport
        fields = [
            'id',
            'reported_user',
            'reporter_user',
            'reason',
            'created_at',
            'updated_at'
        ]

class UserBlockSerializer(serializers.ModelSerializer):

    user = serializers.PrimaryKeyRelatedField(read_only=True)

    blocked_user_detail = serializers.SerializerMethodField(read_only=True)
    def get_blocked_user_detail(self, obj):
        return PublicUserSerializer(obj.blocked_user).data

    class Meta:
        model = UserBlock
        fields = [
            'id',
            'user',
            'blocked_user',
            'blocked_user_detail',
            'created_at',
            'updated_at'
        ]

class SeenEpisodeTimeSerializer(serializers.ModelSerializer):

    user = PublicUserSerializer(read_only=True)
    
    class Meta:
        model = SeenEpisodeTime
        fields = [
            'id',
            'user',
            'episode',
            'seconds',
            'total_seconds',
            'created_at',
            'updated_at'
        ]