ARG ucs=latest
FROM docker-registry.knut.univention.de/phahn/ucs-minbase:$ucs
ENV LANG C.UTF-8
RUN apt-get -qq update && \
	apt-get -qq install --no-install-recommends ca-certificates devscripts python3-apt python3-pip python3-setuptools python3-debian python3-junit.xml && \
	find /var/lib/apt/lists /var/cache/apt/archives -not -name lock -type f -delete
COPY . /build
RUN python3 -m pip install /build
ENTRYPOINT ["/usr/local/bin/ucslint"]
