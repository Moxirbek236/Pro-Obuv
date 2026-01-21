"""Minimal SMS helper shim for local development.
Provides `send_sms(phone, text, **kwargs)` used by app.py.
This implementation logs to stdout and returns True. Replace with
real provider integration (Twilio, Nexmo, etc.) in production.
"""
import os
import logging

logger = logging.getLogger('sms_helper')


def send_sms(phone, text, **kwargs):
    """Send SMS to `phone` with message `text`.
    Local shim: log and return True.
    """
    try:
        # Best-effort: print to console for local dev
        logger.info(f"[sms_helper] To={phone} Msg={text}")
        print(f"[sms_helper] To={phone} Msg={text}")
        return True
    except Exception as e:
        try:
            logger.exception('sms send failed')
        except Exception:
            pass
        return False
