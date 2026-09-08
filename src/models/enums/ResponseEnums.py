from enum import Enum

class ResponseSignal(Enum):

    FILE_VALIDATED_SUCCESS: str = "file_validate_successfully"
    FILE_TYPE_NOT_SUPPORTED: str = "file_type_not_supported"
    FILE_SIZE_EXCEEDED: str = "file_size_exceeded"
    FILE_UPLOAD_SUCCESS: str = "file_upload_success"
    FILE_UPLOAD_FAILED: str = "file_upload_failed"

    PROCESSING_FAILED: str = "processing_failed"
    PROCESSING_SUCCESS: str = "processing_success"