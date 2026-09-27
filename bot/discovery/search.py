import time
import random
import logging
from bs4 import BeautifulSoup

from bot.application.workflow import Workflow
from bot.discovery.job_filter import JobFilter, LocationCategory
from bot.utils.delays import sleep_random
from bot.utils.selectors import LOCATORS, get_locator
from bot.utils.logger import logger
from bot.utils.retry import retry
from bot.utils.stale_guard import safe_action
from bot.discovery.job_identity import JobIdentity
from bot.discovery.scroll_tracker import ScrollTracker
from bot.utils.human_interaction import HumanInteraction
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError


class Search:
    def __init__(self, page: Page, workflow: Workflow, blacklist=None, experience_level=None, phone_number=None, filter_config=None):
        self.page = page
        self.workflow = workflow
        self.blacklist = blacklist or []
        self.experience_level = experience_level or []
        self.locator = LOCATORS
        self.MAX_SEARCH_TIME = 60 * 60
        self.phone_number = phone_number
        self.job_filter = JobFilter(filter_config or {})

    def start_apply(self, positions, locations):
        combos = []
        while len(combos) < len(positions) * len(locations):
            position = positions[random.randint(0, len(positions) - 1)]
            location = locations[random.randint(0, len(locations) - 1)]
            combo = (position, location)
            if combo not in combos:
                combos.append(combo)
                logger.info(f"Applying to {position}: {location}", step="search_init")
                location_param = "&location=" + location

                self.applications_loop(position, location_param)
            if len(combos) > 500:
                break

    def applications_loop(self, position, location):
        jobs_per_page = 0
        start_time = time.time()
        scroll_tracker = ScrollTracker(self.page)
        human = HumanInteraction(self.page)

        logger.info("Looking for jobs.. Please wait..", step="job_search", event="start")

        self.next_jobs_page(position, location, jobs_per_page)
        logger.info("Looking for jobs.. Please wait..", step="job_search", event="page_loaded")

        while time.time() - start_time < self.MAX_SEARCH_TIME:
            try:
                logger.info(f"{(self.MAX_SEARCH_TIME - (time.time() - start_time)) // 60} minutes left in this search", 
                           step="job_search", event="timer")
                sleep_random()

                # Check if search results container is present
                search_selector = get_locator("search")
                if self.is_present(search_selector):
                    scrollresults = self.page.locator(search_selector).first
                    
                    # Get current scroll height
                    current_height = scrollresults.evaluate("el => el.scrollHeight")
                    
                    # Scroll down with human-like behavior
                    for i in range(300, int(current_height), 300):
                        scrollresults.evaluate(f"el => el.scrollTo(0, {i})")
                        time.sleep(random.uniform(0.1, 0.3))

                    if not scroll_tracker.update_scroll(current_height):
                        if scroll_tracker.should_stop():
                            logger.warning("Scroll limits reached, moving to next page", step="job_search", event="scroll_stop")
                            jobs_per_page = self.next_jobs_page(position, location, jobs_per_page)
                            continue
                
                
                # Extract jobs
                links_selector = get_locator("links")
                logger.debug(f"Using job card selector: {links_selector}", step="job_search")
                
                if self.is_present(links_selector):
                    # Wait a bit for job cards to fully load
                    time.sleep(random.uniform(1, 2))
                    
                    links = self.page.locator(links_selector).all()
                    logger.info(f"Found {len(links)} job cards on page", step="job_search", event="cards_found")
                    
                    if len(links) == 0:
                        # Try fallback selector
                        fallback_selector = get_locator("links", use_fallback=True)
                        logger.warning(f"No cards with primary selector, trying fallback: {fallback_selector}", step="job_search")
                        if fallback_selector:
                            links = self.page.locator(fallback_selector).all()
                            logger.info(f"Fallback found {len(links)} job cards", step="job_search", event="cards_found_fallback")
                    
                    for i, link in enumerate(links):
                        try:
                            # Check if element is visible before processing
                            if not link.is_visible():
                                continue
                            
                            job_id = JobIdentity.extract_job_id(link)
                            if job_id and not scroll_tracker.is_processed(job_id):
                                try:
                                    link_text = link.text_content(timeout=3000)
                                except:
                                    link_text = ""
                                
                                if 'Applied' not in link_text:
                                    if link_text not in self.blacklist:
                                        logger.info(f"Found new job: {job_id}", step="job_search", event="found_job")
                                        
                                        # Click the job card to load the preview panel
                                        try:
                                            link.click(timeout=5000, force=False)
                                            logger.debug(f"Clicked job card {job_id} to show preview", step="job_search")
                                            time.sleep(1.5)  # Wait for preview panel to load
                                        except Exception as click_err:
                                            logger.warning(f"Could not click job card: {click_err}", step="job_search")

                                        # Extract preview details for AI/ML evaluation
                                        preview_title = ""
                                        preview_location = ""
                                        preview_workplace = ""
                                        preview_description = ""
                                        
                                        try:
                                            title_el = self.page.locator(".job-details-jobs-unified-top-card__job-title, h1, .jobs-unified-top-card__job-title").first
                                            if title_el.is_visible(timeout=1200):
                                                preview_title = title_el.text_content().strip()
                                        except Exception:
                                            pass
                                            
                                        if not preview_title:
                                            preview_title = link_text.split("\n")[0].strip() if link_text else ""
                                            
                                        try:
                                            loc_el = self.page.locator(".job-details-jobs-unified-top-card__primary-description, .jobs-unified-top-card__bullet, .job-details-jobs-unified-top-card__bullet").first
                                            if loc_el.is_visible(timeout=1000):
                                                preview_location = loc_el.text_content().strip()
                                        except Exception:
                                            pass
                                            
                                        try:
                                            workplace_el = self.page.locator(".job-details-jobs-unified-top-card__workplace-type, span.jobs-unified-top-card__workplace-type").first
                                            if workplace_el.is_visible(timeout=1000):
                                                preview_workplace = workplace_el.text_content().strip()
                                        except Exception:
                                            pass
                                            
                                        try:
                                            desc_el = self.page.locator("#job-details, .jobs-description__content, .jobs-box__html-content").first
                                            if desc_el.is_visible(timeout=1500):
                                                preview_description = desc_el.text_content()[:3000].strip()
                                        except Exception:
                                            pass

                                        # Run AI/ML & Location Eligibility Evaluation
                                        evaluation = self.job_filter.evaluate_job(
                                            title=preview_title or link_text,
                                            location_text=preview_location or location,
                                            description_text=preview_description,
                                            workplace_type=preview_workplace
                                        )

                                        if not evaluation["is_eligible"]:
                                            logger.info(
                                                f"Filtered out job {job_id} ('{preview_title}'): {'; '.join(evaluation['reasons'][:2])} "
                                                f"(Score: {evaluation['relevance_score']}/100, Loc: {evaluation['location_category']})",
                                                step="job_filter",
                                                event="job_skipped"
                                            )
                                            scroll_tracker.add_job(job_id)
                                            continue

                                        logger.info(
                                            f"🎯 Matching AI/ML Job! '{preview_title}' | Score: {evaluation['relevance_score']}/100 | "
                                            f"Category: {evaluation['location_category']}",
                                            step="job_filter",
                                            event="job_matched"
                                        )

                                        self.workflow.apply_to_job(job_id, self.phone_number, filter_result=evaluation)
                                        scroll_tracker.add_job(job_id)
                                    else:
                                        logger.info(f"Skipping blacklisted job: {job_id}", step="job_search", event="blacklisted")
                                        scroll_tracker.add_job(job_id)
                                else:
                                    logger.debug(f"Already applied to job: {job_id}", step="job_search", event="already_applied")
                                    scroll_tracker.add_job(job_id)
                            elif job_id:
                                logger.debug(f"Job {job_id} already processed", step="job_search", event="duplicate")
                        except Exception as e:
                            logger.warning(f"Error processing job card {i}: {e}", step="job_search", event="card_error")
                            continue
                    
                    if scroll_tracker.should_stop():
                        jobs_per_page = self.next_jobs_page(position, location, jobs_per_page)

                else:
                    logger.warning(f"No job cards found with selector: {links_selector}", step="job_search", event="no_cards")
                    # Debug: print what elements are on the page
                    try:
                        all_divs = self.page.locator("div").count()
                        all_lis = self.page.locator("li").count()
                        logger.debug(f"Page has {all_divs} divs and {all_lis} list items", step="job_search")
                    except:
                        pass
                    jobs_per_page = self.next_jobs_page(position, location, jobs_per_page)

            except Exception as e:
                logger.error(f"Search loop error: {e}", step="job_search", event="error", exception=e)
                break

    @retry(max_attempts=3, delay=1)
    def next_jobs_page(self, position, location, jobs_per_page):
        experience_level_str = ",".join(map(str, self.experience_level)) if self.experience_level else ""
        experience_level_param = f"&f_E={experience_level_str}" if experience_level_str else ""
        
        # Correct Easy Apply filter: f_AL=true
        url = ("https://www.linkedin.com/jobs/search/?f_AL=true&keywords=" +
               position + location + "&start=" + str(jobs_per_page) + experience_level_param)
        
        logger.info(f"Loading jobs page: {url[:100]}...", step="next_jobs_page")
        self.page.goto(url, wait_until="domcontentloaded")
        self.load_page()
        return jobs_per_page + 25

    @retry(max_attempts=3, delay=1)
    def load_page(self, sleep=1):
        """
        Scroll the page to load all content
        """
        # Wait for initial page load
        time.sleep(2)
        
        scroll_page = 0
        while scroll_page < 4000:
            self.page.evaluate(f"window.scrollTo(0, {scroll_page})")
            scroll_page += 500
            time.sleep(sleep)

        if sleep != 1:
            self.page.evaluate("window.scrollTo(0, 0)")
            time.sleep(sleep)
        
        # Extra wait for job cards to render
        time.sleep(2)

        return BeautifulSoup(self.page.content(), "lxml")

    def get_elements(self, type) -> list:
        """
        Get elements by type from locators
        """
        selector = get_locator(type)
        if selector and self.is_present(selector):
            return self.page.locator(selector).all()
        return []

    def is_present(self, selector):
        """
        Check if element is present on page
        """
        try:
            return self.page.locator(selector).count() > 0
        except:
            return False
