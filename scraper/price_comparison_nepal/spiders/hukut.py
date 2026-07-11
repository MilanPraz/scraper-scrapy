from datetime import datetime, timezone

import scrapy
from scrapy_playwright.page import PageMethod

from price_comparison_nepal.items import ProductOfferItem
from price_comparison_nepal.sources import HUKUT_SOURCES
from price_comparison_nepal.hukut_utils import (
    detect_brand_from_model,
    parse_hukut_brand_heading,
    parse_starting_price,
)

from price_comparison_nepal.utils import clean_text


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
                "playwright_page_methods": [
                    PageMethod(
                        "wait_for_selector",
                        "table.blog-content",
                    ),
                    PageMethod(
                        "wait_for_timeout",
                        1500,
                    ),
                ],
            },
            dont_filter=True,
        )

    def parse(
        self,
        response: scrapy.http.Response,
    ):
        category_name = self.source["category"]

        tables = response.css("table.blog-content")

        self.logger.info(
            "Found %s Hukut tables on %s",
            len(tables),
            response.url,
        )

        if not tables:
            self.logger.error(
                "No rendered Hukut tables found. "
                "Saving response for inspection."
            )

            with open(
                "outputs/hukut/hukut_debug.html",
                "wb",
            ) as debug_file:
                debug_file.write(response.body)

            return

        for table in tables:
            heading_parts = table.xpath(
                """
                preceding::*[
                    self::h1
                    or self::h2
                    or self::h3
                    or self::h4
                ][1]//text()
                """
            ).getall()

            heading_text = clean_text(
                " ".join(heading_parts)
            )

            table_brand = parse_hukut_brand_heading(
                heading_text
            )

            self.logger.info(
                "Parsing table heading='%s', brand='%s'",
                heading_text,
                table_brand,
            )

            # Use all tr elements. Header rows will be skipped
            # because they do not contain two td elements.
            for row in table.css("tr"):
                cells = row.xpath("./td")

                if len(cells) < 2:
                    continue

                model_cell = cells[0]
                price_cell = cells[-1]

                model_name = clean_text(
                    model_cell.xpath(
                        "normalize-space(string(.//a[1]))"
                    ).get()
                )

                product_path = model_cell.xpath(
                    ".//a[1]/@href"
                ).get()

                raw_price = clean_text(
                    price_cell.xpath(
                        "normalize-space(string(.))"
                    ).get()
                )

                # A real product row must have a linked
                # model and a product URL.
                if not model_name or not product_path:
                    continue

                parsed_price = parse_starting_price(
                    raw_price
                )

                if parsed_price is None:
                    self.logger.debug(
                        "Skipping invalid Hukut row: "
                        "%s | %s",
                        model_name,
                        raw_price,
                    )
                    continue

                brand_name = table_brand

                if not brand_name:
                    brand_name = detect_brand_from_model(
                        model_name
                    )

                if not brand_name:
                    self.logger.debug(
                        "Unable to detect brand: %s",
                        model_name,
                    )
                    continue

                if (
                    self.brand_filter != "all"
                    and brand_name.lower()
                    != self.brand_filter
                ):
                    continue

                yield ProductOfferItem(
                    store="Hukut",
                    category=category_name,
                    brand=brand_name,
                    model_name=model_name,

                    # This table has only starting prices,
                    # not exact RAM/storage variant prices.
                    variant=None,
                    ram=None,
                    storage=None,

                    price=parsed_price["price"],
                    price_text=parsed_price[
                        "price_text"
                    ],
                    price_type="starting",
                    currency="NPR",

                    product_url=response.urljoin(
                        product_path
                    ),
                    source_url=response.url,

                    # The price-list page does not confirm
                    # current inventory.
                    in_stock=None,

                    scraped_at=datetime.now(
                        timezone.utc
                    ).isoformat(),
                )