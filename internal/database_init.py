from motor.motor_asyncio import AsyncIOMotorClient
from umongo import Instance


instance = None


def init(dburl, dbname):
    """Initializes a database instance."""
    global instance

    client = AsyncIOMotorClient(dburl)

    instance = Instance(client[dbname])
