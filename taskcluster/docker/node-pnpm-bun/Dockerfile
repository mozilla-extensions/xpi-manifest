ARG DOCKER_IMAGE_PARENT
FROM $DOCKER_IMAGE_PARENT

ARG PNPM_VERSION
ARG BUN_VERSION

# Set shell
SHELL ["/bin/bash", "-c"]

# Install dependencies
RUN apt-get update && \
    apt-get install -y \
    rsync \
    jq
RUN curl -fsSL https://bun.sh/install | bash -s "bun-v${BUN_VERSION}"
RUN curl -fsSL https://get.pnpm.io/install.sh | bash

ENV PNPM_HOME=/builds/worker/.local/share/pnpm
ENV PATH=$PNPM_HOME:$PATH
ENV PATH=/builds/worker/.bun/bin:$PATH

# Set a default command useful for debugging
CMD ["/bin/bash", "--login"]
