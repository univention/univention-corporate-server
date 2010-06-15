<?php
/**
 * Contains functions related to managing
 * Access Control Lists on an IMAP server using RFC 2086.
 *
 * <pre>
 * Required parameters:
 * ====================
 *  'username'  --  The username for the server connection
 *  'password'  --  The password for the server connection
 *  'hostspec'  --  The hostname or IP address of the server.
 *                  DEFAULT: 'localhost'
 *  'port'      --  The server port to which we will connect.
 *                  IMAP is generally 143, while IMAP-SSL is generally 993.
 *                  DEFAULT: 143
 *  'protocol'  --  The connection protocol (e.g. 'imap', 'pop3', 'nntp').
 *                  Protocol is one of 'imap/notls' (or only 'imap' if you
 *                  have a c-client version 2000c or older), 'imap/ssl', or
 *                  'imap/ssl/novalidate-cert' (for a self-signed certificate).
 *                  DEFAULT: 'imap'
 * </pre>
 *
 * $Horde: framework/IMAP/IMAP/ACL/rfc2086.php,v 1.3 2004/04/17 14:24:13 jan Exp $
 *
 * Copyright 2003-2004 Chris Hastie <imp@oak-wood.co.uk>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chris Hastie <imp@oak-wood.co.uk>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_IMAP
 */
class IMAP_ACL_rfc2086 extends IMAP_ACL {

    /**
     * IMAP resource.
     */
    var $_imap;

    /**
     * List of server's capabilities, output of
     * CAPABILITY command. Formated as a hash
     * array(
     *     *capability* => 1
     * )
     *
     * @var array $_caps
     */
    var $_caps = array();

    /**
     * Constructor.
     *
     * @access public
     *
     * @param array $params  Any additional parameters this driver may need.
     */
    function IMAP_ACL_rfc2086($params = array())
    {
        $this->_params = array_merge(array('hostspec' => 'localhost',
                                           'port' => 143,
                                           'protocol' => 'imap'),
                                     $params);

        $this->_caps = $this->_getCapability();
        if (is_a($this->_caps, 'PEAR_Error')) {
            $this->_error = $this->_caps;
            return;
        }

        if (substr($this->_params['protocol'], 0, 4) != 'imap') {
            /* No point in going any further if it's not an IMAP server. */
            $this->_error = PEAR::raiseError(_("Only IMAP servers support shared folders."));
            $this->_supported = false;
        } elseif (!isset($this->_caps['acl'])) {
            /* If we couldn't get the server's capability, we'll assume
               ACL is not supported for now. */
            $this->_supported = false;
        } else {
            $this->_supported = true;
        }

        $this->_protected = array($this->_params['username']);

        $this->_rightsList = array(
             'l' => _("List - user can see the folder"),
             'r' => _("Read messages"),
             's' => _("Mark with Seen/Unseen flags"),
             'w' => _("Mark with other flags (e.g. Important/Answered)"),
             'i' => _("Insert messages"),
             'p' => _("Post to this folder (not enforced by IMAP)"),
             'c' => _("Create sub folders"),
             'd' => _("Delete and purge messages"),
             'a' => _("Administer - set permissions for other users")
        );
    }

    function _connect()
    {
        $this->_imap = @imap_open(sprintf('{%s:%d/%s}', 
                                          $this->_params['hostspec'],
                                          $this->_params['port'],
                                          $this->_params['protocol']),
                                  $this->_params['username'],
                                  $this->_params['password'], 
                                  OP_HALFOPEN);
        if (!$this->_imap) {
            $this->_imap = PEAR::raiseError(imap_last_error());
            return false;
        }
        return true;
    }

    /**
     * Sets the ACL on an IMAP server
     *
     * @access public
     *
     * @param string $folder      The folder on which to edit the ACL.
     * @param string $share_user  The user to grant rights to.
     * @param array $acl          An array, the keys of which are the
     *                            rights to be granted (see RFC 2086).
     *
     * @return mixed  True on success, PEAR_Error on failure or if
     *                server doesn't support ACLs.
     */
    function createACL($folder, $share_user, $acl)
    {
        if (!$this->_connect()) {
            return $this->_imap;
        }

        $acl_str = '';
        if (!empty($acl)) {
            foreach ($acl as $key => $val) {
                $acl_str .= $key;
            }
        }

        /* Can't call this as @imap_setacl() as suppressing errors leads to 
           imap_errors() returning nothing. */
        $result = imap_setacl($this->_imap, $folder, $share_user, $acl_str);

        if (!$result) {
            $errors = imap_errors();
            if (is_array($errors)) {
                $error_string = '';
                foreach ($errors as $err) {
                    if ($err == 'ACL not available on this IMAP server') {
                        $err .= _("This IMAP server does not support sharing folders.");
                    }
                    $error_string .= $err;
                }
                return PEAR::raiseError($error_string);
            }
            return PEAR::raiseError(sprintf(_("Couldn't give user '%s' the following rights for the folder '%s': %s"), $share_user, $folder, $acl_str));
        }

        return $result;
    }

    /**
     * Edits an ACL on an IMAP server
     *
     * @access public
     *
     * @param string $folder      The folder on which to edit the ACL.
     * @param string $share_user  The user to grant rights to.
     * @param array $acl          An array, the keys of which are the
     *                            rights to be granted (see RFC 2086).
     *
     * @return mixed  True on success, false on failure unless
     *                server doesn't support ACLs, returns 'no_support'
     */
    function editACL($folder, $share_user, $acl)
    {
        return $this->createACL($folder, $share_user, $acl);
    }

    /**
     * Attempts to get the result of a CAPABILITY command to
     * the current IMAP server. If protocol is imap/ssl, will
     * only attempt ssl connection with PHP >= 4.3.
     *
     * @access private
     *
     * @return array  An array containing the server's capabilities.
     */
    function _getCapability()
    {
        $capabilities = null;
        $server = $this->_params['hostspec'];
        $sub_proto = null;

        if (($pos = strpos($this->_params['protocol'], '/'))) {
            $sub_proto = substr($this->_params['protocol'], $pos + 1);
        }

        if ($sub_proto == 'ssl') {
            if (version_compare(phpversion(), '4.3.0') >= 0) {
                $server = $sub_proto . '://' . $server;
            } else {
                return PEAR::raiseError(_("Could not retrieve server's capabilities. SSL connections require PHP 4.3 or better"));
            }
        }

        $imap = fsockopen($server, $this->_params['port'], $errno, $errstr, 30);

        if (!$imap) {
            return PEAR::raiseError(_("Could not retrieve server's capabilities") . ' - ' . _("Connection failed: ") . $errno . ' : ' . $errstr);
            return null;
        } else {
            $response = fgets($imap, 4096);
            if (preg_match('/^\*\s+OK/', $response)) {
                fputs($imap, "x CAPABILITY\r\n");
                $response = trim(fgets($imap, 1024));
                if (preg_match('/^\*\s+CAPABILITY/', $response)) {
                    $response_array = explode(' ', $response);
                    foreach ($response_array as $var) {
                        if (strstr($var, '=')) {
                            $var2 = explode('=', $var, 2);
                            $capabilities[String::lower($var2[0])][String::lower($var2[1])] = 1;
                        } else {
                            $capabilities[String::lower($var)] = 1;
                        }
                    }

                } else {
                    fclose ($imap);
                    return PEAR::raiseError(_("Could not retrieve server's capabilities") . ' - ' . _("Unexpected response from server to: ") . '\'x CAPABILITY\' : ' . $response);
                }
            } else {
                fclose ($imap);
                return PEAR::raiseError(_("Could not retrieve server's capabilities") . ' - ' . _("Unexpected response from server on connection: ") . $response);
            }
            fclose ($imap);
        }

        return $capabilities;
    }

    /**
     * Attempts to retrieve the existing ACL for a folder from
     * the current IMAP server.
     *
     * @access public
     *
     * @param string folder  The folder to get the ACL for.
     *
     * @return array  A hash containing information on the ACL.
     * <pre>
     * Array (
     *   user => Array (
     *     right => 1
     *   )
     * )
     * </pre>
     */
    function getACL($folder)
    {
        if (isset($this->_caps['auth']['digest-md5'])) {
            return $this->_getACL($folder, 'digest-md5');
        } elseif (isset($this->_caps['auth']['cram-md5'])) {
            return $this->_getACL($folder, 'cram-md5');
        } else {
            return $this->_getACL($folder, 'login');
        }
    }

    /**
     * Attempts to retrieve the existing ACL for a folder from
     * the current IMAP server. If protocol is imap/ssl, will
     * only attempt ssl connection with PHP >= 4.3
     *
     * NB: if Auth_SASL is not installed this function will send
     * the users password to the IMAP server as plain text!!
     *
     * @access private
     *
     * @param string folder    The folder to get the ACL for.
     * @param string authMech  The authorisation mechanism to use.
     *                         One of cram-md5, digest-md5 or login.
     *
     * @return array  A hash containing information on the ACL
     * <pre>
     * Array (
     *   user => Array (
     *     right => 1
     *   )
     * )
     * </pre>
     */
    function _getACL($folder, $authMech)
    {
        global $notification;

        $have_sasl = false;
        $returnACL = array();
        $server = $this->_params['hostspec'];
        $sub_proto = null;
        $txid = 0;

        /* Silence warnings during check if Auth_SASL module is installed. */
        if (@include_once 'Auth/SASL.php') {
            $have_sasl = true;
        }

        $pass = $this->_params['password'];

        if (($pos = strpos($this->_params['protocol'], '/'))) {
            $sub_proto = substr($this->_params['protocol'], $pos+1);
        }

        if ($sub_proto == 'ssl') {
            if (version_compare(phpversion(), '4.3.0') >= 0) {
                $server = $sub_proto . '://' . $server;
            } else {
                return PEAR::raiseError(_("Could not retrieve ACL. SSL connections require PHP 4.3 or better"));
            }
        }

        // Quote the folder string if it contains non alpha-numeric
        // characters
        if (preg_match('/\W/',$folder)) {
            $folder = '"' . $folder . '"';
        }

        $imap = fsockopen($server, $this->_params['port'], $errno, $errstr, 30);

        if (!$imap) {
            return PEAR::raiseError(_("Could not retrieve ACL")
                . ' - ' . _("Connection failed: ") . $errno.' : ' . $errstr);
        } else {
            $response = fgets($imap, 4096);
            if (preg_match('/^\*\s+OK/', $response)) {

                // login using the preferred mechanism
                // default to login if Auth_SASL is not installed
                if ($have_sasl && ($authMech == 'cram-md5')) {
                    $login = Auth_SASL::factory('crammd5');

                    fputs($imap, "$txid AUTHENTICATE CRAM-MD5\r\n");
                    $challenge = explode(' ', trim(fgets($imap, 1024)));

                    $response = $login->getResponse($_SESSION['imp']['user'], $pass, base64_decode($challenge[1]));
                    fputs($imap, base64_encode($response) . "\r\n");

                } elseif($have_sasl && ($authMech == 'digest-md5')) {
                    $login = Auth_SASL::factory('digestmd5');

                    fputs($imap, "$txid AUTHENTICATE DIGEST-MD5\r\n");
                    $challenge = explode(' ', trim(fgets($imap, 1024)));

                    $response = $login->getResponse($_SESSION['imp']['user'], $pass, base64_decode($challenge[1]),
                        $_SESSION['imp']['server'], $_SESSION['imp']['base_protocol']);

                    fputs($imap, base64_encode($response) . "\r\n");
                    $response = explode(' ', trim(fgets($imap, 1024)));
                    $response = base64_decode($response[1]);
                    if (!strstr($response, 'rspauth=')) {
                        fclose($imap);
                        return PEAR::raiseError(_("Could not retrieve ACL")
                            . ' - ' . _("Unexpected response from server to: ") . 'Digest-MD5 response', 'horde.warning');
                    }
                    fputs($imap, "\r\n");

                } else {
                    if (preg_match('/\W/', $pass)) {
                        $pass = addslashes($pass);
                        $pass = '"' . $pass . '"';
                    }
                    fputs($imap, "$txid LOGIN " . $_SESSION['imp']['user'] . ' ' . $pass . "\r\n");

                }
                $response = trim(fgets($imap, 1024));
                if (preg_match("/^$txid\sOK/", $response)) {
                    $txid++;
                    fputs($imap, "$txid GETACL " . $folder . "\r\n");
                    $response = trim(fgets($imap, 4096));
                    if (preg_match('/^\*\s+ACL\s+(.*)/i', $response, $matches)) {
                        $res_arr = $this->_atomise($matches[1]);
                        $res_folder = array_shift($res_arr);
                        $is_key = 1;
                        $key = null;
                        foreach ($res_arr as $var) {
                            if ($is_key) {
                                $key = $var;
                                $is_key = 0;
                            } else {
                                $perms = preg_split('//', $var, -1, PREG_SPLIT_NO_EMPTY);
                                foreach ($perms as $p_key => $p_var) {
                                    $returnACL[$key][$p_var] = 1;
                                }
                                $is_key = 1;
                            }
                        }
                    } else {
                        fclose($imap);
                        return PEAR::raiseError(_("Could not retrieve ACL")
                            . ' - ' . _("Unexpected response from server to: ") . "'$txid GETACL' : " .$response);

                    }
                } else {
                    fclose($imap);
                    return PEAR::raiseError(_("Could not retrieve ACL")
                        . ' - ' . _("Unexpected response from server to: ") . 'login : ' . $response);

                }
            } else {
                fclose($imap);
                return PEAR::raiseError(_("Could not retrieve ACL")
                    . ' - ' . _("Unexpected response from server on connection: ") . $response);

            }
            fclose($imap);
        }

        return $returnACL;
    }

    /**
     * Can a user edit the ACL for this folder?
     *
     * @access public
     *
     * @param string $folder  The folder name.
     * @param string $user    A user name.
     *
     * @return boolean  True if $user has permission to edit the ACL on
     *                  $folder.
     */
    function canEdit($folder, $user)
    {
        /* We can't establish if the user is in a group with the
           'a' privilege, so just return true and leave the decision
           to the server */
        return true;
    }

    /**
     * Crudely split a string into 'atoms'
     *
     * @access private
     *
     * @param string $in  The string to split.
     *
     * @return array  An array of 'atoms'.
     */
    function _atomise($in)
    {
        $length = strlen($in);
        $qt = false;
        $idx = 0;
        $out = array();

        for ($i = 0; $i < $length; $i++) {
            $char = substr($in, $i, 1);
            if (($char == '"') && !$qt) {
                $qt = true;
                $idx++;
                continue;
            } elseif (($char == ' ') && !$qt) {
                $idx++;
            } elseif (($char == '"') && $qt) {
                $qt = false;
                $idx++;
            } else {
                if (empty($out[$idx])) {
                    $out[$idx] = $char;
                } else {
                    $out[$idx] .= $char;
                }
            }
        }

        return $out;
    }

}
