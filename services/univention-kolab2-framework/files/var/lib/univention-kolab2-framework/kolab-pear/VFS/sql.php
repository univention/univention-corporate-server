<?php

/** @constant integer VFS_FILE  File value for vfs_type column. */
define('VFS_FILE', 1);

/** @constant integer VFS_FOLDER  Folder value for vfs_type column. */
define('VFS_FOLDER', 2);

/**
 * VFS implementation for PHP's PEAR database abstraction layer.
 *
 * <pre>
 * Required values for $params:
 *      'phptype'       The database type (ie. 'pgsql', 'mysql, etc.).
 *      'hostspec'      The hostname of the database server.
 *      'protocol'      The communication protocol ('tcp', 'unix', etc.).
 *      'username'      The username with which to connect to the database.
 *      'password'      The password associated with 'username'.
 *      'database'      The name of the database.
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
 * Database specific notes:
 *
 * MSSQL:
 * <pre>
 * - The vfs_data field must be of type IMAGE.
 * - You need the following php.ini settings:
 *    ; Valid range 0 - 2147483647. Default = 4096.
 *    mssql.textlimit = 0 ; zero to pass through
 *
 *    ; Valid range 0 - 2147483647. Default = 4096.
 *    mssql.textsize = 0 ; zero to pass through
 * </pre>
 *
 * $Horde: framework/VFS/VFS/sql.php,v 1.79 2004/05/25 14:39:19 jan Exp $
 *
 * Copyright 2002-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.2
 * @package VFS
 */
class VFS_sql extends VFS {

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

        return $this->_readBlob($this->_params['table'], 'vfs_data',
                                array('vfs_path' => $path,
                                      'vfs_name' => $name));
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
        $conn = $this->_connect();
        if (is_a($conn, 'PEAR_Error')) {
            return $conn;
        }

        /* Check to see if the data already exists. */
        $sql = sprintf('SELECT vfs_id FROM %s WHERE vfs_path %s AND vfs_name = %s',
                       $this->_params['table'],
                       (empty($path) && $this->_db->dbsyntax == 'oci8') ? ' IS NULL' : ' = ' . $this->_db->quote($path),
                       $this->_db->quote($name));
        $id = $this->_db->getOne($sql);

        if (is_a($id, 'PEAR_Error')) {
            return $id;
        }

        if (!is_null($id)) {
            return $this->_updateBlob($this->_params['table'], 'vfs_data',
                                      $data, array('vfs_id' => $id),
                                      array('vfs_modified' => time()));
        } else {
            /* Check to see if the folder already exists. */
            $dirs = explode('/', $path);
            $path_name = array_pop($dirs);
            $parent = implode('/', $dirs);
            if (!$this->isFolder($parent, $path_name)) {
                if (!$autocreate) {
                    return PEAR::raiseError(sprintf(_("Folder %s does not exist"), $path), 'horde.error');
                } else {
                    $result = $this->autocreatePath($path);
                    if (is_a($result, 'PEAR_Error')) {
                        return $result;
                    }
                }
            }

            $id = $this->_db->nextId($this->_params['table']);
            if (is_a($id, 'PEAR_Error')) {
                return $id;
            }
            return $this->_insertBlob($this->_params['table'], 'vfs_data',
                                      $data, array('vfs_id' => $id,
                                                   'vfs_type' => VFS_FILE,
                                                   'vfs_path' => $path,
                                                   'vfs_name' => $name,
                                                   'vfs_modified' => time(),
                                                   'vfs_owner' => $this->_params['user']));
        }
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

        $sql = sprintf('DELETE FROM %s WHERE vfs_type = %s AND vfs_path %s AND vfs_name = %s',
                       $this->_params['table'],
                       $this->_db->quote(VFS_FILE),
                       (empty($path) && $this->_db->dbsyntax == 'oci8') ? ' IS NULL' : ' = ' . $this->_db->quote($path),
                       $this->_db->quote($name));
        $result = $this->_db->query($sql);

        if ($this->_db->affectedRows() == 0) {
            return PEAR::raiseError(_("Unable to delete VFS file."));
        }

        return $result;
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

        $sql = sprintf('UPDATE %s SET vfs_path = %s, vfs_name = %s, vfs_modified = %s WHERE vfs_path = %s AND vfs_name = %s',
                       $this->_params['table'],
                       $this->_db->quote($newpath),
                       $this->_db->quote($newname),
                       $this->_db->quote(time()),
                       $this->_db->quote($oldpath),
                       $this->_db->quote($oldname));
        $result = $this->_db->query($sql);

        if ($this->_db->affectedRows() == 0) {
            return PEAR::raiseError(_("Unable to rename VFS file."));
        }

        $rename = $this->_recursiveRename($oldpath, $oldname, $newpath, $newname);
        if (is_a($rename, 'PEAR_Error')) {
            return PEAR::raiseError(sprintf(_("Unable to rename VFS directory: %s."), $rename->getMessage()));
        }

        return $result;
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
        if (is_a($id, 'PEAR_Error')) {
            return $id;
        }

        $sql = sprintf('INSERT INTO %s (vfs_id, vfs_type, vfs_path, vfs_name, vfs_modified, vfs_owner) VALUES (%s, %s, %s, %s, %s, %s)',
                       $this->_params['table'],
                       $this->_db->quote($id),
                       $this->_db->quote(VFS_FOLDER),
                       $this->_db->quote($path),
                       $this->_db->quote($name),
                       $this->_db->quote(time()),
                       $this->_db->quote($this->_params['user']));
        return $this->_db->query($sql);
    }

    /**
     * Delete a folder from the VFS.
     *
     * @access public
     *
     * @param string $path                 The path of the folder.
     * @param string $name                 The folder name to use.
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

        $folderPath = $this->_getNativePath($path, $name);

        /* Check if not recursive and fail if directory not empty */
        if (!$recursive) {
            $folderList = $this->listFolder($folderPath, null, true);
            if (is_a($folderList, 'PEAR_Error')) {
                return $folderList;
            } elseif (!empty($folderList)) {
                return PEAR::raiseError(sprintf(_("Unable to delete %s, the directory is not empty"),
                                                $path . '/' . $name));
            }
        }

        /* First delete everything below the folder, so if error we get
         * no orphans */
        $sql = sprintf('DELETE FROM %s WHERE vfs_path %s',
                       $this->_params['table'],
                       (empty($folderPath) && $this->_db->dbsyntax == 'oci8') ? ' IS NULL' : ' LIKE ' . $this->_db->quote($this->_getNativePath($folderPath, '%')));
        $deleteContents = $this->_db->query($sql);
        if (is_a($deleteContents, 'PEAR_Error')) {
            return PEAR::raiseError(sprintf(_("Unable to delete VFS recursively: %s."), $deleteContents->getMessage()));
        }

        /* Now delete everything inside the folder. */
        $sql = sprintf('DELETE FROM %s WHERE vfs_path %s',
                       $this->_params['table'],
                       (empty($path) && $this->_db->dbsyntax == 'oci8') ? ' IS NULL' : ' = ' . $this->_db->quote($folderPath));
        $delete = $this->_db->query($sql);
        if (is_a($delete, 'PEAR_Error')) {
            return PEAR::raiseError(sprintf(_("Unable to delete VFS directory: %s."), $delete->getMessage()));
        }

        /* All ok now delete the actual folder */
        $sql = sprintf('DELETE FROM %s WHERE vfs_path %s AND vfs_name = %s',
                       $this->_params['table'],
                       (empty($path) && $this->_db->dbsyntax == 'oci8') ? ' IS NULL' : ' = ' . $this->_db->quote($path),
                       $this->_db->quote($name));
        $delete = $this->_db->query($sql);
        if (is_a($delete, 'PEAR_Error')) {
            return PEAR::raiseError(sprintf(_("Unable to delete VFS directory: %s."), $delete->getMessage()));
        }

        return $delete;
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

        // Fix for an ODD Oracle quirk.
        if (empty($path) && $this->_db->dbsyntax == 'oci8') {
            $where = 'vfs_path IS NULL';
        } else {
            $where = 'vfs_path = ' . $this->_db->quote($path);
        }

        $sql = sprintf('SELECT vfs_name, vfs_type, vfs_data, vfs_modified, vfs_owner FROM %s WHERE %s',
                            $this->_params['table'],
                            $where);
        $fileList = $this->_db->getAll($sql);
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

                $file['size'] = VFS::strlen($line[2]);
            } elseif ($line[1] == VFS_FOLDER) {
                $file['type'] = '**dir';
                $file['size'] = -1;
            }

            $file['date'] = $line[3];
            $file['owner'] = $line[4];
            $file['perms'] = '-';
            $file['group'] = '-';

            // filtering
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
     * @return mixed  Folder list on success or PEAR_Error object on failure.
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
     * Renames all child paths.
     *
     * @access private
     *
     * @param string $path  The path of the folder to rename.
     * @param string $name  The foldername to use.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function _recursiveRename($oldpath, $oldname, $newpath, $newname)
    {
        $sql = sprintf('SELECT vfs_name FROM %s WHERE vfs_type = %s AND vfs_path = %s',
                       $this->_params['table'],
                       $this->_db->quote(VFS_FOLDER),
                       $this->_db->quote($this->_getNativePath($oldpath, $oldname)));
        $folderList = $this->_db->getCol($sql);

        foreach ($folderList as $folder) {
            $this->_recursiveRename($this->_getNativePath($oldpath, $oldname), $folder, $this->_getNativePath($newpath, $newname), $folder);
        }

        $sql = sprintf('UPDATE %s SET vfs_path = %s WHERE vfs_path = %s',
                       $this->_params['table'],
                       $this->_db->quote($this->_getNativePath($newpath, $newname)),
                       $this->_db->quote($this->_getNativePath($oldpath, $oldname)));
        $result = $this->_db->query($sql);

        return $result;
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
        if (empty($path)) {
            return $name;
        }

        if (!empty($path)) {
            if (isset($this->_params['home']) &&
                preg_match('|^~/?(.*)$|', $path, $matches)) {
                $path = $this->_params['home'] . '/' . $matches[1];
            }
        }

        return $path . '/' . $name;
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
                return PEAR::raiseError(_("No configuration information specified for SQL VFS."));
            }

            $required = array('phptype', 'hostspec', 'username', 'password', 'database');
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
            if (is_a($this->_db, 'PEAR_Error')) {
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
     * TODO
     *
     * @access private
     *
     * @param string $table     TODO
     * @param string $field     TODO
     * @param string $criteria  TODO
     *
     * @return mixed  TODO
     */
    function _readBlob($table, $field, $criteria)
    {
        if (!count($criteria)) {
            return PEAR::raiseError('You must specify the fetch criteria');
        }

        $where = '';

        switch ($this->_db->dbsyntax) {
        case 'oci8':
            foreach ($criteria as $key => $value) {
                if (!empty($where)) {
                    $where .= ' AND ';
                }
                if (empty($value)) {
                    $where .= $key . ' IS NULL';
                } else {
                    $where .= $key . ' = ' . $this->_db->quote($value);
                }
            }

            $statement = OCIParse($this->_db->connection,
                                  sprintf('SELECT %s FROM %s WHERE %s',
                                          $field, $table, $where));
            OCIExecute($statement);
            if (OCIFetchInto($statement, $lob)) {
                $result = $lob[0]->load();
                if (is_null($result)) {
                    $result = PEAR::raiseError('Unable to load SQL data.');
                }
            } else {
                $result = PEAR::raiseError('Unable to load SQL data.');
            }
            OCIFreeStatement($statement);
            break;

        default:
            foreach ($criteria as $key => $value) {
                if (!empty($where)) {
                    $where .= ' AND ';
                }
                $where .= $key . ' = ' . $this->_db->quote($value);
            }

            $sql = sprintf('SELECT %s FROM %s WHERE %s',
                           $field, $table, $where);
            $result = $this->_db->getOne($sql);

            if (is_null($result)) {
                $result = PEAR::raiseError('Unable to load SQL data.');
            } else {
                switch ($this->_db->dbsyntax) {
                case 'pgsql':
                    $result = pack('H' . strlen($result), $result);
                    break;
                }
            }
        }

        return $result;
    }

    /**
     * TODO
     *
     * @access private
     *
     * @param string $table       TODO
     * @param string $field       TODO
     * @param string $data        TODO
     * @param string $attributes  TODO
     *
     * @return mixed  TODO
     */
    function _insertBlob($table, $field, $data, $attributes)
    {
        $fields = array();
        $values = array();

        switch ($this->_db->dbsyntax) {
        case 'oci8':
            foreach ($attributes as $key => $value) {
                $fields[] = $key;
                $values[] = $this->_db->quote($value);
            }

            $statement = OCIParse($this->_db->connection,
                                  sprintf('INSERT INTO %s (%s, %s)' .
                                          ' VALUES (%s, EMPTY_BLOB()) RETURNING %s INTO :blob',
                                          $table,
                                          implode(', ', $fields),
                                          $field,
                                          implode(', ', $values),
                                          $field));

            $lob = OCINewDescriptor($this->_db->connection);
            OCIBindByName($statement, ':blob', $lob, -1, SQLT_BLOB);
            OCIExecute($statement, OCI_DEFAULT);
            $lob->save($data);
            $result = OCICommit($this->_db->connection);
            $lob->free();
            OCIFreeStatement($statement);
            return $result ? true : PEAR::raiseError('Unknown Error');

        default:
            foreach ($attributes as $key => $value) {
                $fields[] = $key;
                $values[] = $value;
            }

            $query = sprintf('INSERT INTO %s (%s, %s) VALUES (%s)',
                             $table,
                             implode(', ', $fields),
                             $field,
                             '?' . str_repeat(', ?', count($values)));
            break;
        }

        switch ($this->_db->dbsyntax) {
        case 'mssql':
        case 'pgsql':
            $values[] = bin2hex($data);
            break;

        default:
            $values[] = $data;
        }

        /* Execute the query. */
        $stmt = $this->_db->prepare($query);
        return $this->_db->execute($stmt, $values);
    }

    /**
     * TODO
     *
     * @access private
     *
     * @param string $table      TODO
     * @param string $field      TODO
     * @param string $data       TODO
     * @param string $where      TODO
     * @param array $alsoupdate  TODO
     *
     * @return mixed  TODO
     */
    function _updateBlob($table, $field, $data, $where, $alsoupdate)
    {
        $fields = array();
        $values = array();

        switch ($this->_db->dbsyntax) {
        case 'oci8':
            $wherestring = '';
            foreach ($where as $key => $value) {
                if (!empty($wherestring)) {
                    $wherestring .= ' AND ';
                }
                $wherestring .= $key . ' = ' . $this->_db->quote($value);
            }

            $statement = OCIParse($this->_db->connection,
                                  sprintf('SELECT %s FROM %s FOR UPDATE WHERE %s',
                                          $field,
                                          $table,
                                          $wherestring));

            OCIExecute($statement, OCI_DEFAULT);
            OCIFetchInto($statement, $lob);
            $lob[0]->save($data);
            $result = OCICommit($this->_db->connection);
            $lob[0]->free();
            OCIFreeStatement($statement);
            return $result ? true : PEAR::raiseError('Unknown Error');

        default:
            $updatestring = '';
            $values = array();
            foreach ($alsoupdate as $key => $value) {
                $updatestring .= $key . ' = ?, ';
                $values[] = $value;
            }
            $updatestring .= $field . ' = ?';
            switch ($this->_db->dbsyntax) {
            case 'mssql':
            case 'pgsql':
                $values[] = bin2hex($data);
                break;

            default:
                $values[] = $data;
            }

            $wherestring = '';
            foreach ($where as $key => $value) {
                if (!empty($wherestring)) {
                    $wherestring .= ' AND ';
                }
                $wherestring .= $key . ' = ?';
                $values[] = $value;
            }

            $query = sprintf('UPDATE %s SET %s WHERE %s',
                             $table,
                             $updatestring,
                             $wherestring);
            break;
        }

        /* Execute the query. */
        $stmt = $this->_db->prepare($query);
        return $this->_db->execute($stmt, $values);
    }

}
