#!/bin/sh
#
# Setup Jenkins job "UCS Branch Test"
#
# <https://support.cloudbees.com/hc/en-us/articles/220857567-How-to-create-a-job-using-the-REST-API-and-cURL->
set -e -u
: "${SECRET:=$HOME/Private/jenkins-api}"
: "${URL:=https://jenkins.knut.univention.de:8181/job/UCS%20Branch%20Test/config.xml}"
: "${XML:=UCSBranchTest.xml}"
[ -n "${TOKEN:-}" ] || read -r TOKEN <"$SECRET"
exec curl -s -X POST "$URL" -u "$TOKEN" -H "Content-Type:text/xml" --data-binary @"$XML"
