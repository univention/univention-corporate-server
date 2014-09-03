#!/bin/bash
## title: Consistency of UCR templates
## description: Verifys whether all installed UCR templates are in their original state


output=$("univention-check-templates" 2>/dev/null)
if [ $? != 0 ]; then
	echo -e 'The following UCR templates have been modified, moved or are missing:\n'
	for line in $output; do
		echo $line
	done
	echo 'summary: Modified UCR templates found'
	exit 1
fi
echo "No modified UCR templates found"
