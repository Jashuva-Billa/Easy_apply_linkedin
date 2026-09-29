import os
import logging
import platform
import random
from playwright.sync_api import sync_playwright, Browser as PlaywrightBrowser, BrowserContext, Page
try:
    import tkinter as tk
    HAS_TKINTER = True
except:
    HAS_TKINTER = False

log = logging.getLogger(__name__)

class Browser:
    def __init__(self, profile_path=None, proxy_config=None, headless=False):
        self.profile_path = profile_path
        self.proxy_config = proxy_config
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        if profile_path:
            os.makedirs(profile_path, exist_ok=True)
            self.use_persistent = True
        else:
            self.use_persistent = False
        self._setup_browser()

    def _get_screen_resolution(self):
        """Detect actual screen resolution to prevent off-screen issues"""
        try:
            if HAS_TKINTER:
                root = tk.Tk()
                root.withdraw()  # Hide the window
                width = root.winfo_screenwidth()
                height = root.winfo_screenheight()
                root.destroy()
                log.info(f"Detected screen resolution: {width}x{height}")
                return {'width': width, 'height': height}
        except Exception as e:
            log.warning(f"Could not detect screen resolution: {e}")
        
        # Fallback to safe default
        return {'width': 1366, 'height': 768}
    
    def _setup_browser(self):
        """
        Initialize Playwright browser with stealth and anti-detection features
        """
        self.playwright = sync_playwright().start()
        
        # Get actual screen resolution
        screen_res = self._get_screen_resolution()
        
        # Browser launch arguments for stealth - reduced set to avoid crashes
        launch_args = [
            '--disable-blink-features=AutomationControlled',
            '--exclude-switches=enable-automation',
            '--disable-infobars',
            '--start-maximized',
            '--no-sandbox',  # Keep this for compatibility
            '--disable-dev-shm-usage',  # Keep this to avoid shared memory issues
        ]
        
        # If using persistent context (recommended for LinkedIn)
        if self.use_persistent:
            log.info(f"Using persistent context: {self.profile_path}")
            
            # Build context options with balanced stealth (avoid flag conflicts)
            context_options = {
                'headless': self.headless,
                'args': launch_args,
                'viewport': screen_res,
                'user_agent': self._get_random_user_agent(),
                'locale': 'en-US',
                'timezone_id': 'America/New_York',
                'permissions': ['geolocation', 'notifications'],
                'color_scheme': 'light',
                'device_scale_factor': 1,
                'has_touch': False,
                'is_mobile': False,
                'ignore_default_args': ['--enable-automation', '--enable-blink-features=AutomationControlled'],
            }
            
            # Add proxy if configured
            if self.proxy_config:
                proxy_dict = self.proxy_config.to_playwright_dict()
                context_options['proxy'] = proxy_dict
                log.info(f"Using proxy: {self.proxy_config.name}")
            
            # Launch persistent context (this is the key for avoiding detection!)
            try:
                self.context = self.playwright.chromium.launch_persistent_context(
                    self.profile_path,
                    **context_options
                )
            except Exception as e:
                log.error(f"Failed to launch with persistent context: {e}")
                log.info("Attempting to launch with minimal flags...")
                # Fallback to minimal configuration
                minimal_options = {
                    'headless': self.headless,
                    'args': ['--no-sandbox', '--disable-dev-shm-usage'],
                    'viewport': screen_res,
                }
                self.context = self.playwright.chromium.launch_persistent_context(
                    self.profile_path,
                    **minimal_options
                )
            
            # Get or create page
            self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
            
            # Add advanced stealth scripts
            self._add_stealth_scripts()
            
        else:
            # Regular browser mode (less stealthy)
            log.info("Using regular browser mode (no persistent profile)")
            
            # Launch browser
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=launch_args,
                chromium_sandbox=False
            )
            
            # Context options for anti-detection
            context_options = {
                'viewport': screen_res,
                'user_agent': self._get_random_user_agent(),
                'locale': 'en-US',
                'timezone_id': 'America/New_York',
                'permissions': ['geolocation', 'notifications'],
                'color_scheme': 'light',
                'extra_http_headers': {
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
            }
            
            # Add proxy if configured
            if self.proxy_config:
                proxy_string = self.proxy_config.get_chrome_proxy_string()
                context_options['proxy'] = {
                    'server': proxy_string
                }
                if self.proxy_config.username and self.proxy_config.password:
                    context_options['proxy']['username'] = self.proxy_config.username
                    context_options['proxy']['password'] = self.proxy_config.password
                log.info(f"Using proxy: {self.proxy_config.name}")
            
            # Create context
            self.context = self.browser.new_context(**context_options)
            
            # Create initial page
            self.page = self.context.new_page()
        
        # Add stealth scripts to bypass detection (for both modes)
        self.context.add_init_script("""
            // Overwrite the `webdriver` property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true
            });
            
            // Overwrite the `plugins` property
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
                configurable: true
            });
            
            // Overwrite the `languages` property
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
                configurable: true
            });
            
            // Add chrome object
            window.chrome = {
                runtime: {}
            };
            
            // Mock permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        log.info("Playwright browser initialized with advanced stealth features")
    
    def _add_stealth_scripts(self):
        """
        Add extra stealth scripts for persistent context
        """
        log.info("Applying additional stealth enhancements...")
    
    def _get_random_user_agent(self):
        """
        Generate a random but realistic user agent
        """
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        ]
        return random.choice(user_agents)
    
    def get_page(self) -> Page:
        """
        Get the current page object
        """
        return self.page
    
    def close(self):
        """
        Clean up browser resources
        """
        if self.page and not self.use_persistent:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser and not self.use_persistent:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        log.info("Browser closed")
