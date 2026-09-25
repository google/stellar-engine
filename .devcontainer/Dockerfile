# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM gcr.io/google.com/cloudsdktool/google-cloud-cli:stable

ARG TERRAFORM_VERSION=1.7.4
ARG TFLINT_VERSION=0.50.3
ARG TERRAGRUNT_VERSION=0.55.21

ENV DEBIAN_FRONTEND=noninteractive

# Install standard Dev Container common-utils packages and development utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    apt-transport-https \
    apt-utils \
    bash-completion \
    bzip2 \
    ca-certificates \
    curl \
    dialog \
    dirmngr \
    dnsutils \
    git \
    gnupg2 \
    htop \
    init-system-helpers \
    iproute2 \
    jq \
    less \
    locales \
    lsb-release \
    lsof \
    make \
    man-db \
    manpages \
    manpages-dev \
    nano \
    ncdu \
    net-tools \
    openssh-client \
    procps \
    psmisc \
    python3-pip \
    python3-venv \
    rsync \
    shellcheck \
    socat \
    strace \
    sudo \
    tree \
    unzip \
    vim-tiny \
    wget \
    xz-utils \
    zip \
    zsh \
  && ARCH="$(dpkg --print-architecture)" \
  && curl -fsSL "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_${ARCH}.zip" -o /tmp/terraform.zip \
  && unzip /tmp/terraform.zip -d /usr/local/bin \
  && rm -f /tmp/terraform.zip \
  && curl -fsSL "https://github.com/terraform-linters/tflint/releases/download/v${TFLINT_VERSION}/tflint_linux_${ARCH}.zip" -o /tmp/tflint.zip \
  && unzip /tmp/tflint.zip -d /usr/local/bin \
  && rm -f /tmp/tflint.zip \
  && curl -fsSL "https://github.com/gruntwork-io/terragrunt/releases/download/v${TERRAGRUNT_VERSION}/terragrunt_linux_${ARCH}" -o /usr/local/bin/terragrunt \
  && chmod +x /usr/local/bin/terragrunt \
  && rm -rf /var/lib/apt/lists/*

