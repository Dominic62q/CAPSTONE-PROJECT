from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend

# Imports from your app
from .models import Subject, UserProfile, StudyGroup, Resource
from .serializers import (
    SubjectSerializer, 
    StudyGroupSerializer, 
    ResourceSerializer, 
    UserMatchSerializer,
    UserRegisterSerializer
)
from .permissions import IsGroupOwnerOrReadOnly

# --- Auth Views (No Changes) ---
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import traceback
@method_decorator(csrf_exempt, name='dispatch')
class UserRegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully"}, status=201)
        return Response(serializer.errors, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class UserLoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        user = authenticate(username=request.data.get("username"), password=request.data.get("password"))
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({"token": token.key, "username": user.username})
        return Response({"error": "Invalid credentials"}, status=400)

class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        request.user.auth_token.delete()
        return Response(status=200)

# --- ViewSets ---

class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Subject.objects.all().order_by('name')
    serializer_class = SubjectSerializer
    permission_classes = [AllowAny]

class ResourceListCreateAPIView(generics.ListCreateAPIView):
    queryset = Resource.objects.select_related('group', 'uploaded_by').order_by('-created_at')
    serializer_class = ResourceSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        # Custom create to handle HTMX response
        group_id = request.data.get('group')
        group = get_object_or_404(StudyGroup, id=group_id)
        if request.user not in group.members.all():
            return Response({"error": "Not a member"}, status=403)
        
        response = super().create(request, *args, **kwargs)
        
        # If HTMX, return the HTML row instead of JSON
        if request.META.get('HTTP_HX_REQUEST'):
            resource_obj = Resource.objects.get(id=response.data['id'])
            return render(request, 'partials/resource_row.html', {'resource': resource_obj})
        return response

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


# --- CORE FIX: Study Group ViewSet ---
class StudyGroupViewSet(viewsets.ModelViewSet):
    queryset = StudyGroup.objects.prefetch_related('subjects', 'members').all()
    serializer_class = StudyGroupSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['subjects']
    # NEW: Ensure form data from HTML is parsed correctly
    parser_classes = [MultiPartParser, FormParser] 

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated(), IsGroupOwnerOrReadOnly()]

    # --- 1. HANDLE GROUP CREATION ---
    def perform_create(self, serializer):
        # This is the "Django Way" to set the user. 
        # It runs BEFORE the M2M subjects are saved, preventing the crash.
        serializer.save(created_by=self.request.user)
        # We also add the creator as a member immediately
        serializer.instance.members.add(self.request.user)

    def create(self, request, *args, **kwargs):
        try:
            # Standard creation logic
            return super().create(request, *args, **kwargs)
            
        except Exception as e:
            # CRASH REPORTER: This prints the real error to your terminal
            print("========================================")
            print("ERROR CREATING GROUP:")
            traceback.print_exc()
            print("========================================")
            
            # If HTMX, show the error on the form
            if request.META.get('HTTP_HX_REQUEST'):
                subjects = Subject.objects.all()
                return render(request, 'partials/create_group_form.html', {
                    'subjects': subjects,
                    'errors': {'name': [f"System Error: {str(e)}"]}, # Show error on UI
                    'data': request.data
                })
            raise e

    # --- 2. LIST (Explore Page) ---
    def list(self, request, *args, **kwargs):
        # ... (Same as before)
        queryset = self.filter_queryset(self.get_queryset())
        if request.META.get('HTTP_HX_REQUEST'):
            return render(request, 'partials/group_list.html', {'groups': queryset, 'user': request.user})
        return super().list(request, *args, **kwargs)

    # --- 3. HTMX SUCCESS OVERRIDE ---
    # This renders the list AFTER a successful create
    def list_after_create(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        return render(request, 'partials/group_list.html', {'groups': queryset, 'user': request.user})

    # Override standard response to return HTML for HTMX
    def finalize_response(self, request, response, *args, **kwargs):
        if request.method == 'POST' and response.status_code == 201 and request.META.get('HTTP_HX_REQUEST'):
            # If create was successful, return the updated list!
            return self.list_after_create(request)
        return super().finalize_response(request, response, *args, **kwargs)

    # ... (Keep retrieve, create_form, join, leave exactly as they were) ...
    # 4. RETRIEVE
    def retrieve(self, request, pk=None, *args, **kwargs):
        group = get_object_or_404(self.queryset, pk=pk)
        if request.META.get('HTTP_HX_REQUEST'):
            is_member = request.user in group.members.all() if request.user.is_authenticated else False
            resources = group.resource_set.all().order_by('-created_at')
            return render(request, 'partials/group_detail.html', {
                'group': group, 'is_member': is_member, 'resources': resources, 'user': request.user
            })
        return super().retrieve(request, *args, **kwargs)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def create_form(self, request):
        subjects = Subject.objects.all()
        return render(request, 'partials/create_group_form.html', {'subjects': subjects})

    # ... inside StudyGroupViewSet ...

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def join(self, request, pk=None):
        group = get_object_or_404(StudyGroup, pk=pk)
        group.members.add(request.user)
        
        # 1. LOGIC: Reload the Detail View (Now Unlocked!)
        is_member = True
        resources = group.resource_set.all().order_by('-created_at')
        
        return render(request, 'partials/group_detail.html', {
            'group': group, 
            'is_member': is_member, 
            'resources': resources, 
            'user': request.user
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def leave(self, request, pk=None):
        group = get_object_or_404(StudyGroup, pk=pk)
        if group.created_by == request.user:
            return Response({'error': 'Owner cannot leave'}, status=400)
        
        group.members.remove(request.user)
        
        # 2. LOGIC: Redirect to Explore Groups (List View)
        queryset = self.filter_queryset(self.get_queryset())
        
        return render(request, 'partials/group_list.html', {
            'groups': queryset, 
            'user': request.user
        })
class UserMatchAPIView(generics.ListAPIView):
    serializer_class = UserMatchSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        try:
            profile = self.request.user.profile
            subjects = profile.subjects.all()
            if not subjects: return UserProfile.objects.none()
            return UserProfile.objects.filter(subjects__in=subjects).exclude(user=self.request.user).distinct()
        except:
            return UserProfile.objects.none()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if request.META.get('HTTP_HX_REQUEST'):
            return render(request, 'partials/match_list.html', {'matches': queryset})
        return super().list(request, *args, **kwargs)
    
# ... existing imports ...

class UserProfileView(APIView):
    """
    GET /api/profile/ - Renders the user's profile page HTML.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # Ensure profile exists (it should via signals, but safety first)
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # Get groups the user has joined
        joined_groups = user.study_groups.all()
        
        # Get groups the user owns
        owned_groups = user.owned_groups.all()

        context = {
            'user': user,
            'profile': profile,
            'joined_groups': joined_groups,
            'owned_groups': owned_groups,
        }
        
        if request.META.get('HTTP_HX_REQUEST'):
            return render(request, 'partials/profile.html', context)
        
        # Fallback (shouldn't really happen with this architecture)
        return Response({"username": user.username})