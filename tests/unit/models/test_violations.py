#!/usr/bin/python
# -*- coding: utf-8 -*-

from preggy import expect

from holmes.models import Violation, Key
from holmes.utils import _
from tests.unit.base import ApiTestCase
from tests.fixtures import ViolationFactory, KeyFactory, DomainFactory


class TestViolations(ApiTestCase):
    def test_can_create_violation(self):
        violation = ViolationFactory.create(
            key=Key(name='some.random.fact'), value='value', points=1203
        )

        loaded_violation = self.db.query(Violation).get(violation.id)

        expect(loaded_violation.value).to_equal('value')
        expect(loaded_violation.key.name).to_equal('some.random.fact')
        expect(loaded_violation.points).to_equal(1203)
        expect(str(loaded_violation)).to_be_like('%s: %s' % (
            violation.key.name,
            violation.value,
        ))

    def test_to_dict(self):
        violation = ViolationFactory.create(
            key=Key(name='some.random.fact'),
            value='value',
            points=1203,
        )

        violations_definitions = {'some.random.fact': {}}

        expect(violation.to_dict(violations_definitions, _)).to_be_like({
            'key': 'some.random.fact',
            'description': 'value',
            'title': 'undefined',
            'points': 1203,
            'category': 'undefined'
        })

    def test_can_get_most_common_violations_names(self):
        for i in range(3):
            key = KeyFactory.create(name='some.random.fact.%s' % i)
            for j in range(i):
                ViolationFactory.create(key=key)

        violations = Violation.get_most_common_violations_names(self.db)

        expect(violations).to_be_like([('some.random.fact.1', 1), ('some.random.fact.2', 2)])

    def test_can_get_by_key_id_group_by_domain(self):
        domains = [DomainFactory.create(name='g%d.com' % i) for i in xrange(2)]
        keys = [KeyFactory.create(name='random.fact.%s' % i) for i in xrange(3)]

        for i in range(3):
            for j in range(i + 1):
                ViolationFactory.create(
                    key=keys[i],
                    domain=domains[j % 2]
                )

        violations = Violation.get_by_key_id_group_by_domain(self.db, keys[1].id)
        expect(violations).to_be_like([('g0.com', 1), ('g1.com', 1)])

        violations = Violation.get_by_key_id_group_by_domain(self.db, keys[2].id)
        expect(violations).to_be_like([('g0.com', 2), ('g1.com', 1)])

    def test_can_get_group_by_value_for_key(self):
        keys = [KeyFactory.create(name='random.key.%s' % i) for i in xrange(3)]

        for i in range(3):
            for j in range(i + 1):
                ViolationFactory.create(
                    key=keys[i],
                    value='random.value.%d' % i
                )

        violations = Violation.get_group_by_value_for_key(self.db, keys[0].name)
        expect(violations).to_be_like([('random.value.0', 1)])

        violations = Violation.get_group_by_value_for_key(self.db, keys[1].name)
        expect(violations).to_be_like([('random.value.1', 2)])

        violations = Violation.get_group_by_value_for_key(self.db, keys[2].name)
        expect(violations).to_be_like([('random.value.2', 3)])
