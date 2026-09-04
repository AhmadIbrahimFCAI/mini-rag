from .BaseConroller import BaseController
from fastapi import UploadFile


class DataController(BaseController):

    def __init__(self):
        super().__init__()
        self.size_scale_bit = 20    # convert MB to bytes via left-shift operator

    def validate_upload_file(self, file: UploadFile):

        if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES:
            return False

        if file.size > self.app_settings.FILE_MAX_SIZE << self.size_scale_bit:
            return False

        return True