<?php
/**
 * VFS implementation for an FTP server.
 *
 * Required values for $params:<pre>
 *      'username'       The username with which to connect to the ftp server.
 *      'password'       The password with which to connect to the ftp server.
 *      'hostspec'       The ftp server to connect to.</pre>
 *
 * Optional values for $params:<pre>
 *      'lsformat'       The return formatting from the 'ls' command).
 *                       Values: 'aix', 'standard' (default)
 *      'maplocalids'    If true and the POSIX extension is available, the
 *                       driver will map the user and group IDs returned from
 *                       the FTP server with the local IDs from the local
 *                       password file.  This is useful only if the FTP server
 *                       is running on localhost or if the local user/group
 *                       IDs are identical to the remote FTP server.
 *      'pasv'           If true, connection will be set to passive mode.
 *      'port'           The port used to connect to the ftp server if other
 *                       than 21.
 *      'ssl'            If true, and PHP had been compiled with OpenSSL
 *                       support, TLS transport-level encryption will be
 *                       negotiated with the server.
 *      'timeout'        If defined, use this value as the timeout for the
 *                       server.
 *      'type'           The type of the remote FTP server.
 *                       Possible values: 'unix', 'win', 'netware'
 *                       By default, we attempt to auto-detect type.</pre>
 *
 * $Horde: framework/VFS/lib/VFS/ftp.php,v 1.1.2.7 2009-10-15 17:18:48 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 * Copyright 2002-2007 Michael Varghese <mike.varghese@ascellatech.com>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Michael Varghese <mike.varghese@ascellatech.com>
 * @package VFS
 */
class VFS_ftp extends VFS {

    /**
     * List of additional credentials required for this VFS backend.
     *
     * @var array
     */
    var $_credentials = array('username', 'password');

    /**
     * List of permissions and if they can be changed in this VFS backend.
     *
     * @var array
     */
    var $_permissions = array(
        'owner' => array('read' => true, 'write' => true, 'execute' => true),
        'group' => array('read' => true, 'write' => true, 'execute' => true),
        'all'   => array('read' => true, 'write' => true, 'execute' => true));

    /**
     * Variable holding the connection to the ftp server.
     *
     * @var resource
     */
    var $_stream = false;

    /**
     * Local cache array for user IDs.
     *
     * @var array
     */
    var $_uids = array();

    /**
     * Local cache array for group IDs.
     *
     * @var array
     */
    var $_gids = array();

    /**
     */
    var $_type;

    /**
     * Returns the size of a file.
     *
     * @access public
     *
     * @param string $path  The path of the file.
     * @param string $name  The filename.
     *
     * @return integer  The size of the file in bytes or PEAR_Error on
     *                  failure.
     */
    function size($path, $name)
    {
        $conn = $this->_connect();
        if (is_a($conn, 'PEAR_Error')) {
            return $conn;
        }

        if (($size = @ftp_size($this->_stream, $this->_getPath($path, $name))) === false) {
            return PEAR::raiseError(sprintf(_("Unable to check file size of \"%s\"."), $this->_getPath($path, $name)));
        }

        return $size;
    }

    /**
     * Retrieves a file from the VFS.
     *
     * @param string $path  The pathname to the file.
     * @param string $name  The filename to retrieve.
     *
     * @return string  The file data.
     */
    function read($path, $name)
    {
        $file = $this->readFile($path, $name);
        if (is_a($file, 'PEAR_Error')) {
            return $file;
        }

        $size = filesize($file);
        if ($size === 0) {
            return '';
        }

        return file_get_contents($file);
    }

    /**
     * Retrieves a file from the VFS as an on-disk local file.
     *
     * This function provides a file on local disk with the data of a VFS file
     * in it. This file <em>cannot</em> be modified! The behavior if you do
     * modify it is undefined. It will be removed at the end of the request.
     *
     * @param string $path  The pathname to the file.
     * @param string $name  The filename to retrieve.
     *
     * @return string A local filename.
     */
    function readFile($path, $name)
    {
        $conn = $this->_connect();
        if (is_a($conn, 'PEAR_Error')) {
            return $conn;
        }

        // Create a temporary file and register it for deletion at the
        // end of this request.
        $localFile = $this->_getTempFile();
        if (!$localFile) {
            return PEAR::raiseError(_("Unable to create temporary file."));
        }
        register_shutdown_function(create_function('', '@unlink(\'' . addslashes($localFile) . '\');'));

        $result = @ftp_get(
            $this->_stream,
            $localFile,
            $this->_getPath($path, $name),
            FTP_BINARY);
        if ($result === false) {
            return PEAR::raiseError(sprintf(_("Unable to open VFS file \"%s\"."), $this->_getPath($path, $name)));
        }

        return $localFile;
    }

    /**
     * Open a stream to a file in the VFS.
     *
     * @param string $path  The pathname to the file.
     * @param string $name  The filename to retrieve.
     *
     * @return resource  The stream.
     */
    function readStream($path, $name)
    {
        $file = $this->readFile($path, $name);
        if (is_a($file, 'PEAR_Error')) {
            return $file;
        }

        $mode = OS_WINDOWS ? 'rb' : 'r';
        return fopen($file, $mode);
    }

    /**
     * Stores a file in the VFS.
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
        $conn = $this->_connect();
        if (is_a($conn, 'PEAR_Error')) {
            return $conn;
        }

        $res = $this->_checkQuotaWrite('file', $tmpFile);
        if (is_a($res, 'PEAR_Error')) {
            return $res;
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
     * Stores a file in the VFS from raw data.
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
        $res = $this->_checkQuotaWrite('string', $data);
        if (is_a($res, 'PEAR_Error')) {
            return $res;
        }

        $tmpFile = $this->_getTempFile();
        $fp = fopen($tmpFile, 'wb');
        fwrite($fp, $data);
        fclose($fp);

        $result = $this->write($path, $name, $tmpFile, $autocreate);
        unlink($tmpFile);
        return $result;
    }

    /**
     * Deletes a file from the VFS.
     *
     * @param string $path  The path to delete the file from.
     * @param string $name  The filename to delete.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function deleteFile($path, $name)
    {
        $res = $this->_checkQuotaDelete($path, $name);
        if (is_a($res, 'PEAR_Error')) {
            return $res;
        }

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
     * Checks if a given item is a folder.
     *
     * @param string $path  The parent folder.
     * @param string $name  The item name.
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
     * Deletes a folder from the VFS.
     *
     * @param string $path        The parent folder.
     * @param string $name        The name of the folder to delete.
     * @param boolean $recursive  Force a recursive delete?
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
     * Renames a file in the VFS.
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
        if (is_a($conn = $this->_connect(), 'PEAR_Error')) {
            return $conn;
        }

        if (is_a($result = $this->autocreatePath($newpath), 'PEAR_Error')) {
            return $result;
        }

        if (!@ftp_rename($this->_stream, $this->_getPath($oldpath, $oldname), $this->_getPath($newpath, $newname))) {
            return PEAR::raiseError(sprintf(_("Unable to rename VFS file \"%s\"."), $this->_getPath($oldpath, $oldname)));
        }

        return true;
    }

    /**
     * Creates a folder on the VFS.
     *
     * @param string $path  The parent folder.
     * @param string $name  The name of the new folder.
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
     * Changes permissions for an item on the VFS.
     *
     * @param string $path        The parent folder of the item.
     * @param string $name        The name of the item.
     * @param string $permission  The permission to set.
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
     * Returns an an unsorted file list of the specified directory.
     *
     * @param string $path       The path of the directory.
     * @param mixed $filter      String/hash to filter file/dirname on.
     * @param boolean $dotfiles  Show dotfiles?
     * @param boolean $dironly   Show only directories?
     *
     * @return array  File list on success or PEAR_Error on failure.
     */
    function _listFolder($path = '', $filter = null, $dotfiles = true,
                         $dironly = false)
    {
        $conn = $this->_connect();
        if (is_a($conn, 'PEAR_Error')) {
            return $conn;
        }

        $files = array();

        if (empty($this->_type)) {
            if (!empty($this->_params['type'])) {
                $this->_type = $this->_params['type'];
            } else {
                $type = VFS::strtolower(@ftp_systype($this->_stream));
                if ($type == 'unknown') {
                    // Go with unix-style listings by default.
                    $type = 'unix';
                } elseif (strpos($type, 'win') !== false) {
                    $type = 'win';
                } elseif (strpos($type, 'netware') !== false) {
                    $type = 'netware';
                }

                $this->_type = $type;
            }
        }

        $olddir = $this->getCurrentDirectory();
        if (strlen($path)) {
            $res = $this->_setPath($path);
            if (is_a($res, 'PEAR_Error')) {
                return $res;
            }
        }

        if ($this->_type == 'unix') {
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

        /* If 'maplocalids' is set, check for the POSIX extension. */
        $mapids = false;
        if (!empty($this->_params['maplocalids']) &&
            extension_loaded('posix')) {
            $mapids = true;
        }

        $currtime = time();

        foreach ($list as $line) {
            $file = array();
            $item = preg_split('/\s+/', $line);
            if (($this->_type == 'unix') ||
                (($this->_type == 'win') && !preg_match('|\d\d-\d\d-\d\d|', $item[0]))) {
                if (count($item) < 8 || substr($line, 0, 5) == 'total') {
                    continue;
                }
                $file['perms'] = $item[0];
                if ($mapids) {
                    if (!isset($this->_uids[$item[2]])) {
                        $entry = posix_getpwuid($item[2]);
                        $this->_uids[$item[2]] = (empty($entry)) ? $item[2] : $entry['name'];
                    }
                    $file['owner'] = $this->_uids[$item[2]];
                    if (!isset($this->_uids[$item[3]])) {
                        $entry = posix_getgrgid($item[3]);
                        $this->_uids[$item[3]] = (empty($entry)) ? $item[3] : $entry['name'];
                    }
                    $file['group'] = $this->_uids[$item[3]];

                } else {
                    $file['owner'] = $item[2];
                    $file['group'] = $item[3];
                }

                if (!empty($this->_params['lsformat']) &&
                    ($this->_params['lsformat'] == 'aix')) {
                    $file['name'] = substr($line, strpos($line, sprintf("%s %2s %-5s", $item[5], $item[6], $item[7])) + 13);
                } else {
                    $file['name'] = substr($line, strpos($line, sprintf("%s %2s %5s", $item[5], $item[6], $item[7])) + 13);
                }

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
                if (strpos($item[7], ':') !== false) {
                    $file['date'] = strtotime($item[7] . ':00' . $item[5] . ' ' . $item[6] . ' ' . date('Y', $currtime));
                    // If the ftp server reports a file modification date more
                    // less than one day in the future, don't try to subtract
                    // a year from the date.  There is no way to know, for
                    // example, if the VFS server and the ftp server reside
                    // in different timezones.  We should simply report to the
                    //  user what the FTP server is returning.
                    if ($file['date'] > ($currtime + 86400)) {
                        $file['date'] = strtotime($item[7] . ':00' . $item[5] . ' ' . $item[6] . ' ' . (date('Y', $currtime) - 1));
                    }
                } else {
                    $file['date'] = strtotime('00:00:00' . $item[5] . ' ' . $item[6] . ' ' . $item[7]);
                }
            } elseif ($this->_type == 'netware') {
                if (count($item) < 8 || substr($line, 0, 5) == 'total') {
                    continue;
                }

                $file = array();
                $file['perms'] = $item[1];
                $file['owner'] = $item[2];
                if ($item[0] == 'd') {
                    $file['type'] = '**dir';
                } else {
                    $file['type'] = '**none';
                }
                $file['size'] = $item[3];

                // We don't know the timezone here. Just report what the FTP server says.
                if (strpos($item[6], ':') !== false) {
                    $file['date'] = strtotime($item[6] . ':00 ' . $item[5] . ' ' . $item[4] . ' ' . date('Y'));
                } else {
                    $file['date'] = strtotime('00:00:00 ' . $item[5] . ' ' . $item[4] . ' ' . $item[6]);
                }

                $file['name'] = $item[7];
                $index = 8;
                while ($index < count($item)) {
                    $file['name'] .= ' ' . $item[$index];
                    $index++;
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
     * Returns a sorted list of folders in the specified directory.
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
     * @param string $path         The path of the original file.
     * @param string $name         The name of the original file.
     * @param string $dest         The name of the destination directory.
     * @param boolean $autocreate  Automatically create directories?
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function copy($path, $name, $dest, $autocreate = false)
    {
        $orig = $this->_getPath($path, $name);
        if (preg_match('|^' . preg_quote($orig) . '/?$|', $dest)) {
            return PEAR::raiseError(_("Cannot copy file(s) - source and destination are the same."));
        }

        $conn = $this->_connect();
        if (is_a($conn, 'PEAR_Error')) {
            return $conn;
        }

        if ($autocreate) {
            $result = $this->autocreatePath($dest);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $fileCheck = $this->listFolder($dest, null, true);
        if (is_a($fileCheck, 'PEAR_Error')) {
            return $fileCheck;
        }
        foreach ($fileCheck as $file) {
            if ($file['name'] == $name) {
                return PEAR::raiseError(sprintf(_("%s already exists."), $this->_getPath($dest, $name)));
            }
        }

        if ($this->isFolder($path, $name)) {
            if (is_a($result = $this->_copyRecursive($path, $name, $dest), 'PEAR_Error')) {
                return $result;
            }
        } else {
            $tmpFile = $this->_getTempFile();
            $fetch = @ftp_get($this->_stream, $tmpFile, $orig, FTP_BINARY);
            if (!$fetch) {
                unlink($tmpFile);
                return PEAR::raiseError(sprintf(_("Failed to copy from \"%s\"."), $orig));
            }

            $res = $this->_checkQuotaWrite('file', $tmpFile);
            if (is_a($res, 'PEAR_Error')) {
                return $res;
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
     * @param string $path         The path of the original file.
     * @param string $name         The name of the original file.
     * @param string $dest         The destination file name.
     * @param boolean $autocreate  Automatically create directories?
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function move($path, $name, $dest, $autocreate = false)
    {
        $orig = $this->_getPath($path, $name);
        if (preg_match('|^' . preg_quote($orig) . '/?$|', $dest)) {
            return PEAR::raiseError(_("Cannot move file(s) - destination is within source."));
        }

        $conn = $this->_connect();
        if (is_a($conn, 'PEAR_Error')) {
            return $conn;
        }

        if ($autocreate) {
            $result = $this->autocreatePath($dest);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $fileCheck = $this->listFolder($dest, null, true);
        if (is_a($fileCheck, 'PEAR_Error')) {
            return $fileCheck;
        }
        foreach ($fileCheck as $file) {
            if ($file['name'] == $name) {
                return PEAR::raiseError(sprintf(_("%s already exists."), $this->_getPath($dest, $name)));
            }
        }

        if (!@ftp_rename($this->_stream, $orig, $this->_getPath($dest, $name))) {
            return PEAR::raiseError(sprintf(_("Failed to move to \"%s\"."), $this->_getPath($dest, $name)));
        }

        return true;
    }

    /**
     * Returns the current working directory on the FTP server.
     *
     * @return string  The current working directory.
     */
    function getCurrentDirectory()
    {
        if (is_a($connected = $this->_connect(), 'PEAR_Error')) {
            return $connected;
        }
        return @ftp_pwd($this->_stream);
    }

    /**
     * Changes the current directory on the server.
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
     * Returns the parent directory of the specified path.
     *
     * @access private
     *
     * @param string $path  The path to get the parent of.
     *
     * @return string  The parent directory (string) on success or a PEAR_Error
     *                 object on failure.
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
                    return PEAR::raiseError(sprintf(_("Required \"%s\" not specified in VFS configuration."), $val));
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
                @ftp_quit($this->_stream);
                $this->_stream = false;
                return PEAR::raiseError(_("Authentication to FTP server failed."));
            }

            if (!empty($this->_params['pasv'])) {
                @ftp_pasv($this->_stream, true);
            }

            if (!empty($this->_params['timeout'])) {
                ftp_set_option($this->_stream, FTP_TIMEOUT_SEC, $this->_params['timeout']);
            }
        }

        return true;
    }

}
