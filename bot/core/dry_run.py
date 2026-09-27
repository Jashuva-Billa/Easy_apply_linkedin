from bot.utils.logger import logger

class DryRun:
    def __init__(self, enabled=True):
        self.enabled = enabled
        if self.enabled:
            logger.info("DRY RUN MODE ENABLED. No applications will be submitted.", step="dry_run", event="init")

    def is_enabled(self):
        return self.enabled

    def is_dry_run(self):
        return self.enabled

    def validate_submit(self):
        """
        Returns True if not in dry run mode (submit allowed).
        Returns False if in dry run mode (submit blocked).
        """
        if self.enabled:
            logger.info("Dry run: Skipping actual submission.", step="dry_run", event="skip_submit")
            return False
        return True
