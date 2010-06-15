#!/bin/sh

email=$1

if [ -z "$email" ]; then
	echo ""
	echo "Usage: $0 foobar@ucs.local"
	echo ""
	exit 1
fi


mkdir -p "/var/cache/horde/$email"
user_prefix=$(echo $email | sed -e 's|@.*||')

grep -o :\"user/${user_prefix}/ /var/cache/horde/kolab_cache* 2>/dev/null | sed -e 's|:.*||' | while read f; do
 mv -v "$f" "/var/cache/horde/$email/"
done

su - postgres -c "psql -d horde -c \"delete from horde_histories where history_who like '%${email}%'\";"
su - postgres -c "psql -d horde -c \"delete from horde_datatree where user_uid = '${email}'\";"
su - postgres -c "psql -d horde -c \"delete from horde_syncml_map where syncml_uid = '${email}'\";"
su - postgres -c "psql -d horde -c \"delete from horde_syncml_anchors where syncml_uid = '${email}'\";"

exit 0
