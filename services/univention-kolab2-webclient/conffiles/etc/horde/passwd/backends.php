<?php

@%@BCWARNING=#@%@

/**
 * $Horde: passwd/config/backends.php.dist,v 1.41.2.1 2007/02/15 18:19:22 jan Exp $
 *
 * This file is where you specify what backends people use to change
 * their passwords. There are a number of properties that you can set
 * for each backend:
 *
 * name: This is the plaintext, english name that you want displayed
 *       to people if you are using the drop down server list.  Also
 *       displayed on the main page (input form).
 *
 * password policy: The password policies for this backend. You are responsible
 *                  for the sanity checks of these options. Options are:
 *              minLength   Minimum length of the password
 *              maxLength   Maximum length of the password
 *              maxSpace    Maximum number of white space characters
 *
 *                  The following are the types of characters required
 *                  in a password.  Either specific characters, character
 *                  classes, or both can be required.  Specific types are:
 *
 *              minUpper    Minimum number of uppercase characters
 *              minLower    Minimum number of lowercase characters
 *              minNumeric  Minimum number of numeric characters (0-9)
 *              minAlphaNum Minimum number of alphanumeric characters
 *              minAlpha    Minimum number of alphabetic characters
 *              minSymbol   Minimum number of alphabetic characters
 *
 *                  Alternatively (or in addition to), the minimum number of
 *                  character classes can be configured by setting the
 *                  following.  The valid range is 0 through 4 character
 *                  classes may be required for a password. The classes are:
 *                  'upper', 'lower', 'number', and 'symbol'.  For example:
 *                  A password of 'p@ssw0rd' satisfies three classes ('number',
 *                  'lower', and 'symbol'), while 'passw0rd' only satisfies
 *                  two classes ('lower' and 'symbols').
 *
 *              minClasses  Minimum number (0 through 4) of character classes.
 *
 * driver:    The Passwd driver used to change the password. Valid
 *            Valid values are currently:
 *              ldap         Change the password on a ldap server
 *              smbldap      Change the password on a ldap server for both
 *                           ldap and samba auth
 *              sql          Change the password for sql authentication
 *                           (exim, pam_mysql, horde)
 *              poppassd     Change the password via a poppassd server
 *              smbpasswd    Change the password via the smbpasswd command
 *              expect       Change the password via an expect script
 *              vmailmgr     Change the password via a local vmailmgr daemon
 *              vpopmail     Change the password for sql based vpopmail
 *              servuftp     Change the password via a servuftp server
 *              pine         Change the password in a Pine-encoded file
 *              composite    Allows you to chain multiple drivers together
 *
 * no_reset:  Do not reset the authenticated user's credentials on success.
 *
 * params:    A params array containing any additional information that the
 *            Passwd driver needs.
 *
 *            The following is a list of supported encryption/hashing
 *            methods supported by Passwd.
 *
 *            1) plain
 *            2) crypt or crypt-des
 *            3) crypt-md5
 *            4) crypt-blowfish
 *            5) md5-hex
 *            6) md5-base64
 *            7) smd5
 *            8) sha
 *            9) ssha
 *
 *            Currently, md5-base64, smd5, sha, and ssha require the
 *            mhash php library in order to work properly.  See the
 *            INSTALL file for directions on enabling this.  md5
 *            passwords have caused some problems in the past because
 *            there are different definitions of what is a "md5
 *            password".  Systems implement them in a different
 *            manner.  If you are using OpenLDAP as your backend or
 *            have migrated your passwords from your OS based passwd
 *            file, you will need to use the md5-base64 hashing
 *            method.  If you are using a SQL database or used the PHP
 *            md5() method to create your passwords, you will need to
 *            use the md5-hex hashing method.
 *
 * preferred: This is only useful if you want to use the same
 *            backend.php file for different machines: if the Hostname
 *            of the Passwd Machine is identical to one of those in
 *            the preferred list, then the corresponding option in the
 *            select box will include SELECTED, i.e. it is selected
 *            per default. Otherwise the first entry in the list is
 *            selected.
 *
 * show_encryption: If you are using the sql or the vpopmail backend
 *                  you have the choice whether or not to store the
 *                  encryption type with the password. If you are
 *                  using for example an SQL based PAM you will most
 *                  likely not want to store the encryption type as it
 *                  would cause PAM to never match the passwords.
 *
 */

$backends['expect'] = array(
    'name' => 'Kerberos Server',
    'preferred' => '',
    'password policy' => array(),
    'driver' => 'expect',
    'params' => array(
        'program' => '/usr/bin/expect',
        'script' => dirname(__FILE__) . '/../scripts/kpasswd_expect',
        'params' => '',
    )
);

