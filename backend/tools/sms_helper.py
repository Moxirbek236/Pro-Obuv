import os
import logging
import random

logger = logging.getLogger("sms_helper")


def send_sms(phone: str, message: str) -> bool:
    """Send SMS to phone.

    Behavior:
    - If TWILIO_* env vars present and twilio is installed, attempt to send via Twilio.
    - Otherwise, log the message and return True (dev fallback).
    """
    phone = (phone or "").strip()
    if not phone:
        logger.warning("No phone provided to send_sms")
        return False

    # Prefer Twilio if configured
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_number = os.environ.get("TWILIO_FROM_NUMBER")

    if account_sid and auth_token and from_number:
        try:
            # Import locally to keep dependency optional
            from twilio.rest import Client

            client = Client(account_sid, auth_token)
            client.messages.create(to=phone, from_=from_number, body=message)
            logger.info(f"Sent SMS to {phone} via Twilio")
            return True
        except Exception as e:
            logger.exception(f"Twilio send failed: {e}")

    # Fallback: log the message (useful in development)
    logger.info(f"[SMS-DEV] To: {phone} | Message: {message}")
    # Also print so it's visible in simple hosting environments
    try:
        print(f"[SMS-DEV] To: {phone} | Message: {message}")
    except Exception:
        pass
    return True
