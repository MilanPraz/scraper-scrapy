import scrapy


class ProductOfferItem(scrapy.Item):
    store = scrapy.Field()
    category = scrapy.Field()
    brand = scrapy.Field()

    model_name = scrapy.Field()
    variant = scrapy.Field()

    ram = scrapy.Field()
    storage = scrapy.Field()

    price = scrapy.Field()
    price_text = scrapy.Field()
    price_type= scrapy.Field()  # exact / starting
    currency = scrapy.Field()
    discounted_price = scrapy.Field()

    product_url = scrapy.Field()
    source_url = scrapy.Field()
    image_url = scrapy.Field()

    in_stock = scrapy.Field()
    scraped_at = scrapy.Field()