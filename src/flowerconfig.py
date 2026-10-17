from helpers.config import get_settings
settings = get_settings()
# Flower configuration
port = 5555
max_tasks = 10000
auto_refresh = True
db = 'flower.db' # SQLite database for persistent storage

# Authentication
basic_auth = [ f'admin:{settings.CELERY_FLOWER_PASSWORD}' ]

