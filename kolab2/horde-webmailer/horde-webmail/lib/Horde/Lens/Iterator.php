<?php
/**
 * $Horde: framework/Lens/lib/Horde/Lens/Iterator.php,v 1.1.2.1 2008-05-15 22:01:06 chuck Exp $
 *
 * This set of classes implements a Flyweight pattern
 * (http://en.wikipedia.org/wiki/Flyweight_pattern). Refactor/rename
 * some based on this fact?
 *
 * @package Horde_Lens
 */

/**
 */
class Horde_Lens_Iterator implements OuterIterator {

    /**
     * The Iterator to decorate.
     * @var Iterator
     */
    private $_i;

    /**
     * The Decorator that will observe each element of the iterator.
     * @var Horde_Lens_Interface
     */
    protected $_d;

    /**
     * Constructs a decorator around an iterator using a single
     * Horde_Lens_Interface object, which decorates the current()
     * element of the iterator. The decorator is like a lens,
     * decotrating one element at a time, instead of having a
     * decorator for every element in the list.
     *
     * @param Iterator $i The iterator to decorate.
     */
    public function __construct(Iterator $i, $d = null)
    {
        $this->_i = $i;
        if ($d !== null) {
            $this->setLens($d);
        }
    }

    /**
     * Set or change the Lens modifying the inner iterator. Sets the
     * current object of the lens automatically and returns the lens.
     */
    public function setLens(Horde_Lens_Interface $d)
    {
        $this->_d = $d;
        return $this->current();
    }

    /**
     * Rewind the inner iterator.
     */
    function rewind()
    {
        $this->_i->rewind();
    }

    /**
     * Move to next element.
     *
     * @return void
     */
    function next()
    {
        $this->_i->next();
    }

    /**
     * @return Whether more elements are available.
     */
    function valid()
    {
        return $this->_i->valid();
    }

    /**
     * @return The current key.
     */
    function key()
    {
        return $this->_i->key();
    }

    /**
     * @return The current value.
     */
    function current()
    {
        return $this->_d->decorate($this->_i->current());
    }

    /**
     * @return Iterator The inner iterator.
     */
    function getInnerIterator()
    {
        return $this->_i;
    }

    /**
     * Aggregate the inner iterator.
     *
     * @param func    Name of method to invoke.
     * @param params  Array of parameters to pass to method.
     */
    function __call($func, $params)
    {
        return call_user_func_array(array($this->_i, $func), $params);
    }

}
