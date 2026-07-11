import re
from decimal import Decimal, InvalidOperation
from typing import TypedDict

from price_comparison_nepal.utils import clean_text


class ParsedYantraPrice(TypedDict):
    price: int
    price_text: str


class ParsedYantraVariant(TypedDict):
    variant: str
    ram: str | None
    storage: str


class PaginationSummary(TypedDict):
    start: int
    end: int
    total: int


PRICE_PATTERN = re.compile(
    r"(?:NPR|NRs\.?|Rs\.?|रु\.?)\s*"
    r"(?P<price>[\d,]+(?:\.\d{1,2})?)",
    re.IGNORECASE,
)


CAPACITY_PATTERN = re.compile(
    r"(?P<value>\d+)\s*(?P<unit>GB|TB)",
    re.IGNORECASE,
)


RAM_STORAGE_IN_TITLE_PATTERN = re.compile(
    r"(?P<ram>\d+)\s*GB?"
    r"\s*(?:\||/|\+|,)\s*"
    r"(?P<storage>\d+)\s*"
    r"(?P<storage_unit>GB|TB)",
    re.IGNORECASE,
)


STORAGE_ONLY_PATTERN = re.compile(
    r"^(?P<storage>\d+)\s*"
    r"(?P<storage_unit>GB|TB)$",
    re.IGNORECASE,
)


TRAILING_PARENTHESES_PATTERN = re.compile(
    r"\s*\((?P<content>[^()]*)\)\s*$"
)


PAGINATION_SUMMARY_PATTERN = re.compile(
    r"Showing\s*"
    r"(?P<start>\d+)"
    r"\s*[-–]\s*"
    r"(?P<end>\d+)"
    r"\s*of\s*"
    r"(?P<total>\d+)"
    r"\s*products?",
    re.IGNORECASE,
)


BRAND_ALIASES: list[tuple[str, str]] = [
    ("apple iphone", "Apple"),
    ("iphone", "Apple"),
    ("apple", "Apple"),
    ("samsung", "Samsung"),
    ("xiaomi", "Xiaomi"),
    ("redmi", "Xiaomi"),
    ("mi ", "Xiaomi"),
    ("poco", "Poco"),
    ("oneplus", "OnePlus"),
    ("nothing", "Nothing"),
    ("google pixel", "Google"),
    ("google", "Google"),
    ("motorola", "Motorola"),
    ("realme", "Realme"),
    ("oppo", "Oppo"),
    ("vivo", "Vivo"),
    ("honor", "Honor"),
    ("infinix", "Infinix"),
    ("tecno", "Tecno"),
    ("blackview", "Blackview"),
    ("huawei", "Huawei"),
    ("nokia", "Nokia"),
    ("itel", "Itel"),
    ("htc", "HTC"),
    ("colors", "Colors"),
    ("zte", "ZTE"),
    ("nubia", "Nubia"),
]


def parse_yantra_price(
    raw_price: str | None,
) -> ParsedYantraPrice | None:
    price_text = clean_text(raw_price)

    if not price_text:
        return None

    match = PRICE_PATTERN.search(price_text)

    if match is None:
        return None

    normalized_price = (
        match.group("price").replace(",", "")
    )

    try:
        decimal_price = Decimal(normalized_price)
    except InvalidOperation:
        return None

    if decimal_price <= 0:
        return None

    if decimal_price != decimal_price.to_integral_value():
        return None

    return {
        "price": int(decimal_price),

        # Only store the matched price,
        # not the full product-card text.
        "price_text": clean_text(match.group(0)),
    }


def normalize_capacity(
    value: str | None,
) -> str | None:
    """
    Examples:

    2GB    -> 2GB
    32 GB  -> 32GB
    1 TB   -> 1TB
    """

    text = clean_text(value)

    if not text:
        return None

    match = CAPACITY_PATTERN.search(text)

    if match is None:
        return None

    number = match.group("value")
    unit = match.group("unit").upper()

    return f"{number}{unit}"


def parse_variant_from_values(
    ram_text: str | None,
    storage_text: str | None,
) -> ParsedYantraVariant | None:
    ram = normalize_capacity(ram_text)
    storage = normalize_capacity(storage_text)

    if storage is None:
        return None

    if ram:
        variant = f"{ram}/{storage}"
    else:
        variant = storage

    return {
        "variant": variant,
        "ram": ram,
        "storage": storage,
    }


def parse_variant_from_title(
    title: str | None,
) -> ParsedYantraVariant | None:
    """
    Examples:

    Xiaomi Redmi A1 (2GB | 32GB)
    Xiaomi Redmi Note 11 Pro
    (Graphite Gray, 8GB | 128GB)
    iPhone 15 (256GB)
    """

    title_text = clean_text(title)

    if not title_text:
        return None

    ram_storage_match = (
        RAM_STORAGE_IN_TITLE_PATTERN.search(title_text)
    )

    if ram_storage_match:
        ram = f"{ram_storage_match.group('ram')}GB"

        storage_value = (
            ram_storage_match.group("storage")
        )

        storage_unit = (
            ram_storage_match
            .group("storage_unit")
            .upper()
        )

        storage = (
            f"{storage_value}{storage_unit}"
        )

        return {
            "variant": f"{ram}/{storage}",
            "ram": ram,
            "storage": storage,
        }

    trailing_match = (
        TRAILING_PARENTHESES_PATTERN.search(
            title_text
        )
    )

    if trailing_match is None:
        return None

    possible_storage = clean_text(
        trailing_match.group("content")
    )

    storage_match = STORAGE_ONLY_PATTERN.fullmatch(
        possible_storage
    )

    if storage_match is None:
        return None

    storage = (
        f"{storage_match.group('storage')}"
        f"{storage_match.group('storage_unit').upper()}"
    )

    return {
        "variant": storage,
        "ram": None,
        "storage": storage,
    }


def remove_variant_from_title(
    title: str | None,
) -> str:
    """
    Examples:

    Xiaomi Redmi A1 (2GB | 32GB)
    -> Xiaomi Redmi A1

    Xiaomi Redmi Note 10 Pro
    (Glacier Blue, 8GB | 128GB)
    -> Xiaomi Redmi Note 10 Pro
    """

    title_text = clean_text(title)

    if not title_text:
        return ""

    trailing_match = (
        TRAILING_PARENTHESES_PATTERN.search(
            title_text
        )
    )

    if trailing_match is None:
        return title_text

    parenthesis_content = clean_text(
        trailing_match.group("content")
    )

    contains_variant = (
        RAM_STORAGE_IN_TITLE_PATTERN.search(
            parenthesis_content
        )
        is not None
        or STORAGE_ONLY_PATTERN.fullmatch(
            parenthesis_content
        )
        is not None
    )

    if not contains_variant:
        return title_text

    return clean_text(
        title_text[: trailing_match.start()]
    )


def detect_yantra_brand(
    model_name: str | None,
) -> str:
    model_text = clean_text(model_name)
    normalized_model = model_text.lower()

    if not model_text:
        return ""

    for alias, brand in BRAND_ALIASES:
        if normalized_model.startswith(alias):
            return brand

    # Fallback to the first word.
    return model_text.split()[0]


def normalize_brand_key(value: str | None) -> str:
    """
    OnePlus  -> oneplus
    AI Plus  -> aiplus
    ai-plus  -> aiplus
    """

    text = clean_text(value).lower()

    return re.sub(r"[^a-z0-9]+", "", text)


def extract_labeled_spec(
    product,
    label: str,
) -> str | None:
    """
    Extract a specification from a product card.

    Example HTML text:

    Ram: 8GB
    Storage: 128GB
    """

    label_key = label.lower().strip()

    spec_lines = product.css(
        "li"
    ).xpath(
        "normalize-space(string(.))"
    ).getall()

    for raw_line in spec_lines:
        line = clean_text(raw_line)

        if not line:
            continue

        normalized_line = line.lower()

        if not normalized_line.startswith(
            label_key
        ):
            continue

        if ":" in line:
            value = line.split(":", 1)[1]
            return clean_text(value)

        # Fallback when the colon is missing.
        return clean_text(
            line[len(label):]
        )

    return None


def parse_pagination_summary(
    page_text: str | None,
) -> PaginationSummary | None:
    text = clean_text(page_text)

    if not text:
        return None

    match = PAGINATION_SUMMARY_PATTERN.search(
        text
    )

    if match is None:
        return None

    return {
        "start": int(match.group("start")),
        "end": int(match.group("end")),
        "total": int(match.group("total")),
    }