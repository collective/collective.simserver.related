#
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary


def criteria_vocabulary_factory(context):
    criteria = []
    for criterion in context.listCriteria():
        if criterion.meta_type =='ATSortCriterion':
            continue
        else:
            criteria.append(criterion.Field())
    items = [(c,c) for c in criteria]
    return SimpleVocabulary.fromItems(items)
