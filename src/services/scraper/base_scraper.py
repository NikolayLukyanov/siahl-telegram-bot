"""Base async scraper with retry logic and rate limiting."""

import asyncio
from typing import Optional
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup
from loguru import logger

from src.config import settings


class ScraperError(Exception):
    """Base exception for scraper errors."""
    pass


class RateLimitError(ScraperError):
    """Raised when rate limit is exceeded."""
    pass


class BaseScraper:
    """
    Base async scraper with:
    - Retry logic with exponential backoff
    - Rate limiting (respect SIAHL servers)
    - User-agent rotation
    - HTML parsing with BeautifulSoup
    """

    def __init__(self):
        self.base_url = settings.siahl_base_url
        self.user_agent = settings.scraper_user_agent
        self.max_retries = settings.scraper_max_retries
        self.delay_seconds = settings.scraper_delay_seconds
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_request_time: float = 0

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(
                headers={"User-Agent": self.user_agent},
                timeout=timeout
            )

    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _rate_limit(self):
        """Implement rate limiting between requests."""
        import time
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time

        if time_since_last_request < self.delay_seconds:
            sleep_time = self.delay_seconds - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            await asyncio.sleep(sleep_time)

        self._last_request_time = time.time()

    async def _fetch_html(
        self,
        url: str,
        retries: int = 0,
        params: Optional[dict] = None
    ) -> str:
        """
        Fetch HTML content from URL with retry logic.

        Args:
            url: URL to fetch
            retries: Current retry attempt
            params: Query parameters

        Returns:
            HTML content as string

        Raises:
            ScraperError: If fetching fails after all retries
        """
        await self._ensure_session()
        await self._rate_limit()

        # Make URL absolute if relative
        if not url.startswith("http"):
            url = urljoin(self.base_url, url)

        try:
            logger.debug(f"Fetching URL: {url} (attempt {retries + 1}/{self.max_retries + 1})")

            async with self._session.get(url, params=params) as response:
                # Check for rate limiting
                if response.status == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    raise RateLimitError(f"Rate limited. Retry after {retry_after}s")

                # Raise for bad status codes
                response.raise_for_status()

                html = await response.text()
                logger.debug(f"Successfully fetched {len(html)} bytes from {url}")
                return html

        except aiohttp.ClientError as e:
            logger.warning(f"Request failed for {url}: {e}")

            # Retry with exponential backoff
            if retries < self.max_retries:
                backoff_time = 2 ** retries  # 1s, 2s, 4s
                logger.info(f"Retrying in {backoff_time}s...")
                await asyncio.sleep(backoff_time)
                return await self._fetch_html(url, retries + 1, params)
            else:
                raise ScraperError(f"Failed to fetch {url} after {self.max_retries} retries: {e}")

        except RateLimitError as e:
            logger.error(f"Rate limit error: {e}")
            if retries < self.max_retries:
                # Wait and retry
                await asyncio.sleep(60)
                return await self._fetch_html(url, retries + 1, params)
            else:
                raise

    def _parse_html(self, html: str) -> BeautifulSoup:
        """
        Parse HTML content with BeautifulSoup.

        Args:
            html: HTML string

        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html, "lxml")

    async def fetch_and_parse(
        self,
        url: str,
        params: Optional[dict] = None
    ) -> BeautifulSoup:
        """
        Fetch URL and parse HTML in one step.

        Args:
            url: URL to fetch
            params: Query parameters

        Returns:
            Parsed BeautifulSoup object
        """
        html = await self._fetch_html(url, params=params)
        return self._parse_html(html)

    def extract_text(self, element, default: str = "") -> str:
        """
        Safely extract text from BeautifulSoup element.

        Args:
            element: BeautifulSoup element
            default: Default value if element is None

        Returns:
            Extracted text or default
        """
        if element is None:
            return default
        return element.get_text(strip=True)

    def extract_attr(self, element, attr: str, default: str = "") -> str:
        """
        Safely extract attribute from BeautifulSoup element.

        Args:
            element: BeautifulSoup element
            attr: Attribute name
            default: Default value if element/attribute is None

        Returns:
            Attribute value or default
        """
        if element is None:
            return default
        return element.get(attr, default)
