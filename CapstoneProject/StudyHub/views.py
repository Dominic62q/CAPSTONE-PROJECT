from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import permissions

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db.models import Q # Used for complex filtering

from .models import Subject, UserProfile, StudyGroup, Resource
from .serializers import (
    SubjectSerializer, 
    StudyGroupSerializer, 
    ResourceSerializer, 
    UserMatchSerializer
)
from .permissions import IsGroupOwnerOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend

# --- Filters ---
class StudyGroupFilter(DjangoFilterBackend):
    """Custom filter to allow filtering groups by subject ID."""
    filter_fields = ['subjects']
    model = StudyGroup

# --- 1. Subject ViewSet (Public Read-Only) ---
class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/subjects/ - List all subjects.
    No authentication needed (Overridden by permission_classes).
    """
    queryset = Subject.objects.all().order_by('name')
    serializer_class = SubjectSerializer
    # Overriding global default: Subjects are public read-only
    permission_classes = [permissions.AllowAny]


# --- 2. Resource ViewSet (Public Read List, Authenticated Create) ---
class ResourceListCreateAPIView(generics.ListCreateAPIView):
    """
    GET /api/resources/ - List all resources (Public).
    POST /api/resources/ - Create a resource (Authenticated).
    """
    queryset = Resource.objects.select_related('group', 'uploaded_by').all()
    serializer_class = ResourceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['group'] # Allows filtering by group ID: ?group=1

    def get_permissions(self):
        """Allows GET to be public, but POST requires authentication."""
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """Automatically assigns the uploaded_by field."""
        group_id = serializer.validated_data.get('group').id
        group = get_object_or_404(StudyGroup, pk=group_id)

        # Ensure the user is authenticated and is a member of the group before posting
        if self.request.user not in group.members.all():
             raise serializers.ValidationError("You must be a member of this group to post resources.")

        serializer.save(uploaded_by=self.request.user)


# --- 3. Study Group ViewSet (Core Logic) ---
class StudyGroupViewSet(viewsets.ModelViewSet):
    """
    Handles CRUD for groups, plus the custom 'join' and 'leave' actions.
    """
    queryset = StudyGroup.objects.prefetch_related('subjects', 'members').all()
    serializer_class = StudyGroupSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['subjects'] # Allows filtering groups by subject ID: ?subjects=1
    permission_classes = [IsGroupOwnerOrReadOnly] # Use custom permission for ownership checks

    def get_permissions(self):
        """Allows LIST (GET) to be public, but all others are protected."""
        if self.action == 'list':
            return [permissions.AllowAny()]
        return [IsAuthenticated(), IsGroupOwnerOrReadOnly()]


    # POST /api/groups/{id}/join/
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def join(self, request, pk=None):
        """Adds the authenticated user to the members of the group."""
        group = get_object_or_404(StudyGroup, pk=pk)
        group.members.add(request.user)
        return Response({'status': f'Successfully joined {group.name}'})

    # POST /api/groups/{id}/leave/
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def leave(self, request, pk=None):
        """Removes the authenticated user from the members of the group."""
        group = get_object_or_404(StudyGroup, pk=pk)
        
        # Prevent the user from leaving if they are the creator
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
    GET /api/matches/
    Lists users who share at least one subject interest with the authenticated user.
    """
    serializer_class = UserMatchSerializer
    permission_classes = [IsAuthenticated] # Must be authenticated to check for matches

    def get_queryset(self):
        user = self.request.user
        
        # 1. Get the current user's subjects (if profile exists)
        try:
            user_profile = user.profile 
        except UserProfile.DoesNotExist:
            return UserProfile.objects.none()

        user_subjects = user_profile.subjects.all()
        
        if not user_subjects.exists():
            return UserProfile.objects.none() # No interests, no matches
        
        # 2. Find other UserProfiles whose 'subjects' M2M field overlaps with the current user's subjects.
        #    Use '__in' to filter profiles whose subjects are in the list of user_subjects.
        #    We must exclude the current user.
        queryset = UserProfile.objects.filter(
            subjects__in=user_subjects
        ).exclude(
            user=user
        ).distinct().select_related('user').prefetch_related('subjects') 
        # select_related('user') and prefetch_related('subjects') are for optimization (N+1 fix)

    