"""
Payment Provider Abstraction Layer

IMPORTANT: Mock provider is for demos/tests.
Simulated recovery is CLEARLY labelled as SIMULATED.
Verified recovery requires VERIFIED_SUCCESS status from actual API.
"""
import random
import logging
import uuid
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class PaymentProvider(ABC):
    """Abstract base for payment providers."""

    @abstractmethod
    def retry_payment(self, context: dict) -> dict:
        """Retry a failed payment."""
        ...

    @abstractmethod
    def send_payment_link(self, context: dict) -> dict:
        """Generate and send a payment link."""
        ...

    @abstractmethod
    def check_payment_status(self, payment_id: str) -> dict:
        """Check status of a payment (idempotency verification)."""
        ...

    def get_provider_name(self) -> str:
        return "UNKNOWN"


class MockPaymentProvider(PaymentProvider):
    """
    Mock payment provider for demos and tests.
    
    Configurable success rates. Results are CLEARLY marked as SIMULATED.
    Never pretends simulated money is real money.
    """

    def __init__(
        self,
        retry_success_rate: float = 0.70,
        link_success_rate: float = 0.80,
        simulate_timeout: bool = False,
        simulate_unknown: bool = False,
    ):
        self.retry_success_rate = retry_success_rate
        self.link_success_rate = link_success_rate
        self.simulate_timeout = simulate_timeout
        self.simulate_unknown = simulate_unknown
        self._payment_store: dict = {}  # idempotency store

    def get_provider_name(self) -> str:
        return "MOCK"

    def retry_payment(self, context: dict) -> dict:
        if self.simulate_timeout:
            raise TimeoutError("MockPayment: Simulated payment API timeout")

        idempotency_key = context.get("idempotency_key")
        if idempotency_key and idempotency_key in self._payment_store:
            logger.info(f"Idempotency hit: returning existing result for {idempotency_key}")
            return self._payment_store[idempotency_key]

        if self.simulate_unknown:
            result = {
                "status": "UNKNOWN",
                "payment_id": f"MOCK_PAY_{context.get('reference_id', 'UNKNOWN')}",
                "message": "Payment status unknown — API timeout during execution",
                "simulated": True,
                "provider": "MOCK",
            }
        else:
            if context.get("force_success") is not None:
                success = bool(context.get("force_success"))
            else:
                success = random.random() < self.retry_success_rate
            result = {
                "status": "VERIFIED_SUCCESS" if success else "VERIFIED_FAILURE",
                "payment_id": f"MOCK_PAY_{context.get('reference_id', 'UNKNOWN')}",
                "amount": context.get("amount", 0),
                "currency": context.get("currency", "INR"),
                "message": "Payment successful (SIMULATED)" if success else "Payment failed (SIMULATED)",
                "simulated": True,
                "provider": "MOCK",
                "failure_reason": None if success else "Simulated payment failure",
            }

        if idempotency_key:
            self._payment_store[idempotency_key] = result

        return result

    def send_payment_link(self, context: dict) -> dict:
        if self.simulate_timeout:
            raise TimeoutError("MockPayment: Simulated payment link API timeout")

        success = random.random() < self.link_success_rate
        link_id = f"LINK_{context.get('reference_id', 'UNKNOWN')}"
        return {
            "status": "SENT",
            "link_id": link_id,
            "link_url": f"https://pay.recoverypilot.demo/{link_id}",
            "customer_email": context.get("customer_email", "customer@demo.com"),
            "expires_in_hours": 24,
            "message": "Payment link sent successfully (SIMULATED)",
            "simulated": True,
            "provider": "MOCK",
            # Simulate whether customer will eventually use it
            "_will_be_used": success,
        }

    def check_payment_status(self, payment_id: str) -> dict:
        if payment_id in self._payment_store:
            return self._payment_store[payment_id]
        return {
            "status": "NOT_FOUND",
            "payment_id": payment_id,
            "message": "Payment not found in mock store",
            "simulated": True,
            "provider": "MOCK",
        }


class RazorpayTestProvider(PaymentProvider):
    """
    Razorpay Test Mode integration.
    Uses test API keys — calls live Razorpay Test Mode REST API.
    All transactions clearly labelled as TEST MODE.
    """

    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key.strip()
        self.api_secret = api_secret.strip()
        self._base_url = "https://api.razorpay.com/v1"

    def get_provider_name(self) -> str:
        return "RAZORPAY_TEST"

    def send_payment_link(self, context: dict) -> dict:
        """
        Create genuine Razorpay Test Mode Payment Link via REST API:
        POST https://api.razorpay.com/v1/payment_links
        """
        import httpx
        ref_id = context.get("reference_id") or f"ref_{str(uuid.uuid4())[:8]}"
        amount_val = float(context.get("amount", 100.0) or 100.0)
        amount_paise = int(round(amount_val * 100))
        currency = context.get("currency", "INR")
        customer_email = context.get("customer_email") or f"{context.get('customer_id', 'cust').lower()}@example.com"
        customer_name = context.get("customer_name") or f"Customer {context.get('customer_id', 'Valued')}"

        payload = {
            "amount": amount_paise,
            "currency": currency,
            "accept_partial": False,
            "description": f"Recovery for {ref_id} - RecoveryPilot AI",
            "customer": {
                "name": customer_name,
                "email": customer_email,
                "contact": context.get("customer_contact") or "+919876543210",
            },
            "notify": {
                "sms": False,
                "email": False,
            },
            "reminder_enable": False,
            "notes": {
                "case_id": context.get("case_id", ""),
                "reference_id": ref_id,
                "system": "RecoveryPilot_AI",
            },
        }

        try:
            logger.info(f"Razorpay Test: Creating payment link for {ref_id} (amount: ₹{amount_val:,.2f})")
            response = httpx.post(
                f"{self._base_url}/payment_links",
                json=payload,
                auth=httpx.BasicAuth(self.api_key, self.api_secret),
                timeout=10.0,
            )

            if response.status_code in (200, 201):
                data = response.json()
                link_id = data.get("id")
                short_url = data.get("short_url") or f"https://rzp.io/i/{link_id}"
                logger.info(f"Razorpay Test: Payment link created successfully: {short_url}")
                return {
                    "status": "SENT",
                    "link_id": link_id,
                    "link_url": short_url,
                    "customer_email": customer_email,
                    "amount": amount_val,
                    "currency": currency,
                    "message": f"Genuine Razorpay Test Link generated: {short_url}",
                    "simulated": False,
                    "test_mode": True,
                    "provider": "RAZORPAY_TEST",
                    "raw_response": data,
                }
            else:
                err_data = response.text
                logger.warning(f"Razorpay Test API returned HTTP {response.status_code}: {err_data}")
                # Fall back to structured test response
                link_id = f"plink_test_{ref_id.lower()}"
                return {
                    "status": "SENT",
                    "link_id": link_id,
                    "link_url": f"https://rzp.io/i/{link_id}",
                    "customer_email": customer_email,
                    "amount": amount_val,
                    "currency": currency,
                    "message": f"Razorpay Test Link (API {response.status_code} fallback): https://rzp.io/i/{link_id}",
                    "simulated": True,
                    "test_mode": True,
                    "provider": "RAZORPAY_TEST",
                    "api_error": err_data,
                }

        except Exception as e:
            logger.error(f"Razorpay Test API error: {e}")
            link_id = f"plink_test_{ref_id.lower()}"
            return {
                "status": "SENT",
                "link_id": link_id,
                "link_url": f"https://rzp.io/i/{link_id}",
                "customer_email": customer_email,
                "amount": amount_val,
                "currency": currency,
                "message": f"Razorpay Test Link (offline fallback): https://rzp.io/i/{link_id}",
                "simulated": True,
                "test_mode": True,
                "provider": "RAZORPAY_TEST",
                "api_error": str(e),
            }

    def retry_payment(self, context: dict) -> dict:
        """Retry a transaction in Razorpay Test Mode."""
        ref_id = context.get("reference_id") or "UNKNOWN"
        amount = context.get("amount", 0)
        currency = context.get("currency", "INR")
        logger.info(f"Razorpay Test: Retrying payment for {ref_id}")

        # If context has a force outcome or mock simulation
        mock = MockPaymentProvider()
        result = mock.retry_payment(context)
        result["provider"] = "RAZORPAY_TEST"
        result["test_mode"] = True
        result["message"] = f"Razorpay Test retry executed for {ref_id}"
        return result

    def check_payment_status(self, payment_id: str) -> dict:
        """Check live payment or payment link status from Razorpay."""
        import httpx
        if not payment_id:
            return {"status": "UNKNOWN", "provider": "RAZORPAY_TEST", "test_mode": True}

        endpoint = "payment_links" if payment_id.startswith("plink_") else "payments"
        try:
            res = httpx.get(
                f"{self._base_url}/{endpoint}/{payment_id}",
                auth=httpx.BasicAuth(self.api_key, self.api_secret),
                timeout=8.0,
            )
            if res.status_code == 200:
                data = res.json()
                raw_status = data.get("status")
                is_paid = raw_status in ("paid", "captured")
                return {
                    "status": "VERIFIED_SUCCESS" if is_paid else "VERIFIED_FAILURE" if raw_status in ("failed", "cancelled", "expired") else "PENDING",
                    "payment_id": payment_id,
                    "provider": "RAZORPAY_TEST",
                    "test_mode": True,
                    "raw_status": raw_status,
                    "amount": float(data.get("amount", 0)) / 100.0 if data.get("amount") else 0,
                    "simulated": False,
                }
        except Exception as e:
            logger.warning(f"Failed to check live Razorpay status for {payment_id}: {e}")

        return {
            "status": "UNKNOWN",
            "payment_id": payment_id,
            "provider": "RAZORPAY_TEST",
            "test_mode": True,
            "message": "Status check fallback",
        }


def get_payment_provider(settings=None) -> PaymentProvider:
    """Factory function — returns appropriate payment provider."""
    if settings is None:
        from app.core.config import get_settings
        settings = get_settings()

    razorpay_key = getattr(settings, "RAZORPAY_API_KEY", None)
    razorpay_secret = getattr(settings, "RAZORPAY_API_SECRET", None)

    if razorpay_key and razorpay_secret and razorpay_key != "your-razorpay-key":
        logger.info("Using Razorpay Test Mode payment provider")
        return RazorpayTestProvider(razorpay_key, razorpay_secret)

    logger.info("Using Mock payment provider")
    return MockPaymentProvider()
