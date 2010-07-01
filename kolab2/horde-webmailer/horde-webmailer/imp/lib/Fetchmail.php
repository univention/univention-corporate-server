<?php
/**
 * The IMP_Fetchmail:: class provides an interface to download mail from
 * remote mail servers.
 *
 * $Horde: imp/lib/Fetchmail.php,v 1.41.8.15 2009-01-06 15:24:03 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Nuno Loureiro <nuno@co.sapo.pt>
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package IMP
 */
class IMP_Fetchmail {

    /**
     * Parameters used by the driver.
     *
     * @var array
     */
    var $_params;

    /**
     * The list of active fetchmail parameters for the current driver.
     * ALL DRIVERS SHOULD UNSET ANY FETCHMAIL PARAMETERS THEY DO NOT USE
     * OR ELSE THEY WILL APPEAR IN THE PREFERENCES PAGE.
     * The following parameters are available:
     *   'id'          --  The account name.
     *   'driver'      --  The driver to use.
     *   'protocol'    --  The protocol type.
     *   'username'    --  The username on the remote server.
     *   'password'    --  The password on the remote server.
     *   'server'      --  The remote server name/address.
     *   'rmailbox'    --  The remote mailbox name.
     *   'lmailbox'    --  The local mailbox to download messages to.
     *   'onlynew'     --  Only retrieve new messages?
     *   'markseen'    --  Mark messages as seen?
     *   'del'         --  Delete messages after fetching?
     *   'loginfetch'  --  Fetch mail from other accounts on login?
     *   'acctcolor'   --  Should these messages be colored differently
     *                     in mailbox view?
     *
     * @var array
     */
    var $_activeparams = array(
        'id', 'driver', 'type', 'protocol', 'username', 'password', 'server',
        'rmailbox', 'lmailbox', 'onlynew', 'markseen', 'del', 'loginfetch',
        'acctcolor'
    );

    /**
     * Attempts to return a concrete IMP_Fetchmail instance based on $driver.
     *
     * @param string $driver  The type of concrete IMP_Fetchmail subclass to
     *                        return, based on the driver indicated. The code
     *                        is dynamically included.
     *
     * @param array $params   The configuration parameter array.
     *
     * @return mixed  The newly created concrete IMP_Fetchmail instance, or
     *                false on error.
     */
    function &factory($driver, $params = array())
    {
        $driver = basename($driver);
        require_once dirname(__FILE__) . '/Fetchmail/' . $driver . '.php';
        $class = 'IMP_Fetchmail_' . $driver;
        if (class_exists($class)) {
            $fetchmail = new $class($params);
        } else {
            $fetchmail = false;
        }

        return $fetchmail;
    }

    /**
     * Returns a list of available drivers, with a description of each.
     * This function can be called statically:
     *   $list = IMP_Fetchmail::listDrivers();
     *
     * @return array  The list of available drivers, with the driver name as
     *                the key and the description as the value.
     */
    function listDrivers()
    {
        $drivers = array();

        if (($dir = opendir(dirname(__FILE__) . '/Fetchmail'))) {
            while (false !== ($file = readdir($dir))) {
                if (!is_dir($file)) {
                    $driver = basename($file, '.php');
                    $class = 'IMP_Fetchmail_' . $driver;
                    require_once dirname(__FILE__) . '/Fetchmail/' . $file;
                    if (is_callable(array($class, 'description')) &&
                        ($descrip = call_user_func(array($class, 'description')))) {
                        $drivers[$driver] = $descrip;
                    }
                }
            }
            closedir($dir);
        }

        return $drivers;
    }

    /**
     * List the colors available for coloring fetched messages.
     * This function can be called statically:
     *   $list = IMP_Fetchmail::listColors();
     *
     * @return array  The list of available colors;
     */
    function listColors()
    {
        return array(
            'purple', 'lime', 'teal', 'blue', 'olive', 'fuchsia', 'navy',
            'aqua'
        );
    }

    /**
     * Returns a description of the driver.
     * This function can be called statically:
     *   $description = IMP_Fetchmail::description();
     *
     * @abstract
     *
     * @return string  The description of the driver.
     */
    function description()
    {
        return '';
    }

    /**
     * Constructor.
     *
     * @param array $params  The configuration parameter array.
     */
    function IMP_Fetchmail($params)
    {
        /* Check for missing params. */
        $paramlist = $this->getParameterList();
        if (array_diff($paramlist, array_keys($params))) {
            // TODO: Error message here
        }

        $this->_params = $params;
    }

    /**
     * Return the list of parameters valid for this driver.
     *
     * @return array  The list of active parameters.
     */
    function getParameterList()
    {
        return $this->_activeparams;
    }

    /**
     * Return a list of protocols supported by this driver.
     *
     * @abstract
     *
     * @return array  The list of protocols.
     *                KEY: protocol ID
     *                VAL: protocol description
     */
    function getProtocolList()
    {
        return array();
    }

    /**
     * Gets the mail using the data in this object.
     *
     * @abstract
     *
     * @return mixed  Returns the number of messages retrieved on success.
     *                Returns PEAR_Error on error.
     */
    function getMail()
    {
        return PEAR::raiseError('not implemented');
    }

    /**
     * Processes a single mail message by calling any user defined functions,
     * stripping bare newlines, and adding color information to the headers.
     *
     * @access private
     *
     * @param string $header  The message header text.
     * @param string $body    The message body text.
     *
     * @return string  The complete message.
     */
    function _processMailMessage($header, $body)
    {
        $msg = rtrim($header);

        if (empty($this->_params['acctcolor'])) {
            $msg .= "\nX-color: " . $this->_params['acctcolor'];
        }
        $msg .= "\n\n" . $body;

        /* If there is a user defined function, call it with the current
         * message as an argument. */
        if ($GLOBALS['conf']['hooks']['fetchmail_filter']) {
            $msg = Horde::callHook('_imp_hook_fetchmail_filter', array($msg), 'imp');
        }

        return IMP::removeBareNewlines($msg);
    }

    /**
     * Checks the message size to see if it exceeds the maximum value
     * allowable in the configuration file.
     *
     * @access private
     *
     * @param integer $size    The size of the message.
     * @param string $subject  The subject of the message.
     * @param string $from     The message sender.
     *
     * @return boolean  False if message is too large, true if OK.
     */
    function _checkMessageSize($size, $subject, $from)
    {
        if (!empty($GLOBALS['conf']['fetchmail']['size_limit']) &&
            ($size > $GLOBALS['conf']['fetchmail']['size_limit'])) {
            require_once 'Horde/MIME.php';
            $GLOBALS['notification']->push(sprintf(_("The message \"%s\" from \"%s\" (%d bytes) exceeds fetch size limit."), MIME::Decode($subject), MIME::Decode($from), $size), 'horde.warning');
            return false;
        } else {
            return true;
        }
    }

    /**
     * Add the message to the requested local mailbox.
     *
     * @access private
     *
     * @param string $msg  The message text.
     *
     * @return boolean  True on success, false on failure.
     */
    function _addMessage($msg)
    {
        $imp_imap = &IMP_IMAP::singleton();
        return @imap_append($imp_imap->stream(), IMP::serverString($this->_params['lmailbox']), $msg);
    }

    /**
     * Perform fetchmail on the list of accounts given. Outputs informaton
     * to the global notification driver.
     * This function can be called statically.
     *
     * @param array $accounts  The list of account identifiers to fetch mail
     *                         for.
     */
    function fetchMail($accounts)
    {
        $fm_account = new IMP_Fetchmail_Account();

        foreach ($accounts as $val) {
            $params = $fm_account->getAllValues($val);
            $driver = &IMP_Fetchmail::factory($params['driver'], $params);
            if ($driver === false) {
                continue;
            }
            $res = $driver->getMail();

            if (is_a($res, 'PEAR_Error')) {
                $GLOBALS['notification']->push(_("Fetchmail: ") . $res->getMessage(), 'horde.warning');
            } elseif ($res == 1) {
                $GLOBALS['notification']->push(_("Fetchmail: ") . sprintf(_("Fetched 1 message from %s"), $fm_account->getValue('id', $val)), 'horde.success');
            } elseif ($res >= 0) {
                $GLOBALS['notification']->push(_("Fetchmail: ") . sprintf(_("Fetched %d messages from %s"), $res, $fm_account->getValue('id', $val)), 'horde.success');
            } else {
                $GLOBALS['notification']->push(_("Fetchmail: no new messages."), 'horde.success');
            }
        }
    }

}

/**
 * The IMP_Fetchmail_Account:: class provides an interface to accessing
 * fetchmail preferences for all mail accounts a user might have.
 *
 * @author  Nuno Loureiro <nuno@co.sapo.pt>
 * @package IMP
 */
class IMP_Fetchmail_Account {

    /**
     * Array containing all the user's accounts.
     *
     * @var array
     */
    var $_accounts = array();

    /**
     * Constructor.
     */
    function IMP_Fetchmail_Account()
    {
        /* Read all the user's accounts from the prefs object or build
         * a new account from the standard values given in prefs.php. */
        $accounts = @unserialize($GLOBALS['prefs']->getValue('fm_accounts'));
        if (is_array($accounts)) {
            $this->_accounts = $accounts;
        }
    }

    /**
     * Return the number of accounts.
     *
     * @return integer  Number of active accounts.
     */
    function count()
    {
        return count($this->_accounts);
    }

    /**
     * Saves all accounts in the prefs backend.
     *
     * @access private
     */
    function _save()
    {
        $GLOBALS['prefs']->setValue('fm_accounts', serialize($this->_accounts));
    }

    /**
     * Adds a new empty account to the array of accounts.
     *
     * @return integer  The pointer to the created account.
     */
    function add()
    {
        $this->_accounts[] = array();
        $this->_save();
        return count($this->_accounts) - 1;
    }

    /**
     * Remove an account from the array of accounts
     *
     * @param integer $account  The pointer to the account to be removed.
     *
     * @return array  The removed account.
     */
    function delete($account)
    {
        $deleted = $this->_accounts[$account];
        unset($this->_accounts[$account]);
        $this->_accounts = array_values($this->_accounts);
        $this->_save();
        return $deleted;
    }

    /**
     * Returns a property from one of the accounts.
     *
     * @param string $key       The property to retrieve.
     * @param integer $account  The account to retrieve the property from.
     *
     * @return mixed  The value of the property or false if the property
     *                doesn't exist.
     */
    function getValue($key, $account)
    {
        return (isset($this->_accounts[$account][$key])) ? $this->_accounts[$account][$key] : false;
    }

    /**
     * Returns all properties from the requested accounts.
     *
     * @param integer $account  The account to retrieve the properties from.
     *
     * @return array  The entire properties array, or false on error.
     */
    function getAllValues($account)
    {
        return (isset($this->_accounts[$account])) ? $this->_accounts[$account] : false;
    }

    /**
     * Returns an array with the specified property from all existing accounts.
     *
     * @param string $key  The property to retrieve.
     *
     * @return array  The array with the values from all accounts.
     */
    function getAll($key)
    {
        $list = array();
        foreach (array_keys($this->_accounts) as $account) {
            $list[$account] = $this->getValue($key, $account);
        }

        return $list;
    }

    /**
     * Sets a property with a specified value.
     *
     * @param string $key       The property to set.
     * @param mixed $val        The value the property should be set to.
     * @param integer $account  The account to set the property in.
     */
    function setValue($key, $val, $account)
    {
        /* These parameters are checkbox items - make sure they are stored
         * as boolean values. */
        $list = array('del', 'onlynew', 'markseen', 'loginfetch');
        if (in_array($key, $list) && !is_bool($val)) {
            if (($val == 'yes') || (intval($val) != 0)) {
                $val = true;
            } else {
                $val = false;
            }
        }

        $this->_accounts[$account][$key] = $val;
        $this->_save();
    }

    /**
     * Returns true if the pair key/value is already in the accounts array.
     *
     * @param string $key  The account key to search.
     * @param string $val  The value to search for in $key.
     *
     * @return boolean  True if the value was found in $key.
     */
    function hasValue($key, $val)
    {
        $list = $this->getAll($key);
        foreach ($list as $val2) {
            if (strpos(String::lower($val), String::lower($val2)) !== false) {
                return true;
            }
        }
        return false;
    }

}
