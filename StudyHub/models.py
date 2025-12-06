from django.db import models
from django.contrib.auth.models import User 
from django.db.models.signals import post_save # <-- NEW: Import signal
from django.dispatch import receiver # <-- NEW: Import receiver
# Create your models here.
# --- 1. Subject Model ---
class Subject(models.Model):
    """
    Represents an academic topic (e.g., 'Linear Algebra', 'Python').
    Used to categorize groups and user interests.
    """
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

# --- 2. User Profile Model ---
class UserProfile(models.Model):
    """
    Extends the built-in Django User model to track academic subjects of interest.
    This model has a One-to-One link with the User model.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Subjects the user is interested in (ManyToMany relationship with Subject)
    subjects = models.ManyToManyField(Subject, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

# --- 3. Study Group Model ---
class StudyGroup(models.Model):
    """
    The main collaboration unit. Links subjects to members.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # The user who created the group (ForeignKey)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='owned_groups'
    )
    
    # Subjects the group covers (ManyToMany)
    subjects = models.ManyToManyField(Subject)
    
    # Members of the group (ManyToMany, including the creator)
    members = models.ManyToManyField(
        User, 
        related_name='study_groups', 
        blank=True
    ) 

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

# --- 4. Resource Model (Corresponds to UserGroup in ERD) ---
class Resource(models.Model):
    """
    A link or document shared within a specific study group (UserGroup in the ERD).
    """
    # The group this resource belongs to (ForeignKey)
    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE)
    
    # The user who uploaded the resource (ForeignKey)
    uploaded_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True
    )
    
    title = models.CharField(max_length=255)
    link = models.URLField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
        
    class Meta:
        ordering = ['-created_at']

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Automatically creates a UserProfile when a new User is created.
    Also ensures the profile is saved if the User is updated.
    """
    if created:
        UserProfile.objects.create(user=instance)
    # If the user is being updated, save the profile too (optional, but robust)
    # instance.profile.save() # Uncomment if you want to ensure profile saves on user update