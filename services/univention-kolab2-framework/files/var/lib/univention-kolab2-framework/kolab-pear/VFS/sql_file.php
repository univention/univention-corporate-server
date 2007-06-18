<?php

/** @constant integer VFS_FILE  File value for vfs_type column. */
define('VFS_FILE', 1);

/** @constant integer VFS_FOLDER  Folder value for vfs_type column. */
define('VFS_FOLDER', 2);

/**
 * VFS:: implementation using PHP's PEAR database abstraction
 * layer and local file system for file storage.
 *
 * <pre>
 * Required values for $params:
 *      'phptype'       The database type (ie. 'pgsql', 'mysql, etc.).
 *      'hostspec'      The hostname of the database server.
 *      'protocol'      The communication protocol ('tcp', 'unix', etc.).
 *      'username'      The username with which to connect to the database.
 *      'password'      The password associated with 'username'.
 *      'database'      The name of the database.
 *      'vfsroot'       The root directory of where the files should be
 *                      actually stored.
 *
 * Optional values:
 *      'table'         The name of the vfs table in 'database'. Defaults to
 *                      'horde_vfs'.
 *
 * Required by some database implementations:
 *      'options'       Additional options to pass to the database.
 *      'tty'           The TTY on which to connect to the database.
 *      'port'          The port on which to connect to the database.
 * </pre>
 *
 * The table structure for the VFS can be found in
 * horde/scripts/db/vfs.sql.
 *
 * $Horde: framework/VFS/VFS/sql_file.php,v 1.40 2004/04/08 18:33:17 slusarz Exp $
 *
 * @author  Michael Varghese <mike.varghese@ascellatech.com>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.2
 * @package VFS
 */
class VFS_sql_file extends VFS {

    /**
     * Handle for the current database connection.
     *
     * @var object DB $_db
     */
    var $_db = false;

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
    function write($path, $name, $tmpFile, $autocreate = false)
    {
        $dataFP = @fopen($tmpFile, 'rb');
        $data = @fread($dataFP, filesize($tmpFile));
        fclose($dataFP);
        return $this->writeData($path, $name, $data, $autocreate);
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
        $fp = @fopen($this->_getNativePath($path, $name), 'w');
        if (!$fp) {
            if ($autocreate) {
                $result = $this->autocreatePath($path);
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }
                $fp = @fopen($this->_getNativePath($path, $name), 'w');
                if (!$fp) {
                    return PEAR::raiseError(_("Unable to open VFS file for writing."));
                }
            }
            return PEAR::raiseError(_("Unable to open VFS file for writing."));
        }

        if (!@fwrite($fp, $data)) {
            return PEAR::raiseError(_("Unable to write VFS file data."));
        }

        if (is_a($this->_writeSQLData($path, $name, $autocreate), 'PEAR_Error')) {
            @unlink($this->_getNativePath($path, $name));
            return PEAR::raiseError(_("Unable to write VFS file data."));
        }
    }

    /**
     * Moves a file in the database and the file system.
     *
     * @access public
     *
     * @param string $path  The path to store the file in.
     * @param string $name  The old filename.
     * @param string $dest  The new filename.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function move($path, $name, $dest)
    {
        $conn = $this->_connect();
        if (is_a($conn, 'PEAR_Error')) {
            return $conn;
        }

        $fileCheck = $this->listFolder($dest, null, false);
        foreach ($fileCheck as $file) {
            if ($file['name'] == $name) {
                return PEAR::raiseError(_("Unable to move VFS file."));
            }
        }

        if (strpos($dest, $this->_getSQLNativePath($path, $name)) !== false) {
            return PEAR::raiseError(_("Unable to move VFS file."));
        }

        return $this->rename($path, $name, $dest, $name);
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

        $fileCheck = $this->listFolder($dest, null, false);
        foreach ($fileCheck as $file) {
            if ($file['name'] == $name) {
                return PEAR::raiseError(_("Unable to copy VFS file."));
            }
        }

        if (strpos($dest, $this->_getSQLNativePath($path, $name)) !== false) {
            return PEAR::raiseError(_("Unable to copy VFS file."));
        }

        if (is_dir($this->_getNativePath($path, $name))) {
            return $this->_recursiveCopy($path, $name, $dest);
        }

        if (!@copy($this->_getNativePath($path, $name), $this->_getNativePath($dest, $name))) {
            return PEAR::raiseError(_("Unable to copy VFS file."));
        }

        $id = $this->_db->nextId($this->_params['table']);

        $query = sprintf('INSERT INTO %s (vfs_id, vfs_type, vfs_path, vfs_name, vfs_modified, vfs_owner) VALUES (%s, %s, %s, %s, %s, %s)',
                         $this->_params['table'],
                         $this->_db->quote($id),
                         $this->_db->quote(VFS_FILE),
                         $this->_db->quote($dest),
                         $this->_db->quote($name),
                         $this->_db->quote(time()),
                         $this->_db->quote($this->_params['user'])
                         );

        $result = $this->_db->query($query);

        if (is_a($result, 'PEAR_Error')) {
            unlink($this->_getNativePath($dest, $name));
            return $result;
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

        $id = $this->_db->nextId($this->_params['table']);
        $result = $this->_db->query(sprintf('INSERT INTO %s (vfs_id, vfs_type, vfs_path, vfs_name, vfs_modified, vfs_owner)
                                         VALUES (%s, %s, %s, %s, %s, %s)',
                                         $this->_params['table'],
                                         $this->_db->quote($id),
                                         $this->_db->quote(VFS_FOLDER),
                                         $this->_db->quote($path),
                                         $this->_db->quote($name),
                                         $this->_db->quote(time()),
                                         $this->_db->quote($this->_params['user'])));
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (!@mkdir($this->_getNativePath($path, $name))) {
            $result = $this->_db->query(sprintf('DELETE FROM %s WHERE vfs_id = %s',
                                                $this->_params['table'],
                                                $this->_db->quote($id)));
            return PEAR::raiseError(_("Unable to create VFS directory."));
        }

        return true;
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
        $conn = $this->_connect();
        if (is_a($conn, 'PEAR_Error')) {
            return $conn;
        }

        $result = $this->_db->query(sprintf('UPDATE %s SET vfs_path = %s, vfs_name = %s, vfs_modified = %s
                                            WHERE vfs_path = %s AND vfs_name = %s',
                                            $this->_params['table'],
                                            $this->_db->quote($newpath),
                                            $this->_db->quote($newname),
                                            $this->_db->quote(time()),
                                            $this->_db->quote($oldpath),
                                            $this->_db->quote($oldname)));

        if ($this->_db->affectedRows() == 0) {
            return PEAR::raiseError(_("Unable to rename VFS file."));
        }

        if (is_a($this->_recursiveSQLRename($oldpath, $oldname, $newpath, $newname), 'PEAR_Error')) {
            $result = $this->_db->query(sprintf('UPDATE %s SET vfs_path = %s, vfs_name = %s
                                                WHERE vfs_path = %s AND vfs_name = %s',
                                                $this->_params['table'],
                                                $this->_db->quote($oldpath),
                                                $this->_db->quote($oldname),
                                                $this->_db->quote($newpath),
                                                $this->_db->quote($newname)));
            return PEAR::raiseError(_("Unable to rename VFS directory."));
        }

        if (!@rename($this->_getNativePath($oldpath, $oldname), $this->_getNativePath($newpath, $newname))) {
            $result = $this->_db->query(sprintf('UPDATE %s SET vfs_path = %s, vfs_name = %s
                                                WHERE vfs_path = %s AND vfs_name = %s',
                                                $this->_params['table'],
                                                $this->_db->quote($oldpath),
                                                $this->_db->quote($oldname),
                                                $this->_db->quote($newpath),
                                                $this->_db->quote($newname)));
            return PEAR::raiseError(_("Unable to rename VFS file."));
        }

        return true;
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
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function deleteFolder($path, $name, $recursive = false)
    {
        $conn = $this->_connect();
        if (is_a($conn, 'PEAR_Error')) {
            return $conn;
        }

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

        $result = $this->_db->query(sprintf('DELETE FROM %s WHERE vfs_type = %s AND vfs_path = %s AND vfs_name = %s',
                                            $this->_params['table'],
                                            $this->_db->quote(VFS_FOLDER),
                                            $this->_db->quote($path),
                                            $this->_db->quote($name)));

        if ($this->_db->affectedRows() == 0 || is_a($result, 'PEAR_Error')) {
            return PEAR::raiseError(_("Unable to delete VFS directory."));
        }

        if (is_a($this->_recursiveSQLDelete($path, $name), 'PEAR_Error')) {
            return PEAR::raiseError(_("Unable to delete VFS directory recursively."));
        }

        if (is_a($this->_recursiveLFSDelete($path, $name), 'PEAR_Error')) {
            return PEAR::raiseError(_("Unable to delete VFS directory recursively."));
        }

        return $result;
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
        $conn = $this->_connect();
        if (is_a($conn, 'PEAR_Error')) {
            return $conn;
        }

        $result = $this->_db->query(sprintf('DELETE FROM %s WHERE vfs_type = %s AND vfs_path = %s AND vfs_name = %s',
                                            $this->_params['table'],
                                            $this->_db->quote(VFS_FILE),
                                            $this->_db->quote($path),
                                            $this->_db->quote($name)));

        if ($this->_db->affectedRows() == 0) {
            return PEAR::raiseError(_("Unable to delete VFS file."));
        }

        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (!@unlink($this->_getNativePath($path, $name))) {
            return PEAR::raiseError(_("Unable to delete VFS file."));
        }
    }

    /**
     * Return a list of the contents of a folder.
     *
     * @access public
     *
     * @param string $path                The directory path.
     * @param optional mixed $filter      String/hash of items to filter based
     *                                    on filename.
     * @param optional boolean $dotfiles  Show dotfiles?
     * @param optional boolean $dironly   Show directories only?
     *
     * @return mixed  File list on success or false on failure.
     */
    function listFolder($path, $filter = null, $dotfiles = true,
                        $dironly = false)
    {
        $conn = $this->_connect();
        if (is_a($conn, 'PEAR_Error')) {
            return $conn;
        }

        $files = array();
        $fileList = array();

        $fileList = $this->_db->getAll(sprintf('SELECT vfs_name, vfs_type, vfs_modified, vfs_owner FROM %s
                                               WHERE vfs_path = %s',
                                               $this->_params['table'],
                                               $this->_db->quote($path)));
        if (is_a($fileList, 'PEAR_Error')) {
            return $fileList;
        }

        foreach ($fileList as $line) {
            // Filter out dotfiles if they aren't wanted.
            if (!$dotfiles && substr($line[0], 0, 1) == '.') {
                continue;
            }

            $file['name'] = $line[0];

            if ($line[1] == VFS_FILE) {
                $name = explode('.', $line[0]);

                if (count($name) == 1) {
                    $file['type'] = '**none';
                } else {
                    $file['type'] = VFS::strtolower($name[count($name) - 1]);
                }

                $file['size'] = filesize($this->_getNativePath($path, $line[0]));
            } elseif ($line[1] == VFS_FOLDER) {
                $file['type'] = '**dir';
                $file['size'] = -1;
            }

            $file['date'] = $line[2];
            $file['owner'] = $line[3];
            $file['perms'] = '-';
            $file['group'] = '-';

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
     * @param optional mixed $filter        String/hash of items to filter
     *                                      based on folderlist.
     * @param optional boolean $dotfolders  Include dotfolders?
     *
     * @return mixed  Folder list on success or a PEAR_Error object on failure.
     */
    function listFolders($path = '', $filter = null, $dotfolders = true)
    {
        $sql = sprintf('SELECT vfs_name, vfs_path FROM %s WHERE vfs_path = %s AND vfs_type = %s',
                       $this->_params['table'],
                       $path,
                       VFS_FOLDER);

        $folderList = $this->_db->getAll($sql);
        if (is_a($folderList, 'PEAR_Error')) {
            return $folderList;
        }

        $folders = array();
        foreach ($folderList as $line) {
            $folder['val'] = $this->_getSQLNativePath($line[1], $line[0]);
            $folder['abbrev'] = '';
            $folder['label'] = '';

            $count = substr_count($folder['val'], '/');

            $x = 0;
            while ($x < $count) {
                $folder['abbrev'] .= '    ';
                $folder['label'] .= '    ';
                $x++;
            }

            $folder['abbrev'] .= $line[0];
            $folder['label'] .= $line[0];

            $strlen = VFS::strlen($folder['label']);
            if ($strlen > 26) {
                $folder['abbrev'] = substr($folder['label'], 0, ($count * 4));
                $length = (29 - ($count * 4)) / 2;
                $folder['abbrev'] .= substr($folder['label'], ($count * 4), $length);
                $folder['abbrev'] .= '...';
                $folder['abbrev'] .= substr($folder['label'], -1 * $length, $length);
            }

            $found = false;
            foreach ($filter as $fltr) {
                if ($folder['val'] == $fltr) {
                    $found = true;
                }
            }

            if (!$found) {
                $folders[$folder['val']] = $folder;
            }
        }

        ksort($folders);
        return $folders;
    }

    /**
     * Recursively copies the contents of a folder to a destination.
     *
     * @access private
     *
     * @param string $path  The path to store the directory in.
     * @param string $name  The name of the directory.
     * @param string $dest  The destination of the directory.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function _recursiveCopy($path, $name, $dest)
    {
        $result = $this->createFolder($dest, $name);

        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $file_list = $this->listFolder($this->_getSQLNativePath($path, $name));

        foreach ($file_list as $file) {
            $result = $this->copy($this->_getSQLNativePath($path, $name), $file['name'], $this->_getSQLNativePath($dest, $name));

            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
        return true;
     }

    /**
     * Store a files information within the database.
     *
     * @access private
     *
     * @param string $path                  The path to store the file in.
     * @param string $name                  The filename to use.
     * @param optional boolean $autocreate  Automatically create directories?
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function _writeSQLData($path, $name, $autocreate = false)
    {
        $conn = $this->_connect();
        if (is_a($conn, 'PEAR_Error')) {
            return $conn;
        }

        $id = $this->_db->nextId($this->_params['table']);

        $query = sprintf('INSERT INTO %s (vfs_id, vfs_type, vfs_path, vfs_name, vfs_modified,' .
                         ' vfs_owner) VALUES (%s, %s, %s, %s, %s, %s)',
                         $this->_params['table'],
                         $this->_db->quote($id),
                         $this->_db->quote(VFS_FILE),
                         $this->_db->quote($path),
                         $this->_db->quote($name),
                         $this->_db->quote(time()),
                         $this->_db->quote($this->_params['user']));

        return $this->_db->query($query);
    }

    /**
     * Renames all child paths.
     *
     * @access private
     *
     * @param string $oldpath  The old path of the folder to rename.
     * @param string $oldname  The old name.
     * @param string $newpath  The new path of the folder to rename.
     * @param string $newname  The new name.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function _recursiveSQLRename($oldpath, $oldname, $newpath, $newname)
    {
        $folderList = $this->_db->getCol(sprintf('SELECT vfs_name FROM %s WHERE vfs_type = %s AND vfs_path = %s',
                                                 $this->_params['table'],
                                                 $this->_db->quote(VFS_FOLDER),
                                                 $this->_db->quote($this->_getSQLNativePath($oldpath, $oldname))));

        foreach ($folderList as $folder) {
            $this->_recursiveSQLRename($this->_getSQLNativePath($oldpath, $oldname), $folder, $this->_getSQLNativePath($newpath, $newname), $folder);
        }

        $result = $this->_db->query(sprintf('UPDATE %s SET vfs_path = %s WHERE vfs_path = %s',
                                            $this->_params['table'],
                                            $this->_db->quote($this->_getSQLNativePath($newpath, $newname)),
                                            $this->_db->quote($this->_getSQLNativePath($oldpath, $oldname))));

        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
    }

    /**
     * Delete a folders contents from the VFS in the SQL database,
     * recursively.
     *
     * @access private
     *
     * @param string $path  The path of the folder.
     * @param string $name  The foldername to use.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function _recursiveSQLDelete($path, $name)
    {
        $result = $this->_db->query(sprintf('DELETE FROM %s WHERE vfs_type = %s AND vfs_path = %s',
                                            $this->_params['table'],
                                            $this->_db->quote(VFS_FILE),
                                            $this->_db->quote($this->_getSQLNativePath($path, $name))));
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $folderList = $this->_db->getCol(sprintf('SELECT vfs_name FROM %s WHERE vfs_type = %s AND vfs_path = %s',
                                                 $this->_params['table'],
                                                 $this->_db->quote(VFS_FOLDER),
                                                 $this->_db->quote($this->_getSQLNativePath($path, $name))));

        foreach ($folderList as $folder) {
            $this->_recursiveSQLDelete($this->_getSQLNativePath($path, $name), $folder);
        }

        $result = $this->_db->query(sprintf('DELETE FROM %s WHERE vfs_type = %s AND vfs_name = %s AND vfs_path = %s',
                                            $this->_params['table'],
                                            $this->_db->quote(VFS_FOLDER),
                                            $this->_db->quote($name),
                                            $this->_db->quote($path)));

        return $result;
    }

    /**
     * Delete a folders contents from the VFS, recursively.
     *
     * @access private
     *
     * @param string $path  The path of the folder.
     * @param string $name  The foldername to use.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function _recursiveLFSDelete($path, $name)
    {
        $dir = $this->_getNativePath($path, $name);
        $dh = @opendir($dir);

        while (false !== ($file = readdir($dh))) {
            if ($file != '.' && $file != '..') {
                if (is_dir($dir . '/' . $file)) {
                    $this->_recursiveLFSDelete(empty($path) ? $name : $path . '/' . $name, $file);
                } else {
                    @unlink($dir . '/' . $file);
                }
            }
        }
        @closedir($dh);

        return rmdir($dir);
    }

    /**
     * Attempts to open a persistent connection to the SQL server.
     *
     * @access private
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function _connect()
    {
        if ($this->_db === false) {
            if (!is_array($this->_params)) {
                return PEAR::raiseError(_("No configuration information specified for SQL-File VFS."));
            }

            $required = array('phptype', 'hostspec', 'username', 'password', 'database', 'vfsroot');
            foreach ($required as $val) {
                if (!isset($this->_params[$val])) {
                    return PEAR::raiseError(sprintf(_("Required '%s' not specified in VFS configuration."), $val));
                }
            }

            if (!isset($this->_params['table'])) {
                $this->_params['table'] = 'horde_vfs';
            }

            /* Connect to the SQL server using the supplied parameters. */
            require_once 'DB.php';
            $this->_db = &DB::connect($this->_params,
                                      array('persistent' => !empty($this->_params['persistent'])));
            if (DB::isError($this->_db)) {
                $error = $this->_db;
                $this->_db = false;
                return $error;
            }

            /* Enable the "portability" option. */
            $this->_db->setOption('optimize', 'portability');
        }

        return true;
    }

    /**
     * Disconnect from the SQL server and clean up the connection.
     *
     * @access private
     */
    function _disconnect()
    {
        if ($this->_db) {
            $this->_db->disconnect();
            $this->_db = false;
        }
    }

    /**
     * Return a full filename on the native filesystem, from a VFS
     * path and name.
     *
     * @access private
     *
     * @param string $path  The VFS file path.
     * @param string $name  The VFS filename.
     *
     * @return string  The full native filename.
     */
    function _getNativePath($path, $name)
    {
        if (!empty($name)) {
            $name = '/' . $name;
        }
        if (isset($path)) {
            if (isset($this->_params['home']) &&
                preg_match('|^~/?(.*)$|', $path, $matches)) {
                $path = $this->_params['home']  . '/' . $matches[1];
            }

            return $this->_params['vfsroot'] . '/' . $path . $name;
        } else {
            return $this->_params['vfsroot'] . $name;
        }
    }

    /**
     * Return a full SQL filename on the native filesystem, from a VFS
     * path and name.
     *
     * @access private
     *
     * @param string $path  The VFS file path.
     * @param string $name  The VFS filename.
     *
     * @return string  The full native filename.
     */
    function _getSQLNativePath($path, $name)
    {
        if (empty($path)) {
            return $name;
        }

        return $path . '/' . $name;
    }

}
