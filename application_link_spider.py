from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
import json
import os
import time


class ApplicationLinkSpider:
    def __init__(self, headless=False, auth_file="himalayan_auth.json"):
        """
        Initialize the spider with browser options and authentication.

        Args:
            headless: Run browser in headless mode (default: False for visible browser)
            auth_file: Path to JSON file containing cookies and localStorage data
        """
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.maximize_window()
        self.auth_file = auth_file
        self._load_auth_data()

    def _load_auth_data(self):
        """Load authentication data (cookies and localStorage) from JSON file."""
        if not os.path.exists(self.auth_file):
            print(f"Warning: Auth file '{self.auth_file}' not found. Continuing without authentication.")
            return

        try:
            with open(self.auth_file, 'r') as f:
                auth_data = json.load(f)

            # Navigate to the domain first before adding cookies
            self.driver.get("https://himalayas.app")
            time.sleep(1)

            # Add cookies
            if 'cookies' in auth_data:
                for cookie in auth_data['cookies']:
                    try:
                        # Remove sameSite if it's not a valid value for Selenium
                        cookie_to_add = cookie.copy()
                        if 'sameSite' in cookie_to_add:
                            # Convert sameSite to proper format
                            same_site = cookie_to_add['sameSite']
                            if same_site not in ['Strict', 'Lax', 'None']:
                                del cookie_to_add['sameSite']

                        # Selenium expects 'expiry' not 'expires'
                        if 'expires' in cookie_to_add:
                            if cookie_to_add['expires'] > 0:
                                cookie_to_add['expiry'] = int(cookie_to_add['expires'])
                            del cookie_to_add['expires']

                        self.driver.add_cookie(cookie_to_add)
                    except Exception as e:
                        # Skip cookies that can't be added (e.g., wrong domain)
                        continue

            # Set localStorage
            if 'origins' in auth_data:
                for origin in auth_data['origins']:
                    origin_url = origin.get('origin')
                    if origin_url and 'localStorage' in origin:
                        # Navigate to the origin to set localStorage
                        self.driver.get(origin_url)
                        time.sleep(0.5)

                        for item in origin['localStorage']:
                            try:
                                script = f"window.localStorage.setItem('{item['name']}', {json.dumps(item['value'])});"
                                self.driver.execute_script(script)
                            except Exception as e:
                                continue

            print(f"Authentication data loaded from '{self.auth_file}'")

        except Exception as e:
            print(f"Error loading auth data: {e}")

    def close_popups(self):
        """Attempt to close any popups that might appear."""
        popup_selectors = [
            "//button[contains(text(), 'Close')]",
            "//button[contains(text(), 'Dismiss')]",
            "//button[contains(text(), 'No thanks')]",
            "//button[contains(@class, 'close')]",
            "//div[contains(@class, 'modal')]//button",
            "//button[@aria-label='Close']",
            "//*[@id='close']",
        ]

        for selector in popup_selectors:
            try:
                close_button = self.driver.find_element(By.XPATH, selector)
                close_button.click()
                time.sleep(0.5)
            except NoSuchElementException:
                continue

    def process_job_link(self, job_url):
        """
        Process a single job link: open it, click apply, handle popups, and return final URL.

        Args:
            job_url: The job application URL to process

        Returns:
            dict: Contains 'original_url', 'final_url', 'status', and 'error' (if any)
        """
        result = {
            'original_url': job_url,
            'final_url': None,
            'status': 'failed',
            'error': None
        }

        try:
            # Load the page
            self.driver.get(job_url)
            time.sleep(2)  # Wait for page to load

            # Store current window handle and count
            original_window = self.driver.current_window_handle
            original_windows = set(self.driver.window_handles)

            # Close any initial popups
            self.close_popups()

            # Try to find and click the apply button
            apply_button_selectors = [
                "//button[contains(text(), 'Apply')]",
                "//a[contains(text(), 'Apply')]",
                "//button[contains(@class, 'apply')]",
                "//a[contains(@class, 'apply')]",
                "//button[contains(text(), 'apply')]",
                "//a[contains(text(), 'apply')]",
                "//*[@id='apply']",
                "//button[@type='submit']",
            ]

            button_clicked = False
            for selector in apply_button_selectors:
                try:
                    wait = WebDriverWait(self.driver, 3)
                    apply_button = wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    apply_button.click()
                    button_clicked = True
                    break
                except (TimeoutException, NoSuchElementException):
                    continue

            if button_clicked:
                # Wait for modal to appear
                time.sleep(1)

                # Check for "Don't show this again" button in modal
                modal_button_selectors = [
                    "//button[contains(text(), \"Don't show this again\")]",
                    "//button[contains(text(), \"Don't show\")]",
                    "//button[contains(text(), 'Do not show')]",
                    "//*[contains(text(), \"Don't show this again\")]",
                ]

                for modal_selector in modal_button_selectors:
                    try:
                        modal_wait = WebDriverWait(self.driver, 2)
                        modal_button = modal_wait.until(
                            EC.element_to_be_clickable((By.XPATH, modal_selector))
                        )
                        modal_button.click()
                        print("  Clicked 'Don't show this again' button")
                        break
                    except (TimeoutException, NoSuchElementException):
                        continue

                # Wait for new tab/window to open or redirect
                time.sleep(2)

                # Check if a new window/tab was opened
                new_windows = set(self.driver.window_handles) - original_windows

                if new_windows:
                    # Switch to the new tab
                    new_window = new_windows.pop()
                    self.driver.switch_to.window(new_window)

                    # Wait for the new tab to load
                    time.sleep(2)

                    # Close any popups in the new tab
                    self.close_popups()

                    # Wait a bit more for any final redirects
                    time.sleep(1)

                    # Get the final URL from the new tab
                    result['final_url'] = self.driver.current_url

                    # Close the new tab and switch back to original
                    self.driver.close()
                    self.driver.switch_to.window(original_window)
                else:
                    # No new tab, just a redirect in the same window
                    self.close_popups()
                    time.sleep(1)
                    result['final_url'] = self.driver.current_url

                result['status'] = 'success'
            else:
                result['error'] = 'Could not find apply button'
                result['final_url'] = self.driver.current_url
                result['status'] = 'no_apply_button'

        except Exception as e:
            result['error'] = str(e)
            try:
                result['final_url'] = self.driver.current_url
            except:
                result['final_url'] = job_url

        return result

    def process_jobs(self, jobs):
        """
        Process multiple job listings from himalayan_jobs_formatter.

        Args:
            jobs: List of job dictionaries from himalayan_jobs_formatter

        Returns:
            list: List of results with original and final URLs
        """
        results = []

        for idx, job in enumerate(jobs):
            print(f"Processing job {idx + 1}/{len(jobs)}: {job.get('title', 'Unknown')} at {job.get('companyName', 'Unknown')}")

            job_url = job.get('url')
            if not job_url:
                results.append({
                    'original_url': None,
                    'final_url': None,
                    'status': 'failed',
                    'error': 'No URL provided',
                    'job_title': job.get('title'),
                    'company': job.get('companyName')
                })
                continue

            result = self.process_job_link(job_url)
            result['job_title'] = job.get('title')
            result['company'] = job.get('companyName')
            results.append(result)

            print(f"  Status: {result['status']}")
            print(f"  Final URL: {result['final_url']}")
            if result['error']:
                print(f"  Error: {result['error']}")
            print()

        return results

    def close(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
