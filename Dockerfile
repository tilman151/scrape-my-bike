FROM public.ecr.aws/lambda/python:3.9

RUN pip install poetry
RUN poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-dev

COPY scrape_my_bike ./scrape_my_bike

# Command can be overwritten by providing a different command in the template directly.
CMD ["scrape_my_bike.app.lambda_handler"]
