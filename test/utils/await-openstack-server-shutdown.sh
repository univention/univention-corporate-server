#!/bin/bash
if [ "$#" -eq 0 ]
    then exit 1
fi
while [[ "$status" != *"SHUTOFF"* ]]
do
    sleep 2s
    status=`openstack server show $1 | grep status`
done
