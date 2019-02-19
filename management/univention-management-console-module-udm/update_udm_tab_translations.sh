#!/bin/bash

# get all labels for (not advanced) tabs
labels=$(
sed -n '/^\s*Tab.*/p' ../univention-directory-manager-modules/modules/univention/admin/handlers/*/*.py | \
	grep -v 'advanced\s*=\s*True' | \
	sed -n "s/[^_]*_(\s*'\([^']*\)'\s*).*/\1/p" | \
	sort | uniq
)

# get the translation
echo "$labels" | \
	while read label; do
		grep -h -A 2 "\"$label\"" ../univention-directory-manager-modules/modules/univention/admin/handlers/*/*.po | head -3 >> umc/js/de.po
	done

# transform into _('...') lines
txt=$(
echo "$labels" | \
	while read label; do
		echo "_('$label');"
	done
)

# add the pseudo translations as comments to .js file
sed -i '/\/\*\{5\} BEGIN \*\{5\}/,/\/\*\{5\} END \*\{5\}/d' umc/js/udm.js
cat >> umc/js/udm.js << EOF
/***** BEGIN *****
$txt
****** END ******/
EOF

