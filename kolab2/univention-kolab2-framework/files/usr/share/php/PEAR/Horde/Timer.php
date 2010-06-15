<?php
/**
 * Horde_Timer
 *
 * Simpler interface for timing operations/actions.
 *
 * $Horde: framework/Timer/Timer.php,v 1.4 2003/11/06 19:44:07 chuck Exp $
 *
 * @package Horde_Timer
 * @since   Horde 3.0
 * @version $Revision: 1.1.2.1 $
 */
class Horde_Timer {

    var $_start = array();
    var $_idx = 0;

    /**
     * Push a new timer start on stack.
     */
    function push()
    {
        list($ms, $s) = explode(' ', microtime());
        $this->_start[$this->_idx++] = floor($ms * 1000) + 1000 * $s;
    }

    /**
     * Pop the latest timer start and return the difference with the
     * current time.
     */
    function pop()
    {
        assert($this->_idx > 0);
        list($ms, $s) = explode(' ', microtime());
        $etime = floor($ms * 1000) + (1000 * $s);
        $this->_idx--;
        return $etime - $this->_start[$this->_idx];
    }

    /**
     * Return a reference to a global Horde_Timer engine.
     */
    function &singleton()
    {
        static $timer;

        if (!isset($timer)) {
            $timer = new Horde_Timer();
        }

        return $timer;
    }

}
