from django.contrib import admin
from .models import Subject, UserProfile, StudyGroup, Resource

# Register your models here.
from django.contrib import admin
from .models import Subject, UserProfile, StudyGroup, Resource

admin.site.register(Subject)
admin.site.register(UserProfile)
admin.site.register(StudyGroup)
admin.site.register(Resource)

