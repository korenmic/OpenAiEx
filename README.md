To run:
```
sudo apt install python3-venv
python3 -m virtualenv .venv
source .venv/bin/activate
```

Then, either run the app and the mongo servers like this (each in its own separate shell/process):
```
uvicorn mongo.server:app --host 0.0.0.0 --port 8001 --reload
uvicorn app.server:app --host 0.0.0.0 --port 8000 --reload
```

If you run the mongo on a different ip address, then run the app like this instead:
```
MONGO_HOST_DEFAULT_VALUE=<IP> MONGO_PORT_DEFAULT_VALUE=<PORT> uvicorn app.server:app --host 0.0.0.0 --port 8000 --reload
```

To make sure everything is working, run `pytest` on an activated venv, for now from the same host as the app
TODO - will be fixed, env variable passable, then this comment will be removed.

Remaining goals:
 - Auto initate mongo database if missing
 - Add block
 - Add undo block
