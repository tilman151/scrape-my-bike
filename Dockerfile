FROM public.ecr.aws/lambda/python:3.9

COPY dist/scrape_my_bike-0.1.0-py3-none-any.whl ./

RUN python3.9 -m pip install scrape_my_bike-0.1.0-py3-none-any.whl

# Command can be overwritten by providing a different command in the template directly.
CMD ["scrape_my_bike.app.lambda_handler"]
