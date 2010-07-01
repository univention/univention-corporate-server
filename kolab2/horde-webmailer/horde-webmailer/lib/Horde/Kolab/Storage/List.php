<?php
/**
 * @package Kolab_Storage
 *
 * $Horde: framework/Kolab_Storage/lib/Horde/Kolab/Storage/List.php,v 1.3.2.8 2009-04-25 18:43:41 wrobel Exp $
 */

/** Kolab IMAP folder representation. **/
require_once 'Horde/Kolab/Storage/Folder.php';

/**
 * The Kolab_List class represents all IMAP folders on the Kolab
 * server visible to the current user.
 *
 * $Horde: framework/Kolab_Storage/lib/Horde/Kolab/Storage/List.php,v 1.3.2.8 2009-04-25 18:43:41 wrobel Exp $
 *
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @package Kolab_Storage
 */
class Kolab_List {

    /**
     * The list of existing folders on this server.
     *
     * @var array
     */
    var $_list;

    /**
     * A cache for folder objects (these do not necessarily exist).
     *
     * @var array
     */
    var $_folders;

    /**
     * A cache array listing a default folder for each folder type.
     *
     * @var array
     */
    var $_defaults;

    /**
     * A cache array listing a the folders for each folder type.
     *
     * @var array
     */
    var $_types;

    /**
     * A validity marker.
     *
     * @var int
     */
    var $validity;


    /**
     * Constructor.
     */
    function Kolab_List()
    {
        $this->validity = 0;
        $this->__wakeup();
    }

    /**
     * Initializes the object.
     */
    function __wakeup()
    {
        if (!isset($this->_folders)) {
            $this->_folders = array();
        }

        foreach($this->_folders as $folder) {
            $folder->setList($this);
        }
    }

    /**
     * Attempts to return a reference to a concrete Kolab_Folders_List instance.
     *
     * It will only create a new instance if no Kolab_Folders instance currently
     * exists.
     *
     * This method must be invoked as:
     *   <code>$var = &Kolab_Folders_List::singleton();</code>
     *
     * @static
     *
     * @return Kolab_Folders_List  The concrete List reference.
     */
    function &singleton($destruct = false)
    {
        static $list;

        if (!isset($list) &&
            !empty($GLOBALS['conf']['kolab']['imap']['cache_folders'])) {
            require_once 'Horde/SessionObjects.php';
            $session = &Horde_SessionObjects::singleton();
            $list = $session->query('kolab_folderlist');
        }

        if (empty($list[Auth::getAuth()]) || $destruct) {
            $list[Auth::getAuth()] = new Kolab_List();
        }

        if (!empty($GLOBALS['conf']['kolab']['imap']['cache_folders'])) {
            register_shutdown_function(array(&$list, 'shutdown'));
        }

        return $list[Auth::getAuth()];
    }

    /**
     * Stores the object in the session cache.
     */
    function shutdown()
    {
        require_once 'Horde/SessionObjects.php';
        $session = &Horde_SessionObjects::singleton();
        $session->overwrite('kolab_folderlist', $this, false);
    }

    /**
     * Returns the list of folders visible to the current user.
     *
     * @return array|PEAR_Error The list of IMAP folders, represented
     *                          as Kolab_Folder objects.
     */
    function &listFolders()
    {
        if (!isset($this->_list)) {
            $session = &Horde_Kolab_Session::singleton();
            $imap = &$session->getImap();
            if (is_a($imap, 'PEAR_Error')) {
                return $imap;
            }

            // Obtain a list of all folders the current user has access to
            $this->_list = $imap->getMailboxes();
            if (is_a($this->_list, 'PEAR_Error')) {
                return $this->_list;
            }
        }
        return $this->_list;
    }

    /**
     * Get several or all Folder objects.
     *
     * @param array $folders Several folder names or unset to retrieve
     *                       all folders.
     *
     * @return array|PEAR_Error An array of Kolab_Folder objects.
     */
    function getFolders($folders = null)
    {
        if (!isset($folders)) {
            $folders = $this->listFolders();
            if (is_a($folders, 'PEAR_Error')) {
                return $folders;
            }
        }

        $result = array();
        foreach ($folders as $folder) {
            $result[] = $this->getFolder($folder);
        }
        return $result;
    }

    /**
     * Get a Folder object.
     *
     * @param string $folder The folder name.
     *
     * @return Kolab_Folder|PEAR_Error The Kolab folder object.
     */
    function getFolder($folder)
    {
        if (!isset($this->_folders[$folder])) {
            $kf = new Kolab_Folder($folder);
            $kf->setList($this);
            $this->_folders[$folder] = &$kf;
        }
        return $this->_folders[$folder];
    }

    /**
     * Get a new Folder object.
     *
     * @return Kolab_Folder|PEAR_Error The new Kolab folder object.
     */
    function getNewFolder()
    {
        $folder = new Kolab_Folder(null);
        $folder->setList($this);
        return $folder;
    }

    /**
     * Get a Folder object based on a share ID.
     *
     * @param string $share The share ID.
     * @param string $type  The type of the share/folder.
     *
     * @return Kolab_Folder|PEAR_Error The Kolab folder object.
     */
    function getByShare($share, $type)
    {
        $folder = $this->parseShare($share, $type);
        if (is_a($folder, 'PEAR_Error')) {
            return $folder;
        }
        return $this->getFolder($folder);
    }

    /**
     * Get a list of folders based on the type.
     *
     * @param string $type  The type of the share/folder.
     *
     * @return Kolab_Folder|PEAR_Error The list of Kolab folder
     *                                 objects.
     */
    function getByType($type)
    {
        if (!isset($this->_types)) {
            $result = $this->initiateCache();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
        if (isset($this->_types[$type])) {
            return $this->getFolders($this->_types[$type]);
        } else {
            return array();
        }
    }

    /**
     * Get the default folder for a certain type.
     *
     * @param string $type  The type of the share/folder.
     *
     * @return mixed The default folder, false if there is no default
     *               and a PEAR_Error in case of an error.
     */
    function getDefault($type)
    {
        if (!isset($this->_defaults)) {
            $result = $this->initiateCache();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
        if (isset($this->_defaults[Auth::getAuth()][$type])) {
            return $this->getFolder($this->_defaults[Auth::getAuth()][$type]);
        } else {
            return false;
        }
    }

    /**
     * Get the default folder for a certain type from a different owner.
     *
     * @param string $owner The folder owner.
     * @param string $type  The type of the share/folder.
     *
     * @return mixed The default folder, false if there is no default
     *               and a PEAR_Error in case of an error.
     */
    function getForeignDefault($owner, $type)
    {
        if (!isset($this->_defaults)) {
            $result = $this->initiateCache();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
        if (isset($this->_defaults[$owner][$type])) {
            return $this->getFolder($this->_defaults[$owner][$type]);
        } else {
            return false;
        }
    }

    /**
     * Start the cache for the type specific and the default folders.
     */
    function initiateCache()
    {
        $folders = $this->getFolders();
        if (is_a($folders, 'PEAR_Error')) {
            return $folders;
        }

        $this->_types = array();
        $this->_defaults = array();

        foreach ($folders as $folder) {
            $type = $folder->getType();
            if (is_a($type, 'PEAR_Error')) {
                return $type;
            }
            $default = $folder->isDefault();
            if (is_a($default, 'PEAR_Error')) {
                return $default;
            }
            $owner = $folder->getOwner();
            if (is_a($owner, 'PEAR_Error')) {
                return $owner;
            }
            if (!isset($this->_types[$type])) {
                $this->_types[$type] = array();
            }
            $this->_types[$type][] = $folder->name;
            if ($default) {
                $this->_defaults[$owner][$type] = $folder->name;
            }
        }
    }

    /**
     * Converts the horde syntax for shares to storage identifiers.
     *
     * @param string $share The share ID that should be parsed.
     * @param string $type  The type of the share/folder.
     *
     * @return string|PEAR_Error The corrected folder name.
     */
    function parseShare($share, $type)
    {
        // Handle default shares
        if ($share == Auth::getAuth()) {
            $result = $this->getDefault($type);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
            if (!empty($result)) {
                return $result->name;
            }
        }
        return rawurldecode($share);
    }

    /**
     * Creates a new IMAP folder.
     *
     * @param Kolab_Folder $folder The folder that should be created.
     *
     * @return boolean|PEAR_Error True on success.
     */
    function create(&$folder)
    {
        $session = &Horde_Kolab_Session::singleton();
        $imap = &$session->getImap();
        if (is_a($imap, 'PEAR_Error')) {
            return $imap;
        }

        $result = $imap->exists($folder->new_name);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        if ($result) {
            return PEAR::raiseError(sprintf(_("Unable to add %s: destination folder already exists"),
                                            $folder->new_name));
        }

        $result = $imap->create($folder->new_name);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        $this->updateCache($folder);
        $this->validity++;
        return true;
    }

    /**
     * Rename an IMAP folder.
     *
     * @param Kolab_Folder $folder The folder that should be renamed.
     *
     * @return boolean|PEAR_Error True on success.
     */
    function rename(&$folder)
    {
        $session = &Horde_Kolab_Session::singleton();
        $imap = &$session->getImap();
        if (is_a($imap, 'PEAR_Error')) {
            return $imap;
        }

        $result = $imap->exists($folder->new_name);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        if ($result) {
            return PEAR::raiseError(sprintf(_("Unable to rename %s to %s: destination folder already exists"),
                                            $folder->name, $folder->new_name));
        }

        $result = $imap->rename($folder->name, $folder->new_name);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $this->updateCache($folder, false);
        $this->updateCache($folder);
        $this->validity++;
        return true;
    }

    /**
     * Delete an IMAP folder.
     *
     * @param Kolab_Folder $folder The folder that should be deleted.
     *
     * @return boolean|PEAR_Error True on success.
     */
    function remove(&$folder)
    {
        $session = &Horde_Kolab_Session::singleton();
        $imap = &$session->getImap();
        if (is_a($imap, 'PEAR_Error')) {
            return $imap;
        }

        $result = $imap->exists($folder->name);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if ($result === true) {
            $result = $imap->delete($folder->name);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
        $this->updateCache($folder, false);
        $this->validity++;
        return true;
    }

    /**
     * Update the cache variables.
     *
     * @param Kolab_Folder $folder The folder that was changed.
     * @param boolean      $added  Has the folder been added or removed?
     */
    function updateCache(&$folder, $added = true)
    {
        $type = $folder->getType();
        if (is_a($type, 'PEAR_Error')) {
            Horde::logMessage(sprintf("Error while updating the Kolab folder list cache: %s.",
                                      $type->getMessage()), __FILE__, __LINE__, PEAR_LOG_ERR);
            return;
        }
        $default = $folder->isDefault();
        if (is_a($default, 'PEAR_Error')) {
            Horde::logMessage(sprintf("Error while updating the Kolab folder list cache: %s.",
                                      $default->getMessage()), __FILE__, __LINE__, PEAR_LOG_ERR);
            return;
        }
        $owner = $folder->getOwner();
        if (is_a($owner, 'PEAR_Error')) {
            Horde::logMessage(sprintf("Error while updating the Kolab folder list cache: %s.",
                                      $owner->getMessage()), __FILE__, __LINE__, PEAR_LOG_ERR);
            return;
        }

        if (!isset($this->_types) || !isset($this->_defaults)) {
            $this->initiateCache();
        }

        if ($added) {
            $this->_folders[$folder->new_name] = &$folder;
            if (isset($this->_list)) {
                $this->_list[] = $folder->new_name;
            }
            $this->_types[$type][] = $folder->new_name;
            if ($default) {
                $this->_defaults[$owner][$type] = $folder->new_name;
            }
        } else {
            unset($this->_folders[$folder->name]);
            if (isset($this->_list)) {
                $idx = array_search($folder->name, $this->_list);
                if ($idx !== false) {
                    unset($this->_list[$idx]);
                }
            }
            if (isset($this->_types[$type])) {
                $idx = array_search($folder->name, $this->_types[$type]);
                if ($idx !== false) {
                    unset($this->_types[$type][$idx]);
                }
            }
            if ($default && isset($this->_defaults[$owner][$type])) {
                unset($this->_defaults[$owner][$type]);
            }
        }
    }
}
