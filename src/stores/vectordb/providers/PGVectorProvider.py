from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import (DistanceMethodEnums, PgVectorTablesSchemeEnums,
                             PgVectorDistanceMethodEnums, PgVectorIndexTypeEnums,)
import logging
from typing import List
from models.db_schemes import RetrievedDocument
from sqlalchemy.sql import text as sql_text
import json
from sqlalchemy.orm import sessionmaker


class PGVectorProvider(VectorDBInterface):
    def __init__(self, db_client:sessionmaker, default_vector_size: int = 785,
                 distance_method: str = None, index_threshold:int = 100):

        self.db_client = db_client
        self.default_vector_size = default_vector_size
        self.index_threshold = index_threshold

        if distance_method == DistanceMethodEnums.COSINE.value:
            distance_method = PgVectorDistanceMethodEnums.COSINE.value
        elif distance_method == DistanceMethodEnums.DOT.value:
            distance_method = PgVectorDistanceMethodEnums.DOT.value

        self.pgvector_table_prefix = PgVectorTablesSchemeEnums._PREFIX.value

        self.distance_method = distance_method
        self.logger = logging.getLogger('uvicorn')
        self.default_index_name = lambda collection_name: f"{collection_name}_vector_idx"


    async def get_pgvector_index_name(self, collection_name: str) -> str:
        return f"{collection_name}_vector_idx"

    async def connect(self):
        session:sessionmaker
        async with self.db_client() as session:
            try:
                # Check if  vector extension already exist
                result = await session.execute(sql_text(
                    "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
                ))
                extension_exists = result.scalar_one_or_none()
                if not extension_exists:
                    # Only create if it doesn't exist
                    await session.execute(sql_text("CREATE EXTENSION vector"))
                    await session.commit()
            except Exception as e:
                # if extension already exists or any other error, just log and continue
                self.logger.warning(f"Vector extension setup: {e}")
                await session.rollback()

    async def disconnect(self):
        pass


    async def is_collection_existed(self, collection_name: str) -> str:
        session: sessionmaker
        async with self.db_client() as session:
            async with session.begin():
                list_tb1 = sql_text(f'SELECT * FROM pg_tables WHERE tablename = :collection_name')
                results = await session.execute(list_tb1, {'collection_name': collection_name})
                print('results: ', type(results))
                record = results.scalar_one_or_none()
                print('record: ', type(record))
        return record


    async def list_all_collections(self) -> List:
        session: sessionmaker
        async with self.db_client() as session:
            async with session.begin():
                list_tb1 = sql_text('SELECT tablename FROM pg_tables WHERE tablename LIKE :prefix')
                results = await session.execute(list_tb1, {'prefix': self.pgvector_table_prefix})
                records = results.scalars().all()
        return records


    async def get_collection_info(self, collection_name: str) -> dict:
        session: sessionmaker
        async with self.db_client() as session:
            async with session.begin():
                table_info_sql = sql_text(f'''
                    SELECT  schemaname, tablename, tableowner, tablespace, hasindexes
                    FROM pg_tables
                    WHERE tablename = :collection_name
                ''')
                count_sql = sql_text(f'SELECT COUNT(*) FROM {collection_name}')

                table_info = await session.execute(table_info_sql, {'collection_name': collection_name})
                record_count = await session.execute(count_sql)

                table_info = table_info.fetchone()
                if not table_info:
                    return None
                
                print('table_info:', table_info)

                return {
                    'table_info' : {
                        'schemaname': table_info[0],
                        'tablename': table_info[1],
                        'tableowner': table_info[2],
                        'tablespace': table_info[3],
                        'hasindexes': table_info[4],
                    },
                    'record_count': record_count.scalar_one(),
                }


    async def delete_collection(self, collection_name: str):
        session: sessionmaker
        async with self.db_client() as session:
            async with session.begin():
                self.logger.info(f"Deleting collection: {collection_name}")
                delete_sql = sql_text(f'DROP TABLE IF EXISTS {collection_name}')
                await session.execute(delete_sql)
                await session.commit()

        return True


    async def create_collection(self, collection_name:str, embedding_size:int, do_reset:bool = False):
        if do_reset:
            _ = await self.delete_collection(collection_name=collection_name)
        is_collection_existed = await self.is_collection_existed(collection_name=collection_name)
        if not is_collection_existed:
            self.logger.info(f"Create collection: {collection_name}")
            session: sessionmaker
            async with self.db_client() as session:
                async with session.begin():
                    create_sql = sql_text(
                        f"CREATE TABLE {collection_name}("
                        f"{PgVectorTablesSchemeEnums.ID.value} bigserial PRIMARY KEY, "
                        f"{PgVectorTablesSchemeEnums.TEXT.value} text, "
                        f"{PgVectorTablesSchemeEnums.VECTOR.value} vector({embedding_size}), "
                        f"{PgVectorTablesSchemeEnums.METADATA.value} jsonb DEFAULT '{{}}', "
                        f"{PgVectorTablesSchemeEnums.CHUNK_ID.value} integer, "
                        f"FOREIGN KEY ({PgVectorTablesSchemeEnums.CHUNK_ID.value}) REFERENCES chunks(chunk_id)"
                        ")"
                    )
                    await session.execute(create_sql)
                    await session.commit()
            return True
    
        return False


    async def is_index_existed(self, collection_name: str) -> bool:
        index_name = self.default_index_name(collection_name)
        session: sessionmaker
        async with self.db_client() as session:
            async with session.begin():
                check_sql = sql_text(f"""
                                    SELECT 1
                                    FROM pg_indexes
                                    WHERE tablename = :collection_name
                                    AND indexname = :index_name
                                    """)
                results = await session.execute(check_sql, {
                    'collection_name': collection_name,
                    'index_name': index_name,
                })

                return bool(results.scalar_one_or_none())

    async def create_vector_index(self, collection_name:str, 
                                  index_type: str = PgVectorIndexTypeEnums.HNSW.value):
        is_index_existed = self.is_index_existed(collection_name=collection_name)
        if is_index_existed:
            return False

        session: sessionmaker
        async with self.db_client() as session:
            async with session.begin():
                count_sql = sql_text(f"SELECT COUNT(*) FROM {collection_name}")
                result = await session.execute(count_sql)
                records_count = result.scalar_one()

                if records_count < self.index_threshold:
                    return False

                self.logger.info(f"START: Creating vector index for collection: {collection_name}")
                index_name = self.default_index_name(collection_name)
                create_idx_sql = sql_text(
                    f"CREATE INDEX {index_name} ON {collection_name} "
                    f"USING {index_type} ({PgVectorTablesSchemeEnums.VECTOR.value} {self.distance_method})"
                )
                await session.execute(create_idx_sql)
                self.logger.info(f"END: Created vector index for collection: {collection_name}")


    async def reset_vector_index(self, collection_name: str, index_type:str = PgVectorIndexTypeEnums.HNSW.value) -> bool:
        index_name = self.default_index_name(collection_name)
        session: sessionmaker
        async with self.db_client() as session:
            async with session.begin():
                drop_sql = sql_text(f"DROP INDEX IF EXISTS {index_name}")
                await session.execute(drop_sql)

        return await self.create_vector_index(collection_name=collection_name, index_type=index_type)
    


    async def insert_one(self, collection_name: str, text: str, vector: list,
                         metadata:dict = None, record_id:str = None):
        is_collection_existed = await self.is_collection_existed(collection_name=collection_name)
        if not is_collection_existed:
            self.logger.error(f"Can not insert new record to not-existed collection: {collection_name}")
            return False

        if not record_id:
            self.logger.error(f"Can not insert new record without chunk_id: {collection_name}")
            return False

        session: sessionmaker
        async with self.db_client() as session:
            async with session.begin():
                insert_sql = sql_text(
                    f"INSERT INTO {collection_name} "
                    f"({PgVectorTablesSchemeEnums.TEXT.value}, {PgVectorTablesSchemeEnums.VECTOR.value}, {PgVectorTablesSchemeEnums.METADATA.value}, {PgVectorTablesSchemeEnums.CHUNK_ID.value}) "
                    f"VALUES (:text, :vector, :metadata, :chunk_id)"
                )
                metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else "{}"
                await session.execute(insert_sql, {
                    'text': text,
                    'vector': '[' + ','.join([str(v) for v in vector]) + ']',
                    'metadata': metadata_json,
                    'chunk_id': record_id,
                })
                await session.commit()  # do .commit if db changed

        return True


    async def insert_many(self, collection_name:str, texts:list, vectors:list, 
                          metadata:list = None, record_ids:list = None, batch_size:int = 50):
        is_collection_existed = await self.is_collection_existed(collection_name=collection_name)
        if not is_collection_existed:
            self.logger.error(f"Can not insert new records to non-existed collection: {collection_name}")
            return False

        if len(vectors) != len(record_ids):
            self.logger.error(f"Invalid data items for collection: {collection_name}")
            return False

        if not metadata or len(metadata) == 0:
            metadata = [None] * len(texts)

        session: sessionmaker
        async with self.db_client() as session:
            async with session.begin():
                for i in range(0, len(texts), batch_size):
                    batch_texts = texts[i: i+batch_size]
                    batch_vectors = vectors[i: i+batch_size]
                    batch_metadata = metadata[i: i+batch_size]
                    batch_record_ids = record_ids[i: i+batch_size]

                    values = []

                    for _text, _vector, _metadata, _record_id in zip(batch_texts, batch_vectors, batch_record_ids):
                        metadata_json = json.dumps(_metadata, ensure_ascii=False) if _metadata else "{}"
                        values.append({
                            'text': _text,
                            'vector': '[' + ','.join([str(v) for v in _vector]) + ']',
                            'metadata': metadata_json,
                            'chunk_id': _record_id,
                        })
                    batch_insert_sql = sql_text(
                        f"INSERT INTO {collection_name} "
                        f"({PgVectorTablesSchemeEnums.TEXT.value}, "
                        f"({PgVectorTablesSchemeEnums.VECTOR.value}, "
                        f"({PgVectorTablesSchemeEnums.METADATA.value}, "
                        f"({PgVectorTablesSchemeEnums.CHUNK_ID.value}) "
                        f"VALUES (:text, :vector, :metadata, :chunk_id)"
                    )

                    await session.execute(batch_insert_sql, values)

        await self.create_vector_index(collection_name=collection_name)
        
        return True


    async def search_by_vector(self, collection_name:str, vector:list, limit:int):
        
        is_collection_existed = await self.is_collection_existed(collection_name=collection_name)
        if not is_collection_existed:
            self.logger.error(f"Can not search for records in a non-existed collection: {collection_name}")
            return False

        vector = '[' + ','.join([str(v) for v in vector]) + ']'

        session: sessionmaker
        async with self.db_client() as session:
            async with session.begin():
                search_sql = sql_text(
                    f"SELECT {PgVectorTablesSchemeEnums.TEXT.value} as text, "
                    f"1 - ({PgVectorTablesSchemeEnums.VECTOR.value} <=> :vector) as score "
                    f"FROM {collection_name} "
                    f"ORDER BY score DESC "
                    F"LIMIT {limit}"
                )

                result = await session.execute(search_sql, {'vector': vector})

                records = result.fetchall()

                return [
                    RetrievedDocument(
                        record=record.text,
                        score=record.score,
                    )
                    for record in records
                ]
