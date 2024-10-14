from django.urls import path
from .views import PDFExtractAPIView
from .views import TaxExemptAPIView
from .views import ClerkActivityAPIView
from .views import FinalAuditAPIView
from .views import OccupancyForecastAPIView
from .views import RateTypeTrackingAPIView
from .views import AccountActivity
from .views import Rateplansummary

urlpatterns = [

    path('extract/', PDFExtractAPIView.as_view(), name='extract_pdf'),
    path('tax-exempt/', TaxExemptAPIView.as_view(), name='tax_exempt'),
    path('clerk-activity/', ClerkActivityAPIView.as_view(), name='clerk_activity'),
    path('final-audit-extract/', FinalAuditAPIView.as_view(), name='final-audit-extract'),
    path('occupancy-forecast/', OccupancyForecastAPIView.as_view(), name='occupancy_forecast'),
    path('rate-type-tracking/', RateTypeTrackingAPIView.as_view(), name='rate_type_tracking'),
    path('Payment-Activity/', AccountActivity.as_view(), name='Payment_Activity'),
    path('Rate-Plan-Summary/', Rateplansummary.as_view(), name='Rate_Plan_Summary'),
    


]
