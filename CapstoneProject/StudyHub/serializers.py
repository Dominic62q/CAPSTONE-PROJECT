from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Subject, UserProfile, StudyGroup, Resource

# --- Basic Serializers for Nesting ---

class SubjectSerializer(serializers.ModelSerializer):
    """Serializer for the Subject model."""
    class Meta:
        model = Subject
        fields = ['id', 'name']
        read_only_fields = ['id']


class UserProfileSerializer(serializers.ModelSerializer):
    """Used to display a user's interests."""
    username = serializers.CharField(source='user.username', read_only=True)
    
    # Nest subjects to show the actual names, not just IDs
    subjects = SubjectSerializer(many=True, read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['username', 'subjects']


class ResourceSerializer(serializers.ModelSerializer):
    """Serializer for Resource model."""
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    
    class Meta:
        model = Resource
        fields = ['id', 'title', 'link', 'group', 'uploaded_by_username', 'created_at']
        read_only_fields = ['uploaded_by_username', 'created_at']


# --- Core StudyGroup Serializer ---

class StudyGroupSerializer(serializers.ModelSerializer):
    """Serializer for the StudyGroup model, with nesting for read operations."""
    
    # Display subjects using the nested serializer
    subjects = SubjectSerializer(many=True, read_only=True)
    
    # Display member usernames instead of just IDs
    # Using SlugRelatedField is cleaner than nesting a full User serializer
    members = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='username'
    )
    
    # Read-only field for the creator's username
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    # Nested field to display all resources associated with the group
    resources = ResourceSerializer(source='resource_set', many=True, read_only=True)


    class Meta:
        model = StudyGroup
        fields = [
            'id', 'name', 'description', 
            'created_by_username', 'subjects', 
            'members', 'resources'
        ]
        read_only_fields = ['created_by_username', 'members', 'resources']
    
    def create(self, validated_data):
        """Override create to automatically assign the creator (created_by) and add them to members."""
        user = self.context['request'].user
        validated_data['created_by'] = user
        
        # Create the group instance
        group = StudyGroup.objects.create(**validated_data)
        
        # Add the creator to the members list (M2M must be set after creation)
        group.members.add(user)
        return group


# --- Serializer for User Matching (Simplified) ---

class UserMatchSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing matching users."""
    username = serializers.CharField(source='user.username', read_only=True)
    subjects = SubjectSerializer(many=True, read_only=True)

    class Meta:
        model = UserProfile
        fields = ['username', 'subjects']