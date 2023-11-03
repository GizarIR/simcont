from django.core.exceptions import ValidationError
import json


def validate_json(value):
    if value is None or value == '{}':
        return
    try:
        json.loads(value)
    except (ValueError, TypeError):
        raise ValidationError("Invalid JSON format")
