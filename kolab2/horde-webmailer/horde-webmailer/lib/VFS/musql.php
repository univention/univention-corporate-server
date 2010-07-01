<?php

require_once dirname(__FILE__) . '/sql.php';

/**
 * Permission for read access.
 */
define('VFS_FLAG_READ', 1);

/**
 * Permission for read access.
 */
define('VFS_FLAG_WRITE', 2);

/**
 * Multi User VFS implementation for PHP's PEAR database
 * abstraction layer.
 *
 * Required values for $params:<pre>
 *      'phptype'       The database type (ie. 'pgsql', 'mysql', etc.).</pre>
 *
 * Optional values:<pre>
 *      'table'         The name of the vfs table in 'database'. Defaults to
 *                      'horde_muvfs'.</pre>
 *
 * Required by some database implementations:<pre>
 *      'hostspec'      The hostname of the database server.
 *      'protocol'      The communication protocol ('tcp', 'unix', etc.).
 *      'database'      The name of the database.
 *      'username'      The username with which to connect to the database.
 *      'password'      The password associated with 'username'.
 *      'options'       Additional options to pass to the database.
 *      'tty'           The TTY on which to connect to the database.
 *      'port'          The port on which to connect to the database.</pre>
 *
 * Known Issues:
 * Delete is not recusive, so files and folders that used to be in a folder
 * that gets deleted live forever in the database, or re-appear when the folder
 * is recreated.
 * Rename has the same issue, so files are lost if a folder is renamed.
 *
 * The table structure for the VFS can be found in
 * data/muvfs.sql.
 *
 * Database specific notes:
 *
 * MSSQL:
 * - The vfs_data field must be of type IMAGE.
 * - You need the following php.ini settings:
 * <code>
 *    ; Valid range 0 - 2147483647. Default = 4096.
 *    mssql.textlimit = 0 ; zero to pass through
 *
 *    ; Valid range 0 - 2147483647. Default = 4096.
 *    mssql.textsize = 0 ; zero to pass through
 * </code>
 *
 * $Horde: framework/VFS/lib/VFS/musql.php,v 1.1.2.4 2009-01-06 15:23:47 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @package VFS
 */
class VFS_musql extends VFS_sql {

    /**
     * List of permissions and if they can be changed in this VFS
     *
     * @var array
     */
    var $_permissions = array(
        'owner' => array('read' => false, 'write' => false, 'execute' => false),
        'group' => array('read' => false, 'write' => false, 'execute' => false),
        'all'   => array('read' => true,  'write' => true,  'execute' => false)
    );

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
        $conn = $this->_connect();
        if (PEAR::isError($conn)) {
            return $conn;
        }

        /* Make sure we have write access to this and all parent paths. */
        if ($path != '') {
            $paths = explode('/', $path);
            $path_name = array_pop($paths);
            if (!$this->isFolder(implode('/', $paths), $path_name)) {
                if (!$autocreate) {
                    return PEAR::raiseError(
                        sprintf(_("Folder \"%s\" does not exist"), $path),
                        'horde.error');
                } else {
                    $result = $this->autocreatePath($path);
                    if (is_a($result, 'PEAR_Error')) {
                        return $result;
                    }
                }
            }
            $paths[] = $path_name;
            $previous = '';

            foreach ($paths as $thispath) {
                $sql = sprintf('SELECT vfs_owner, vfs_perms FROM %s
                                WHERE vfs_path = ? AND vfs_name= ?',
                               $this->_params['table']);
                $this->log($sql, PEAR_LOG_DEBUG);
                $results = $this->_db->getAll($sql, array($previous, $thispath));
                if (is_a($results, 'PEAR_Error')) {
                    $this->log($results, PEAR_LOG_ERR);
                    return $results;
                }
                if (!is_array($results) || count($results) < 1) {
                    return PEAR::raiseError(_("Unable to create VFS file."));
                }

                $allowed = false;
                foreach ($results as $result) {
                    if ($result[0] == $this->_params['user'] ||
                        $result[1] & VFS_FLAG_WRITE) {
                        $allowed = true;
                        break;
                    }
                }

                if (!$allowed) {
                    return PEAR::raiseError(_("Access denied creating VFS file."));
                }

                $previous = $thispath;
            }
        }

        return parent::writeData($path, $name, $data, $autocreate);
    }

    /**
     * Deletes a file from the VFS.
     *
     * @param string $path  The path to store the file in.
     * @param string $name  The filename to use.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function deleteFile($path, $name)
    {
        $conn = $this->_connect();
        if (PEAR::isError($conn)) {
            return $conn;
        }

        $sql = sprintf('SELECT vfs_id, vfs_owner, vfs_perms FROM %s
                        WHERE vfs_path = ? AND vfs_name= ? AND vfs_type = ?',
                       $this->_params['table']);
        $this->log($sql, PEAR_LOG_DEBUG);
        $fileList = $this->_db->getAll($sql, array($path, $name, VFS_FILE));

        if (is_a($fileList, 'PEAR_Error')) {
            $this->log($fileList, PEAR_LOG_ERR);
            return $fileList;
        }
        if (!is_array($fileList) || count($fileList) < 1) {
            return PEAR::raiseError(_("Unable to delete VFS file."));
        }

        /* There may be one or more files with the same name but the user may
         * not have read access to them, so doesn't see them. So we have to
         * delete the one they have access to. */
        foreach ($fileList as $file) {
            if ($file[1] == $this->_params['user'] ||
                $file[2] & VFS_FLAG_WRITE) {
                $sql = sprintf('DELETE FROM %s WHERE vfs_id = ?',
                               $this->_params['table']);
                $this->log($sql, PEAR_LOG_DEBUG);
                $result = $this->_db->query($sql, array($file[0]));

                if (is_a($result, 'PEAR_Error')) {
                    $this->log($result, PEAR_LOG_ERR);
                    return $result;
                }
                if ($this->_db->affectedRows() == 0) {
                    return PEAR::raiseError(_("Unable to delete VFS file."));
                }
                return $result;
            }
        }

        // FIXME: 'Access Denied deleting file %s/%s'
        return PEAR::raiseError(_("Unable to delete VFS file."));
    }

    /**
     * Renames a file or folder in the VFS.
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
        if (PEAR::isError($conn)) {
            return $conn;
        }

        $sql = sprintf('SELECT vfs_id, vfs_owner, vfs_perms FROM %s
                        WHERE vfs_path = ? AND vfs_name= ?',
                       $this->_params['table']);
        $this->log($sql, PEAR_LOG_DEBUG);
        $fileList = $this->_db->getAll($sql, array($oldpath, $oldname));

        if (is_a($fileList, 'PEAR_Error')) {
            $this->log($fileList, PEAR_LOG_ERR);
            return $fileList;
        }
        if (!is_array($fileList) || count($fileList) < 1) {
            return PEAR::raiseError(_("Unable to rename VFS file."));
        }

        if (strpos($newpath, '/') === false) {
            $parent = '';
            $path = $newpath;
        } else {
            list($parent, $path) = explode('/', $newpath, 2);
        }
        if (!$this->isFolder($parent, $path)) {
            if (is_a($result = $this->autocreatePath($newpath), 'PEAR_Error')) {
                return $result;
            }
        }

        /* There may be one or more files with the same name but the user may
         * not have read access to them, so doesn't see them. So we have to
         * rename the one they have access to. */
        foreach ($fileList as $file) {
            if ($file[1] == $this->_params['user'] ||
                $file[2] & VFS_FLAG_WRITE) {
                $sql = sprintf('UPDATE %s SET vfs_path = ?, vfs_name = ?, vfs_modified = ?
                                WHERE vfs_id = ?',
                               $this->_params['table']);
                $this->log($sql, PEAR_LOG_DEBUG);
                $result = $this->_db->query(
                    $sql,
                    array($newpath, $newname, time(), $file[0]));
                if (is_a($result, 'PEAR_Error')) {
                    $this->log($result, PEAR_LOG_ERR);
                    return $result;
                }
                return $result;
            }
        }

        return PEAR::raiseError(sprintf(_("Unable to rename VFS file %s/%s."),
                                        $oldpath, $oldname));
    }

    /**
     * Creates a folder on the VFS.
     *
     * @param string $path  Holds the path of directory to create folder.
     * @param string $name  Holds the name of the new folder.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function createFolder($path, $name)
    {
        $conn = $this->_connect();
        if (PEAR::isError($conn)) {
            return $conn;
        }

        /* Make sure we have write access to this and all parent paths. */
        if (strlen($path)) {
            $paths = explode('/', $path);
            $previous = '';

            foreach ($paths as $thispath) {
                $sql = sprintf('SELECT vfs_owner, vfs_perms FROM %s
                                WHERE vfs_path = ? AND vfs_name= ?',
                               $this->_params['table']);
                $this->log($sql, PEAR_LOG_DEBUG);
                $results = $this->_db->getAll($sql, array($previous, $thispath));
                if (is_a($results, 'PEAR_Error')) {
                    $this->log($results, PEAR_LOG_ERR);
                    return $results;
                }
                if (!is_array($results) || count($results) < 1) {
                    return PEAR::raiseError(_("Unable to create VFS directory."));
                }

                $allowed = false;
                foreach ($results as $result) {
                    if ($result[0] == $this->_params['user'] ||
                        $result[1] & VFS_FLAG_WRITE) {
                        $allowed = true;
                        break;
                    }
                }

                if (!$allowed) {
                    return PEAR::raiseError(_("Access denied creating VFS directory."));
                }

                $previous = $thispath;
            }
        }

        $id = $this->_db->nextId($this->_params['table']);
        $sql = sprintf('INSERT INTO %s
                        (vfs_id, vfs_type, vfs_path, vfs_name, vfs_modified, vfs_owner, vfs_perms)
                        VALUES (?, ?, ?, ?, ?, ?, ?)',
                       $this->_params['table']);
        $this->log($sql, PEAR_LOG_DEBUG);
        $result = $this->_db->query(
            $sql,
            array($id, VFS_FOLDER, $path, $name, time(), $this->_params['user'], 0));
        var_dump($this->_db->last_query);
        if (is_a($result, 'PEAR_Error')) {
            $this->log($result, PEAR_LOG_ERR);
        }

        return $result;
    }

    /**
     * Deletes a folder from the VFS.
     *
     * @param string $path        The path to delete the folder from.
     * @param string $name        The foldername to use.
     * @param boolean $recursive  Force a recursive delete?
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function deleteFolder($path, $name, $recursive = false)
    {
        $conn = $this->_connect();
        if (PEAR::isError($conn)) {
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
                return PEAR::raiseError(
                    sprintf(_("Unable to delete %s, the directory is not empty"),
                            $path . '/' . $name));
            }
        }

        $sql = sprintf('SELECT vfs_id, vfs_owner, vfs_perms FROM %s
                        WHERE vfs_path = ? AND vfs_name= ? AND vfs_type = ?',
                       $this->_params['table']);
        $this->log($sql, PEAR_LOG_DEBUG);
        $fileList = $this->_db->getAll($sql, array($path, $name, VFS_FOLDER));

        if (is_a($fileList, 'PEAR_Error')) {
            $this->log($fileList, PEAR_LOG_ERR);
            return $fileList;
        }
        if (!is_array($fileList) || count($fileList) < 1) {
            return PEAR::raiseError(_("Unable to delete VFS directory."));
        }

        /* There may be one or more folders with the same name but as the user
         * may not have read access to them, they don't see them. So we have
         * to delete the one they have access to */
        foreach ($fileList as $file) {
            if ($file[1] == $this->_params['user'] ||
                $file[2] & VFS_FLAG_WRITE) {
                $sql = sprintf('DELETE FROM %s WHERE vfs_id = ?',
                               $this->_params['table']);
                $this->log($sql, PEAR_LOG_DEBUG);
                $result = $this->_db->query($sql, array($file[0]));

                if (is_a($result, 'PEAR_Error')) {
                    $this->log($result, PEAR_LOG_ERR);
                    return $result;
                }
                if ($this->_db->affectedRows() == 0) {
                    return PEAR::raiseError(_("Unable to delete VFS directory."));
                }

                return $result;
            }
        }

        // FIXME: 'Access Denied deleting folder %s/%s'
        return PEAR::raiseError(_("Unable to delete VFS directory."));
    }

    /**
     * Returns a list of the contents of a folder.
     *
     * @param string $path       The path of the directory.
     * @param mixed $filter      String/hash to filter file/dirname on.
     * @param boolean $dotfiles  Show dotfiles?
     * @param boolean $dironly   Show only directories?
     *
     * @return mixed  File list on success or false on failure.
     */
    function _listFolder($path, $filter = null, $dotfiles = true,
                        $dironly = false)
    {
        $conn = $this->_connect();
        if (is_a($conn, 'PEAR_Error')) {
            return $conn;
        }

        $length_op = $this->_getFileSizeOp();
        $sql = sprintf('SELECT vfs_name, vfs_type, vfs_modified, vfs_owner, vfs_perms, %s(vfs_data) FROM %s
                        WHERE vfs_path = ? AND (vfs_owner = ? OR vfs_perms \&\& ?)',
                       $length_op, $this->_params['table']);
        $this->log($sql, PEAR_LOG_DEBUG);
        $fileList = $this->_db->getAll(
            $sql,
            array($path, $this->_params['user'], VFS_FLAG_READ));
        if (is_a($fileList, 'PEAR_Error')) {
            $this->log($fileList, PEAR_LOG_ERR);
            return $fileList;
        }

        $files = array();
        foreach ($fileList as $line) {
            // Filter out dotfiles if they aren't wanted.
            if (!$dotfiles && substr($line[0], 0, 1) == '.') {
                continue;
            }

            $file['name'] = stripslashes($line[0]);

            if ($line[1] == VFS_FILE) {
                $name = explode('.', $line[0]);

                if (count($name) == 1) {
                    $file['type'] = '**none';
                } else {
                    $file['type'] = VFS::strtolower($name[count($name) - 1]);
                }

                $file['size'] = $line[5];
            } elseif ($line[1] == VFS_FOLDER) {
                $file['type'] = '**dir';
                $file['size'] = -1;
            }

            $file['date'] = $line[2];
            $file['owner'] = $line[3];

            $line[4] = intval($line[4]);
            $file['perms']  = ($line[1] == VFS_FOLDER) ? 'd' : '-';
            $file['perms'] .= 'rw-';
            $file['perms'] .= ($line[4] & VFS_FLAG_READ) ? 'r' : '-';
            $file['perms'] .= ($line[4] & VFS_FLAG_WRITE) ? 'w' : '-';
            $file['perms'] .= '-';
            $file['group'] = '';

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
     * Changes permissions for an Item on the VFS.
     *
     * @param string $path  Holds the path of directory of the Item.
     * @param string $name  Holds the name of the Item.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function changePermissions($path, $name, $permission)
    {
        $conn = $this->_connect();
        if (PEAR::isError($conn)) {
            return $conn;
        }

        $val = intval(substr($permission, -1));
        $perm = 0;
        $perm |= ($val & 4) ? VFS_FLAG_READ : 0;
        $perm |= ($val & 2) ? VFS_FLAG_WRITE : 0;

        $sql = sprintf('SELECT vfs_id, vfs_owner, vfs_perms FROM %s
                        WHERE vfs_path = ? AND vfs_name= ?',
                       $this->_params['table']);
        $this->log($sql, PEAR_LOG_DEBUG);
        $fileList = $this->_db->getAll($sql, array($path, $name));

        if (is_a($fileList, 'PEAR_Error')) {
            $this->log($fileList, PEAR_LOG_ERR);
            return $fileList;
        }
        if (!is_array($fileList) || count($fileList) < 1) {
            return PEAR::raiseError(_("Unable to rename VFS file."));
        }

        /* There may be one or more files with the same name but the user may
         * not have read access to them, so doesn't see them. So we have to
         * chmod the one they have access to. */
        foreach ($fileList as $file) {
            if ($file[1] == $this->_params['user'] ||
                $file[2] & VFS_FLAG_WRITE) {
                $sql = sprintf('UPDATE %s SET vfs_perms = ?
                                WHERE vfs_id = ?',
                               $this->_params['table']);
                $this->log($sql, PEAR_LOG_DEBUG);
                $result = $this->_db->query($sql, array($perm, $file[0]));
                return $result;
            }
        }

        return PEAR::raiseError(
            sprintf(_("Unable to change permission for VFS file %s/%s."),
                    $path, $name));
    }

}
