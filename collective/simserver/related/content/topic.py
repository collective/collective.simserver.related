#
from zope.interface import implements
import logging
from Products.CMFCore.utils import getToolByName

from Products.Archetypes import atapi
from Products.ATContentTypes.content import topic
from Products.ATContentTypes.content import schemata

from collective.simserver.related.config import PROJECTNAME

from collective.simserver.core.utils import SimService
from collective.simserver.related import simserverMessageFactory as _

SimserverTopicSchema = topic.ATTopicSchema.copy() + atapi.Schema((

    atapi.FloatField(
        'min_score',
        required = True,

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
            label = u'related to XX% items',
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


    def queryCatalog(self, *args, **kw):
        """Invoke the catalog using our criteria to augment any passed
        in query before calling the catalog.
        """
        baseresults = super(SimserverTopic, self).queryCatalog(*args, **kw)
        portal_catalog = getToolByName(self, 'portal_catalog')
        uids = [brain.UID for brain in baseresults]
        service = SimService()
        min_score = self.getMin_score()
        min_similar = float(self.getMin_similar())/100.0
        simresult = service.query(documents=uids, min_score=min_score, max_results=200)
        simuids = [uid for uid in simresult.itervalues()]
        import ipdb; ipdb.set_trace()
        #if self.hasSortCriterion():




atapi.registerType(SimserverTopic, PROJECTNAME)
