<?php
/**
 * @category Horde
 * @package Horde_Rdo
 */

/**
 * Iterator for Horde_Rdo_Base objects that allows relationships and
 * decorated objects to be handled gracefully.
 *
 * @category Horde
 * @package Horde_Rdo
 */
class Horde_Rdo_Iterator implements Iterator {

    /**
     * @var Horde_Rdo_Base
     */
    private $_rdo;

    /**
     * List of keys that we'll iterator over. This is the combined
     * list of the fields, lazyFields, relationships, and
     * lazyRelationships properties from the objects Horde_Rdo_Mapper.
     */
    private $_keys = array();

    /**
     * Current index
     *
     * @var mixed
     */
    private $_index = null;

    /**
     * Are we inside the array bounds?
     *
     * @var boolean
     */
    private $_valid = false;

    /**
     * New Horde_Rdo_Iterator for iterating over Rdo objects.
     *
     * @param Horde_Rdo_Base $rdo The object to iterate over
     */
    public function __construct($rdo)
    {
        $this->_rdo = $rdo;

        $m = $rdo->getMapper();
        $this->_keys = array_merge($m->fields,
                                   $m->lazyFields,
                                   array_keys($m->relationships),
                                   array_keys($m->lazyRelationships));
    }

    /**
     * Reset to the first key.
     */
    public function rewind()
    {
        $this->_valid = (false !== reset($this->_keys));
    }

    /**
     * Return the current value.
     *
     * @return mixed The current value
     */
    public function current()
    {
        $key = $this->key();
        return $this->_rdo->$key;
    }

    /**
     * Return the current key.
     *
     * @return mixed The current key
     */
    public function key()
    {
        return current($this->_keys);
    }

    /**
     * Move to the next key in the iterator.
     */
    public function next()
    {
        $this->_valid = (false !== next($this->_keys));
    }

    /**
     * Check array bounds.
     *
     * @return boolean Inside array bounds?
     */
    public function valid()
    {
        return $this->_valid;
    }

}
