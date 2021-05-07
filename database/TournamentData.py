from umongo import Document
from umongo.fields import StringField, IntegerField, FloatField

from internal.database_init import instance


@instance.register
class TournamentData(Document):
    """TournamentData database document."""

    code = StringField(required=True, unique=True)
    posted_by = IntegerField(required=True)
    record = FloatField(required=True)

    class Meta:
        """MongoDb database collection name."""

        collection_name = "TournamentData"
