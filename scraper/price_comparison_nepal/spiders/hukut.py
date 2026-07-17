from datetime import datetime, timezone

from anyio.itertools import product
import scrapy
from scrapy_playwright.page import PageMethod

from price_comparison_nepal.items import ProductOfferItem
from price_comparison_nepal.sources import HUKUT_SOURCES

from price_comparison_nepal.utils import clean_text
from price_comparison_nepal.utilities.brand_extractor import extract_brand_name , clean_price , clean_next_image
from price_comparison_nepal.utilities.hukut_utils import parse_starting_price , extract_hukut_price
class HukutSpider(scrapy.Spider):
    name = "hukut"

    allowed_domains = [
        "hukut.com",
        "www.hukut.com",
    ]

    def __init__(
        self,
        category: str = "mobiles",
        brand: str = "all",
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.category_key = category.lower().strip()
        self.brand_filter = brand.lower().strip()

        source = HUKUT_SOURCES.get(self.category_key)

        if source is None:
            available_categories = ", ".join(
                HUKUT_SOURCES.keys()
            )

            raise ValueError(
                f"Unsupported Hukut category: {category}. "
                f"Available categories: "
                f"{available_categories}"
            )

        self.source = source

    async def start(self):
        """
        Open the page using Playwright and wait until
        JavaScript has rendered the product tables.
        """

        yield scrapy.Request(
            url=self.source["url"],
            callback=self.parse,
            meta={
                # Handle this request using a real Playwright browser instead of only Scrapy’s HTTP downloader.
                "playwright": True,
                "playwright_include_page": True,
                "playwright_page_methods": [
                    PageMethod(
                        "wait_for_selector",
                        "div.grid.grid-cols-2.md\\:grid-cols-3",
                    ),
                    PageMethod(
                        "wait_for_timeout",
                        1500,
                    ),
                ],
            },
            dont_filter=True,
        )

    # def parse_product(self,response:scrapy.http.Response):

    #     category_name = self.source["category"]

    #     productGrid = response.css("div.grid.grid-cols-2.md\\:grid-cols-3")
    #     products_card=productGrid.css("a[href]")

    #     print(f"Found {len(products_card)} products on {response.url}")


    #     self.logger.info(
    #         "Found %s Hukut tables on %s",
    #         len(productGrid),
    #         response.url,
    #     )

    #     if not productGrid:
    #         self.logger.error(
    #             "No rendered Hukut tables found. "
    #             "Saving response for inspection."
    #         )

    #         with open(
    #             "outputs/hukut/hukut_debug.html",
    #             "wb",
    #         ) as debug_file:
    #             debug_file.write(response.body)

    #         return

    #     for product in products_card:
    #         product_url = product.css("::attr(href)").get()
    #         product_url=response.urljoin(product_url)
    #         model_name=(
    #             product.css("h3::attr(title)").get()
    #             or
    #             product.css("h3::text").get()
    #         )
    #         currency=clean_text(
    #             product.css("span::text").re_first(r"Rs\.?\s*")

    #         )
    #         price_number= product.css("span::text").re_first(r"[\d,]+")

    #         raw_price=None
    #         if currency and price_number:
    #             raw_price= clean_price(currency, price_number)
            
    #         raw_image_url = product.css("img::attr(src)").get()
    #         image_url = clean_next_image(raw_image_url, response)

    #         brand_name=extract_brand_name(model_name)
            

    #         print(f"Product: {model_name} | Brand: {brand_name} | Price: {raw_price} | URL: {product_url} | Image: {image_url}")

    def parse_products(
    self,
    response: scrapy.http.Response,
):
        
        category_name = self.source["category"]

        product_grid = response.css("div.grid.grid-cols-2")

        self.logger.info(
            "Found %s product grids on %s",
            len(product_grid),
            response.url,
        )

        if not product_grid:
            self.logger.error("No Hukut product grid found.")

            with open("outputs/hukut/hukut_debug.html", "wb") as debug_file:
                debug_file.write(response.body)

            return

        product_cards = product_grid.css("a[href]")

        self.logger.info(
            "Found %s Hukut product cards after Load More clicks.",
            len(product_cards),
        )

        for product in product_cards:
            product_path = product.css("::attr(href)").get()

            model_name = (
                product.css("h3::attr(title)").get()
                or product.css("h3::text").get()
                or product.css("img::attr(alt)").get()
            )

            raw_price = extract_hukut_price(product)

            raw_image_url = product.css("img::attr(src)").get()
            image_url = clean_next_image(raw_image_url, response)

            brand_name = extract_brand_name(model_name)

            product_url = response.urljoin(product_path) if product_path else None

            self.logger.info(
                "Product: %s | Brand: %s | Price: %s | URL: %s | Image: %s",
                model_name,
                brand_name,
                raw_price,
                product_url,
                image_url,
            )

            parsed_price = parse_starting_price(raw_price)

            if parsed_price is None:
                self.logger.debug(
                    "Skipping invalid Hukut product: "
                    "%s | %s",
                    model_name,
                    raw_price,
                )
                continue

            print(f"Product: {model_name} | Brand: {brand_name} | Price: {raw_price} | URL: {product_url} | Image: {image_url}")
            yield ProductOfferItem(

            store="Hukut",
            category=category_name,
            brand=brand_name,
            model_name=model_name.strip() if model_name else None,

            variant=None,
            ram=None,
            storage=None,

            price=parsed_price["price"],
            price_text=parsed_price["price_text"],
            price_type="starting",
            currency="NPR",

            product_url=product_url,
            source_url=response.url,
            image_url=image_url,

            in_stock=True,
            scraped_at=datetime.now(timezone.utc).isoformat(),
        )

    async def parse(
        self,
        response: scrapy.http.Response,
    ):
        page = response.meta['playwright_page']  
        max_clicks=6
        click_count=0

        while click_count<max_clicks:
            load_more_button= page.locator("button:has-text('Load More')") 

            if await load_more_button.count()==0:
                self.logger.info("No more 'Load More' button found. Stopping clicks.")
                break

            try:
                await load_more_button.first.scroll_into_view_if_needed()
                await page.wait_for_timeout(1000)  # Wait for 1 second before clicking

                previous_count=await page.locator("a[href]").count()

                await load_more_button.first.click()
                await page.wait_for_timeout(2000)  # Wait for 2 seconds after clicking

                current_count= await page.locator("a[href]").count()

                self.logger.info(
                    "Clicked Load More %s times. Products before: %s, after: %s",
                    click_count + 1,
                    previous_count,
                    current_count,
                )

                if current_count<=previous_count:
                    self.logger.info("No new products loaded after clicking. Stopping clicks.")
                    break

                click_count+=1

            except Exception as e:
                self.logger.info("Error clicking 'Load More' button: %s", e)
                break
        
        html_content= await page.content()
        await page.close()
        rendered_response= response.replace(body=html_content.encode('utf-8'))

        for item in self.parse_products(rendered_response):
            yield item

            # Use all tr elements. Header rows will be skipped
            # because they do not contain two td elements.
            # for row in table.css("tr"):
            #     cells = row.xpath("./td")

            #     if len(cells) < 2:
            #         continue

            #     model_cell = cells[0]
            #     price_cell = cells[-1]

            #     model_name = clean_text(
            #         model_cell.xpath(
            #             "normalize-space(string(.//a[1]))"
            #         ).get()
            #     )

            #     product_path = model_cell.xpath(
            #         ".//a[1]/@href"
            #     ).get()

            #     raw_price = clean_text(
            #         price_cell.xpath(
            #             "normalize-space(string(.))"
            #         ).get()
            #     )

            #     # A real product row must have a linked
            #     # model and a product URL.
            #     if not model_name or not product_path:
            #         continue

            #     parsed_price = parse_starting_price(
            #         raw_price
            #     )

            #     if parsed_price is None:
            #         self.logger.debug(
            #             "Skipping invalid Hukut row: "
            #             "%s | %s",
            #             model_name,
            #             raw_price,
            #         )
            #         continue

            #     brand_name = table_brand

            #     if not brand_name:
            #         brand_name = detect_brand_from_model(
            #             model_name
            #         )

            #     if not brand_name:
            #         self.logger.debug(
            #             "Unable to detect brand: %s",
            #             model_name,
            #         )
            #         continue

            #     if (
            #         self.brand_filter != "all"
            #         and brand_name.lower()
            #         != self.brand_filter
            #     ):
            #         continue

                # yield ProductOfferItem(
                #     store="Hukut",
                #     category=category_name,
                #     brand=brand_name,
                #     model_name=model_name,

                #     # This table has only starting prices,
                #     # not exact RAM/storage variant prices.
                #     variant=None,
                #     ram=None,
                #     storage=None,

                #     price=parsed_price["price"],
                #     price_text=parsed_price[
                #         "price_text"
                #     ],
                #     price_type="starting",
                #     currency="NPR",

                #     product_url=response.urljoin(
                #         product_path
                #     ),
                #     source_url=response.url,

                #     # The price-list page does not confirm
                #     # current inventory.
                #     in_stock=None,

                #     scraped_at=datetime.now(
                #         timezone.utc
                #     ).isoformat(),
                # )