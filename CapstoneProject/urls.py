from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView 
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin Interface
    path('admin/', admin.site.urls),

    # Frontend Dashboard (Renders the HTMX template)
    path('', TemplateView.as_view(template_name='dashboard.html'), name='home'),

    # API Endpoints
    path('api/', include('StudyHub.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)