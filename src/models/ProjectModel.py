from .BaseDataModel import BaseDataModel
from .db_schemes import Project
from .enums.DataBaseEnum import DataBaseEnum
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.engine.result import ChunkedIteratorResult

class ProjectModel(BaseDataModel):
    # Note that `__init__` hasn't to be async
    def __init__(self, db_client: sessionmaker):
        super().__init__(db_client=db_client)
        self.collection = self.db_client
        print("db_client:", type(db_client))



    # `init_collection` has to be called after `__init__` directly,
    # so we create thisss method
    @classmethod
    async def create_instance(cls,db_client: sessionmaker):
        instance = cls(db_client)
        return instance

    
    async def create_project(self, project: Project):
        async with self.db_client() as session:
            async with session.begin():
                session.add(project)
            await session.commit()
            await session.refresh(project)
        
        return project

    async def get_project_or_create_one(self, project_id: int):
        async with self.db_client() as session:
            async with session.begin():
                
                query = select(Project).where(Project.project_id == project_id)
                # project = query.scalar_subquery()
                result:ChunkedIteratorResult = await session.execute(query)
                
                project = result.scalar_one_or_none()
                if project is None:
                    project_rec = Project(
                        project_id = project_id,
                    )
                    project = await self.create_project(project=project_rec)

                return project

    async def get_all_projects(self, page: int = 1, page_size: int = 10) -> tuple[list[Project], int]:
        async with self.db_client() as session:
            async with session.begin():
                total_documents:ChunkedIteratorResult = await session.execute(select(
                    func.count(Project.project_id)
                ))
                total_documents = total_documents.scalar_one()
                total_pages = total_documents // page_size
                if total_documents % page_size > 0:
                    total_pages += 1

                query = select(Project).offset((page - 1) * page_size).limit(page_size)
                result:ChunkedIteratorResult = await session.execute(query)
                projects = result.scalars().all()
                return projects, total_pages
        
        # # count total number of documents
        # total_documents = await self.collection.count_documents({})

        # # calculate total number of pages
        # total_pages = total_documents // page_size
        # if total_documents % page_size > 0:
        #     total_pages += 1

        # cursor = self.collection.find().skip( (page-1) * page_size ).limit(page_size)

        # projects = []

        # async for document in cursor:
        #     projects.append(
        #         Project(**document)
        #     )

        # return projects, total_pages
