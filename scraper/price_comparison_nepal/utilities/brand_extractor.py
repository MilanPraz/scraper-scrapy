import re
from urllib.parse import unquote, urlparse , parse_qs


def extract_brand_name(model_name:str|None)->str|None:

    if not model_name:
        return None
    
    known_brands = [
        "Samsung",
        "Xiaomi",
        "Redmi",
        "Poco",
        "Apple",
        "iPhone",
        "Honor",
        "Realme",
        "OnePlus",
        "Oppo",
        "Vivo",
        "Motorola",
        "Infinix",
        "Tecno",
        "Nothing",
    ]

    model_name_lower=model_name.lower()

    for brand in known_brands:
        if brand.lower() in model_name_lower:
            # ecepptional brands
            if brand == "iPhone":
                return "Apple"
            if brand == "Poco":
                return "Xiaomi"
            if brand == "Redmi":
                return "Xiaomi"
            return brand
        
    # fallback to first word of model name
    return model_name.split()[0]



def clean_price(currency:str |None, price_number:str |None)->str|None:

    if not currency or not price_number:
        return None
    
    currency= currency or "Rs"
    return f"{currency} {(price_number)}".strip()

def clean_next_image(image_url:str|None, response)->str|None:
    if not image_url:
        return None

    # Image: /_next/image?url=https%3A%2F%2Fcdn.hukut.com%2Fxiaomi-redmi-a7-sky-blue.webp1778437965432&w=3840&q=7

    # 1st absolute url
    absolute_url=response.urljoin(image_url)
    parsed=urlparse(absolute_url)

    if parsed.path.startswith("/_next/image"):
        query= parse_qs(parsed.query)
        original_url=query.get("url",[None])[0]

        if original_url:
            original_url=unquote(original_url)

            if original_url.startswith("/"):
                original_url=response.urljoin(original_url)

            # hukut may appendtimestamp after .jpg
            # match = re.search(r"^(.+?\.(webp|jpg|jpeg|png))",original_url,re.IGNORECASE)

            # if match:
                # return match.group(1)
            
            return original_url
    return absolute_url
