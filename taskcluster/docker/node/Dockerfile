# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

ARG           NODE_VERSION
FROM          node:$NODE_VERSION
MAINTAINER    Aki Sasaki <aki@mozilla.com>

RUN echo "deb http://deb.debian.org/debian testing main" >> /etc/apt/sources.list
RUN apt-get update -qq \
    && apt-get install -y zip \
    && apt-get install -y python3 \
    && apt-get install -y python3-venv \
    && apt-get install -y python3-pip \
    && apt-get clean

# Add worker user
RUN mkdir /builds && \
    useradd -d /builds/worker -s /bin/bash -m worker -g 1000 -o -u 1000 && \
    groupadd -g 1000 -o worker && \
    mkdir /builds/worker/artifacts && \
    chown worker:worker /builds/worker/artifacts

# %include-run-task

COPY build.py /usr/local/bin/build.py
COPY test.py /usr/local/bin/test.py

ENV SHELL=/bin/bash \
    HOME=/builds/worker \
    PATH=/builds/worker/.local/bin:$PATH

VOLUME /builds/worker/checkouts
VOLUME /builds/worker/.cache

# Set a default command useful for debugging
CMD ["/bin/bash", "--login"]
