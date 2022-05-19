# Description
Script to import demo accounts.
This creates an example company with a small OU structure for different locations with roughly
- 60 users and computers
- 20 groups

# Process
- All files are copied from the local file to the UCS Primary:

      rsync -a data root@<ip>

- On the target host a customized import scripts is cerated for UDM:

      root@ucs-master:~/data# ./import.py > import.sh

- Start the import:

      root@ucs-master:~/data# sh import.sh

Import takes roughly 3-4 minutes.

# Pictures
Pictures were taken from [FreeDigitalPhotos.net](http://www.freedigitalphotos.net/images/search.php?search=faces)
