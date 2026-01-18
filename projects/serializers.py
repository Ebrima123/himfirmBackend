# projects/serializers.py
from rest_framework import serializers
from .models import LandParcel, Project, ProjectTask
from documents.serializers import DocumentSerializer
from core.models import EmployeeProfile

class LandParcelSerializer(serializers.ModelSerializer):
    documents = DocumentSerializer(many=True, read_only=True)

    class Meta:
        model = LandParcel
        fields = '__all__'

class ProjectSerializer(serializers.ModelSerializer):
    land_parcel_title = serializers.CharField(source='land_parcel.title_number', read_only=True)
    manager_name = serializers.CharField(source='manager.user.get_full_name', read_only=True)
    documents = DocumentSerializer(many=True, read_only=True)
    task_count = serializers.IntegerField(source='tasks.count', read_only=True)

    class Meta:
        model = Project
        fields = '__all__'

class ProjectTaskSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.user.get_full_name', read_only=True)

    class Meta:
        model = ProjectTask
        fields = '__all__'