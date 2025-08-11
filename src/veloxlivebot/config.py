import configparser
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Config:
    """
    Handles loading and accessing configuration from a .ini file.
    """
    def __init__(self, path='config.ini'):
        self.path = path
        self.config = configparser.ConfigParser()

        if not os.path.exists(self.path):
            logging.error(f"Configuration file not found: '{self.path}'.")
            logging.info(f"Please copy 'config.ini.example' to '{self.path}' and fill in your details.")
            # In a GUI app, we wouldn't exit, but rather show an error dialog.
            # For now, we'll proceed with an empty config, methods will return None.
            self.config = None
        else:
            self.config.read(path)

    def get(self, section, key, fallback=None):
        """Get a value from a specific section and key."""
        if self.config is None:
            return fallback
        return self.config.get(section, key, fallback=fallback)

    def get_section(self, section):
        """Get a whole section as a dictionary."""
        if self.config is None or not self.config.has_section(section):
            return {}
        return dict(self.config.items(section))

# Global config instance for easy access from other modules.
# This approach is simple, but for larger applications, dependency injection might be preferred.
config = Config()
