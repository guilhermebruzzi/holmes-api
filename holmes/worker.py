#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
import logging
from uuid import uuid4
from os.path import abspath, dirname, join
from ujson import loads

import requests
from requests.exceptions import ConnectionError
from derpconf.config import verify_config
from optparse import OptionParser

from holmes.config import Config


class HolmesWorker(object):

    def __init__(self, arguments=[]):
        self.root_path = abspath(join(dirname(__file__), ".."))

        self.uuid = uuid4().hex

        self.working = True
        self.config = None
        self.validators = set()

        self._parse_opt(arguments)
        self._load_config(self.options.verbose == 3)
        self._config_logging()

    def run(self):
        try:
            while self.working:
                self._do_work()
                time.sleep(self.config.WORKER_SLEEP_TIME)
        except KeyboardInterrupt:
            self.working = False

    def stop_work(self):
        self.working = False

    def _do_work(self):
        if self._ping_api():
            job = self._load_next_job()
            if job:
                self._start_job(job['review'])
                #Reviewer(job=[review_uuid, page_uuid, page_url], url_base_api)
                self._complete_job(job['review'])

    def _load_validators(self):
        return self.config.VALIDATORS

    def _ping_api(self):
        try:
            requests.post("%s/worker/%s/ping" % (self.config.HOLMES_API_URL, self.uuid), data={"worker_uuid": self.uuid})
            return True
        except ConnectionError:
            logging.fatal("Fail to ping API [%s]. Stopping Worker." % self.config.HOLMES_API_URL)
            self.working = False
            return False

    def _load_next_job(self):
        try:
            response = requests.post("%s/next" % self.config.HOLMES_API_URL, data={})
            if response and response.text:
                return loads(response.text)
        except ConnectionError:
            logging.fatal("Fail to get next review from [%s]. Stopping Worker." % self.config.HOLMES_API_URL)
            self.working = False

    def _start_job(self, review_uuid):
        if not review_uuid:
            return False

        try:
            response = requests.post("%s/worker/%s/start/%s" %
                                    (self.config.HOLMES_API_URL, self.uuid, review_uuid))
            return ("OK" == response.text)

        except ConnectionError:
            logging.error("Fail to start review.")

    def _complete_job(self, review_uuid):
        if not review_uuid:
            return False

        try:
            response = requests.post("%s/worker/%s/complete/%s" %
                                    (self.config.HOLMES_API_URL, self.uuid, review_uuid))
            return ("OK" == response.text)

        except ConnectionError:
            logging.error("Fail to start review.")

    def _parse_opt(self, arguments):
        parser = OptionParser()
        parser.add_option('-c', '--conf', dest='conf', default=join(self.root_path, 'holmes/config/local.conf'),
                          help='Configuration file to use for the server.')
        parser.add_option('--verbose', '-v', action='count', default=0,
                          help='Log level: v=warning, vv=info, vvv=debug.')

        self.options, self.arguments = parser.parse_args(arguments)

    def _load_config(self, verify=False):
        if verify:
            verify_config(self.options.conf)
        self.config = Config.load(self.options.conf)

    def _config_logging(self):
        LOGS = {
            0: 'error',
            1: 'warning',
            2: 'info',
            3: 'debug'
        }

        if self.options.verbose:
            log_level = LOGS[self.options.verbose].upper()
        else:
            log_level = self.config.LOG_LEVEL.upper()

        logging.basicConfig(
            level=log_level,
            format=self.config.LOG_FORMAT,
            datefmt=self.config.LOG_DATE_FORMAT
        )

        return log_level


def main():
    worker = HolmesWorker(sys.argv[1:])
    worker.run()

if __name__ == '__main__':
    main()
