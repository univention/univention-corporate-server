ARG ucs=latest
FROM docker-registry.knut.univention.de/phahn/ucs-aptbase:$ucs
ENV LANG C.UTF-8
RUN apt-get -qq update && \
	apt-get -qq install --no-install-recommends ca-certificates devscripts python-flake8 python3-apt python3-debian python3-flake8 python3-pip && \
	find /var/lib/apt/lists /var/cache/apt/archives -not -name lock -type f -delete
RUN pip3 install junit-xml
COPY . /usr/local/bin/
ENTRYPOINT ["/usr/local/bin/ucslint"]
