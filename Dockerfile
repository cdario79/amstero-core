FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV OPENCODE_VERSION=1.0.41

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    ca-certificates \
    gnupg \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
RUN /opt/venv/bin/pip install questionary cryptography
ENV PATH="/opt/venv/bin:${PATH}"

RUN apt-get update && apt-get install -y age && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install -y gh \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL "https://opencode.ai/install.sh" | sh \
    && ln -s /root/.opencode/bin/opencode /usr/local/bin/opencode

RUN git config --global init.defaultBranch main
RUN git config --global pull.rebase false
RUN gh config set editor git

RUN ln -s /workspace/repos/amstero-core/bin/am /usr/local/bin/am
ENV AMSTERO_ROOT=/workspace/amstero-core

WORKDIR /workspace

ENTRYPOINT ["bash", "-c", "if [ -f /workspace/repos/amstero-core/bin/entrypoint.sh ]; then chmod +x /workspace/repos/amstero-core/bin/entrypoint.sh && /workspace/repos/amstero-core/bin/entrypoint.sh; else /bin/bash; fi"]
CMD ["/bin/bash"]