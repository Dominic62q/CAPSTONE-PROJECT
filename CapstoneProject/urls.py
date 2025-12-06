from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView 

urlpatterns = [
    # Admin Interface
    path('admin/', admin.site.urls),

    # Frontend Dashboard (Renders the HTMX template)
    path('', TemplateView.as_view(template_name='dashboard.html'), name='home'),

    # API Endpoints
    path('api/', include('StudyHub.urls')),
]