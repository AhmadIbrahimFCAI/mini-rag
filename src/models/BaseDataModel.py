from helpers.config import get_settings, Settings
from motor.motor_asyncio import AsyncIOMotorDatabase

class BaseDataModel:

    def __init__(self, db_client: AsyncIOMotorDatabase):
        self.db_client = db_client
        self.app_settings: Settings = get_settings()



        