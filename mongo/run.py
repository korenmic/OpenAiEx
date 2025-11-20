# run_app.py
import os

import uvicorn

from mongo.utils import get_mongo_host_port


def main() -> None:
    host, port = get_mongo_host_port()

    uvicorn.run(
        'app.server:app',
        host=host,
        port=port,
        reload=os.getenv('APP_RELOAD', 'false').lower() == 'true',
    )


if __name__ == '__main__':
    main()
