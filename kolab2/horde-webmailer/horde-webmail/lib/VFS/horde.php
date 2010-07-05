<?php
/**
 * VFS implementation for the Horde Application Framework.
 *
 * Required parameters:<pre>
 *   'horde_base'  Filesystem location of a local Horde installation.</pre>
 *
 * Optional parameters:<pre>
 *   'user'      A valid Horde user name.
 *   'password'  The user's password.</pre>
 *
 * $Horde: framework/VFS/lib/VFS/horde.php,v 1.1.2.3 2009-01-06 15:23:47 jan Exp $
 *
 * Copyright 2006-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.2
 * @package VFS
 */
class VFS_horde extends VFS {

    /**
     * Reference to a Horde Registry instance.
     *
     * @var Registry
     */
    var $_registry;

    /**
     * Constructor.
     *
     * @param array $params  A hash containing connection parameters.
     */
    function VFS_horde($params = array())
    {
        parent::VFS($params);
        if (!isset($this->_params['horde_base'])) {
            $this->_registry = PEAR::raiseError(sprintf(_("Required \"%s\" not specified in VFS configuration."), 'horde_base'));
            return;
        }

        // Define path to Horde.
        @define('HORDE_BASE', $this->_params['horde_base']);

        // Load the Horde Framework core, and set up inclusion paths.
        require_once HORDE_BASE . '/lib/core.php';

        // Create the Registry object.
        $this->_registry = &Registry::singleton();
    }

    function _connect()
    {
        if (!empty($this->_params['user']) &&
            !empty($this->_params['password'])) {
            include HORDE_BASE . '/config/conf.php';
            $auth_driver = empty($conf['auth']['driver']) ? 'none' : $conf['auth']['driver'];
            $auth = &Auth::singleton($auth_driver);
            $auth->setAuth($this->_params['user'],
                           array('password' => $this->_params['password']));
        }
    }

    /**
     * Retrieves the size of a file from the VFS.
     *
     * @abstract
     *
     * @param string $path  The pathname to the file.
     * @param string $name  The filename to retrieve.
     *
     * @return integer The file size.
     */
    function size($path, $name)
    {
        if (is_a($this->_registry, 'PEAR_Error')) {
            return $this->_registry;
        }
        return PEAR::raiseError(_("Not supported."));
    }

    /**
     * Retrieves a file from the VFS.
     *
     * @abstract
     *
     * @param string $path  The pathname to the file.
     * @param string $name  The filename to retrieve.
     *
     * @return string The file data.
     */
    function read($path, $name)
    {
        if (is_a($this->_registry, 'PEAR_Error')) {
            return $this->_registry;
        }

        if (substr($path, 0, 1) == '/') {
            $path = substr($path, 1);
        }
        $pieces = explode('/', $path);
        $data = $this->_registry->callByPackage($pieces[0], 'browse', array('path' => $path . '/' . $name));

        if (is_object($data)) {
            return $data;
        }
        return $data['data'];
    }

    /**
     * Stores a file in the VFS.
     *
     * @abstract
     *
     * @param string $path         The path to store the file in.
     * @param string $name         The filename to use.
     * @param string $tmpFile      The temporary file containing the data to
     *                             be stored.
     * @param boolean $autocreate  Automatically create directories?
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function write($path, $name, $tmpFile, $autocreate = false)
    {
        if (is_a($this->_registry, 'PEAR_Error')) {
            return $this->_registry;
        }
        return PEAR::raiseError(_("Not supported."));
    }

    /**
     * Stores a file in the VFS from raw data.
     *
     * @abstract
     *
     * @param string $path         The path to store the file in.
     * @param string $name         The filename to use.
     * @param string $data         The file data.
     * @param boolean $autocreate  Automatically create directories?
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function writeData($path, $name, $data, $autocreate = false)
    {
        if (is_a($this->_registry, 'PEAR_Error')) {
            return $this->_registry;
        }
        return PEAR::raiseError(_("Not supported."));
    }

    /**
     * Moves a file through the backend.
     *
     * @abstract
     *
     * @param string $path  The path of the original file.
     * @param string $name  The name of the original file.
     * @param string $dest  The destination file name.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function move($path, $name, $dest)
    {
        if (is_a($this->_registry, 'PEAR_Error')) {
            return $this->_registry;
        }
        return PEAR::raiseError(_("Not supported."));
    }

    /**
     * Copies a file through the backend.
     *
     * @abstract
     *
     * @param string $path  The path of the original file.
     * @param string $name  The name of the original file.
     * @param string $dest  The name of the destination directory.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function copy($path, $name, $dest)
    {
        if (is_a($this->_registry, 'PEAR_Error')) {
            return $this->_registry;
        }
        return PEAR::raiseError(_("Not supported."));
    }

    /**
     * Deletes a file from the VFS.
     *
     * @abstract
     *
     * @param string $path  The path to delete the file from.
     * @param string $name  The filename to delete.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function deleteFile($path, $name)
    {
        if (is_a($this->_registry, 'PEAR_Error')) {
            return $this->_registry;
        }
        return PEAR::raiseError(_("Not supported."));
    }

    /**
     * Renames a file in the VFS.
     *
     * @abstract
     *
     * @param string $oldpath  The old path to the file.
     * @param string $oldname  The old filename.
     * @param string $newpath  The new path of the file.
     * @param string $newname  The new filename.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function rename($oldpath, $oldname, $newpath, $newname)
    {
        if (is_a($this->_registry, 'PEAR_Error')) {
            return $this->_registry;
        }
        return PEAR::raiseError(_("Not supported."));
    }

    /**
     * Returns an an unsorted file list of the specified directory.
     *
     * @abstract
     *
     * @param string $path       The path of the directory.
     * @param mixed $filter      String/hash to filter file/dirname on.
     * @param boolean $dotfiles  Show dotfiles?
     * @param boolean $dironly   Show only directories?
     *
     * @return array  File list on success or PEAR_Error on failure.
     */
    function _listFolder($path, $filter = null, $dotfiles = true,
                         $dironly = false)
    {
        if (is_a($this->_registry, 'PEAR_Error')) {
            return $this->_registry;
        }
        $list = array();
        if ($path == '/') {
            $apps = $this->_registry->listApps(null, false, PERMS_READ);
            if (is_a($apps, 'PEAR_Error')) {
                return $apps;
            }
            foreach ($apps as $app) {
                if ($this->_registry->hasMethod('browse', $app)) {
                    $file = array(
                        //'name' => $this->_registry->get('name', $app),
                        'name' => $app,
                        'date' => time(),
                        'type' => '**dir',
                        'size' => -1
                    );
                    $list[] = $file;
                }
            }
            return $list;
        }

        if (substr($path, 0, 1) == '/') {
            $path = substr($path, 1);
        }
        $pieces = explode('/', $path);
        $items = $this->_registry->callByPackage($pieces[0], 'browse', array('path' => $path, 'properties' => array('name', 'browseable', 'contenttype', 'contentlength', 'modified')));
        if (is_a($items, 'PEAR_Error')) {
            return $items;
        }
        if (!is_array(reset($items))) {
            /* We return an object's content. */
            return PEAR::raiseError(_("unknown error"));
        }

        include_once 'Horde/MIME/Magic.php';
        foreach ($items as $sub_path => $i) {
            if ($dironly && !$i['browseable']) {
                continue;
            }

            $name = basename($sub_path);
            if ($this->_filterMatch($filter, $name)) {
                continue;
            }

            if (class_exists('MIME_Magic')) {
                $type = empty($i['contenttype']) ? 'application/octet-stream' : $i['contenttype'];
                $type = MIME_Magic::MIMEToExt($type);
            } else {
                $type = '**none';
            }

            $file = array(
                //'name' => $i['name'],
                'name' => $name,
                'date' => empty($i['modified']) ? 0 : $i['modified'],
                'type' => $i['browseable'] ? '**dir' : $type,
                'size' => empty($i['contentlength']) ? 0 : $i['contentlength']
            );
            $list[] = $file;
        }

        return $list;
    }

    /**
     * Returns a sorted list of folders in the specified directory.
     *
     * @abstract
     *
     * @param string $path         The path of the directory to get the
     *                             directory list for.
     * @param mixed $filter        Hash of items to filter based on folderlist.
     * @param boolean $dotfolders  Include dotfolders?
     *
     * @return mixed  Folder list on success or a PEAR_Error object on failure.
     */
    function listFolders($path = '', $filter = null, $dotfolders = true)
    {
        if (is_a($this->_registry, 'PEAR_Error')) {
            return $this->_registry;
        }
        return PEAR::raiseError(_("Not supported."));
    }

}