<?php

require_once 'Horde/Identity.php';

/**
 * This class provides an IMP-specific interface to all identities a
 * user might have. Its methods take care of any site-specific
 * restrictions configured in prefs.php and conf.php.
 *
 * $Horde: imp/lib/Identity/imp.php,v 1.44.2.22 2009-01-06 15:24:08 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @package Horde_Identity
 */
class Identity_imp extends Identity {

    /**
     * Cached alias list.
     *
     * @var array
     */
    var $_aliases = array();

    /**
     * Cached from address list.
     *
     * @var array
     */
    var $_fromList = array();

    /**
     * Cached names list.
     *
     * @var array
     */
    var $_names = array();

    /**
     * Cached signature list.
     *
     * @var array
     */
    var $_signatures = array();

    /**
     * Reads all the user's identities from the prefs object or builds
     * a new identity from the standard values given in prefs.php.
     */
    function Identity_imp()
    {
        parent::Identity();
        $this->_properties = array_merge(
            $this->_properties,
            array('replyto_addr', 'alias_addr', 'tieto_addr', 'bcc_addr',
                  'signature', 'sig_first', 'sig_dashes', 'save_sent_mail',
                  'sent_mail_folder'));
    }

    /**
     * Verifies and sanitizes all identity properties.
     *
     * @param integer $identity  The identity to verify.
     *
     * @return boolean|object  True if the properties are valid or a PEAR_Error
     *                         with an error description otherwise.
     */
    function verify($identity = null)
    {
        if (is_a($result = parent::verify($identity), 'PEAR_Error')) {
            return $result;
        }

        if (!isset($identity)) {
            $identity = $this->_default;
        }

        /* Prepare email validator */
        require_once 'Horde/Form.php';
        require_once 'Horde/Variables.php';
        $email = new Horde_Form_Type_email();
        $vars = new Variables();
        $var = new Horde_Form_Variable('', 'replyto_addr', $email, false);

        /* Verify From address. */
        if (!$email->isValid($var, $vars, $this->getValue('from_addr', $identity), $error_message)) {
            return PEAR::raiseError($error_message);
        }

        /* Verify Reply-to address. */
        if (!$email->isValid($var, $vars, $this->getValue('replyto_addr', $identity), $error_message)) {
            return PEAR::raiseError($error_message);
        }

        /* Clean up Alias, Tie-to, and BCC addresses. */
        require_once 'Horde/Array.php';
        foreach (array('alias_addr', 'tieto_addr', 'bcc_addr') as $val) {
            $data = $this->getValue($val, $identity);
            if (is_array($data)) {
                $data = implode("\n", $data);
            }
            $data = trim($data);
            $data = (empty($data)) ? array() : Horde_Array::prepareAddressList(preg_split("/[\n\r]+/", $data));

            /* Validate addresses */
            foreach ($data as $address) {
                if (!$email->isValid($var, $vars, $address, $error_message)) {
                    return PEAR::raiseError($error_message);
                }
            }

            $this->setValue($val, $data, $identity);
        }

        return true;
    }

    /**
     * Returns a complete From: header based on all relevant factors (fullname,
     * from address, input fields, locks etc.)
     *
     * @param integer $ident        The identity to retrieve the values from.
     * @param string $from_address  A default from address to use if no
     *                              identity is selected and the from_addr
     *                              preference is locked.
     *
     * @return string  A full From: header in the format
     *                 'Fullname <user@example.com>'.
     */
    function getFromLine($ident = null, $from_address = '')
    {
        static $froms = array();

        if (isset($froms[$ident])) {
            return $froms[$ident];
        }

        if (!isset($ident)) {
            $address = $from_address;
        }

        if (empty($address) || $this->_prefs->isLocked('from_addr')) {
            $address = $this->getFromAddress($ident);
            $name = $this->getFullname($ident);
        }

        if (!empty($address)) {
            $ob = IMP::parseAddressList($address, false, true);
        }
        if (is_a($ob, 'PEAR_Error')) {
            $ob->message .= ' ' . _("Your From address is not a valid email address. This can be fixed in your Personal Information options page.");
            return $ob;
        }

        if (empty($name)) {
            if (!empty($ob[0]->personal)) {
                $name = $ob[0]->personal;
            } else {
                $name = $this->getFullname($ident);
            }
        }

        $from = MIME::trimEmailAddress(MIME::rfc822WriteAddress($ob[0]->mailbox, $ob[0]->host, $name));

        $froms[$ident] = $from;
        return $from;
    }

    /**
     * Returns an array with From: headers from all identities
     *
     * @return array  The From: headers from all identities
     */
    function getAllFromLines()
    {
        foreach (array_keys($this->_identities) as $ident) {
            $list[$ident] = $this->getFromAddress($ident);
        }
        return $list;
    }

    /**
     * Returns an array with the necessary values for the identity select
     * box in the IMP compose window.
     *
     * @return array  The array with the necessary strings
     */
    function getSelectList()
    {
        $ids = $this->getAll('id');
        foreach ($ids as $key => $id) {
            $list[$key] = $this->getFromAddress($key) . ' (' . $id . ')';
        }
        return $list;
    }

    /**
     * Returns true if the given address belongs to one of the identities.
     * This function will search aliases for an identity automatically.
     *
     * @param string $address  The address to search for in the identities.
     *
     * @return boolean  True if the address was found.
     */
    function hasAddress($address)
    {
        static $list;

        $address = String::lower($address);
        if (!isset($list)) {
            $list = $this->getAllFromAddresses(true);
        }

        return isset($list[$address]);
    }

    /**
     * Returns the from address based on the chosen identity. If no
     * address can be found it is built from the current user name and
     * the specified maildomain.
     *
     * @param integer $ident  The identity to retrieve the address from.
     *
     * @return string  A valid from address.
     */
    function getFromAddress($ident = null)
    {
        if (!empty($this->_fromList[$ident])) {
            return $this->_fromList[$ident];
        }

        $val = $this->getValue('from_addr', $ident);
        if (empty($val)) {
            $val = $_SESSION['imp']['user'];
        }

        if (!strstr($val, '@')) {
            $val .= '@' . $_SESSION['imp']['maildomain'];
        }

        $this->_fromList[$ident] = $val;

        return $val;
    }

    /**
     * Returns all aliases based on the chosen identity.
     *
     * @param integer $ident  The identity to retrieve the aliases from.
     *
     * @return array  Aliases for the identity.
     */
    function getAliasAddress($ident)
    {
        if (empty($this->_aliases[$ident])) {
            $this->_aliases[$ident] = @array_merge($this->getValue('alias_addr', $ident),
                                                   array($this->getValue('replyto_addr', $ident)));
        }

        return $this->_aliases[$ident];
    }

    /**
     * Returns an array with all identities' from addresses.
     *
     * @param boolean $alias  Include aliases?
     *
     * @return array  The array with
     *                KEY - address
     *                VAL - identity number
     */
    function getAllFromAddresses($alias = false)
    {
        $list = array();

        foreach ($this->_identitiesWithDefaultLast() as $key => $identity) {
            /* Get From Addresses. */
            $list[String::lower($this->getFromAddress($key))] = $key;

            /* Get Aliases. */
            if ($alias) {
                $addrs = $this->getAliasAddress($key);
                if (!empty($addrs)) {
                    foreach (array_filter($addrs) as $val) {
                        $list[String::lower($val)] = $key;
                    }
                }
            }
        }

        return $list;
    }

    /**
     * Get all 'tie to' address/identity pairs.
     *
     * @return array  The array with
     *                KEY - address
     *                VAL - identity number
     */
    function getAllTieAddresses()
    {
        $list = array();

        foreach ($this->_identitiesWithDefaultLast() as $key => $identity) {
            $tieaddr = $this->getValue('tieto_addr', $key);
            if (!empty($tieaddr)) {
                foreach ($tieaddr as $val) {
                    $list[$val] = $key;
                }
            }
        }

        return $list;
    }

    /**
     * Returns the list of identities with the default identity positioned
     * last.
     *
     * @access private
     *
     * @return array  The identities list with the default identity last.
     */
    function _identitiesWithDefaultLast()
    {
        $ids = $this->_identities;
        $default = $this->getDefault();
        $tmp = $ids[$default];
        unset($ids[$default]);
        $ids[$default] = $tmp;
        return $ids;
    }

    /**
     * Returns the BCC addresses for a given identity.
     *
     * @param integer $ident  The identity to retrieve the Bcc addresses from.
     *
     * @return array  The array of objects (IMAP addresses).
     */
    function getBccAddresses($ident = null)
    {
        $bcc = $this->getValue('bcc_addr', $ident);
        if (empty($bcc)) {
            return array();
        } else {
            if (!is_array($bcc)) {
                $bcc = array($bcc);
            }
            $addr_list = IMP::parseAddressList(implode(', ', $bcc));
            if (is_a($addr_list, 'PEAR_Error')) {
                return array();
            }
            return $addr_list;
        }
    }

    /**
     * Returns the identity's id that matches the passed addresses.
     *
     * @param mixed $addresses      Either an array or a single string or a
     *                              comma-separated list of email addresses.
     * @param boolean $search_ties  Search for a matching identity in tied
     *                              addresses too?
     *
     * @return integer  The id of the first identity that from or alias
     *                  addresses match (one of) the passed addresses or
     *                  null if none matches.
     */
    function getMatchingIdentity($addresses, $search_ties = true)
    {
        static $tie_addresses, $own_addresses;

        if (!isset($tie_addresses)) {
            $tie_addresses = $this->getAllTieAddresses();
            $own_addresses = $this->getAllFromAddresses(true);
        }

        /* Normalize address list. */
        if (is_array($addresses)) {
            $addresses = array_filter($addresses);
        } else {
            $addresses = array($addresses);
        }

        $addr_list = IMP::parseAddressList(implode(', ', $addresses));
        if (is_a($addr_list, 'PEAR_Error')) {
            return null;
        }

        foreach ($addr_list as $address) {
            if (empty($address->mailbox)) {
                continue;
            }
            $find_address = $address->mailbox;
            if (!empty($address->host)) {
                $find_address .= '@' . $address->host;
            }
            $find_address = String::lower($find_address);

            /* Search 'tieto' addresses first. */
            /* Check for this address explicitly. */
            if ($search_ties && isset($tie_addresses[$find_address])) {
                return $tie_addresses[$find_address];
            }

            /* If we didn't find the address, check for the domain. */
            if (!empty($address->host)) {
                $host = '@' . $address->host;
                if ($search_ties && $host != '@' && isset($tie_addresses[$host])) {
                    return $tie_addresses[$host];
                }
            }

            /* Next, search all from addresses. */
            if (isset($own_addresses[$find_address])) {
                return $own_addresses[$find_address];
            }
        }

        return null;
    }

    /**
     * Returns the user's full name.
     *
     * @param integer $ident  The identity to retrieve the name from.
     *
     * @return string  The user's full name.
     */
    function getFullname($ident = null)
    {
        if (isset($this->_names[$ident])) {
            return $this->_names[$ident];
        }

        $this->_names[$ident] = $this->getValue('fullname', $ident);

        return $this->_names[$ident];
    }

    /**
     * Returns the full signature based on the current settings for the
     * signature itself, the dashes and the position.
     *
     * @param integer $ident  The identity to retrieve the signature from.
     *
     * @return string  The full signature.
     */
    function getSignature($ident = null)
    {
        if (isset($this->_signatures[$ident])) {
            return $this->_signatures[$ident];
        }

        $val = $this->getValue('signature', $ident);
        if (!empty($val)) {
            $sig_first = $this->getValue('sig_first', $ident);
            $sig_dashes = $this->getValue('sig_dashes', $ident);
            $val = str_replace("\r\n", "\n", $val);
            if ($sig_dashes) {
                $val = "-- \n$val";
            }
            if (isset($sig_first) && $sig_first) {
                $val = "\n" . $val . "\n\n\n";
            } else {
                $val = "\n" . $val;
            }
        }

        if (!empty($GLOBALS['conf']['hooks']['signature'])) {
            $val = Horde::callHook('_imp_hook_signature', array($val),
                                   'imp', $val);
        }

        $this->_signatures[$ident] = $val;

        return $val;
    }

    /**
     * Returns an array with the signatures from all identities
     *
     * @return array  The array with all the signatures.
     */
    function getAllSignatures()
    {
        static $list;

        if (isset($list)) {
            return $list;
        }

        foreach ($this->_identities as $key => $identity) {
            $list[$key] = $this->getSignature($key);
        }

        return $list;
    }

    /**
     * @see Identity::getValue()
     */
    function getValue($key, $identity = null)
    {
        if ($key == 'sent_mail_folder') {
            $folder = parent::getValue('sent_mail_folder', $identity);
            return strlen($folder) ? IMP::folderPref($folder, true) : '';
        }
        return parent::getValue($key, $identity);
    }

    /**
     * Returns an array with the sent-mail folder names from all the
     * identities.
     *
     * @return array  The array with the folder names.
     */
    function getAllSentmailFolders()
    {
        $list = array();
        foreach ($this->_identities as $key => $identity) {
            if ($folder = $this->getValue('sent_mail_folder', $key)) {
                $list[$folder] = 1;
            }
        }

        /* Get rid of duplicates and empty folders. */
        return array_filter(array_keys($list));
    }

    /**
     * Returns true if the mail should be saved and the user is allowed to.
     *
     * @param integer $ident  The identity to retrieve the setting from.
     *
     * @return boolean  True if the sent mail should be saved.
     */
    function saveSentmail($ident = null)
    {
        if (!$GLOBALS['conf']['user']['allow_folders']) {
            return false;
        }

        return $this->getValue('save_sent_mail', $ident);
    }

}
