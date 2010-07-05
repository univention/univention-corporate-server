<?php
/**
 * Ingo_Driver_vfs:: Implements an Ingo storage driver using Horde VFS.
 *
 * $Horde: ingo/lib/Driver/vfs.php,v 1.12.10.17 2009-11-01 02:09:44 chuck Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author  Brent J. Nordquist <bjn@horde.org>
 * @author  Jan Schneider <jan@horde.org>
 * @package Ingo
 */
class Ingo_Driver_vfs extends Ingo_Driver {

    /**
     * Whether this driver allows managing other users' rules.
     *
     * @var boolean
     */
    var $_support_shares = true;

    /**
     * Constructs a new VFS-based storage driver.
     *
     * @param array $params  A hash containing driver parameters.
     */
    function Ingo_Driver_vfs($params = array())
    {
        $default_params = array(
            'hostspec' => 'localhost',
            'port'     => 21,
            'filename' => '.ingo_filter',
            'vfstype'  => 'ftp',
            'vfs_path' => '',
            'vfs_forward_path' => '',
        );
        $this->_params = array_merge($this->_params, $default_params, $params);
    }

    /**
     * Sets a script running on the backend.
     *
     * @param string $script  The filter script
     *
     * @return mixed  True on success, or PEAR_Error on failure.
     */
    function setScriptActive($script)
    {
        $result = $this->_connect();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (empty($script)) {
            $result = $this->_vfs->deleteFile($this->_params['vfs_path'], $this->_params['filename']);
        } else {
            $result = $this->_vfs->writeData($this->_params['vfs_path'], $this->_params['filename'], $script, true);
        }
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (isset($this->_params['file_perms']) && !empty($script)) {
            $result = $this->_vfs->changePermissions($this->_params['vfs_path'], $this->_params['filename'], $this->_params['file_perms']);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        // Get the backend; necessary if a .forward is needed for
        // procmail.
        $backend = Ingo::getBackend();
        if ($backend['script'] == 'procmail' && isset($backend['params']['forward_file']) && isset($backend['params']['forward_string'])) {
            if (empty($script)) {
                $result = $this->_vfs->deleteFile($this->_params['vfs_forward_path'], $backend['params']['forward_file']);
            } else {
                $result = $this->_vfs->writeData($this->_params['vfs_forward_path'], $backend['params']['forward_file'], $backend['params']['forward_string'], true);
            }
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            if (isset($this->_params['file_perms']) && !empty($script)) {
                $result = $this->_vfs->changePermissions($this->_params['vfs_forward_path'], $backend['params']['forward_file'], $this->_params['file_perms']);
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }
            }
        }

        return true;
    }

    /**
     * Returns the content of the currently active script.
     *
     * @return string  The complete ruleset of the specified user.
     */
    function getScript()
    {
        $result = $this->_connect();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        return $this->_vfs->read($this->_params['vfs_path'], $this->_params['filename']);
    }

    /**
     * Connect to the VFS server.
     *
     * @access private
     *
     * @return boolean  True on success, PEAR_Error on false.
     */
    function _connect()
    {
        /* Do variable substitution. */
        if (!empty($this->_params['vfs_path'])) {
            $user = Ingo::getUser();
            $domain = Ingo::getDomain();
            if ($_SESSION['ingo']['backend']['hordeauth'] !== 'full') {
                $pos = strpos($user, '@');
                if ($pos !== false) {
                    $domain = substr($user, $pos + 1);
                    $user = substr($user, 0, $pos);
                }
            }
            $this->_params['vfs_path'] = str_replace(
                array('%u', '%d', '%U'),
                array($user, $domain, $this->_params['username']),
                $this->_params['vfs_path']);
        }

        if (!empty($this->_vfs)) {
            return true;
        }

        require_once 'VFS.php';
        $this->_vfs = &VFS::singleton($this->_params['vfstype'], $this->_params);
        if (is_a($this->_vfs, 'PEAR_Error')) {
            $error = $this->_vfs;
            $this->_vfs = null;
            return $error;
        } else {
            return true;
        }
    }

}
