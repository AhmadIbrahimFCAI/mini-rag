from fastapi import FastAPI, APIRouter, Depends
import os
from helpers.config import get_settings, Settings
from time import sleep
import logging
from tasks.mail_service import send_email_reports
from celery.result import AsyncResult
from celery_app import celery_app

logger = logging.getLogger('uvicorn')


base_router = APIRouter(
    prefix='/api/v1',
    tags=['api_v1'],
)


@base_router.get("/")
async def welcome(app_settings: Settings = Depends(get_settings)):

    app_name = app_settings.APP_NAME
    app_version = app_settings.APP_VERSION

    return {
        "app_name": app_name,
        "app_version": app_version,
    }

@base_router.get("/send_reports")
async def send_reports(app_settings: Settings = Depends(get_settings)):

    # ==== START ==== send reports
    task = send_email_reports.delay(
        mail_wait_seconds=3,
    )
    # ===== END ===== send reports

    return {
        'success': True,
        'task_id': task.id,
    }

@base_router.get("/send_reports/task-status/{task_id}")
async def get_send_report_task_status(task_id: str, app_settings: Settings = Depends(get_settings)):
    task_result = AsyncResult(task_id, app=celery_app)

    response_data = {
        "task_id": task_id,
        "state": task_result.state,
        "ready": task_result.ready(),
    }

    if task_result.state == "PROGRESS":
        response_data["progress_info"] = task_result.info
    elif task_result.ready():
        if task_result.successful():
            response_data["result"] = task_result.result
        else:
            response_data["error"] = str(task_result.result)
    else:
        response_data["progress_info"] = task_result.info


    return {
        'success': True,
        'data': response_data,
    }