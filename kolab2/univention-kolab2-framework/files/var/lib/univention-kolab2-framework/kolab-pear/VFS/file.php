<?php
/**
 * VFS implementation for a standard filesystem.
 *
 * <pre>
 * Required values for $params:
 *      'vfsroot'       The root path
 * </pre>
 *
 * Note: The user that your webserver runs as (commonly 'nobody',
 * 'apache', or 'www-data') MUST have read/write permission to the
 * directory you specific as the 'vfsroot'.
 *
 * $Horde: framework/VFS/VFS/file.php,v 1.57 2004/05/27 22:06:27 jan Exp $
 *
 * Copyright 2002-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.2
 * @package VFS
 */
class VFS_file extends VFS {

    /**
     * List of permissions and if they can be changed in this VFS
     * backend.
     *
     * @var array $_permissions
     */
    var $_permissions = array(
        'owner' => array('read' => true, 'write' => true, 'execute' => true),
        'group' => array('read' => true, 'write' => true, 'execute' => true),
        'all'   => array('read' => true, 'write' => true, 'execute' => true)
    );

    /**
     * Constructs a new Filesystem based VFS object.
     *
     * @access public
     *
     * @param optional array $params  A hash containing connection parameters.
     */
    function VFS_file($params = array())
    {
        parent::VFS($params);

        if (substr($this->_params['vfsroot'], -1) == '/' ||
            substr($this->_params['vfsroot'], -1) == '\\') {
            $this->_params['vfsroot'] = substr($this->_params['vfsroot'], 0, strlen($this->_params['vfsroot']) - 1);
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
     * @return string  The file data.
     */
    function read($path, $name)
    {
        $file = $this->_getNativePath($path, $name);
        $fp = @fopen($file, 'rb');
        if (!$fp) {
            return PEAR::raiseError(_("Unable to open VFS file."));
        }
        $data = fread($fp, filesize($file));
        fclose($fp);

        return $data;
    }

    /**
     * Store a file in the VFS, with the data copied from a temporary
     * file.
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
    function write($path, $name, $tmpFile, $autocreate = true)
    {
        if (!@is_dir($this->_getNativePath($path))) {
            if ($autocreate) {
                $res = $this->autocreatePath($path);
                if (is_a($res, 'PEAR_Error')) {
                    return $res;
                }
            } else {
                return PEAR::raiseError(_("VFS directory does not exist."));
            }
        }

        $fp = @fopen($this->_getNativePath($path, $name), 'w');
        if (!$fp) {
            return PEAR::raiseError(_("Unable to open VFS file for writing."));
        }

        $dataFP = @fopen($tmpFile, 'rb');
        $data = @fread($dataFP, filesize($tmpFile));
        fclose($dataFP);

        if (!@fwrite($fp, $data)) {
            return PEAR::raiseError(_("Unable to write VFS file data."));
        }

        return true;
    }

    /**
     * Moves a file in the database and the file system.
     *
     * @access public
     *
     * @param string $path  The path to store the file in.
     * @param string $name  The filename to use.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function move($path, $name, $dest)
    {
        $fileCheck = $this->listFolder($dest, false);
        foreach ($fileCheck as $file) {
            if ($file['name'] == $name) {
                return PEAR::raiseError(_("Unable to move VFS file."));
            }
        }

        if (!@rename($this->_getNativePath($path, $name), $this->_getNativePath($dest, $name))) {
            return PEAR::raiseError(_("Unable to move VFS file."));
        }

        return true;
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
        $fileCheck = $this->listFolder($dest, false);
        if ($path == $dest) {
            return PEAR::raiseError(_("The file can not be copied onto itself."));
        }
        foreach ($fileCheck as $file) {
            if ($file['name'] == $name) {
                return PEAR::raiseError(_("Unable to copy VFS file."));
            }
        }
        if (!@copy($this->_getNativePath($path, $name), $this->_getNativePath($dest, $name))) {
            return PEAR::raiseError(_("Unable to copy VFS file."));
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
    function writeData($path, $name, $data, $autocreate = true)
    {
        if (!@is_dir($this->_getNativePath($path))) {
            if ($autocreate) {
                $res = $this->autocreatePath($path);
                if (is_a($res, 'PEAR_Error')) {
                    return $res;
                }
            } else {
                return PEAR::raiseError(_("VFS directory does not exist."));
            }
        }

        $fp = @fopen($this->_getNativePath($path, $name), 'w');
        if (!$fp) {
            return PEAR::raiseError(_("Unable to open VFS file for writing."));
        }

        if (!@fwrite($fp, $data)) {
            return PEAR::raiseError(_("Unable to write VFS file data."));
        }

        return true;
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
     */
    function deleteFile($path, $name)
    {
        if (!@unlink($this->_getNativePath($path, $name))) {
            return PEAR::raiseError(_("Unable to delete VFS file."));
        }
    }

    /**
     * Delete a folder from the VFS.
     *
     * @access public
     *
     * @param string $path                 The path to delete the folder from.
     * @param string $name                 The foldername to use.
     * @param optional boolean $recursive  Force a recursive delete?
     *
     * @return mixed True on success or a PEAR_Error object on failure.
     */
    function deleteFolder($path, $name, $recursive = false)
    {
        if ($recursive) {
            $result = $this->emptyFolder($path . '/' . $name);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        } else {
            $list = $this->listFolder($path . '/' . $name);
            if (is_a($list, 'PEAR_Error')) {
                return $list;
            }
            if (count($list)) {
                return PEAR::raiseError(sprintf(_("Unable to delete %s, the directory is not empty"),
                                                $path . '/' . $name));
            }
        }

        if (!@rmdir($this->_getNativePath($path, $name))) {
            return PEAR::raiseError(_("Unable to delete VFS directory."));
        }

        return true;
    }

    /**
     * Creates a folder on the VFS.
     *
     * @access public
     *
     * @param string $path  The path to delete the folder from.
     * @param string $name  The foldername to use.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function createFolder($path, $name)
    {
        if (!@mkdir($this->_getNativePath($path, $name))) {
            return PEAR::raiseError(_("Unable to create VFS directory."));
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
        return @is_dir($this->_getNativePath($path, $name));
    }

    /**
     * Changes permissions for an item in the VFS.
     *
     * @access public
     *
     * @param string $path         The path of directory of the item.
     * @param string $name         The name of the item.
     * @param integer $permission  The octal value of the new permission.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function changePermissions($path, $name, $permission)
    {
        if (!@chmod($this->_getNativePath($path, $name), $permission)) {
            return PEAR::raiseError(sprintf(_("Unable to change permission for VFS file %s/%s."), $path, $name));
        }

        return true;
    }

    /**
     * Return a list of the contents of a folder.
     *
     * @access public
     *
     * @param string $path                The path of the directory.
     * @param optional mixed $filter      String/hash to filter file/dirname
     *                                    on.
     * @param optional boolean $dotfiles  Show dotfiles?
     * @param optional boolean $dironly   Show only directories?
     *
     * @return array  File list on success, PEAR_Error on error.
     */
    function listFolder($path, $filter = null, $dotfiles = true,
                        $dironly = false)
    {
        $files = array();
        $path = isset($path) ? $this->_getNativePath($path) : $this->_getNativePath();

        if (!@is_dir($path)) {
            return PEAR::raiseError(_("Not a directory"));
        }

        if (!@chdir($path)) {
            return PEAR::raiseError(_("Unable to access VFS directory."));
        }

        $handle = opendir($path);
        while (($entry = readdir($handle)) !== false) {
            // Filter out '.' and '..' entries.
            if ($entry == '.' || $entry == '..') {
                continue;
            }

            // Filter out dotfiles if they aren't wanted.
            if (!$dotfiles && substr($entry, 0, 1) == '.') {
                continue;
            }

            // File name
            $file['name'] = $entry;

            // Unix style file permissions
            $file['perms'] = $this->_getUnixPerms(fileperms($entry));

            // Owner
            $file['owner'] = fileowner($entry);
            if (function_exists('posix_getpwuid')) {
                $owner = posix_getpwuid($file['owner']);
                $file['owner'] = $owner['name'];
            }

            // Group
            $file['group'] = filegroup($entry);
            if (function_exists('posix_getgrgid')) {
                $group = posix_getgrgid($file['group']);
                $file['group'] = $group['name'];
            }

            // Size
            $file['size'] = filesize($entry);

            // Date
            $file['date'] = filemtime($entry);

            // Type
            if (@is_dir($entry) && !is_link($entry)) {
                $file['perms'] = 'd' . $file['perms'];
                $file['type'] = '**dir';
                $file['size'] = -1;
            } elseif (is_link($entry)) {
                $file['perms'] = 'l' . $file['perms'];
                $file['type'] = '**sym';
                $file['link'] = readlink($entry);
                $file['linktype'] = '**none';
                if (file_exists($file['link'])) {
                    if (is_dir($file['link'])) {
                        $file['linktype'] = '**dir';
                    } elseif (is_link($file['link'])) {
                        $file['linktype'] = '**sym';
                    } elseif (is_file($file['link'])) {
                        $ext = explode('.', $file['link']);
                        if (!(count($ext) == 1 || ($ext[0] === '' && count($ext) == 2))) {
                            $file['linktype'] = VFS::strtolower($ext[count($ext) - 1]);
                        }
                    }
                } else {
                    $file['linktype'] = '**broken';
                }
            } elseif (is_file($entry)) {
                $file['perms'] = '-' . $file['perms'];
                $ext = explode('.', $entry);

                if (count($ext) == 1 || (substr($file['name'], 0, 1) === '.' && count($ext) == 2)) {
                    $file['type'] = '**none';
                } else {
                    $file['type'] = VFS::strtolower($ext[count($ext) - 1]);
                }
            } else {
                $file['type'] = '**none';
                if ((fileperms($entry) & 0xC000) == 0xC000) {
                    $file['perms'] = 's' . $file['perms'];
                } elseif ((fileperms($entry) & 0x6000) == 0x6000) {
                    $file['perms'] = 'b' . $file['perms'];
                } elseif ((fileperms($entry) & 0x2000) == 0x2000) {
                    $file['perms'] = 'c' . $file['perms'];
                } elseif ((fileperms($entry) & 0x1000) == 0x1000) {
                    $file['perms'] = 'p' . $file['perms'];
                } else {
                    $file['perms'] = '?' . $file['perms'];
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

        $folder['val'] = dirname($path);
        $folder['abbrev'] = '..';
        $folder['label'] = '..';

        $folders[$folder['val']] = $folder;

        foreach ($folderList as $files) {
            $folder['val'] = $path . '/' . $files['name'];
            $folder['abbrev'] = $files['name'];
            $folder['label'] = $folder['val'];

            $folders[$folder['val']] = $folder;
        }

        ksort($folders);

        return $folders;
    }

    /**
     * Return Unix style perms.
     *
     * @access private
     *
     * @param integer $perms  The permissions to set.
     *
     * @return string  Unix style perms.
     */
    function _getUnixPerms($perms)
    {
        // Determine permissions
        $owner['read']    = ($perms & 00400) ? 'r' : '-';
        $owner['write']   = ($perms & 00200) ? 'w' : '-';
        $owner['execute'] = ($perms & 00100) ? 'x' : '-';
        $group['read']    = ($perms & 00040) ? 'r' : '-';
        $group['write']   = ($perms & 00020) ? 'w' : '-';
        $group['execute'] = ($perms & 00010) ? 'x' : '-';
        $world['read']    = ($perms & 00004) ? 'r' : '-';
        $world['write']   = ($perms & 00002) ? 'w' : '-';
        $world['execute'] = ($perms & 00001) ? 'x' : '-';

        // Adjust for SUID, SGID and sticky bit
        if ($perms & 0x800) {
            $owner['execute'] = ($owner['execute'] == 'x') ? 's' : 'S';
        }
        if ($perms & 0x400) {
            $group['execute'] = ($group['execute'] == 'x') ? 's' : 'S';
        }
        if ($perms & 0x200) {
            $world['execute'] = ($world['execute'] == 'x') ? 't' : 'T';
        }

        $unixPerms = $owner['read'] . $owner['write'] . $owner['execute'] .
                     $group['read'] . $group['write'] . $group['execute'] .
                     $world['read'] . $world['write'] . $world['execute'];

        return $unixPerms;
    }

    /**
     * Rename a file or folder in the VFS.
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
        if (!@rename($this->_getNativePath($oldpath, $oldname),
                     $this->_getNativePath($newpath, $newname))) {
            return PEAR::raiseError(sprintf(_("Unable to rename VFS file %s/%s."), $oldpath, $oldname));
        }

        return true;
    }

    /**
     * Return a full filename on the native filesystem, from a VFS
     * path and name.
     *
     * @access private
     *
     * @param optional string $path  The VFS file path.
     * @param optional string $name  The VFS filename.
     *
     * @return string  The full native filename.
     */
    function _getNativePath($path = '', $name = '')
    {
        $name = basename($name);
        if (!empty($name)) {
            if ($name == '..') {
                $name = '';
            } else {
                if (substr($name, 0, 1) != '/') {
                    $name = '/' . $name;
                }
            }
        }

        if (!empty($path)) {
            if (isset($this->_params['home']) &&
                preg_match('|^~/?(.*)$|', $path, $matches)) {
                $path = $this->_params['home'] . '/' . $matches[1];
            }

            $path = str_replace('..', '', $path);
            if (substr($path, 0, 1) == '/') {
                return $this->_params['vfsroot'] . $path . $name;
            } else {
                return $this->_params['vfsroot'] . '/' . $path . $name;
            }
        } else {
            return $this->_params['vfsroot'] . $name;
        }
    }

    /**
     * Stub to check if we have a valid connection. Makes sure that
     * the vfsroot is readable.
     *
     * @access private
     *
     * @return mixed  True if vfsroot is readable, PEAR_Error if it isn't.
     */
    function _connect()
    {
        if ((@is_dir($this->_params['vfsroot']) &&
             @is_readable($this->_params['vfsroot'])) ||
            @mkdir($this->_params['vfsroot'])) {
            return true;
        } else {
            return PEAR::raiseError(_("Unable to read the vfsroot directory."));
        }
    }

}
