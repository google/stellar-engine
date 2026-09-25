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
  && case "${ARCH}" in \
       amd64) \
         TF_SHA256="285539a6fd62fb79f05edc15cc207ca90f282901c32261085ea0642a0d638dfd"; \
         TFLINT_SHA256="70d66470f161ed48e6da0c58dc61787eced1ebd02397618424b8a55ff67f465f"; \
         TG_SHA256="adc30ed8f50f946628dd828223df983144d78ff8b81b1965867200197aac22c8" \
         ;; \
       arm64) \
         TF_SHA256="36680616b54c5ce8c8222c7bf81c187727b3c5c1a3a6e3af5b5372caa28697b7"; \
         TFLINT_SHA256="46b04f8f793e5ff96b74948b993588e5f48476534b570216ad303951fa3ee1e3"; \
         TG_SHA256="da5df9061bed81850d38ef104740d041fcec9ee788b3a8163cd503c76d77976e" \
         ;; \
       *) echo "Unsupported architecture: ${ARCH}" >&2; exit 1 ;; \
     esac \
  && curl -fsSL "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_${ARCH}.zip" -o /tmp/terraform.zip \
  && echo "${TF_SHA256}  /tmp/terraform.zip" | sha256sum -c - \
  && unzip /tmp/terraform.zip -d /usr/local/bin \
  && rm -f /tmp/terraform.zip \
  && curl -fsSL "https://github.com/terraform-linters/tflint/releases/download/v${TFLINT_VERSION}/tflint_linux_${ARCH}.zip" -o /tmp/tflint.zip \
  && echo "${TFLINT_SHA256}  /tmp/tflint.zip" | sha256sum -c - \
  && unzip /tmp/tflint.zip -d /usr/local/bin \
  && rm -f /tmp/tflint.zip \
  && curl -fsSL "https://github.com/gruntwork-io/terragrunt/releases/download/v${TERRAGRUNT_VERSION}/terragrunt_linux_${ARCH}" -o /usr/local/bin/terragrunt \
  && echo "${TG_SHA256}  /usr/local/bin/terragrunt" | sha256sum -c - \
  && chmod +x /usr/local/bin/terragrunt \
  && rm -rf /var/lib/apt/lists/*

