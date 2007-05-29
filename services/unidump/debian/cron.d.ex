#
# Regular cron jobs for the unidump package with strategie archiv (level 0 dump from Monday thru Friday
#
30 23 * * 1       export PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin; /usr/bin/unidump -strategy Monday | mail -e -s "Backup Montag" root
30 23 * * 2       export PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin; /usr/bin/unidump -strategy Tuesday | mail -e -s "Backup Dienstag" root
30 23 * * 3       export PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin; /usr/bin/unidump -strategy Wednesday | mail -e -s "Backup Mittwoch" root
30 23 * * 4       export PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin; /usr/bin/unidump -strategy Thursday | mail -e -s "Backup Donnerstag" root
30 23 * * 5       export PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin; /usr/bin/unidump -strategy Friday | mail -e -s "Backup Freitag" root

