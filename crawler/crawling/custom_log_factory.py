# -*- coding:utf-8 -*-
import logging
import sys
import datetime
import os
import errno
import copy

from pythonjsonlogger import jsonlogger
from cloghandler import ConcurrentRotatingFileHandler

from scutils.log_factory import LogFactory, LogObject


class CustomLogFactory(LogFactory):
    '''
    Goal is to manage Simple LogObject instances
    Like a Singleton
    '''
    _instance = None

    @classmethod
    def get_instance(self, **kwargs):
        if self._instance is None:
            self._instance = CustomLogObject(**kwargs)

        return self._instance


class CustomLogObject(LogObject):
    '''
    加入Print
    '''


    def info(self, message, extra={}):
        '''
        Writes an info message to the log

        @param message: The message to write
        @param extra: The extras object to pass in
        '''
        if self.level_dict['INFO'] >= self.level_dict[self.log_level]:
            extras = self.add_extras(extra, "INFO")
            self._write_message(message, extras)
            print message

