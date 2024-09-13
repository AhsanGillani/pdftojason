from django.urls import path
from .views import PDFExtractAPIView

urlpatterns = [
    path('extract/', PDFExtractAPIView.as_view(), name='extract_pdf'),
]
