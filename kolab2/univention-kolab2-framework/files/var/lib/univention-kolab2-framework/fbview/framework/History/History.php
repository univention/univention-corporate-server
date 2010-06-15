<?php

require_once 'Horde/DataTree.php';

/**
 * The History:: class provides a method of tracking changes in Horde
 * objects using the Horde DataTree backend.
 *
 * $Horde: framework/History/History.php,v 1.17 2004/04/07 14:43:08 chuck Exp $
 *
 * Copyright 2003-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.1
 * @package Horde_History
 */
class Horde_History {

    /**
     * Pointer to a DataTree instance to manage the history.
     * @var object DataTree $_datatree
     */
    var $_datatree;

    /**
     * Constructor.
     */
    function Horde_History()
    {
        global $conf;

        if (!isset($conf['datatree']['driver'])) {
            Horde::fatal('You must configure a DataTree backend to use History.');
        }
        $driver = $conf['datatree']['driver'];
        $this->_datatree = &DataTree::singleton($driver,
                                                array_merge(Horde::getDriverConfig('datatree', $driver),
                                                            array('group' => 'horde.history')));
    }

    /**
     * Log an event to an item's history log. The item must be
     * uniquely identified by $itemGuid. Any other details about the
     * event are passed in $attributes. Standard suggested attributes
     * are:
     *
     *   'who' => The id of the user that performed the action (will
     * be added automatically if not present).
     *
     *   'ts' => Timestamp of the action (this will be added
     * automatically if it is not present).
     *
     *   'desc' => Text description of the action (this may contain a
     * %s to represent the date of the action).
     *
     * @access public.
     *
     * @param string  $guid           The unique identifier of the entry to add to.
     * @param array   $attributes     (optional) The hash of name => value entries that describe this event.
     * @param boolean $replaceAction  (optional) If $attributes['action'] is already present in the
     *                                item's history log, update that entry instead of creating
     *                                a new one.
     *
     * @return boolean|object PEAR_Error  True on success, or a PEAR_Error object on failure.
     */
    function log($guid, $attributes = array(), $replaceAction = false)
    {
        $history = &$this->getHistory($guid, true);
        if (is_a($history, 'PEAR_Error')) {
            return $history;
        }

        $history->log($attributes, $replaceAction);

        return $this->_updateHistory($history);
    }

    /**
     * Return a DataTreeObject_History object corresponding to the
     * named history entry, with the data retrieved appropriately. If
     * $autocreate is true, and $guid does not already exist, create,
     * save, and return a new History object with this $id.
     *
     * @param optional boolean $autocreate  Automatically create the history entry?
     *
     * @param string $guid  The name of the history entry to retrieve.
     */
    function &getHistory($guid, $autocreate = false)
    {
        // If the $guid doesn't already contain a specified parent id,
        // then use the current application name as the parent
        // object.
        if (!strstr($guid, ':')) {
            global $registry;
            $guid = $registry->getApp() . ':' . $guid;
        }

        if ($this->_datatree->exists($guid)) {
            $history = &$this->_getHistory($guid);
        } elseif ($autocreate) {
            $history = &$this->_newHistory($guid);
            $result = $this->_addHistory($history);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        } else {
            // Return an empty history object for ease of use.
            $history = &new DataTreeObject_History($guid);
            $history->setHistoryOb($this);
        }

        return $history;
    }

    /**
     * Find history objects by timestamp, and optionally filter on
     * other fields as well.
     *
     * @param string $cmp    The comparison operator (<, >, <=, >=, or =) to
     *                       check the timestamps with.
     * @param integer $ts    The timestamp to compare against.
     * @param array $filters (optional) An array of additional (ANDed) criteria.
     *                       each array value should be an array with 3 entries:
     *                         'op'    - the operator to compare this field with.
     *                         'field' - the history field being compared (i.e., 'action').
     *                         'value' - the value to check for (i.e., 'add').
     * @param string $parent (optional) The parent history to start searching at.
     *
     * @return array  An array of history object ids, or an empty array
     *                if none matched the criteria.
     */
    function &getByTimestamp($cmp, $ts, $filters = array(), $parent = '-1')
    {
        // Build the timestamp test.
        $criteria = array(
            array('field' => 'key', 'op' => '=', 'test' => 'ts'),
            array('field' => 'value', 'op' => $cmp, 'test' => $ts));

        // Add additional filters, if there are any.
        if (count($filters)) {
            foreach ($filters as $filter) {
                $criteria[] = array('JOIN' => array(
                                  array('field' => 'key', 'op' => '=', 'test' => $filter['field']),
                                  array('field' => 'value', 'op' => $filter['op'], 'test' => $filter['value'])));
            }
        }

        // Everything is ANDed together.
        $criteria = array('AND' => $criteria);

        $histories = $this->_datatree->getByAttributes($criteria, $parent);
        if (is_a($histories, 'PEAR_Error') || !count($histories)) {
            // If we got back an error or an empty array, just return
            // it.
            return $histories;
        }

        return $this->_getHistories(array_keys($histories));
    }

    /**
     * Return a DataTreeObject_History object corresponding to the
     * named history entry, with the data retrieved appropriately.
     *
     * @param string $guid  The name of the history entry to retrieve.
     */
    function &_getHistory($guid)
    {
        /* Cache of previous retrieved history entries. */
        static $historyCache;

        if (!is_array($historyCache)) {
            $historyCache = array();
        }

        if (!isset($historyCache[$guid])) {
            $historyCache[$guid] = $this->_datatree->getObject($guid, 'DataTreeObject_History');
            if (!is_a($historyCache[$guid], 'PEAR_Error')) {
                $historyCache[$guid]->setHistoryOb($this);
            }
        }

        return $historyCache[$guid];
    }

    /**
     * Return an array of DataTreeObject_History objects corresponding
     * to the given set of unique IDs, with the details retrieved
     * appropriately.
     *
     * @param array $guids  The array of ids to retrieve.
     */
    function &_getHistories($guids)
    {
        $histories = &$this->_datatree->getObjects($guids, 'DataTreeObject_History');
        if (is_a($histories, 'PEAR_Error')) {
            return $histories;
        }

        $keys = array_keys($histories);
        foreach ($keys as $key) {
            if (!is_a($histories[$key], 'PEAR_Error')) {
                $histories[$key]->setHistoryOb($this);
            }
        }

        return $histories;
    }

    /**
     * Change the name of a history entry without changing its
     * contents.
     *
     * @param object DataTreeObject_History $history  The history entry to rename.
     * @param string                        $newName  The entry's new name.
     */
    function rename($history, $newName)
    {
        if (!is_a($history, 'DataTreeObject_History')) {
            return PEAR::raiseError('History entries must be DataTreeObject_History objects or extend that class.');
        }
        return $this->_datatree->rename($history, $newName);
    }

    /**
     * Copy a history entry's data to a new name, keeping the old
     * entry as well.
     *
     * @param object DataTreeObject_History $history  The history entry to rename.
     * @param string                        $newName  The entry's new name.
     */
    function copy($history, $newName)
    {
        if (!is_a($history, 'DataTreeObject_History')) {
            return PEAR::raiseError('History entries must be DataTreeObject_History objects or extend that class.');
        }
        $new = &$this->_newHistory($newName);
        $new->data = $history->data;
        return $this->_addHistory($new);
    }

    /**
     * Remove a history entry from the history system permanently.
     *
     * @param object DataTreeObject_History $history  The history entry to remove.
     */
    function removeHistory($history)
    {
        if (!is_a($history, 'DataTreeObject_History')) {
            return PEAR::raiseError('History entries must be DataTreeObject_History objects or extend that class.');
        }
        return $this->_datatree->remove($history, false);
    }

    /**
     * Get a list of every history entry, in the format cid =>
     * historyname.
     *
     * @return array  CID => historyname hash.
     */
    function listHistories()
    {
        static $entries;

        if (is_null($entries)) {
            $entries = $this->_datatree->get(DATATREE_FORMAT_FLAT, '-1', true);
            unset($entries['-1']);
        }

        return $entries;
    }

    /**
     * Return a new history entry object.
     *
     * @access private
     *
     * @param string $guid  The entry's name.
     *
     * @return object DataTreeObject_History  A new history entry object.
     */
    function &_newHistory($guid)
    {
        if (empty($guid)) {
            return PEAR::raiseError(_("History entry names must be non-empty"));
        }
        $history = &new DataTreeObject_History($guid);
        $history->setHistoryOb($this);
        return $history;
    }

    /**
     * Add an entry to the history system. The entry must first be
     * created with &History::_newHistory() before this function is
     * called.
     *
     * @access private
     *
     * @param object DataTreeObject_History $history  The new history entry object.
     */
    function _addHistory($history)
    {
        if (!is_a($history, 'DataTreeObject_History')) {
            return PEAR::raiseError('History entries must be DataTreeObject_History objects or extend that class.');
        }
        return $this->_datatree->add($history);
    }

    /**
     * Store updated data of a history to the backend system.
     *
     * @access private
     *
     * @param object DataTreeObject_History $history  The history entry to update.
     */
    function _updateHistory($history)
    {
        if (!is_a($history, 'DataTreeObject_History')) {
            return PEAR::raiseError('History entries must be DataTreeObject_History objects or extend that class.');
        }
        return $this->_datatree->updateData($history);
    }

    /**
     * Attempts to return a reference to a concrete History instance.
     * It will only create a new instance if no History instance
     * currently exists.
     *
     * This method must be invoked as: $var = &History::singleton()
     *
     * @return object Horde_History  The concrete History reference, or false on an
     *                               error.
     */
    function &singleton()
    {
        static $history;

        if (!isset($history)) {
            $history = new Horde_History();
        }

        return $history;
    }

}

/**
 * Extension of the DataTreeObject class for storing History information
 * in the DataTree backend. If you want to store specialized History
 * information, you should extend this class instead of extending
 * DataTreeObject directly.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.1
 * @package Horde_History
 */
class DataTreeObject_History extends DataTreeObject {

    /**
     * The History object which this history came from - needed for
     * updating data in the backend to make changes stick, etc.
     *
     * @var object History $historyOb
     */
    var $_historyOb;

    /**
     * Associates a History object with this history.
     *
     * @param object History $historyOb The History object.
     */
    function setHistoryOb(&$historyOb)
    {
        $this->_historyOb = &$historyOb;
    }

    /**
     * Log an event to this item's history log. Details about the
     * event are passed in $attributes. Standard suggested attributes
     * are:
     *
     *   'who' => The id of the user that performed the action (will
     * be added automatically if not present).
     *
     *   'ts' => Timestamp of the action (this will be added
     * automatically if it is not present).
     *
     *   'desc' => Text description of the action (this may contain a
     * %s to represent the date of the action).
     *
     * @access public.
     *
     * @param array   $attributes     The hash of name => value entries that describe this event.
     * @param boolean $replaceAction  (optional) If $attributes['action'] is already present in the
     *                                item's history log, update that entry instead of creating
     *                                a new one.
     *
     * @return boolean|object PEAR_Error  True on success, or a PEAR_Error object on failure.
     */
    function log($attributes = array(), $replaceAction = false)
    {
        if (empty($attributes['who'])) {
            $attributes['who'] = Auth::getAuth();
        }
        if (empty($attributes['ts'])) {
            $attributes['ts'] = time();
        }

        // If we want to replace an entry with the same action, try
        // and find one. Track whether or not we succeed in $done, so
        // we know whether or not to add the entry later.
        $done = false;
        if ($replaceAction && !empty($attributes['action'])) {
            $count = count($this->data);
            for ($i = 0; $i < $count; $i++) {
                if (!empty($this->data[$i]['action']) &&
                    $this->data[$i]['action'] == $attributes['action']) {
                    $this->data[$i] = $attributes;
                    $done = true;
                    break;
                }
            }
        }

        // If we're not replacing by action, or if we didn't find an
        // entry to replace, tack $attributes onto the end of the
        // $data array.
        if (!$done) {
            $this->data[] = $attributes;
        }
    }

    /**
     * Format the description from a history entry using the default
     * timestamp format or a specified one.
     *
     * @param          array  $entry   The history entry.
     * @param optional string $format  The format string to use for the timestamp.
     *
     * @return string  The formatted description.
     */
    function getDescription($entry, $format = '%x %X')
    {
        return @sprintf($entry['desc'], strftime($format, $entry['ts']));
    }

    /**
     * Save any changes to this object to the backend permanently.
     */
    function save()
    {
        $this->_historyOb->_updateHistory($this);
    }

    /**
     * Map this object's attributes from the data array into a format
     * that we can store in the attributes storage backend.
     *
     * @return array  The attributes array.
     */
    function _toAttributes()
    {
        // Default to no attributes.
        $attributes = array();

        // Loop through all users, if any.
        foreach ($this->data as $index => $entry) {
            foreach ($entry as $key => $value) {
                $attributes[] = array('name' => (string)$index,
                                      'key' => (string)$key,
                                      'value' => (string)$value);
            }
        }

        return $attributes;
    }

    /**
     * Take in a list of attributes from the backend and map it to our
     * internal data array.
     *
     * @param array $attributes  The list of attributes from the
     *                           backend (attribute name, key, and value).
     */
    function _fromAttributes($attributes)
    {
        // Initialize data array.
        $this->data = array();

        foreach ($attributes as $attr) {
            if (!isset($this->data[$attr['name']])) {
                $this->data[$attr['name']] = array();
            }
            $this->data[$attr['name']][$attr['key']] = $attr['value'];
        }
    }

}
