# run_app.py
import os

import uvicorn

from mongo.utils import get_mongo_host_port
from utils.consts import APP_RELOAD_ENV, ENVIRONMENT_DEFAULTS


def main() -> None:
    host, port = get_mongo_host_port()

    reload_flag = os.getenv(APP_RELOAD_ENV, str(ENVIRONMENT_DEFAULTS[APP_RELOAD_ENV]))
    reload_bool = reload_flag.lower() == 'true'

    uvicorn.run(
        'mongo.server:app',
        host=host,
        port=port,
        reload=reload_bool,
    )


if __name__ == '__main__':
    main()
