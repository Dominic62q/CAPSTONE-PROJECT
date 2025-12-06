from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SubjectViewSet, 
    StudyGroupViewSet, 
    ResourceListCreateAPIView, 
    UserMatchAPIView,
    UserRegisterView,
    UserLoginView,
    UserLogoutView,
)

# Use a router for ViewSets (automatic URL generation for CRUD)
router = DefaultRouter()
router.register(r'subjects', SubjectViewSet) # /api/subjects/
router.register(r'groups', StudyGroupViewSet) # /api/groups/

urlpatterns = [
    # Router URLs (Subjects, Groups, Groups Join/Leave)
    path('', include(router.urls)),
     # --- NEW: Authentication Endpoints ---
    path('register/', UserRegisterView.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('logout/', UserLogoutView.as_view(), name='user-logout'), 

    # Resource Endpoints (ListCreateAPIView)
    path('resources/', ResourceListCreateAPIView.as_view(), name='resource-list-create'),

    # User Matching Endpoint (Custom APIView)
    path('matches/', UserMatchAPIView.as_view(), name='user-match'),

    # DRF Login/Logout (Optional, for browsable API)
    path('auth/', include('rest_framework.urls', namespace='rest_framework')),
]