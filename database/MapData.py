from umongo import Document, validate
from umongo.fields import *

from internal.database_init import instance
import logging

# TODO: Change code from _id to unique
# TODO: Figure out how to edit current DB to reflect above change


@instance.register
class MapData(Document):
    """MapData"""

    code = StringField(required=True, unique=True)
    creator = StringField(required=True)
    map_name = StringField(required=True)
    posted_by = IntegerField(required=True)
    type = ListField(StringField(), required=True)
    desc = StringField()

    class Meta:
        collection_name = "MapData"
