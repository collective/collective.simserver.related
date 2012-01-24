# -*- coding: utf-8 -*-
import logging
from zope.interface import implements, Interface

from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName

from collective.simserver.core import utils as coreutils

from collective.simserver.related import simserverMessageFactory as _

logger = logging.getLogger('collective.simserver.related')

class IRelatedItemsView(Interface):
    """
    RelatedItems view interface
    """

class RelatedItemsView(BrowserView):
    """
    RelatedItems browser view
    """
    implements(IRelatedItemsView)

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    @property
    def portal(self):
        return getToolByName(self.context, 'portal_url').getPortalObject()


    def getsimilaritems(self):
        """ query simserver for related items, exclude self.context"""
        contextuid = self.context.UID()
        service = coreutils.SimService()
        simserveritems = service.query([contextuid])
        suids =[s[0] for s in simserveritems[contextuid]
                    if contextuid != s[0]]
        brains = self.portal_catalog(UID = suids)
        items = {}
        for brain in brains:
            items[brain.UID] = {'url': brain.getURL(),
                    'uid': brain.UID,
                    'title': brain.Title,
                    'desc': brain.Description}
        results = []
        for item in simserveritems[contextuid]:
            if item[0] in items:
                result = {}
                result = items[item[0]]
                result['similarity'] = item[1]
                results.append(result)
        return results



