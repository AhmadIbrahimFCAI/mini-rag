from .BaseDataModel import BaseDataModel
from .db_schemes import Asset
from .enums.DataBaseEnum import DataBaseEnum
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from sqlalchemy.future import select
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.engine.result import ChunkedIteratorResult

class AssetModel(BaseDataModel):
    # Note that `__init__` hasn't to be async
    def __init__(self, db_client: sessionmaker):
        super().__init__(db_client=db_client)
        self.collection = self.db_client



    # `init_collection` has to be called after `__init__` directly,
    # so we create thisss method
    @classmethod
    async def create_instance(cls,db_client: sessionmaker):
        instance = cls(db_client)
        return instance


    async def create_asset(self, asset:Asset):
        async with self.db_client() as session:
            async with session.begin():
                session.add(asset)
            await session.commit()
            await session.refresh(asset)
        return asset
        # result = await self.collection.insert_one(asset.dict(by_alias=True, exclude_unset=True))
        # asset.asset_id = result.inserted_id
        # return asset

    async def get_all_project_assets(self, asset_project_id: str, asset_type: str):
        async with self.db_client() as session:
            stmt = select(Asset).where(
                Asset.asset_project_id == asset_project_id,
                Asset.asset_type == asset_type,
            )
            result:ChunkedIteratorResult = await session.execute(stmt)
            records = result.scalars().all()
        return records

    async def get_asset_record(self, asset_project_id: str, asset_name: str):
        async with self.db_client() as session:
            stmt = select(Asset).where(
                Asset.asset_project_id == asset_project_id,
                Asset.asset_name == asset_name,
            )
            result:ChunkedIteratorResult = await session.execute(stmt)
            record = result.scalar_one_or_none()
        return record
        
        # print('asset_project_id', asset_project_id)
        # record = await self.collection.find_one({
        #     'asset_project_id': ObjectId(asset_project_id) if isinstance(asset_project_id, str) else asset_project_id,
        #     'asset_name': asset_name,
        # })

        # if record: return Asset(**record)
        # return None