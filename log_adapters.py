# -*- coding: utf-8 -*-

import logging


class CentralogHandler(logging.Handler):

	def __init__(self, centraloger):
		self._centraloger = centraloger
		logging.Handler.__init__(self)

	def emit(self, record):
		ei = record.exc_info
		if ei:
			dummy = self.format(record) # just to get traceback text into record.exc_text
			record.exc_info = None  # to avoid Unpickleable error
		self._centraloger.logEvent(record)
		if ei:
			record.exc_info = ei  # for next handler
