import logging
from django.http import HttpResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

SUCCESS_HTML = """<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MedCardy - پرداخت موفق</title>
<style>
  body {{ font-family: Tahoma, Arial, sans-serif; background: #f0fdf4; display: flex;
         align-items: center; justify-content: center; min-height: 100vh; margin: 0; }}
  .card {{ background: white; border-radius: 16px; padding: 40px; text-align: center;
           max-width: 420px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); }}
  h1 {{ color: #16a34a; font-size: 22px; margin-bottom: 12px; }}
  p {{ color: #374151; line-height: 1.7; }}
  a {{ display: inline-block; margin: 8px 4px; padding: 12px 24px; border-radius: 10px;
       text-decoration: none; font-weight: bold; font-size: 15px; }}
  .btn-primary {{ background: #0ea5e9; color: white; }}
  .btn-secondary {{ background: #f3f4f6; color: #374151; border: 1px solid #e5e7eb; }}
  .icon {{ font-size: 48px; margin-bottom: 16px; }}
</style>
</head>
<body>
<div class="card">
  <div class="icon">✅</div>
  <h1>پرداخت موفق بود</h1>
  <p>پرداخت شما با موفقیت انجام شد.<br>
  لطفاً به بات MedCardy برگردید.<br>
  وضعیت خرید یا سفارش از طریق بات برای شما ارسال می‌شود.</p>
  <br>
  <a href="https://t.me/{bot_username}" class="btn-primary">🤖 بازگشت به بات MedCardy</a>
  <a href="https://t.me/{support_username}" class="btn-secondary">💬 تماس با پشتیبانی</a>
</div>
</body>
</html>"""

FAILURE_HTML = """<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MedCardy - پرداخت ناموفق</title>
<style>
  body {{ font-family: Tahoma, Arial, sans-serif; background: #fef2f2; display: flex;
         align-items: center; justify-content: center; min-height: 100vh; margin: 0; }}
  .card {{ background: white; border-radius: 16px; padding: 40px; text-align: center;
           max-width: 420px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); }}
  h1 {{ color: #dc2626; font-size: 22px; margin-bottom: 12px; }}
  p {{ color: #374151; line-height: 1.7; }}
  a {{ display: inline-block; margin: 8px 4px; padding: 12px 24px; border-radius: 10px;
       text-decoration: none; font-weight: bold; font-size: 15px; }}
  .btn-primary {{ background: #0ea5e9; color: white; }}
  .btn-secondary {{ background: #f3f4f6; color: #374151; border: 1px solid #e5e7eb; }}
  .icon {{ font-size: 48px; margin-bottom: 16px; }}
</style>
</head>
<body>
<div class="card">
  <div class="icon">❌</div>
  <h1>پرداخت ناموفق بود</h1>
  <p>پرداخت شما موفق نبود.<br>
  اگر مبلغی از حساب شما کم شده باشد، طبق قوانین بانکی به حساب شما برگشت داده می‌شود.<br>
  لطفاً دوباره تلاش کنید یا با پشتیبانی MedCardy تماس بگیرید.</p>
  <br>
  <a href="https://t.me/{bot_username}" class="btn-primary">🤖 بازگشت به بات MedCardy</a>
  <a href="https://t.me/{support_username}" class="btn-secondary">💬 تماس با پشتیبانی</a>
</div>
</body>
</html>"""


@method_decorator(csrf_exempt, name='dispatch')
class ZibalCallbackView(View):
    """
    GET /api/payments/zibal/callback/
    Zibal redirects the user here after payment.
    """

    def get(self, request):
        from django.conf import settings
        bot_username = getattr(settings, 'TELEGRAM_BOT_USERNAME', 'MedCardyBot')
        support_username = getattr(settings, 'DEFAULT_SUPPORT_USERNAME', 'MedCardySupport').lstrip('@')

        params = dict(request.GET)
        flat_params = {k: v[0] if isinstance(v, list) else v for k, v in params.items()}

        logger.info(f'Zibal callback received: {flat_params}')

        try:
            from apps.payments.services.payment_service import handle_zibal_callback
            payment, verified, message = handle_zibal_callback(flat_params)
        except Exception as exc:
            logger.error(f'Zibal callback processing error: {exc}', exc_info=True)
            return HttpResponse(
                FAILURE_HTML.format(bot_username=bot_username, support_username=support_username),
                content_type='text/html; charset=utf-8',
                status=200,
            )

        if verified:
            return HttpResponse(
                SUCCESS_HTML.format(bot_username=bot_username, support_username=support_username),
                content_type='text/html; charset=utf-8',
                status=200,
            )
        else:
            return HttpResponse(
                FAILURE_HTML.format(bot_username=bot_username, support_username=support_username),
                content_type='text/html; charset=utf-8',
                status=200,
            )
