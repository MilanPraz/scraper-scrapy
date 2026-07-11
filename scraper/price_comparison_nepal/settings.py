# Scrapy settings for price_comparison_nepal project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "price_comparison_nepal"

SPIDER_MODULES = ["price_comparison_nepal.spiders"]
NEWSPIDER_MODULE = "price_comparison_nepal.spiders"

ADDONS = {}


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "price_comparison_nepal (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Concurrency and throttling settings
#CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "price_comparison_nepal.middlewares.PriceComparisonNepalSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    "price_comparison_nepal.middlewares.PriceComparisonNepalDownloaderMiddleware": 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   "price_comparison_nepal.pipelines.ProductValidationPipeline": 100,
   "price_comparison_nepal.pipelines.DuplicateProductRemovePipeline": 200,
   "price_comparison_nepal.pipelines.SaveProductToDatabasePipeline": 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"
FEED_EXPORT_FIELDS = [
    "store",
    "category",
    "brand",
    "model_name",
    "variant",
    "ram",
    "storage",
    "price",
    "price_text",
    "price_type",
    "currency",
    "product_url",
    "source_url",
    "in_stock",
    "scraped_at",
]

# Reduce unnecessary console output.
LOG_LEVEL = "INFO"

TELNETCONSOLE_ENABLED = False

DOWNLOAD_HANDLERS = {
    "http": (
        "scrapy_playwright.handler."
        "ScrapyPlaywrightDownloadHandler"
    ),
    "https": (
        "scrapy_playwright.handler."
        "ScrapyPlaywrightDownloadHandler"
    ),
}

TWISTED_REACTOR = (
    "twisted.internet.asyncioreactor."
    "AsyncioSelectorReactor"
)

PLAYWRIGHT_BROWSER_TYPE = "chromium"

PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
}

# Used only when evaluating robots.txt rules.
ROBOTSTXT_USER_AGENT = "NepalPriceComparisonBot"
# Let Chromium send its normal browser User-Agent.

USER_AGENT = None

