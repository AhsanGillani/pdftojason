from django.urls import path
from .views import PDFExtractAPIView
from .views import TaxExemptAPIView
from .views import ClerkActivityAPIView
from .views import FinalAuditAPIView
from .views import OccupancyForecastAPIView
from .views import RateTypeTrackingAPIView
from .views import AccountActivity
from .views import Rateplansummary
from .views import Adjustmentandrefund
from .views import Directbilagging
from .views import Rateplansummaryhampton
from .views import TaxReport
from .views import SentimentAnalysisView
from .views import QRCodeScanView

urlpatterns = [

    path('extract/', PDFExtractAPIView.as_view(), name='extract_pdf'),
    path('tax-exempt/', TaxExemptAPIView.as_view(), name='tax_exempt'),
    path('clerk-activity/', ClerkActivityAPIView.as_view(), name='clerk_activity'),
    path('final-audit-extract/', FinalAuditAPIView.as_view(), name='final-audit-extract'),
    path('occupancy-forecast/', OccupancyForecastAPIView.as_view(), name='occupancy_forecast'),
    path('rate-type-tracking/', RateTypeTrackingAPIView.as_view(), name='rate_type_tracking'),
    path('Payment-Activity/', AccountActivity.as_view(), name='Payment_Activity'),
    path('Rate-Plan-Summary/', Rateplansummary.as_view(), name='Rate_Plan_Summary'),
    path('adjustment-plan/', Adjustmentandrefund.as_view(), name='adjustment_plan'),
    path('Direct-Bill-Agging/', Directbilagging.as_view(), name='Direct_Bill_Agging'),
    path('Rate-plan-summary-hampton/', Rateplansummaryhampton.as_view(), name='Rate_plan_summary_hampton'),
    path('Tax-Report-Hotels/', TaxReport.as_view(), name='Tax_Report'),


    path('sentiment-analysis/', SentimentAnalysisView.as_view(), name='sentiment-analysis'),
    path('scan/', QRCodeScanView.as_view(), name='qr-scan'),


]
