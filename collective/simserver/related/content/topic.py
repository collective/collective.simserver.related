#
from operator import itemgetter
from zope.interface import implements
import logging
from Products.CMFCore.utils import getToolByName

from Products.Archetypes import atapi
from Products.ATContentTypes.content import topic
from Products.ATContentTypes.content import schemata

from collective.simserver.related.config import PROJECTNAME

from collective.simserver.core.utils import SimService
from collective.simserver.related import simserverMessageFactory as _
from collective.simserver.related.interfaces import ISimserverCollection

SimserverTopicSchema = topic.ATTopicSchema.copy() + atapi.Schema((

    atapi.FloatField(
        'min_score',
        required = True,
        default = 0.7,
        widget=atapi.DecimalWidget(
            label=_(u"Minimal score"),
            description=_(u"Minimal score of related items"),
            visible={'edit': 'visible', 'view': 'invisible'},
        ),
        validators=('isDecimal'),
    ),

    atapi.IntegerField( 'min_similar',
        required = True,
        default = 30,
        widget = atapi.IntegerWidget(
            label = u'related to % items',
            description=_(u"The content must be similar to at least this percentage of basevalues"),
            visible={'edit': 'visible', 'view': 'visible'},
        ),
        validators=('isInt',)
    ),



    atapi.BooleanField(
        'exclude_orig',
        required=False,
        searchable=True,
        default=False,
        widget=atapi.BooleanWidget(
            label=_(u"Show related only"),
            description=_(u"Exclude the original values and show similar items only"),
        ),

    ),


))

schemata.finalizeATCTSchema(SimserverTopicSchema)

class SimserverTopic(topic.ATTopic):

    implements(ISimserverCollection)
    schema = SimserverTopicSchema


    def queryCatalog(self, *args, **kw):
        """Invoke the catalog using our criteria to augment any passed
        in query before calling the catalog.
        """
        basequery = self.buildQuery()
        portal_catalog = getToolByName(self, 'portal_catalog')
        baseresults = portal_catalog.searchResults(basequery)
        uids = [brain.UID for brain in baseresults]
        service = SimService()
        min_score = self.getMin_score()
        response = service.query(documents=uids, min_score=min_score, max_results=200)
        if response['status']=='OK':
            indexed_documents = response['response'].keys()
            similar_documents = []
            for values in response['response'].itervalues():
                similar_documents +=[k[0] for k in values]
            unique_docs = list(set(similar_documents))
            doc_count={}
            for doc in unique_docs:
                count = similar_documents.count(doc)
                docs = doc_count.get(count, [])
                docs.append(doc)
                doc_count[count] = docs
            min_similar = self.getMin_similar()
            for k, v in doc_count.iteritems():
                if (k*100)/len(indexed_documents) < min_similar:
                    for doc in v:
                        if doc in unique_docs:
                            unique_docs.remove(doc)

            if self.getExclude_orig():
                for doc in indexed_documents:
                    if doc in unique_docs:
                        unique_docs.remove(doc)
                for doc in uids:
                    if doc in unique_docs:
                        unique_docs.remove(doc)
            else:
                unique_docs += uids
            if self.hasSortCriterion():
                criterion = self.getSortCriterion()
                sort_order = None
                sort_on = criterion.getCriteriaItems()[0][1]
                if len(criterion.getCriteriaItems())==2:
                    sort_order = criterion.getCriteriaItems()[1][1]
                return portal_catalog(UID=unique_docs, sort_on=sort_on,
                                        sort_order=sort_order)
            else:
                sim_relevance = {}
                for values in response['response'].itervalues():
                    for v in values:
                        rel = sim_relevance.get(v[0],0)
                        rel += v[1]
                        sim_relevance[v[0]] = rel
                by_relevance = sorted(sim_relevance.items(),
                        key=itemgetter(1), reverse=True)
                brains= portal_catalog(UID=unique_docs)
                uid_brains ={}
                for brain in brains:
                    uid_brains[brain.UID] = brain
                result = []
                for r in by_relevance:
                    if r[0] in uid_brains:
                        result.append(uid_brains[r[0]])
                return result






atapi.registerType(SimserverTopic, PROJECTNAME)
