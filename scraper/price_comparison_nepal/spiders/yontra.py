import scrapy
from scrapy_playwright.page import PageMethod
from price_comparison_nepal.sources import YANTRA_SOURCES
from price_comparison_nepal.items import ProductOfferItem
from price_comparison_nepal.utilities.brand_extractor import extract_brand_name
from price_comparison_nepal.utilities.yantra_utils import extract_attribute, extract_price_text, parse_yantra_price
from price_comparison_nepal.utils import clean_text
from datetime import datetime, timezone

class YontraSpider(scrapy.Spider):
    name="yontra"

    allowed_domains=[
        'yantranepal.com',
        'www.yantranepal.com'
    ]


    def __init__(self,category:str="mobiles",brand:str="all",*args,**kwargs):
        super().__init__(*args,**kwargs)

        self.category=category
        self.brand= brand

        source = YANTRA_SOURCES.get(self.category)

        if source is None:
            available_sources=', '.join(YANTRA_SOURCES.keys())

            raise ValueError(f"Invalid category '{self.category}'. Available categories: {available_sources}")

        self.source=source

    
    async def start(self):
        self.logger.info("Starting Yantra spider with URL: %s", self.source["url"])

        yield scrapy.Request(
            url=self.source["url"],
            callback=self.parse,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_load_state", "networkidle"),
                    PageMethod("wait_for_timeout", 2000),
                ],
            },
            dont_filter=True,
        )

    # async def start(self):
    #     yield scrapy.Request(
    #         url=self.source['url'],
    #         callback=self.parse,
    #         dont_filter=True,
    #     )


    def parse_products(self,response):
        category_name=self.source['category']

        products_cards=response.css('div[data-elementor-type="loop-item"].product')

        self.logger.info(f"Found {len(products_cards)} products in category '{category_name}'.")

        if not products_cards:
            self.logger.warning(f"No products found in category '{category_name}'.")

            with open("debug_response.html","wb") as f:
                f.write(response.body)
            return
        
        for product in products_cards:
            product_url=product.css('h2.product_title a::attr(href)').get()

            model_name=clean_text(product.css('h2.product_title a::text').get())

            image_url=product.css('div.elementor-widget-theme-post-featured-image  img::attr(src)').get()

            image_url=response.urljoin(image_url) if image_url else None

            raw_price= extract_price_text(product)
            parsed_prices=parse_yantra_price(product)

            ram = extract_attribute(product,"Ram")
            storage= extract_attribute(product,"Storage")

            brand_name=extract_brand_name(model_name)

            if not model_name or not product_url:
                continue
            
            in_stock = "instock" in " ".join(
                product.css("::attr(class)").getall()
            )

            self.logger.info(
                "Product: %s | Brand: %s | Price: %s | URL: %s | Image: %s",
                model_name,
                brand_name,
                raw_price,
                product_url,
                image_url,
            )
            print(
                "Product: %s | Brand: %s | Price: %s | URL: %s | Image: %s",
                model_name,
                brand_name,
                raw_price,
                product_url,
                image_url,
            )

            yield ProductOfferItem(
                store="Yantra",
                category=category_name,
                brand=brand_name,
                model_name=model_name,

                variant=None,
                ram=ram,
                storage=storage,

                price=parsed_prices["current_price"],
                price_text=raw_price,
                price_type="exact",
                currency="NPR",

                product_url=product_url,
                source_url=response.url,
                image_url=image_url,

                in_stock=in_stock,
                scraped_at=datetime.now(timezone.utc).isoformat(),
            )

            next_page = response.css('a.next.page-numbers::attr(href)').get()

            if next_page:
                yield response.follow(
                    next_page,
                    callback=self.parse
                )


    async def parse(self, response:scrapy.http.Response):

        page = response.meta["playwright_page"]

        current_page =1
        max_pages = 18

        try:
            while current_page<=max_pages:
                self.logger.info(f"Scraping page {current_page} of {max_pages} for category '{self.category}'.")

                html_content = await page.content()

                rendered_response = response.replace(body=html_content.encode("utf-8"))

                for item in self.parse_products(rendered_response):
                    yield item
                
                next_button = page.locator('a.facetwp-page.next')

                if await next_button.count()==0:
                    self.logger.info(f"No more pages found after page {current_page}. Stopping pagination.")
                    break
                next_button_class = await next_button.first.get_attribute('class')

                if next_button_class and "disabled" in next_button_class:
                    self.logger.info(f"Next button is disabled on page {current_page}. Stopping pagination.")
                    break


                old_html= html_content

                await next_button.first.scroll_into_view_if_needed()
                await page.wait_for_timeout(500)
                await next_button.first.click()

                await page.wait_for_timeout(2000)

                new_html= await page.content()
                if new_html==old_html:
                    self.logger.info(f"Page content did not change after clicking next on page {current_page}. Stopping pagination.")
                    break

                current_page+=1
        finally:
            await page.close()




       


