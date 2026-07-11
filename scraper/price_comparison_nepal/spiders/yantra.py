from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import (
    parse_qs,
    urlencode,
    urlsplit,
    urlunsplit,
)
import scrapy
from price_comparison_nepal.items import ProductOfferItem
from price_comparison_nepal.sources import YANTRA_SOURCES
from price_comparison_nepal.utils import clean_text
from price_comparison_nepal.yantra_utils import (
    detect_yantra_brand,
    extract_labeled_spec,
    normalize_brand_key,
    parse_pagination_summary,
    parse_variant_from_title,
    parse_variant_from_values,
    parse_yantra_price,
    remove_variant_from_title,
)


class YantraSpider(scrapy.Spider):
    name = "yantra"

    allowed_domains = [
        "yantranepal.com",
        "www.yantranepal.com",
    ]

    # Allows us to inspect a 403 response instead of
    # Scrapy ignoring it before parse() is called.
    handle_httpstatus_list = [403]

    custom_settings = {
        # Global USER_AGENT is None because Hukut uses
        # Playwright. Yantra uses normal Scrapy, so it
        # needs its own browser-like user agent.
        "USER_AGENT": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/150.0.0.0 Safari/537.36"
        ),
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,"
                "image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Upgrade-Insecure-Requests": "1",
        },
    }

    def __init__(
        self,
        category: str = "mobiles",
        brand: str = "all",
        start_page: str = "1",
        max_pages: str = "100",
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.category_key = category.lower().strip()
        self.brand_filter = normalize_brand_key(brand)

        source = YANTRA_SOURCES.get(
            self.category_key
        )

        if source is None:
            available_categories = ", ".join(
                YANTRA_SOURCES.keys()
            )

            raise ValueError(
                f"Unsupported Yantra category: "
                f"{category}. "
                f"Available categories: "
                f"{available_categories}"
            )

        try:
            self.start_page = max(
                1,
                int(start_page),
            )

            self.max_pages = max(
                self.start_page,
                int(max_pages),
            )
        except ValueError as error:
            raise ValueError(
                "start_page and max_pages "
                "must be valid integers."
            ) from error

        self.source: dict[str, Any] = source

    def build_page_url(
        self,
        page_number: int,
    ) -> str:
        """
        Add or replace Yantra's _paged query parameter.

        Example:
        https://yantranepal.com/mobile-price-in-nepal/
        becomes:
        https://yantranepal.com/mobile-price-in-nepal/?_paged=2
        """

        base_url = self.source["url"]

        url_parts = urlsplit(base_url)

        query_params = parse_qs(
            url_parts.query,
            keep_blank_values=True,
        )

        query_params["_paged"] = [
            str(page_number)
        ]

        return urlunsplit(
            (
                url_parts.scheme,
                url_parts.netloc,
                url_parts.path,
                urlencode(
                    query_params,
                    doseq=True,
                ),
                url_parts.fragment,
            )
        )

    async def start(self):
        """
        Generate the first Yantra request.

        Scrapy 2.16 uses async start() instead of
        the older start_requests() method.
        """

        first_url = self.build_page_url(
            self.start_page
        )

        yield scrapy.Request(
            url=first_url,
            callback=self.parse,
            headers={
                "Referer": (
                    "https://yantranepal.com/"
                ),
            },
            cb_kwargs={
                "page_number": self.start_page,
                "previous_signature": None,
            },
            dont_filter=True,
        )

    def save_debug_response(
        self,
        response: scrapy.http.Response,
        page_number: int,
        suffix: str = "debug",
    ) -> None:
        """
        Save the HTML response when selectors fail.
        """

        output_directory = Path(
            "outputs/yantra"
        )

        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        debug_path = output_directory / (
            f"yantra_page_{page_number}_"
            f"{suffix}.html"
        )

        try:
            debug_path.write_bytes(
                response.body
            )

            self.logger.info(
                "Saved Yantra debug response: %s",
                debug_path,
            )
        except OSError as error:
            self.logger.error(
                "Could not save Yantra debug "
                "response: %s",
                error,
            )

    def find_product_card(
        self,
        title_link,
    ):
        """
        Starting from the product title link, move upward
        to the nearest surrounding element that also
        contains a product price.

        This avoids depending on one specific CSS class.
        """

        return title_link.xpath(
            """
            ancestor::*[
                (
                    self::div
                    or self::article
                    or self::li
                    or self::section
                )
                and (
                    contains(
                        normalize-space(string(.)),
                        'Rs.'
                    )
                    or contains(
                        normalize-space(string(.)),
                        'NPR'
                    )
                )
            ][1]
            """
        )

    def extract_price_text(
        self,
        product_card,
    ) -> str:
        """
        Try common WooCommerce price selectors first.
        Fall back to the complete product-card text.
        """

        price_selectors = product_card.css(
            (
                ".price, "
                ".product-price, "
                ".woocommerce-Price-amount, "
                ".amount"
            )
        )

        for selector in price_selectors:
            price_text = clean_text(
                selector.xpath(
                    "normalize-space(string(.))"
                ).get()
            )

            if parse_yantra_price(
                price_text
            ) is not None:
                return price_text

        return clean_text(
            product_card.xpath(
                "normalize-space(string(.))"
            ).get()
        )

    def parse(
        self,
        response: scrapy.http.Response, # type:ignore
        page_number: int,
        previous_signature: (
            tuple[str, ...] | None
        ),
    ):
        category_name = self.source["category"]

        if response.status == 403:
            self.logger.error(
                "Yantra rejected page %s with "
                "HTTP 403: %s",
                page_number,
                response.url,
            )

            self.save_debug_response(
                response=response,
                page_number=page_number,
                suffix="403",
            )

            return

        # Yantra product names are displayed as linked
        # h2 headings. Non-product h2 links are filtered
        # later by price and variant validation.
        title_links = response.xpath(
            "//h2/a[@href]"
        )

        self.logger.info(
            "Yantra page %s: found %s "
            "linked h2 headings",
            page_number,
            len(title_links),
        )

        if not title_links:
            self.logger.error(
                "No linked h2 headings were found "
                "on Yantra page %s.",
                page_number,
            )

            self.save_debug_response(
                response=response,
                page_number=page_number,
            )

            return

        current_product_urls: list[str] = []

        # Number of valid products on this page before
        # applying the optional brand filter.
        page_products_found = 0

        # Number of items actually yielded after applying
        # the optional brand filter.
        yielded_products = 0

        for title_link in title_links:
            raw_title = clean_text(
                title_link.xpath(
                    "normalize-space(string(.))"
                ).get()
            )

            product_path = title_link.attrib.get(
                "href"
            )

            if not raw_title or not product_path:
                continue

            product_card = self.find_product_card(
                title_link
            )

            if not product_card:
                self.logger.debug(
                    "No product card found for: %s",
                    raw_title,
                )
                continue

            card_text = clean_text(
                product_card.xpath(
                    "normalize-space(string(.))"
                ).get()
            )

            raw_price = self.extract_price_text(
                product_card
            )

            parsed_price = parse_yantra_price(
                raw_price
            )

            if parsed_price is None:
                self.logger.debug(
                    "Skipping product with invalid "
                    "price: %s | %s",
                    raw_title,
                    raw_price,
                )
                continue

            # First extract RAM/storage from the title:
            #
            # Xiaomi Redmi A1 (2GB | 32GB)
            parsed_variant = (
                parse_variant_from_title(
                    raw_title
                )
            )

            # Fall back to the specification list:
            #
            # Ram: 2GB
            # Storage: 32GB
            if parsed_variant is None:
                raw_ram = extract_labeled_spec(
                    product_card,
                    "Ram",
                )

                raw_storage = extract_labeled_spec(
                    product_card,
                    "Storage",
                )

                parsed_variant = (
                    parse_variant_from_values(
                        ram_text=raw_ram,
                        storage_text=raw_storage,
                    )
                )

            # Stick to the existing schema. Products
            # without a valid storage/variant structure
            # are skipped.
            if parsed_variant is None:
                self.logger.debug(
                    "Skipping product without valid "
                    "RAM/storage: %s",
                    raw_title,
                )
                continue

            model_name = (
                remove_variant_from_title(
                    raw_title
                )
            )

            if not model_name:
                continue

            brand_name = detect_yantra_brand(
                model_name
            )

            if not brand_name:
                self.logger.debug(
                    "Unable to detect brand: %s",
                    model_name,
                )
                continue

            product_url = response.urljoin(
                product_path
            )

            current_product_urls.append(
                product_url
            )

            page_products_found += 1

            # When a specific brand is requested,
            # continue crawling other pages even when
            # this page does not contain that brand.
            if (
                self.brand_filter != "all"
                and normalize_brand_key(
                    brand_name
                )
                != self.brand_filter
            ):
                continue

            normalized_card_text = (
                card_text.lower()
            )

            if (
                "out of stock"
                in normalized_card_text
            ):
                in_stock: bool | None = False

            elif (
                "add to cart"
                in normalized_card_text
            ):
                in_stock = True

            else:
                in_stock = None

            yielded_products += 1

            yield ProductOfferItem(
                store="Yantra Nepal",
                category=category_name,
                brand=brand_name,
                model_name=model_name,
                variant=parsed_variant[
                    "variant"
                ],
                ram=parsed_variant["ram"],
                storage=parsed_variant[
                    "storage"
                ],
                price=parsed_price["price"],
                price_text=parsed_price[
                    "price_text"
                ],
                price_type="exact",
                currency="NPR",
                product_url=product_url,
                source_url=response.url,
                in_stock=in_stock,
                scraped_at=datetime.now(
                    timezone.utc
                ).isoformat(),
            )

        self.logger.info(
            "Yantra page %s: parsed %s valid "
            "products and yielded %s items",
            page_number,
            page_products_found,
            yielded_products,
        )

        if page_products_found == 0:
            self.logger.error(
                "No valid Yantra products were "
                "parsed on page %s.",
                page_number,
            )

            self.save_debug_response(
                response=response,
                page_number=page_number,
            )

            return

        current_signature = tuple(
            sorted(
                set(current_product_urls)
            )
        )

        # Stop if the website returns the same products
        # again for the next page number.
        if (
            previous_signature is not None
            and current_signature
            == previous_signature
        ):
            self.logger.warning(
                "Yantra page %s repeated the "
                "previous page. Pagination stopped.",
                page_number,
            )

            return

        body_text = clean_text(
            response.xpath(
                "string(//body)"
            ).get()
        )

        pagination_summary = (
            parse_pagination_summary(
                body_text
            )
        )

        if pagination_summary is not None:
            self.logger.info(
                "Yantra pagination: showing "
                "%s-%s of %s products",
                pagination_summary["start"],
                pagination_summary["end"],
                pagination_summary["total"],
            )

            if (
                pagination_summary["end"]
                >= pagination_summary["total"]
            ):
                self.logger.info(
                    "Reached the final Yantra page."
                )

                return

        next_page_number = page_number + 1

        if next_page_number > self.max_pages:
            self.logger.warning(
                "Reached configured max_pages=%s.",
                self.max_pages,
            )

            return

        # Prefer Yantra's actual next-page link.
        next_url = response.css(
            (
                "a.next.page-numbers::attr(href), "
                "a.next::attr(href), "
                "a[rel='next']::attr(href)"
            )
        ).get()

        # If no next link is found, generate the next
        # _paged URL manually. Repeated-page detection
        # prevents an infinite loop after the final page.
        if next_url:
            next_url = response.urljoin(
                next_url
            )
        else:
            next_url = self.build_page_url(
                next_page_number
            )

        self.logger.info(
            "Requesting Yantra page %s: %s",
            next_page_number,
            next_url,
        )

        yield scrapy.Request(
            url=next_url,
            callback=self.parse,
            headers={
                "Referer": response.url,
            },
            cb_kwargs={
                "page_number": next_page_number,
                "previous_signature": (
                    current_signature
                ),
            },
        )