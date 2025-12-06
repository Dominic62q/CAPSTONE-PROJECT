from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.permissions import AllowAny


from .models import Subject, UserProfile, StudyGroup, Resource
from .serializers import (
    SubjectSerializer, 
    StudyGroupSerializer, 
    ResourceSerializer, 
    UserMatchSerializer,
    UserRegisterSerializer,
)
from .permissions import IsGroupOwnerOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend

# --- NEW: Authentication Views ---

@method_decorator(csrf_exempt, name='dispatch')
class UserRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": "User registered successfully"}, status=201)
        return Response(serializer.errors, status=400)




@method_decorator(csrf_exempt, name='dispatch')
class UserLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)
        
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({"token": token.key, "username": user.username})
        
        return Response({"error": "Invalid credentials"}, status=400)




class UserLogoutView(APIView):
    """POST /api/logout/ - Deletes the user's current token, requiring a new login."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Delete the user's token (logs them out)
        request.user.auth_token.delete()
        return Response(
            {'detail': 'Successfully logged out.'}, 
            status=status.HTTP_200_OK
        )


# --- 1. Subject ViewSet (Public Read-Only) ---
class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/subjects/ - Returns a list of all subjects (Public).
    """
    queryset = Subject.objects.all().order_by('name')
    serializer_class = SubjectSerializer
    permission_classes = [AllowAny]


# --- 2. Resource ViewSet (Public Read List, Authenticated Create) ---
class ResourceListCreateAPIView(generics.ListCreateAPIView):
    """
    GET /api/resources/ - List all resources (Public).
    POST /api/resources/ - Create a resource (Authenticated, requires membership).
    """
    queryset = Resource.objects.select_related('group', 'uploaded_by').all()
    serializer_class = ResourceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['group'] 

    def get_permissions(self):
        # Public GET, Authenticated POST
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        group_id = serializer.validated_data.get('group').id
        group = get_object_or_404(StudyGroup, pk=group_id)

        # Custom validation: User must be a member of the group before posting
        if self.request.user not in group.members.all():
             raise serializers.ValidationError({"group": "You must be a member of this group to post resources."})

        serializer.save(uploaded_by=self.request.user)


# --- 3. Study Group ViewSet (Core Logic) ---
class StudyGroupViewSet(viewsets.ModelViewSet):
    """
    Handles CRUD for groups, plus the custom 'join' and 'leave' actions.
    """
    queryset = StudyGroup.objects.prefetch_related('subjects', 'members', 'resource_set').all()
    serializer_class = StudyGroupSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['subjects'] # Filter by subject ID: ?subjects=1
    
    def get_permissions(self):
        # Public GET list, Authenticated GET retrieve, Protected CUD
        if self.action == 'list' or self.action == 'retrieve':
            return [AllowAny()]
        return [IsAuthenticated(), IsGroupOwnerOrReadOnly()]


    # POST /api/groups/{id}/join/
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def join(self, request, pk=None):
        """Adds the authenticated user to the members of the group."""
        group = get_object_or_404(StudyGroup, pk=pk)
        
        if request.user in group.members.all():
            return Response({'error': 'User is already a member.'}, status=status.HTTP_400_BAD_REQUEST)

        group.members.add(request.user)
        return Response({'status': f'Successfully joined {group.name}'})

    # POST /api/groups/{id}/leave/
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def leave(self, request, pk=None):
        """Removes the authenticated user from the members of the group."""
        group = get_object_or_404(StudyGroup, pk=pk)
        
        # Prevent the owner from leaving
        if group.created_by == request.user:
            return Response(
                {'error': 'Owner cannot leave the group. Transfer ownership first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        group.members.remove(request.user)
        return Response({'status': f'Successfully left {group.name}'})


# --- 4. User Matching View (Unique Feature) ---
class UserMatchAPIView(generics.ListAPIView):
    """
    GET /api/matches/ - Lists users who share at least one subject interest (Protected).
    """
    serializer_class = UserMatchSerializer
    permission_classes = [IsAuthenticated] # Requires authentication

    def get_queryset(self):
        user = self.request.user
        
        # User must have a profile and subjects defined to match
        try:
            user_profile = user.profile 
        except UserProfile.DoesNotExist:
            return UserProfile.objects.none()

        user_subjects = user_profile.subjects.all()
        
        if not user_subjects.exists():
            return UserProfile.objects.none()
        
        # Find other profiles with overlapping subjects, exclude self, and optimize query
        queryset = UserProfile.objects.filter(
            subjects__in=user_subjects
        ).exclude(
            user=user
        ).distinct().select_related('user').prefetch_related('subjects') 

        return queryset