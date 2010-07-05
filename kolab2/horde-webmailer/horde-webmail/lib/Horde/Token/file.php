<?php
/**
 * Token tracking implementation for local files.
 *
 * Optional parameters:<pre>
 *   'token_dir'  The directory where to keep token files.
 *   'timeout'    The period (in seconds) after which an id is purged.
 *                Defaults to 86400 (i.e. 24 hours).</pre>
 *
 * $Horde: framework/Token/Token/file.php,v 1.19.6.11 2009-01-06 15:23:44 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Max Kalika <max@horde.org>
 * @since   Horde 1.3
 * @package Horde_Token
 */
class Horde_Token_file extends Horde_Token {

    /**
     * Handle for the open file descriptor.
     *
     * @var resource
     */
    var $_fd = false;

    /**
     * Boolean indicating whether or not we have an open file descriptor.
     *
     * @var boolean
     */
    var $_connected = false;

    /**
     * Create a new file based token-tracking container.
     *
     * @param array $params  A hash containing storage parameters.
     */
    function Horde_Token_file($params = array())
    {
        $this->_params = $params;

        /* Choose the directory to save the stub files. */
        if (!isset($this->_params['token_dir'])) {
            $this->_params['token_dir'] = Util::getTempDir();
        }

        /* Set timeout to 24 hours if not specified. */
        if (!isset($this->_params['timeout'])) {
            $this->_params['timeout'] = 86400;
        }
    }

    /**
     * Deletes all expired connection id's from the SQL server.
     *
     * @return boolean True on success, a PEAR_Error object on failure.
     */
    function purge()
    {
        // Make sure we have no open file descriptors before unlinking
        // files.
        if (!$this->_disconnect()) {
            return PEAR::raiseError('Unable to close file descriptors');
        }

        /* Build stub file list. */
        if (!($dir = opendir($this->_params['token_dir']))) {
            return PEAR::raiseError('Unable to open token directory');
        }

        /* Find expired stub files */
        while (($dirEntry = readdir($dir)) != '') {
            if (preg_match('|^conn_\w{8}$|', $dirEntry) && (time() - filemtime($this->_params['token_dir'] . '/' . $dirEntry) >= $this->_params['timeout'])) {
                if (!@unlink($this->_params['token_dir'] . '/' . $dirEntry)) {
                    return PEAR::raiseError('Unable to purge token file.');
                }
            }
        }

        closedir($dir);
        return true;
    }

    function exists($tokenID)
    {
        if (is_a(($result = $this->_connect($tokenID)), 'PEAR_Error')) {
            return $result;
        }

        /* Find already used IDs. */
        $fileContents = file($this->_params['token_dir'] . '/conn_' . $this->encodeRemoteAddress());
        if ($fileContents) {
            $iMax = count($fileContents);
            for ($i = 0; $i < $iMax; $i++) {
                if (chop($fileContents[$i]) == $tokenID) {
                    return true;
                }
            }
        }

        return false;
    }

    function add($tokenID)
    {
        if (is_a(($result = $this->_connect($tokenID)), 'PEAR_Error')) {
            return $result;
        }

        /* Write the entry. */
        fwrite($this->_fd, "$tokenID\n");

        /* Return an error if the update fails, too. */
        if (!$this->_disconnect()) {
            return PEAR::raiseError('Failed to close token file cleanly.');
        }

        return true;
    }

    /**
     * Opens a file descriptor to a new or existing file.
     *
     * @return boolean  True on success, a PEAR_Error object on failure.
     */
    function _connect($tokenID)
    {
        if (!$this->_connected) {

            // Open a file descriptor to the token stub file.
            $this->_fd = @fopen($this->_params['token_dir'] . '/conn_' . $this->encodeRemoteAddress(), 'a');
            if (!$this->_fd) {
                return PEAR::raiseError('Failed to open token file.');
            }

            $this->_connected = true;
        }

        return true;
    }

    /**
     * Closes the file descriptor.
     *
     * @return boolean  True on success, false on failure.
     */
    function _disconnect()
    {
        if ($this->_connected) {
            $this->_connected = false;
            return fclose($this->_fd);
        }

        return true;
    }

}
