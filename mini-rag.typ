// Style inline code (single backtick)
#show raw.where(block: false): box.with(
  fill: rgb("#2222"),
  inset: (x: 3pt, y: 0pt),
  outset: (y: 3pt),
  radius: 25%,
)


=== Boilerplate Structure

+ Put `LICENSE` file for your license

+ At `README.md` file for all command & explaination for everything, imagine some human don't know anything and want to use your project.

+ All source code put it in `src/`

+ Add requirements.txt files contains all used libraries and their versions like ```py 
fastapi==0.141.1
uvicorn[standard]==0.52.4
``` and you can import them via ```bash pip install -r requirements.txt```

+ Add `.env` file UPPER_CASE keys for all your configurations & secret keys, copy `.env.example` from `.env` without adding any secret data. ```py
APP_NAME="Mini-RAG"
APP_VERSION="0.1"
FILE_ALLOWED_TYPES=["text/plain", "application/pdf"]
FILE_MAX_SIZE=10
```

+ Add `.gitignore` file for all files where you want to untracked by git and `.gitkeep` for uploading empty folders

+ Add folder `helpers/` containing `.env` handler like ```py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str
    FILE_ALLOWED_TYPES: list
    FILE_MAX_SIZE: int
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

def get_settings():
    return Settings()
```

+ Inside any folder create `__init__.py` file to collapsed importing chain like ```py from .enums.ResponseEnums import ResponseSignal ```

+ Add `assets/` contains data files like `API.yaml` & images & ..., can add `.gitignore` & `.gitkeep` files for improve tracking

+ Divide you Arch into MVC (Models Views Controllers), so create 3 dirs `Models/` everything related with data, `Views/` related with UI/UX, and `Controllers` related with logic and adding parent base inherting class containing shared data and functions needed in any child controller

+ For all const data, define them @ Enum like ```py
from enum import Enum
class ResponseSignal(Enum):
    FILE_VALIDATED_SUCCESS: str = "file_validate_successfully"
```




#pagebreak()

== Code

- Make `main.py` file with minimal code, just define `app` and its routes like ```py 
    from fastapi import FastAPI
    from routes import base
    app = FastAPI()
    app.include_router(base.base_router)
```

- Inside `routes/` define `files.py` for each endpoint and add `schemes/` inside `routes/` to define transfered JSON objects like ```bash
.
├── base.py
├── data.py
├── __init__.py
└── schemes
    ├── data.py
    └── __init__.py
```

- Inside each `endpiont.py`

    + Define route with tag (for docs) ```py
        data_router = APIRouter(
            prefix='/api/v1/data',
            tags=['api_v1', 'data'],
        )
    ```
    
    + Add logs logic by logging module ```py
        import logging
        logger = logging.getLogger('uvicorn.error')
        logger.error('Error while uploading file: ...')
    ```

    + If operation take data from project, define params with `Depends` fn in `fastapi` and make any endpoint `async` if needed like ```py
        @data_router.post('/upload/{project_id}')
        async def upload_data(project_id: str, file: UploadFile, 
                            app_settings: Settings = Depends(get_settings)):
        pass
    ```

    + make any operaiton return obj like `JSONResponse` to define status like ```py
        JSONResponse(
            status_code = status.HTTP_400_BAD_REQUEST,
            content = {
                'signal': ResponseSignal.FILE_UPLOAD_FAILED.value,
            }
        )
    ```
    
#pagebreak()

    + FastAPI was built on Starlette so initially if loaded file size > 1MB stored on hard disk @ `/tmp/`, so to save RAM storage load chunks and this store them @ your place like ```py
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
    ```
