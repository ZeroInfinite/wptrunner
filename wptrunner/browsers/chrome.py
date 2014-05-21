import os
import socket
import sys
import uuid
import traceback
import urlparse
import time
import threading

import mozprocess
from mozprofile import FirefoxProfile, Preferences
from mozprofile.permissions import ServerLocations
from mozrunner import FirefoxRunner

from .base import get_free_port, Browser, ExecutorBrowser
from ..executors.executorwebdriver import WebdriverTestharnessExecutor

here = os.path.split(__file__)[0]

__wptrunner__ = {"product": "chrome",
                 "browser": "ChromeBrowser",
                 "executor": {"testharness": "WebdriverTestharnessExecutor"},
                 "browser_kwargs": "browser_kwargs",
                 "executor_kwargs": "executor_kwargs",
                 "env_options": "env_options"}

def browser_kwargs(product, binary, prefs_root):
    return {"binary": binary}

def executor_kwargs(http_server_url, timeout_multiplier):
    from selenium import webdriver
    return {"http_server_url": http_server_url,
            "timeout_multiplier":timeout_multiplier,
            "capabilities": webdriver.DesiredCapabilities.CHROME}

def env_options():
    return {"host": "localhost"}

class ChromeBrowser(Browser):
    used_ports = set()

    def __init__(self, logger, binary):
        Browser.__init__(self, logger)
        self.binary = binary
        self.webdriver_port = get_free_port(4444, exclude=self.used_ports)
        self.used_ports.add(self.webdriver_port)
        self.proc = None
        self.cmd = None

    def start(self):
        self.cmd = [self.binary, "--port=%i" % self.webdriver_port, "--url-base=wd/url"]
        self.proc = mozprocess.ProcessHandler(self.cmd, processOutputLine=self.on_output)
        self.logger.debug("Starting chromedriver")
        self.proc.run()

    def stop(self):
        if self.proc is not None and hasattr(self.proc, "proc"):
            self.proc.kill()

    def pid(self):
        if self.proc is not None:
            return self.proc.pid

    def on_output(self, line):
        """Write a line of output from the firefox process to the log"""
        self.logger.process_output(self.pid(),
                                   line.decode("utf8"),
                                   command=" ".join(self.cmd))

    def is_alive(self):
        return self.pid() is not None

    def cleanup(self):
        self.stop()

    def executor_browser(self):
        return ExecutorBrowser, {"webdriver_port": self.webdriver_port}