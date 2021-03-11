#docker run --rm -v $(pwd):/debbuilder phoenixportalbuilder bash -c 'yarn --cwd=frontend && yarn --cwd=frontend build && apt-get -q --assume-yes build-dep . && dpkg-buildpackage -uc -us -b  && cp ../*.deb .'

docker run --rm -v $(pwd):/debbuilder phoenixportalbuilder bash -c 'dpkg-buildpackage -uc -us -b  && cp ../*.deb .'
