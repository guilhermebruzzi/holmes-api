#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

from holmes.validators.base import Validator
from holmes.utils import get_domain_from_url, _

REMOVE_HASH = re.compile('([#].*)$')


class LinkCrawlerValidator(Validator):
    @classmethod
    def get_links_parsed_value(cls, value):
        return {'links': ', '.join([
            '<a href="%s" target="_blank">Link #%s</a>' % (url, index)
            for index, url in enumerate(value)
        ])}

    @classmethod
    def get_violation_definitions(cls):
        return {
            'link.crawler': {
                'title': _('Crawler'),
                'description': _('Crawler'),
                'value_parser': cls.get_links_parsed_value,
                'category': _('HTTP'),
                'generic_description': _(
                    'Follows links on the page'
                )
            }
        }

    def validate(self):
        links = self.get_links()

        total_score = float(self.reviewer.page_score)
        tax = total_score * float(self.reviewer.config.PAGE_SCORE_TAX_RATE)
        available_score = total_score - tax

        number_of_links = float(len(links)) or 1.0
        link_score = available_score / number_of_links

        for url, response in links:
            domain, domain_url = get_domain_from_url(url)
            if domain in self.page_url:
                self.send_url(response.effective_url, link_score, response)

        self.flush()

    def get_links(self):
        return self.review.data['page.links']
