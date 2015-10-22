#!/bin/bash

DATE="${1:?Missing argument: date for file/directory names}"

if ! ls app/*/*.ini > /dev/null; then
	echo "ERROR: Please start from package directory."
	exit 1
fi

scp app/*/*.meta app/*/*_screenshot.* app/*/*_$DATE.{ini,png} omar:/mnt/omar/vmwares/mirror/appcenter.test/meta-inf/4.1/
ssh omar mkdir /mnt/omar/vmwares/mirror/appcenter.test/univention-repository/4.1/maintained/component/self-service-changepassword_$DATE
scp app/*/README* omar:/mnt/omar/vmwares/mirror/appcenter.test/univention-repository/4.1/maintained/component/self-service-changepassword_$DATE/

