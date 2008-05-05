#!/bin/sh

email=$1

if [ -z "$email ]; then
	echo ""
	echo "Usage: $0 foobar@ucs.local"
	echo ""
	exit 1
fi


su - postgres -c "psql -d horde -c \"delete from horde_histories where history_who like '%${email}%'\";"
su - postgres -c "psql -d horde -c \"delete from horde_datatree where user_uid = '${email}'\";"
su - postgres -c "psql -d horde -c \"delete from horde_syncml_map where syncml_uid = '${email}'\";"

exit 0
