#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright © 2010 Red Hat, Inc.
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

__author__ = 'Jason L Connor <jconnor@redhat.com>'

import web

from juicer.controllers.base import JSONController
from pulp.api.repo import RepoApi

# web.py application ----------------------------------------------------------

URLS = (
    '/$', 'Repositories',
    '/([^/]+)/$', 'Repository',
    '/([^/]+)/sync/$', 'Sync',
    '/([^/]+)/list/$', 'Packages',
)

application = web.application(URLS, globals())

# repository api --------------------------------------------------------------

# TODO: jdobies, Jun 1: Wire this into juicer's configuration loading
API = RepoApi(None)

# controllers -----------------------------------------------------------------

class Repositories(JSONController):
    
    def GET(self):
        """
        @return: a list of all available repositories
        """
        return self.output(API.repositories())
    
    def POST(self):
        """
        @return: repository meta data on successful creation of repository
        """
        repo_data = self.input()
        repo = API.create(repo_data['id'],
                          repo_data['name'],
                          repo_data['arch'],
                          repo_data['feed'])
        return self.output(repo)
    
    
class Repository(JSONController):
    
    def DELETE(self, id):
        """
        @param id: repository id
        @return: True on successful deletion of repository
        """
        API.delete(id)
        return self.output(True)

    def GET(self, id):
        """
        @param id: repository id
        @return: repository meta data
        """
        return self.output(API.repository(id))
    
    def POST(self, id):
        """
        @return: True on successful update of repository meta data
        """
        repo_data = self.input()
        repo_data['id'] = id
        API.update(repo_data)
        return self.output(True)
    
    
class Sync(JSONController):
    
    def GET(self, id):
        """
        @param id: repository id
        @return: True on successful sync of repository from feed
        """
        API.sync(id)
        return self.output(True)
       
  
class Packages(JSONController):
    
    def GET(self, id):
        """
        @param id: repository id
        @return: list of all packages available in corresponding repository
        """
        return self.output(API.packages(id))
