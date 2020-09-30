#!/bin/sed -nrf
# Convert DSC entries to file names

# Only collect Directory: and Files: and Checksums-ShaX:
/^Directory:|^ [[:xdigit:]]+ [[:digit:]]+ /{
  s/^Directory: /D/
  s/^ [[:xdigit:]]+ [[:digit:]]+ /F/
  H
  d
}
/^$/!d

# Switch hold and pattern space
x

# Move Directory: to front
s,((\nF[[:graph:]]+)+)(\nD[[:graph:]]+)\',\3\1,m

:next
# Eliminate duplicate files
s/(\nF[[:graph:]]+)(\nF[[:graph:]]+)*\1/\1\2/g
tnext
# Repeatedly print first entry
s,\`(\nD([[:graph:]]+))\nF([[:graph:]]+)$,\2/\3\1,m
T
P
s/[^\n]+//
bnext
