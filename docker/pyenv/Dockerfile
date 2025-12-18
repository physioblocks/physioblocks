FROM debian:latest

ENV HOME="/root"
WORKDIR $HOME
ENV PYENV_ROOT="$HOME/.pyenv"
ENV PATH="$PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH"
RUN echo $PYENV_ROOT
RUN echo $PATH

# get ca certificates to be able to get pyenv
RUN apt-get update \
    && apt-get install -y ca-certificates

# install recommended environment for pyenv
RUN apt-get update \
    && apt-get install -y --no-install-recommends make build-essential \
    libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev curl \
    git libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev \
    liblzma-dev

# install pyenv
RUN curl https://pyenv.run | bash \ 
    && pyenv update

# install python versions 3.10 to 3.14
RUN pyenv install 3.10 \
    && pyenv install 3.11 \
    && pyenv install 3.12 \
    && pyenv install 3.13 \
    && pyenv install 3.14 \
    && pyenv global 3.10 3.11 3.12 3.12 3.13
