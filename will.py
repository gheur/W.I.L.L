#Builtin imports
import logging
import logging.handlers
import json
import sys
import os
import datetime

#Internal imports
from userspace import userspace
from core import core
from API import API
from exceptions import *

version = "4.0-alpha+02"
author = "Will Beddow"

class will:
    def configure_logging(self):
        global log
        #Logging presets.
        #Since they won't change in the code, no reason to make them keyword args
        log_data = {
            "filename": "will.log",
            "filemode": "w",
            "format": "%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
            "maxBytes": 10000000,
            "backupCount": 5,
            "consoleLevel": logging.INFO
        }
        if self.configuration_data["debug"]:
            log_data.update({"level": logging.DEBUG})
        else:
            log_data.update({"level": logging.INFO})
        #If relevant, override presets with user preferences
        #Define logging settings in the configuration by logging_{mysetting}: setting_value
        #Example: logging_filename: "will.log"
        for conf_key, conf_val in self.configuration_data.items():
            if conf_key.startswith("logging_"):
                setting_name = conf_key.split("logging_")[1]
                if setting_name in log_data.keys():
                    log_data[setting_name] = conf_val
                else:
                    raise ConfigurationError("Logging setting {0} either does not exist or is not supported. "
                                             "The supported logging settings are {1}".format(
                        setting_name, log_data.keys()
                    ))
        # Do the actual configuration
        # The handler for the logging files
        fh = logging.handlers.RotatingFileHandler(
            log_data["filename"],
            maxBytes=log_data["maxBytes"],
            backupCount=log_data["backupCount"])
        # The handler for console messages
        ch = logging.StreamHandler()
        ch.setLevel(log_data["consoleLevel"])
        # Pull all of the handlers and settings into a configuration
        logging.basicConfig(
            filename=log_data["filename"],
            filemode=log_data["filemode"],
            format=log_data["format"],
            level=log_data["level"])
        log = logging.getLogger()
        log.addHandler(ch)
        log.addHandler(fh)
        # Silence noisy loggers from external libraries
        logging.getLogger('neo4j').setLevel(logging.CRITICAL)
        logging.getLogger('neo4j.bolt').setLevel(logging.CRITICAL)

    def load_modules(self):
        log.info("Loading core...")
        self.core = core(configuration_data=self.configuration_data)
        log.info("Loading userspace...")
        self.userspace = userspace(configuration_data=self.configuration_data)
        log.info("Loading API...")
        self.API = API(configuration_data=self.configuration_data)

    def __init__(self, conf_file="will.conf", intro_file="will_logo.txt"):
        self.start_time = datetime.datetime.now()
        if os.path.isfile(conf_file):
            conf_data = open(conf_file)
            try:
                configuration_data = json.load(conf_data)
                #Validation of configuration_data
                required_attrs = {
                    "db": dict,
                    "debug": bool
                }
                error_key, error_type = (None, None)
                #Check the type of the configuration data
                if type(configuration_data) == dict:
                    try:
                        for attr, attr_type in required_attrs.items():
                            error_key = attr
                            error_type = attr_type
                            assert error_key in configuration_data.keys()
                            assert type(configuration_data[attr]) == attr_type
                    except AssertionError:
                        raise ConfigurationError("Incorrect configuration. Configuration key {0} must be of type "
                                                     "{1}".format(
                            error_key, error_type
                        ))
                    #Configuration data fully validated
                    self.configuration_data = configuration_data
                    #Set the configuration data for userspace too
                    userspace.configuration_data = self.configuration_data
                    #Configure logging
                    self.configure_logging()
                    if os.path.isfile(intro_file):
                        intro = open(intro_file).read()
                        logo_screen = intro.format(version_number=version)
                        log.info(logo_screen)
                    else:
                        log.warning("Introduction file, not found.")
                    #Load the modules with timing and a visual display
                    log.info("Loading W.I.L.L modules...")
                    self.load_modules()
                else:
                    raise ConfigurationError("Configuration data isn't a dictionary. Please check your configuration.")
            except json.JSONDecodeError:
                raise ConfigurationError("Couldn't decode configuration data. Please make sure that your configuration "
                                         "file is in JSON format")
        else:
            raise ConfigurationError("Couldn't find configuration file {0}.".format(conf_file))

if __name__ == "__main__":
    will()