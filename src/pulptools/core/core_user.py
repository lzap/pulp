#!/usr/bin/python
#
# Pulp Repo management module
#
# Copyright (c) 2010 Red Hat, Inc.

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
#

import os
import sys

import pulptools.constants as constants
from pulptools.core.basecore import BaseCore, systemExit
from pulptools.connection import UserConnection, RestlibException
from pulptools.logutil import getLogger
from pulptools.repolib import RepoLib
from pulptools.config import Config
CFG = Config()

import gettext
_ = gettext.gettext
log = getLogger(__name__)

class user(BaseCore):
    def __init__(self):
        usage = "usage: %prog user [OPTIONS]"
        shortdesc = "user specific actions to pulp server."
        desc = ""

        BaseCore.__init__(self, "user", usage, shortdesc, desc)
        self.actions = {"create" : "Create a user",
                        "list"   : "List available users",
                        "delete" : "Delete a user",}

        self.username = None
        self.password = None
        self.name = "user"
        self.userconn = UserConnection(host=CFG.server.host or "localhost", 
                                              port=CFG.server.port or 8811)
        self.repolib = RepoLib()
        self.generate_options()

    def generate_options(self):
        
        self.action = self.validate_args()
        if self.action == "create":
            usage = "usage: %prog user create [OPTIONS]"
            BaseCore.__init__(self, "user create", usage, "", "")
            self.parser.add_option("--login", dest="login",
                           help="login to assign to user"),
            self.parser.add_option("--password", dest="password",
                           help="password for authentication")
            self.parser.add_option("--name", dest="name",
                           help="name of user for display purposes")
        if self.action == "delete":
            usage = "usage: %prog user delete [OPTIONS]"
            BaseCore.__init__(self, "user delete", usage, "", "")
            self.parser.add_option("--login", dest="login",
                           help="Login of user you wish to delete")
        if self.action == "list":
            usage = "usage: %prog user list [OPTIONS]"
            BaseCore.__init__(self, "user list", usage, "", "")


    def _do_core(self):
        if self.action == "create":
            self._create()
        if self.action == "list":
            self._list()
        if self.action == "delete":
            self._delete()

    def _create(self):
        (self.options, self.args) = self.parser.parse_args()
        if not self.options.login:
            print("login required. Try --help")
            sys.exit(0)
        if not self.options.name:
            self.options.name = ""
        if not self.options.password:
            self.options.password = ""
        try:
            user = self.userconn.create(self.options.login, self.options.password,
                                    self.options.name)
            print _(" Successfully created User [ %s ] with name [ %s ]" % \
                                     (user['login'], user["name"]))
        except RestlibException, re:
            log.error("Error: %s" % re)
            systemExit(re.code, re.msg)
        except Exception, e:
            log.error("Error: %s" % e)
            raise

    def _list(self):
        (self.options, self.args) = self.parser.parse_args()
        try:
            users = self.userconn.users()
            columns = ["login", "name"]
            if not len(users):
                print _("No users available to list")
                sys.exit(0)
            print "+-------------------------------------------+"
            print "             Available Users                 "  
            print "+-------------------------------------------+"
            for user in users:
                print constants.AVAILABLE_USERS_LIST % (user["login"], user["name"])
        except RestlibException, re:
            log.error("Error: %s" % re)
            systemExit(re.code, re.msg)
        except Exception, e:
            log.error("Error: %s" % e)
            raise


    def _delete(self):
        (self.options, self.args) = self.parser.parse_args()
        if not self.options.login:
            print("User's login required. Try --help")
            sys.exit(0)
        user = self.userconn.user(login=self.options.login)
        if not user:
            print _(" User [ %s ] does not exist" % \
                  self.options.login)
            sys.exit(-1)
        try:
            self.userconn.delete(login=self.options.login)
            print _(" Successfully deleted User [ %s ] " % self.options.login)
        except Exception, e:
            print _(" Delete operation failed on User [ %s ]. " % \
                  self.options.login)
            log.error("Error: %s" % e)
            sys.exit(-1)


