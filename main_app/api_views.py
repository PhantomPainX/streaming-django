from django.contrib.auth.models import User
from .models import Anime, EpisodiosVisto, Episodio
from rest_framework import viewsets, permissions, filters, status, generics
from .serializers import *
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import login, authenticate
from django.conf import settings

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect

from rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter

from main_app.notifications import android_all_notification, android_user_notification
import json, jsbeautifier, datetime, poe

from django.db.models import OuterRef, Subquery, Max, Q, When, Exists, F, Case, BooleanField

from main_app.discord.webhooks import DsWebhook, RegistrationSources

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the blog.
        return obj.user == request.user

# REST FRAMEWORK
class UserViewSet(viewsets.ModelViewSet):
    serializer_class =  PublicUserSerializer
    http_method_names = ['get', 'options']
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['is_active', 'is_staff', 'is_superuser']
    search_fields = ['username', 'email']
    ordering_fields = ['date_joined', 'last_login']
    permission_classes = [permissions.IsAuthenticated]

    queryset = User.objects.all()

    def get_queryset(self):
        #if user-extra-last-updated in params
        # si el usuario es staff o tiene el grupo de moderadores
        if self.request.user.is_staff or self.request.user.groups.filter(name='Moderator').exists():
            if 'profile-last-updated' in self.request.query_params:
                return User.objects.all().order_by('-userextra__updated_at')

            # otro filtro por numero de reportes en UserReports model de más a menos
            elif 'more-reports' in self.request.query_params:
                return User.objects.all().order_by('-userreport__reports')
            elif 'less-reports' in self.request.query_params:
                return User.objects.all().order_by('userreport__reports')
            else:
                return User.objects.all()
        else:
            return User.objects.none()
            

class UserPrivateDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PrivateUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        user = request.user
        if user.is_staff:
            if User.objects.filter(id=pk).exists():
                serializer = PrivateUserSerializer(User.objects.get(id=pk), many=False, context={'request': request})
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"error": "El usuario no existe"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            if user.id != pk:
                return Response({"error": "Solo puedes ver tus propios datos"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                serializer = PrivateUserSerializer(User.objects.get(id=pk), many=False, context={'request': request})
                return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk, *args, **kwargs):
        user = request.user

        if not user.is_staff:
            if user.id != pk:
                return Response({"error": "Solo puedes editar tu propio usuario"}, status=status.HTTP_400_BAD_REQUEST)

        username = user.username
        email = user.email
        first_name = user.first_name
        last_name = user.last_name

        try:
            username = self.request.data['username']
            if User.objects.filter(username=username).exclude(id=request.user.id).exists():
                return Response({"error": "El nombre de usuario ya existe"}, status=status.HTTP_400_BAD_REQUEST)
            user.username = username
        except:
            pass

        try:
            email = self.request.data['email']
            if User.objects.filter(email=email).exclude(id=request.user.id).exists():
                return Response({"error": "El email ya existe"}, status=status.HTTP_400_BAD_REQUEST)
            user.email = email
        except:
            pass

        try:
            first_name = self.request.data['first_name']
            user.first_name = first_name
        except:
            pass
        try:
            last_name = self.request.data['last_name']
            user.last_name = last_name
        except:
            pass

        user.save()
        user_object = User.objects.get(id=request.user.id)
        serializer = PrivateUserSerializer(user_object, many=False, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk, *args, **kwargs):
        user = request.user
        if user.is_staff:
            if User.objects.filter(id=pk).exists():
                user = User.objects.get(id=pk)
                user.delete()
                return Response({"message": "El usuario ha sido eliminado"}, status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error": "El usuario no existe"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            if user.id != pk:
                return Response({"error": "Solo puedes eliminar tu propio usuario"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                if User.objects.filter(id=pk).exists():
                    user = User.objects.get(id=pk)
                    user.delete()
                    return Response({"message": "Cuenta eliminada"}, status=status.HTTP_204_NO_CONTENT)
                else:
                    return Response({"error": "El usuario no existe"}, status=status.HTTP_400_BAD_REQUEST)

class UserExtraViewSet(viewsets.ModelViewSet):
    # authentication_classes = [TokenAuthentication,]
    queryset = UserExtra.objects.all()
    serializer_class = UserExtraSerializer
    http_method_names = ['get', 'post', 'put', 'options']
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return UserExtra.objects.filter(user=user.id)

    def create(self, request, *args, **kwargs):
        user = request.user
        if UserExtra.objects.filter(user=user.id).exists():
            return Response({"error": "Este perfil de usuario ya existe"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            serializer = UserExtraSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save(user=user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        user = request.user
        if UserExtra.objects.filter(user=user.id).exists():
            user_extra = UserExtra.objects.get(user=user.id)
            serializer = UserExtraSerializer(user_extra, data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "Este perfil de usuario no existe"}, status=status.HTTP_400_BAD_REQUEST)

class AnimeViewSet(viewsets.ModelViewSet):
    serializer_class = AnimeSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    #allowed methods
    http_method_names = ['get', 'put', 'options']
    filterset_fields = ['estreno', 'idioma', 'generos', 'tipo', 'estado']
    search_fields = ['nombre', 'sinopsis']
    ordering_fields = ['agregado', 'nombre', 'estreno']
    queryset = Anime.objects.all()

    def get_queryset(self):
        if self.request.query_params.get('random') == 'true':
            return Anime.objects.order_by('?')
        return Anime.objects.all()



class EpisodeViewSet(viewsets.ModelViewSet):
    serializer_class = EpisodeSerializer
    http_method_names = ['get','options', 'post']
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['ep_nombre']
    ordering_fields = ['fecha']
    queryset = Episodio.objects.all()

    def create(self, request):

        try:
            anime = request.data['anime']
            temporada = request.data['temporada']
            numero = request.data['numero']
        except:
            return Response({'error': "Faltan parametros ['anime', 'temporada', 'numero']"}, status=status.HTTP_400_BAD_REQUEST)

        
        if not Anime.objects.filter(id=anime).exists():
            return Response({'error': 'Anime no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        anime = Anime.objects.get(id=anime)

        if Episodio.objects.filter(anime=anime, temporada=temporada, numero=numero).exists():
            return Response({'error': 'Episodio ya existe'}, status=status.HTTP_400_BAD_REQUEST)

        ep_slug = anime.slug + '-' + str(numero)
        episodio = Episodio.objects.create(anime=anime, temporada=temporada, numero=numero, slug=ep_slug)
        return Response(EpisodeSerializer(episodio).data, status=status.HTTP_201_CREATED)

class EmbedViewSet(viewsets.ModelViewSet):
    serializer_class = EmbedSerializer
    http_method_names = ['get','options', 'post']
    permission_classes = [permissions.DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['embed']
    ordering_fields = ['id']
    queryset = Embed.objects.all()

    def create(self, request):

        try:
            episode = request.data['episode']
            name = request.data['name']
            url = request.data['url']
        except:
            return Response({'error': "Faltan parametros ['episode', 'name', 'url']"}, status=status.HTTP_400_BAD_REQUEST)

        if not Episodio.objects.filter(id=episode).exists():
            return Response({'error': 'Episodio no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        episode = Episodio.objects.get(id=episode)
        if Embed.objects.filter(episodio=episode, embed=name, url=url).exists():
            return Response({'error': 'Embed ya existe'}, status=status.HTTP_400_BAD_REQUEST)

        embed = Embed.objects.create(episodio=episode, embed=name, url=url)
        return Response(EmbedSerializer(embed).data, status=status.HTTP_201_CREATED)

class FavAnimeViewSet(viewsets.ModelViewSet):
    serializer_class = AnimesFavoritosSerializer
    http_method_names = ['get', 'post', 'put', 'options', 'delete']
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['fecha']
    
    def get_queryset(self):
        user = self.request.user
        anime_id = self.request.query_params.get('anime', None)
        if anime_id is not None:
            #disable pagination
            self.pagination_class = None
            return AnimesFavorito.objects.filter(usuario=user, anime=anime_id)
        else:
            return AnimesFavorito.objects.filter(usuario=user)

    #POST /api/fav_anime/
    def create(self, request):
        anime = Anime.objects.get(id=request.data['anime'])
        usuario = self.request.user
        animes_favoritos, created = AnimesFavorito.objects.get_or_create(
            anime=anime,
            usuario=usuario
        )

        #Si ya existe, se elimina
        if not created:
            animes_favoritos.delete()
            return Response(status=status.HTTP_204_NO_CONTENT) 

        context = {'request': request}
        serializer = AnimesFavoritosSerializer(animes_favoritos, context=context)
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        animefav = AnimesFavorito.objects.get(id=pk)
        animefav.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class EpisodiosVistoViewSet(viewsets.ModelViewSet):
    serializer_class = EpisodiosVistosSerializer
    http_method_names = ['get', 'post', 'put', 'options', 'delete']
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['fecha']
    
    def get_queryset(self):
        user = self.request.user
        anime_id = self.request.query_params.get('anime', None)
        if anime_id is not None:
            #disable pagination
            self.pagination_class = None
            return EpisodiosVisto.objects.filter(usuario=user, episodio__anime=anime_id)
        else:
            return EpisodiosVisto.objects.filter(usuario=user)

    #POST /api/episodios_vistos/
    def create(self, request):
        episodio = Episodio.objects.get(id=request.data['episodio'])
        usuario = self.request.user
        episodios_vistos, created = EpisodiosVisto.objects.get_or_create(
            episodio=episodio,
            usuario=usuario
        )

        #Si ya existe, se elimina
        if not created:
            episodios_vistos.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = EpisodiosVistosSerializer(episodios_vistos)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        episodio_visto = EpisodiosVisto.objects.get(id=pk)
        episodio_visto.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AnimeCommentsViewSet(viewsets.ModelViewSet):
    serializer_class = AnimeCommentsSerializer
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['anime']
    ordering_fields = ['created_at']
    queryset = AnimeComment.objects.all()

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return AnimeComment.objects.exclude(user__in=UserBlock.objects.filter(user=user).values('blocked_user'))
        else:
            return AnimeComment.objects.all()

    def create(self, request):
        serializer = AnimeCommentsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        anime = Anime.objects.get(id=request.data['anime'])
        if anime.comments_disabled and not request.user.is_staff:
            raise serializers.ValidationError({'error': 'Los comentarios están desactivados para este anime'})

        clean_comment = palabrota.censor(request.data['comment'], '***')
        comment_obj = AnimeComment.objects.filter(user=request.user, anime=request.data['anime'], comment=clean_comment)
        if comment_obj.exists():
            raise serializers.ValidationError({'error': 'Ya has comentado esto'})
        else:
            serializer.save(user=request.user, comment=clean_comment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, pk=None):
        comment = AnimeComment.objects.get(id=pk)

        if request.user.is_staff:
            comment.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        elif comment.user == request.user:
            comment.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

class AnimeCommentRepliesViewSet(viewsets.ModelViewSet):
    serializer_class = AnimeCommentRepliesSerializer
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['comment']
    ordering_fields = ['created_at']
    queryset = AnimeCommentsReply.objects.all()

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return AnimeCommentsReply.objects.exclude(user__in=UserBlock.objects.filter(user=user).values('blocked_user'))
        else:
            return AnimeCommentsReply.objects.all()

    def destroy(self, request, pk=None):

        if AnimeCommentsReply.objects.filter(id=pk).exists():
            reply = AnimeCommentsReply.objects.get(id=pk)
            if request.user.is_staff:
                reply.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            elif reply.user == request.user:
                reply.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(status=status.HTTP_403_FORBIDDEN)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        serializer = AnimeCommentRepliesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        clean_reply = palabrota.censor(request.data['reply'], '***')
        reply_obj = AnimeCommentsReply.objects.filter(user=request.user, comment=request.data['comment'], reply=clean_reply)
        if reply_obj.exists():
            raise serializers.ValidationError({'error': 'Ya has replicado esto'})
        else:
            serializer.save(user=request.user, reply=clean_reply)

            comment = AnimeComment.objects.get(id=request.data['comment'])
            if comment.user != request.user and comment.notifications:
                android_user_notification(
                    user=comment.user,
                    title=request.user.username + " te ha respondido",
                    message=clean_reply,
                    image="http://127.0.0.1/media/" + str(UserExtra.objects.get(user=request.user).avatar),
                    extra = {
                        "type": "comment_reply",
                        "reply_type": "anime",
                        "comment_id": request.data['comment'],
                    }
                )

                print("http://127.0.0.1/media/" + str(UserExtra.objects.get(user=request.user).avatar))

            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class EpisodeCommentsViewSet(viewsets.ModelViewSet):
    serializer_class = EpisodeCommentsSerializer
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['episode']
    ordering_fields = ['created_at']
    queryset = EpisodeComment.objects.all()

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return EpisodeComment.objects.exclude(user__in=UserBlock.objects.filter(user=user).values('blocked_user'))
        else:
            return EpisodeComment.objects.all()

    def create(self, request):
        serializer = EpisodeCommentsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        anime = Episodio.objects.get(id=request.data['episode']).anime
        if anime.comments_disabled and not request.user.is_staff:
            raise serializers.ValidationError({'error': 'Los comentarios están desactivados para este episodio'})

        clean_comment = palabrota.censor(request.data['comment'], '***')
        comment_obj = EpisodeComment.objects.filter(user=request.user, episode=request.data['episode'], comment=clean_comment)
        if comment_obj.exists():
            raise serializers.ValidationError({'error': 'Ya has comentado esto'})
        else:
            serializer.save(user=request.user, comment=clean_comment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    #override put method
    def update(self, request, pk=None):
        comment = EpisodeComment.objects.get(id=pk)
        if comment.user == request.user:
            serializer = EpisodeCommentsSerializer(comment, data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "This comment doesn't belong to you"} ,status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, pk=None):
        comment = EpisodeComment.objects.get(id=pk)

        if request.user.is_staff:
            comment.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        elif comment.user == request.user:
            comment.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class EpisodeCommentRepliesViewSet(viewsets.ModelViewSet):
    serializer_class = EpisodeCommentRepliesSerializer
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['comment']
    ordering_fields = ['created_at']
    queryset = EpisodeCommentsReply.objects.all()

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return EpisodeCommentsReply.objects.exclude(user__in=UserBlock.objects.filter(user=user).values('blocked_user'))
        else:
            return EpisodeCommentsReply.objects.all()

    def destroy(self, request, pk=None):

        if EpisodeCommentsReply.objects.filter(id=pk).exists():
            reply = EpisodeCommentsReply.objects.get(id=pk)
            if request.user.is_staff:
                reply.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            elif reply.user == request.user:
                reply.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(status=status.HTTP_403_FORBIDDEN)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        serializer = EpisodeCommentRepliesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        clean_reply = palabrota.censor(request.data['reply'], '***')
        reply_obj = EpisodeCommentsReply.objects.filter(user=request.user, comment=request.data['comment'], reply=clean_reply)
        if reply_obj.exists():
            raise serializers.ValidationError({'error': 'Ya has replicado esto'})
        else:
            serializer.save(user=request.user, reply=clean_reply)

            comment = EpisodeComment.objects.get(id=request.data['comment'])
            if comment.user != request.user and comment.notifications:

                android_user_notification(
                    user=comment.user,
                    title=request.user.username + " te ha respondido",
                    message=clean_reply,
                    image= "http://127.0.0.1/media/" + str(UserExtra.objects.get(user=request.user).avatar),
                    extra = {
                        "type": "comment_reply",
                        "reply_type": "episode",
                        "comment_id": request.data['comment'],
                    }
                )

            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AnimeCommentReportsViewSet(viewsets.ModelViewSet):
    serializer_class = AnimeCommentReportSerializer
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at']
    http_method_names = ['get', 'post', 'options']
    queryset = AnimeCommentReport.objects.all()

    def create(self, request):
        serializer = AnimeCommentReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        report = AnimeCommentReport.objects.filter(
            comment=request.data['comment'],
            user=request.user,
        )

        if report.exists():
            raise serializers.ValidationError({'error': '¡Ya has reportado este comentario!'})
        else:
            comment = AnimeComment.objects.get(id=request.data['comment'])
            if comment.user.is_staff:
                raise serializers.ValidationError({'error': '¡No puedes reportar un comentario de un admin!'})
            else:
                serializer.save(user=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AnimeCommentReplyReportsViewSet(viewsets.ModelViewSet):
    serializer_class = AnimeCommentReplyReportSerializer
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at']
    http_method_names = ['get', 'post', 'options']
    queryset = AnimeReplyReport.objects.all()

    def create(self, request):
        serializer = AnimeCommentReplyReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        report = AnimeReplyReport.objects.filter(
            reply=request.data['reply'],
            user=request.user,
        )

        if report.exists():
            raise serializers.ValidationError({'error': '¡Ya has reportado esta respuesta!'})
        else:
            reply = AnimeCommentsReply.objects.get(id=request.data['reply'])
            if reply.user.is_staff:
                raise serializers.ValidationError({'error': '¡No puedes reportar una respuesta de un admin!'})
            else:
                serializer.save(user=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)        

class EpisodeCommentReportsViewSet(viewsets.ModelViewSet):
    serializer_class = EpisodeCommentReportSerializer
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at']
    http_method_names = ['get', 'post', 'options']
    queryset = EpisodeCommentReport.objects.all()

    def create(self, request):
        serializer = EpisodeCommentReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        report = EpisodeCommentReport.objects.filter(
            comment=request.data['comment'],
            user=request.user,
        )

        if report.exists():
            raise serializers.ValidationError({'error': '¡Ya has reportado este comentario!'})
        else:
            comment = EpisodeComment.objects.get(id=request.data['comment'])
            if comment.user.is_staff:
                raise serializers.ValidationError({'error': '¡No puedes reportar un comentario de un admin!'})
            else:
                serializer.save(user=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class EpisodeCommentReplyReportsViewSet(viewsets.ModelViewSet):
    serializer_class = EpisodeCommentReplyReportSerializer
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at']
    http_method_names = ['get', 'post', 'options']
    queryset = EpisodeReplyReport.objects.all()

    def create(self, request):
        serializer = EpisodeCommentReplyReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        report = EpisodeReplyReport.objects.filter(
            reply=request.data['reply'],
            user=request.user,
        )

        if report.exists():
            raise serializers.ValidationError({'error': '¡Ya has reportado esta respuesta!'})
        else:
            reply = EpisodeCommentsReply.objects.get(id=request.data['reply'])
            if reply.user.is_staff:
                raise serializers.ValidationError({'error': '¡No puedes reportar una respuesta de un admin!'})
            else:
                serializer.save(user=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ReportKindsViewSet(viewsets.ModelViewSet):
    serializer_class = ReportKindSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['sensitive']
    http_method_names = ['get', 'options']
    queryset = ReportKind.objects.all()



# GOOGLE LOGIN

# BORRAR CUANDO APP ESTE EN PRODUCCION
class GoogleLogin(SocialLoginView):
    #import GoogleOAuth2Adapter

    adapter_class = GoogleOAuth2Adapter

    def post(self, request, *args, **kwargs):
        
        response = super(GoogleLogin, self).post(request, *args, **kwargs)
        token = Token.objects.get(key=response.data['key'])
        return Response(
            {
                'user': {
                    'id': token.user.id,
                    'username': token.user.username,
                    'email': token.user.email,
                    'first_name': token.user.first_name,
                    'last_name': token.user.last_name,
                    'isAdmin': token.user.is_staff,
                    'is_superuser': token.user.is_superuser,
                    'is_active': token.user.is_active,
                    'token': token.key
                }
            }
        )

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)


class GoogleRealLogin(SocialLoginView):

    adapter_class = GoogleOAuth2Adapter

    def post(self, request, *args, **kwargs):

        response = super(GoogleRealLogin, self).post(request, *args, **kwargs)
        token = Token.objects.get(key=response.data['key'])
        return Response(
            {
                'user': PrivateUserSerializer(token.user).data
            }
        )

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)


class GCMDeviceViewSet(viewsets.ModelViewSet):
    serializer_class = GCMDeviceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at']
    http_method_names = ['get', 'post', 'put', 'options', 'delete']

    def get_queryset(self):
        if self.request.user.is_staff:
            return GCMDevice.objects.all()
        else:
            return GCMDevice.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        user = request.user
        serializer = GCMDeviceSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            #check if registration_id already exists
            if GCMDevice.objects.filter(registration_id=serializer.validated_data['registration_id']).exists():
                gcmdevice = GCMDevice.objects.get(registration_id=serializer.validated_data['registration_id'])
                if gcmdevice.user != user:
                    gcmdevice.user = user
                    gcmdevice.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                serializer.save(user=user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        device = GCMDevice.objects.get(id=pk)
        
        if request.user.is_staff or device.user == request.user:
            device.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

    #put 
    def update(self, request, pk=None):
        device = GCMDevice.objects.get(id=pk)
        if device.user == request.user:
            serializer = GCMDeviceSerializer(device, data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class GenreViewSet(viewsets.ModelViewSet):
    serializer_class = GenreSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    http_method_names = ['get', 'options']
    queryset = Genero.objects.all()

class TypeViewSet(viewsets.ModelViewSet):
    serializer_class = TypeSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    http_method_names = ['get', 'options']
    queryset = Tipo.objects.all()

class StatusViewSet(viewsets.ModelViewSet):
    serializer_class = StatusSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    http_method_names = ['get', 'options']
    queryset = Estado.objects.all()

class LanguageViewSet(viewsets.ModelViewSet):
    serializer_class = LanguageSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    http_method_names = ['get', 'options']
    queryset = Idioma.objects.all()

class UserReportViewSet(viewsets.ModelViewSet):
    serializer_class = UserReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'options']
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['reported_user', 'reporter_user']
    ordering_fields = ['created_at', 'updated_at']

    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.groups.filter(name='Moderator').exists():
            return UserReport.objects.all()
        else:
            return UserReport.objects.filter(reporter_user=self.request.user)

    def create(self, request):
        serializer = UserReportSerializer(data=request.data, context={'request': request})

        #check if report already exists
        if UserReport.objects.filter(reported_user=request.data['reported_user'], reporter_user=request.user).exists():
            return Response({'error': 'Ya has reportado al usuario'}, status=status.HTTP_409_CONFLICT)

        if serializer.is_valid():
            serializer.save(reporter_user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        serializer.save(reporter_user=self.request.user)

class UserBlockViewSet(viewsets.ModelViewSet):
    serializer_class = UserBlockSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'delete', 'options']
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['blocked_user', 'user']
    ordering_fields = ['created_at', 'updated_at']

    def get_queryset(self):
        return UserBlock.objects.filter(user=self.request.user)

    def create(self, request):
        serializer = UserBlockSerializer(data=request.data, context={'request': request})

        #check if block already exists
        if UserBlock.objects.filter(blocked_user=request.data['blocked_user'], user=request.user).exists():
            return Response({'error': 'Ya has bloqueado al usuario'}, status=status.HTTP_409_CONFLICT)

        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        
        if UserBlock.objects.filter(id=kwargs['pk'], user=request.user).exists():
            user_block = UserBlock.objects.get(id=kwargs['pk'])
            if not user_block.user == request.user:
                return Response(status=status.HTTP_403_FORBIDDEN)

            return super().destroy(request, *args, **kwargs)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SeenEpisodeTimeViewSet(viewsets.ModelViewSet):
    serializer_class = SeenEpisodeTimeSerializer
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['user', 'episode']
    ordering_fields = ['created_at', 'updated_at']
    queryset = SeenEpisodeTime.objects.all()

    def get_queryset(self):
        return SeenEpisodeTime.objects.all()

    def create(self, request):
        serializer = SeenEpisodeTimeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ## nuevo codigo
        #check if episode exists
        if not Episodio.objects.filter(id=request.data['episode']).exists():
            return Response({'error': 'El episodio no existe'}, status=status.HTTP_404_NOT_FOUND)
        
        episode = Episodio.objects.get(id=request.data['episode'])
        seconds = request.data['seconds']
        total_seconds = request.data['total_seconds']
        #check if object already exists
        if SeenEpisodeTime.objects.filter(user=request.user, episode=episode).exists():
            seen_episode_time = SeenEpisodeTime.objects.get(user=request.user, episode=episode)
            seen_episode_time.seconds = seconds
            seen_episode_time.total_seconds = total_seconds
            seen_episode_time.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@csrf_exempt
def google_one_tap_login(request):
    login_url = "http://127.0.0.1" + '/accounts/google/login/'
    return HttpResponseRedirect(login_url)


# LOGIN NORMAL

@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def signin(request):

    try:
        username = request.GET['username']
        password = request.GET['password']
        access_token = request.GET['access_token']
    except KeyError:
        return Response({'error': 'Missing username, password or access_token.'}, status=status.HTTP_400_BAD_REQUEST)

    if access_token != settings.NORMAL_AUTH_ACCESS_TOKEN:
        return Response({'error': 'Invalid access_token.'}, status=status.HTTP_400_BAD_REQUEST)

    if "@" in username and "." in username:
        try:
            username = User.objects.get(email=username).username
        except User.DoesNotExist:
            return Response({'error': 'Invalid credentials.'}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)

    if user is not None:
        if user.is_active:
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)

            user_data = PrivateUserSerializer(user).data

            return Response({'user' : user_data}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'User is not active.'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'error': 'Invalid credentials.'}, status=status.HTTP_400_BAD_REQUEST)

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

@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def signup(request):
    try:
        username = request.data['username']
        email = request.data['email']
        password = request.data['password']
        coppa = request.data['thirteen_age_coppa_compliant']
        access_token = request.data['access_token']
    except KeyError:
        return Response({
            'error': 'Missing params.',
            'params': ['username', 'email', 'password', 'thirteen_age_coppa_compliant', 'access_token']
        }, status=status.HTTP_400_BAD_REQUEST)

    if access_token != settings.NORMAL_AUTH_ACCESS_TOKEN:
        return Response({'error': 'Token de acceso invalido'}, status=status.HTTP_400_BAD_REQUEST)

    if not coppa:
        return Response({'error': 'Debes ser tener 13 años o más para registrarte.'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'El nombre de usuario ya existe'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({'error': 'El email ya existe'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, email=email, password=password)
    user.save()

    user_extra = UserExtra(user=user, thirteen_age_coppa_compliant=coppa)
    user_extra.save()

    t = Thread(target=send_email_admin, args=(username, email))
    t.start()

    # ds = DsWebhook("")
    # ds.send_new_user(user, RegistrationSources.MOBILE)

    return Response({'message': 'Cuenta creada éxitosamente'}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def change_coppa_compliance(request):
    try:
        thirteen_age_coppa_compliant = request.data['thirteen_age_coppa_compliant']
    except KeyError:
        return Response({'error': 'Missing thirteen_age_coppa_compliant.'}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    user_extra = UserExtra.objects.get(user=user)
    user_extra.thirteen_age_coppa_compliant = thirteen_age_coppa_compliant
    user_extra.save()

    user_data = PrivateUserSerializer(user).data

    return Response({'message': 'Coppa compliance cambiado éxitosamente', 'user': user_data}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes((permissions.IsAdminUser,))
def send_push_notification(request):

    try:
        title = request.data['title']
        message = request.data['message']
        image = request.data['image']
        extra = request.data['extra']
    except KeyError:
        return Response({'error': 'Missing title, message'}, status=status.HTTP_400_BAD_REQUEST)


    print(title, message, image, extra)
    # android_all_notification(
    #     title=title,
    #     message=message,
    #     image=image,
    #     extra=json.loads(extra)
    # )

    return Response({'message': 'Notificación enviada éxitosamente'}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def eval_unpack(request):

    try:
        eval = request.data['eval']
    except KeyError:
        return Response({'error': 'Missing eval.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        unpack = jsbeautifier.beautify(eval)
        return Response({'eval': unpack}, status=status.HTTP_200_OK)
    except:
        return Response({'error': 'Invalid eval.'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def ban_user(request):

    if request.user.is_staff or request.user.groups.filter(name='Moderator').exists():
        try:
            user_id = request.data['user_id']
            reason = request.data['reason']
        except KeyError:
            return Response({'error': 'Missing user_id, reason.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.get(id=user_id)

        if user.is_staff or user.groups.filter(name='Moderator').exists():
            return Response({'error': 'No puedes banear a un administrador o moderador'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.is_active:
            return Response({'error': 'El usuario ya está baneado'}, status=status.HTTP_400_BAD_REQUEST)

        if user == request.user:
            return Response({'error': 'No te puedes banear a ti mismo'}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = False
        user.save()

        user_extra = UserExtra.objects.get(user=user)
        user_extra.ban_reason = reason
        user_extra.ban_date = datetime.datetime.now()
        user_extra.ban_admin = request.user
        user_extra.save()

        banned_user = PublicUserSerializer(user).data

        return Response({'message': 'Usuario baneado éxitosamente', 'banned_user': banned_user}, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'No tienes permisos para realizar esta acción'}, status=status.HTTP_403_FORBIDDEN)

@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def unban_user(request):

    if request.user.is_staff or request.user.groups.filter(name='Moderator').exists():
        try:
            user_id = request.data['user_id']
        except KeyError:
            return Response({'error': 'Missing user_id'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.get(id=user_id)

        if user.is_active:
            return Response({'error': 'Este usuario no esta baneado'}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = True
        user.save()

        user_extra = UserExtra.objects.get(user=user)
        user_extra.ban_reason = None
        user_extra.ban_date = None
        user_extra.ban_admin = None
        user_extra.save()

        unbanned_user = PublicUserSerializer(user).data

        return Response({'message': 'Usuario desbaneado éxitosamente', 'unbanned_user': unbanned_user}, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'No tienes permisos para realizar esta acción'}, status=status.HTTP_403_FORBIDDEN)


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def get_user_episodes_next(request):
    user = request.user

    # episodes = Episodio.objects.raw('SELECT * FROM main_app_episodio JOIN main_app_episodiosvisto on main_app_episodiosvisto.episodio_id = main_app_episodio.id WHERE main_app_episodio.id IN (SELECT MAX(main_app_episodio.id) FROM main_app_episodio INNER JOIN main_app_anime ON main_app_episodio.anime_id = main_app_anime.id INNER JOIN main_app_episodiosvisto ON main_app_episodio.id = main_app_episodiosvisto.episodio_id WHERE main_app_episodiosvisto.usuario_id = %s GROUP BY main_app_anime.id) GROUP BY main_app_episodiosvisto.id ORDER BY main_app_episodiosvisto.fecha DESC LIMIT 18', [user.id])
    # if not episodes:
    #     return Response({'message': 'No hay episodios vistos'}, status=status.HTTP_200_OK)
    # episodes = [episode.get_next_episode() for episode in episodes]

    user_filter = Q(usuario=user)
    higher_anime_episode_seen = EpisodiosVisto.objects.filter(user_filter).values('episodio__anime').annotate(max_id=Max('episodio__id'))
    episodes = Episodio.objects.filter(id__in=Subquery(higher_anime_episode_seen.values('max_id'))).order_by('-episodiosvisto__fecha')[:24]
    if not episodes:
        return Response({'message': 'No hay episodios vistos'}, status=status.HTTP_200_OK)
    episodes = [episode.get_next_episode() for episode in episodes]

    ##pass context to serializer
    context = {'request': request}
    serializer = EpisodeSerializer(episodes, many=True, context=context)

    return Response({'message': 'Episodios vistos siguientes', 'episodes': serializer.data}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((permissions.IsAdminUser,))
def discord(request):
    # ds = DsWebhook("")
    # rand_anime = Anime.objects.order_by('?').first()
    # ds.send_new_anime(rand_anime)

    # rand_episode = Episodio.objects.order_by('?').first()
    # ds.send_new_episode(rand_episode)

    rand_user = User.objects.order_by('?').first()
    ds.send_new_user(rand_user, 1)

    return Response({'message': 'https://discord.gg/'}, status=status.HTTP_200_OK)

# from POE import load_chat_id_map, clear_context, send_message, get_latest_message, set_auth
@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def poe_api(request):

    try:
        anime_name = request.GET['anime_name']
    except KeyError:
        return Response({'error': 'No se ha especificado el nombre del anime (anime_name)'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        consult_type = request.GET['consult_type']
    except KeyError:
        return Response({'error': 'No se ha especificado el tipo de consulta (consult_type)'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        token = request.GET['poe_token']
    except KeyError:
        return Response({'error': 'Falta el token de Poe (poe_token)'}, status=status.HTTP_400_BAD_REQUEST)

    # Consult Types: 
    # resume_no_spoilers, resume, interesting_facts, characters, staff, action_episodes, recommendations

    types = {
        'resume_no_spoilers': 'Resumen sin spoilers',
        'resume': 'Resumen normal',
        'interesting_facts': 'Curiosidades',
        'characters': 'Personajes',
        'staff': 'Staff',
        'relevant_episodes': 'Episodios relevantes',
        'recommendations': 'Recomendaciones basadas en el anime'
    }

    if consult_type not in types:
        return Response({'error': 'Tipo de consulta no soportada', 'types': types}, status=status.HTTP_400_BAD_REQUEST)
    
    prompts = {
        'resume_no_spoilers': 'Dame solo el resumen sin spoilers del anime ' + anime_name + " en formato JSON, clave 'resume_no_spoilers', valor: el resumen",
        'resume': 'Solo el resumen del anime con partes vitales de la trama ' + anime_name + " en formato JSON, clave 'resume', valor: el resumen",
        'interesting_facts': 'Datos interesantes del anime ' + anime_name + " en formato JSON, clave 'interesting_facts', valor: los datos interesantes. Los datos interesantes tienen las claves 'nombre', 'descripcion'",
        'characters': '4 personajes principales del anime ' + anime_name + " en formato JSON, clave 'characters', valor: los personajes. Los personajes tienen las claves 'nombre', 'edad', 'genero', 'ocupacion', 'descripcion', 'imagen'",
        'staff': 'Staff principal del anime ' + anime_name + " en formato JSON, clave 'staff', valor: el staff. Los staff tienen las claves 'nombre', 'edad', 'genero', 'ocupacion'",
        'relevant_episodes': '5 episodios más relevantes del anime ' + anime_name + " en formato JSON, clave 'relevant_episodes', valor: los episodios relevantes. Los episodios relevantes tienen las claves 'nombre', 'numero', 'descripcion', 'minuto_mas_interesante'",
        'recommendations': '5 recomendaciones de otros animes basados en el anime ' + anime_name + " en formato JSON, clave 'recommendations', valor: las recomendaciones. Las recomendaciones tienen las claves 'nombre', 'fecha_emision', 'breve_descripcion', 'total_episodios', 'imagen'",
    }

    prompt = prompts[consult_type]
    client = poe.Client(token=token)
    for chunk in client.send_message("capybara", prompt, timeout=60):
        pass

    print(chunk["text"])

    # bot = "chinchilla"
    # set_auth('Quora-Formkey','43c9a51f30c71b421364704e6a0349de')
    # set_auth('Cookie','m-b=YYm67Oh4kKrhzN6v-s8Vwg==')
    # chat_id = load_chat_id_map(bot) #capybara (Sage GPT-3)
    # clear_context(chat_id)
    # send_message(prompt,bot,chat_id)
    # reply = get_latest_message(bot)
    # print(reply)

    dump = extract_json(chunk["text"])

    if (dump is None):
        return Response({'error': 'No se ha encontrado el JSON'}, status=status.HTTP_400_BAD_REQUEST)

    return Response(dump, status=status.HTTP_200_OK)

#crea una funcion para extraer el json de la respuesta, la respuesta usualmente tiene otro texto aparte del json
def extract_json(text):
    try:
        json_text = text[text.index("{") : text.rindex("}") + 1]
        return json.loads(json_text)
    except ValueError:
        return None
