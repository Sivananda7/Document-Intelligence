DRIVER_LICENSE_SCHEMA = """
{
  "document": {
    "type": "string",
    "state": "string",
    "license_number": "string",
    "date_of_issue": "string",
    "date_of_expiry": "string",
    "document_discriminator": "string",
    "duplicates": "string",
    "real_id": "boolean"
  },
  "holder": {
    "last_name": "string",
    "first_name": "string",
    "date_of_birth": "string",
    "sex": "string",
    "address": "string",
    "city": "string",
    "state": "string",
    "zip": "string",
    "height": "string",
    "weight": "string",
    "eye_color": "string",
    "hair_color": "string",
    "organ_donor": "boolean",
    "veteran": "boolean",
    "safe_driver": "boolean"
  },
  "license": {
    "class": "string",
    "endorsements": "string",
    "restrictions": "string"
  }
}
"""

PASSPORT_SCHEMA = """
{
  "document": {
    "type": "string",
    "code": "string",
    "passport_number": "string",
    "issuing_authority": "string",
    "date_of_issue": "string",
    "date_of_expiry": "string",
    "endorsements": "string"
  },
  "holder": {
    "surname": "string",
    "given_names": "string",
    "nationality": "string",
    "date_of_birth": "string",
    "sex": "string",
    "place_of_birth": "string"
  },
  "mrz": {
    "line_1": "string",
    "line_2": "string"
  }
}
"""

STUDENT_ID_SCHEMA = """
{
  "institution": {
    "name": "string",
    "registration_number": "string",
    "address": "string",
    "city": "string",
    "state": "string",
    "zip": "string",
    "phone": "string"
  },
  "student": {
    "full_name": "string",
    "student_number": "string",
    "date_of_birth": "string",
    "gender": "string",
    "email": "string",
    "address": "string",
    "city": "string",
    "state": "string",
    "zip": "string",
    "country": "string",
    "phone_home": "string",
    "phone_cell": "string",
    "emergency_call": "string",
    "father_guardian": "string"
  },
  "academic": {
    "semester": "string",
    "grade": "string",
    "homeroom": "string",
    "teacher": "string"
  }
}
"""

TX_POA_SCHEMA = """
{
  "vehicle": {
    "vin": "string",
    "year": "string",
    "make": "string",
    "body_style": "string",
    "model": "string",
    "license_plate": "string",
    "title_document_number": "string"
  },
  "grantor": {
    "full_name": "string",
    "address": "string",
    "city": "string",
    "county": "string",
    "state": "string",
    "zip": "string"
  },
  "grantee": {
    "full_name": "string",
    "address": "string",
    "city": "string",
    "county": "string",
    "state": "string",
    "zip": "string"
  },
  "certification": {
    "printed_name": "string",
    "date": "string"
  }
}
"""

import json

DRIVER_LICENSE_TEMPLATE = json.loads(DRIVER_LICENSE_SCHEMA)
PASSPORT_TEMPLATE = json.loads(PASSPORT_SCHEMA)
STUDENT_ID_TEMPLATE = json.loads(STUDENT_ID_SCHEMA)
TX_POA_TEMPLATE = json.loads(TX_POA_SCHEMA)

TEMPLATE_MAP = {
    "driver_license": DRIVER_LICENSE_TEMPLATE,
    "passport": PASSPORT_TEMPLATE,
    "student_id": STUDENT_ID_TEMPLATE,
    "vehicle_power_of_attorney": TX_POA_TEMPLATE
}

def enforce_schema(extracted: dict, template: dict) -> dict:
    """Recursively ensures the extracted data contains all keys from the template.
    If a key is missing, it creates an empty string so the frontend displays it."""
    if not isinstance(extracted, dict):
        extracted = {}
        
    result = {}
    for k, v in template.items():
        if isinstance(v, dict):
            # Recurse for nested dictionaries
            result[k] = enforce_schema(extracted.get(k, {}), v)
        else:
            # Grab extracted value, fallback to empty string if missing
            val = extracted.get(k, "")
            # If the LLM returned literally 'None' mapped, make it empty string
            result[k] = val if val is not None else ""
    return result

