"""
Base Web Automation Framework

Provides foundational classes for web browser automation experiments.
"""

import logging
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Any

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager

from .config import RPAConfig, CredentialsManager


class BaseWebAutomation:
    """
    Base class for web automation experiments

    Provides common functionality for browser automation including:
    - Browser initialization and cleanup
    - Element interaction with retry logic
    - Screenshot capture
    - Logging and error handling
    """

    def __init__(self, config: Optional[RPAConfig] = None):
        """
        Initialize web automation

        Args:
            config: RPA configuration (uses default if not provided)
        """
        self.config = config or RPAConfig()
        self.driver: Optional[webdriver.Chrome] = None
        self.logger = self._setup_logging()
        self.credentials_manager = CredentialsManager()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(getattr(logging, self.config.log_level))

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # File handler
        if self.config.log_file:
            file_handler = logging.FileHandler(self.config.log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(console_formatter)
            logger.addHandler(file_handler)

        return logger

    def _initialize_browser(self):
        """Initialize browser with configuration"""
        self.logger.info("Initializing browser...")

        chrome_options = ChromeOptions()

        if self.config.headless:
            chrome_options.add_argument("--headless")

        # Security and privacy settings
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        # Window size
        chrome_options.add_argument(
            f"--window-size={self.config.window_width},{self.config.window_height}"
        )

        # User agent to avoid detection
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # Initialize driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        # Set timeouts
        self.driver.set_page_load_timeout(self.config.page_load_timeout)
        self.driver.implicitly_wait(self.config.implicit_wait)

        self.logger.info("Browser initialized successfully")

    def start(self):
        """Start the automation session"""
        if not self.driver:
            self._initialize_browser()

    def stop(self):
        """Stop the automation session and cleanup"""
        if self.driver:
            self.logger.info("Closing browser...")
            self.driver.quit()
            self.driver = None
            self.logger.info("Browser closed")

        # Clear credentials from memory
        self.credentials_manager.clear_credentials()

    def navigate_to(self, url: str):
        """
        Navigate to URL

        Args:
            url: Target URL
        """
        self.logger.info(f"Navigating to: {url}")
        self.driver.get(url)
        self._random_delay()

    def _random_delay(self, min_delay: Optional[float] = None, max_delay: Optional[float] = None):
        """
        Add random delay to mimic human behavior

        Args:
            min_delay: Minimum delay in seconds (uses config if not provided)
            max_delay: Maximum delay in seconds (uses config if not provided)
        """
        min_d = min_delay or self.config.min_action_delay
        max_d = max_delay or self.config.max_action_delay
        delay = random.uniform(min_d, max_d)
        time.sleep(delay)

    def find_element_safe(
        self, by: By, value: str, timeout: Optional[int] = None
    ) -> Optional[Any]:
        """
        Safely find element with explicit wait

        Args:
            by: Locator strategy (By.ID, By.CSS_SELECTOR, etc.)
            value: Locator value
            timeout: Wait timeout in seconds (uses config if not provided)

        Returns:
            WebElement if found, None otherwise
        """
        timeout = timeout or self.config.explicit_wait

        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.presence_of_element_located((by, value)))
            self.logger.debug(f"Element found: {by}={value}")
            return element
        except TimeoutException:
            self.logger.warning(f"Element not found within {timeout}s: {by}={value}")
            return None
        except Exception as e:
            self.logger.error(f"Error finding element {by}={value}: {e}")
            return None

    def click_element_safe(self, by: By, value: str, timeout: Optional[int] = None) -> bool:
        """
        Safely click element with retry logic

        Args:
            by: Locator strategy
            value: Locator value
            timeout: Wait timeout in seconds

        Returns:
            True if successful, False otherwise
        """
        for attempt in range(self.config.max_retries):
            try:
                element = self.find_element_safe(by, value, timeout)
                if element:
                    # Wait for element to be clickable
                    wait = WebDriverWait(self.driver, timeout or self.config.explicit_wait)
                    clickable = wait.until(EC.element_to_be_clickable((by, value)))
                    clickable.click()
                    self.logger.info(f"Clicked element: {by}={value}")
                    self._random_delay()
                    return True
            except Exception as e:
                self.logger.warning(
                    f"Click attempt {attempt + 1} failed for {by}={value}: {e}"
                )
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay)

        self.logger.error(f"Failed to click element after {self.config.max_retries} attempts")
        return False

    def input_text_safe(
        self, by: By, value: str, text: str, clear_first: bool = True
    ) -> bool:
        """
        Safely input text into element

        Args:
            by: Locator strategy
            value: Locator value
            text: Text to input
            clear_first: Clear existing text first

        Returns:
            True if successful, False otherwise
        """
        try:
            element = self.find_element_safe(by, value)
            if element:
                if clear_first:
                    element.clear()
                    self._random_delay(0.2, 0.5)

                # Type character by character to mimic human typing
                for char in text:
                    element.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))

                self.logger.info(f"Input text to element: {by}={value}")
                self._random_delay()
                return True
        except Exception as e:
            self.logger.error(f"Failed to input text to {by}={value}: {e}")

        return False

    def take_screenshot(self, name: Optional[str] = None) -> Optional[str]:
        """
        Take screenshot

        Args:
            name: Screenshot name (generates timestamp-based name if not provided)

        Returns:
            Screenshot file path if successful, None otherwise
        """
        if not self.driver:
            return None

        try:
            if not name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                name = f"screenshot_{timestamp}.png"

            filepath = Path(self.config.screenshot_dir) / name
            self.driver.save_screenshot(str(filepath))
            self.logger.info(f"Screenshot saved: {filepath}")
            return str(filepath)
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
            return None

    def handle_error(self, error: Exception, context: str = ""):
        """
        Handle errors with logging and optional screenshot

        Args:
            error: Exception that occurred
            context: Context description
        """
        self.logger.error(f"Error in {context}: {error}", exc_info=True)

        if self.config.screenshot_on_error:
            error_name = f"error_{context}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            self.take_screenshot(error_name)

    def wait_for_page_load(self, timeout: Optional[int] = None):
        """
        Wait for page to fully load

        Args:
            timeout: Wait timeout in seconds
        """
        timeout = timeout or self.config.page_load_timeout
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            self.logger.debug("Page loaded completely")
        except TimeoutException:
            self.logger.warning(f"Page load timeout after {timeout}s")

    def execute_with_retry(self, func, *args, **kwargs) -> Optional[Any]:
        """
        Execute function with retry logic

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result if successful, None otherwise
        """
        for attempt in range(self.config.max_retries):
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay)
                else:
                    self.logger.error(f"All {self.config.max_retries} attempts failed")
                    return None

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
