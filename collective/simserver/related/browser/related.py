# -*- coding: utf-8 -*-
from collections import defaultdict
from operator import itemgetter

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
    tags = None

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
        max_votes = 3
        intervall = (1 - service.min_score) / max_votes
        response = service.query([contextuid])
        related = list(self.context.getRawRelatedItems())
        items = {}
        tags = []
        similarities = {}
        if response['status'] == 'OK':
            simserveritems = response['response']
            if contextuid in simserveritems:
                for item in simserveritems[contextuid]:
                    if contextuid != item[0]:
                        similarities[item[0]] = item[1]
            if similarities:
                brains = self.portal_catalog(UID = similarities.keys())
                for brain in brains:
                    isrelated = (brain.UID in related)
                    similarity = similarities.get(brain.UID, 0)
                    items[brain.UID] = {'url': brain.getURL(),
                            'uid': brain.UID,
                            'title': brain.Title,
                            'desc': brain.Description,
                            'state': brain.review_state,
                            'icon': brain.getIcon,
                            'similarity': similarity,
                            'tags': brain.Subject,
                            'isrelated':isrelated}
                    if brain.Subject:
                        #votes = 1
                        votes = int((similarity -  service.min_score) /intervall) + 1
                        tags += votes * brain.Subject
        else:
            simserveritems = {contextuid : []}
        results = []
        nsuids =[] #related items not returned by similarity index
        for ruid in related:
            if ruid not in items:
                nsuids.append(ruid)
        # add items that are related items but not
        # in the similarity results to the results

        if nsuids:
            brains = self.portal_catalog(UID = nsuids)
            for brain in brains:
                result = {'url': brain.getURL(),
                    'uid': brain.UID,
                    'title': brain.Title,
                    'desc': brain.Description,
                    'state': brain.review_state,
                    'icon': brain.getIcon,
                    'tags': brain.Subject,
                    'similarity' : 'N/A',
                    'isrelated':True}
                results.append(result)
                if brain.Subject:
                    tags += max_votes * brain.Subject
        # sort the items by similarity and append to results
        for item in simserveritems[contextuid]:
            if item[0] in items:
                results.append(items[item[0]])
        self.tags = tags
        return results



class RelatedItemsEdit(RelatedItemsView):

    template = ViewPageTemplateFile('relateditems.pt')

    def get_tags(self):
        has_tags = self.context.Subject()
        if not has_tags:
            has_tages = []
        counts = defaultdict(int)
        for tag in self.tags:
            counts[tag] += 1
        weighted = []
        for tag, occurences in counts.items():
            if tag in has_tags:
                istag = True
            else:
                istag = False
            weighted.append({'tag': tag, 'istag': istag,
                'freq': float(occurences)/len(self.tags)})
        for t in has_tags:
            if t not in counts:
                weighted.append({'tag': tag, 'istag': istag,
                    'freq': 1})
        weighted.sort(key=itemgetter('freq'), reverse=True)
        return weighted

    def __call__(self):
        form = self.request.form
        if form.has_key('form.button.save'):
            related = [uid for uid in form.get('UID', [])]
            if related:
                self.context.setRelatedItems(related)
            self.request.response.redirect(self.context.absolute_url() + '/view')
            tags = [tag for tag in form.get('Subject', [])]
            if tags:
                self.context.setSubject(tags)
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
