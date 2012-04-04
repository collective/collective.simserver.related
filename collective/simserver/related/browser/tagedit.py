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


class ITagSimilar(Interface):
    """
    RelatedItems view interface
    """

class TagSimilar(BrowserView):
    implements(ITagSimilar)

    template = ViewPageTemplateFile('tagedit.pt')

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')


    def getTags(self):
        """ return tags defined by subject criterion if any """
        criteria = self.context.listCriteria()
        for criterion in criteria:
            for key, value in criterion.getCriteriaItems():
                    if key == 'Subject':
                        if 'query' in value:
                            return ';'.join(value['query'])
                        else:
                            return ';'.join(value)

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


    def __call__(self):
        form = self.request.form
        if 'form.button.save' in form:
            if 'tags' in form:
                tags = form['tags'].split(';')
                uids = form.get('UID', [])
                brains = self.portal_catalog(UID = uids)
                for brain in brains:
                    ob = brain.getObject()
                    otags = list(ob.Subject())
                    ob.setSubject(set(otags + tags))
                    ob.indexObject()
                status = _(u'documents tagged')
                IStatusMessage(self.request).addStatusMessage(status,
                type='info')
            else:
                status = _(u'No value to tag supplied')
                IStatusMessage(self.request).addStatusMessage(status,
                type='error')
        return self.template()
