import scrapy
from scrapy_playwright.page import PageMethod
from datetime import datetime, timezone
from price_comparison_nepal.items import ProductOfferItem
from price_comparison_nepal.sources import MOBILEMANDU_SOURCES
from price_comparison_nepal.utilities.brand_extractor import extract_brand_name
from price_comparison_nepal.utilities.yantra_utils import clean_text

class MobilemanduSpider(scrapy.Spider):
    name="mobilemandu"

    allowed_domains=[
        'mobilemandu.com',
        'www.mobilemandu.com'
    ]


    def __init__(self,category:str="mobiles",brand:str="all",*args,**kwargs):
        super().__init__(*args,**kwargs)

        self.category=category.lower().strip()
        self.brand= brand.lower().strip()

        source = MOBILEMANDU_SOURCES.get(self.category)
        
        if source is None:
            available_sources = " ,".join(MOBILEMANDU_SOURCES.keys())

            raise ValueError(f"Invalid category '{self.category}'. Available categories: {available_sources}")
        self.source= source

    
    async def start(self):
        self.logger.info("Starting Mobilemandu spider with URL: %s", self.source["url"])

        yield scrapy.Request(
            url=self.source["url"],
            callback=self.parse,
            meta={
                "playwright":True,
                "playwright_page_methods":[
                    PageMethod("wait_for_load_state","networkidle"),
                    PageMethod("wait_for_timeout",2000)
                ]
            },
            dont_filter=True
        )

    def parse(self, response):
        for item in self.parse_products(response):
            yield item

        next_page = response.css("a[rel='next']::attr(href)").get()

        if next_page:
            next_url = response.urljoin(next_page)

            self.logger.info("Going to next Mobilemandu page: %s", next_url)

            yield scrapy.Request(
                url=next_url,
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_load_state", "networkidle"),
                        PageMethod("wait_for_timeout", 2000),
                    ],
                },
            )


    def parse_products(self,response):
        category_name=self.source.get("category")

        products_cards=response.css("div.relative.bg-white.shadow-lg")

        self.logger.info(f"Found {len(products_cards)} products in category '{category_name}'.")

        if not products_cards:
            self.logger.warning(f"No products found for category '{category_name}' at URL: {response.url}")

            with open("mobilemandu_no_products_found.log","a") as f:
                f.write(f"No products found for category '{category_name}' at URL: {response.url}\n")
            return
        

        for product in products_cards:
            model_name = clean_text(
                product.css("h3::text").get()
            )

            product_url = product.css("a.block::attr(href)").get()
            product_url = response.urljoin(product_url) if product_url else None

            image_url = product.css("img::attr(src)").get()
            image_url = response.urljoin(image_url) if image_url else None

            price_text = self.extract_price_text(product)
            price = self.clean_price_number(price_text)

            original_price_text = self.extract_original_price_text(product)
            original_price = self.clean_price_number(original_price_text)

            stock_text = clean_text(
                product.css("span::text").re_first(
                    r"(In Stock|Out of Stock)"
                )
            )

            in_stock = stock_text == "In Stock"

            brand_name = extract_brand_name(model_name)

            ram, storage = self.extract_ram_storage(model_name)

            if not model_name or not product_url:
                continue

            if self.brand != "all" and brand_name:
                if brand_name.lower() != self.brand:
                    continue

        
            yield ProductOfferItem(
                store="Mobilemandu",
                category=category_name,
                brand=brand_name,
                model_name=model_name,

                variant=None,
                ram=ram,
                storage=storage,

                price=price,
                discounted_price=original_price,
                price_text=price_text,
                price_type="exact",
                currency="NPR",

                product_url=product_url,
                source_url=response.url,
                image_url=image_url,

                in_stock=in_stock,
                scraped_at=datetime.now(timezone.utc).isoformat(),
            )

        
        
    def extract_price_text(self, product) -> str | None:
        prices = product.css(
            "span.text-webblack.font-medium::text"
        ).getall()

        if not prices:
            return None

        return clean_text(prices[0])
    
    def clean_price_number(self, value: str | None) -> float | None:
        if not value:
            return None

        cleaned = (
            value.replace("रु.", "")
            .replace("रु", "")
            .replace("Rs.", "")
            .replace("Rs", "")
            .replace(",", "")
            .strip()
        )

        try:
            return float(cleaned)
        except ValueError:
            return None

    def extract_original_price_text(self, product) -> str | None:
        original_price = product.css(
            "span.line-through::text"
        ).get()

        return clean_text(original_price)
    

    def extract_ram_storage(
        self,
        model_name: str | None,
    ) -> tuple[str | None, str | None]:
        if not model_name:
            return None, None

        import re

        patterns = [
            r"\((\d+)\s*/\s*(\d+)\s*GB\)",
            r"\((\d+)\s*\+\s*(\d+)\s*GB\)",
            r"\((\d+)GB\s*\+\s*(\d+)GB\)",
            r"(\d+)GB\s*\+\s*(\d+)GB",
            r"(\d+)\s*/\s*(\d+)GB",
        ]

        for pattern in patterns:
            match = re.search(pattern, model_name, re.IGNORECASE)

            if match:
                ram = f"{match.group(1)}GB"
                storage = f"{match.group(2)}GB"

                return ram, storage

        return None, None
        
        
        

            

