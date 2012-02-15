# -*- coding: utf-8 -*-
import logging
from zope.interface import implements, Interface

from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName

from Products.statusmessages.interfaces import IStatusMessage

from collective.simserver.core import utils as coreutils

from collective.simserver.related import simserverMessageFactory as _

logger = logging.getLogger('collective.simserver.related')


class ISimilarTopicView(Interface):
    """
    RelatedItems view interface
    """

class SimilarTopicView(BrowserView):
    implements(ISimilarTopicView)

    def item_count(self):
        return self.context.getItemCount()


    def results(self, *args, **kw):
        limit = self.context.getLimitNumber()
        max_items = self.context.getItemCount()
        result = self.context.queryCatalog(*args, **kw)
        if limit and max_items:
            return result[:max_items]
        else:
            return result
