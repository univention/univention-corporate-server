FROM docker-registry.knut.univention.de/locustio/locust:master
USER root
RUN apt-get --quiet update && \
  DEBIAN_FRONTEND=noninteractive \
  apt-get --assume-yes --verbose-versions --no-install-recommends install \
    curl \
    && rm -rf /apt /var/lib/apt/lists/*
    # python3-bs4 \
    # python3-lxml \
RUN pip3 install bs4 lxml locust-plugins

