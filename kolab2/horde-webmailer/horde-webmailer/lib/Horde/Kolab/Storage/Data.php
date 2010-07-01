<?php
/**
 * @package Kolab_Storage
 *
 * $Horde: framework/Kolab_Storage/lib/Horde/Kolab/Storage/Data.php,v 1.5.2.4 2009-01-06 15:23:18 jan Exp $
 */

/** Data caching for Kolab **/
require_once 'Horde/Kolab/Storage/Cache.php';

/**
 * The Kolab_Data class represents a data type in an IMAP folder on the Kolab
 * server.
 *
 * $Horde: framework/Kolab_Storage/lib/Horde/Kolab/Storage/Data.php,v 1.5.2.4 2009-01-06 15:23:18 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Stuart Binge <omicron@mighty.co.za>
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @author  Thomas Jarosch <thomas.jarosch@intra2net.com>
 * @package Kolab_Storage
 */
class Kolab_Data {

    /**
     * The link to the folder object.
     *
     * @var Kolab_Folder
     */
    var $_folder;

    /**
     * The folder type.
     *
     * @var string
     */
    var $_type;

    /**
     * The object type of the data.
     *
     * @var string
     */
    var $_object_type;

    /**
     * The version of the data.
     *
     * @var int
     */
    var $_data_version;

    /**
     * The data cache.
     *
     * @var Kolab_Cache
     */
    var $_cache;

    /**
     * The Id of this data object in the cache.
     *
     * @var string
     */
    var $_cache_key;

    /**
     * An addition to the cache key in case we are operating on
     * something other than the default type.
     *
     * @var string
     */
    var $_type_key;

    /**
     * Do we optimize for cyrus IMAPD?
     *
     * @var boolean
     */
    var $_cache_cyrus_optimize = true;

    /**
     * Creates a Kolab Folder Data representation.
     *
     * @param string  $type         Type of the folder.
     * @param string  $object_type  Type of the objects we want to read.
     * @param int     $data_version Format version of the object data.
     */
    function Kolab_Data($type, $object_type = null, $data_version = 1)
    {
        $this->_type = $type;
        if (!empty($object_type)) {
            $this->_object_type  = $object_type;
        } else {
            $this->_object_type  = $type;
        }
        $this->_data_version = $data_version;

        if ($this->_object_type != $this->_type) {
            $this->_type_key = '@' . $this->_object_type;
        } else {
            $this->_type_key = '';
        }
        $this->__wakeup();
    }

    /**
     * Initializes the object.
     */
    function __wakeup()
    {
        $this->_cache = &Kolab_Cache::singleton();
    }

    /**
     * Returns the properties that need to be serialized.
     *
     * @return array  List of serializable properties.
     */
    function __sleep()
    {
        $properties = get_object_vars($this);
        unset($properties['_cache'], $properties['_folder']);
        $properties = array_keys($properties);
        return $properties;
    }

    /**
     * Set the folder handler.
     *
     * @param Kolab_Folder $folder  The handler for the folder of folders.
     */
    function setFolder(&$folder)
    {
        $this->_folder = &$folder;
        $this->_cache_key = $this->_getCacheKey();
    }

    /**
     * Return a unique key for the current folder.
     *
     * @return string A key that represents the current folder.
     */
    function _getCacheKey()
    {
        if ($this->_cache_cyrus_optimize) {
            $search_prefix = 'INBOX/';

            $pos = strpos($this->_folder->name, $search_prefix);
            if ($pos !== false && $pos == 0) {
                $key = 'user/' . Auth::getBareAuth() . '/'
                           . substr($this->_folder->name,
                                    strlen($search_prefix))
                           . $this->_type_key;
            } else {
                $key = $this->_folder->name;
            }
        } else {
            $key = $this->_folder->getOwner() . '/' . $this->_folder->name;
        }
        return $key;
    }

    /**
     * Delete the specified message from this folder.
     *
     * @param  string $object_uid Id of the message to be deleted.
     *
     * @return boolean|PEAR_Error True is successful, false if the
     *                            message does not exist.
     */
    function delete($object_uid)
    {
        if (!$this->objectUidExists($object_uid)) {
            return false;
        }

        // Find the storage ID
        $id = $this->_getStorageId($object_uid);
        if ($id === false) {
            return false;
        }

        $result = $this->_folder->deleteMessage($id);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $this->_cache->load($this->_cache_key, $this->_data_version);

        unset($this->_cache->objects[$object_uid]);
        unset($this->_cache->uids[$id]);
        $this->_cache->save();
        return true;
    }

    /**
     * Delete all messages from the current folder.
     *
     * @return boolean|PEAR_Error True if successful.
     */
    function deleteAll()
    {
        if (empty($this->_cache->uids)) {
            return true;
        }
        foreach ($this->_cache->uids as $id => $object_uid) {
            $result = $this->_folder->deleteMessage($id, false);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            $this->_cache->load($this->_cache_key, $this->_data_version);

            unset($this->_cache->objects[$object_uid]);
            unset($this->_cache->uids[$id]);
        }
        $this->_cache->save();

        $result = $this->_folder->trigger();
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage(sprintf('Failed triggering folder %s!',
                                      $this->_folder->name),
                              __FILE__, __LINE__, PEAR_LOG_ERR);
        }

        return true;
    }

    /**
     * Move the specified message from the current folder into a new
     * folder.
     *
     * @param  string $object_uid  ID of the message to be deleted.
     * @param  string $new_share   ID of the target share.
     *
     * @return boolean|PEAR_Error True is successful, false if the
     *                            object does not exist.
     */
    function move($object_uid, $new_share)
    {
        if (!$this->objectUidExists($object_uid)) {
            return false;
        }

        // Find the storage ID
        $id = $this->_getStorageId($object_uid);
        if ($id === false) {
            return false;
        }

        $result = $this->_folder->moveMessageToShare($id, $new_share);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $this->_cache->load($this->_cache_key, $this->_data_version);

        unset($this->_cache->objects[$object_uid]);
        unset($this->_cache->uids[$id]);
        $this->_cache->save();
        return true;
    }

    /**
     * Save an object.
     *
     * @param array  $object         The array that holds the data object.
     * @param string $old_object_id  The id of the object if it existed before.
     *
     * @return boolean|PEAR_Error    True on success.
     */
    function save($object, $old_object_id = null)
    {
        // update existing kolab object
        if ($old_object_id != null) {
            // check if object really exists
            if (!$this->objectUidExists($old_object_id)) {
                return PEAR::raiseError(sprintf(_("Old object %s does not exist."),
                                                $old_object_id));
            }

            // get the storage ID
            $id = $this->_getStorageId($old_object_id);
            if ($id === false) {
                return PEAR::raiseError(sprintf(_("Old object %s does not map to a uid."),
                                                $old_object_id));
            }

            $old_object = $this->getObject($old_object_id);
        } else {
            $id = null;
            $old_object = null;
        }

        $result = $this->_folder->saveObject($object, $this->_data_version,
                                             $this->_object_type, $id, $old_object);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $result = $this->synchronize($old_object_id);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        return true;
    }

    /**
     * Synchronize the data cache for the current folder.
     *
     * @param string $history_ignore Object uid that should not be
     *                               updated in the History
     */
    function synchronize($history_ignore = null)
    {
        $this->_cache->load($this->_cache_key, $this->_data_version);

        $result = $this->_folder->getStatus();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        list($validity, $nextid, $ids) = $result;

        $changes = $this->_folderChanged($validity, $nextid, array_keys($this->_cache->uids), $ids);
        if ($changes) {
            $modified = array();

            $recent_uids = array_diff($ids, array_keys($this->_cache->uids));

            $formats = $this->_folder->getFormats();

            $handler = Horde_Kolab_Format::factory('XML', $this->_object_type, $this->_data_version);
            if (is_a($handler, 'PEAR_Error')) {
                return $handler;
            }

            $count = 0;
            foreach ($recent_uids as $id) {

                if ($this->_type == 'annotation' && $id != 1) {
                    continue;
                }

                $mime = $this->_folder->parseMessage($id, $handler->getMimeType(), false);
                if (is_a($mime, 'PEAR_Error')) {
                    Horde::logMessage($text, __FILE__, __LINE__, PEAR_LOG_WARNING);
                    $text = false;
                } else {
                    $text = $mime[0];
                }

                if ($text) {
                    $object = $handler->load($text);
                    if (is_a($object, 'PEAR_Error')) {
                        $this->_cache->ignore($id);
                        $object->addUserInfo('STORAGE ID: ' . $id);
                        Horde::logMessage($object, __FILE__, __LINE__, PEAR_LOG_WARNING);
                        continue;
                    }
                } else {
                    $object = false;
                }

                if ($object !== false) {
                    $message = &$mime[2];
                    $handler_type = $handler->getMimeType();
                    foreach ($message->getParts() as $part) {
                        $name = $part->getName();
                        $type = $part->getType();
                        $dp   = $part->getDispositionParameter('x-kolab-type');
                        if (!empty($name) && $type != $handler_type
                            || (!empty($dp) && in_array($dp, $formats))) {
                            $object['_attachments'][$name]['type'] = $type;
                            $object['_attachments'][$name]['key'] = $this->_cache_key . '/' . $object['uid'] . ':' . $name;
                            $part->transferDecodeContents();
                            $result = $this->_cache->storeAttachment($object['_attachments'][$name]['key'],
                                                                     $part->getContents());
                            if (is_a($result, 'PEAR_Error')) {
                                Horde::logMessage(sprintf('Failed storing attachment of object %s: %s',
                                                          $id, $result->getMessage()),
                                                  __FILE__, __LINE__, PEAR_LOG_ERR);
                                $object = false;
                                break;
                            }
                        }
                    }
                }

                if ($object !== false) {
                    $this->_cache->store($id, $object['uid'], $object);
                    $mod_ts = time();
                    if (is_array($changes) && in_array($object['uid'], $changes)
                        && $object['uid'] != $history_ignore) {
                        $this->_updateHistory($object['uid'], $mod_ts, 'modify');
                        $modified[] = $object['uid'];
                    } else {
                        $this->_updateHistory($object['uid'], $mod_ts, 'add');
                    }
                } else {
                    $this->_cache->ignore($id);
                }

                // write out cache once in a while so if the browser times out
                // we don't have to start from the beginning.
                if ($count > 500) {
                    $count = 0;
                    $this->_cache->save();
                }
                $count++;
            }

            $this->_cache->save();

            if (is_array($changes)) {
                $deleted = array_diff($changes, $modified);
                foreach ($deleted as $deleted_oid) {
                    if ($deleted_oid != $history_ignore) {
                        $this->_updateHistory($deleted_oid, time(), 'delete');
                    }
                }
            }
        }
    }

    /**
     * Update the Horde history in case an element was modified
     * outside of Horde.
     *
     * @param string $object_uid Object uid that should be updated.
     * @param int    $mod_ts     Timestamp of the modification.
     * @param string $action     The action that was performed.
     */
    function _updateHistory($object_uid, $mod_ts, $action)
    {
        global $registry;

        if (!isset($registry)) {
            return;
        }

        $app = $registry->getApp();
        if (empty($app) || is_a($app, 'PEAR_Error')) {
            /**
             * Ignore the history if we are not in application
             * context.
             */
            return $app;
        }

        /* Log the action on this item in the history log. */
        $history = &Horde_History::singleton();

        $history_id = $app . ':' . $this->_folder->getShareId() . ':' . $object_uid;
        $history->log($history_id, array('action' => $action, 'ts' => $mod_ts), true);
    }


    /**
     * Check if the folder has changed and the cache needs to be updated.
     *
     * @param string $validity    ID validity of the folder.
     * @param string $nextid      next ID for the folder.
     * @param array  $old_ids     Old list of IDs in the folder.
     * @param array  $new_ids     New list of IDs in the folder.
     *
     * @return mixed True or an array of deleted IDs if the
     *               folder changed and false otherwise.
     */
    function _folderChanged($validity, $nextid, &$old_ids, &$new_ids)
    {
        $changed = false;
        $reset_done = false;

        // uidvalidity changed?
        if ($validity != $this->_cache->validity) {
            $this->_cache->reset();
            $reset_done = true;
        }

        // nextid changed?
        if ($nextid != $this->_cache->nextid) {
            $changed = true;
        }

        $this->_cache->validity = $validity;
        $this->_cache->nextid = $nextid;

        if ($reset_done) {
            return true;
        }

        // Speed optimization: if nextid and validity didn't change
        // and count(old_ids) == count(new_ids), the folder didn't change.
        if ($changed || count($old_ids) != count ($new_ids)) {
            // remove deleted messages from cache
            $delete_ids = array_diff($old_ids, $new_ids);
            $deleted_oids = array();
            foreach ($delete_ids as $delete_id) {
                $object_id = $this->_cache->uids[$delete_id];
                if ($object_id !== false) {
                    unset($this->_cache->objects[$object_id]);
                    $deleted_oids[] = $object_id;
                }
                unset($this->_cache->uids[$delete_id]);
            }
            if (!empty($deleted_oids)) {
                $changed = $deleted_oids;
            } else {
                $changed = true;
            }
        }
        return $changed;
    }

    /**
     * Return the IMAP ID for the given object ID.
     *
     * @param string   $object_id      The object ID.
     *
     * @return int  The IMAP ID.
     */
    function _getStorageId($object_uid)
    {
        $this->_cache->load($this->_cache_key, $this->_data_version);

        $id = array_search($object_uid, $this->_cache->uids);
        if ($id === false) {
            return false;
        }

        return $id;
    }

    /**
     * Test if the storage ID exists.
     *
     * @param int   $uid      The storage ID.
     *
     * @return boolean  True if the ID exists.
     */
    function _storageIdExists($uid)
    {
        $this->_cache->load($this->_cache_key, $this->_data_version);

        return array_key_exists($uid, $this->_cache->uids);
    }

    /**
     * Generate a unique object id.
     *
     * @return string  The unique id.
     */
    function generateUID()
    {
        do {
            $key = md5(uniqid(mt_rand(), true));
        } while($this->objectUidExists($key));

        return $key;
    }

    /**
     * Check if the given id exists.
     *
     * @param string $uid  The object id.
     *
     * @return boolean  True if the id was found, false otherwise.
     */
    function objectUidExists($uid)
    {
        $this->_cache->load($this->_cache_key, $this->_data_version);

        return array_key_exists($uid, $this->_cache->objects);
    }

    /**
     * Return the specified object.
     *
     * @param string     $object_id       The object id.
     *
     * @return array|PEAR_Error  The object data as an array.
     */
    function getObject($object_id)
    {
        $this->_cache->load($this->_cache_key, $this->_data_version);

        if (!$this->objectUidExists($object_id)) {
            return PEAR::raiseError(sprintf(_("Kolab cache: Object uid %s does not exist in the cache!"), $object_id));
        }
        return $this->_cache->objects[$object_id];
    }

    /**
     * Return the specified attachment.
     *
     * @param string     $attachment_id       The attachment id.
     *
     * @return string|PEAR_Error  The attachment data as a string.
     */
    function getAttachment($attachment_id)
    {
        return $this->_cache->loadAttachment($attachment_id);
    }

    /**
     * Retrieve all object ids in the current folder.
     *
     * @return array  The object ids.
     */
    function getObjectIds()
    {
        $this->_cache->load($this->_cache_key, $this->_data_version);

        return array_keys($this->_cache->objects);
    }

    /**
     * Retrieve all objects in the current folder.
     *
     * @return array  All object data arrays.
     */
    function getObjects()
    {
        $this->_cache->load($this->_cache_key, $this->_data_version);

        return array_values($this->_cache->objects);
    }

    /**
     * Retrieve all objects in the current folder as an array.
     *
     * @return array  The object data array.
     */
    function getObjectArray()
    {
        $this->_cache->load($this->_cache_key, $this->_data_version);

        return $this->_cache->objects;
    }
}
