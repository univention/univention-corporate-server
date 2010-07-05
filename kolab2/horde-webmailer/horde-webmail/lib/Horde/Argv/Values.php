<?php
/**
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @author   Mike Naberezny <mike@maintainable.com>
 * @license  http://opensource.org/licenses/bsd-license.php BSD
 * @category Horde
 * @package  Horde_Argv
 */

/**
 * Result hash for Horde_Argv_Parser
 *
 * @category Horde
 * @package  Horde_Argv
 */
class Horde_Argv_Values implements IteratorAggregate, ArrayAccess, Countable
{
    public function __construct($defaults = array())
    {
        foreach ($defaults as $attr => $val) {
            $this->$attr = $val;
        }
    }

    public function __toString()
    {
        $str = array();
        foreach ($this as $attr => $val) {
            $str[] = $attr . ': ' . (string)$val;
        }
        return implode(', ', $str);
    }

    public function offsetExists($attr)
    {
        return !is_null($this->$attr);
    }

    public function offsetGet($attr)
    {
        return $this->$attr;
    }

    public function offsetSet($attr, $val)
    {
        $this->$attr = $val;
    }

    public function offsetUnset($attr)
    {
        unset($this->$attr);
    }

    public function getIterator()
    {
        return new ArrayIterator(get_object_vars($this));
    }

    public function count()
    {
        return count(get_object_vars($this));
    }

    public function ensureValue($attr, $value)
    {
        if (is_null($this->$attr)) {
            $this->$attr = $value;
        }
        return $this->$attr;
    }

}
