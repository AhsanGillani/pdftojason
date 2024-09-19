from django.urls import path
from .views import PDFExtractAPIView
from .views import TaxExemptAPIView
from .views import ClerkActivityAPIView
from .views import FinalAuditAPIView
urlpatterns = [
    path('extract/', PDFExtractAPIView.as_view(), name='extract_pdf'),
    path('tax-exempt/', TaxExemptAPIView.as_view(), name='tax_exempt'),
    path('clerk-activity/', ClerkActivityAPIView.as_view(), name='clerk_activity'),
    path('final-audit-extract/', FinalAuditAPIView.as_view(), name='final-audit-extract'),


]
