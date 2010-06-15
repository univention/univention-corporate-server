<?php

require_once 'Horde/History.php';

/**
 * The Turba_Source:: class provides a set of methods for dealing with
 * specific contact sources.
 *
 * $Horde: turba/lib/Source.php,v 1.88 2004/05/25 00:11:06 jan Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jon Parise <jon@csh.rit.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Turba 0.0.1
 * @package Turba
 */
class Turba_Source {

    /**
     * The internal name of this source.
     * @var string $name
     */
    var $name;

    /**
     * The symbolic title of this source.
     * @var string $title
     */
    var $title;

    /**
     * Instance of the underlying Turba_Driver class.
     * @var object Turba_Driver $driver
     */
    var $driver;

    /**
     * Hash describing the mapping between Turba attributes and
     * driver-specific fields.
     * @var array $map
     */
    var $map = array();

    /**
     * List of all fields that can be accessed in the backend
     * (excludes composite attributes, etc.).
     * @var array $fields
     */
    var $fields = array();

    /**
     * Array of fields that must match exactly.
     * @var array $strict
     */
    var $strict = array();

    /**
     * Whether this source is publicly searchable.
     * @var boolean $public
     */
    var $public = false;

    /**
     * Whether this source is read-only (not editable).
     * @var boolean $readonly
     */
    var $readonly = true;

    /**
     * Any admins for this source.
     * @var array $admin
     */
    var $admin = array();

    /**
     * Translates the keys of the first hash from the generalized
     * Turba attributes to the driver-specific fields. The translation
     * is based on the contents of $this->map. This ignores composite
     * fields.
     *
     * @param array $hash  Hash using Turba keys.
     *
     * @return array  Translated version of $hash.
     */
    function toDriverKeys($hash)
    {
        $fields = array();
        foreach ($hash as $key => $val) {
            if (isset($this->map[$key]) && !is_array($this->map[$key])) {
                $fields[$this->map[$key]] = $val;
            }
        }
        return $fields;
    }

    /**
     * Takes a hash of Turba key => search value and return a
     * (possibly nested) array, using backend attribute names, that
     * can be turned into a search by the driver. The translation is
     * based on the contents of $this->map, and includes nested OR
     * searches for composite fields.
     *
     * @param array  $hash         Hash of criteria using Turba keys.
     * @param string $search_type  OR search or AND search?
     * @param array  $strict       Fields that must be matched exactly.
     *
     * @return array  An array of search criteria.
     */
    function makeSearch($criteria, $search_type, $strict)
    {
        $search = array();
        $strict_search = array();
        foreach ($criteria as $key => $val) {
            if (isset($this->map[$key])) {
                if (is_array($this->map[$key])) {
                    $subsearch = array();
                    foreach ($this->map[$key]['fields'] as $field) {
                        $field = $this->toDriver($field);
                        if (!empty($strict[$field])) {
                            $strict_search[] = array('field' => $field, 'op' => '=', 'test' => $val);
                        } else {
                            $subsearch[] = array('field' => $field, 'op' => 'LIKE', 'test' => $val);
                        }
                    }
                    if (count($subsearch)) {
                        $search[] = array('OR' => $subsearch);
                    }
                } else {
                    if (!empty($strict[$this->map[$key]])) {
                        $strict_search[] = array('field' => $this->map[$key], 'op' => '=', 'test' => $val);
                    } else {
                        $search[] = array('field' => $this->map[$key], 'op' => 'LIKE', 'test' => $val);
                    }
                }
            }
        }

        if (count($strict_search) && count($search)) {
            return array('AND' => array($strict_search, array($search_type => $search)));
        } elseif (count($strict_search)) {
            return array('AND' => $strict_search);
        } elseif (count($search)) {
            return array($search_type => $search);
        } else {
            return array();
        }
    }

    /**
     * Translates a single Turba attribute to the driver-specific
     * counterpart. The translation is based on the contents of
     * $this->map. This ignores composite fields.
     *
     * @param string $attribute  The Turba attribute to translate.
     *
     * @return string  The driver name for this attribute.
     */
    function toDriver($attribute)
    {
        return isset($this->map[$attribute]) && !is_array($this->map[$attribute]) ? $this->map[$attribute] : null;
    }

    /**
     * Translates an array of hashes from being keyed on
     * driver-specific fields to being keyed on the generalized Turba
     * attributes. The translation is based on the contents of
     * $this->map.
     *
     * @param array $objects  Array of hashes using driver-specific keys.
     *
     * @return array  Translated version of $objects.
     */
    function toTurbaKeys($objects)
    {
        $attributes = array();
        foreach ($objects as $entry) {
            $new_entry = array();

            foreach ($this->map as $key => $val) {
                if (!is_array($val)) {
                    $new_entry[$key] = null;
                    if (isset($entry[$val]) && !empty($entry[$val]) && !is_null($entry[$val])) {
                        $new_entry[$key] = $entry[$val];
                    }
                }
            }

            $attributes[] = $new_entry;
        }
        return $attributes;
    }

    /**
     * Searches the source based on the provided criteria.
     *
     * TODO: Allow $criteria to contain the comparison operator (<, =, >,
     *       'like') and modify the drivers accordingly.
     *
     * @param $search_criteria   Hash containing the search criteria.
     * @param $sort_criteria     The requested sort order which is passed to
     *                           Turba_List::sort().
     * @param string $search_type  (optional) Do an AND or an OR search (defaults to AND).
     *
     * @return                   The sorted, filtered list of search results.
     */
    function &search($search_criteria, $sort_criteria = 'lastname',
                     $search_type = 'AND', $sort_direction = 0)
    {
        require_once TURBA_BASE . '/lib/List.php';
        require_once TURBA_BASE . '/lib/Object.php';

        /* If this is not a public source, enforce the requirement
         * that the source's owner must be equal to the current
         * user. */
        $strict_fields = array();
        if (!$this->public && !in_array(Auth::getAuth(), $this->admin)) {
            $search_criteria['__owner'] = Auth::getAuth();
            $strict_fields = array($this->toDriver('__owner') => true);
        }

        /* Add any fields that much match exactly for this source to
           the $strict_fields array. */
        foreach ($this->strict as $strict_field) {
            $strict_fields[$strict_field] = true;
        }

        /* Translate the Turba attributes to a driver-specific search
         * array. */
        $fields = $this->makeSearch($search_criteria, $search_type, $strict_fields);

        /* Retrieve the search results from the driver. */
        $results = $this->driver->search($fields, array_values($this->fields), $strict_fields);

        /* Translate the driver-specific fields in the result back to
         * the more generalized common Turba attributes using the
         * map. */
        $results = $this->toTurbaKeys($results);

        require_once TURBA_BASE . '/lib/Object.php';
        require_once TURBA_BASE . '/lib/Group.php';
        $list = &new Turba_List();
        foreach ($results as $attributes) {
            if (!empty($attributes['__type']) &&
                $attributes['__type'] == 'Group') {
                $list->insert(new Turba_Group($this, $attributes));
            } else {
                $list->insert(new Turba_Object($this, $attributes));
            }
        }
        $list->sort($sort_criteria, $sort_direction);

        /* Return the filtered (sorted) results. */
        return $list;
    }

    /**
     * Retrieve a set of objects from the source.
     *
     * @param array $objectIds  The unique ids of the objects to retrieve.
     *
     * @return array  The array of retrieved objects (Turba_AbstractObjects).
     */
    function &getObjects($objectIds)
    {
        require_once TURBA_BASE . '/lib/Object.php';
        $criteria = $this->map['__key'];

        $objects = $this->driver->read($criteria, $objectIds, array_values($this->fields));
        if (!is_array($objects)) {
            return PEAR::raiseError(_("Requested object not found."));
        }

        $results = array();
        $objects = $this->toTurbaKeys($objects);
        foreach ($objects as $object) {
            $done = false;
            if (!empty($object['__type'])) {
                $type = ucwords($object['__type']);
                $class = 'Turba_' . $type;
                if (!class_exists($class)) {
                    @require_once TURBA_BASE . '/lib/' . $type . '.php';
                }

                if (class_exists($class)) {
                    $results[] = &new $class($this, $object);
                    $done = true;
                }
            }
            if (!$done) {
                $results[] = &new Turba_Object($this, $object);
            }
        }

        return $results;
    }

    /**
     * Retrieve one object from the source.
     *
     * @param string $objectId  The unique id of the object to retrieve.
     *
     * @return object Turba_AbstractObject  The retrieved object.
     */
    function &getObject($objectId)
    {
        $result = &$this->getObjects(array($objectId));
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        } elseif (empty($result[0])) {
            return PEAR::raiseError('No results');
        } else {
            if (isset($this->map['__owner'])) {
                $result[0]->attributes['__owner'] = Auth::getAuth();
            }
            return $result[0];
        }
    }

    /**
     * Adds a new entry to the contact source.
     *
     * @param array $attributes  The attributes of the new object to add.
     *
     * @return mixed             The new __key value on success, or a
     *                           PEAR_Error object on failure.
     */
    function addObject($attributes)
    {
        if ($this->readonly) {
            return false;
        }

        // Always generate a new key.
        $attributes['__key'] = $this->driver->makeKey($this->toDriverKeys($attributes));

        if (!isset($attributes['__type'])) {
            $attributes['__type'] = 'Object';
        }
        if (isset($this->map['__owner'])) {
            $attributes['__owner'] = Auth::getAuth();
        }

        $key = $attributes['__key'];
        $attributes = $this->toDriverKeys($attributes);
        $result = $this->driver->addObject($attributes);

        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        /* Log the creation of this item in the history log. */
        $history = &Horde_History::singleton();
        $history->log($this->getGUID($key), array('action' => 'add'), true);

        return $key;
    }

    /**
     * Deletes the specified entry from the contact source.
     *
     * @param string $object_id     The ID of the object to delete.
     */
    function removeObject($object_id)
    {
        if ($this->readonly) {
            return false;
        }

        $result = $this->driver->removeObject($this->toDriver('__key'), $object_id);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        /* Log the deletion of this item in the history log. */
        $history = &Horde_History::singleton();
        $history->log($this->getGUID($object_id), array('action' => 'delete'), true);

        return true;
    }

    /**
     * Modifies an existing entry in the contact source.
     *
     * @param Turba_AbstractObject $object     The object to update.
     *
     * @return string  The object id, possibly updated.
     */
    function setObject($object)
    {
        if ($this->readonly) {
            return PEAR::raiseError(_("Address book is read-only."));
        }

        $attributes = $this->toDriverKeys($object->getAttributes());
        list($object_key, $object_id) = each($this->toDriverKeys(array('__key' => $object->getValue('__key'))));

        $object_id = $this->driver->setObject($object_key, $object_id, $attributes);
        if (is_a($object_id, 'PEAR_Error')) {
            return $object_id;
        }

        /* Log the modification of this item in the history log. */
        $history = &Horde_History::singleton();
        $history->log($this->getGUID($object_id), array('action' => 'modify'), true);

        return $object_id;
    }

    /**
     * Returns the criteria available for this source except '__key'.
     *
     * @return array  An array containing the criteria.
     */
    function getCriteria()
    {
        $criteria = $this->map;
        unset($criteria['__key']);
        return $criteria;
    }

    /**
     * Get a globally unique ID for a contact object.
     *
     * @param integer $objectId  The object id.
     *
     * @return string  A GUID referring to $objectId.
     */
    function getGUID($objectId)
    {
        return 'turba:' . $this->name . ':' . $objectId;
    }

    /**
     * Returns all non-composite fields for this source. Useful for
     * importing and exporting data, etc.
     *
     * @return array  The field list.
     */
    function getFields()
    {
        return array_flip($this->fields);
    }

    /**
     * Static method to contruct Turba_Source objects. Use this so
     * that we can return PEAR_Error objects if anything goes wrong.
     *
     * @param $name         String containing the internal name of this source.
     * @param $source       Array containing the configuration information for this source.
     */
    function &factory($name, $source)
    {
        $object = &new Turba_Source();

        $object->name = $name;
        $object->title = $source['title'];

        // Obtain a handle to a driver of the requested type. If an
        // instance of that driver doesn't already exist, a new one
        // will be created and returned.
        require_once TURBA_BASE . '/lib/Driver.php';
        $object->driver = &Turba_Driver::singleton($source['type'], $source['params']);
        $init = $object->driver->init();
        if (is_a($init, 'PEAR_Error')) {
            return $init;
        }

        /* Store and translate the map at the Source level. */
        $object->map = $source['map'];
        foreach ($object->map as $key => $val) {
            if (!is_array($val)) {
                $object->fields[$key] = $val;
            }
        }

        /* Store strict fields. */
        if (isset($source['strict'])) {
            $object->strict = $source['strict'];
        }

        /* Store admins. */
        if (isset($source['admin'])) {
            $object->admin = $source['admin'];
        }

        /* Set flags. */
        if (isset($source['public'])) {
            $object->public = $source['public'];
        }
        if (isset($source['readonly'])) {
            $object->readonly = $source['readonly'] &&
                (!isset($source['admin']) || !in_array(Auth::getAuth(), $source['admin']));
        }

        return $object;
    }

    /**
     * Attempts to return a reference to a concrete Turba_Source instance
     * based on $driver. It will only create a new instance if no
     * Turba_Source instance with the same parameters currently exists.
     *
     * This method must be invoked as: $source = &Turba_Source::singleton()
     *
     * @param $name         String containing the internal name of this source.
     * @param $source       Array containing the configuration information for this source.
     *
     * @return          The concrete Turba_Source reference, or false on an
     *                  error.
     */
    function &singleton($name, $source)
    {
        static $instances;

        if (!isset($instances)) {
            $instances = array();
        }

        $signature = serialize(array($name, $source));
        if (!isset($instances[$signature])) {
            $instances[$signature] = &Turba_Source::factory($name, $source);
        }

        return $instances[$signature];
    }

}
