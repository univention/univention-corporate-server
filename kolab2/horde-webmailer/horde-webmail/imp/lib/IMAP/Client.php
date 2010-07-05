<?php

define('IMP_IMAPCLIENT_TAGGED', 0);
define('IMP_IMAPCLIENT_UNTAGGED', 1);
define('IMP_IMAPCLIENT_CONTINUATION', 2);

/**
 * The IMP_IMAPClient:: class enables connection to an IMAP server through
 * built-in PHP functions.
 *
 * TODO: This should eventually be moved to Horde 4.0/framework.
 *
 * $Horde: imp/lib/IMAP/Client.php,v 1.21.2.36 2009-08-05 08:36:37 slusarz Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * Based on code from:
 *   + auth.php (1.49)
 *   + imap_general.php (1.212)
 *   + strings.php (1.184.2.35)
 *   from the Squirrelmail project.
 *   Copyright 1999-2005 The SquirrelMail Project Team
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @since   IMP 4.1
 * @package IMP
 */
class IMP_IMAPClient {

    /**
     * The list of capabilities of the IMAP server.
     *
     * @var array
     */
    var $_capability = null;

    /**
     * The hostname of the IMAP server to connect to.
     *
     * @var string
     */
    var $_host;

    /**
     * The namespace information.
     *
     * @var array
     */
    var $_namespace = null;

    /**
     * The port number of the IMAP server to connect to.
     *
     * @var string
     */
    var $_port;

    /**
     * The unique ID to use when making an IMAP query.
     *
     * @var integer
     */
    var $_sessionid = 1;

    /**
     * The currently active tag.
     *
     * @var string
     */
    var $_currtag = null;

    /**
     * The socket connection to the IMAP server.
     *
     * @var resource
     */
    var $_stream;

    /**
     * Are we using SSL to connect to the IMAP server?
     *
     * @var string
     */
    var $_usessl = false;

    /**
     * Are we using TLS to connect to the IMAP server?
     *
     * @var string
     */
    var $_usetls = false;

    /**
     * Constructor.
     *
     * @param string $host      The address/hostname of the IMAP server.
     * @param string $port      The port to connect to on the IMAP server.
     * @param string $protocol  The protocol string (See, e.g., servers.php).
     */
    function IMP_IMAPClient($host, $port, $protocol)
    {
        $this->_host = $host;
        $this->_port = $port;

        /* Split apart protocol string to discover if we need to use either
         * SSL or TLS. */
        $tmp = explode('/', strtolower($protocol));
        if (in_array('tls', $tmp)) {
            $this->_usetls = true;
        } elseif (in_array('ssl', $tmp)) {
            $this->_usessl = true;
        }
    }

    /**
     * Are we using TLS to connect and is it supported?
     *
     * @return mixed  Returns true if TLS is being used to connect, false if
     *                is not, and PEAR_Error if we are attempting to use TLS
     *                and this version of PHP doesn't support it.
     */
    function useTLS()
    {
        if ($this->_usetls) {
            /* There is no way in PHP 4 to open a TLS connection to a
             * non-secured port.  See http://bugs.php.net/bug.php?id=26040 */
            if (!function_exists('stream_socket_enable_crypto')) {
                return PEAR::raiseError(_("To use a TLS connection, you must be running a version of PHP 5.1.0 or higher."), 'horde.error');
            }
        }

        return $this->_usetls;
    }

    /**
     * Generates a new IMAP session ID by incrementing the last one used.
     *
     * @access private
     *
     * @return string  IMAP session id of the form 'A000'.
     */
    function _generateSid()
    {
        return sprintf("A%03d", $this->_sessionid++);
    }

    /**
     * Perform a command on the IMAP server.
     *
     * @access private
     *
     * @param string $query  The IMAP command to execute.
     *
     * @return stdClass  Returns PEAR_Error on error.  On success, returns
     *                   a stdClass object with the following elements:
     * <pre>
     * 'message' - The response message
     * 'response' - The response code
     * 'type' - Either IMP_IMAPCLIENT_TAGGED, IMP_IMAPCLIENT_UNTAGGED, or
     *          IMP_IMAPCLIENT_CONTINUATION
     * </pre>
     */
    function _runCommand($query)
    {
        if (!$this->_currtag) {
            $this->_currtag = $this->_generateSid();
            $query = $this->_currtag . ' ' . $query;
        }

        fwrite($this->_stream, $query . "\r\n");
        $ob = $this->_parseLine();
        if (is_a($ob, 'PEAR_Error')) {
            $this->_currtag = null;
            return $ob;
        }

        switch ($ob->response) {
        case 'OK':
            break;

        case 'NO':
            /* Ignore this error from M$ exchange, it is not fatal (aka
             * bug). */
            if (strstr($ob->message, 'command resulted in') === false) {
                $this->_currtag = null;
                return PEAR::raiseError(sprintf(_("Could not complete request. Reason Given: %s"), $ob->message), 'horde.error', null, null, $ob->response);
            }
            break;

        case 'BAD':
            $this->_currtag = null;
            return PEAR::raiseError(sprintf(_("Bad or malformed request. Server Responded: %s"), $ob->message), 'horde.error', null, null, $ob->response);
            break;

        case 'BYE':
            $this->_currtag = null;
            return PEAR::raiseError(sprintf(_("IMAP Server closed the connection. Server Responded: %s"), $ob->message), 'horde.error', null, null, $ob->response);
            break;

        default:
            $this->_currtag = null;
            return PEAR::raiseError(sprintf(_("Unknown IMAP response from the server. Server Responded: %s"), $ob->message), 'horde.error', null, null, $ob->response);
            break;
        }

        if ($ob->type != IMP_IMAPCLIENT_CONTINUATION) {
            $this->_currtag = null;
        }

        return $ob;
    }

    /**
     * TODO
     *
     * @access private
     *
     * @return stdClass  See _runCommand().
     */
    function _parseLine()
    {
        $ob = new stdClass;
        $read = explode(' ', trim(fgets($this->_stream)), 2);

        switch ($read[0]) {
        /* Continuation response. */
        case '+':
            $ob->message = isset($read[1]) ? trim($read[1]) : '';
            $ob->response = 'OK';
            $ob->type = IMP_IMAPCLIENT_CONTINUATION;
            break;

        /* Untagged response. */
        case '*':
            $tmp = explode(' ', $read[1], 2);
            $ob->response = trim($tmp[0]);
            if (in_array($ob->response, array('OK', 'NO', 'BAD', 'PREAUTH', 'BYE'))) {
                $ob->message = trim($tmp[1]);
            } else {
                $ob->response = 'OK';
                $ob->message = $read[1];
            }
            $ob->type = IMP_IMAPCLIENT_UNTAGGED;
            $ob2 = $this->_parseLine();
            if ($ob2->response != 'OK') {
                $ob = $ob2;
            } elseif ($ob2->type == IMP_IMAPCLIENT_UNTAGGED) {
                $ob->message .= "\n" . $ob2->message;
            } else {
                $ob->response = $ob2->response;
            }
            break;

        /* Tagged response. */
        default:
            $tmp = explode(' ', $read[1], 2);
            $ob->type = IMP_IMAPCLIENT_TAGGED;
            if ($this->_currtag && ($read[0] == $this->_currtag)) {
                $ob->message = trim($tmp[1]);
                $ob->response = trim($tmp[0]);
            } else {
                $ob->message = $read[0];
                $ob->response = '';
            }
            break;
        }

        return $ob;
    }

    /**
     * Connects to the IMAP server.
     *
     * @access private
     *
     * @return mixed  Returns true on success, PEAR_Error on error.
     */
    function _createStream()
    {
        if (($this->_usessl || $this->_usetls) &&
            !Util::extensionExists('openssl')) {
            return PEAR::raiseError(_("If using SSL or TLS, you must have the PHP openssl extension loaded."), 'horde.error');
        }

        if ($res = $this->useTLS()) {
            if (is_a($res, 'PEAR_Error')) {
                return $res;
            } else {
                $this->_host = 'tcp://' . $this->_host . ':' . $this->_port;
            }
        }

        if ($this->_usessl) {
            $this->_host = 'ssl://' . $this->_host;
        }
        $error_number = $error_string = '';
        $timeout = 10;

        if ($this->_usetls) {
            $this->_stream = stream_socket_client($this->_host, $error_number, $error_string, $timeout);
            if (!$this->_stream) {
                return PEAR::raiseError(sprintf(_("Error connecting to IMAP server: [%s] %s."), $error_number, $error_string), 'horde.error');
            }

            /* Disregard any server information returned. */
            fgets($this->_stream);

            /* Send the STARTTLS command. */
            $res = $this->_runCommand('STARTTLS');

            /* Switch over to a TLS connection. */
            if (!is_a($res, 'PEAR_Error')) {
                $res = stream_socket_enable_crypto($this->_stream, true, STREAM_CRYPTO_METHOD_TLS_CLIENT);
            }
            if (!$res || is_a($res, 'PEAR_Error')) {
                $this->logout();
                return PEAR::raiseError(_("Could not open secure connection to the IMAP server."), 'horde.error');
            }
        } else {
            $this->_stream = fsockopen($this->_host, $this->_port, $error_number, $error_string, $timeout);
            if (!$this->_stream) {
                return PEAR::raiseError(sprintf(_("Error connecting to IMAP server: [%s] %s."), $error_number, $error_string), 'horde.error');
            }

            /* Disregard server information. */
            fgets($this->_stream);
        }

        register_shutdown_function(array(&$this, 'logout'));
    }

    /**
     * Log the user into the IMAP server.
     *
     * @param string $username  Username.
     * @param string $password  Encrypted password.
     *
     * @return mixed  True on success, PEAR_Error on error.
     */
    function login($username, $password)
    {
        $res = $this->_createStream();
        if (is_a($res, 'PEAR_Error')) {
            Horde::logMessage($res, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $res;
        }

        $imap_auth_mech = array();

        /* Use md5 authentication, if available. But no need to use special
         * authentication if we are already using an encrypted connection. */
        $auth_methods = $this->queryCapability('AUTH');
        if (!$this->_usessl && !$this->_usetls && !empty($auth_methods)) {
            if (in_array('CRAM-MD5', $auth_methods)) {
                $imap_auth_mech[] = 'cram-md5';
            }
            if (in_array('DIGEST-MD5', $auth_methods)) {
                $imap_auth_mech[] = 'digest-md5';
            }
        }

        /* Next, try 'PLAIN' authentication. */
        if (!empty($auth_methods) && in_array('PLAIN', $auth_methods)) {
            $imap_auth_mech[] = 'plain';
        }

        /* Fall back to 'LOGIN' if available. */
        if (!$this->queryCapability('LOGINDISABLED')) {
            $imap_auth_mech[] = 'login';
        }

        if (empty($imap_auth_mech)) {
            return PEAR::raiseError(_("No supported IMAP authentication method could be found."), 'horde.error');
        }

        foreach ($imap_auth_mech as $method) {
            $res = $this->_login($username, $password, $method);
            if (!is_a($res, 'PEAR_Error')) {
                return true;
            } else {
                Horde::logMessage($res, __FILE__, __LINE__, PEAR_LOG_WARNING);
            }
        }

        return $res;
    }

    /**
     * Log the user into the IMAP server.
     *
     * @access private
     *
     * @param string $username  Username.
     * @param string $password  Encrypted password.
     * @param string $method    IMAP login method.
     *
     * @return mixed  True on success, PEAR_Error on error.
     */
    function _login($username, $password, $method)
    {
        switch ($method) {
        case 'cram-md5':
        case 'digest-md5':
            /* If we don't have Auth_SASL package install, return error. */
            if (!@include_once 'Auth/SASL.php') {
                return PEAR::raiseError(_("CRAM-MD5 or DIGEST-MD5 requires PEAR's Auth_SASL package to be installed."), 'horde.error');
            }

            $res = $this->_runCommand('AUTHENTICATE ' . $method);
            if (is_a($res, 'PEAR_Error')) {
                return $res;
            }

            if ($method == 'cram-md5') {
                $auth_sasl = Auth_SASL::factory('crammd5');
                $response = $auth_sasl->getResponse($username, $password, base64_decode($res->message));
                $read = $this->_runCommand(base64_encode($response));
            } elseif ($method == 'digest-md5') {
                $auth_sasl = Auth_SASL::factory('digestmd5');
                $response = $auth_sasl->getResponse($username, $password, base64_decode($res->message), $this->_host, 'imap');
                $res = $this->_runCommand(base64_encode($response));
                if (is_a($res, 'PEAR_Error')) {
                    return $res;
                }
                $response = base64_decode($res->message);
                if (strpos($response, 'rspauth=') === false) {
                    return PEAR::raiseError(_("Unexpected response from server to Digest-MD5 response."), 'horde.error');
                }
                $read = $this->_runCommand('');
            } else {
                return PEAR::raiseError(_("The IMAP server does not appear to support the authentication method selected. Please contact your system administrator."), 'horde.error');
            }
            break;

        case 'login':
            /* We should use a literal string to send the username, but some
             * IMAP servers don't support a literal string request inside of a
             * literal string. Thus, use a quoted string for the username
             * (which should probably be OK since it is very unlikely a
             * username will include a double-quote character). */
            $read = $this->_runCommand("LOGIN \"$username\" {" . strlen($password) . "}");
            if (!is_a($read, 'PEAR_Error') &&
                ($read->type == IMP_IMAPCLIENT_CONTINUATION)) {
                $read = $this->_runCommand($password);
            }
            break;

        case 'plain':
            $sasl = $this->queryCapability('SASL-IR');
            $auth = base64_encode("$username\0$username\0$password");
            if ($sasl) {
                // IMAP Extension for SASL Initial Client Response
                // <draft-siemborski-imap-sasl-initial-response-01b.txt>
                $read = $this->_runCommand("AUTHENTICATE PLAIN $auth");
            } else {
                $read = $this->_runCommand("AUTHENTICATE PLAIN");
                if (!is_a($read, 'PEAR_Error') &&
                    ($read->type == IMP_IMAPCLIENT_CONTINUATION)) {
                    $read = $this->_runCommand($auth);
                } else {
                    return PEAR::raiseError(_("Unexpected response from server to AUTHENTICATE command."), 'horde.error');
                }
            }
            break;
        }

        if (is_a($read, 'PEAR_Error')) {
            return $read;
        }

        /* Check for failed login. */
        if ($read->response != 'OK') {
            $message = !empty($read->message) ? htmlspecialchars($read->message) : _("No message returned.");

            switch ($read->response) {
            case 'NO':
                return PEAR::raiseError(sprintf(_("Bad login name or password."), $message), 'horde.error');

            case 'BAD':
            default:
                return PEAR::raiseError(sprintf(_("Bad request: %s"), $message), 'horde.error');
            }
        }

        return true;
    }

    /**
     * Log out of the IMAP session.
     */
    function logout()
    {
        if (!empty($this->_stream)) {
            $this->_runCommand('LOGOUT');
            fclose($this->_stream);
        }
    }

    /**
     * Get the CAPABILITY string from the IMAP server.
     *
     * @access private
     */
    function _capability()
    {
        if ($this->_capability !== null) {
            return;
        }

        $this->_capability = array();
        $read = $this->_runCommand('CAPABILITY');
        if (is_a($read, 'PEAR_Error')) {
            Horde::logMessage($read, __FILE__, __LINE__, PEAR_LOG_ERR);
            return;
        }

        $c = explode(' ', $read->message);
        for ($i = 2; $i < count($c); $i++) {
            $cap_list = explode('=', $c[$i]);
            if (isset($cap_list[1])) {
                if (!isset($this->_capability[$cap_list[0]]) ||
                    !is_array($this->_capability[$cap_list[0]])) {
                    $this->_capability[$cap_list[0]] = array();
                }
                $this->_capability[$cap_list[0]][] = $cap_list[1];
            } elseif (!isset($this->_capability[$cap_list[0]])) {
                $this->_capability[$cap_list[0]] = true;
            }
        }
    }

    /**
     * Returns whether the IMAP server supports the given capability.
     *
     * @param string $capability  The capability string to query. If null,
     *                            returns the entire capability array.
     *
     * @param mixed  True if the server supports the queried capability,
     *               false if it doesn't, or an array if the capability can
     *               contain multiple values.
     */
    function queryCapability($capability)
    {
        $this->_capability();
        return ($capability === null) ? $this->_capability : (isset($this->_capability[$capability]) ? $this->_capability[$capability] : false);
    }

    /**
     * Get the NAMESPACE information from the IMAP server.
     *
     * @param array $additional  If the server supports namespaces, any
     *                           additional namespaces to add to the
     *                           namespace list that are not broadcast by
     *                           the server.
     *
     * @return array  An array with the following format:
     * <pre>
     * Array
     * (
     *   [foo1] => Array
     *   (
     *     [name] => (string)
     *     [delimiter] => (string)
     *     [type] => [personal|other|shared] (string)
     *     [hidden] => (boolean)
     *   )
     *
     *   [foo2] => Array
     *   (
     *     ...
     *   )
     * )
     * </pre>
     *                Returns PEAR_Error object on error.
     */
    function getNamespace($additional = array())
    {
        if ($this->_namespace !== null) {
            return $this->_namespace;
        }

        $namespace_array = array(
            1 => 'personal',
            2 => 'other',
            3 => 'shared'
        );

        if ($this->queryCapability('NAMESPACE')) {
            /* According to RFC 2342, response from NAMESPACE command is:
             * * NAMESPACE (PERSONAL NAMESPACES) (OTHER_USERS NAMESPACE) (SHARED NAMESPACES)
             */
            $read = $this->_runCommand('NAMESPACE');
            if (is_a($read, 'PEAR_Error')) {
                Horde::logMessage($read, __FILE__, __LINE__, PEAR_LOG_ERR);
                return $read;
            }

            if (($read->type == IMP_IMAPCLIENT_UNTAGGED) &&
                eregi('NAMESPACE +(\\( *\\(.+\\) *\\)|NIL) +(\\( *\\(.+\\) *\\)|NIL) +(\\( *\\(.+\\) *\\)|NIL)', $read->message, $data)) {
                for ($i = 1; $i <= 3; $i++) {
                    if ($data[$i] == 'NIL') {
                        continue;
                    }
                    $pna = explode(')(', $data[$i]);
                    while (list($k, $v) = each($pna)) {
                        $lst = explode('"', $v);
                        $delimiter = (isset($lst[3])) ? $lst[3] : '';
                        $this->_namespace[$lst[1]] = array('name' => $lst[1], 'delimiter' => $delimiter, 'type' => $namespace_array[$i], 'hidden' => false);
                    }
                }
            }

            foreach ($additional as $val) {
                /* Skip namespaces if we have already auto-detected them.
                 * Also, hidden namespaces cannot be empty. */
                $val = trim($val);
                if (empty($val) || isset($this->_namespace[$val])) {
                    continue;
                }
                $read = $this->_runCommand('LIST "" "' . $val . '"');
                if (is_a($read, 'PEAR_Error')) {
                    Horde::logMessage($read, __FILE__, __LINE__, PEAR_LOG_ERR);
                    return $read;
                }
                if (($read->type == IMP_IMAPCLIENT_UNTAGGED) &&
                    preg_match("/^LIST \(.*\) \"(.*)\" \"?(.*?)\"?\s*$/", $read->message, $data) &&
                    ($data[2] == $val)) {
                    $this->_namespace[$val] = array('name' => $val, 'delimiter' => $data[1], 'type' => $namespace_array[3], 'hidden' => true);
                }
            }
        }

        if (empty($this->_namespace)) {
            $res = $this->_runCommand('LIST "" ""');
            if (is_a($res, 'PEAR_Error')) {
                Horde::logMessage($res, __FILE__, __LINE__, PEAR_LOG_ERR);
                return $res;
            }
            $quote_position = strpos($res->message, '"');
            $this->_namespace[''] = array('name' => '', 'delimiter' => substr($res->message, $quote_position + 1 , 1), 'type' => $namespace_array[1], 'hidden' => false);
        }

        return $this->_namespace;
    }

    /**
     * Determines whether the IMAP search command supports the optional
     * charset provided.
     *
     * @param string $charset  The character set to test.
     *
     * @return boolean  True if the IMAP search command supports the charset.
     */
    function searchCharset($charset)
    {
        $read = $this->_runCommand('SELECT INBOX');
        if (!is_a($read, 'PEAR_Error')) {
            $read = $this->_runCommand('SEARCH CHARSET ' . $charset . ' TEXT "charsettest" 1');
        }
        return !is_a($read, 'PEAR_Error');
    }

}
