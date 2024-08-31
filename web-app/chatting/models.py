from django.db import models
from django.contrib.auth.models import User
 
  
class XeroToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    access_token = models.JSONField(null=True)
    refresh_token = models.TextField(null=True)
    expires_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete= models.CASCADE)
    token = models.TextField(max_length=200, null= True)
    first_name = models.TextField(max_length=300, null=True)
    last_name = models.TextField(max_length=300, null=True)
    phone = models.TextField(max_length=100, null=True)
    free_trail = models.BooleanField(default=False)
    cancel_subscription = models.BooleanField(default=False)
    payment_expiration_date = models.DateTimeField(null=True)
    is_payment = models.BooleanField(default=False)
    stripe_customer_id = models.CharField(max_length=50, blank=True, null=True)
    is_xero_connection = models.BooleanField(default=False)


class Document(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document_name = models.CharField(max_length=300)
    file_size = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self) -> str:
        return self.document_name
 

class DocumetChatHistory(models.Model):
    question = models.TextField()
    ai_result = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    track_chat_id = models.CharField(max_length=500, default='foobar')
    created_at = models.DateTimeField(auto_now_add=True)
 

class XeroChatHistory(models.Model):
    question = models.TextField()
    ai_result = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    track_chat_id = models.CharField(max_length=500,default='foobar')
    created_at = models.DateTimeField(auto_now_add=True)