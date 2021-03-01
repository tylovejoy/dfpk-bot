from umongo import Document
from umongo.fields import StringField, FloatField, IntegerField, BooleanField

from internal.database_init import instance


@instance.register
class WorldRecords(Document):
    """WorldRecords"""

    code = StringField(required=True)
    name = StringField(required=True)
    posted_by = IntegerField(required=True)
    message_id = IntegerField(required=True)
    url = StringField(required=True)
    level = StringField(required=True)
    record = FloatField(required=True)
    verified = BooleanField(require=True)
    hidden_id = IntegerField(required=True)

    class Meta:
        collection_name = "WorldRecords"
