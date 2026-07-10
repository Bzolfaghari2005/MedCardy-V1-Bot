"""
Zibal IPG integration service.
Docs: https://zibal.ir/fa/developers
"""
import logging
from dataclasses import dataclass, field
from typing import Optional
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

ZIBAL_BASE_URL = 'https://gateway.zibal.ir'
REQUEST_TIMEOUT = 15


@dataclass
class PaymentRequestResult:
    success: bool
    track_id: Optional[str] = None
    result_code: Optional[int] = None
    message: str = ''
    raw_response: dict = field(default_factory=dict)


@dataclass
class VerifyResult:
    success: bool
    result_code: Optional[int] = None
    status: Optional[int] = None
    message: str = ''
    ref_number: Optional[str] = None
    card_number: Optional[str] = None
    hashed_card_number: Optional[str] = None
    amount: Optional[int] = None
    raw_response: dict = field(default_factory=dict)


@dataclass
class InquiryResult:
    success: bool
    result_code: Optional[int] = None
    status: Optional[int] = None
    message: str = ''
    raw_response: dict = field(default_factory=dict)


class ZibalPaymentService:

    def __init__(self):
        self.merchant = settings.ZIBAL_MERCHANT
        self.base_url = getattr(settings, 'ZIBAL_BASE_URL', ZIBAL_BASE_URL)
        self.callback_url = settings.ZIBAL_CALLBACK_URL
        self.test_mode = getattr(settings, 'ZIBAL_TEST_MODE', False)

        # In test mode always use Zibal sandbox merchant (no IP whitelist needed).
        if self.test_mode:
            self.merchant = 'zibal'

    def request_payment(self, payment) -> PaymentRequestResult:
        """
        Call Zibal /v1/request and return a PaymentRequestResult.
        `payment` is a Payment model instance.
        """
        payload = {
            'merchant': self.merchant,
            'amount': int(payment.amount_rial),
            'callbackUrl': self.callback_url,
            'description': payment.description or f'MedCardy - {payment.payment_code}',
            'orderId': payment.payment_code,
        }
        if payment.user.phone_number:
            payload['mobile'] = payment.user.phone_number

        # Save request payload (excluding merchant)
        safe_payload = {k: v for k, v in payload.items() if k != 'merchant'}
        payment.request_payload = safe_payload
        payment.save(update_fields=['request_payload'])

        logger.info(f'Zibal request for payment {payment.payment_code}, amount_rial={payment.amount_rial}')

        try:
            response = requests.post(
                f'{self.base_url}/v1/request',
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as exc:
            logger.error(f'Zibal request error for {payment.payment_code}: {exc}')
            payment.request_response = {'error': str(exc)}
            payment.save(update_fields=['request_response'])
            return PaymentRequestResult(success=False, message=str(exc))

        payment.request_response = data
        payment.save(update_fields=['request_response'])

        logger.info(f'Zibal request response for {payment.payment_code}: result={data.get("result")}')

        if data.get('result') == 100:
            track_id = str(data.get('trackId', ''))
            return PaymentRequestResult(
                success=True,
                track_id=track_id,
                result_code=100,
                message='درخواست پرداخت با موفقیت ایجاد شد',
                raw_response=data,
            )
        else:
            msg = data.get('message', 'خطا در ایجاد درخواست پرداخت')
            return PaymentRequestResult(
                success=False,
                result_code=data.get('result'),
                message=msg,
                raw_response=data,
            )

    def verify_payment(self, track_id: str) -> VerifyResult:
        """Call Zibal /v1/verify for the given trackId."""
        payload = {
            'merchant': self.merchant,
            'trackId': track_id,
        }

        logger.info(f'Zibal verify for trackId={track_id}')

        try:
            response = requests.post(
                f'{self.base_url}/v1/verify',
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as exc:
            logger.error(f'Zibal verify error for trackId={track_id}: {exc}')
            return VerifyResult(success=False, message=str(exc))

        logger.info(f'Zibal verify response for trackId={track_id}: result={data.get("result")}')

        result_code = data.get('result')
        if result_code in (100, 201):
            return VerifyResult(
                success=True,
                result_code=result_code,
                status=data.get('status'),
                ref_number=str(data.get('refNumber', '')),
                card_number=str(data.get('cardNumber', '')),
                hashed_card_number=str(data.get('hashedCardNumber', '')),
                amount=data.get('amount'),
                message='پرداخت با موفقیت تأیید شد',
                raw_response=data,
            )
        else:
            msg = data.get('message', 'تأیید پرداخت ناموفق بود')
            return VerifyResult(
                success=False,
                result_code=result_code,
                status=data.get('status'),
                message=msg,
                raw_response=data,
            )

    def inquiry_payment(self, track_id: str) -> InquiryResult:
        """Optional: call Zibal /v1/inquiry for status check."""
        payload = {
            'merchant': self.merchant,
            'trackId': track_id,
        }
        try:
            response = requests.post(
                f'{self.base_url}/v1/inquiry',
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as exc:
            logger.error(f'Zibal inquiry error for trackId={track_id}: {exc}')
            return InquiryResult(success=False, message=str(exc))

        return InquiryResult(
            success=data.get('result') == 100,
            result_code=data.get('result'),
            status=data.get('status'),
            message=data.get('message', ''),
            raw_response=data,
        )

    def build_start_url(self, track_id: str) -> str:
        return f'{self.base_url}/start/{track_id}'
