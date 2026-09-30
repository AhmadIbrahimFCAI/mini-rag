from .BaseDataModel import BaseDataModel
from .db_schemes import DataChunk
from .enums.DataBaseEnum import DataBaseEnum
from bson.objectid import ObjectId
from pymongo import InsertOne
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.future import select
from sqlalchemy import func, delete
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.engine.result import ChunkedIteratorResult


class ChunkModel(BaseDataModel):

    def __init__(self, db_client: sessionmaker):
        super().__init__(db_client=db_client)
        # self.collection = self.db_client

    # `init_collection` has to be called after `__init__` directly,
    # so we create thisss method
    @classmethod
    async def create_instance(cls, db_client: sessionmaker):
        instance = cls(db_client)
        return instance

    async def create_chunk(self, chunk: DataChunk):
        async with self.db_client() as session:
            async with session.begin():
                session.add(chunk)
            await session.commit()
            await session.refresh(chunk)
        
        return chunk

    async def get_chunk(self, chunk_id: str):
        async with self.db_client() as session:
            async with session.begin():
                query = select(DataChunk).where(DataChunk.chunk_id == chunk_id)
                result:ChunkedIteratorResult = await session.execute(query)
                chunk = result.scalar_one_or_none()
            return chunk
        # result = await self.collection.find_one({
        #     '_id': ObjectId(chunk_id),
        # })

        # if result is None: return None

        # return DataChunk(**result)

    async def insert_many_chunks(self, chunks: list, batch_size: int = 100):
        session: sessionmaker
        async with self.db_client() as session:
            async with session.begin():
                for i in range(0, len(chunks), batch_size):
                    batch = chunks[i:i+batch_size]
                    session.add_all(batch)
                    print("session.add_all: ", type(session))
            await session.commit()
        return len(chunks)

        # for i in range(0, len(chunks), batch_size):
        #     batch = chunks[i:i+batch_size]
        #     operation = [
        #         InsertOne(chunk.dict(by_alias=True, exclude_unset=True))
        #         for chunk in batch
        #     ]
        #     await self.collection.bulk_write(operation)
        # return len(chunks)

    async def delete_chunks_by_project_id(self, project_id: ObjectId):
        session: sessionmaker
        async with self.db_client() as session:
            stmt = delete(DataChunk).where(DataChunk.chunk_project_id == project_id)
            result:ChunkedIteratorResult = await session.execute(stmt)
            await session.commit()
        return result.rowcount
        
        # result = await self.collection.delete_many({
        #     'chunk_project_id': project_id,
        # })
        # return result.deleted_count


    async def get_project_chunks(self, project_id: ObjectId, page_no: int=1, page_size: int = 50):
        session: sessionmaker
        async with self.db_client() as session:
            stmt = select(DataChunk).where(
                DataChunk.chunk_project_id == project_id
            ).offset((page_no-1) * page_size).limit(page_size)
            result:ChunkedIteratorResult = await session.execute(stmt)
            records = result.scalars().all()

        return records

        