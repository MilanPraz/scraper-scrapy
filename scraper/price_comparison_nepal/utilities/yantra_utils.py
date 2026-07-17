
from anyio.itertools import product


def extract_price_text(product)->str | None:
    price_text=product.css("p.price").xpath("string(.)").get()

    if not price_text:
        return None
    return (
            price_text.replace("\xa0", " ")
            .replace("Rs.", "Rs")
            .replace("Original price was:", "")
            .replace("Current price is:", "")
            .strip()
        )

def parse_yantra_price(product)->dict:

    regular_price_text = product.css(
            "p.price del .woocommerce-Price-amount bdi"
        ).xpath("string(.)").get()

    sale_price_text = product.css(
            "p.price ins .woocommerce-Price-amount bdi"
        ).xpath("string(.)").get()

    normal_price_text = product.css(
            "p.price > .woocommerce-Price-amount bdi"
        ).xpath("string(.)").get()


    regular_price= clean_price_number(regular_price_text)
    sale_price = clean_price_number(sale_price_text)
    normal_price = clean_price_number(normal_price_text)

    if sale_price is not None:
        return {
            "current_price": sale_price,
            "original_price": regular_price,
        }
    return {
        "current_price": normal_price,
        "original_price": None,
    }


def clean_price_number( value: str | None) -> float | None:
        if not value:
            return None

        cleaned = (
            value.replace("Rs.", "")
            .replace("Rs", "")
            .replace(",", "")
            .replace("\xa0", "")
            .strip()
        )

        try:
            return float(cleaned)
        except ValueError:
            return None
        

def clean_text(value: str | None) -> str:
    """
    Remove extra spaces and line breaks.

    Example:
        "  Galaxy   S26  " -> "Galaxy S26"
    """

    if not value:
        return ""

    return " ".join(value.split()).strip()


def extract_attribute( product, label: str) -> str | None:
        value = product.xpath(
            f"""
            .//tr[
                contains(
                    translate(
                        normalize-space(.//th),
                        'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                        'abcdefghijklmnopqrstuvwxyz'
                    ),
                    '{label.lower()}'
                )
            ]//td//text()
            """
        ).get()

        return clean_text(value)