from .BaseConroller import BaseController
from stores.vectordb.VectorDBInterface import VectorDBInterface
from stores.llm.LLMInterface import LLMInterface
from models.db_schemes import Project, DataChunk
from stores.llm.LLMEnums import DocumentTypeEnum
from typing import List
import json
from models.db_schemes import RetrivedDocument
from stores.llm.templates.template_parser import TemplateParser


class NLPController(BaseController):

    def __init__(self, vectordb_client: VectorDBInterface, generation_client: LLMInterface,
                 embedding_client: LLMInterface, template_parser: TemplateParser, ):
        super().__init__()
        self.vectordb_client = vectordb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.template_parser = template_parser

    def create_collection_name(self, project_id: str):
        return f"collection_{project_id}".strip()

    def reset_vector_db_collection(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        return self.vectordb_client.delete_collection(collection_name=collection_name)

    def get_vector_db_collection_info(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        try:
            collection_info = self.vectordb_client.get_collection_info(collection_name=collection_name)
        except: return {}    
        return json.loads(
            json.dumps(collection_info, default=lambda x: x.__dict__)
        )

    def index_into_vector_db(self, project: Project, chunks: List[DataChunk], chunks_ids: List[int], do_reset: bool = False):

        # step1: get collection name
        collection_name = self.create_collection_name(project_id=project.project_id)

        # step2: manage items
        texts = [c.chunk_text for c in chunks]
        metadata = [c.chunk_metadata for c in chunks]

        vectors = [
            self.embedding_client.embed_text(text=text, document_type=DocumentTypeEnum.DOCUMENT.value)
            for text in texts
        ]


        # step3: create collection if not exists
        _ = self.vectordb_client.create_collection(
            collection_name=collection_name,
            embedding_size=self.embedding_client.embedding_size,
            do_reset=do_reset,
        )



        # step4: insert into vector db
        _ = self.vectordb_client.insert_many(
                collection_name=collection_name,
                texts=texts,
                vectors=vectors,
                metadata=metadata,
                record_ids=chunks_ids,
            )
        return True

    def search_vector_db_collection(self, project: Project, text: str, limit: int = 10) -> list[RetrivedDocument] | bool:
        # step1: get collection name
        collection_name = self.create_collection_name(project_id=project.project_id)

        # step2: get collection name
        vector = self.embedding_client.embed_text(text=text, document_type=DocumentTypeEnum.QUERY.value)
        if not vector or len(vector)==0:
            return False

        # step3: get collection name
        results = self.vectordb_client.search_by_vector(
            collection_name=collection_name,
            vector=vector,
            limit=limit,
        )



        if not results: return False

        # return json.load(
        #     json.dumps(results, default=lambda x: x.__dict__)
        # )
        return results

    def answer_rag_question(self, project: Project, query: str, limit: int = 10):
        answer, full_prompt, chat_history = None, None, None

        # step1: retrive related documents
        retrived_documents = self.search_vector_db_collection(
            project=project,
            text=query,
            limit=limit,
        )

        if not retrived_documents or len(retrived_documents)==0:
            return answer, full_prompt, chat_history

        # step2: construct LLM prompt
        system_prompt = self.template_parser.get('rag', 'system_prompt')

        document_prompts = '\n'.join([
            self.template_parser.get('rag', 'document_prompt', {
                'doc_num': idx,
                'chunk_text': doc.text,
            })
            for idx, doc in enumerate(retrived_documents, 1)
        ])

        footer_prompt = self.template_parser.get('rag', 'footer_prompt')

        chat_history = [
            self.generation_client.construct_prompt(
                prompt=system_prompt,
                role=self.generation_client.enums.SYSTEM.value,
            )
        ]
        full_prompt = '\n\n'.join([
            document_prompts, footer_prompt,
        ])

        answer = self.generation_client.generate_text(
            prompt=full_prompt,
            chat_histroy=chat_history,
        )
        

        return answer, full_prompt, chat_history