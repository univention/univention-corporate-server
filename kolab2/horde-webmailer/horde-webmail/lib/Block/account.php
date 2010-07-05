<?php

$block_name = _("Account Information");

/**
 * $Horde: horde/lib/Block/account.php,v 1.7.2.10 2009-01-06 15:24:52 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Eric Jon Rostetter <eric.rostetter@physics.utexas.edu>
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.1
 * @package Horde_Block
 */
class Horde_Block_Horde_account extends Horde_Block {

    var $_app = 'horde';

    /**
     * The title to go in this block.
     *
     * @return string   The title text.
     */
    function _title()
    {
        return _("My Account Information");
    }

    /**
     * The content to go in this block.
     *
     * @return string   The content
     */
    function _content()
    {
        global $registry, $conf;

        switch ($conf['accounts']['driver']) {
        case 'null':
            $mydriver = new Accounts_Driver();
            break;

        case 'localhost':
        case 'finger':
        case 'ldap':
        case 'kolab':
            $class = 'Accounts_Driver_' . $conf['accounts']['driver'];
            $mydriver = new $class($conf['accounts']['params']);
            break;

        default:
            return '';
        }

        // Check for password status.
        if (is_a($status = $mydriver->checkPasswordStatus(), 'PEAR_Error')) {
            $status = $status->getMessage();
        }

        if (is_a($username = $mydriver->getUsername(), 'PEAR_Error')) {
            return $username->getMessage();
        }
        $table = array(_("Login") => $username);
        if (is_a($fullname = $mydriver->getFullname(), 'PEAR_Error')) {
            return $fullname->getMessage();
        } elseif ($fullname) {
            $table[_("Full Name")] = $fullname;
        }
        if (is_a($home = $mydriver->getHome(), 'PEAR_Error')) {
            return $home->getMessage();
        } elseif ($home) {
            $table[_("Home Directory")] = $home;
        }
        if (is_a($shell = $mydriver->getShell(), 'PEAR_Error')) {
            return $shell->getMessage();
        } elseif ($shell) {
            $table[_("Default Shell")] = $shell;
        }
        if (is_a($quota = $mydriver->getQuota(), 'PEAR_Error')) {
            return $quota->getMessage();
        } elseif ($quota) {
            $table[_("Quota")] = sprintf(_("%.2fMB used of %.2fMB allowed (%.2f%%)"),
                                         $quota['used'] / ( 1024 * 1024.0),
                                         $quota['limit'] / ( 1024 * 1024.0),
                                         ($quota['used'] * 100.0) / $quota['limit']);
        }
        if (is_a($lastchange = $mydriver->getPasswordChange(), 'PEAR_Error')) {
            return $lastchange->getMessage();
        } elseif ($lastchange) {
            $table[_("Last Password Change")] = $lastchange;
        }

        $output = '<table class="item" width="100%" cellspacing="1">';

        if (!empty($status)) {
            $output .= '<tr><td colspan="2"><p class="notice">' .
                Horde::img('alerts/warning.png', _("Warning")) .
                '&nbsp;&nbsp;' . $status . '</p></td></tr>';
        }

        foreach ($table as $key => $value) {
            $output .= "<tr class=\"text\"><td>$key</td><td>$value</td></tr>\n";
        }
        $output .= "</table>\n";

        if ($registry->get('status', 'forwards') != 'inactive' &&
            $registry->hasMethod('summary', 'forwards')) {
            $summary = $registry->callByPackage('forwards', 'summary');
            if (!is_a($summary, 'PEAR_Error')) {
                $output .= '<br />' . $summary . "\n";
            }
        }
        if ($registry->get('status', 'vacation') != 'inactive' &&
            $registry->hasMethod('summary', 'vacation')) {
            $summary = $registry->callByPackage('vacation', 'summary');
            if (!is_a($summary, 'PEAR_Error')) {
                $output .= '<br />' . $summary . "\n";
            }
        }

        return $output;
    }

}

/**
 * Accounts_Driver:: defines an API for getting/displaying account information
 * for a user for the accounts module.
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Eric Jon Rostetter <eric.rostetter@physics.utexas.edu>
 * @since   Horde 3.1
 * @package Horde_Block
 */
class Accounts_Driver {

    /**
     * Error string returned to user if an error occurs.
     *
     * @var string
     */
    var $err_str;

    /**
     * Returns the username.
     *
     * @return string  The lowercased username.
     *
     */
    function getUsername()
    {
        return String::lower(Auth::getBareAuth());
    }

    /**
     * Returns the user realm.
     *
     * @return string  The user realm.
     */
    function getRealm()
    {
        return (string)Auth::getAuthDomain();
    }

    /**
     * Returns the user's quota if available.
     *
     * @return mixed  A quota array, elements are used bytes and limit bytes on
     *                success, false on failure.
     */
    function getQuota()
    {
        return false;
    }

    /**
     * Returns the user's full name.
     *
     * @return mixed  The user's full name (string), or false (error).
     */
    function getFullname()
    {
        return false;
    }

    /**
     * Returns the user's home (login) directory.
     *
     * @return mixed  The user's directory (string), or false (error).
     */
    function getHome()
    {
        return false;
    }

    /**
     * Returns the user's default shell.
     *
     * @return mixed  The user's shell (string), or false (error).
     */
    function getShell()
    {
        return false;
    }

    /**
     * Returns the date of the user's last password change.
     *
     * @return mixed  Date string (string) or false (error).
     */
    function getPasswordChange()
    {
        return false;
    }

    /**
     * Returns the status of the current password.
     *
     * @return mixed  A string with a warning message if the password is about
     *                to expire, PEAR_Error on error and false otherwise.
     */
    function checkPasswordStatus()
    {
        return false;
    }

}

/**
 * Implements the Accounts API for servers with unix accounts on the localhost
 * machine (same machine as the web server).  Should work for local unix
 * accounts, nis/nis+ accounts, or any PAM oriented accounts that appear as
 * local accounts on the local machine.  The exception is the quota support.
 * See that routine for additional comments.
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Eric Jon Rostetter <eric.rostetter@physics.utexas.edu>
 * @since   Horde 3.1
 * @package Horde_Block
 */
class Accounts_Driver_localhost extends Accounts_Driver {

    /**
     * Hash containing connection parameters.
     *
     * @var array
     */
    var $params = array();

    /**
     * Constructor.
     *
     * @param array $params  Hash containing connection parameters.
     */
    function Accounts_Driver_localhost($params = array())
    {
        $this->params = $params;
        if (!isset($this->params['quota_path'])) {
            $this->params['quota_path'] = 'quota';
        }
        if (!isset($this->params['grep_path'])) {
            $this->params['grep_path'] = 'grep';
        }
    }

    /**
     * Returns the user account from the posix information.
     *
     * @return array  A hash with complete account details.
     */
    function _getAccount()
    {
        static $information;

        if (!isset($information)) {
            // this won't work if we don't have posix extensions
            if (!Util::extensionExists('posix')) {
                return PEAR::raiseError(_("POSIX extension is missing"));
            }

            $user = String::lower($this->getUsername());
            $information = posix_getpwnam($user);
        }

        return $information;
    }

    /**
     * Implement the Quota API for IMAP servers with a unix quota command.
     * This may require a modified "quota" command that allows the httpd
     * server account to get quotas for other users...  It requires that your
     * web server and user server be the same server or at least have shared
     * authentication and file servers (e.g. via NIS/NFS).  And last, it (as
     * written) requires the posix php extensions.
     *
     * If your quota command wraps the output onto two lines, then this module
     * will only work if you have a grep which supports the -A switch, and you
     * append an -A1 switch to your grep_path (e.g. '/bin/grep -A1').
     *
     * @return mixed  The quota hash (bytes used, limit) or false for error.
     */
    function getQuota()
    {
        $information = $this->_getAccount();
        if (is_a($information, 'PEAR_Error')) {
            return $information;
        }

        $homedir = $information['dir'];

        // If we want mount point translations, then translate the login dir
        // name to a mount point.  If not, then simply parse out the device
        // name from the login directory, and use that instead.
        if ($this->params['translateMountPoint'] &&
            file_exists($this->params['translationTable'])) {
            require_once 'File/Fstab.php';
            $sysTab = File_Fstab::singleton($this->params['translationTable']);
            do {
                $entry = $sysTab->getEntryForPath($homedir);
                $homedir = dirname($homedir);
                if ($homedir == '.' || empty($homedir)) {
                    $homedir = '/';
                }
            } while (is_a($entry, 'PEAR_Error'));
            $mountPoint = $entry->device;
        } else {
            $homedir = explode('/', $homedir);
            $mountPoint = '/' . $homedir[1];
        }

        $cmdline = sprintf('%s -u %s 2>&1 | %s %s',
                           $this->params['quota_path'],
                           $this->getUserName(),
                           $this->params['grep_path'],
                           $mountPoint);
        $junk = exec($cmdline, $quota_data, $return_code);
        if ($return_code == 0 && !empty($quota_data[0])) {
            // In case of quota output wrapping on two lines, we concat the
            // second line of results, if any, here.
            if (!empty($quota_data[1])) {
                $quota_data[0] .= $quota_data[1];
            }
            // Now parse out the quota info and return it.
            $quota = preg_split('/\s+/', trim($quota_data[0]));
            return array('used' => $quota[1] * 1024, 'limit' => $quota[2] * 1024);
        }

        return false;
    }

    /**
     * Returns the user's full name.
     *
     * @return mixed  The user's full name (string), or false (error).
     */
    function getFullname()
    {
        $information = $this->_getAccount();
        if (is_a($information, 'PEAR_Error')) {
            return $information;
        }
        $gecos_array = explode(',', $information['gecos']);
        return $gecos_array[0];
    }

    /**
     * Returns the user's home (login) directory.
     *
     * @return mixed  The user's directory (string), or false (error).
     */
    function getHome()
    {
        $information = $this->_getAccount();
        if (is_a($information, 'PEAR_Error')) {
            return $information;
        }
        return $information['dir'];
    }

    /**
     * Returns the user's default shell.
     *
     * @return mixed  The user's shell (string), or false (error).
     */
    function getShell()
    {
        $information = $this->_getAccount();
        if (is_a($information, 'PEAR_Error')) {
            return $information;
        }
        return $information['shell'];
    }

}

/**
 * The ldap class attempts to return user information stored in an ldap
 * directory service.
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Eric Jon Rostetter <eric.rostetter@physics.utexas.edu>
 * @since   Horde 3.1
 * @package Horde_Block
 */
class Accounts_Driver_ldap extends Accounts_Driver {

    /**
     * Pointer to the ldap connection.
     *
     * @var resource
     */
    var $_ds;

    /**
     * Hash containing connection parameters.
     *
     * @var array
     */
    var $_params;

    /**
     * Constructs a new Accounts_Driver_ldap object.
     *
     * @param array $params  A hash containing connection parameters.
     */
    function Accounts_Driver_ldap($params = array())
    {
        $this->_params = array_merge(
            array('host' => 'localhost',
                  'port' => 389,
                  'basedn' => '',
                  'attr' => 'uid',
                  'version' => '3',
                  'strip' => false,
            ),
            $params);
    }

    /**
     */
    function _bind()
    {
        if (is_resource($this->_ds) && get_resource_type($this->_ds) == 'ldap link') {
            return true;
        }

        // Connect to the LDAP server.
        $this->_ds = ldap_connect($this->_params['host'],
                                  $this->_params['port']);
        if (!$this->_ds) {
            return PEAR::raiseError(_("Could not connect to LDAP server."));
        }
        if (isset($this->_params['version'])) {
            if (!ldap_set_option($this->_ds, LDAP_OPT_PROTOCOL_VERSION,
                                 $this->_params['version'])) {
                Horde::logMessage(sprintf('Set LDAP protocol version to %d failed: [%d] %s',
                                          $this->_params['version'],
                                          ldap_errno($conn),
                                          ldap_error($conn)),
                                  __FILE__, __LINE__);
                }
        }

        // Bind.
        if (!empty($this->_params['binddn'])) {
            $result = @ldap_bind($this->_ds, $this->_params['binddn'],
                                 $this->_params['password']);
        } else {
            $result = @ldap_bind($this->_ds);
        }
        if (!$result) {
            return PEAR::raiseError(_("Could not bind to LDAP server."));
        }

        return true;
    }

    /**
     * Returns the win32 AD epoch number of days the password may be
     * unchanged.
     *
     * @return int The AD epoch number of days the password may
     * unchanged.
     */
    function _getMaxPasswd()
    {
        $result = $this->_bind();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $domaindn = $this->_params['basedn'];
        $adomaindn = explode('.', array_pop(explode(',', ldap_dn2ufn($domaindn))));
        $domaindn = '';
        foreach ($adomaindn as $name) {
            $domaindn .= 'DC=' . $name . ',';
        }
        $domaindn = trim($domaindn, ',');
        $searchResult = ldap_search($this->_ds, $domaindn, 'objectClass=*');
        $first = @ldap_first_entry($this->_ds, $searchResult);
        $res = @ldap_get_values($this->_ds, $first, 'maxPwdAge');
        if ($res === false) {
            return false;
        }
        return $res[0];
    }

    /**
     * Code from 'brudinie at yahoo dot co dot uk' at http://nl3.php.net/ldap/
     *
     * @param int $dateLargeInt The win32 active directory epoch time.
     * @return int A unix timestamp.
     */
    function _convertWinTimeToUnix($dateLargeInt)
    {
        // Seconds since jan 1st 1601.
        $secsAfterADEpoch = $dateLargeInt / (10000000);

        // Unix epoch - AD epoch * number of tropical days * seconds in a day.
        $ADToUnixConvertor = ((1970-1601) * 365.242190) * 86400;

        return intval($secsAfterADEpoch-$ADToUnixConvertor);
    }

    /**
     * Returns the user account from the ldap source.
     *
     * @return array  A hash with complete account details.
     */
    function _getAccount()
    {
        static $information;
        if (!isset($information)) {
            $result = $this->_bind();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            // Get the fullname.
            $searchResult = ldap_search($this->_ds, $this->_params['basedn'],
                                        $this->_params['attr'] . '=' . $this->getUsername());
            $first = ldap_first_entry($this->_ds, $searchResult);
            $information = ldap_get_entries($this->_ds, $searchResult);

            // Disconnect from the ldap server.
            @ldap_close($this->_ds);

            if ($information['count'] == 0) {
                $information = PEAR::raiseError(_("User account not found"));
            }
        }

        return $information;
    }

    /**
     * Returns the username. Since this method is called for authenticating
     * in the parent class, we also have the option to NOT strip the domain
     * name if there is one. This is a configuration checkbox.
     *
     * @return string  The username.
     */
    function getUsername()
    {
        return $this->_params['strip'] ? Auth::getBareAuth() : Auth::getAuth();
    }

    /**
     * Returns the user's full name.
     *
     * @return mixed  The user's full name (string), or false (error).
     */
    function getFullname()
    {
        $information = $this->_getAccount();
        if (is_a($information, 'PEAR_Error')) {
            return $information;
        }

        if (isset($information[0]['cn;lang-es'][0]) &&
            $information[0]['cn;lang-es'][0] != '') {
            $name = $information[0]['cn;lang-es'][0];
        } else {
            $name = $information[0]['cn'][0];
        }

        return (empty($name) ? false : $name);
    }

    /**
     * Returns the user's home (login) directory.
     *
     * @return mixed  The user's directory (string), or false (error).
     */
    function getHome()
    {
        $information = $this->_getAccount();
        if (is_a($information, 'PEAR_Error')) {
            return $information;
        }

        if (empty($information[0]['homedirectory'][0])) {
            return false;
        }

        return $information[0]['homedirectory'][0];
    }

    /**
     * Returns the user's default shell.
     *
     * @return mixed  The user's shell (string), or false (error).
     */
    function getShell()
    {
        $information = $this->_getAccount();
        if (is_a($information, 'PEAR_Error')) {
            return $information;
        }

        if (isset($information[0]['useraccountcontrol'][0])) {
            return _("Windows");
        }

        if (empty($information[0]['loginshell'][0])) {
            return false;
        }

        return $information[0]['loginshell'][0];
    }

    /**
     * Returns the date of the user's last password change.
     *
     * @return mixed  Date string (string) or false (error).
     */
    function getPasswordChange()
    {
        $information = $this->_getAccount();
        if (is_a($information, 'PEAR_Error')) {
            return $information;
        }

        if (isset($information[0]['shadowlastchange'][0])) {
            $lastchange = strftime('%x', $information[0]['shadowlastchange'][0] * 86400);
        } elseif (isset($information[0]['pwdlastset'][0])) {
            $lastchangetime = $this->_convertWinTimeToUnix($information[0]['pwdlastset'][0]);
            $lastchange = strftime('%x', $lastchangetime);
        }

        return (empty($lastchange) ? false : $lastchange);
    }

    /**
     * Returns the status of the current password.
     *
     * @return mixed  A string with a warning message if the password is about
     *                to expire, PEAR_Error on error and false otherwise.
     */
    function checkPasswordStatus()
    {
        $information = $this->_getAccount();
        if (is_a($information, 'PEAR_Error')) {
            return $information;
        }

        if (isset($information[0]['pwdlastset'][0]) &&
            isset($information[0]['useraccountcontrol'][0])) {
            // Active Directory.
            $accountControl = $information[0]['useraccountcontrol'][0];
            if (($accountControl & 65536) != 0) {
                // ADS_UF_DONT_EXPIRE_PASSWD
                return false;
            }
            if (($accountControl & 524288) != 0) {
                // ADS_UF_PASSWORD_EXPIRED
                return _("Your password has expired");
            }

            $maxdays = $this->_getMaxPasswd();
            if (is_a($maxdays, 'PEAR_error')) {
                return $maxdays;
            }
            if ($maxdays === false) {
                return false;
            }

            $today = time();
            $lastset = $information[0]['pwdlastset'][0] - $maxdays;
            $toexpire = floor(($this->_convertWinTimeToUnix($lastset) - $today) / 86400);
            if ($toexpire < 0) {
                return _("Your password has expired");
            }
            if ($toexpire < 14) {
                // Two weeks.
                return sprintf(_("%d days until your password expires."), $toexpire);
            }
        } elseif (isset($information[0]['shadowmax'][0]) &&
                  isset($information[0]['shadowlastchange'][0]) &&
                  isset($information[0]['shadowwarning'][0])) {
            // OpenLDAP.
            $today = floor(time() / 86400);
            $warnday = $information[0]['shadowlastchange'][0] +
                $information[0]['shadowmax'][0] - $information[0]['shadowwarning'][0];
            $toexpire = $information[0]['shadowlastchange'][0] + $information[0]['shadowmax'][0] - $today;

            if ($today >= $warnday) {
                return sprintf(_("%d days until your password expires."), $toexpire);
            }
        }

        return false;
    }

}

/**
 * The kolab driver class is merely an extension to the ldap class. It reuses
 * existing Kolab configuration instead of requiring another set of
 * parameters. It also binds using a set internal user (normally this is
 * cn=nobody,cn=internal), so that account information can be fetched even for
 * internal accounts.
 *
 * @author mzizka@hotmail.com
 */
class Accounts_Driver_kolab extends Accounts_Driver_ldap {

    /**
     * Constructs a new Accounts_Driver_kolab object. Uses Kolab configuration.
     *
     * @param array $params  A hash containing connection parameters.
     */
    function Accounts_Driver_kolab($params = array())
    {
        $ldap_params = array(
            'host'      => $GLOBALS['conf']['kolab']['ldap']['server'],
            'port'      => $GLOBALS['conf']['kolab']['ldap']['port'],
            'basedn'    => $GLOBALS['conf']['kolab']['ldap']['basedn'],
            'binddn'    => $GLOBALS['conf']['kolab']['ldap']['phpdn'],
            'password'  => $GLOBALS['conf']['kolab']['ldap']['phppw']);
        $params = array_merge($ldap_params, $params);
        parent::Accounts_Driver_ldap($params);
    }

}

/**
 * Implements the Accounts API using finger to fetch information.
 *
 * @author  Peter Paul Elfferich <pp@lazyfox.org>
 * @package Horde_Block
 */
class Accounts_Driver_finger extends Accounts_Driver {

    /**
     * Hash containing connection parameters.
     *
     * @var array
     */
    var $params = array();

    /**
     * Constructor.
     *
     * @param array $params  Hash containing connection parameters.
     */
    function Accounts_Driver_finger($params = array())
    {
        $this->params = $params;
        if (!isset($this->params['finger_path'])) {
            $this->params['finger_path'] = 'finger';
        }
        if (!isset($this->params['host'])) {
            $this->params['host'] = 'localhost';
        }
    }

    /**
     * Returns a hash with parsed account information.
     *
     * @param array $output  Array of finger output strings
     * @return array  A hash with account details parsed from output
     */
    function _parseAccount($output)
    {
        $info = array();

        ereg("^.*Name: (.*)$", $output[1], $regs);
        $info['fullname'] = $regs[1];

        ereg("^Directory: (.*)Shell: (.*)$", $output[2], $regs);
        $info['home'] = trim($regs[1]);
        $info['shell'] = $regs[2];

        return $info;
    }

    /**
     * Returns the user account.
     *
     * @return array  A hash with complete account details.
     */
    function _getAccount()
    {
        static $information;

        if (!isset($information)) {
            $user = String::lower($this->getUsername());
            $command = $this->params['finger_path'] . ' ' . escapeshellarg($user . '@' . $this->params['host']);
            exec($command, $output);
            $information = $this->_parseAccount($output);
        }

        return $information;
    }

    /**
     * Returns the user's full name.
     *
     * @return mixed  The user's full name (string), or false (error).
     */
    function getFullname()
    {
        $information = $this->_getAccount();
        return $information['fullname'];
    }

    /**
     * Returns the user's home (login) directory.
     *
     * @return mixed  The user's directory (string), or false (error).
     */
    function getHome()
    {
        $information = $this->_getAccount();
        return $information['home'];
    }

    /**
     * Returns the user's default shell.
     *
     * @return mixed  The user's shell (string), or false (error).
     */
    function getShell()
    {
        $information = $this->_getAccount();
        return $information['shell'];
    }

}
