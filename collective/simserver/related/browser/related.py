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

class IRelatedItemsView(Interface):
    """
    RelatedItems view interface
    """

class RelatedItemsView(BrowserView):
    """
    RelatedItems browser view
    """
    #XXX This needs some caching
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
        response = service.query([contextuid])
        related = list(self.context.getRawRelatedItems())
        if response['status'] == 'OK':
            simserveritems = response['response']
            if contextuid in simserveritems:
                suids =[s[0] for s in simserveritems[contextuid]
                            if contextuid != s[0]]
            else:
                return []
            brains = self.portal_catalog(UID = suids)
            items = {}
            for brain in brains:
                isrelated = (brain.UID in related)
                items[brain.UID] = {'url': brain.getURL(),
                        'uid': brain.UID,
                        'title': brain.Title,
                        'desc': brain.Description,
                        'state': brain.review_state,
                        'icon': brain.getIcon,
                        'isrelated':isrelated}
            results = []
            for item in simserveritems[contextuid]:
                if item[0] in items:
                    result = {}
                    result = items[item[0]]
                    result['similarity'] = item[1]
                    results.append(result)
            return results



class RelatedItemsEdit(RelatedItemsView):

    template = ViewPageTemplateFile('relateditems.pt')

    def __call__(self):
        form = self.request.form
        if form.has_key('form.button.save'):
            related = list(self.context.getRawRelatedItems())
            related = related + [uid for uid in form.get('UID', [])
                                    if uid not in related]
            self.context.setRelatedItems(related)
            self.request.response.redirect(self.context.absolute_url() + '/edit')
            return ''
        elif form.has_key('form.button.cancel'):
            self.request.response.redirect(self.context.absolute_url() + '/view')
            return ''
        elif form.has_key('form.button.reindex'):
            id = self.context.getId()
            text = self.context.SearchableText()
            text = text.strip()
            text = text.lstrip(id).lstrip()
            text = text.decode('utf-8', 'ignore')
            text = text.encode('utf-8')
            uid = self.context.UID()
            service = coreutils.SimService()
            response = service.index([{'id': uid, 'text': text}])
            status = str(response)
            IStatusMessage(self.request).addStatusMessage(status,
                type='info')
        return self.template()
