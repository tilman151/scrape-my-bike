FROM public.ecr.aws/lambda/python@sha256:30f4b8ccdd8321fb9b22f0f32e688c225044497b1a4e82b53d3554efd452bab3 as build
RUN yum install -y unzip && \
    curl -Lo "/tmp/chromedriver.zip" "https://chromedriver.storage.googleapis.com/100.0.4896.60/chromedriver_linux64.zip" && \
    curl -Lo "/tmp/chrome-linux.zip" "https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F972765%2Fchrome-linux.zip?alt=media" && \
    unzip /tmp/chromedriver.zip -d /opt/ && \
    unzip /tmp/chrome-linux.zip -d /opt/

FROM public.ecr.aws/lambda/python@sha256:30f4b8ccdd8321fb9b22f0f32e688c225044497b1a4e82b53d3554efd452bab3
RUN yum install atk cups-libs gtk3 libXcomposite alsa-lib \
    libXcursor libXdamage libXext libXi libXrandr libXScrnSaver \
    libXtst pango at-spi2-atk libXt xorg-x11-server-Xvfb \
    xorg-x11-xauth dbus-glib dbus-glib-devel -y

COPY --from=build /opt/chrome-linux /opt/chrome
COPY --from=build /opt/chromedriver /opt/

RUN pip install poetry
RUN poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-dev

COPY scrape_my_bike ./scrape_my_bike

ENV PATH="/opt:${PATH}"

# Command can be overwritten by providing a different command in the template directly.
CMD ["scrape_my_bike.app.lambda_handler"]
