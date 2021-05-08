from umongo import Document
from umongo.fields import StringField, IntegerField, FloatField

from internal.database_init import instance


@instance.register
class MildcoreData(Document):
    """TournamentData database document."""

    posted_by = IntegerField(required=True, unique=True)
    record = FloatField(required=True)
    attachment_url = StringField(required=True)

    class Meta:
        """MongoDb database collection name."""

        collection_name = "MildcoreData"
