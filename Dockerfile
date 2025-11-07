FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y curl unzip nodejs npm awscli

RUN npm install -g axios

RUN echo "Installing OpenCode CLI..."

RUN curl -fsSL https://opencode.ai/install | bash

RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    chmod +x kubectl && \
    mv kubectl /usr/local/bin/

ENV PATH="/root/.opencode/bin:$PATH"
