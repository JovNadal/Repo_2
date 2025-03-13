import re
from django.core.exceptions import ValidationError

def validate_currency_code(value):
    """Validate ISO 4217 currency code"""
    if not re.match(r'^[A-Z]{3}$', value):
        raise ValidationError("Currency code must be 3 uppercase letters (ISO 4217)")

def validate_iso_date(value):
    """Validate ISO 8601 date format"""
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', value):
        raise ValidationError("Date must be in ISO 8601 format (YYYY-MM-DD)")

def validate_uen(value):
    """Validate UEN format"""
    if not re.match(r'^\d{9}[A-Z]$', value):
        raise ValidationError("UEN must be 8 digits followed by 1 uppercase letter")
