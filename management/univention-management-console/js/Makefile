jsFiles=$(shell find . -name "*.js")

jslint: 
	jslint $(jsFiles)

doc:
	cd $(HOME)/dev/dojo-release-1.5.0-src/util/docscripts; rm cache/*; php generate.php umc2
	rm -rf $(HOME)/dev/dojo-api-viewer/data/*
	wget -O /dev/null --post-data 'api=http://10.200.26.20/dojo/util/docscripts/cache/api.xml&dir=' \
		http://10.200.26.20/api/lib/upload.php

all: jslint

.PHONY: jslint all doc
