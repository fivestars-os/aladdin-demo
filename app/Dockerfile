FROM alpine:3.6

# install python and pip with apk package manager
RUN apk -Uuv add python py-pip

# uwsgi in particular requires a lot of packages to install, delete them afterwards
RUN apk add --no-cache \
        gettext \
        python3 \
        build-base \
        linux-headers \
        python3-dev

# copies requirements.txt to the docker container
ADD requirements.txt requirements.txt

# Install requirements
RUN pip3 install --no-cache-dir -r requirements.txt

# clean up environment by deleting extra packages
RUN apk del \
        build-base \
        linux-headers \
        python3-dev

# specify the directory that CMD executes from
WORKDIR /home

# copy over the directory into docker container with given path
COPY . /home

# Create unprivileged user account
RUN addgroup aladdin-user && \
    adduser -SD -G aladdin-user aladdin-user

# Switch to the unpriveleged user account
USER aladdin-user

# run the application with uwsgi once the container has been created
ENTRYPOINT ["/bin/sh", "entrypoint.sh"]
