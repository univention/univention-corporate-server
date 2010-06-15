<?php
// +-----------------------------------------------------------------------+
// | Copyright (c) 2002-2003, Richard Heyes                                |
// | All rights reserved.                                                  |
// |                                                                       |
// | Redistribution and use in source and binary forms, with or without    |
// | modification, are permitted provided that the following conditions    |
// | are met:                                                              |
// |                                                                       |
// | o Redistributions of source code must retain the above copyright      |
// |   notice, this list of conditions and the following disclaimer.       |
// | o Redistributions in binary form must reproduce the above copyright   |
// |   notice, this list of conditions and the following disclaimer in the |
// |   documentation and/or other materials provided with the distribution.|
// | o The names of the authors may not be used to endorse or promote      |
// |   products derived from this software without specific prior written  |
// |   permission.                                                         |
// |                                                                       |
// | THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS   |
// | "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT     |
// | LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR |
// | A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT  |
// | OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, |
// | SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT      |
// | LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, |
// | DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY |
// | THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT   |
// | (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE |
// | OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.  |
// |                                                                       |
// +-----------------------------------------------------------------------+
// | Author: Richard Heyes <richard@phpguru.org>                           |
// +-----------------------------------------------------------------------+

require_once('Net/Socket.php');
require_once('Auth/SASL.php');

/**
* TODO
*
* o hasExtension()
* o getExtensions()
* o supportsAuthMech()
*/

/**
* Disconnected state
* @const NET_SIEVE_STATE_DISCONNECTED
*/
define('NET_SIEVE_STATE_DISCONNECTED',  1, true);

/**
* Authorisation state
* @const NET_SIEVE_STATE_AUTHORISATION
*/
define('NET_SIEVE_STATE_AUTHORISATION', 2, true);

/**
* Transaction state
* @const NET_SIEVE_STATE_TRANSACTION
*/
define('NET_SIEVE_STATE_TRANSACTION',   3, true);

/**
* A class for talking to the timsieved server which
* comes with Cyrus IMAP. Does not support the HAVESPACE
* command which appears to be broken (Cyrus 2.0.16).
*
* @author  Richard Heyes <richard@php.net>
* @access  public
* @version 0.8
* @package Net_Sieve
*/

class Net_Sieve
{
    /**
    * The socket object
    * @var object
    */
    var $_sock;

    /**
    * Info about the connect
    * @var array
    */
    var $_data;

    /**
    * Current state of the connection
    * @var integer
    */
    var $_state;

    /**
    * Constructor error is any
    * @var object
    */
    var $_error;

    /**
    * Constructor
    * Sets up the object, connects to the server and logs in. stores
    * any generated error in $this->_error, which can be retrieved
    * using the getError() method.
    *
    * @access public
    * @param  string $user      Login username
    * @param  string $pass      Login password
    * @param  string $host      Hostname of server
    * @param  string $port      Port of server
    * @param  string $logintype Type of login to perform
    * @param  string $euser     Effective User (if $user=admin, login as $euser)
    */
    function Net_Sieve($user, $pass, $host = 'localhost', $port = 2000, $logintype = 'PLAIN', $euser = '')
    {
        $this->_state = NET_SIEVE_STATE_DISCONNECTED;

        $this->_data['user'] = $user;
        $this->_data['pass'] = $pass;
        $this->_data['host'] = $host;
        $this->_data['port'] = $port;
        $this->_data['euser'] = $euser;
        $this->_sock = &new Net_Socket();

        if (PEAR::isError($res = $this->_connect($host, $port))) {
            $this->_error = $res;
            return;
        }

        if (PEAR::isError($res = $this->_login($user, $pass, $logintype, $euser))) {
            $this->_error = $res;
        }
    }

    /**
    * Returns an indexed array of scripts currently
    * on the server
    *
    * @access public
    * @return mixed Indexed array of scriptnames or PEAR_Error on failure
    */
    function listScripts()
    {
        if (is_array($scripts = $this->_cmdListScripts())) {
            $this->_active = $scripts[1];
            return $scripts[0];
        } else {
            return $scripts;
        }
    }

    /**
    * Returns the active script
    *
    * @access public
    * @return mixed The active scriptname or PEAR_Error on failure
    */
    function getActive()
    {
        if (!empty($this->_active)) {
            return $this->_active;

        } elseif (is_array($scripts = $this->_cmdListScripts())) {
            $this->_active = $scripts[1];
            return $scripts[1];
        }
    }

    /**
    * Sets the active script
    *
    * @access public
    * @param  string $scriptname The name of the script to be set as active
    * @return mixed              true on success, PEAR_Error on failure
    */
    function setActive($scriptname)
    {
        return $this->_cmdSetActive($scriptname);
    }

    /**
    * Retrieves a script
    *
    * @access public
    * @param  string $scriptname The name of the script to be retrieved
    * @return mixed              The script on success, PEAR_Error on failure
    */
    function getScript($scriptname)
    {
        return $this->_cmdGetScript($scriptname);
    }

    /**
    * Adds a script to the server
    *
    * @access public
    * @param  string $scriptname Name of the script
    * @param  string $script     The script
    * @param  bool   $makeactive Whether to make this the active script
    * @return mixed              true on success, PEAR_Error on failure
    */
    function installScript($scriptname, $script, $makeactive = false)
    {
        if (PEAR::isError($res = $this->_cmdPutScript($scriptname, $script))) {
            return $res;

        } elseif ($makeactive) {
            return $this->_cmdSetActive($scriptname);

        } else {
            return true;
        }
    }

    /**
    * Removes a script from the server
    *
    * @access public
    * @param  string $scriptname Name of the script
    * @return mixed              True on success, PEAR_Error on failure
    */
    function removeScript($scriptname)
    {
        return $this->_cmdDeleteScript($scriptname);
    }

    /**
    * Returns any error that may have been generated in the
    * constructor
    *
    * @access public
    * @return mixed False if no error, PEAR_Error otherwise
    */
    function getError()
    {
        return PEAR::isError($this->_error) ? $this->_error : false;
    }

    /**
    * Handles connecting to the server and checking the
    * response is valid.
    *
    * @access private
    * @param  string $host Hostname of server
    * @param  string $port Port of server
    * @return mixed        True on success, PEAR_Error otherwise
    */
    function _connect($host, $port)
    {
        if (NET_SIEVE_STATE_DISCONNECTED == $this->_state) {
            if (PEAR::isError($res = $this->_sock->connect($host, $port, null, 5))) {
                return $res;
            }
            // Get logon greeting/capability and parse
            if(!PEAR::isError($res = $this->_getResponse())) {
                $this->_parseCapability($res);
                $this->_state = NET_SIEVE_STATE_AUTHORISATION;
                if (!isset($this->_capability['sasl'])) {
                    return PEAR::raiseError('No authentication mechanisms available.');
                }
                return true;
            } else {
                return PEAR::raiseError('Failed to connect, server said: ' . $res->getMessage());
            }
        } else {
            return PEAR::raiseError('Not currently in DISCONNECTED state');
        }
    }

    /**
    * Logs into server.
    *
    * @access private
    * @param  string $user      Login username
    * @param  string $pass      Login password
    * @param  string $logintype Type of login method to use
    * @param  string $euser     Effective UID (perform on behalf of $euser)
    * @return mixed             True on success, PEAR_Error otherwise
    */
    function _login($user, $pass, $logintype = 'PLAIN', $euser = '')
    {
        if (NET_SIEVE_STATE_AUTHORISATION != $this->_state) {
            return PEAR::raiseError('Not currently in AUTHORISATION state');
        }            
            
        if (!in_array($logintype, $this->_capability['sasl'])) {
            return PEAR::raiseError(sprintf('Authentication mechanism %s not supported by this server.', $logintype));
        }

        $sasl = &Auth_SASL::factory($logintype);
        if (PEAR::isError($sasl)) {
            return $sasl;
        }

        switch ($logintype) {
        case 'PLAIN':
            $this->_sendCmd(sprintf('AUTHENTICATE "PLAIN" "%s"',
                                    base64_encode($sasl->getResponse($user, $pass, $euser))));
            break;
        case 'LOGIN':
            $this->_sendCmd('AUTHENTICATE "LOGIN"');
            $this->_sendCmd('"' . base64_encode($user) . '"');
            $this->_sendCmd('"' . base64_encode($pass) . '"');
            break;
        default:
            return PEAR::raiseError(sprintf('Authentication mechanism %s not supported by this client.', $logintype));
        }
        
        if (!PEAR::isError($res = $this->_getResponse())) {
            $this->_state = NET_SIEVE_STATE_TRANSACTION;
            return true;
        } else {
            return $res;
        }
    }

    /**
    * Removes a script from the server
    *
    * @access private
    * @param  string $scriptname Name of the script to delete
    * @return mixed              True on success, PEAR_Error otherwise
    */
    function _cmdDeleteScript($scriptname)
    {
        if (NET_SIEVE_STATE_TRANSACTION === $this->_state) {
            $this->_sendCmd(sprintf('DELETESCRIPT "%s"', $scriptname));

            if (PEAR::isError($res = $this->_getResponse())) {
                return $res;
            } else {
                return true;
            }
        } else {
            return PEAR::raiseError('Not currently in TRANSACTION state');
        }
    }

    /**
    * Retrieves the contents of the named script
    *
    * @access private
    * @param  string $scriptname Name of the script to retrieve
    * @return mixed              The script if successful, PEAR_Error otherwise
    */
    function _cmdGetScript($scriptname)
    {
        if (NET_SIEVE_STATE_TRANSACTION === $this->_state) {
            $this->_sendCmd(sprintf('GETSCRIPT "%s"', $scriptname));
            if (PEAR::isError($res = $this->_getResponse())) {
                return $res;
            } else {
                return preg_replace('/{[0-9]+}\r\n/', '', $res);
            }
        } else {
            return PEAR::raiseError('Not currently in TRANSACTION state');
        }
    }

    /**
    * Sets the ACTIVE script, ie the one that gets run on new mail
    * by the server
    *
    * @access private
    * @param  string $scriptname The name of the script to mark as active
    * @return mixed              True on success, PEAR_Error otherwise
    */
    function _cmdSetActive($scriptname)
    {
        if (NET_SIEVE_STATE_TRANSACTION === $this->_state) {
            $this->_sendCmd(sprintf('SETACTIVE "%s"', $scriptname));

            if (PEAR::isError($res = $this->_getResponse())) {
                return $res;
            } else {
                $this->_activeScript = $scriptname;
                return true;
            }
        } else {
            return PEAR::raiseError('Not currently in TRANSACTION state');
        }
    }

    /**
    * Sends the LISTSCRIPTS command
    *
    * @access private
    * @return mixed Two item array of scripts, and active script on success,
    *               PEAR_Error otherwise.
    */
    function _cmdListScripts()
    {
        if (NET_SIEVE_STATE_TRANSACTION === $this->_state) {
            $scripts = array();
            $activescript = null;
            $this->_sendCmd('LISTSCRIPTS');
            if (PEAR::isError($res = $this->_getResponse())) {
                return $res;
            } else {
                $res = explode("\r\n", $res);
                foreach ($res as $value) {
                    if (preg_match('/^"(.*)"( ACTIVE)?$/i', $value, $matches)) {
                        $scripts[] = $matches[1];
                        if (!empty($matches[2])) {
                            $activescript = $matches[1];
                        }
                    }
                }
                return array($scripts, $activescript);
            }
        } else {
            return PEAR::raiseError('Not currently in TRANSACTION state');
        }
    }

    /**
    * Sends the PUTSCRIPT command to add a script to
    * the server.
    *
    * @access private
    * @param  string $scriptname Name of the new script
    * @param  string $scriptdata The new script
    * @return mixed              True on success, PEAR_Error otherwise
    */
    function _cmdPutScript($scriptname, $scriptdata)
    {
        if (NET_SIEVE_STATE_TRANSACTION === $this->_state) {
            $this->_sendCmd(sprintf('PUTSCRIPT "%s" {%d+}', $scriptname, strlen($scriptdata)));
            $this->_sendCmd($scriptdata);
            if (!PEAR::isError($res = $this->_getResponse())) {
                return true;
            } else {
                return $res;
            }
        } else {
            return PEAR::raiseError('Not currently in TRANSACTION state');
        }
    }

    /**
    * Sends the LOGOUT command and terminates the connection
    *
    * @access private
    * @return mixed True on success, PEAR_Error otherwise
    */
    function _cmdLogout()
    {
        if (NET_SIEVE_STATE_DISCONNECTED !== $this->_state) {
            $this->_sendCmd('LOGOUT');
            if (!PEAR::isError($res = $this->_getResponse())) {
                $this->_sock->disconnect();
                $this->_state = NET_SIEVE_STATE_DISCONNECTED;
                return true;
            } else {
                return $res;
            }
        } else {
            return PEAR::raiseError('Not currently connected');
        }
    }

    /**
    * Sends the CAPABILITY command
    *
    * @access private
    * @return mixed True on success, PEAR_Error otherwise
    */
    function _cmdCapability()
    {
        if (NET_SIEVE_STATE_TRANSACTION === $this->_state) {
            $this->_sendCmd('CAPABILITY');
            if (!PEAR::isError($res = $this->_getResponse())) {
                $this->_parseCapability($res);
                return true;
            } else {
                return $res;
            }
        } else {
            return PEAR::raiseError('Not currently in TRANSACTION state');
        }
    }

    /**
    * Parses the response from the capability command. Stores
    * the result in $this->_capability
    *
    * @access private
    */
    function _parseCapability($data)
    {
        $data = preg_split('/\r?\n/', $data, -1, PREG_SPLIT_NO_EMPTY);

        for ($i = 0; $i < count($data); $i++) {
            if (preg_match('/^"([a-z]+)" ("(.*)")?$/i', $data[$i], $matches)) {
                switch (strtolower($matches[1])) {
                    case 'implementation':
                        $this->_capability['implementation'] = $matches[3];
                        break;

                    case 'sasl':
                        $this->_capability['sasl'] = preg_split('/\s+/', $matches[3]);
                        break;

                    case 'sieve':
                        $this->_capability['extensions'] = preg_split('/\s+/', $matches[3]);
                        break;

                    case 'starttls':
                        $this->_capability['starttls'] = true;
                }
            }
        }
    }

    /**
    * Sends a command to the server
    *
    * @access private
    * @param string $cmd The command to send
    */
    function _sendCmd($cmd)
    {
        $this->_sock->writeLine($cmd);
    }

    /**
    * Retrieves a response from the server and, to a certain degree,
    * parses it.
    *
    * @access private
    * @return mixed Reponse string if an OK response, PEAR_Error if a NO response
    */
    function _getResponse()
    {
        $response = '';

        while (true) {
            $line = $this->_sock->readLine();
            if ('ok' == strtolower(substr($line, 0, 2))) {
                return rtrim($response);

            } elseif ('no' == strtolower(substr($line, 0, 2))) {
                // Check for string literal error message
                if (preg_match('/^no {([0-9]+)\+?}/i', $line, $matches)) {
                    $line .= str_replace("\r\n", ' ', $this->_sock->read($matches[1]));
                }
                return PEAR::raiseError(trim($response . substr($line, 2)));
            } elseif ('bye' == strtolower(substr($line, 0, 3))) {
                if (preg_match('/^bye \((referral) "([^"]+)/i', $line, $matches)) {
                    $line = $matches[1] . " " . $matches[2];
                }
                return PEAR::raiseError(trim($response . $line));
            }

            $response .= $line . "\r\n";
        }
    }
}

