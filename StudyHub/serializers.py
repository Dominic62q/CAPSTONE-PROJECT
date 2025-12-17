from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Subject, UserProfile, StudyGroup, Resource

# --- 1. User Registration ---
class UserRegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)
    
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
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )

# --- 2. Basic Models ---
class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name']
        read_only_fields = ['id', 'name']

class ResourceSerializer(serializers.ModelSerializer):
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)

    class Meta:
        model = Resource
        fields = ['id', 'title', 'file', 'link', 'group', 'uploaded_by_username', 'created_at']
        read_only_fields = ['uploaded_by_username', 'created_at']

# --- 3. User Matching ---
class UserMatchSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    subjects = SubjectSerializer(many=True, read_only=True)

    class Meta:
        model = UserProfile
        fields = ['username', 'subjects']

# --- 4. Study Group (FIXED) ---
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
            'members'
            # REMOVED 'created_at' because it does not exist in your models.py
        ]
        read_only_fields = ['created_by_username', 'members']
        extra_kwargs = {
            'subjects': {'required': False}
        }