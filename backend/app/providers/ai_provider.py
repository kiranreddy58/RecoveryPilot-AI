"""
AI Provider Abstraction Layer

Architecture: AI PROPOSES → Guardian validates → Only approved actions execute.
The provider is ONLY responsible for generating analysis and suggestions.
It has NO power to execute anything directly.
"""
import random
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    def analyze_root_cause(self, context: dict) -> dict:
        """Analyze root cause of a revenue loss event."""
        ...

    @abstractmethod
    def generate_strategies(self, context: dict) -> list[dict]:
        """Generate recovery strategy proposals."""
        ...

    @abstractmethod
    def generate_communication(self, context: dict, language: str = "EN") -> str:
        """Generate a recovery communication message."""
        ...

    @abstractmethod
    def summarize_case(self, context: dict) -> str:
        """Generate a human-readable case summary."""
        ...

    def is_available(self) -> bool:
        return True


# ─────────────────────────────────────────────────────────
# MOCK AI PROVIDER — deterministic, always works, great for demos
# ─────────────────────────────────────────────────────────

ROOT_CAUSE_MAP = {
    "PAYMENT_FAILED": [
        {"cause": "Temporary bank timeout", "category": "TECHNICAL", "confidence": 0.91},
        {"cause": "Insufficient funds", "category": "FINANCIAL", "confidence": 0.85},
        {"cause": "Card expired", "category": "TECHNICAL", "confidence": 0.88},
        {"cause": "Network connectivity issue", "category": "TECHNICAL", "confidence": 0.79},
        {"cause": "Daily transaction limit exceeded", "category": "FINANCIAL", "confidence": 0.82},
        {"cause": "Payment gateway timeout", "category": "TECHNICAL", "confidence": 0.87},
        {"cause": "UPI declined by bank", "category": "TECHNICAL", "confidence": 0.90},
        {"cause": "Fraud risk flag by bank", "category": "RISK", "confidence": 0.75},
    ],
    "CHECKOUT_ABANDONED": [
        {"cause": "High shipping cost at checkout", "category": "BEHAVIOURAL", "confidence": 0.83},
        {"cause": "Distraction or intent to compare prices", "category": "BEHAVIOURAL", "confidence": 0.78},
        {"cause": "Preferred payment method unavailable", "category": "TECHNICAL", "confidence": 0.81},
        {"cause": "Complicated checkout UX", "category": "BEHAVIOURAL", "confidence": 0.76},
        {"cause": "Customer waiting for discount code", "category": "BEHAVIOURAL", "confidence": 0.80},
    ],
    "INVOICE_OVERDUE": [
        {"cause": "Cash flow delay on customer side", "category": "FINANCIAL", "confidence": 0.84},
        {"cause": "Invoice not received by accounts payable", "category": "OPERATIONAL", "confidence": 0.79},
        {"cause": "Dispute on invoice amount", "category": "OPERATIONAL", "confidence": 0.72},
        {"cause": "Repeated broken promises", "category": "BEHAVIOURAL", "confidence": 0.88},
        {"cause": "Customer facing financial distress", "category": "FINANCIAL", "confidence": 0.65},
    ],
    "SUBSCRIPTION_PAYMENT_FAILED": [
        {"cause": "Card expired since subscription started", "category": "TECHNICAL", "confidence": 0.89},
        {"cause": "Insufficient funds at billing date", "category": "FINANCIAL", "confidence": 0.85},
        {"cause": "Bank blocked recurring payment", "category": "TECHNICAL", "confidence": 0.83},
        {"cause": "Customer changed card details", "category": "TECHNICAL", "confidence": 0.87},
    ],
    "PROMISE_TO_PAY_BROKEN": [
        {"cause": "Cash flow shortfall persisted", "category": "FINANCIAL", "confidence": 0.86},
        {"cause": "Customer unreachable", "category": "BEHAVIOURAL", "confidence": 0.78},
        {"cause": "Disputed payment amount", "category": "OPERATIONAL", "confidence": 0.73},
    ],
    "MANDATE_PAYMENT_FAILED": [
        {"cause": "Mandate limit exceeded", "category": "TECHNICAL", "confidence": 0.88},
        {"cause": "Bank rejected NACH mandate", "category": "TECHNICAL", "confidence": 0.85},
        {"cause": "Account closed or changed", "category": "FINANCIAL", "confidence": 0.79},
    ],
}

STRATEGY_TEMPLATES = {
    "PAYMENT_FAILED": [
        {
            "strategy_name": "RETRY_PAYMENT",
            "strategy_label": "Safe Retry",
            "description": "Retry the payment using the same method after a short delay.",
            "base_probability": 0.60,
            "operational_cost": 0,
            "discount_amount": 0,
        },
        {
            "strategy_name": "SEND_PAYMENT_LINK",
            "strategy_label": "Alternative Payment Link",
            "description": "Send a secure payment link via email/SMS for customer to pay using a different method.",
            "base_probability": 0.75,
            "operational_cost": 50,
            "discount_amount": 0,
        },
        {
            "strategy_name": "WAIT_AND_RETRY",
            "strategy_label": "Wait & Retry (24h)",
            "description": "Wait 24 hours and retry, allowing customer funds to replenish.",
            "base_probability": 0.55,
            "operational_cost": 0,
            "discount_amount": 0,
        },
        {
            "strategy_name": "OFFER_EMI",
            "strategy_label": "Offer EMI / Instalment Plan",
            "description": "Offer the customer a no-cost EMI plan to reduce barrier to payment.",
            "base_probability": 0.70,
            "operational_cost": 200,
            "discount_amount": 0,
        },
    ],
    "CHECKOUT_ABANDONED": [
        {
            "strategy_name": "DO_NOTHING",
            "strategy_label": "No Action",
            "description": "Do not contact customer. They may return organically.",
            "base_probability": 0.15,
            "operational_cost": 0,
            "discount_amount": 0,
        },
        {
            "strategy_name": "SEND_RECOVERY_LINK",
            "strategy_label": "Recovery Link",
            "description": "Send personalised recovery link restoring exact cart.",
            "base_probability": 0.45,
            "operational_cost": 30,
            "discount_amount": 0,
        },
        {
            "strategy_name": "SEND_DISCOUNT_OFFER",
            "strategy_label": "Discount Offer",
            "description": "Offer 5% discount to incentivise checkout completion.",
            "base_probability": 0.65,
            "operational_cost": 30,
            "discount_amount": None,  # Calculated at runtime as % of amount
        },
    ],
    "INVOICE_OVERDUE": [
        {
            "strategy_name": "SEND_REMINDER",
            "strategy_label": "Polite Reminder",
            "description": "Send a polite overdue payment reminder.",
            "base_probability": 0.50,
            "operational_cost": 0,
            "discount_amount": 0,
        },
        {
            "strategy_name": "ESCALATE_TO_HUMAN",
            "strategy_label": "Human Follow-Up",
            "description": "Assign case to human accounts team for direct follow-up.",
            "base_probability": 0.72,
            "operational_cost": 500,
            "discount_amount": 0,
        },
        {
            "strategy_name": "LEGAL_NOTICE",
            "strategy_label": "Legal Notice Warning",
            "description": "Inform customer of impending legal action if payment not received.",
            "base_probability": 0.80,
            "operational_cost": 1000,
            "discount_amount": 0,
        },
    ],
    "SUBSCRIPTION_PAYMENT_FAILED": [
        {
            "strategy_name": "RETRY_PAYMENT",
            "strategy_label": "Retry Billing",
            "description": "Retry subscription billing.",
            "base_probability": 0.55,
            "operational_cost": 0,
            "discount_amount": 0,
        },
        {
            "strategy_name": "SEND_CARD_UPDATE_LINK",
            "strategy_label": "Card Update Link",
            "description": "Send a secure link for customer to update their payment method.",
            "base_probability": 0.78,
            "operational_cost": 30,
            "discount_amount": 0,
        },
        {
            "strategy_name": "PAUSE_SUBSCRIPTION",
            "strategy_label": "Pause Subscription",
            "description": "Pause subscription temporarily and send payment update request.",
            "base_probability": 0.62,
            "operational_cost": 0,
            "discount_amount": 0,
        },
    ],
    "PROMISE_TO_PAY_BROKEN": [
        {
            "strategy_name": "SEND_PAYMENT_LINK",
            "strategy_label": "Payment Link",
            "description": "Send a new secure payment link with a deadline.",
            "base_probability": 0.58,
            "operational_cost": 30,
            "discount_amount": 0,
        },
        {
            "strategy_name": "ESCALATE_TO_HUMAN",
            "strategy_label": "Human Escalation",
            "description": "Assign to collections team for direct resolution.",
            "base_probability": 0.75,
            "operational_cost": 500,
            "discount_amount": 0,
        },
    ],
    "MANDATE_PAYMENT_FAILED": [
        {
            "strategy_name": "RETRY_MANDATE",
            "strategy_label": "Retry Mandate",
            "description": "Retry the NACH/UPI mandate debit.",
            "base_probability": 0.60,
            "operational_cost": 0,
            "discount_amount": 0,
        },
        {
            "strategy_name": "SEND_PAYMENT_LINK",
            "strategy_label": "Manual Payment Link",
            "description": "Send manual payment link for this cycle while mandate is fixed.",
            "base_probability": 0.70,
            "operational_cost": 30,
            "discount_amount": 0,
        },
    ],
}

HINGLISH_TEMPLATES = {
    "PAYMENT_FAILED": [
        "Namaste! Aapka ₹{amount} ka payment process nahi ho saka. Koi baat nahi — yeh link se try karein: {link}",
        "Namaste {customer}! Aapki purchase ke liye payment fail ho gayi hai. Kripya is link se dobara try karein aur hum aapki madad karenge: {link}",
    ],
    "CHECKOUT_ABANDONED": [
        "Namaste! Aapne apna cart ₹{amount} ka chhod diya. Kya aap checkout complete karna chahenge? Yeh raha aapka cart link: {link}",
        "Aapka order aapka intezaar kar raha hai! ₹{amount} ka checkout abhi bhi pending hai. Yahan click karein: {link}",
    ],
    "INVOICE_OVERDUE": [
        "Namaste! Aapka ₹{amount} ka invoice overdue hai. Kripya jald se jald payment karein ya hamare team se baat karein.",
        "Aapka invoice ₹{amount} ka {days} din se pending hai. Hum aapki sahayata karne ke liye taiyaar hain — please contact karein.",
    ],
}


class MockAIProvider(AIProvider):
    """
    Deterministic mock AI — always succeeds, uses realistic templates.
    Perfect for demos, testing, and hackathon presentations.
    """

    def __init__(self, simulate_timeout: bool = False, confidence_override: float = None):
        self.simulate_timeout = simulate_timeout
        self.confidence_override = confidence_override

    def is_available(self) -> bool:
        return not self.simulate_timeout

    def analyze_root_cause(self, context: dict) -> dict:
        if self.simulate_timeout:
            raise TimeoutError("MockAI: Simulated AI provider timeout")

        event_type = str(context.get("event_type") or "PAYMENT_FAILED")
        candidates = ROOT_CAUSE_MAP.get(event_type, ROOT_CAUSE_MAP["PAYMENT_FAILED"])

        # Deterministically pick one based on context
        ref_val = str(context.get("reference_id") or context.get("case_id") or "ref")
        seed = hash(ref_val + event_type) % len(candidates)
        chosen = candidates[seed]

        confidence = self.confidence_override or chosen["confidence"]

        return {
            "root_cause": chosen["cause"],
            "root_cause_category": chosen["category"],
            "root_cause_detail": f"Analysis based on {event_type} pattern. {chosen['cause']} detected with {confidence:.0%} confidence.",
            "confidence": confidence,
            "ai_provider": "MOCK",
            "ai_model": "mock-v1",
            "fallback_used": None,
        }

    def generate_strategies(self, context: dict) -> list[dict]:
        if self.simulate_timeout:
            raise TimeoutError("MockAI: Simulated AI provider timeout")

        event_type = context.get("event_type", "PAYMENT_FAILED")
        amount = context.get("amount", 0) or 0
        templates = STRATEGY_TEMPLATES.get(event_type, STRATEGY_TEMPLATES["PAYMENT_FAILED"])

        strategies = []
        for i, tmpl in enumerate(templates):
            prob = tmpl["base_probability"]
            # Adjust probability slightly based on amount
            if amount > 100000:
                prob = max(0.3, prob - 0.05)  # High value = slightly harder
            elif amount < 1000:
                prob = min(0.95, prob + 0.05)  # Low value = easier

            discount = tmpl["discount_amount"]
            if discount is None:
                discount = amount * 0.05  # 5% of amount

            expected_net = (prob * amount) - tmpl["operational_cost"] - discount
            strategies.append({
                **tmpl,
                "recovery_probability": round(prob, 2),
                "discount_amount": round(discount, 2),
                "expected_net_recovery": round(max(0, expected_net), 2),
                "ai_explanation": f"Based on {event_type} analysis: {tmpl['description']}",
                "risk_notes": "Requires Guardian approval before execution." if amount > 50000 else "",
                "rank": i + 1,  # Will be re-ranked after sorting
            })

        # Sort by expected_net_recovery descending
        strategies.sort(key=lambda x: x["expected_net_recovery"], reverse=True)
        for i, s in enumerate(strategies):
            s["rank"] = i + 1

        return strategies

    def generate_communication(self, context: dict, language: str = "EN") -> str:
        event_type = context.get("event_type", "PAYMENT_FAILED")
        amount = context.get("amount", 0)
        customer_name = context.get("customer_name", "Valued Customer")

        if language == "HI" or language == "HINGLISH":
            templates = HINGLISH_TEMPLATES.get(event_type, HINGLISH_TEMPLATES["PAYMENT_FAILED"])
            ref_str = str(context.get("reference_id") or context.get("case_id") or "ref")
            seed = hash(ref_str) % len(templates)
            template = templates[seed]
            return template.format(
                amount=f"{amount:,.0f}",
                customer=customer_name,
                link="https://pay.recoverypilot.ai/secure-link",
                days=context.get("days_overdue", 0),
            )

        # English fallback
        messages = {
            "PAYMENT_FAILED": f"Hello {customer_name}, your payment of ₹{amount:,.0f} was unsuccessful. Please use this secure link to complete your payment: https://pay.recoverypilot.ai/secure-link",
            "CHECKOUT_ABANDONED": f"Hi {customer_name}, you left ₹{amount:,.0f} worth of items in your cart. Complete your purchase here: https://pay.recoverypilot.ai/cart",
            "INVOICE_OVERDUE": f"Dear {customer_name}, your invoice of ₹{amount:,.0f} is overdue. Please arrange payment at your earliest convenience.",
        }
        return messages.get(event_type, f"Hello {customer_name}, please take action on your pending payment of ₹{amount:,.0f}.")

    def summarize_case(self, context: dict) -> str:
        case_id = context.get("case_id", "UNKNOWN")
        event_type = context.get("event_type", "PAYMENT_FAILED")
        amount = context.get("amount", 0)
        root_cause = context.get("root_cause", "Unknown")
        confidence = context.get("confidence", 0)
        strategy = context.get("recommended_strategy", "Pending")

        return (
            f"Case {case_id}: {event_type.replace('_', ' ').title()} of ₹{amount:,.0f}. "
            f"Root cause: {root_cause} (confidence: {confidence:.0%}). "
            f"Recommended action: {strategy}."
        )


def _clean_json_response(raw_text: str) -> dict:
    """Helper to parse JSON even if wrapped in markdown codeblocks."""
    import json
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return json.loads(text)


class GeminiLiveProvider(AIProvider):
    """
    Live Google Gemini AI provider via REST API.
    Uses structured response schema with deterministic fallback.
    """

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash", timeout: int = 8):
        self.api_key = api_key.strip()
        self.model = model
        self.timeout = timeout
        self._fallback = MockAIProvider()

    def is_available(self) -> bool:
        return bool(self.api_key)

    def _call_gemini(self, prompt: str, system_instruction: str) -> str:
        import httpx
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.2,
                "maxOutputTokens": 800,
            }
        }
        resp = httpx.post(url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    def analyze_root_cause(self, context: dict) -> dict:
        try:
            system = (
                "You are an expert fintech revenue recovery AI for Razorpay merchants in India. "
                "Analyze the payment/invoice failure and return a JSON object with: "
                "root_cause (concise string), root_cause_category (TECHNICAL, FINANCIAL, BEHAVIOURAL, or OPERATIONAL), "
                "root_cause_detail (1-2 sentences explainable detail), confidence (float between 0.0 and 1.0)."
            )
            raw = self._call_gemini(f"Failure Context: {context}", system)
            parsed = _clean_json_response(raw)
            return {
                "root_cause": parsed.get("root_cause", "Bank processing timeout"),
                "root_cause_category": parsed.get("root_cause_category", "TECHNICAL"),
                "root_cause_detail": parsed.get("root_cause_detail", "Autonomous analysis of transaction failure parameters."),
                "confidence": float(parsed.get("confidence", 0.85)),
                "ai_provider": "gemini",
                "ai_model": self.model,
                "fallback_used": None,
            }
        except Exception as e:
            logger.warning(f"Gemini AI diagnosis failed: {e}. Utilizing deterministic fallback.")
            res = self._fallback.analyze_root_cause(context)
            res["fallback_used"] = "deterministic"
            return res

    def generate_strategies(self, context: dict) -> list[dict]:
        try:
            system = (
                "You are a fintech strategy engine. Generate an array of 3-4 candidate recovery strategies for this case. "
                "Return JSON array where each object has: strategy_name (e.g. RETRY_PAYMENT, SEND_PAYMENT_LINK, OFFER_EMI), "
                "strategy_label, description, recovery_probability (0.0 to 1.0), operational_cost (number in INR), "
                "discount_amount (number in INR, max 10% of amount), ai_explanation (why this strategy fits)."
            )
            raw = self._call_gemini(f"Case Context: {context}", system)
            parsed = _clean_json_response(raw)
            strategies = parsed if isinstance(parsed, list) else parsed.get("strategies", [])
            amount = float(context.get("amount", 0) or 0)
            formatted = []
            for i, s in enumerate(strategies):
                prob = float(s.get("recovery_probability", 0.6))
                cost = float(s.get("operational_cost", 0))
                disc = min(float(s.get("discount_amount", 0)), amount * 0.10)
                expected_net = max(0.0, round((prob * amount) - cost - disc, 2))
                formatted.append({
                    "strategy_name": s.get("strategy_name", "SEND_PAYMENT_LINK"),
                    "strategy_label": s.get("strategy_label", "Alternative Payment Link"),
                    "description": s.get("description", "Send secure recovery payment link."),
                    "recovery_probability": round(prob, 2),
                    "operational_cost": round(cost, 2),
                    "discount_amount": round(disc, 2),
                    "expected_net_recovery": expected_net,
                    "ai_explanation": s.get("ai_explanation", "AI tailored recovery path"),
                    "risk_notes": "Requires Guardian verification" if amount > 100000 else "",
                    "ai_provider": "gemini",
                })
            formatted.sort(key=lambda x: x["expected_net_recovery"], reverse=True)
            for idx, item in enumerate(formatted):
                item["rank"] = idx + 1
            return formatted if formatted else self._fallback.generate_strategies(context)
        except Exception as e:
            logger.warning(f"Gemini strategy generation failed: {e}. Utilizing deterministic fallback.")
            return self._fallback.generate_strategies(context)

    def generate_communication(self, context: dict, language: str = "EN") -> str:
        try:
            system = f"Generate an empathetic, concise 1-2 sentence recovery notification message in {language} for an Indian customer."
            raw = self._call_gemini(f"Context: {context}", system)
            parsed = _clean_json_response(raw) if "{" in raw else {"message": raw}
            return parsed.get("message", raw)
        except Exception:
            return self._fallback.generate_communication(context, language)

    def summarize_case(self, context: dict) -> str:
        return self._fallback.summarize_case(context)


class OpenAICompatibleProvider(AIProvider):
    """
    Real AI provider using OpenAI-compatible API (GPT-4o, Ollama, etc.).
    Falls back to MockAIProvider on failure.
    """

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", model: str = "gpt-4o-mini", timeout: int = 8):
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._fallback = MockAIProvider()

    def is_available(self) -> bool:
        return bool(self.api_key)

    def _call_api(self, system_prompt: str, user_prompt: str) -> str:
        import httpx
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        # Primary model followed by resilient active model fallbacks
        candidate_models = [self.model, "openai/gpt-oss-20b", "groq/compound-mini", "qwen/qwen3.6-27b"]
        last_error = None

        for model_name in candidate_models:
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 512,
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            }
            try:
                response = httpx.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"]
                elif response.status_code == 404:
                    # Model not available on this tier, try next candidate
                    continue
                else:
                    response.raise_for_status()
            except Exception as e:
                last_error = e
                continue

        if last_error:
            raise last_error
        raise RuntimeError("No candidate LLM models succeeded")

    def analyze_root_cause(self, context: dict) -> dict:
        try:
            system = (
                "You are a fintech revenue recovery expert. Analyze the payment failure context "
                "and return a JSON with keys: root_cause, root_cause_category, root_cause_detail, confidence (0-1)."
            )
            user = f"Context: {context}"
            raw = self._call_api(system, user)
            parsed = _clean_json_response(raw)
            return {
                "root_cause": parsed.get("root_cause", "Technical Gateway Timeout"),
                "root_cause_category": parsed.get("root_cause_category", "TECHNICAL"),
                "root_cause_detail": parsed.get("root_cause_detail", "Analysis of payment gateway timeout."),
                "confidence": float(parsed.get("confidence", 0.85)),
                "ai_provider": "openai",
                "ai_model": self.model,
                "fallback_used": None,
            }
        except Exception as e:
            logger.warning(f"OpenAI provider failed, using fallback: {e}")
            result = self._fallback.analyze_root_cause(context)
            result["fallback_used"] = "deterministic"
            return result

    def generate_strategies(self, context: dict) -> list[dict]:
        try:
            system = (
                "You are a fintech strategy engine. Generate a JSON with key 'strategies' containing 3-4 candidate options. "
                "Each object: strategy_name, strategy_label, description, recovery_probability, operational_cost, discount_amount, ai_explanation."
            )
            user = f"Context: {context}"
            raw = self._call_api(system, user)
            parsed = _clean_json_response(raw)
            strategies = parsed.get("strategies", [])
            amount = float(context.get("amount", 0) or 0)
            formatted = []
            for s in strategies:
                prob = float(s.get("recovery_probability", 0.6))
                cost = float(s.get("operational_cost", 0))
                disc = min(float(s.get("discount_amount", 0)), amount * 0.10)
                expected_net = max(0.0, round((prob * amount) - cost - disc, 2))
                formatted.append({
                    "strategy_name": s.get("strategy_name", "SEND_PAYMENT_LINK"),
                    "strategy_label": s.get("strategy_label", "Payment Link"),
                    "description": s.get("description", "Send secure payment link"),
                    "recovery_probability": round(prob, 2),
                    "operational_cost": round(cost, 2),
                    "discount_amount": round(disc, 2),
                    "expected_net_recovery": expected_net,
                    "ai_explanation": s.get("ai_explanation", "AI recovery path"),
                    "risk_notes": "Requires Guardian approval" if amount > 100000 else "",
                    "ai_provider": "openai",
                })
            formatted.sort(key=lambda x: x["expected_net_recovery"], reverse=True)
            for idx, item in enumerate(formatted):
                item["rank"] = idx + 1
            return formatted if formatted else self._fallback.generate_strategies(context)
        except Exception as e:
            logger.warning(f"OpenAI strategy failed, using fallback: {e}")
            return self._fallback.generate_strategies(context)

    def generate_communication(self, context: dict, language: str = "EN") -> str:
        try:
            system = f"Generate an empathetic recovery message in {language} for the pending payment."
            raw = self._call_api(system, f"Context: {context}")
            parsed = _clean_json_response(raw) if "{" in raw else {"message": raw}
            return parsed.get("message", raw)
        except Exception:
            return self._fallback.generate_communication(context, language)

    def summarize_case(self, context: dict) -> str:
        return self._fallback.summarize_case(context)


def get_ai_provider(settings=None) -> AIProvider:
    """Factory function — returns appropriate AI provider based on configuration."""
    if settings is None:
        from app.core.config import get_settings
        settings = get_settings()

    # Check Groq API key first (ultra fast live inference)
    groq_key = getattr(settings, "GROQ_API_KEY", None)
    if groq_key and groq_key.startswith("gsk_") and "your_" not in groq_key and "here" not in groq_key:
        logger.info("Using Groq live LLM provider")
        return OpenAICompatibleProvider(
            api_key=groq_key,
            base_url="https://api.groq.com/openai/v1",
            model=getattr(settings, "AI_MODEL", "llama-3.1-8b-instant") or "llama-3.1-8b-instant",
            timeout=getattr(settings, "AI_TIMEOUT_SECONDS", 8),
        )

    # Check standard Gemini API key (starts with AIza)
    gemini_key = getattr(settings, "GEMINI_API_KEY", None)
    if gemini_key and gemini_key.startswith("AIza"):
        logger.info("Using Gemini AI provider")
        return GeminiLiveProvider(api_key=gemini_key)

    # Check standard OpenAI API key
    openai_key = getattr(settings, "OPENAI_API_KEY", None)
    if openai_key and openai_key not in ("", "your-openai-api-key-here", "your_openai_api_key_here", "mock") and "your_" not in openai_key and "here" not in openai_key:
        logger.info("Using OpenAI-compatible AI provider")
        return OpenAICompatibleProvider(
            api_key=openai_key,
            base_url=getattr(settings, "OPENAI_BASE_URL", "https://api.openai.com/v1"),
            model=getattr(settings, "AI_MODEL", "openai/gpt-oss-20b"),
            timeout=getattr(settings, "AI_TIMEOUT_SECONDS", 8),
        )

    logger.info("Using deterministic Mock AI provider (no live LLM key configured)")
    return MockAIProvider()
