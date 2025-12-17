from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views  # <--- THIS IMPORT WAS MISSING

# Create a router and register our ViewSets with it.
router = DefaultRouter()
router.register(r'subjects', views.SubjectViewSet, basename='subject')
router.register(r'groups', views.StudyGroupViewSet, basename='studygroup')
# Note: Resources, Matches, Profile, and Auth are APIViews/Generics, so they go in urlpatterns below.

urlpatterns = [
    # Router URLs (Groups & Subjects)
    path('', include(router.urls)),

    # Authentication
    path('register/', views.UserRegisterView.as_view(), name='register'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),

    # Resources (List & Create)
    path('resources/', views.ResourceListCreateAPIView.as_view(), name='resource-list'),

    # User Matching (Find a Buddy)
    path('matches/', views.UserMatchAPIView.as_view(), name='user-matches'),

    # User Profile (The new page)
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
]