# univention-skel
UCS - user default configuration manager

## univention-skel
The univention-skel command installs skeleton files into the user's home directory. Different to the conventional approach to copy the files from /etc/skel when the home directory is created, univention-skel keeps track of the files it installed for the user and updates them as long as they are not modified.
