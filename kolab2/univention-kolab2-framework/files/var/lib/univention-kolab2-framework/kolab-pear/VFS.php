<?php

require_once 'PEAR.php';

/**
 * VFS API for abstracted file storage and access.
 *
 * $Horde: framework/VFS/VFS.php,v 1.66 2004/04/08 22:02:02 slusarz Exp $
 *
 * Copyright 2002-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @package VFS
 * @since   Horde 2.2
 */
class VFS {

    /**
     * Hash containing connection parameters.
     *
     * @var array $_params
     */
    var $_params = array();

    /**
     * List of additional credentials required for this VFS backend
     * (example: For FTP, we need a username and password to log in to
     * the server with).
     *
     * @var array $_credentials
     */
    var $_credentials = array();

    /**
     * List of permissions and if they can be changed in this VFS
     * backend.
     *
     * @var array $_permissions
     */
    var $_permissions = array(
        'owner' => array('read' => false, 'write' => false, 'execute' => false),
        'group' => array('read' => false, 'write' => false, 'execute' => false),
        'all'   => array('read' => false, 'write' => false, 'execute' => false));

    /**
     * Constructs a new VFS object.
     *
     * @access public
     *
     * @param optional array $params  A hash containing connection parameters.
     */
    function VFS($params = array())
    {
        if (empty($params['user'])) {
            $params['user'] = '';
        }
        $this->_params = $params;
    }

    /**
     * Check the credentials that we have by calling _connect(), to
     * see if there is a valid login.
     *
     * @access public
     *
     * @return mixed  True on success, PEAR_Error describing the problem
     *                if the credentials are invalid.
     */
    function checkCredentials()
    {
        return $this->_connect();
    }

    /**
     * Set configuration parameters.
     *
     * @access public
     *
     * @param optional array $params  An associative array:
     *                                KEY: param name, VAL: param value
     */
    function setParams($params = array())
    {
        foreach ($params as $name => $value) {
            $this->_params[$name] = $value;
        }
    }

    /**
     * Retrieve a file from the VFS.
     *
     * @access public
     *
     * @param string $path  The pathname to the file.
     * @param string $name  The filename to retrieve.
     *
     * @return string The file data.
     *
     * @abstract
     */
    function read($path, $name)
    {
        return PEAR::raiseError(_("Not supported."));
    }

    /**
     * Store a file in the VFS.
     *
     * @access public
     *
     * @param string $path                  The path to store the file in.
     * @param string $name                  The filename to use.
     * @param string $tmpFile               The temporary file containing the
     *                                      data to be stored.
     * @param optional boolean $autocreate  Automatically create directories?
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     *
     * @abstract
     */
    function write($path, $name, $tmpFile, $autocreate = false)
    {
        return PEAR::raiseError(_("Not supported."));
    }

    /**
     * Moves a file through the backend.
     *
     * @access public
     *
     * @param string $path  The path to store the file in.
     * @param string $name  The filename to use.
     * @param string $dest  The destination of the file.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     *
     * @abstract
     */
    function move($path, $name, $dest)
    {
        return PEAR::raiseError(_("Not supported."));
    }

    /**
     * Copies a file through the backend.
     *
     * @access public
     *
     * @param string $path  The path to store the file in.
     * @param string $name  The filename to use.
     * @param string $dest  The destination of the file.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     *
     * @abstract
     */
    function copy($path, $name, $dest)
    {
        return PEAR::raiseError(_("Not supported."));
    }

    /**
     * Store a file in the VFS from raw data.
     *
     * @access public
     *
     * @param string $path                  The path to store the file in.
     * @param string $name                  The filename to use.
     * @param string $data                  The file data.
     * @param optional boolean $autocreate  Automatically create directories?
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     *
     * @abstract
     */
    function writeData($path, $name, $data, $autocreate = false)
    {
        return PEAR::raiseError(_("Not supported."));
    }

    /**
     * Delete a file from the VFS.
     *
     * @access public
     *
     * @param string $path  The path to store the file in.
     * @param string $name  The filename to use.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     *
     * @abstract
     */
    function deleteFile($path, $name)
    {
        return PEAR::raiseError(_("Not supported."));
    }

    /**
     * Rename a file in the VFS.
     *
     * @access public
     *
     * @param string $oldpath  The old path to the file.
     * @param string $oldname  The old filename.
     * @param string $newpath  The new path of the file.
     * @param string $newname  The new filename.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     *
     * @abstract
     */
    function rename($oldpath, $oldname, $newpath, $newname)
    {
        return PEAR::raiseError(_("Not supported."));
    }

    /**
     * Check if a given file/folder exists in a folder.
     *
     * @access public
     *
     * @param string $path  The path to the folder.
     * @param string $name  The file/folder name.
     *
     * @return boolean  True if it exists, false otherwise.
     */
    function exists($path, $name)
    {
        $list = $this->listFolder($path);
        return isset($list[$name]);
    }

    /**
     * Create a folder in the VFS.
     *
     * @access public
     *
     * @param string $path  The path to the folder.
     * @param string $name  The name of the new folder.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     *
     * @abstract
     */
    function createFolder($path, $name)
    {
        return PEAR::raiseError(_("Not supported."));
    }

    /**
     * Automatically create any necessary parent directories in the
     * specified $path.
     *
     * @access public
     *
     * @param string $path  The VFS path to autocreate.
     */
    function autocreatePath($path)
    {
        $dirs = explode('/', $path);
        if (is_array($dirs)) {
            $cur = '';
            foreach ($dirs as $dir) {
                if (!$this->isFolder($cur, $dir)) {
                    $result = $this->createFolder($cur, $dir);
                    if (is_a($result, 'PEAR_Error')) {
                        return $result;
                    }
                }
                if (!empty($cur)) {
                    $cur .= '/';
                }
                $cur .= $dir;
            }
        }

        return true;
    }

    /**
     * Check if a given pathname is a folder.
     *
     * @access public
     *
     * @param string $path  The path to the folder.
     * @param string $name  The file/folder name.
     *
     * @return boolean  True if it is a folder, false otherwise.
     */
    function isFolder($path, $name)
    {
        $folderList = $this->listFolder($path, null, true, true);
        return isset($folderList[$name]);
    }

    /**
     * Deletes a folder from the VFS.
     *
     * @access public
     *
     * @param string $path                 The path of the folder to delete.
     * @param string $name                 The name of the folder to delete.
     * @param optional boolean $recursive  Force a recursive delete?
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     *
     * @abstract
     */
    function deleteFolder($path, $name, $recursive = false)
    {
        return PEAR::raiseError(_("Not supported."));
    }

    /**
     * Removes recursively all files and subfolders from the given folder.
     *
     * @access public
     *
     * @param string $path  The path of the folder to empty.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function emptyFolder($path)
    {
        // Get and delete the subfolders.
        $list = $this->listFolder($path, null, true, true);
        if (is_a($list, 'PEAR_Error')) {
            return $list;
        }
        foreach ($list as $folder) {
            $result = $this->deleteFolder($path, $folder['name'], true);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
        // Only files are left, get and delete them.
        $list = $this->listFolder($path);
        if (is_a($list, 'PEAR_Error')) {
            return $list;
        }
        foreach ($list as $file) {
            $result = $this->deleteFile($path, $file['name']);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
    }

    /**
     * Returns a file list of the directory passed in.
     *
     * @access public
     *
     * @param string $path                The path of the directory.
     * @param optional mixed $filter      String/hash to filter file/dirname
     *                                    on.
     * @param optional boolean $dotfiles  Show dotfiles?
     * @param optional boolean $dironly   Show only directories?
     *
     * @return array  File list on success.
     *                Returns PEAR_Error on failure.
     *
     * @abstract
     */
    function listFolder($path, $filter = null, $dotfiles = true,
                        $dironly = false)
    {
        return PEAR::raiseError(_("Not supported."));
    }

    /**
     * Returns the current working directory of the VFS backend.
     *
     * @access public
     *
     * @return string  The current working directory.
     */
    function getCurrentDirectory()
    {
        return '';
    }

    /**
     * Returns a boolean indicating whether or not the filename
     * matches any filter element.
     *
     * @access private
     *
     * @param mixed $filter     String/hash to build the regular expression
     *                          from.
     * @param string $filename  String containing the filename to match.
     *
     * @return boolean  True on match, false on no match.
     */
    function _filterMatch($filter, $filename)
    {
        $namefilter = null;

        // Build a regexp based on $filter.
        if ($filter !== null) {
            $namefilter = '/';
            if (is_array($filter)) {
                $once = false;
                foreach ($filter as $item) {
                    if ($once !== true) {
                        $namefilter .= '(';
                        $once = true;
                    } else {
                        $namefilter .= '|(';
                    }
                    $namefilter .= $item . ')';
                }
            } else {
                $namefilter .= '(' . $filter . ')';
            }
            $namefilter .= '/';
        }

        $match = false;
        if ($namefilter !== null) {
            $match = preg_match($namefilter, $filename);
        }

        return $match;
    }

    /**
     * Changes permissions for an Item on the VFS.
     *
     * @access public
     *
     * @param string $path  Holds the path of directory of the Item.
     * @param string $name  Holds the name of the Item.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     *
     * @abstract
     */
    function changePermissions($path, $name, $permission)
    {
        return PEAR::raiseError(_("Not supported."));
    }

    /**
     * Returns a sorted list of folders in specified directory.
     *
     * @access public
     *
     * @param optional string $path         The path of the directory to get
     *                                      the directory list for.
     * @param optional mixed $filter        Hash of items to filter based on
     *                                      folderlist.
     * @param optional boolean $dotfolders  Include dotfolders?
     *
     * @return mixed  Folder list on success or a PEAR_Error object on failure.
     *
     * @abstract
     */
    function listFolders($path = '', $filter = null, $dotfolders = true)
    {
        return PEAR::raiseError(_("Not supported."));
    }

    /**
     * Return the list of additional credentials required, if any.
     *
     * @access public
     *
     * @return array  Credential list.
     */
    function getRequiredCredentials()
    {
        return array_diff($this->_credentials, array_keys($this->_params));
    }

    /**
     * Return the array specificying what permissions are
     * changeable for this implementation.
     *
     * @access public
     *
     * @return array  Changeable permisions.
     */
    function getModifiablePermissions()
    {
        return $this->_permissions;
    }

    /**
     * Close any resources that need to be closed.
     *
     * @access private
     */
    function _disconnect()
    {
    }

    /**
     * Converts a string to all lowercase characters ignoring the
     * current locale.
     *
     * @access public
     *
     * @param string $string  The string to be lowercased
     *
     * @return string  The string with lowercase characters
     */
    function strtolower($string)
    {
        $language = setlocale(LC_CTYPE, 0);
        setlocale(LC_CTYPE, 'en');
        $string = strtolower($string);
        setlocale(LC_CTYPE, $language);
        return $string;
    }

    /**
     * Returns the character (not byte) length of a string.
     *
     * @access public
     *
     * @param string $string   The string to return the length of.
     * @param string $charset  The charset to use when calculating the
     *                         string's length.
     *
     * @return string  The string's length.
     */
    function strlen($string, $charset = null)
    {
        if (extension_loaded('mbstring')) {
            if (is_null($charset)) {
                $charset = 'ISO-8859-1';
            }
            $ret = @mb_strlen($string, $charset);
            if (!empty($ret)) {
                return $ret;
            }
        }
        return strlen($string);
    }

    /**
     * Attempts to return a concrete VFS instance based on $driver.
     *
     * @access public
     *
     * @param mixed $driver           The type of concrete VFS subclass to
     *                                return. This is based on the storage
     *                                driver ($driver). The code is
     *                                dynamically included.
     * @param optional array $params  A hash containing any additional
     *                                configuration or connection parameters a
     *                                subclass might need.
     *
     * @return object VFS  The newly created concrete VFS instance,
     *                     or a PEAR_Error on an error.
     */
    function &factory($driver, $params = array())
    {
        include_once 'VFS/' . $driver . '.php';
        $class = 'VFS_' . $driver;
        if (class_exists($class)) {
            return $ret = &new $class($params);
        } else {
            return PEAR::raiseError(sprintf(_("Class definition of %s not found."), $class));
        }
    }

    /**
     * Attempts to return a reference to a concrete VFS instance
     * based on $driver. It will only create a new instance if no
     * VFS instance with the same parameters currently exists.
     *
     * This should be used if multiple types of file backends (and,
     * thus, multiple VFS instances) are required.
     *
     * This method must be invoked as: $var = &VFS::singleton()
     *
     * @access public
     *
     * @param mixed $driver           The type of concrete VFS subclass to
     *                                return. This is based on the storage
     *                                driver ($driver). The code is
     *                                dynamically included.
     * @param optional array $params  A hash containing any additional
     *                                configuration or connection parameters a
     *                                subclass might need.
     *
     * @return object VFS  The concrete VFS reference, or a PEAR_Error on an
     *                     error.
     */
    function &singleton($driver, $params = array())
    {
        static $instances;
        if (!isset($instances)) {
            $instances = array();
        }

        $signature = serialize(array($driver, $params));
        if (!isset($instances[$signature])) {
            $instances[$signature] = &VFS::factory($driver, $params);
        }

        return $instances[$signature];
    }

}
