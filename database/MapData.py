from umongo import Document
from umongo.fields import StringField, IntegerField, ListField

from internal.database_init import instance


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
