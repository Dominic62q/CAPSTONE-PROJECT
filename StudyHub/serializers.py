from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Subject, UserProfile, StudyGroup, Resource

# --- Basic Serializers for Nesting ---
# --- New: User Registration Serializer ---
class UserRegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords must match."})
        return data

    def create(self, validated_data):
        # Create the User object
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        # REMOVED: UserProfile.objects.create(user=user) - This is now handled by the signal.
        return user
class SubjectSerializer(serializers.ModelSerializer):
    """Serializer for the Subject model."""
    class Meta:
        model = Subject
        fields = ['id', 'name']
        read_only_fields = ['id', 'name']


class ResourceSerializer(serializers.ModelSerializer):
    uploaded_by_username = serializers.CharField(
        source='uploaded_by.username',
        read_only=True
    )

    class Meta:
        model = Resource
        fields = [
            'id',
            'title',
            'file',
            'link',
            'group',
            'uploaded_by_username',
            'created_at'
        ]
        read_only_fields = ['uploaded_by_username', 'created_at']

    
class StudyGroupSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(
        source='created_by.username',
        read_only=True
    )

    class Meta:
        model = StudyGroup
        fields = [
            'id',
            'name',
            'description',
            'subjects',
            'created_by_username',
            'members',
            'created_at',
        ]
        read_only_fields = ['created_by_username', 'members', 'created_at']

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user

        group = StudyGroup.objects.create(**validated_data)
        group.members.add(user)
        return group



# --- Serializer for User Matching ---

class UserMatchSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing matching users."""
    username = serializers.CharField(source='user.username', read_only=True)
    subjects = SubjectSerializer(many=True, read_only=True)

    class Meta:
        model = UserProfile
        fields = ['username', 'subjects']