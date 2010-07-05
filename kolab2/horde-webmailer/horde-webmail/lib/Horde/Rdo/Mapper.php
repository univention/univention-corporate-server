<?php
/**
 * Rdo Mapper base class.
 *
 * @category Horde
 * @package Horde_Rdo
 */

/**
 * Rdo Mapper class. Controls mapping of entity obects (instances of
 * Horde_Rdo_Base) from and to Horde_Rdo_Adapters.
 *
 * Public properties:
 *   $adapter - Horde_Rdo_Adapter that stores this Mapper's objects.
 *
 *   $inflector - Horde_Rdo_Inflector object for doing table name to
 *   class name, class name to table name, etc. conversions.
 *
 *   $model - The Horde_Rdo_Model object describing the main table of
 *   this entity.
 *
 * @category Horde
 * @package Horde_Rdo
 */
abstract class Horde_Rdo_Mapper implements Countable {

    /**
     * If this is true and fields named created and updated are
     * present, Rdo will automatically set creation and last updated
     * timestamps. Timestamps are always GMT for portability.
     *
     * @var boolean
     */
    protected $_setTimestamps = true;

    /**
     * What class should this Mapper create for objects? Defaults to
     * the Mapper subclass' name minus "Mapper". So if the Rdo_Mapper
     * subclass is UserMapper, it will default to trying to create
     * User objects.
     *
     * @var string
     */
    protected $_classname;

    /**
     * The name of the database table (or view, etc.) that holds this
     * Mapper's objects.
     *
     * @var string
     */
    protected $_table;

    /**
     * Fields that should only be read from the database when they are
     * accessed.
     *
     * @var array
     */
    protected $_lazyFields = array();

    /**
     * Relationships for this entity.
     *
     * @var array
     */
    protected $_relationships = array();

    /**
     * Relationships that should only be read from the database when
     * they are accessed.
     *
     * @var array
     */
    protected $_lazyRelationships = array();

    /**
     * Default sorting rules to use for all queries made with this
     * mapper. Each element of this array can either be a tuple (a
     * single numerically indexed array) of a field name followed by a
     * sort order (Horde_Rdo::SORT_ASC or Horde_Rdo::SORT_DESC), or
     * just a field name. If just a field name is specified the
     * default sorting order (ascending) will be used.
     *
     * @var array
     */
    protected $_defaultSortRules;

    /**
     * Provide read-only, on-demand access to several properties. This
     * method will only be called for properties that aren't already
     * present; once a property is fetched once it is cached and
     * returned directly on any subsequent access.
     *
     * These properties are available:
     *
     * adapter: The Horde_Rdo_Adapter this mapper is using to talk to
     * the database.
     *
     * inflector: The Horde_Rdo_Inflector this mapper uses to
     * translate between PHP class, database table, and database
     * field/key names.
     *
     * model: The Horde_Rdo_Model object describing the table or view
     * this Mapper manages.
     *
     * fields: Array of all field names that are loaded up front
     * (eager loading) from the Model.
     *
     * lazyFields: Array of fields that are only loaded when accessed.
     *
     * relationships: Array of relationships to other Models.
     *
     * lazyRelationships: Array of relationships to other Models which
     * are only loaded when accessed.
     *
     * @param string $key Property name to fetch
     *
     * @return mixed Value of $key
     */
    public function __get($key)
    {
        switch ($key) {
        case 'adapter':
            $this->adapter = $this->getAdapter();
            return $this->adapter;

        case 'inflector':
            return Horde_Rdo::getInflector();

        case 'model':
            $this->model = new Horde_Rdo_Model;
            if ($this->_table) {
                $this->model->table = $this->_table;
            } else {
                $this->model->table = $this->inflector->mapperToTable($this);
            }
            $this->model->load($this);
            return $this->model;

        case 'fields':
            $this->fields = array_diff($this->model->listFields(), $this->_lazyFields);
            return $this->fields;

        case 'lazyFields':
        case 'relationships':
        case 'lazyRelationships':
        case 'defaultSortRules':
            return $this->{'_' . $key};
        }

        return null;
    }

    /**
     * Associate an adapter with this mapper. Not needed in the
     * general case if getAdapter() is overridden in the concrete
     * Mapper implementation.
     *
     * @param Horde_Rdo_Adapter $adapter Horde_Rdo_Adapter to store objects.
     *
     * @see getAdapter()
     */
    public function setAdapter($adapter)
    {
        $this->adapter = $adapter;
    }

    /**
     * getAdapter() must be overridden by Horde_Rdo_Mapper subclasses
     * if they don't provide $adapter in some other way (by calling
     * setAdapter() or on construction, for example), and there is no
     * global Adapter.
     *
     * @see setAdapter()
     *
     * @return Horde_Rdo_Adapter The adapter for storing this Mapper's objects.
     */
    public function getAdapter()
    {
        $adapter = Horde_Rdo::getAdapter();
        if ($adapter) {
            return $adapter;
        }
        throw new Horde_Rdo_Exception('You must override getAdapter(), assign a Horde_Rdo_Adapter by calling setAdapter(), or set a global adapter by calling Horde_Rdo::setAdapter().');
    }

    /**
     * Create an instance of $this->_classname from a set of data.
     *
     * @param array $fields Field names/default values for the new object.
     *
     * @see $_classname
     *
     * @return Horde_Rdo_Base An instance of $this->_classname with $fields
     * as initial data.
     */
    public function map($fields = array())
    {
        // Guess a classname if one isn't explicitly set.
        if (!$this->_classname) {
            $this->_classname = $this->inflector->mapperToEntity($this);
        }

        $relationships = array();
        foreach ($fields as $fieldName => $fieldValue) {
            if (strpos($fieldName, '@') !== false) {
                list($rel, $field) = explode('@', $fieldName, 2);
                $relationships[$rel][$field] = $fieldValue;
                unset($fields[$fieldName]);
            }
        }

        $o = new $this->_classname($fields);
        $o->setMapper($this);

        if (count($relationships)) {
            foreach ($this->relationships as $relationship => $rel) {
                if (isset($rel['mapper'])) {
                    $m = new $rel['mapper']();
                } else {
                    $m = $this->inflector->tableToMapper($relationship);
                    if (is_null($m)) {
                        // @TODO Throw an exception?
                        continue;
                    }
                }

                if (isset($relationships[$m->model->table])) {
                    $o->$relationship = $m->map($relationships[$m->model->table]);
                }
            }
        }

        if (is_callable(array($o, 'afterMap'))) {
            $o->afterMap();
        }

        return $o;
    }

    /**
     * Count objects that match $query.
     *
     * @param mixed $query The query to count matches of.
     *
     * @return integer All objects matching $query.
     */
    public function count($query = null)
    {
        return $this->adapter->count($query, $this);
    }

    /**
     * Check if at least one object matches $query.
     *
     * @param mixed $query Either a primary key, an array of keys
     *                     => values, or an Horde_Rdo_Query object.
     *
     * @return boolean True or false.
     */
    public function exists($query)
    {
        return (bool)$this->adapter->exists($query, $this);
    }

    /**
     * Create a new object in the backend with $fields as initial values.
     *
     * @param array $fields Array of field names => initial values.
     *
     * @return Horde_Rdo_Base The newly created object.
     */
    public function create($fields)
    {
        // If configured to record creation and update times, set them
        // here. We set updated to the initial creation time so it's
        // always set.
        if ($this->_setTimestamps) {
            $time = gmmktime();
            $fields['created'] = $time;
            $fields['updated'] = $time;
        }

        // Filter out any extra fields.
        $fields = array_intersect_key($fields, $this->model->getFields());

        $id = $this->adapter->create($this, $fields);
        return $this->map(array_merge(array($this->model->key => $id),
                                      $fields));
    }

    /**
     * Updates a record in the backend. $object can be either a
     * primary key or an Rdo object. If $object is an Rdo instance
     * then $fields will be ignored as values will be pulled from the
     * object.
     *
     * @param string|Rdo $object The Rdo instance or unique id to update.
     * @param array $fields If passing a unique id, the array of field properties
     *                      to set for $object.
     *
     * @return integer Number of objects updated.
     */
    public function update($object, $fields = null)
    {
        if ($object instanceof Horde_Rdo_Base) {
            $key = $this->model->key;
            $id = $object->$key;
            $fields = iterator_to_array($object);

            if (!$id) {
                // Object doesn't exist yet; create it instead.
                $object = $this->create($fields);
                return 1;
            }
        } else {
            $id = $object;
        }

        // If configured to record update time, set it here.
        if ($this->_setTimestamps) {
            $fields['updated'] = gmmktime();
        }

        // Filter out any extra fields.
        $fields = array_intersect_key($fields, $this->model->getFields());

        return $this->adapter->update($this, $id, $fields);
    }

    /**
     * Deletes a record from the backend. $object can be either a
     * primary key, an Rdo_Query object, or an Rdo object.
     *
     * @param string|Horde_Rdo_Base|Horde_Rdo_Query $object The Rdo object,
     * Horde_Rdo_Query, or unique id to delete.
     *
     * @return integer Number of objects deleted.
     */
    public function delete($object)
    {
        if ($object instanceof Horde_Rdo_Base) {
            $key = $this->model->key;
            $id = $object->$key;
            $query = array($key => $id);
        } elseif ($object instanceof Horde_Rdo_Query) {
            $query = $object;
        } else {
            $key = $this->model->key;
            $query = array($key => $object);
        }

        return $this->adapter->delete($this, $query);
    }

    /**
     * Find can be called in several ways.
     *
     * Primary key mode: pass find() a single primary key or an array
     * of primary keys, and it will return either a single object or a
     * Horde_Rdo_List of objects matching those primary keys.
     *
     * Find mode: otherwise the first argument to find should be a
     * find mode. The defaults modes are Rdo::FIND_FIRST (returns the
     * first object matching the rest of the query), and Rdo::FIND_ALL
     * (return a Horde_Rdo_List of all matches).
     *
     * When using a find mode, the second argument can be blank (find
     * all objects or the first object depending on find mode), an
     * associative array (keys are fields, values are the values those
     * fields must match exactly), or an Rdo_Query object, which
     * defines arbitrarily complex find rules.
     */
    public function find()
    {
        $argc = func_num_args();
        $argv = func_get_args();

        // Make sure we have some sort of find query.
        if (!$argc) {
            throw new Horde_Rdo_Exception('find() called with no arguments');
        }

        // Figure out what kind of query we have.
        if ($argc == 1) {
            if ($argv[0] == Horde_Rdo::FIND_FIRST ||
                $argv[0] == Horde_Rdo::FIND_ALL) {
                // Using a find mode with no query.
                $mode = array_shift($argv);
                $query = null;
            } else {
                // Find the name of our primary key.
                $key = $this->model->key;

                if (is_null($argv[0])) {
                    $query = new Horde_Rdo_Query();
                    $mode = Horde_Rdo::FIND_FIRST;
                } elseif (is_scalar($argv[0])) {
                    // Looking for one primary key. We'll just return
                    // the corresponding object, or throw an
                    // exception.
                    $mode = Horde_Rdo::FIND_FIRST;
                    $query = array($key => $argv[0]);
                } else {
                    // Looking for several primary keys. Build an OR
                    // search for them. We'll return a Horde_Rdo_List
                    // that iterates over them.
                    $mode = Horde_Rdo::FIND_ALL;
                    $query = new Horde_Rdo_Query();
                    $query->combineWith('OR');
                    foreach ($argv[0] as $id) {
                        $query->addTest($key, '=', $id);
                    }
                }
            }
        } else {
            // Using a find mode with arbitrary query.
            $mode = array_shift($argv);
            $query = array_shift($argv);
        }

        // Build a full Query object.
        $query = Horde_Rdo_Query::create($query, $this);

        // If we only want one result, make sure we don't get more.
        if ($mode == Horde_Rdo::FIND_FIRST) {
            $query->limit(1);
        }

        $list = new Horde_Rdo_List($query);

        // The adapter's find() method can limit results (if we're
        // using Horde_Rdo::FIND_FIRST) but will always return a
        // collection to remain simpler. We take care of returning
        // either the collection or a single object here.
        switch ($mode) {
        case Horde_Rdo::FIND_FIRST:
            return $list->current();

        case Horde_Rdo::FIND_ALL:
            return $list;

        default:
            throw new Horde_Rdo_Exception('Unknown find mode ' . $mode);
        }
    }

    /**
     * Set a default sort field and order for all queries done with
     * this Mapper.
     *
     * @param string $field Field to sort by
     * @param constant $direction Sort ascending (Horde_Rdo::SORT_ASC)
     * or descending (Horde_Rdo::SORT_DESC). Defaults to ascending.
     */
    public function sortBy($field, $direction = Horde_Rdo::SORT_ASC)
    {
        $this->_defaultSortRules[] = array($field, $direction);
        return $this;
    }

}
