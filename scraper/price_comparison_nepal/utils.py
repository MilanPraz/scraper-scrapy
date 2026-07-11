import re
from typing import TypedDict


class ParsedProductOffer(TypedDict):
    model_name: str
    variant: str
    ram: str | None
    storage: str
    price: int
    price_text: str


PRICE_PATTERN = re.compile(
    r"^(?:NPR|NRs\.?|Rs\.?|रु\.?)\s*"
    r"(?P<price>[\d,]+)"
    r"(?:\s*\((?P<variant>[^()]*)\))?"
    r"$",
    re.IGNORECASE,
)


RAM_STORAGE_PATTERN = re.compile(
    r"^(?P<ram>\d+)\s*(?:GB)?"
    r"\s*(?:/|\+|x|×)\s*"
    r"(?P<storage>\d+)\s*"
    r"(?P<storage_unit>GB|TB)?$",
    re.IGNORECASE,
)


STORAGE_ONLY_PATTERN = re.compile(
    r"^(?P<storage>\d+)\s*"
    r"(?P<storage_unit>GB|TB)$",
    re.IGNORECASE,
)


PARENTHESES_PATTERN = re.compile(
    r"\((?P<value>[^()]*)\)"
)


def clean_text(value: str | None) -> str:
    """
    Remove extra spaces and line breaks.

    Example:
        "  Galaxy   S26  " -> "Galaxy S26"
    """

    if not value:
        return ""

    return " ".join(value.split()).strip()


def normalize_mobile_variant(
    value: str | None,
) -> dict[str, str | None] | None:
    """
    Supported examples:

    8/256GB       -> 8GB/256GB
    8+256GB       -> 8GB/256GB
    8GB/256GB     -> 8GB/256GB
    8 GB + 256 GB -> 8GB/256GB
    256GB         -> 256GB
    1TB           -> 1TB
    """

    value = clean_text(value)

    if not value:
        return None

    ram_storage_match = RAM_STORAGE_PATTERN.fullmatch(
        value
    )

    if ram_storage_match:
        ram_value = ram_storage_match.group("ram")
        storage_value = ram_storage_match.group(
            "storage"
        )

        storage_unit = (
            ram_storage_match.group(
                "storage_unit"
            )
            or "GB"
        ).upper()

        ram = f"{ram_value}GB"
        storage = (
            f"{storage_value}{storage_unit}"
        )

        return {
            "variant": f"{ram}/{storage}",
            "ram": ram,
            "storage": storage,
        }

    storage_only_match = (
        STORAGE_ONLY_PATTERN.fullmatch(value)
    )

    if storage_only_match:
        storage_value = storage_only_match.group(
            "storage"
        )

        storage_unit = storage_only_match.group(
            "storage_unit"
        ).upper()

        storage = (
            f"{storage_value}{storage_unit}"
        )

        return {
            "variant": storage,
            "ram": None,
            "storage": storage,
        }

    return None


def extract_variant_from_text(
    value: str | None,
) -> dict[str, str | None] | None:
    """
    Extract a valid mobile variant from parentheses.

    Examples:

    Vivo Y05 (4/64GB)
    iPhone 16 (256GB)
    """

    value = clean_text(value)

    if not value:
        return None

    matches = PARENTHESES_PATTERN.findall(value)

    # Check from last parentheses to first.
    for matched_value in reversed(matches):
        parsed_variant = normalize_mobile_variant(
            matched_value
        )

        if parsed_variant:
            return parsed_variant

    return None


def remove_variant_from_model(
    value: str | None,
) -> str:
    """
    Remove a trailing variant only when it is a valid
    RAM/storage or storage-only variant.

    Examples:

    Vivo Y05 (4/64GB) -> Vivo Y05
    iPhone 16 (256GB) -> iPhone 16
    Phone (5G)        -> Phone (5G)
    """

    model_name = clean_text(value)

    if not model_name:
        return ""

    trailing_parentheses = re.search(
        r"\((?P<value>[^()]*)\)\s*$",
        model_name,
    )

    if trailing_parentheses is None:
        return model_name

    possible_variant = (
        trailing_parentheses.group("value")
    )

    if normalize_mobile_variant(
        possible_variant
    ) is None:
        return model_name

    return clean_text(
        model_name[
            : trailing_parentheses.start()
        ]
    )


def parse_mobile_offer(
    raw_model: str | None,
    raw_price: str | None,
    linked_model_name: str | None = None,
) -> ParsedProductOffer | None:
    """
    Supports both formats.

    Format 1:

        Galaxy A57
        NPR 79,999 (8+256GB)

    Format 2:

        Vivo Y05 (4/64GB)
        Rs. 21,999

    Format 3:

        iPhone 16
        NPR 149,999 (256GB)

    Invalid rows return None.
    """

    model_text = clean_text(raw_model)
    price_text = clean_text(raw_price)
    link_text = clean_text(linked_model_name)

    if not price_text:
        return None

    price_match = PRICE_PATTERN.fullmatch(
        price_text
    )

    if price_match is None:
        return None

    try:
        price = int(
            price_match.group(
                "price"
            ).replace(",", "")
        )
    except ValueError:
        return None

    # First try to get the variant from the price.
    parsed_variant = normalize_mobile_variant(
        price_match.group("variant")
    )

    # Otherwise get it from the model cell.
    if parsed_variant is None:
        parsed_variant = extract_variant_from_text(
            model_text
        )

    if parsed_variant is None:
        return None

    model_source = link_text or model_text

    model_name = remove_variant_from_model(
        model_source
    )

    if not model_name:
        return None

    variant = parsed_variant["variant"]
    ram = parsed_variant["ram"]
    storage = parsed_variant["storage"]

    if not isinstance(variant, str):
        return None

    if not isinstance(storage, str):
        return None

    return {
        "model_name": model_name,
        "variant": variant,
        "ram": ram,
        "storage": storage,
        "price": price,
        "price_text": price_text,
    }


def parse_product_offer(
    parser_name: str,
    raw_model: str | None,
    raw_price: str | None,
    linked_model_name: str | None = None,
) -> ParsedProductOffer | None:
    """
    Select parser based on the configured product category.
    """

    if parser_name == "mobile":
        return parse_mobile_offer(
            raw_model=raw_model,
            raw_price=raw_price,
            linked_model_name=linked_model_name,
        )

    # Monitor, TV and laptop parsers will be added later.
    return None