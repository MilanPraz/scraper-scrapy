from datetime import datetime, timezone
from typing import Any

import scrapy

from price_comparison_nepal.items import (
    ProductOfferItem,
)
from price_comparison_nepal.sources import (
    GADGETBYTE_SOURCES,
)
from price_comparison_nepal.utils import (
    clean_text,
    parse_product_offer,
)


class GadgetbyteSpider(scrapy.Spider):
    name = "gadgetbyte"

    allowed_domains = [
        "gadgetbytenepal.com",
        "www.gadgetbytenepal.com",
    ]

    def __init__(
        self,
        category: str = "mobiles",
        brand: str = "all",
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.category_key = (
            category.lower().strip()
        )

        self.brand_key = (
            brand.lower().strip()
        )

        category_sources = (
            GADGETBYTE_SOURCES.get(
                self.category_key
            )
        )

        if category_sources is None:
            available_categories = ", ".join(
                GADGETBYTE_SOURCES.keys()
            )

            raise ValueError(
                f"Unsupported category: "
                f"{category}. "
                f"Available categories: "
                f"{available_categories}"
            )

        if not category_sources:
            raise ValueError(
                f"No sources have been configured "
                f"for category: {category}"
            )

        if (
            self.brand_key != "all"
            and self.brand_key
            not in category_sources
        ):
            available_brands = ", ".join(
                category_sources.keys()
            )

            raise ValueError(
                f"Unsupported brand '{brand}' "
                f"for category '{category}'. "
                f"Available brands: "
                f"{available_brands}"
            )

        self.category_sources = (
            category_sources
        )

    async def start(self):
        """
        Generate requests for one brand or all brands.
        """

        if self.brand_key == "all":
            selected_sources = (
                self.category_sources.items()
            )
        else:
            selected_sources = [
                (
                    self.brand_key,
                    self.category_sources[
                        self.brand_key
                    ],
                )
            ]

        for brand_key, source in selected_sources:
            self.logger.info(
                "Crawling brand=%s "
                "category=%s url=%s",
                source["brand"],
                source["category"],
                source["url"],
            )

            yield scrapy.Request(
                url=source["url"],
                callback=self.parse,
                cb_kwargs={
                    "source": source,
                },
            )

    def parse(
        self,
        response: scrapy.http.Response,
        source: dict[str, Any],
    ):
        brand_name = source["brand"]
        category_name = source["category"]
        parser_name = source["parser"]

        self.logger.info(
            "Parsing %s %s page: %s",
            brand_name,
            category_name,
            response.url,
        )

        # Reset rowspan state for each table.
        for table in response.css("table"):
            current_model_name: str | None = None
            current_product_url: str | None = None

            for row in table.css("tr"):
                cells = row.css("td")

                if not cells:
                    continue

                raw_model: str | None = None
                linked_model_name: str | None = None

                candidate_product_url = (
                    current_product_url
                    or response.url
                )

                # Normal row:
                # model cell + price cell
                if len(cells) >= 2:
                    model_cell = cells[0]

                    # Use the last cell as price.
                    price_cell = cells[-1]

                    raw_model = clean_text(
                        model_cell.xpath(
                            "normalize-space("
                            "string(.))"
                        ).get()
                    )

                    linked_model_name = clean_text(
                        model_cell.xpath(
                            "normalize-space("
                            "string(.//a[1]))"
                        ).get()
                    )

                    product_path = (
                        model_cell.xpath(
                            ".//a[1]/@href"
                        ).get()
                    )

                    candidate_product_url = (
                        response.urljoin(
                            product_path
                        )
                        if product_path
                        else response.url
                    )

                    raw_price = clean_text(
                        price_cell.xpath(
                            "normalize-space("
                            "string(.))"
                        ).get()
                    )

                # Rowspan continuation:
                # this row contains only another price.
                elif len(cells) == 1:
                    if not current_model_name:
                        continue

                    linked_model_name = (
                        current_model_name
                    )

                    raw_model = current_model_name

                    raw_price = clean_text(
                        cells[0].xpath(
                            "normalize-space("
                            "string(.))"
                        ).get()
                    )

                else:
                    continue

                parsed_offer = (
                    parse_product_offer(
                        parser_name=parser_name,
                        raw_model=raw_model,
                        raw_price=raw_price,
                        linked_model_name=(
                            linked_model_name
                        ),
                    )
                )

                # Ignore advertisements, accessories,
                # offer prices and invalid formats.
                if parsed_offer is None:
                    self.logger.debug(
                        "Skipping invalid row: "
                        "%s | %s",
                        raw_model
                        or current_model_name,
                        raw_price,
                    )

                    continue

                current_model_name = (
                    parsed_offer["model_name"]
                )

                current_product_url = (
                    candidate_product_url
                )

                yield ProductOfferItem(
                    store="GadgetByte Nepal",
                    category=category_name,
                    brand=brand_name,
                    model_name=parsed_offer[
                        "model_name"
                    ],
                    variant=parsed_offer[
                        "variant"
                    ],
                    ram=parsed_offer["ram"],
                    storage=parsed_offer[
                        "storage"
                    ],
                    price=parsed_offer["price"],
                    price_type="exact",
                    price_text=parsed_offer[
                        "price_text"
                    ],
                    currency="NPR",
                    product_url=(
                        current_product_url
                        or response.url
                    ),
                    source_url=response.url,

                    # The article page does not
                    # guarantee stock availability.
                    in_stock=None,

                    scraped_at=datetime.now(
                        timezone.utc
                    ).isoformat(),
                )