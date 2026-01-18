# documents/serializers.py
from rest_framework import serializers
from .models import Document, DocumentType

class DocumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentType
        fields = '__all__'

class DocumentSerializer(serializers.ModelSerializer):
    document_type = DocumentTypeSerializer(read_only=True)
    uploaded_by = serializers.StringRelatedField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = '__all__'

    def get_file_url(self, obj):
        return obj.file.url if obj.file else None