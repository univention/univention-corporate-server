<?php
/**
 * VFS implementation for an SSH2 server.
 * This module requires the SSH2 (version 0.10+) PECL package.
 *
 * Required values for $params:<pre>
 *      'username'       The username with which to connect to the ssh2 server.
 *      'password'       The password with which to connect to the ssh2 server.
 *      'hostspec'       The ssh2 server to connect to.</pre>
 *
 * Optional values for $params:<pre>
 *      'port'           The port used to connect to the ssh2 server if other
 *                       than 22.</pre>
 *
 * $Horde: framework/VFS/lib/VFS/ssh2.php,v 1.1.2.16 2009-11-01 02:29:08 chuck Exp $
 *
 * Copyright 2006-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @editor  Cliff Green <green@umdnj.edu>
 * @since   Horde 3.2
 * @package VFS
 */
class VFS_ssh2 extends VFS {

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
     * Variable holding the connection to the ssh2 server.
     *
     * @var resource
     */
    var $_stream = false;

    /**
     * The SFTP resource stream.
     *
     * @var resource
     */
    var $_sftp;

    /**
     * The current working directory.
     *
     * @var string
     */
    var $_cwd;

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

        $statinfo = @ssh2_sftp_stat($this->_sftp, $this->_getPath($path, $name));
        if (($size = $statinfo['size']) === false) {
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

        clearstatcache();
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
        $result = $this->_connect();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        // Create a temporary file and register it for deletion at the
        // end of this request.
        $localFile = $this->_getTempFile();
        if (!$localFile) {
            return PEAR::raiseError(_("Unable to create temporary file."));
        }
        register_shutdown_function(create_function('', 'unlink(\'' . addslashes($localFile) . '\');'));

        if (!$this->_recv($this->_getPath($path, $name), $localFile)) {
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

        if (!$this->_send($tmpFile, $this->_getPath($path, $name)))  {
            if ($autocreate) {
                $result = $this->autocreatePath($path);
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }
                if (!$this->_send($tmpFile, $this->_getPath($path, $name))) {
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
        if (function_exists('file_put_contents')) {
            file_put_contents($tmpFile, $data);
        } else {
            $fp = fopen($tmpFile, 'wb');
            fwrite($fp, $data);
            fclose($fp);
        }

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

        if (!@ssh2_sftp_unlink($this->_sftp, $this->_getPath($path, $name))) {
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

        /* See if we can stat the remote filename. ANDed with 040000 is true
         * if it is a directory. */
        $statinfo = @ssh2_sftp_stat($this->_sftp, $this->_getPath($path, $name));
        return $statinfo['mode'] & 040000;
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

            if (!@ssh2_sftp_rmdir($this->_sftp, $this->_getPath($path, $name))) {
                return PEAR::raiseError(sprintf(_("Cannot remove directory \"%s\"."), $this->_getPath($path, $name)));
            }
        } else {
            if (!@ssh2_sftp_unlink($this->_sftp, $this->_getPath($path, $name))) {
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
        $conn = $this->_connect();
        if (is_a($conn, 'PEAR_Error')) {
            return $conn;
        }

        if (is_a($res = $this->autocreatePath($newpath), 'PEAR_Error')) {
            return $res;
        }

        if (!@ssh2_sftp_rename($this->_sftp, $this->_getPath($oldpath, $oldname), $this->_getPath($newpath, $newname))) {
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

        if (!@ssh2_sftp_mkdir($this->_sftp, $this->_getPath($path, $name))) {
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

        if (!@ssh2_exec($this->_stream, 'chmod ' . escapeshellarg($permission) . ' ' . escapeshellarg($this->_getPath($path, $name)))) {
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

        /* If 'maplocalids' is set, check for the POSIX extension. */
        $mapids = false;
        if (!empty($this->_params['maplocalids']) &&
            extension_loaded('posix')) {
            $mapids = true;
        }

        // THIS IS A PROBLEM....  there is no builtin systype() fn for SSH2.
        // Go with unix-style listings for now...
        $type = 'unix';

        $olddir = $this->getCurrentDirectory();
        if (strlen($path)) {
            $res = $this->_setPath($path);
            if (is_a($res, 'PEAR_Error')) {
                return $res;
            }
        }

        if ($type == 'unix') {
            $ls_args = 'l';

            // Get numeric ids if we're going to use posix_* functions to
            // map them.
            if ($mapids) {
                $ls_args .= 'n';
            }

            // If we don't want dotfiles, We can save work here by not doing
            // an ls -a and then not doing the check later (by setting
            // $dotfiles to true, the if is short-circuited).
            if ($dotfiles) {
                $ls_args .= 'a';
                $dotfiles = true;
            }

            $stream = @ssh2_exec($this->_stream, 'LC_TIME=C ls -' . $ls_args . ' ' . escapeshellarg($path));
        } else {
            $stream = @ssh2_exec($this->_stream, '');
        }

        stream_set_blocking($stream, true);
        unset($list);
        while (!feof($stream)) {
            $line = fgets($stream);
            if ($line === false) {
                break;
            }
            $list[] = trim($line);
        }
        fclose($stream);

        if (!is_array($list)) {
            if (isset($olddir)) {
                $res = $this->_setPath($olddir);
                if (is_a($res, 'PEAR_Error')) {
                    return $res;
                }
            }
            return array();
        }

        $currtime = time();

        foreach ($list as $line) {
            $file = array();
            $item = preg_split('/\s+/', $line);
            if (($type == 'unix') ||
                (($type == 'win') &&
                 !preg_match('|\d\d-\d\d-\d\d|', $item[0]))) {
                if ((count($item) < 8) || (substr($line, 0, 5) == 'total')) {
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
                $file['name'] = substr($line, strpos($line, sprintf("%s %2s %5s", $item[5], $item[6], $item[7])) + 13);

                // Filter out '.' and '..' entries.
                if (preg_match('/^\.\.?\/?$/', $file['name'])) {
                    continue;
                }

                // Filter out dotfiles if they aren't wanted.
                if (!$dotfiles && (substr($file['name'], 0, 1) == '.')) {
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
                       if ((count($name) == 1) ||
                           (($name[0] === '') && (count($name) == 2))) {
                           $file['linktype'] = '**none';
                       } else {
                           $file['linktype'] = VFS::strtolower(array_pop($name));
                       }
                   }
                } elseif ($p1 === 'd') {
                    $file['type'] = '**dir';
                } else {
                    $name = explode('.', $file['name']);
                    if ((count($name) == 1) ||
                        ((substr($file['name'], 0, 1) === '.') &&
                         (count($name) == 2))) {
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
                    // If the ssh2 server reports a file modification date more
                    // less than one day in the future, don't try to subtract
                    // a year from the date.  There is no way to know, for
                    // example, if the VFS server and the ssh2 server reside
                    // in different timezones.  We should simply report to the
                    //  user what the SSH2 server is returning.
                    if ($file['date'] > ($currtime + 86400)) {
                        $file['date'] = strtotime($item[7] . ':00' . $item[5] . ' ' . $item[6] . ' ' . (date('Y', $currtime) - 1));
                    }
                } else {
                    $file['date'] = strtotime('00:00:00' . $item[5] . ' ' . $item[6] . ' ' . $item[7]);
                }
            } elseif ($type == 'netware') {
                $file = Array();
                $file['perms'] = $item[1];
                $file['owner'] = $item[2];
                if ($item[0] == 'd') {
                    $file['type'] = '**dir';
                } else {
                    $file['type'] = '**none';
                }
                $file['size'] = $item[3];
                $file['name'] = $item[7];
                $index = 8;
                while ($index < count($item)) {
                    $file['name'] .= ' ' . $item[$index];
                    $index++;
                }
            } else {
                /* Handle Windows SSH2 servers returning DOS-style file
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
                    if ((count($name) == 1) ||
                        ((substr($file['name'], 0, 1) === '.') &&
                         (count($name) == 2))) {
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
        $folder['abbrev'] = $folder['label'] = '..';

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
     * @param boolean $autocreate  Auto-create the directory if it doesn't
     *                             exist?
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
            $res = $this->autocreatePath($dest);
            if (is_a($res, 'PEAR_Error')) {
                return $res;
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
            $result = $this->_copyRecursive($path, $name, $dest);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        } else {
            $tmpFile = $this->_getTempFile();
            $fetch = $this->_recv($orig, $tmpFile);
            if (!$fetch) {
                unlink($tmpFile);
                return PEAR::raiseError(sprintf(_("Failed to copy from \"%s\"."), $orig));
            }

            $res = $this->_checkQuotaWrite('file', $tmpFile);
            if (is_a($res, 'PEAR_Error')) {
                return $res;
            }

            if (!$this->_send($tmpFile, $this->_getPath($dest, $name))) {
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
     * @param boolean $autocreate  Auto-create the directory if it doesn't
     *                             exist?
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
            $res = $this->autocreatePath($dest);
            if (is_a($res, 'PEAR_Error')) {
                return $res;
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

        if (!@ssh2_sftp_rename($this->_sftp, $orig, $this->_getPath($dest, $name))) {
            return PEAR::raiseError(sprintf(_("Failed to move to \"%s\"."), $this->_getPath($dest, $name)));
        }

        return true;
    }

    /**
     * Returns the current working directory on the SSH2 server.
     *
     * @return string  The current working directory.
     */
    function getCurrentDirectory()
    {
        if (is_a($res = $this->_connect(), 'PEAR_Error')) {
            return $res;
        }
        if (!strlen($this->_cwd)) {
            $stream = @ssh2_exec($this->_stream, 'pwd');
            stream_set_blocking($stream, true);
            $this->_cwd = trim(fgets($stream));
        }
        return $this->_cwd;
    }

    /**
     * Changes the current directory on the server.
     *
     * @access private
     *
     * @param string $path  The path to change to.
     *
     * @return boolean  True on success, or a PEAR_Error on failure.
     */
    function _setPath($path)
    {
        if ($stream = @ssh2_exec($this->_stream, 'cd ' . escapeshellarg($path) . '; pwd')) {
            stream_set_blocking($stream, true);
            $this->_cwd = trim(fgets($stream));
            fclose($stream);
            return true;
        } else {
            return PEAR::raiseError(sprintf(_("Unable to change to %s."), $path));
        }
    }

    /**
     * Returns the full path of an item.
     *
     * @access private
     *
     * @param string $path  The directory of the item.
     * @param string $name  The name of the item.
     *
     * @return mixed  Full path to the file when $path is not empty and just
     *                $name when not set.
     */
    function _getPath($path, $name)
    {
        if ($path !== '') {
            return ($path . '/' . $name);
        }
        return $name;
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

        $this->_setPath('cd ' . $path . '/..');
        return $this->getCurrentDirectory();
    }

    /**
     * Attempts to open a connection to the SSH2 server.
     *
     * @access private
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function _connect()
    {
        if ($this->_stream === false) {
            if (!extension_loaded('ssh2')) {
                return PEAR::raiseError(_("The SSH2 PECL extension is not available."));
            }

            if (!is_array($this->_params)) {
                return PEAR::raiseError(_("No configuration information specified for SSH2 VFS."));
            }

            $required = array('hostspec', 'username', 'password');
            foreach ($required as $val) {
                if (!isset($this->_params[$val])) {
                    return PEAR::raiseError(sprintf(_("Required \"%s\" not specified in VFS configuration."), $val));
                }
            }

            /* Connect to the ssh2 server using the supplied parameters. */
            if (empty($this->_params['port'])) {
                $this->_stream = @ssh2_connect($this->_params['hostspec']);
            } else {
                $this->_stream = @ssh2_connect($this->_params['hostspec'], $this->_params['port']);
            }
            if (!$this->_stream) {
                return PEAR::raiseError(_("Connection to SSH2 server failed."));
            }

            $connected = @ssh2_auth_password($this->_stream, $this->_params['username'], $this->_params['password']);
            if (!$connected) {
                $this->_stream = false;
                return PEAR::raiseError(_("Authentication to SSH2 server failed."));
            }

            /* Create sftp resource. */
            $this->_sftp = @ssh2_sftp($this->_stream);
        }

        return true;
    }

    /**
     * Sends local file to remote host.
     * This function exists because the php_scp_* functions doesn't seem to work on some hosts.
     *
     * @access private
     *
     * @param string $local   Full path to the local file.
     * @param string $remote  Full path to the remote location.
     *
     * @return boolean TRUE on success, FALSE on failure.
     */
    function _send($local, $remote)
    {
        return @copy($local, $this->_wrap($remote));
    }

    /**
     * Receives file from remote host.
     * This function exists because the php_scp_* functions doesn't seem to work on some hosts.
     *
     * @access private
     *
     * @param string $local  Full path to the local file.
     * @param string $remote Full path to the remote location.
     *
     * @return boolean TRUE on success, FALSE on failure.
     */
    function _recv($remote, $local)
    {
        return @copy($this->_wrap($remote), $local);
    }

    /**
     * Generate a stream wrapper file spec for a remote file path
     *
     * @access private
     *
     * @param string $remote  Full path to the remote location
     *
     * @return string  A full stream wrapper path to the remote location
     */
    function _wrap($remote)
    {
        return 'ssh2.sftp://' . $this->_params['username'] . ':' . $this->_params['password']
            . '@' . $this->_params['hostspec'] . ':' . $this->_params['port'] . $remote;
    }

}
