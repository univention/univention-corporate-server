<?php
/**
 * IMAP_Thread provides functions for working with imap_thread() output.
 *
 * $Horde: framework/IMAP/IMAP/Thread.php,v 1.4.10.19 2009-01-06 15:23:11 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@curecanti.org>
 * @since   Horde 3.0
 * @package Horde_IMAP
 */
class IMAP_Thread {

    /**
     * Internal thread data structure.
     *
     * @var array
     */
    var $_thread = array();

    /**
     * Array index to Message index lookup array.
     *
     * @var array
     */
    var $_lookup = array();

    /**
     * Constructor.
     *
     * @param array $ob  Output from imap_thread().
     */
    function IMAP_Thread($ob)
    {
        $this->_processStructure($ob);
    }

   /**
     * Gets the indention level for an IMAP message index.
     *
     * @param integer $index  The IMAP message index.
     *
     * @return mixed  Returns the thread indent level if $index found.
     *                Returns false on failure.
     */
    function getThreadIndent($index)
    {
        $key = $this->_getKey($index);
        return (!is_null($key) && isset($this->_thread[$key]['level']))
            ? $this->_thread[$key]['level']
            : false;
    }

    /**
     * Gets the base thread index for an IMAP message index.
     *
     * @param integer $index  The IMAP message index.
     *
     * @return mixed  Returns the base IMAP index if $index is part of a
     *                thread.
     *                Returns false on failure.
     */
    function getThreadBase($index)
    {
        $key = $this->_getKey($index);
        return (!is_null($key) && !empty($this->_thread[$key]['base']))
            ? $this->_thread[$key]['base']
            : false;
    }

    /**
     * Is this index the last in the current level?
     *
     * @param integer $index  The IMAP message index.
     *
     * @return boolean  Returns true if $index is the last element in the
     *                  current thread level.
     *                  Returns false if not, or on failure.
     */
    function lastInLevel($index)
    {
        $key = $this->_getKey($index);
        return (!is_null($key) && !empty($this->_thread[$key]['last']))
            ? $this->_thread[$key]['last']
            : false;
    }

    /**
     * Do the message index -> array index lookup.
     *
     * @access private
     *
     * @param integer $index  The IMAP message index.
     *
     * @return mixed  The array index value or null if no index.
     */
    function _getKey($index)
    {
        return (isset($this->_lookup[$index])) ? $this->_lookup[$index] : null;
    }

    /**
     * Return the sorted list of messages indices.
     *
     * @param boolean $new  True for newest first, false for oldest first.
     *
     * @return array  The sorted list of messages.
     */
    function messageList($new)
    {
        return ($new) ? array_reverse(array_keys($this->_lookup)) : array_keys($this->_lookup);
    }

    /**
     * Returns the list of messages in the current thread.
     *
     * @param integer $index  The IMAP index of the current message.
     *
     * @return array  A list of IMAP message indices.
     */
    function getThread($index)
    {
        /* Find the beginning of the thread. */
        $begin = $this->getThreadBase($index);
        $key = $this->_getKey($begin);
        if (is_null($key) || empty($begin)) {
            return array($index);
        }

        /* Work forward from the first thread element to find the end of the
         * thread. */
        $thread_list = array($this->_thread[$key]['index']);
        while (++$key) {
            if (!isset($this->_thread[$key])) {
                break;
            }
            $curr = $this->_thread[$key];
            if ($curr['base'] == $begin) {
                $thread_list[] = $this->_thread[$key]['index'];
            } else {
                break;
            }
        }

        return $thread_list;
    }

    /**
     * Process the output from imap_thread() into an internal data structure.
     *
     * @access private
     *
     * @param array $ob  Output from imap_thread().
     */
    function _processStructure($ob)
    {
        $container = $container_base = $last_index = $thread_base = $thread_base_idx = null;
        $indices = array();
        $i = $last_i = $level = 0;

        reset($ob);
        while (list($key, $val) = each($ob)) {
            $pos = strpos($key, '.');
            $index = substr($key, 0, $pos);
            $type = substr($key, $pos + 1);

            switch ($type) {
            case 'num':
                if ($val === 0) {
                    $container = $index;
                } else {
                    ++$i;
                    if (is_null($container) && empty($level)) {
                        $thread_base = $val;
                        $thread_base_idx = $index;
                    }
                    $this->_lookup[$val] = $index;
                    $this->_thread[$index] = array(
                        'index' => $val
                    );
                }
                break;

            case 'next':
                if (!is_null($container) && ($container === $index)) {
                    $container_base = $ob[$val . '.num'];
                } else {
                    $this->_thread[$index]['base'] = (!is_null($container))
                        ? $container_base
                        : ((!empty($level) || ($val != 0)) ? $thread_base : null);
                    ++$i;
                    ++$level;
                }
                break;

            case 'branch':
                if ($container === $index) {
                    $container = $container_base = null;
                    $this->_thread[$last_index]['last'] = true;
                } else {
                    $this->_thread[$index]['level'] = $level--;
                    $this->_thread[$index]['last'] = !(!is_null($container) && empty($level));
                    if ($index === $thread_base_idx) {
                        $index = null;
                    } elseif (!empty($level) &&
                              !is_null($last_index) &&
                              isset($this->_thread[$last_index])) {
                        $this->_thread[$last_index]['last'] = ($last_i == ($i - 1));
                    }
                }
                $last_index = $index;
                $last_i = $i++;
                break;
            }
        }
    }

}
