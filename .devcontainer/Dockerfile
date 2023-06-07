FROM alpine/helm:latest

ARG DEV_USER

# Install base packages
RUN apk add --upgrade --no-cache \
  bash curl make gcc g++ openssl openssh git bash-completion ncurses perl gnupg util-linux shadow \
  python3 docker docker-cli-compose docker-cli-buildx \
  && ln -sf python3 /usr/bin/python

# Install Python modules
RUN python3 -m ensurepip
COPY ./archivist/requirements.txt /requirements.txt
RUN python3 -m pip install --no-cache --upgrade -r /requirements.txt
RUN python3 -m pip install --no-cache --upgrade awscli==1.27.142 awscli-plugin-endpoint==0.4 setuptools==67.8.0

# Install Kubectx
RUN git clone https://github.com/ahmetb/kubectx /opt/kubectx \
  && mv /opt/kubectx/kubectx /usr/local/bin/kubectx \
  && mv /opt/kubectx/kubens /usr/local/bin/kubens
# Install direnv
RUN curl -sfL https://direnv.net/install.sh | bash
# Install Vault
COPY --from=vault:latest /bin/vault /bin/vault
# Install Kubectl
COPY --from=bitnami/kubectl:1.21.8 /opt/bitnami/kubectl/bin/kubectl /usr/bin/kubectl

# Create custom user
RUN adduser -h /home/${DEV_USER} -s /bin/bash -u 1000 -D ${DEV_USER}
# Copy custom scripts to home directory
COPY --chown=${DEV_USER}:${DEV_USER} ./.devcontainer/.bashrc /home/${DEV_USER}/.bashrc
COPY --chown=${DEV_USER}:${DEV_USER} ./.devcontainer/.profile /home/${DEV_USER}/.profile
# Hook direnv into shell
RUN direnv hook bash >> /home/${DEV_USER}/.bashrc
# Create VSCode folder
RUN mkdir -p /home/${DEV_USER}/.vscode-server/extensions \
  /home/${DEV_USER}/.vscode-server-insiders/extensions
RUN chown -R ${DEV_USER} \
  /home/${DEV_USER}/.vscode-server \
  /home/${DEV_USER}/.vscode-server-insiders

RUN groupmod -g 990 ping
RUN TEST=$(grep 'docker:' /etc/group | cut -d : -f 3); \
  if [ -z ${TEST} ]; then addgroup -g 999 docker && addgroup -g 998 docker2; \
  elif [ ! ${TEST} -eq 999 ] && [ ! ${TEST} -eq 998 ]; then groupmod -g 999 docker && addgroup -g 998 docker2; \
  elif [ ${TEST} -eq 999 ]; then addgroup -g 998 docker2; \
  elif [ ${TEST} -eq 998 ]; then addgroup -g 999 docker2; fi \
  && addgroup ${DEV_USER} docker \
  && addgroup ${DEV_USER} docker2

# Clean up
RUN rm -rf /tmp/* && rm -rf /opt/*

USER ${DEV_USER}

RUN mkdir -p /home/${DEV_USER}/.aws

# Install and configure fzf
RUN git clone --depth 1 https://github.com/junegunn/fzf.git /home/${DEV_USER}/.fzf \
  && /home/${DEV_USER}/.fzf/install --all

ENTRYPOINT [ "sleep", "infinity" ]
