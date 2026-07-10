from django.urls import path
from apps.payments.views import ZibalCallbackView

app_name = 'payments'

urlpatterns = [
    path('zibal/callback/', ZibalCallbackView.as_view(), name='zibal_callback'),
]
