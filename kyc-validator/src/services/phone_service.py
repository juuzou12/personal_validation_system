import phonenumbers
from phonenumbers import geocoder, carrier, NumberParseException

def validate_phone_number(phone_number: str, region: str = "KE") -> dict:
    """
    Validate and extract information about a phone number.
    Default region: Kenya (KE).
    """
    try:
        parsed = phonenumbers.parse(phone_number, region)
        is_valid = phonenumbers.is_valid_number(parsed)
        is_possible = phonenumbers.is_possible_number(parsed)

        result = {
            "input": phone_number,
            "international_format": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
            "national_format": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL),
            "country_code": parsed.country_code,
            "region_code": geocoder.region_code_for_number(parsed),
            "carrier": carrier.name_for_number(parsed, "en"),
            "is_valid": is_valid,
            "is_possible": is_possible,
        }

        return result
    except NumberParseException as e:
        return {"error": f"Invalid number format: {str(e)}"}
