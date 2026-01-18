# documents/models.py
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from core.models import CustomUser

class DocumentType(models.Model):
    name = models.CharField(max_length=100)  # e.g., Land Title, Invoice, Contract

    def __str__(self):
        return self.name

class Document(models.Model):
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='documents/%Y/%m/%d/')
    document_type = models.ForeignKey(DocumentType, on_delete=models.SET_NULL, null=True)
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)

    # Generic relation
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return self.title