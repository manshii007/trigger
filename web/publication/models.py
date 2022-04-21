from django.db import models
import uuid

# Create your models here.
class Publication(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	# publised_date = models.DateTimeField(auto_now_add=False, null=True)
	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)
	comment = models.TextField(blank=True)
	
	def __str__(self):
		return str(self.id)

	class Meta:
		permissions = (("view_publication", "Can view publication"),)