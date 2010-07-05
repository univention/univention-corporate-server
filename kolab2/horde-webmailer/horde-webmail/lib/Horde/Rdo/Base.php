<?php
/**
 * @category Horde
 * @package Horde_Rdo
 */

/**
 * Horde_Rdo_Base abstract class (Rampage Data Objects). Entity
 * classes extend this baseline.
 *
 * @category Horde
 * @package Horde_Rdo
 */
abstract class Horde_Rdo_Base implements IteratorAggregate {

    /**
     * The Horde_Rdo_Mapper instance associated with this Rdo object. The
     * Mapper takes care of all backend access.
     *
     * @see Horde_Rdo_Mapper
     * @var Horde_Rdo_Mapper
     */
    protected $_mapper;

    /**
     * This object's fields.
     *
     * @var array
     */
    protected $_fields = array();

    /**
     * Constructor. Can be called directly by a programmer, or is
     * called in Horde_Rdo_Mapper::map(). Takes an associative array
     * of initial object values.
     *
     * @param array $fields Initial values for the new object.
     *
     * @see Horde_Rdo_Mapper::map()
     */
    public function __construct($fields = array())
    {
        $this->_fields = $fields;
    }

    /**
     * When Rdo objects are cloned, unset the unique id that
     * identifies them so that they can be modified and saved to the
     * backend as new objects. If you don't really want a new object,
     * don't clone.
     */
    public function __clone()
    {
        // @TODO Support composite primary keys
        unset($this->{$this->getMapper()->model->key});

        // @TODO What about associated objects?
    }

    /**
     * Fetch fields that haven't yet been loaded. Lazy-loaded fields
     * and lazy-loaded relationships are handled this way. Once a
     * field is retrieved, it is cached in the $_fields array so it
     * doesn't need to be fetched again.
     *
     * @param string $field The name of the field to access.
     *
     * @return mixed The value of $field or null.
     */
    public function __get($field)
    {
        // Honor any explicit getters.
        $fieldMethod = 'get' . ucfirst($field);
        // If an Rdo_Base subclass has a __call() method, is_callable
        // returns true on every method name, so use method_exists
        // instead.
        if (method_exists($this, $fieldMethod)) {
            return call_user_func(array($this, $fieldMethod));
        }

        if (isset($this->_fields[$field])) {
            return $this->_fields[$field];
        }

        $mapper = $this->getMapper();

        // Look for lazy fields first, then relationships.
        if (in_array($field, $mapper->lazyFields)) {
            // @TODO Support composite primary keys
            $query = new Horde_Rdo_Query($mapper);
            $query->setFields($field)
                  ->addTest($mapper->model->key, '=', $this->{$mapper->model->key});
            $this->_fields[$field] = $mapper->adapter->queryOne($query);
            return $this->_fields[$field];
        } elseif (isset($mapper->lazyRelationships[$field])) {
            $rel = $mapper->lazyRelationships[$field];
        } else {
            return null;
        }

        // Try to find the Mapper class for the object the
        // relationship is with, and fail if we can't.
        if (isset($rel['mapper'])) {
            $m = new $rel['mapper']();
        } else {
            $m = $mapper->inflector->tableToMapper($field);
            if (is_null($m)) {
                return null;
            }
        }

        // Based on the kind of relationship, fetch the appropriate
        // objects and fill the cache.
        switch ($rel['type']) {
        case Horde_Rdo::ONE_TO_ONE:
        case Horde_Rdo::MANY_TO_ONE:
            if (isset($rel['query'])) {
                $query = $this->_fillPlaceholders($rel['query']);
                $this->_fields[$field] = $m->find(Horde_Rdo::FIND_ONE, $query);
            } else {
                $this->_fields[$field] = $m->find($this->{$rel['foreignKey']});
            }
            break;

        case Horde_Rdo::ONE_TO_MANY:
            $this->_fields[$field] = $this->cache($field,
                $m->find(Horde_Rdo::FIND_ALL,
                         array($rel['foreignKey'] => $this->{$rel['foreignKey']})));
            break;

        case Horde_Rdo::MANY_TO_MANY:
            $key = $mapper->model->key;
            $query = new Horde_Rdo_Query();
            $on = isset($rel['on']) ? $rel['on'] : $m->model->key;
            $query->addRelationship($field, array('mapper' => $mapper,
                                                     'table' => $rel['through'],
                                                     'type' => Horde_Rdo::MANY_TO_MANY,
                                                     'query' => array($on => new Horde_Rdo_Query_Literal($on), $key => $this->$key)));
            $this->_fields[$field] = $m->find(Horde_Rdo::FIND_ALL, $query);
            break;

        case Horde_Rdo::CUSTOM:
            $query = array();
            $rel['query'] = $this->_fillPlaceholders($rel['query']);

            foreach ($rel['on'] as $field => $value) {
                if (preg_match('/^@(.*)@$/', $value, $matches)) {
                    $query[$field] = $this->{$matches[1]};
                } else {
                    $query[$field] = $value;
                }
            }
            $this->_fields[$field] = $m->find($rel['mode'], $query);
            break;
        }

        return $this->_fields[$field];
    }

    /**
     * Set a field's value.
     *
     * @param string $field The field to set
     * @param mixed $value The field's new value
     */
    public function __set($field, $value)
    {
        // Honor any explicit setters.
        $fieldMethod = 'set' . ucfirst($field);
        // If an Rdo_Base subclass has a __call() method, is_callable
        // returns true on every method name, so use method_exists
        // instead.
        if (method_exists($this, $fieldMethod)) {
            return call_user_func(array($this, $fieldMethod), $value);
        }

        $this->_fields[$field] = $value;
    }

    /**
     * Allow using isset($rdo->foo) to check for field or
     * relationship presence.
     *
     * @param string $field The field name to check existence of.
     */
    public function __isset($field)
    {
        $m = $this->getMapper();
        return isset($m->fields[$field])
            || isset($m->lazyFields[$field])
            || isset($m->relationships[$field])
            || isset($m->lazyRelationships[$field]);
    }

    /**
     * Allow using unset($rdo->foo) to unset a basic
     * field. Relationships cannot be unset in this way.
     *
     * @param string $field The field name to unset.
     */
    public function __unset($field)
    {
        // @TODO Should unsetting a MANY_TO_MANY relationship remove
        // the relationship?
        unset($this->_fields[$field]);
    }

    /**
     * Implement the IteratorAggregate interface. Looping over an Rdo
     * object goes through each property of the object in turn.
     *
     * @return Horde_Rdo_Iterator The Iterator instance.
     */
    public function getIterator()
    {
        return new Horde_Rdo_Iterator($this);
    }

    /**
     * Get a Mapper instance that can be used to manage this
     * object. The Mapper instance can come from a few places:
     *
     * - If the class <RdoClassName>Mapper exists, it will be used
     *   automatically.
     *
     * - Any Rdo instance created with Horde_Rdo_Mapper::map() will have a
     *   $mapper object set automatically.
     *
     * - Subclasses can override getMapper() to return the correct
     *   mapper object.
     *
     * - The programmer can call $rdoObject->setMapper($mapper) to provide a
     *   mapper object.
     *
     * A Horde_Rdo_Exception will be thrown if none of these
     * conditions are met.
     *
     * @return Horde_Rdo_Mapper The Mapper instance managing this object.
     */
    public function getMapper()
    {
        if (!$this->_mapper) {
            $class = get_class($this) . 'Mapper';
            if (class_exists($class)) {
                $this->_mapper = new $class();
            } else {
                throw new Horde_Rdo_Exception('No Horde_Rdo_Mapper object found. Override getMapper() or define the ' . get_class($this) . 'Mapper class.');
            }
        }

        return $this->_mapper;
    }

    /**
     * Associate this Rdo object with the Mapper instance that will
     * manage it. Called automatically by Horde_Rdo_Mapper:map().
     *
     * @param Horde_Rdo_Mapper $mapper The Mapper to manage this Rdo object.
     *
     * @see Horde_Rdo_Mapper::map()
     */
    public function setMapper($mapper)
    {
        $this->_mapper = $mapper;
    }

    /**
     * Save any changes to the backend.
     *
     * @return boolean Success.
     */
    public function save()
    {
        return $this->getMapper()->update($this) == 1;
    }

    /**
     * Delete this object from the backend.
     *
     * @return boolean Success or failure.
     */
    public function delete()
    {
        return $this->getMapper()->delete($this) == 1;
    }

    /**
     * Take a query array and replace @field@ placeholders with values
     * from this object.
     *
     * @param array $query The query to process placeholders on.
     *
     * @return array The query with placeholders filled in.
     */
    protected function _fillPlaceholders($query)
    {
        foreach (array_keys($query) as $field) {
            $value = $query[$field];
            if (preg_match('/^@(.*)@$/', $value, $matches)) {
                $query[$field] = $this->{$matches[1]};
            }
        }

        return $query;
    }

}
