<?php

require_once dirname(__FILE__) . '/sql.php';

/** @constant integer VFS_FLAG_READ  Permission for read access. */
define('VFS_FLAG_READ', 1);

/** @constant integer VFS_FLAG_WRITE  Permission for read access. */
define('VFS_FLAG_WRITE', 2);

/**
 * Multi User VFS implementation for PHP's PEAR database
 * abstraction layer.
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
 *                      'horde_muvfs'.
 *
 * Required by some database implementations:
 *      'options'       Additional options to pass to the database.
 *      'tty'           The TTY on which to connect to the database.
 *      'port'          The port on which to connect to the database.
 * </pre>
 *
 * Known Issues:
 * Delete is not recusive, so file and folders that used to be in a folder that
 * gets deleted life forever in the database, or re-appear when the folder is
 * recreated.
 * Rename has the same issue, if files are lost if a folder is renamed.
 *
 * The table structure for the VFS can be found in
 * horde/scripts/db/muvfs.sql.
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
 * $Horde: framework/VFS/VFS/musql.php,v 1.29 2004/04/08 18:33:17 slusarz Exp $
 *
 * Copyright 2002-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.2
 * @package VFS
 */
class VFS_musql extends VFS_sql {

    /**
     * List of permissions and if they can be changed in this VFS
     *
     * @var array $_permissions
     */
    var $_permissions = array(
        'owner' => array('read' => false, 'write' => false, 'execute' => false),
        'group' => array('read' => false, 'write' => false, 'execute' => false),
        'all'   => array('read' => true,  'write' => true,  'execute' => false)
    );

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
        if (PEAR::isError($conn)) {
            return $conn;
        }

        /* Make sure we have write access to this and all parent
         * paths. */
        if ($path != '') {
            $paths = explode('/', $path);
            $path_name = array_pop($paths);
            if (!$this->isFolder(implode('/', $paths), $path_name)) {
                if (!$autocreate) {
                    return PEAR::raiseError(sprintf(_("Folder %s does not exist"), $path), 'horde.error');
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
                $results = $this->_db->getAll(sprintf('SELECT vfs_owner, vfs_perms FROM %s
                                                       WHERE vfs_path = %s AND vfs_name= %s',
                                                      $this->_params['table'],
                                                      $this->_db->quote($previous),
                                                      $this->_db->quote($thispath)));
                if (!is_array($results) || count($results) < 1) {
                    return PEAR::raiseError(_("Unable to create VFS file."));
                }

                $allowed = false;
                foreach ($results as $result) {
                    if ($result[0] == $this->_params['user'] || $result[1] & VFS_FLAG_WRITE) {
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
        if (PEAR::isError($conn)) {
            return $conn;
        }

        $fileList = $this->_db->getAll(sprintf('SELECT vfs_id, vfs_owner, vfs_perms FROM %s
                                                WHERE vfs_path = %s AND vfs_name= %s AND vfs_type = %s',
                                               $this->_params['table'],
                                               $this->_db->quote($path),
                                               $this->_db->quote($name),
                                               $this->_db->quote(VFS_FILE)));

        if (!is_array($fileList) || count($fileList) < 1) {
            return PEAR::raiseError(_("Unable to delete VFS file."));
        }

        /* There may be one or more files with the same name but the
           user may not have read access to them, so doesn't see
           them. So we have to delete the one they have access to. */
        foreach ($fileList as $file) {
            if ($file[1] == $this->_params['user'] || $file[2] & VFS_FLAG_WRITE) {
                $result = $this->_db->query(sprintf('DELETE FROM %s WHERE vfs_id = %s',
                                                    $this->_params['table'],
                                                    $this->_db->quote($file[0])));

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
        if (PEAR::isError($conn)) {
            return $conn;
        }

        $fileList = $this->_db->getAll(sprintf('SELECT vfs_id, vfs_owner, vfs_perms FROM %s
                                                       WHERE vfs_path = %s AND vfs_name= %s',
                                                       $this->_params['table'],
                                                       $this->_db->quote($oldpath),
                                                       $this->_db->quote($oldname)));

        if (!is_array($fileList) || count($fileList) < 1) {
            return PEAR::raiseError(_("Unable to rename VFS file."));
        }

        /* There may be one or more files with the same name but the user may
	 * not have read access to them, so doesn't see them. So we have to
	 * rename the one they have access to. */
        foreach ($fileList as $file) {
            if ($file[1] == $this->_params['user'] || $file[2] & VFS_FLAG_WRITE) {
                $result = $this->_db->query(sprintf('UPDATE %s SET vfs_path = %s, vfs_name = %s, vfs_modified = %s
                                                    WHERE vfs_id = %s',
                                                    $this->_params['table'],
                                                    $this->_db->quote($newpath),
                                                    $this->_db->quote($newname),
                                                    $this->_db->quote(time()),
                                                    $this->_db->quote($file[0])));
                return $result;
            }
        }

        return PEAR::raiseError(sprintf(_("Unable to rename VFS file %s/%s."), $oldpath, $oldname));
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
        if (PEAR::isError($conn)) {
            return $conn;
        }

        /* make sure we have write access to this and all parent paths */
        if ($path != "") {
            $paths = explode('/', $path);
            $previous = '';

            foreach ($paths as $thispath) {
                $results = $this->_db->getAll(sprintf('SELECT vfs_owner, vfs_perms FROM %s
                                                               WHERE vfs_path = %s AND vfs_name= %s',
                                                               $this->_params['table'],
                                                               $this->_db->quote($previous),
                                                               $this->_db->quote($thispath)));
                if (!is_array($results) || count($results) < 1) {
                    return PEAR::raiseError(_("Unable to create VFS directory."));
                }

                $allowed = false;
                foreach ($results as $result) {
                    if ($result[0] == $this->_params['user'] || $result[1] & VFS_FLAG_WRITE) {
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
        return $this->_db->query(sprintf('INSERT INTO %s (vfs_id, vfs_type, vfs_path, vfs_name, vfs_modified, vfs_owner, vfs_perms)
                                         VALUES (%s, %s, %s, %s, %s, %s, %s)',
                                         $this->_params['table'],
                                         $this->_db->quote($id),
                                         $this->_db->quote(VFS_FOLDER),
                                         $this->_db->quote($path),
                                         $this->_db->quote($name),
                                         $this->_db->quote(time()),
                                         $this->_db->quote($this->_params['user']),
                                         $this->_db->quote(0)
                                         ));
    }

    /**
     * Delete a file from the VFS.
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
                return PEAR::raiseError(sprintf(_("Unable to delete %s, the directory is not empty"),
                                                $path . '/' . $name));
            }
        }

        $fileList = $this->_db->getAll(sprintf('SELECT vfs_id, vfs_owner, vfs_perms FROM %s
                                                       WHERE vfs_path = %s AND vfs_name= %s AND vfs_type = %s',
                                                       $this->_params['table'],
                                                       $this->_db->quote($path),
                                                       $this->_db->quote($name),
                                                       $this->_db->quote(VFS_FOLDER)));

        if (!is_array($fileList) || count($fileList) < 1) {
            return PEAR::raiseError(_("Unable to delete VFS directory."));
        }

        /* There may be one or more folders with the same name but as the user
	 * may not have read access to them, they don't see them. So we have to
	 * delete the one they have access to */
        foreach ($fileList as $file) {
            if ($file[1] == $this->_params['user'] || $file[2] & VFS_FLAG_WRITE) {
                $result = $this->_db->query(sprintf('DELETE FROM %s WHERE vfs_id = %s',
                                                    $this->_params['table'],
                                                    $this->_db->quote($file[0])));

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
     * Return a list of the contents of a folder.
     *
     * @param string $path                The path of the directory.
     * @param optional mixed $filter      String/hash to filter file/dirname
     *                                    on.
     * @param optional boolean $dotfiles  Show dotfiles?
     * @param optional boolean $dironly   Show only directories?
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

        $fileList = $this->_db->getAll(sprintf('SELECT vfs_name, vfs_type, vfs_modified, vfs_owner, vfs_perms, vfs_data FROM %s
                                               WHERE vfs_path = %s AND (vfs_owner = %s or vfs_perms && %s)',
                                               $this->_params['table'],
                                               $this->_db->quote($path),
                                               $this->_db->quote($this->_params['user']),
                                               $this->_db->quote(VFS_FLAG_READ)
                                               ));
        if (is_a($fileList, 'PEAR_Error')) {
            return $fileList;
        }

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

                $file['size'] = VFS::strlen($line[5]);
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
     * Changes permissions for an Item on the VFS.
     *
     * @access public
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

        $fileList = $this->_db->getAll(sprintf('SELECT vfs_id, vfs_owner, vfs_perms FROM %s
                                                       WHERE vfs_path = %s AND vfs_name= %s',
                                                       $this->_params['table'],
                                                       $this->_db->quote($path),
                                                       $this->_db->quote($name)));

        if (!is_array($fileList) || count($fileList) < 1) {
            return PEAR::raiseError(_("Unable to rename VFS file."));
        }

        /* There may be one or more files with the same name but the user may
	 * not have read access to them, so doesn't see them. So we have to
	 * chmod the one they have access to. */
        foreach ($fileList as $file) {
            if ($file[1] == $this->_params['user'] || $file[2] & VFS_FLAG_WRITE) {
                $result = $this->_db->query(sprintf('UPDATE %s SET vfs_perms = %s
                                                    WHERE vfs_id = %s',
                                                    $this->_params['table'],
                                                    $this->_db->quote($perm),
                                                    $this->_db->quote($file[0])));
                return $result;
            }
        }

        return PEAR::raiseError(sprintf(_("Unable to change permission for VFS file %s/%s."), $path, $name));
    }

}
