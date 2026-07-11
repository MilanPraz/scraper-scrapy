import re
from typing import TypedDict

from price_comparison_nepal.utils import clean_text


class ParsedStartingPrice(TypedDict):
    price: int
    price_text: str


STARTING_PRICE_PATTERN = re.compile(
    r"^(?:NPR|NRs\.?|Rs\.?|रु\.?)\s*"
    r"(?P<price>[\d,]+)"
    r"$",
    re.IGNORECASE,
)


HUKUT_BRAND_ALIASES = {
    "apple": "Apple",
    "apple iphone": "Apple",
    "iphone": "Apple",
    "iphones": "Apple",
    "samsung": "Samsung",
    "xiaomi": "Xiaomi",
    "redmi": "Xiaomi",
    "poco": "Poco",
    "vivo": "Vivo",
    "oppo": "Oppo",
    "realme": "Realme",
    "oneplus": "OnePlus",
    "nothing": "Nothing",
    "honor": "Honor",
    "motorola": "Motorola",
    "infinix": "Infinix",
    "tecno": "Tecno",
    "zte": "ZTE",
    "nubia": "Nubia",
    "hmd": "HMD",
    "ai plus": "AI Plus",
    "ai+": "AI Plus",
}


# def parse_starting_price(
#     raw_price: str | None,
# ) -> ParsedStartingPrice | None:
#     """
#     Valid examples:

#     Rs. 53,999
#     Rs 53,999
#     NPR 53,999
#     NRs. 53,999

#     Invalid price structures return None.
#     """

#     price_text = clean_text(raw_price)

#     if not price_text:
#         return None

#     match = STARTING_PRICE_PATTERN.fullmatch(
#         price_text
#     )

#     if match is None:
#         return None

#     try:
#         price = int(
#             match.group("price").replace(",", "")
#         )
#     except ValueError:
#         return None

#     if price <= 0:
#         return None

#     return {
#         "price": price,
#         "price_text": price_text,
#     }


def parse_starting_price(
    raw_price: str | None,
) -> ParsedStartingPrice | None:
    price_text = clean_text(raw_price)

    if not price_text:
        return None

    match = STARTING_PRICE_PATTERN.fullmatch(
        price_text
    )

    if match is None:
        return None

    try:
        price = int(
            match.group("price").replace(",", "")
        )
    except ValueError:
        return None

    if price <= 0:
        return None

    return {
        "price": price,
        "price_text": price_text,
    }

def parse_hukut_brand_heading(
    heading: str | None,
) -> str:
    """
    Examples:

    OnePlus Mobile Phones -> OnePlus
    Samsung Mobile Phones -> Samsung
    Apple iPhones         -> Apple
    """

    heading_text = clean_text(heading)

    if not heading_text:
        return ""

    cleaned_heading = re.sub(
        (
            r"\b(?:mobile\s+phones?|smartphones?|"
            r"phones?|mobiles?)\b.*$"
        ),
        "",
        heading_text,
        flags=re.IGNORECASE,
    )

    cleaned_heading = clean_text(
        cleaned_heading.strip(":-|")
    )

    normalized_heading = (
        cleaned_heading.lower().strip()
    )

    if normalized_heading in HUKUT_BRAND_ALIASES:
        return HUKUT_BRAND_ALIASES[
            normalized_heading
        ]

    # Handle headings such as "Apple iPhones".
    for alias, brand in HUKUT_BRAND_ALIASES.items():
        if normalized_heading.startswith(alias):
            return brand

    return cleaned_heading


def detect_brand_from_model(
    model_name: str | None,
) -> str:
    """
    Fallback when no nearby brand heading is found.
    """

    model_text = clean_text(model_name)
    normalized_model = model_text.lower()

    if not model_text:
        return ""

    # Longer aliases first so "AI Plus" is checked
    # before smaller words.
    sorted_aliases = sorted(
        HUKUT_BRAND_ALIASES.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    )

    for alias, brand in sorted_aliases:
        if normalized_model.startswith(alias):
            return brand

    # Final fallback: first word of model name.
    return model_text.split()[0]