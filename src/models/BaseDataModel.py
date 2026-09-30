from helpers.config import get_settings, Settings
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.orm.session import sessionmaker

class BaseDataModel:

    def __init__(self, db_client: sessionmaker):
        self.db_client = db_client
        self.app_settings: Settings = get_settings()



        