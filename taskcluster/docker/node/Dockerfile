# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

ARG           NODE_VERSION
FROM          node:$NODE_VERSION

VOLUME /builds/worker/checkouts
VOLUME /builds/worker/objdir
VOLUME /builds/worker/.cache

RUN apt-get update -qq \
    && apt-get install -y \
    zip \
    python3 \
    python3-venv \
    python3-pip \
    && apt-get clean

# Add worker user
RUN mkdir -p /builds && \
    useradd -d /builds/worker -s /bin/bash -m worker -g 1000 -o -u 1000 && \
    groupadd -g 1000 -o worker && \
    mkdir /builds/worker/artifacts && \
    chown -R worker:worker /builds/worker

WORKDIR /builds/worker

# %include-run-task

COPY build.py /usr/local/bin/build.py
COPY test.py /usr/local/bin/test.py

ENV SHELL=/bin/bash \
    HOME=/builds/worker \
    PATH=/builds/worker/.local/bin:$PATH

# Set a default command useful for debugging
CMD ["/bin/bash", "--login"]
