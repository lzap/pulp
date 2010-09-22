#!/usr/bin/python
#
# Copyright (c) 2010 Red Hat, Inc.
#
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
#
# Red Hat trademarks are not licensed under GPLv2. No permission is
# granted to use or replicate Red Hat trademarks that are incorporated
# in this software or its documentation.

# Python
import datetime
import os
import sys
import time
import unittest

# Pulp
srcdir = os.path.abspath(os.path.dirname(__file__)) + "/../../src/"

sys.path.insert(0, srcdir)
commondir = os.path.abspath(os.path.dirname(__file__)) + '/../common/'

sys.path.insert(0, commondir)

from pulp.server.api.consumer import ConsumerApi
from pulp.server.api.consumer_history import ConsumerHistoryApi
import pulp.server.api.consumer_history as consumer_history
import pulp.server.auth.auth as auth
from pulp.server.db.model import ConsumerHistoryEvent, User
from pulp.server.pexceptions import PulpException
import testutil

class TestConsumerHistoryApi(unittest.TestCase):

    def clean(self):
        self.consumer_history_api.clean()
        self.consumer_api.clean()

    def setUp(self):
        self.config = testutil.load_test_config()
        self.consumer_history_api = ConsumerHistoryApi()
        self.consumer_api = ConsumerApi()
        self.clean()

        self.user = User('admin', '12345', 'admin', 'Admin')
        auth.set_principal(self.user)

    def tearDown(self):
        self.clean()
        testutil.common_cleanup()

    def test_consumer_created(self):
        # Test
        self.consumer_history_api.consumer_created(123)
        time.sleep(.1)
        auth.set_principal(auth.SystemPrincipal())
        self.consumer_history_api.consumer_created(123)

        # Verify
        entries = self.consumer_history_api.query()
        self.assertEqual(2, len(entries))

        entry = entries[1]
        self.assertEqual(entry['consumer_id'], 123)
        self.assertEqual(entry['originator'], 'admin')
        self.assertEqual(entry['type_name'], consumer_history.TYPE_CONSUMER_CREATED)
        self.assertTrue(entry['timestamp'] is not None)

        entry = entries[0]
        self.assertEqual(entry['consumer_id'], 123)
        self.assertEqual(entry['originator'], consumer_history.ORIGINATOR_CONSUMER)
        self.assertEqual(entry['type_name'], consumer_history.TYPE_CONSUMER_CREATED)
        self.assertTrue(entry['timestamp'] is not None)

    def test_consumer_deleted(self):
        # Test
        self.consumer_history_api.consumer_deleted(123)
        time.sleep(.1)
        auth.set_principal(auth.SystemPrincipal())
        self.consumer_history_api.consumer_deleted(123)

        # Verify
        entries = self.consumer_history_api.query()
        self.assertEqual(2, len(entries))

        entry = entries[1]
        self.assertEqual(entry['consumer_id'], 123)
        self.assertEqual(entry['originator'], 'admin')
        self.assertEqual(entry['type_name'], consumer_history.TYPE_CONSUMER_DELETED)
        self.assertTrue(entry['timestamp'] is not None)

        entry = entries[0]
        self.assertEqual(entry['consumer_id'], 123)
        self.assertEqual(entry['originator'], consumer_history.ORIGINATOR_CONSUMER)
        self.assertEqual(entry['type_name'], consumer_history.TYPE_CONSUMER_DELETED)
        self.assertTrue(entry['timestamp'] is not None)

    def test_repo_bound(self):
        # Test
        self.consumer_history_api.repo_bound(123, 456)
        time.sleep(.1)
        auth.set_principal(auth.SystemPrincipal())
        self.consumer_history_api.repo_bound(123, 789)

        # Verify
        entries = self.consumer_history_api.query()
        self.assertEqual(2, len(entries))

        entry = entries[1]
        self.assertEqual(entry['consumer_id'], 123)
        self.assertEqual(entry['originator'], 'admin')
        self.assertEqual(entry['type_name'], consumer_history.TYPE_REPO_BOUND)
        self.assertTrue(entry['timestamp'] is not None)
        self.assertEqual(entry['details']['repo_id'], 456)

        entry = entries[0]
        self.assertEqual(entry['consumer_id'], 123)
        self.assertEqual(entry['originator'], consumer_history.ORIGINATOR_CONSUMER)
        self.assertEqual(entry['type_name'], consumer_history.TYPE_REPO_BOUND)
        self.assertTrue(entry['timestamp'] is not None)
        self.assertEqual(entry['details']['repo_id'], 789)

    def test_repo_unbound(self):
        # Test
        self.consumer_history_api.repo_unbound(123, 456)
        time.sleep(.1)
        auth.set_principal(auth.SystemPrincipal())
        self.consumer_history_api.repo_unbound(123, 789)

        # Verify
        entries = self.consumer_history_api.query()
        self.assertEqual(2, len(entries))

        entry = entries[1]
        self.assertEqual(entry['consumer_id'], 123)
        self.assertEqual(entry['originator'], 'admin')
        self.assertEqual(entry['type_name'], consumer_history.TYPE_REPO_UNBOUND)
        self.assertTrue(entry['timestamp'] is not None)
        self.assertEqual(entry['details']['repo_id'], 456)

        entry = entries[0]
        self.assertEqual(entry['consumer_id'], 123)
        self.assertEqual(entry['originator'], consumer_history.ORIGINATOR_CONSUMER)
        self.assertEqual(entry['type_name'], consumer_history.TYPE_REPO_UNBOUND)
        self.assertTrue(entry['timestamp'] is not None)
        self.assertEqual(entry['details']['repo_id'], 789)

    def test_packages_installed(self):
        # Test
        packages = ['foo-1.0', 'bar-2.0', 'baz-3.0']
        self.consumer_history_api.packages_installed(123, packages)
        time.sleep(.1)
        auth.set_principal(auth.SystemPrincipal())
        self.consumer_history_api.packages_installed(123, 'zombie-1.0')

        # Verify
        entries = self.consumer_history_api.query()
        self.assertEqual(2, len(entries))

        entry = entries[1]
        self.assertEqual(entry['consumer_id'], 123)
        self.assertEqual(entry['originator'], 'admin')
        self.assertEqual(entry['type_name'], consumer_history.TYPE_PACKAGE_INSTALLED)
        self.assertTrue(entry['timestamp'] is not None)
        package_list = entry['details']['package_nveras']
        self.assertTrue(len(package_list), len(packages))

        entry = entries[0]
        self.assertEqual(entry['consumer_id'], 123)
        self.assertEqual(entry['originator'], consumer_history.ORIGINATOR_CONSUMER)
        self.assertEqual(entry['type_name'], consumer_history.TYPE_PACKAGE_INSTALLED)
        self.assertTrue(entry['timestamp'] is not None)
        package_list = entry['details']['package_nveras']
        self.assertTrue(len(package_list), 1)

    def test_errata_installed(self):
        # Test
        packages = ['foo-1.0', 'bar-2.0', 'baz-3.0']
        errata_titles = ['err123', 'err456']
        self.consumer_history_api.packages_installed(123, packages, errata_titles=errata_titles)
        time.sleep(.1)
        auth.set_principal(auth.SystemPrincipal())
        self.consumer_history_api.packages_installed(123, 'zombie-1.0', errata_titles=errata_titles)

        # Verify
        entries = self.consumer_history_api.query()
        self.assertEqual(2, len(entries))

        entry = entries[1]
        self.assertEqual(entry['consumer_id'], 123)
        self.assertEqual(entry['originator'], 'admin')
        self.assertEqual(entry['type_name'], consumer_history.TYPE_ERRATA_INSTALLED)
        self.assertTrue(entry['timestamp'] is not None)
        package_list = entry['details']['package_nveras']
        self.assertTrue(len(package_list), len(packages))
        self.assertEqual(entry['details']['errata_titles'], errata_titles)

        entry = entries[0]
        self.assertEqual(entry['consumer_id'], 123)
        self.assertEqual(entry['originator'], consumer_history.ORIGINATOR_CONSUMER)
        self.assertEqual(entry['type_name'], consumer_history.TYPE_ERRATA_INSTALLED)
        self.assertTrue(entry['timestamp'] is not None)
        package_list = entry['details']['package_nveras']
        self.assertTrue(len(package_list), 1)
        self.assertEqual(entry['details']['errata_titles'], errata_titles)
        
    def test_packages_removed(self):
        # Test
        packages = ['foo-1.0', 'bar-2.0', 'baz-3.0']
        self.consumer_history_api.packages_removed(123, packages)
        time.sleep(.1)
        auth.set_principal(auth.SystemPrincipal())
        self.consumer_history_api.packages_removed(123, 'zombie-1.0')

        # Verify
        entries = self.consumer_history_api.query()
        self.assertEqual(2, len(entries))

        entry = entries[1]
        self.assertEqual(entry['consumer_id'], 123)
        self.assertEqual(entry['originator'], 'admin')
        self.assertEqual(entry['type_name'], consumer_history.TYPE_PACKAGE_UNINSTALLED)
        self.assertTrue(entry['timestamp'] is not None)
        package_list = entry['details']['package_nveras']
        self.assertTrue(len(package_list), len(packages))

        entry = entries[0]
        self.assertEqual(entry['consumer_id'], 123)
        self.assertEqual(entry['originator'], consumer_history.ORIGINATOR_CONSUMER)
        self.assertEqual(entry['type_name'], consumer_history.TYPE_PACKAGE_UNINSTALLED)
        self.assertTrue(entry['timestamp'] is not None)
        package_list = entry['details']['package_nveras']
        self.assertTrue(len(package_list), 1)

    def test_profile_updated(self):
        # Test
        profile = {'libtasn1-devel-2.4-2.fc13.x86_64':
                       {'OS': 'linux',
                        'Platform': 'x86_64-redhat-linux-gnu',
                        'Size': 56009L,
                        'URL': 'http://www.gnu.org/software/libtasn1/'
                        ,
                        'Vendor': 'Fedora Project',
                        'arch': 'x86_64',
                        'description': 'This is the ASN.1 library used in GNUTLS.'
                        ,
                        'epoch': '',
                        'group': 'Development/Libraries',
                        'installtime': 1276010433L,
                        'name': 'libtasn1-devel',
                        'release': '2.fc13',
                        'summary': 'Files for development of applications which will use libtasn1'
                        ,
                        'version': '2.4'}}

        self.consumer_history_api.profile_updated(123, profile)
        time.sleep(.1)
        auth.set_principal(auth.SystemPrincipal())
        self.consumer_history_api.profile_updated(123, profile)

        # Verify
        entries = self.consumer_history_api.query()
        self.assertEqual(2, len(entries))

        entry = entries[1]
        self.assertEqual(entry['consumer_id'], 123)
        self.assertEqual(entry['originator'], 'admin')
        self.assertEqual(entry['type_name'], consumer_history.TYPE_PROFILE_CHANGED)
        self.assertTrue(entry['timestamp'] is not None)
        self.assertTrue(entry['details']['package_profile'] is not None)
        self.assertEqual(profile, entry['details']['package_profile'])

        entry = entries[0]
        self.assertEqual(entry['consumer_id'], 123)
        self.assertEqual(entry['originator'], consumer_history.ORIGINATOR_CONSUMER)
        self.assertEqual(entry['type_name'], consumer_history.TYPE_PROFILE_CHANGED)
        self.assertTrue(entry['timestamp'] is not None)
        self.assertTrue(entry['details']['package_profile'] is not None)
        self.assertEqual(profile, entry['details']['package_profile'])

    def test_types(self):
        # Test
        types = self.consumer_history_api.event_types()

        # Verify
        self.assertTrue(types is not None)
        self.assertTrue(len(types) > 0)

    def test_query_invalid_type(self):
        # Test
        self.assertRaises(PulpException, self.consumer_history_api.query, event_type='foo')

    def test_query_invalid_sort(self):
        # Test
        self.assertRaises(PulpException, self.consumer_history_api.query, sort='foo')

    def test_query_invalid_consumer_id(self):
        # Test
        self.assertRaises(PulpException, self.consumer_history_api.query, consumer_id='foo')

    def test_query_none(self):
        # Test
        results = self.consumer_history_api.query()

        # Verify
        self.assertTrue(results is not None)
        self.assertEqual(len(results), 0)

    def test_query_all(self):
        # Setup
        self._populate_for_queries()

        # Test
        results = self.consumer_history_api.query()

        # Verify
        self.assertEqual(len(results), 7)

    def test_query_by_consumer(self):
        # Setup
        self._populate_for_queries()

        # Test
        results1 = self.consumer_history_api.query(consumer_id=1)
        results2 = self.consumer_history_api.query(consumer_id=2)

        # Verify
        self.assertEqual(len(results1), 3)
        for entry in results1:
            self.assertEqual(entry['consumer_id'], 1)

        self.assertEqual(len(results2), 4)
        for entry in results2:
            self.assertEqual(entry['consumer_id'], 2)

    def test_query_by_type(self):
        # Setup
        self._populate_for_queries()

        # Test
        results_created = self.consumer_history_api.query(event_type=consumer_history.TYPE_CONSUMER_CREATED)
        results_bound = self.consumer_history_api.query(event_type=consumer_history.TYPE_REPO_BOUND)

        # Verify
        self.assertEqual(len(results_created), 2)
        for entry in results_created:
            self.assertEqual(entry['type_name'], consumer_history.TYPE_CONSUMER_CREATED)

        self.assertEqual(len(results_bound), 5)
        for entry in results_bound:
            self.assertEqual(entry['type_name'], consumer_history.TYPE_REPO_BOUND)

    def test_query_by_consumer_and_type(self):
        # Setup
        self._populate_for_queries()

        # Test
        results = self.consumer_history_api.query(consumer_id=1, event_type=consumer_history.TYPE_REPO_BOUND)

        # Verify
        self.assertEqual(len(results), 2)

    def test_query_with_limit(self):
        # Setup
        self._populate_for_queries()

        # Test
        results = self.consumer_history_api.query(limit=3)

        # Verify
        self.assertEqual(len(results), 3)

    def test_query_with_params_and_limit(self):
        # Setup
        self._populate_for_queries()

        # Test
        results = self.consumer_history_api.query(consumer_id=2, limit=2)

        # Verify
        self.assertEqual(len(results), 2)

        for entry in results:
            self.assertEqual(entry['consumer_id'], 2)

    def test_query_with_negative_limit(self):
        # Setup
        self._populate_for_queries()

        # Test
        self.assertRaises(PulpException, self.consumer_history_api.query, limit=0)
        self.assertRaises(PulpException, self.consumer_history_api.query, limit= -1)

    def test_query_sort_directions(self):
        # Setup
        e1 = ConsumerHistoryEvent(123, 'admin', consumer_history.TYPE_CONSUMER_CREATED, None)
        self.consumer_history_api.objectdb.insert(e1, safe=True)

        e2 = ConsumerHistoryEvent(123, 'admin', consumer_history.TYPE_CONSUMER_DELETED, None)
        e2.timestamp = datetime.datetime.now() + datetime.timedelta(days=1)
        self.consumer_history_api.objectdb.insert(e2, safe=True)

        # Test
        ascending = self.consumer_history_api.query(sort='ascending')
        descending = self.consumer_history_api.query(sort='descending')
        default_sort = self.consumer_history_api.query()

        # Verify
        self.assertEqual(len(ascending), 2)
        self.assertEqual(len(descending), 2)
        self.assertEqual(len(default_sort), 2)

        self.assertEqual(ascending[0]['type_name'], consumer_history.TYPE_CONSUMER_CREATED)
        self.assertEqual(descending[0]['type_name'], consumer_history.TYPE_CONSUMER_DELETED)
        self.assertEqual(default_sort[0]['type_name'], consumer_history.TYPE_CONSUMER_DELETED)

    def test_query_start_range(self):
        # Setup
        self._populate_for_date_queries()

        # Test
        start_date = datetime.datetime(2000, 5, 1)
        results = self.consumer_history_api.query(start_date=start_date)

        # Verify
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['type_name'], consumer_history.TYPE_REPO_UNBOUND)
        self.assertEqual(results[1]['type_name'], consumer_history.TYPE_REPO_BOUND)

    def test_query_end_range(self):
        # Setup
        self._populate_for_date_queries()

        # Test
        end_date = datetime.datetime(2000, 5, 1)
        results = self.consumer_history_api.query(end_date=end_date)

        # Verify
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['type_name'], consumer_history.TYPE_CONSUMER_DELETED)
        self.assertEqual(results[1]['type_name'], consumer_history.TYPE_CONSUMER_CREATED)

    def test_query_start_end_range(self):
        # Setup
        self._populate_for_date_queries()

        # Test
        start_date = datetime.datetime(2000, 3, 1)
        end_date = datetime.datetime(2000, 7, 1)
        results = self.consumer_history_api.query(start_date=start_date, end_date=end_date)

        # Verify
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['type_name'], consumer_history.TYPE_REPO_BOUND)
        self.assertEqual(results[1]['type_name'], consumer_history.TYPE_CONSUMER_DELETED)

    def test_cull_history(self):
        # Setup
        self._populate_for_cull()
        self.assertEqual(5, len(self.consumer_history_api.query()))

        # Test
        self.consumer_history_api.cull_history(datetime.timedelta(days=100))
        self.assertEqual(4, len(self.consumer_history_api.query()))

        self.consumer_history_api.cull_history(datetime.timedelta(days=40))
        self.assertEqual(2, len(self.consumer_history_api.query()))

        self.consumer_history_api.cull_history(datetime.timedelta(days=1))
        self.assertEqual(1, len(self.consumer_history_api.query()))

    def _populate_for_queries(self):
        '''
        Populates the history store with a number of entries to help test the query
        functionality.
        '''

        # Create consumers
        self.consumer_api.create(1, 'Test consumer 1')
        self.consumer_api.create(2, 'Test consumer 1')

        # Create history entries
        self.consumer_history_api.repo_bound(1, 0000)
        self.consumer_history_api.repo_bound(1, 1111)
        self.consumer_history_api.repo_bound(2, 1111)
        self.consumer_history_api.repo_bound(2, 2222)
        self.consumer_history_api.repo_bound(2, 3333)

    def _populate_for_date_queries(self):
        '''
        Populates the history with events scattered over the course of a year, suitable for
        date range tests.
        '''

        e1 = ConsumerHistoryEvent(123, 'admin', consumer_history.TYPE_CONSUMER_CREATED, None)
        e2 = ConsumerHistoryEvent(123, 'admin', consumer_history.TYPE_CONSUMER_DELETED, None)
        e3 = ConsumerHistoryEvent(123, 'admin', consumer_history.TYPE_REPO_BOUND, None)
        e4 = ConsumerHistoryEvent(123, 'admin', consumer_history.TYPE_REPO_UNBOUND, None)

        e1.timestamp = datetime.datetime(2000, 2, 1)
        e2.timestamp = datetime.datetime(2000, 4, 1)
        e3.timestamp = datetime.datetime(2000, 6, 1)
        e4.timestamp = datetime.datetime(2000, 10, 1)

        self.consumer_history_api.objectdb.insert(e1)
        self.consumer_history_api.objectdb.insert(e2)
        self.consumer_history_api.objectdb.insert(e3)
        self.consumer_history_api.objectdb.insert(e4)

    def _populate_for_cull(self):
        '''
        Populates the history with events created in terms of today, suitable for
        testing the cull functionality.
        '''

        e1 = ConsumerHistoryEvent(123, 'admin', consumer_history.TYPE_CONSUMER_CREATED, None)
        e2 = ConsumerHistoryEvent(123, 'admin', consumer_history.TYPE_CONSUMER_CREATED, None)
        e3 = ConsumerHistoryEvent(123, 'admin', consumer_history.TYPE_CONSUMER_CREATED, None)
        e4 = ConsumerHistoryEvent(123, 'admin', consumer_history.TYPE_CONSUMER_CREATED, None)
        e5 = ConsumerHistoryEvent(123, 'admin', consumer_history.TYPE_CONSUMER_CREATED, None)

        now = datetime.datetime.now()
        days_ago_30 = datetime.timedelta(days=30)
        days_ago_60 = datetime.timedelta(days=60)
        days_ago_90 = datetime.timedelta(days=90)
        days_ago_120 = datetime.timedelta(days=120)

        e1.timestamp = now
        e2.timestamp = now - days_ago_30
        e3.timestamp = now - days_ago_60
        e4.timestamp = now - days_ago_90
        e5.timestamp = now - days_ago_120

        self.consumer_history_api.objectdb.insert(e1)
        self.consumer_history_api.objectdb.insert(e2)
        self.consumer_history_api.objectdb.insert(e3)
        self.consumer_history_api.objectdb.insert(e4)
        self.consumer_history_api.objectdb.insert(e5)
