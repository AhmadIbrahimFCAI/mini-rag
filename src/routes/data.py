from fastapi import APIRouter, Depends, UploadFile, status
from fastapi.responses import JSONResponse
from helpers.config import get_settings, Settings
from controllers import DataController, ProjectController, ProcessController
import aiofiles
from models import ResponseSignal
import logging
from .schemes.data import ProcessRequest

logger = logging.getLogger('uvicorn.error')

data_router = APIRouter(
    prefix='/api/v1/data',
    tags=['api_v1', 'data'],
)

@data_router.post('/upload/{project_id}')
async def upload_data(project_id: str, file: UploadFile, 
                      app_settings: Settings = Depends(get_settings)):

    # validate the file properities
    data_ctrl = DataController()

    is_valid, result_signal = data_ctrl.validate_upload_file(file=file)

    if not is_valid:
        return JSONResponse(
            status_code = status.HTTP_400_BAD_REQUEST,
            content = {
                'signal': result_signal,
            }
        )

    project_dir_path = ProjectController().get_project_path(project_id=project_id)
    file_path, file_id = data_ctrl.generate_unique_filename(
        org_filename = file.filename, 
        project_id = project_id,
    )
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)

    except Exception as e:
        logger.error(f'Error while uploading file: {e}')
        return JSONResponse(
            status_code = status.HTTP_400_BAD_REQUEST,
            content = {
                'signal': ResponseSignal.FILE_UPLOAD_FAILED.value,
            }
        )
    
    return JSONResponse(
        content={
            'signal': ResponseSignal.FILE_UPLOAD_SUCCESS.value,
            'file_id': file_id
        }
    )

@data_router.post('/process/{project_id}')
async def process_endpoint(project_id: str, process_request: ProcessRequest):
    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size

    process_ctrl = ProcessController(project_id=project_id)

    file_content = process_ctrl.get_file_content(file_id=file_id)

    file_chunks = process_ctrl.process_file_content(
        file_id=file_id,
        file_content=file_content,
        chunk_size=chunk_size,
        overlap_size=overlap_size,
    )

    if file_chunks is None or len(file_chunks)==0:
        return JSONResponse(
            status_code = status.HTTP_400_BAD_REQUEST,
            content={
                'signal': ResponseSignal.PROCESSING_FAILED.value,
            }
        )

    return file_chunks