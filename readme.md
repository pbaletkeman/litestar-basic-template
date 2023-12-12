### About
Sample Python 3.11.7 project which uses [Litestar](http://litestar.dev) - http://litestar.dev.
- Two database tables
- Utilizes a one-to-many relationship

### Install
- Ensure that you have Python Poetry installed - https://python-poetry.org/
- Activate Python Poetry
- Install Python pages by running `poetry update`

### Run
- Option 1 - execute `litestar --app main:app run` from the terminal
- Option 2 - execute `litestar --app main:app run --debug` from the terminal
- Option 3 - execute `uvicorn main:app` from the terminal
- Option 4 - execute `uvicorn main:app --log-config=log_config.yml` from the terminal

