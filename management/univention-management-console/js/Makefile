jsFiles=$(shell find . -name "*.js")

jslint: 
	jslint $(jsFiles)

doc:
	cd $(HOME)/dev/dojo-release-1.5.0-src/util/docscripts; rm cache/*; php generate.php umc
	rm -rf $(HOME)/dev/dojo-api-viewer/data/*
	wget -O /dev/null --post-data 'api=http://10.200.26.20/dojo/util/docscripts/cache/api.xml&dir=' \
		http://10.200.26.20/api/lib/upload.php

all: jslint

sync: build
#	git push root@10.200.15.10:/root/umc-js
	rsync -vrlt --delete --exclude .git --exclude "*~" --exclude .svn --exclude '.*.sw*' . root@10.200.15.10:/root/umc-js
#	rsync -vrlt --delete --exclude .git --exclude .svn --exclude '.*.sw*' --exclude 'roomadmin.js*' --exclude 'TabbedModule.js*' . root@10.200.15.10:/root/umc-js

syncsvn:
	rsync -vrlt --delete --exclude '*~' --exclude ".*.sw*" --exclude ".git" --exclude ".svn" . /home/aklaeser/svn/dev/branches/ucs-3.0/ucs/management/univention-management-console/js/

build:
	for idir in umc css; do \
		find . -maxdepth 1 -type l -a -name "$${idir}_*" -delete; \
		ln -s $$idir "$${idir}_$$(date +'%Y%d%m%H%M%S')"; \
	done;

.PHONY: jslint all doc sync syncsvn build
