# -*- coding: utf-8 -*-
import logging
from zope import interface, schema
from zope.formlib import form
from five.formlib import formbase

from Products.CMFCore.utils import getToolByName
from Products.statusmessages.interfaces import IStatusMessage

from collective.simserver.core.utils import SimService

from collective.simserver.related import simserverMessageFactory as _

logger = logging.getLogger('collective.simserver.related')

class ISetRelatedForm(interface.Interface):

    min_score = schema.Float(
        title = _("Minimal score"),
        description = _("Minimal score an item must have to be set as related"),
        required = True,
        readonly = False,
        default = 0.4,
        min = 0.0,
        max = 1.0,
        )

    max_results = schema.Int(
        title= _(u'Max Relations'),
        description = _(u'Maximum number of related items to be set on an object'),
        required = True,
        readonly = False,
        default = 7,
        min = 1,
        max = 50,
        )

    max_related = schema.Int(
        title= _(u'Skip objects with x or more related items'),
        description = _(u'Do not add additional items if the object allready has this much related items'),
        required = True,
        readonly = False,
        default = 5,
        min = 1,
        max = 50,
        )


    same_query = schema.Bool(
        title= _(u"Same query"),
        description= _(u"Relate only to results that appear in this topic"),
        required=False,
        default=False,
        )


class SetRelatedForm(formbase.PageForm):

    form_fields = form.FormFields(ISetRelatedForm)
    label = _(u'Set related items')
    description = _(u'''Set similar items as related items''')

    @property
    def next_url(self):
        url = self.context.absolute_url()
        return url

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')


    @form.action('update')
    def actionUpdate(self, action, data):
        min_score = data['min_score']
        same_query = data['same_query']
        max_results = data['max_results']
        max_related = data['max_related']
        basequery = self.context.buildQuery()
        if basequery is None:
            return LazyCat([[]])
        baseresults = self.portal_catalog.searchResults(basequery)
        uids = [brain.UID for brain in baseresults]
        service = SimService()
        for brain in baseresults:
            if len(brain.getRawRelatedItems) >= max_related:
                continue
            response = service.query(brain.UID, min_score=min_score)
            if response['status'] == 'OK':
                simserveritems = response['response']
                suids =[s[0] for s in simserveritems
                            if brain.UID != s[0]]
                if same_query:
                    suids =[s for s in suids if s in uids]
                if suids:
                    related = brain.getRawRelatedItems
                    if len(related) < max_results:
                        new_related = related +[s for s in suids
                                        if s not in related]
                    else:
                        continue
                    if len(new_related[:max_results]) > len(related):
                        ob = brain.getObject()
                        ob.setRelatedItems(new_related[:max_results])
                        logger.info('set %i new relations to "%s"' %
                            (len(new_related[:max_results]) - len(related),
                             brain.Title))
            elif response['status'] == 'NOTFOUND':
                logger.info('document "%s" not in index' % brain.Title)
            else:
                IStatusMessage(self.request).addStatusMessage(
                        response['response'], type='error')
        status = _(u'related items set')
        IStatusMessage(self.request).addStatusMessage(status, type='info')
        self.request.response.redirect(self.next_url)




    @form.action('Cancel')
    def actionCancel(self, action, data):
        status = _(u'canceled')
        IStatusMessage(self.request).addStatusMessage(status, type='info')
        self.request.response.redirect(self.next_url)

