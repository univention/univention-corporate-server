This PAM Module allows to run a script during the auth or the session
setup phase of the PAM authentication.

Available Options
-----------------

* `save_pass`:
    save the credentials (password) during the auth phase for later
    usage during the session setup phase.

* `export_pass`:
    the credentials (password) of the user will be
    exported in the environment variable `PASSWD`, if available.

* `program=<filename>*:
    absolute path of the program or file to execute.

* `silent`:
    no messages.

* `user`:
    execute program as regular PAM user.

* `demouser=<user>`:
    intercept given user and use user `<user>-<hostname>` instead.

* `demouserscript=<filename>`:
    absolute path of extra program or file to execute when `demouser` matches.

Example
-------

Here is a sample /etc/pam.d/login file for Debian GNU/Linux 3.0:

    auth       requisite  pam_securetty.so
    auth       sufficient pam_ldap.so
    auth       required   pam_pwdb.so
    auth       optional   pam_group.so
    auth       optional   pam_mail.so
    auth       optional   pam_runasroot.so save_pass program=/usr/bin/prepare_remote.sh
    account    requisite  pam_time.so
    account    sufficient pam_ldap.so
    account    required   pam_pwdb.so
    session    required   pam_mkhomedir.so skel=/etc/skel/ umask=0022
    session    required   pam_runasroot.so export_pass program=/usr/bin/mountdrives.sh
    session    required   pam_pwdb.so
    session    optional   pam_lastlog.so
    password   required   pam_pwdb.so
