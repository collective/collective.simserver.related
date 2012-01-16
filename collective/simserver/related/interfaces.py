# -*- coding: utf-8 -*-
from zope import interface, schema
from plone.theme.interfaces import IDefaultPloneLayer

from collective.simserver.related import simserverMessageFactory as _


class ISimserverLayer(IDefaultPloneLayer):
    """Marker interface that defines a Zope 3 browser layer.
    """
