# __init__.py
#
# Copyright (C) 2007 Carlos Garcia Campos <carlosgc@gsyc.escet.urjc.es>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from repositoryhandler.backends.watchers import *

DEBUG = False

__all__ = [
        'Repository',
        'create_repository',
        'register_backend', 
        'create_repository_from_path'
]

class RepositoryUnknownError (Exception):
    '''Unkown repository type'''

class RepositoryInvalidWorkingCopy (Exception):
    '''Invalid Working Copy directory'''

class RepositoryInvalidBranch (Exception):
    '''Invalid Branch'''
    
class InvalidWatch (Exception):
    '''Invalid watch type'''

class Repository:
    '''Abstract class representing a file repository'''

    def __init__ (self, uri, type):
        self.uri = uri
        self.type = type
        self.watchers = {}

    def get_uri (self):
        return self.uri
        
    def get_type (self):
        return self.type
        
    def checkout (self, uri, rootdir, newdir = None, branch = None, rev = None):
        '''Checkout uri to the given directory'''
        raise NotImplementedError

    def update (self, uri, rev = None):
        '''Update a working copy uri'''
        raise NotImplementedError

    def log (self, uri, rev = None, files = None):
        '''Return log for working copy uri'''
        raise NotImplementedError

    def diff (self, uri, branch = None, revs = None, files = None):
        '''Return diff for files in working copy betweeen revisions'''
        raise NotImplementedError

    def get_modules (self):
        '''Return the list of modules of the repository'''
        raise NotImplementedError

    def get_last_revision (self, uri):
        '''Return the last revision'''
        raise NotImplementedError 

    def add_watch (self, type, callback, user_data = None):
        if type not in range (N_WATCHES):
            raise InvalidWatch ('Type %d is not a valid watch type' % (type))
        
        if not self.watchers.has_key (type):
            self.watchers[type] = [(callback, user_data)]
        else:
            self.watchers[type].append ((callback, user_data))

        return len (self.watchers[type]) - 1

    def remove_watch (self, type, watcher_id):
        if type not in range (N_WATCHES):
            raise InvalidWatch ('Type %d is not a valid watch type' % (type))
        
        if not self.watchers.has_key (type):
            return

        try:
            self.watchers[type][watcher_id] = (None, None)
        except IndexError:
            pass
        except:
            raise

    def __run_callbacks (self, type, data):
        if not self.watchers.has_key (type):
            return
    
        for cb, user_data in self.watchers[type]:
            if cb is None:
                continue
            cb (data, user_data)

    def _run_command (self, command, type):
        def callback (data):
            self.__run_callbacks (type, data)

        if DEBUG:
            print command.cmd
            
        command.run (callback)

_backends = {}
def register_backend (backend_name, backend_class):
    _backends[backend_name] = backend_class

def _get_backend (backend_name):
    if backend_name not in _backends:
        try:
            __import__ ('repositoryhandler.backends.%s' % backend_name)
        except ImportError:
            pass

    if backend_name not in _backends:
        raise RepositoryUnknownError ('Repository type %s not registered' % backend_name)

    return _backends[backend_name]

def create_repository (backend_name, uri):
    repo_class = _get_backend (backend_name)
    return repo_class (uri)

def create_repository_from_path (path):
    rep = None
    repo_types = ['cvs', 'svn', 'git', 'bzr']
    for repo_type in repo_types:
        try:
            backend = 'repositoryhandler.backends.%s' % repo_type
            f = getattr (__import__ (backend, None, None, ['get_repository_from_path']), 
                    'get_repository_from_path')
        except ImportError:
            continue

        try:    
            type, uri = f (path)
            rep = create_repository (type, uri)
            if rep is not None:
                return rep
        except:
            continue

    if rep is None:
        raise RepositoryUnknownError ('Unknown repository type for path %s' % path)

