### BUILD IMAGE ###
# Set up the build environment.  We need to build in a container that has everything
# needed to build and install our pip dependencies that have native parts, but we'd
# rather not include gcc et al. in the final service image since they're not needed
# to run the service.
FROM python:3.8-slim AS builder

# uwsgi in particular requires a lot of packages to install, delete them afterwards
RUN apt-get update && apt-get -y --no-install-recommends install \
        gettext \
        gcc \
        g++ \
        make \
        libc6-dev \
    && apt-get clean

# copies requirements.txt to the docker container
ADD requirements.txt requirements.txt

# Install requirements into ~/.local where they'll be easy to copy out.
RUN pip3 install --user --no-cache-dir -r requirements.txt
### END BUILD IMAGE ###


### SERVICE IMAGE ###
FROM python:3.8-slim

# Create unprivileged user account
RUN useradd -m -U -d /home/aladdin-user aladdin-user

# switch to the unpriveleged user account
USER aladdin-user

# specify the directory that CMD executes from
WORKDIR /srv

# Copy installed python packages from build image and include them in $PATH.
COPY --from=builder --chown=aladdin-user:aladdin-user /root/.local /home/aladdin-user/.local
ENV PATH /home/aladdin-user/.local/bin:$PATH

# display how old the python libraries are
RUN pip3 list --no-cache-dir --outdated

# copy over the directory into docker container with given path
COPY app /srv

# run the application with uwsgi once the container has been created
ENTRYPOINT ["/bin/sh", "entrypoint.sh"]
### END SERVICE IMAGE ###
