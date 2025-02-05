"""
Module: config.py
Description: This module loads configuration from config.yaml and exposes it as a Python dictionary (config).
Logs any errors encountered during configuration loading.
"""
import os
import yaml
from etl.utils import Utils

logger = Utils.get_logger("config")

# Determine the path to the YAML configuration file.
_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.yaml")

try:
    with open(_CONFIG_FILE, "r") as f:
        config = yaml.safe_load(f)
except Exception as e:
    logger.error("Failed to load config file {}: {}".format(_CONFIG_FILE, e))
    raise 