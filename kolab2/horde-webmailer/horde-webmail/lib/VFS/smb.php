<?php
/**
 * Stateless VFS implementation for a SMB server, based on smbclient.
 *
 * Required values for $params:
 * <pre>
 *   'username'  - The username with which to connect to the SMB server.
 *   'password'  - The password with which to connect to the SMB server.
 *   'hostspec'  - The SMB server to connect to.
 *   'port'      - The SMB port number to connect to.
 *   'share'     - The share to access on the SMB server.
 *   'smbclient' - The path to the 'smbclient' executable.
 * </pre>
 *
 * Optional values for $params:
 * <pre>
 *   'ipaddress' - The address of the server to connect to.
 * </pre>
 *
 * Functions not implemented:
 *   - changePermissions(): The SMB permission style does not fit with the
 *                          module.
 *
 * $Horde: framework/VFS/lib/VFS/smb.php,v 1.1.2.5 2009-02-06 18:24:20 slusarz Exp $
 *
 * Codebase copyright 2002 Paul Gareau <paul@xhawk.net>.  Adapted with
 * permission by Patrice Levesque <wayne@ptaff.ca> from phpsmb-0.8 code, and
 * converted to the LGPL.  Please do not taunt original author, contact
 * Patrice Levesque or dev@lists.horde.org.
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Paul Gareau <paul@xhawk.net>
 * @author  Patrice Levesque <wayne@ptaff.ca>
 * @since   Horde 3.1
 * @package VFS
 */
class VFS_smb extends VFS {

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
        'owner' => array('read' => false, 'write' => false, 'execute' => false),
        'group' => array('read' => false, 'write' => false, 'execute' => false),
        'all'   => array('read' => false, 'write' => false, 'execute' => false));

    /**
     * Authenticates a user on the SMB server and share.
     *
     * @access private
     *
     * @return boolean|PEAR_Error  True on success or a PEAR_Error on failure.
     */
    function _connect()
    {
        $cmd = array('quit');
        $err = $this->_command('', $cmd);
        if (is_a($err, 'PEAR_Error')) {
            return PEAR::raiseError(_("Authentication to the SMB server failed."));
        }
        return true;
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
        // Create a temporary file and register it for deletion at the
        // end of this request.
        $localFile = $this->_getTempFile();
        if (!$localFile) {
            return PEAR::raiseError(_("Unable to create temporary file."));
        }
        register_shutdown_function(create_function('', 'unlink(\'' . addslashes($localFile) . '\');'));

        list($path, $name) = $this->_escapeShellCommand($path, $name);
        $cmd = array('get \"' . $name . '\" ' . $localFile);
        $result = $this->_command($path, $cmd);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        if (!file_exists($localFile)) {
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
     * @param string $tmpFile      The temporary file containing the data to be
     *                             stored.
     * @param boolean $autocreate  Automatically create directories?
     *
     * @return boolean|PEAR_Error  True on success or a PEAR_Error on failure.
     */
    function write($path, $name, $tmpFile, $autocreate = false)
    {
        // Double quotes not allowed in SMB filename.
        $name = str_replace('"', "'", $name);

        list($path, $name) = $this->_escapeShellCommand($path, $name);
        $cmd = array('put \"' . $tmpFile . '\" \"' . $name . '\"');
        // do we need to first autocreate the directory?
        if ($autocreate) {
            $result = $this->autocreatePath($path);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
        $err = $this->_command($path, $cmd);
        if (is_a($err, 'PEAR_Error')) {
            return $err;
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
     * @return boolean|PEAR_Error  True on success or a PEAR_Error on failure.
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
     * Deletes a file from the VFS.
     *
     * @param string $path  The path to delete the file from.
     * @param string $name  The filename to use.
     *
     * @return boolean|PEAR_Error  True on success or a PEAR_Error on failure.
     */
    function deleteFile($path, $name)
    {
        // In some samba versions after samba-3.0.25-pre2, $path must
        // end in a trailing slash.
        if (substr($path, -1) != '/') {
            $path .= '/';
        }

        list($path, $name) = $this->_escapeShellCommand($path, $name);
        $cmd = array('del \"' . $name . '\"');
        $err = $this->_command($path, $cmd);
        if (is_a($err, 'PEAR_Error')) {
            return $err;
        }
        return true;
    }

    /**
     * Checks if a given pathname is a folder.
     *
     * @param string $path  The path to the folder.
     * @param string $name  The file or folder name.
     *
     * @return boolean  True if it is a folder, false otherwise.
     */
    function isFolder($path, $name)
    {
        list($path, $name) = $this->_escapeShellCommand($path, $name);
        $cmd = array('quit');
        $err = $this->_command($this->_getPath($path, $name), $cmd);
        if (is_a($err, 'PEAR_Error')) {
            return false;
        }
        return true;
    }

    /**
     * Deletes a folder from the VFS.
     *
     * @param string $path        The path to delete the folder from.
     * @param string $name        The name of the folder to delete.
     * @param boolean $recursive  Force a recursive delete?
     *
     * @return boolean|PEAR_Error  True on success or a PEAR_Error on failure.
     */
    function deleteFolder($path, $name, $recursive = false)
    {
        // In some samba versions after samba-3.0.25-pre2, $path must
        // end in a trailing slash.
        if (substr($path, -1) != '/') {
            $path .= '/';
        }

        if (!$this->isFolder($path, $name)) {
            return PEAR::raiseError(sprintf(_("\"%s\" is not a directory."), $path . '/' . $name));
        }

        $file_list = $this->listFolder($this->_getPath($path, $name));
        if (is_a($file_list, 'PEAR_Error')) {
            return $file_list;
        }

        if ($file_list && !$recursive) {
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

        // Really delete the folder.
        list($path, $name) = $this->_escapeShellCommand($path, $name);
        $cmd = array('rmdir \"' . $name . '\"');
        $err = $this->_command($path, $cmd);
        if (is_a($err, 'PEAR_Error')) {
            return PEAR::raiseError(sprintf(_("Unable to delete VFS folder \"%s\"."), $this->_getPath($path, $name)));
        } else {
            return true;
        }
    }

    /**
     * Renames a file in the VFS.
     *
     * @param string $oldpath  The old path to the file.
     * @param string $oldname  The old filename.
     * @param string $newpath  The new path of the file.
     * @param string $newname  The new filename.
     *
     * @return boolean|PEAR_Error  True on success or a PEAR_Error on failure.
     */
    function rename($oldpath, $oldname, $newpath, $newname)
    {
        if (is_a($result = $this->autocreatePath($newpath), 'PEAR_Error')) {
            return $result;
        }

        // Double quotes not allowed in SMB filename. The '/' character should
        // also be removed from the beginning/end of the names.
        $oldname = str_replace('"', "'", trim($oldname, '/'));
        $newname = str_replace('"', "'", trim($newname, '/'));

        if (empty($oldname)) {
            return PEAR::raiseError(_("Unable to rename VFS file to same name."));
        }

        /* If the path was not empty (i.e. the path is not the root path),
         * then add the trailing '/' character to path. */
        if (!empty($oldpath)) {
            $oldpath .= '/';
        }
        if (!empty($newpath)) {
            $newpath .= '/';
        }

        list($file, $name) = $this->_escapeShellCommand($oldname, $newname);
        $cmd = array('rename \"' .  str_replace('/', '\\\\', $oldpath) . $file . '\" \"' .
                                    str_replace('/', '\\\\', $newpath) . $name . '\"');
        if (is_a($err = $this->_command('', $cmd), 'PEAR_Error')) {
            return PEAR::raiseError(sprintf(_("Unable to rename VFS file \"%s\"."), $this->_getPath($path, $name)));
        }

        return true;
    }

    /**
     * Creates a folder on the VFS.
     *
     * @param string $path  The path of directory to create folder.
     * @param string $name  The name of the new folder.
     *
     * @return boolean|PEAR_Error  True on success or a PEAR_Error on failure.
     */
    function createFolder($path, $name)
    {
        // In some samba versions after samba-3.0.25-pre2, $path must
        // end in a trailing slash.
        if (substr($path, -1) != '/') {
            $path .= '/';
        }

        // Double quotes not allowed in SMB filename.
        $name = str_replace('"', "'", $name);

        list($dir, $mkdir) = $this->_escapeShellCommand($path, $name);
        $cmd = array('mkdir \"' . $mkdir . '\"');
        $err = $this->_command($dir, $cmd);
        if (is_a($err, 'PEAR_Error')) {
            return PEAR::raiseError(sprintf(_("Unable to create VFS folder \"%s\"."), $this->_getPath($path, $name)));
        }
        return true;
    }

    /**
     * Returns an unsorted file list.
     *
     * @param string $path       The path of the directory to get the file list
     *                           for.
     * @param mixed $filter      Hash of items to filter based on filename.
     * @param boolean $dotfiles  Show dotfiles? This is irrelevant with
     *                           smbclient.
     * @param boolean $dironly   Show directories only?
     *
     * @return boolean|PEAR_Error  File list on success or a PEAR_Error on
     *                             failure.
     */
    function listFolder($path = '', $filter = null, $dotfiles = true, $dironly = false)
    {
        list($path) = $this->_escapeShellCommand($path);
        $cmd = array('ls');
        $res = $this->_command($path, $cmd);
        if (is_a($res, 'PEAR_Error')) {
            return $res;
        }
        $num_lines = count($res);
        $files = array();
        for ($r = 0; $r < $num_lines; $r++) {
            // Match file listing.
            if (preg_match('/^(\s\s.+\s{6,})/', $res[$r])) {
                // Split into columns at every six spaces
                $split1 = preg_split('/\s{6,}/', trim($res[$r]));
                // If the file name isn't . or ..
                if ($split1[0] != '.' && $split1[0] != '..') {
                    if (isset($split1[2])) {
                        // If there is a small file size, inf could be split
                        // into 3 cols.
                        $split1[1] .= ' ' . $split1[2];
                    }
                    // Split file inf at every one or more spaces.
                    $split2 = preg_split('/\s+/', $split1[1]);
                    if (is_numeric($split2[0])) {
                        // If there is no file attr, shift cols over.
                        array_unshift($split2, '');
                    }
                    $my_name = $split1[0];

                    // Filter out dotfiles if they aren't wanted.
                    if (!$dotfiles && substr($my_name, 0, 1) == '.') {
                        continue;
                    }

                    $my_size = $split2[1];
                    $ext_name = explode('.', $my_name);

                    if ((strpos($split2[0], 'D') !== false)) {
                        $my_type = '**dir';
                        $my_size = -1;
                    } else {
                        $my_type = VFS::strtolower($ext_name[count($ext_name) - 1]);
                    }
                    $my_date = strtotime($split2[4] . ' ' . $split2[3] . ' ' .
                                         $split2[6] . ' ' . $split2[5]);
                    $filedata = array('owner' => '',
                                      'group' => '',
                                      'perms' => '',
                                      'name' => $my_name,
                                      'type' => $my_type,
                                      'date' => $my_date,
                                      'size' => $my_size);
                    // watch for filters and dironly
                    if ($this->_filterMatch($filter, $my_name)) {
                        unset($file);
                        continue;
                    }
                    if ($dironly && $my_type !== '**dir') {
                        unset($file);
                        continue;
                    }

                    $files[$filedata['name']] = $filedata;
                }
            }
        }
        return $files;
    }

    /**
     * Returns a sorted list of folders in specified directory.
     *
     * @param string $path         The path of the directory to get the
     *                             directory list for.
     * @param mixed $filter        Hash of items to filter based on folderlist.
     * @param boolean $dotfolders  Include dotfolders? Irrelevant for SMB.
     *
     * @return boolean|PEAR_Error  Folder list on success or a PEAR_Error on
     *                             failure.
     */
    function listFolders($path = '', $filter = null, $dotfolders = true)
    {
        $folders = array();
        $folder = array();

        $folderList = $this->listFolder($path, null, $dotfolders, true);
        if (is_a($folderList, 'PEAR_Error')) {
            return $folderList;
        }

        // dirname will strip last component from path, even on a directory
        $folder['val'] = dirname($path);
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
     * @param string $path         The path to store the file in.
     * @param string $name         The filename to use.
     * @param string $dest         The destination of the file.
     * @param boolean $autocreate  Automatically create directories?
     *
     * @return boolean|PEAR_Error  True on success or a PEAR_Error on failure.
     */
    function copy($path, $name, $dest, $autocreate = false)
    {
        $orig = $this->_getPath($path, $name);
        if (preg_match('|^' . preg_quote($orig) . '/?$|', $dest)) {
            return PEAR::raiseError(_("Cannot copy file(s) - source and destination are the same."));
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
                return PEAR::raiseError(sprintf(_("%s already exists."),
                                                $this->_getPath($dest, $name)));
            }
        }

        if ($this->isFolder($path, $name)) {
            if (is_a($result = $this->_copyRecursive($path, $name, $dest), 'PEAR_Error')) {
                return $result;
            }
        } else {
            $tmpFile = $this->readFile($path, $name);
            if (is_a($tmpFile, 'PEAR_Error')) {
                return PEAR::raiseError(sprintf(_("Failed to retrieve: %s"), $orig));
            }

            $result = $this->write($dest, $name, $tmpFile);
            if (is_a($result, 'PEAR_Error')) {
                return PEAR::raiseError(sprintf(_("Copy failed: %s"),
                                                $this->_getPath($dest, $name)));
            }
        }

        return true;
    }

    /**
     * Moves a file through the backend.
     *
     * @param string $path         The path to store the file in.
     * @param string $name         The filename to use.
     * @param string $dest         The destination of the file.
     * @param boolean $autocreate  Automatically create directories?
     *
     * @return boolean|PEAR_Error  True on success or a PEAR_Error on failure.
     */
    function move($path, $name, $dest, $autocreate = false)
    {
        $orig = $this->_getPath($path, $name);
        if (preg_match('|^' . preg_quote($orig) . '/?$|', $dest)) {
            return PEAR::raiseError(_("Cannot move file(s) - destination is within source."));
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
                return PEAR::raiseError(sprintf(_("%s already exists."),
                                                $this->_getPath($dest, $name)));
            }
        }

        $err = $this->rename($path, $name, $dest, $name);
        if (is_a($err, 'PEAR_Error')) {
            return PEAR::raiseError(sprintf(_("Failed to move to \"%s\"."),
                                            $this->_getPath($dest, $name)));
        }
        return true;
    }

    /**
     * Replacement for escapeshellcmd(), variable length args, as we only want
     * certain characters escaped.
     *
     * @access private
     *
     * @param array $array  Strings to escape.
     *
     * @return array
     */
    function _escapeShellCommand()
    {
        $ret = array();
        $args = func_get_args();
        foreach ($args as $arg) {
            $ret[] = str_replace(array(';', '\\'), array('\;', '\\\\'), $arg);
        }
        return $ret;
    }

    /**
     * Executes a command and returns output lines in array.
     *
     * @access private
     *
     * @param string $cmd  Command to be executed
     *
     * @return mixed  Array on success, false on failure.
     */
    function _execute($cmd)
    {
        $cmd = str_replace('"-U%"', '-N', $cmd);
        exec($cmd, $out, $ret);

        // In some cases, (like trying to delete a nonexistant file),
        // smbclient will return success (at least on 2.2.7 version I'm
        // testing on). So try to match error strings, even after success.
        if ($ret != 0) {
            $err = '';
            foreach ($out as $line) {
                if (strpos($line, 'Usage:') === 0) {
                    $err = 'Command syntax incorrect';
                    break;
                }
                if (strpos($line, 'ERRSRV') !== false ||
                    strpos($line, 'ERRDOS') !== false) {
                    $err = preg_replace('/.*\((.+)\).*/', '\\1', $line);
                    if (!$err) {
                        $err = $line;
                    }
                    break;
                }
            }
            if (!$err) {
                $err = $out ? $out[count($out) - 1] : $ret;
            }
            return PEAR::raiseError($err);
        }

        // Check for errors even on success.
        $err = '';
        foreach ($out as $line) {
            if (strpos($line, 'NT_STATUS_NO_SUCH_FILE') !== false ||
                strpos($line, 'NT_STATUS_OBJECT_NAME_NOT_FOUND') !== false) {
                $err = _("No such file");
                break;
            } elseif (strpos($line, 'NT_STATUS_ACCESS_DENIED') !== false) {
                $err = _("Permission Denied");
                break;
            }
        }

        if ($err) {
            return PEAR::raiseError($err);
        }

        return $out;
    }

    /**
     * Executes SMB commands - without authentication - and returns output
     * lines in array.
     *
     * @access private
     *
     * @param array $path  Base path for command.
     * @param array $cmd   Commands to be executed.
     *
     * @return mixed  Array on success, false on failure.
     */
    function _command($path, $cmd)
    {
        list($share) = $this->_escapeShellCommand($this->_params['share']);
        putenv('PASSWD=' . $this->_params['password']);
        $ipoption = (isset($this->_params['ipaddress'])) ? (' -I ' . $this->_params['ipaddress']) : null;
        $fullcmd = $this->_params['smbclient'] .
            ' "//' . $this->_params['hostspec'] . '/' . $share . '"' .
            ' "-p' . $this->_params['port'] . '"' .
            ' "-U' . $this->_params['username'] . '"' .
            ' -D "' . $path . '" ' .
            $ipoption .
            ' -c "';
        foreach ($cmd as $c) {
            $fullcmd .= $c . ";";
        }
        $fullcmd .= '"';
        return $this->_execute($fullcmd);
    }

}
