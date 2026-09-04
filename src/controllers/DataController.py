from .BaseConroller import BaseController
from fastapi import UploadFile
from models import ResponseSignal
from .ProjectController import ProjectController
import re, os

class DataController(BaseController):

    def __init__(self):
        super().__init__()
        self.size_scale_bit = 20    # convert MB to bytes via left-shift operator

    def validate_upload_file(self, file: UploadFile):

        if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES:
            return False, ResponseSignal.FILE_TYPE_NOT_SUPPORTED.value

        if file.size > self.app_settings.FILE_MAX_SIZE << self.size_scale_bit:
            print(file.size)
            return False, ResponseSignal.FILE_SIZE_EXCEEDED.value

        return True, ResponseSignal.FILE_VALIDATED_SUCCESS.value

    def generate_unique_filename(self, org_filename: str, project_id: str, ):

        project_path = ProjectController().get_project_path(project_id=project_id)

        cleaned_filename = self.get_clean_filename(org_filename=org_filename)

        new_file_path = self.get_semi_filename(
            project_path=project_path,
            cleaned_filename=cleaned_filename,
        )


        while os.path.exists(new_file_path):
            new_file_path = self.get_semi_filename(
                project_path=project_path, 
                cleaned_filename=cleaned_filename
            )

        return new_file_path

    def get_semi_filename(self, project_path, cleaned_filename):
        random_filename = self.generate_random_string()
        new_file_path = os.path.join(
            project_path,
            random_filename + '_' + cleaned_filename
        )
        return new_file_path

    def get_clean_filename(self, org_filename: str,):

        # remove any special characters, except underscore and .
        cleaned_filename = re.sub(r'[^\w.]', '', org_filename)

        # replace spaces with underscore
        cleaned_filename = cleaned_filename.replace(' ', '_')

        return cleaned_filename