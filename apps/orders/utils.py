import uuid
from django.utils import timezone


def generate_order_number():
    prefix = "ORD"
    date_part = timezone.now().strftime("%Y%m%d")
    unique_part = uuid.uuid4().hex[:6].upper()
    return f"{prefix}-{date_part}-{unique_part}"


def generate_invoice_number():
    prefix = "INV"
    date_part = timezone.now().strftime("%Y%m%d")
    unique_part = uuid.uuid4().hex[:6].upper()
    return f"{prefix}-{date_part}-{unique_part}"