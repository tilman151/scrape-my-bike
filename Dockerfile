FROM public.ecr.aws/lambda/python:3.9

RUN yum update -y
RUN yum install -y \
    gcc \
    openssl-devel \
    zlib-devel \
    libffi-devel \
    wget \
    unzip \
    libX11 && \
    yum -y clean all

RUN wget https://chromedriver.storage.googleapis.com/2.43/chromedriver_linux64.zip
RUN unzip chromedriver_linux64.zip

RUN curl -SL https://github.com/adieuadieu/serverless-chrome/releases/download/v1.0.0-55/stable-headless-chromium-amazonlinux-2017-03.zip > headless-chromium.zip
RUN unzip headless-chromium.zip
RUN rm *.zip
ENV CHROME_BINARY_LOC = "/var/task/headless-chromium"

ENV PATH="./:${PATH}"

RUN pip install poetry
RUN poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-dev

COPY fonts ./fonts
ENV FONTCONFIG_PATH="/var/task/fonts"

COPY scrape_my_bike ./scrape_my_bike

# Command can be overwritten by providing a different command in the template directly.
CMD ["scrape_my_bike.app.lambda_handler"]
