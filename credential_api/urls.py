from django.urls import path
from . import views

urlpatterns = [
    path('issue/', views.issue_credential, name='issue_credential'),
    path('verify/<str:document_hash>/', views.verify_credential, name='verify_credential'),
    
]