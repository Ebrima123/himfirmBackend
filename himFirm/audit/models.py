# audit/models.py
from django.db import models

class AuditLog(models.Model):
    user = models.ForeignKey('core.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)  # e.g., "CREATE", "UPDATE", "DELETE"
    model_name = models.CharField(max_length=100)  # e.g., "Project", "Allocation"
    object_id = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    changes = models.JSONField(null=True, blank=True)  # Stores old/new values as dict

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'

    def __str__(self):
        return f"{self.action} on {self.model_name} #{self.object_id} by {self.user or 'System'}"