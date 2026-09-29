import time
import random
from typing import Tuple
from bot.utils.logger import logger
from bot.utils.selectors import get_locator
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError


class Session:
    def __init__(self, page: Page):
        self.page = page
        self._is_authenticated = False

    def is_authenticated(self, timeout_ms: int = 5000) -> bool:
        """
        Verify if the current browser session is authenticated on LinkedIn.
        Checks:
        1. Current URL does not contain login/authwall/checkpoint paths.
        2. Presence of authenticated navigation elements (global-nav, avatar, feed link, search bar).
        3. Absence of visible login inputs / sign-in forms.
        """
        try:
            current_url = self.page.url.lower()

            # If on about:blank or not on LinkedIn, navigate to feed to verify
            if not current_url.startswith("https://www.linkedin.com") and not current_url.startswith("https://linkedin.com"):
                try:
                    self.page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=timeout_ms)
                    current_url = self.page.url.lower()
                except Exception:
                    return False

            # Explicit unauthenticated or checkpoint URLs
            unauth_fragments = [
                "/login",
                "/uas/login",
                "/authwall",
                "/checkpoint",
                "/signup",
                "/home",
                "/uas/consumer-captcha"
            ]
            if any(fragment in current_url for fragment in unauth_fragments):
                return False

            # Negative check: visible password input or login button means unauthenticated
            login_inputs = self.page.locator("input[type='password']:visible").count()
            if login_inputs > 0:
                return False

            # Positive indicators: check for authenticated nav elements
            auth_selectors = [
                "nav.global-nav",
                "#global-nav",
                ".global-nav__me",
                "img.global-nav__me-photo",
                "button[aria-label*='me' i]",
                "button[aria-label*='profile' i]",
                "a.global-nav__primary-link[href*='/feed']",
                ".search-global-typeahead__input",
                ".feed-identity-module",
                "a[href*='/jobs']"
            ]

            for selector in auth_selectors:
                if self.page.locator(selector).first.is_visible():
                    self._is_authenticated = True
                    return True

            # If on /feed, /jobs, or /mynetwork, wait briefly for nav selector to render
            if any(path in current_url for path in ["/feed", "/jobs", "/mynetwork", "/in/"]):
                try:
                    self.page.wait_for_selector(
                        "nav.global-nav, #global-nav, .global-nav__me, img.global-nav__me-photo, .search-global-typeahead__input",
                        timeout=timeout_ms
                    )
                    self._is_authenticated = True
                    return True
                except Exception:
                    pass

            return False
        except Exception as e:
            logger.debug(f"Error checking authentication state: {e}", step="login")
            return False

    def detect_security_challenge(self) -> Tuple[bool, str]:
        """
        Detect if LinkedIn has presented a security challenge, CAPTCHA, 2FA, or checkpoint.
        """
        try:
            current_url = self.page.url.lower()
            if any(p in current_url for p in ["checkpoint", "challenge", "consumer-captcha"]):
                return True, f"Checkpoint URL detected: {current_url}"

            # Check for captcha or challenge frames
            for frame in self.page.frames:
                frame_url = frame.url.lower()
                if any(k in frame_url for k in ["captcha", "challenge", "arkose"]):
                    return True, f"Security challenge frame detected: {frame_url}"

            # Check for challenge DOM elements
            challenge_selectors = [
                "#captcha-internal",
                "iframe[src*='captcha']",
                "iframe[title*='challenge']",
                "input#input__email_verification_pin",
                "input#input__phone_verification_pin",
                "input[name='pin']",
                "#email-pin-challenge",
                "#phone-pin-challenge"
            ]
            for sel in challenge_selectors:
                if self.page.locator(sel).first.is_visible():
                    return True, f"Challenge element detected: {sel}"

            # Text content check for known challenge phrases
            body_text = ""
            try:
                body_text = self.page.locator("body").inner_text(timeout=2000).lower()
            except Exception:
                pass

            challenge_phrases = [
                "quick security check",
                "security check",
                "verify it's you",
                "verification code",
                "two-step verification",
                "enter the code",
                "confirm your identity",
                "check your phone",
                "unusual activity"
            ]
            for phrase in challenge_phrases:
                if phrase in body_text:
                    return True, f"Security check phrase detected: '{phrase}'"

            return False, ""
        except Exception as e:
            logger.debug(f"Error checking security challenge: {e}", step="login")
            return False, ""

    def detect_login_error(self) -> Tuple[bool, str]:
        """
        Detect if LinkedIn displayed credential error messages (wrong password, account not found).
        """
        try:
            current_url = self.page.url.lower()
            if "/login" not in current_url and "/uas/login" not in current_url:
                return False, ""

            error_selectors = [
                "#error-for-password",
                "#error-for-username",
                "[role='alert']",
                ".artdeco-inline-feedback--error",
                "[data-test-form-element-error-message]",
                ".form__label--error"
            ]
            for sel in error_selectors:
                loc = self.page.locator(sel).first
                if loc.is_visible():
                    text = loc.text_content().strip()
                    if text:
                        return True, text

            # Check page body for explicit error keywords
            try:
                body_text = self.page.locator("body").inner_text(timeout=1000).lower()
                error_keywords = [
                    "that's not the right password",
                    "wrong password",
                    "couldn't find an account",
                    "please enter a valid email",
                    "incorrect password",
                    "we don't recognize that email"
                ]
                for kw in error_keywords:
                    if kw in body_text:
                        return True, kw
            except Exception:
                pass

            return False, ""
        except Exception as e:
            logger.debug(f"Error checking login error: {e}", step="login")
            return False, ""

    def handle_security_challenge(self) -> bool:
        """
        Pause and allow human-in-the-loop completion of security checkpoint / 2FA / CAPTCHA.
        """
        logger.warning("[LOGIN] Security verification / checkpoint detected!", step="login", event="checkpoint")
        print("\n" + "=" * 70)
        print("[!] LINKEDIN SECURITY VERIFICATION / CHECKPOINT DETECTED")
        print("=" * 70)
        print("LinkedIn requires manual verification (CAPTCHA, 2FA, or PIN code).")
        print("Please complete the verification directly in the opened browser window.")
        print("Once you see your LinkedIn feed or home page, return here.")
        print("=" * 70)

        try:
            ans = input("Press ENTER once verified in browser (or type 'cancel' to abort): ").strip()
            if ans.lower() == 'cancel':
                logger.error("[LOGIN] User cancelled security verification", step="login", event="cancelled")
                return False
        except (KeyboardInterrupt, EOFError):
            logger.error("[LOGIN] Verification interrupted", step="login", event="interrupted")
            return False

        logger.info("[LOGIN] Verifying authenticated session after manual action...", step="login", event="reverifying")

        # Allow up to 10 seconds for the session to settle and verify
        start_wait = time.time()
        while time.time() - start_wait < 10:
            if self.is_authenticated(timeout_ms=3000):
                logger.info("[LOGIN] SUCCESS", step="login", event="success")
                logger.info("[LOGIN] Authenticated LinkedIn session confirmed", step="login", event="authenticated")
                logger.info("[LOGIN] AUTHENTICATED SESSION VERIFIED", step="login", event="verified")
                return True
            time.sleep(1)

        logger.error("[LOGIN] FAILED", step="login", event="failure")
        logger.error("[LOGIN] Authentication could not be verified after verification step", step="login", event="failure")
        return False

    def login(self, username: str, password: str) -> bool:
        """
        Execute the complete LinkedIn authentication and verification flow.
        1. Check if persistent browser context is already authenticated.
        2. If not, navigate to login page.
        3. Enter credentials and submit.
        4. Explicitly verify authentication state (or detect challenges/errors).
        Returns True if session is verified as authenticated, False otherwise.
        """
        logger.info("LOGIN START", step="login", event="start")
        logger.info("[LOGIN] LOGIN START", step="login", event="start")

        # Step 1: Check existing session (session persistence)
        try:
            logger.info("[LOGIN] Checking existing session...", step="login", event="check_existing")
            if not self.page.url.startswith("https://www.linkedin.com"):
                self.page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=15000)

            time.sleep(2)
            if self.is_authenticated(timeout_ms=5000):
                logger.info("[LOGIN] Existing authenticated session found", step="login", event="session_reused")
                logger.info("LOGIN SUCCESS", step="login", event="success")
                logger.info("[LOGIN] SUCCESS", step="login", event="success")
                logger.info("[LOGIN] Authenticated LinkedIn session confirmed", step="login", event="authenticated")
                logger.info("AUTHENTICATED SESSION VERIFIED", step="login", event="verified")
                logger.info("[LOGIN] AUTHENTICATED SESSION VERIFIED", step="login", event="verified")
                return True

            # Check if initial navigation hit a security checkpoint
            is_challenge, challenge_reason = self.detect_security_challenge()
            if is_challenge:
                logger.warning(f"[LOGIN] Challenge encountered on startup: {challenge_reason}", step="login")
                return self.handle_security_challenge()

        except Exception as e:
            logger.warning(f"[LOGIN] Error checking existing session: {e}", step="login")

        # Step 2: Navigate to login page
        logger.info("[LOGIN] Opening LinkedIn login page", step="login", event="open_login")
        try:
            self.page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded", timeout=20000)

            # Robust locators for username/email, password, and sign-in button
            email_selector = get_locator("login_email") or "input[type='email']:visible, input[autocomplete='username']:visible, #username:visible, input[name='session_key']:visible"
            pwd_selector = get_locator("login_password") or "input[type='password']:visible, input[autocomplete='current-password']:visible, #password:visible, input[name='session_password']:visible"
            btn_selector = get_locator("login_submit") or "button:has-text('Sign in'):not(:has-text('Microsoft')):not(:has-text('Apple')):not(:has-text('Google')):visible, button[type='submit']:visible"

            email_loc = self.page.locator(email_selector).first
            pwd_loc = self.page.locator(pwd_selector).first
            btn_loc = self.page.locator(btn_selector).first

            # Wait for email input to be visible
            try:
                email_loc.wait_for(state="visible", timeout=15000)
            except PlaywrightTimeoutError:
                # Page could have redirected to feed or checkpoint
                if self.is_authenticated(timeout_ms=3000):
                    logger.info("LOGIN SUCCESS", step="login", event="success")
                    logger.info("[LOGIN] SUCCESS", step="login", event="success")
                    logger.info("[LOGIN] Authenticated LinkedIn session confirmed", step="login", event="authenticated")
                    logger.info("AUTHENTICATED SESSION VERIFIED", step="login", event="verified")
                    logger.info("[LOGIN] AUTHENTICATED SESSION VERIFIED", step="login", event="verified")
                    return True

                is_challenge, challenge_reason = self.detect_security_challenge()
                if is_challenge:
                    return self.handle_security_challenge()

                logger.error("[LOGIN] FAILED - Login form elements could not be found", step="login", event="failure")
                logger.error("[LOGIN] Authentication could not be verified", step="login", event="failure")
                return False

            # Step 3: Enter credentials
            logger.info("[LOGIN] Entering credentials", step="login", event="enter_credentials")
            email_loc.fill(username)
            time.sleep(random.uniform(0.5, 1.0))

            pwd_loc.fill(password)
            time.sleep(random.uniform(0.5, 1.0))

            # Step 4: Submit login form
            logger.info("[LOGIN] Submitting login form", step="login", event="submit")
            btn_loc.click()

            # Step 5: Wait for authentication state
            logger.info("[LOGIN] Waiting for authentication", step="login", event="waiting")

            # Poll state with Playwright checks every 500ms up to 25 seconds
            max_wait_seconds = 25
            start_time = time.time()

            while time.time() - start_time < max_wait_seconds:
                # A. Check for authentication success
                if self.is_authenticated(timeout_ms=1000):
                    logger.info("[LOGIN] Verifying authenticated session", step="login", event="verifying")
                    logger.info("LOGIN SUCCESS", step="login", event="success")
                    logger.info("[LOGIN] SUCCESS", step="login", event="success")
                    logger.info("[LOGIN] Authenticated LinkedIn session confirmed", step="login", event="authenticated")
                    logger.info("AUTHENTICATED SESSION VERIFIED", step="login", event="verified")
                    logger.info("[LOGIN] AUTHENTICATED SESSION VERIFIED", step="login", event="verified")
                    return True

                # B. Check for security challenge / checkpoint
                is_challenge, challenge_reason = self.detect_security_challenge()
                if is_challenge:
                    logger.warning(f"[LOGIN] Challenge detected: {challenge_reason}", step="login")
                    return self.handle_security_challenge()

                # C. Check for explicit login error (wrong password, account not found)
                has_error, error_msg = self.detect_login_error()
                if has_error:
                    logger.error(f"[LOGIN] FAILED: {error_msg}", step="login", event="credential_error")
                    logger.error("[LOGIN] Authentication could not be verified", step="login", event="failure")
                    return False

                time.sleep(0.5)

            # Timeout expired - final check
            if self.is_authenticated(timeout_ms=3000):
                logger.info("LOGIN SUCCESS", step="login", event="success")
                logger.info("[LOGIN] SUCCESS", step="login", event="success")
                logger.info("[LOGIN] Authenticated LinkedIn session confirmed", step="login", event="authenticated")
                logger.info("AUTHENTICATED SESSION VERIFIED", step="login", event="verified")
                logger.info("[LOGIN] AUTHENTICATED SESSION VERIFIED", step="login", event="verified")
                return True
            else:
                logger.error("[LOGIN] FAILED", step="login", event="failure")
                logger.error("[LOGIN] Authentication could not be verified (timed out waiting for session)", step="login", event="timeout")
                return False

        except Exception as e:
            logger.error(f"[LOGIN] FAILED: Unexpected error during login: {e}", step="login", event="error", exception=e)
            logger.error("[LOGIN] Authentication could not be verified", step="login", event="failure")
            return False
