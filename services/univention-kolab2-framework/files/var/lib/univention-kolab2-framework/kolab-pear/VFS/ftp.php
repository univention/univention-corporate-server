<?php
/**
 * VFS implementation for an FTP server.
 *
 * <pre>
 * Required values for $params:
 *      'username'       The username with which to connect to the ftp server.
 *      'password'       The password with which to connect to the ftp server.
 *      'hostspec'       The ftp server to connect to.
 * Optional values for $params:
 *      'pasv'           If true, connection will be set to passive mode.
 *      'port'           The port used to connect to the ftp server if other
 *                       than 21.
 *      'ssl'            If true, and PHP had been compiled with OpenSSL
 *                       support, TLS transport-level encryption will be
 *                       negotiated with the server.
 * </pre>
 *
 * $Horde: framework/VFS/VFS/ftp.php,v 1.70 2004/04/18 13:46:15 jan Exp $
 *
 * Copyright 2002-2004 Chuck Hagenbuch <chuck@horde.org>
 * Copyright 2002-2004 Michael Varghese <mike.varghese@ascellatech.com>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Michael Varghese <mike.varghese@ascellatech.com>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.2
 * @package VFS
 */
class VFS_ftp extends VFS {

    /**
     * List of additional credentials required for this VFS backend.
     *
     * @var array $_credentials
     */
    var $_credentials = array('username', 'password');

    /**
     * List of permissions and if they can be changed in this VFS
     * backend.
     *
     * @var array $_permissions
     */
    var $_permissions = array(
        'owner' => array('read' => true, 'write' => true, 'execute' => true),
        'group' => array('read' => true, 'write' => true, 'execute' => true),
        'all'   => array('read' => true, 'write' => true, 'execute' => true));

    /**
     * Variable holding the connection to the ftp server.
     *
     * @var resource $_stream
     */
    var $_stream = false;

    /**
     * Retrieve a file from the VFS.
     *
     * @access public
     *
     * @param string $path  The pathname to the file.
     * @param string $name  The filename to retrieve.
     *
     * @return string  The file data.
     */
    function read($path, $name)
    {
        $conn = $this->_connect();
        if (is_a($conn, 'PEAR_Error')) {
            return $conn;
        }

        $tmpFile = $this->_getTempFile();
        $fetch = @ftp_get($this->_stream, $tmpFile,
                          $this->_getPath($path, $name), FTP_BINARY);
        if ($fetch === false) {
            return PEAR::raiseError(sprintf(_("Unable to open VFS file \"%s\"."), $this->_getPath($path, $name)));
        }

        if (OS_WINDOWS) {
            $mode = 'rb';
        } else {
            $mode = 'r';
        }
        $fp = fopen($tmpFile, $mode);
        $data = fread($fp, filesize($tmpFile));
        fclose($fp);
        unlink($tmpFile);
        return $data;
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
     */
    function write($path, $name, $tmpFile, $autocreate = false)
    {
        $conn = $this->_connect();
        if (is_a($conn, 'PEAR_Error')) {
            return $conn;
        }

        if (!@ftp_put($this->_stream, $this->_getPath($path, $name), $tmpFile, FTP_BINARY)) {
            if ($autocreate) {
                $result = $this->autocreatePath($path);
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }
                if (!@ftp_put($this->_stream, $this->_getPath($path, $name), $tmpFile, FTP_BINARY)) {
                    return PEAR::raiseError(sprintf(_("Unable to write VFS file \"%s\"."), $this->_getPath($path, $name)));
                }
            } else {
                return PEAR::raiseError(sprintf(_("Unable to write VFS file \"%s\"."), $this->_getPath($path, $name)));
            }
        }

        return true;
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
     */
    function writeData($path, $name, $data, $autocreate = false)
    {
        $tmpFile = $this->_getTempFile();
        $fp = fopen($tmpFile, 'wb');
        fwrite($fp, $data);
        fclose($fp);

        $result = $this->write($path, $name, $tmpFile, $autocreate);
        unlink($tmpFile);
        return $result;
    }

    /**
     * Delete a file from the VFS.
     *
     * @access public
     *
     * @param string $path  The path to delete the file from.
     * @param string $name  The filename to use.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function deleteFile($path, $name)
    {
        $conn = $this->_connect();
        if (is_a($conn, 'PEAR_Error')) {
            return $conn;
        }

        if (!@ftp_delete($this->_stream, $this->_getPath($path, $name))) {
            return PEAR::raiseError(sprintf(_("Unable to delete VFS file \"%s\"."), $this->_getPath($path, $name)));
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
        $conn = $this->_connect();
        if (is_a($conn, 'PEAR_Error')) {
            return $conn;
        }

        $result = false;
        $olddir = $this->getCurrentDirectory();

        /* See if we can change to the given path. */
        if (@ftp_chdir($this->_stream, $this->_getPath($path, $name))) {
            $result = true;
        }

        $this->_setPath($olddir);

        return $result;
    }

    /**
     * Delete a folder from the VFS.
     *
     * @access public
     *
     * @param string $path                 The path to delete the folder from.
     * @param string $name                 The name of the folder to delete.
     * @param optional boolean $recursive  Force a recursive delete?
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function deleteFolder($path, $name, $recursive = false)
    {
        $conn = $this->_connect();
        if (is_a($conn, 'PEAR_Error')) {
            return $conn;
        }

        $isDir = false;
        $dirCheck = $this->listFolder($path);
        foreach ($dirCheck as $file) {
            if ($file['name'] == $name && $file['type'] == '**dir') {
                $isDir = true;
                break;
            }
        }

        if ($isDir) {
            $file_list = $this->listFolder($this->_getPath($path, $name));
            if (is_a($file_list, 'PEAR_Error')) {
                return $file_list;
            }

            if (count($file_list) && !$recursive) {
                return PEAR::raiseError(sprintf(_("Unable to delete \"%s\", the directory is not empty."),
                                                $this->_getPath($path, $name)));
            }

            foreach ($file_list as $file) {
                if ($file['type'] == '**dir') {
                    $result = $this->deleteFolder($this->_getPath($path, $name), $file['name'], $recursive);
                } else {
                    $result = $this->deleteFile($this->_getPath($path, $name), $file['name']);
                }
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }
            }

            if (!@ftp_rmdir($this->_stream, $this->_getPath($path, $name))) {
                return PEAR::raiseError(sprintf(_("Cannot remove directory \"%s\"."), $this->_getPath($path, $name)));
            }
        } else {
            if (!@ftp_delete($this->_stream, $this->_getPath($path, $name))) {
                return PEAR::raiseError(sprintf(_("Cannot delete file \"%s\"."), $this->_getPath($path, $name)));
            }
        }

        return true;
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
     */
    function rename($oldpath, $oldname, $newpath, $newname)
    {
        $conn = $this->_connect();
        if (is_a($conn, 'PEAR_Error')) {
            return $conn;
        }

        if (!@ftp_rename($this->_stream, $this->_getPath($oldpath, $oldname), $this->_getPath($newpath, $newname))) {
            return PEAR::raiseError(sprintf(_("Unable to rename VFS file \"%s\"."), $this->_getPath($oldpath, $oldname)));
        }

        return true;
    }

    /**
     * Creates a folder on the VFS.
     *
     * @access public
     *
     * @param string $path  Holds the path of directory to create folder.
     * @param string $name  Holds the name of the new folder.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function createFolder($path, $name)
    {
        $conn = $this->_connect();
        if (is_a($conn, 'PEAR_Error')) {
            return $conn;
        }

        if (!@ftp_mkdir($this->_stream, $this->_getPath($path, $name))) {
            return PEAR::raiseError(sprintf(_("Unable to create VFS directory \"%s\"."), $this->_getPath($path, $name)));
        }

        return true;
    }

    /**
     * Changes permissions for an Item on the VFS.
     *
     * @access public
     *
     * @param string $path        Holds the path of directory of the Item.
     * @param string $name        Holds the name of the Item.
     * @param string $permission  TODO
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function changePermissions($path, $name, $permission)
    {
        $conn = $this->_connect();
        if (is_a($conn, 'PEAR_Error')) {
            return $conn;
        }

        if (!@ftp_site($this->_stream, 'CHMOD ' . $permission . ' ' . $this->_getPath($path, $name))) {
            return PEAR::raiseError(sprintf(_("Unable to change permission for VFS file \"%s\"."), $this->_getPath($path, $name)));
        }

        return true;
    }

    /**
     * Returns an unsorted file list.
     *
     * @access public
     *
     * @param optional string $path       The path of the directory to get the
     *                                    file list for.
     * @param optional mixed $filter      Hash of items to filter based on
     *                                    filename.
     * @param optional boolean $dotfiles  Show dotfiles?
     * @param optional boolean $dironly   Show directories only?
     *
     * @return mixed  File list on success or a PEAR_Error object on failure.
     */
    function listFolder($path = '', $filter = null, $dotfiles = true,
                        $dironly = false)
    {
        $conn = $this->_connect();
        if (is_a($conn, 'PEAR_Error')) {
            return $conn;
        }

        $files = array();
        $type = @ftp_systype($this->_stream);
        if ($type == 'UNKNOWN') {
            // Go with unix-style listings by default.
            $type = 'UNIX';
        }

        $olddir = $this->getCurrentDirectory();
        if (!empty($path)) {
            $res = $this->_setPath($path);
            if (is_a($res, 'PEAR_Error')) {
                return $res;
            }
        }

        if ($type == 'UNIX') {
            // If we don't want dotfiles, We can save work here by not
            // doing an ls -a and then not doing the check later (by
            // setting $dotfiles to true, the if is short-circuited).
            if ($dotfiles) {
                $list = ftp_rawlist($this->_stream, '-al');
                $dotfiles = true;
            } else {
                $list = ftp_rawlist($this->_stream, '-l');
            }
        } else {
           $list = ftp_rawlist($this->_stream, '');
        }

        if (!is_array($list)) {
            if (isset($olddir)) {
                $res = $this->_setPath($olddir);
                if (is_a($res, 'PEAR_Error')) {
                    return $res;
                }
            }
            return array();
        }

        foreach ($list as $line) {
            $file = array();
            $item = preg_split('/\s+/', $line);
            if ($type == 'UNIX' || (stristr($type, 'win') && !preg_match('|\d\d-\d\d-\d\d|', $item[0]))) {
                if (count($item) < 8 || substr($line, 0, 5) == 'total') {
                    continue;
                }
                $file['perms'] = $item[0];
                $file['owner'] = $item[2];
                $file['group'] = $item[3];
                $file['name'] = substr($line, strpos($line, sprintf("%s %2s %5s", $item[5], $item[6], $item[7])) + 13);

                // Filter out '.' and '..' entries.
                if (preg_match('/^\.\.?\/?$/', $file['name'])) {
                    continue;
                }

                // Filter out dotfiles if they aren't wanted.
                if (!$dotfiles && substr($file['name'], 0, 1) == '.') {
                    continue;
                }

                $p1 = substr($file['perms'], 0, 1);
                if ($p1 === 'l') {
                    $file['link'] = substr($file['name'], strpos($file['name'], '->') + 3);
                    $file['name'] = substr($file['name'], 0, strpos($file['name'], '->') - 1);
                    $file['type'] = '**sym';

                   if ($this->isFolder('', $file['link'])) {
                              $file['linktype'] = '**dir';
                                                    } else {
                                                    $parts = explode('/', $file['link']);
                                                    $name = explode('.', array_pop($parts));
                                                    if (count($name) == 1 || ($name[0] === '' && count($name) == 2)) {
                                                        $file['linktype'] = '**none';
                                                        } else {
                                                            $file['linktype'] = VFS::strtolower(array_pop($name));
                                                            }
                                                                   }
                } elseif ($p1 === 'd') {
                    $file['type'] = '**dir';
                } else {
                    $name = explode('.', $file['name']);
                    if (count($name) == 1 || (substr($file['name'], 0, 1) === '.' && count($name) == 2)) {
                        $file['type'] = '**none';
                    } else {
                        $file['type'] = VFS::strtolower($name[count($name) - 1]);
                    }
                }
                if ($file['type'] == '**dir') {
                    $file['size'] = -1;
                } else {
                    $file['size'] = $item[4];
                }
                if (strstr($item[7], ':')) {
                    $file['date'] = strtotime($item[7] . ':00' . $item[5] . ' ' . $item[6] . ' ' . date('Y', time()));
                    if ($file['date'] > time()) {
                        $file['date'] = strtotime($item[7] . ':00' . $item[5] . ' ' . $item[6] . ' ' . (date('Y', time()) - 1));
                    }
                } else {
                    $file['date'] = strtotime('00:00:00' . $item[5] . ' ' . $item[6] . ' ' . $item[7]);
                }
            } else {
                /* Handle Windows FTP servers returning DOS-style file
                 * listings. */
                $file['perms'] = '';
                $file['owner'] = '';
                $file['group'] = '';
                $file['name'] = $item[3];
                $index = 4;
                while ($index < count($item)) {
                    $file['name'] .= ' ' . $item[$index];
                    $index++;
                }
                $file['date'] = strtotime($item[0] . ' ' . $item[1]);
                if ($item[2] == '<DIR>') {
                    $file['type'] = '**dir';
                    $file['size'] = -1;
                } else {
                    $file['size'] = $item[2];
                    $name = explode('.', $file['name']);
                    if (count($name) == 1 || (substr($file['name'], 0, 1) === '.' && count($name) == 2)) {
                        $file['type'] = '**none';
                    } else {
                        $file['type'] = VFS::strtolower($name[count($name) - 1]);
                    }
                }
            }

            // Filtering.
            if ($this->_filterMatch($filter, $file['name'])) {
                unset($file);
                continue;
            }
            if ($dironly && $file['type'] !== '**dir') {
                unset($file);
                continue;
            }

            $files[$file['name']] = $file;
            unset($file);
        }

        if (isset($olddir)) {
            $res = $this->_setPath($olddir);
            if (is_a($res, 'PEAR_Error')) {
                return $res;
            }
        }
        return $files;
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
     */
    function listFolders($path = '', $filter = null, $dotfolders = true)
    {
        $conn = $this->_connect();
        if (is_a($conn, 'PEAR_Error')) {
            return $conn;
        }

        $folders = array();
        $folder = array();

        $folderList = $this->listFolder($path, null, $dotfolders, true);
        if (is_a($folderList, 'PEAR_Error')) {
            return $folderList;
        }

        $folder['val'] = $this->_parentDir($path);
        $folder['abbrev'] = '..';
        $folder['label'] = '..';

        $folders[$folder['val']] = $folder;

        foreach ($folderList as $files) {
            $folder['val'] = $this->_getPath($path, $files['name']);
            $folder['abbrev'] = $files['name'];
            $folder['label'] = $folder['val'];

            $folders[$folder['val']] = $folder;
        }

        ksort($folders);
        return $folders;
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
     */
    function copy($path, $name, $dest)
    {
        $conn = $this->_connect();
        if (is_a($conn, 'PEAR_Error')) {
            return $conn;
        }

        $fileCheck = $this->listFolder($dest, null, true);
        foreach ($fileCheck as $file) {
            if ($file['name'] == $name) {
                return PEAR::raiseError(sprintf(_("%s already exists."), $this->_getPath($dest, $name)));
            }
        }

        $isDir = false;
        $dirCheck = $this->listFolder($path, null, false);
        foreach ($dirCheck as $file) {
            if ($file['name'] == $name && $file['type'] == '**dir') {
                $isDir = true;
                break;
            }
        }

        if ($isDir) {
            $result = $this->createFolder($dest, $name);

            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            $file_list = $this->listFolder($this->_getPath($path, $name));
            foreach ($file_list as $file) {
                $result = $this->copy($this->_getPath($path, $name), $file['name'], $this->_getPath($dest, $name));
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }
            }
        } else {
            $tmpFile = $this->_getTempFile();
            $fetch = @ftp_get($this->_stream, $tmpFile, $this->_getPath($path, $name), FTP_BINARY);
            if (!$fetch) {
                unlink($tmpFile);
                return PEAR::raiseError(sprintf(_("Failed to copy from \"%s\"."), $this->_getPath($path, $name)));
            }

            if (!@ftp_put($this->_stream, $this->_getPath($dest, $name), $tmpFile, FTP_BINARY)) {
                unlink($tmpFile);
                return PEAR::raiseError(sprintf(_("Failed to copy to \"%s\"."), $this->_getPath($dest, $name)));
            }

            unlink($tmpFile);
        }

        return true;
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
     */
    function move($path, $name, $dest)
    {
        $conn = $this->_connect();
        if (is_a($conn, 'PEAR_Error')) {
            return $conn;
        }

        $fileCheck = $this->listFolder($dest, null, true);
        foreach ($fileCheck as $file) {
            if ($file['name'] == $name) {
                return PEAR::raiseError(sprintf(_("%s already exists."), $this->_getPath($dest, $name)));
            }
        }

        if (!@ftp_rename($this->_stream, $this->_getPath($path, $name), $this->_getPath($dest, $name))) {
            return PEAR::raiseError(sprintf(_("Failed to move to \"%s\"."), $this->_getPath($dest, $name)));
        }

        return true;
    }

    /**
     * Return the current working directory on the FTP server.
     *
     * @access public
     *
     * @return string  The current working directory.
     */
    function getCurrentDirectory()
    {
        $this->_connect();
        return ftp_pwd($this->_stream);
    }

    /**
     * Change directories on the server.
     *
     * @access private
     *
     * @param string $path  The path to change to.
     *
     * @return mixed  True on success, or a PEAR_Error on failure.
     */
    function _setPath($path)
    {
        if (!@ftp_chdir($this->_stream, $path)) {
            return PEAR::raiseError(sprintf(_("Unable to change to %s."), $path));
        }
        return true;
    }

    /**
     * Returns the full path of an item.
     *
     * @access private
     *
     * @param string $path  Holds the path of directory of the Item.
     * @param string $name  Holds the name of the Item.
     *
     * @return mixed  Full path when $path isset and just $name when not set.
     */
    function _getPath($path, $name)
    {
        if ($path !== '') {
             return ($path . '/' . $name);
        }
        return ($name);
    }

    /**
     * Returns the parent directory of specified path.
     *
     * @access private
     *
     * @param string $path  The path to get the parent of.
     *
     * @return mixed  The parent directory (string) on success
     *                or a PEAR_Error object on failure.
     */
    function _parentDir($path)
    {
        $conn = $this->_connect();
        if (is_a($conn, 'PEAR_Error')) {
            return $conn;
        }

        $olddir = $this->getCurrentDirectory();
        @ftp_cdup($this->_stream);

        $parent = $this->getCurrentDirectory();
        $this->_setPath($olddir);

        if (!$parent) {
            return PEAR::raiseError(_("Unable to determine current directory."));
        }

        return $parent;
    }

    /**
     * Attempts to open a connection to the FTP server.
     *
     * @access private
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function _connect()
    {
        if ($this->_stream === false) {
            if (!extension_loaded('ftp')) {
                return PEAR::raiseError(_("The FTP extension is not available."));
            }

            if (!is_array($this->_params)) {
                return PEAR::raiseError(_("No configuration information specified for FTP VFS."));
            }

            $required = array('hostspec', 'username', 'password');
            foreach ($required as $val) {
                if (!isset($this->_params[$val])) {
                    return PEAR::raiseError(sprintf(_("Required '%s' not specified in VFS configuration."), $val));
                }
            }

            /* Connect to the ftp server using the supplied parameters. */
            if (!empty($this->_params['ssl'])) {
                if (function_exists('ftp_ssl_connect')) {
                    $this->_stream = @ftp_ssl_connect($this->_params['hostspec'], $this->_params['port']);
                } else {
                    return PEAR::raiseError(_("Unable to connect with SSL."));
                }
            } else {
                $this->_stream = @ftp_connect($this->_params['hostspec'], $this->_params['port']);
            }
            if (!$this->_stream) {
                return PEAR::raiseError(_("Connection to FTP server failed."));
            }

            $connected = @ftp_login($this->_stream, $this->_params['username'], $this->_params['password']);
            if (!$connected) {
                return PEAR::raiseError(_("Authentication to FTP server failed."));
                $this->_disconnect();
            }

            if (!empty($this->_params['pasv'])) {
                @ftp_pasv($this->_stream, true);
            }
        }

        return true;
    }

    /**
     * Disconnect from the FTP server and clean up the connection.
     *
     * @access private
     */
    function _disconnect()
    {
        @ftp_quit($this->_stream);
        $this->_stream = false;
    }

    /**
     * Determine the location of the system temporary directory.  If a
     * specific setting cannot be found, it defaults to /tmp
     *
     * @access private
     *
     * @return string  A directory name which can be used for temp files.
     *                 Returns false if one could not be found.
     */
    function _getTempDir()
    {
        $tmp_locations = array('/tmp', '/var/tmp', 'c:\WUTemp', 'c:\temp', 'c:\windows\temp', 'c:\winnt\temp');

        /* Try PHP's upload_tmp_dir directive. */
        $tmp = ini_get('upload_tmp_dir');

        /* Otherwise, try to determine the TMPDIR environment
           variable. */
        if (empty($tmp)) {
            $tmp = getenv('TMPDIR');
        }

        /* If we still cannot determine a value, then cycle through a
         * list of preset possibilities. */
        while (empty($tmp) && sizeof($tmp_locations)) {
            $tmp_check = array_shift($tmp_locations);
            if (@is_dir($tmp_check)) {
                $tmp = $tmp_check;
            }
        }

        /* If it is still empty, we have failed, so return false;
         * otherwise return the directory determined. */
        return empty($tmp) ? false : $tmp;
    }

    /**
     * Create a temporary file.
     *
     * @access private
     *
     * @return string  Returns the full path-name to the temporary file.
     *                 Returns false if a temp file could not be created.
     */
    function _getTempFile()
    {
        $tmp_dir = $this->_getTempDir();
        if (empty($tmp_dir)) {
            return false;
        }

        $tmp_file = tempnam($tmp_dir, 'vfs');

        /* If the file was created, then register it for deletion and return */
        if (empty($tmp_file)) {
            return false;
        } else {
            return $tmp_file;
        }
    }

}
