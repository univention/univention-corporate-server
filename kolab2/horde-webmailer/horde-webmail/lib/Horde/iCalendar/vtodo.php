<?php
/**
 * Class representing vTodos.
 *
 * $Horde: framework/iCalendar/iCalendar/vtodo.php,v 1.13.10.9 2009-01-06 15:23:53 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @since   Horde 3.0
 * @package Horde_iCalendar
 */
class Horde_iCalendar_vtodo extends Horde_iCalendar {

    function getType()
    {
        return 'vTodo';
    }

    function exportvCalendar()
    {
        return parent::_exportvData('VTODO');
    }

    /**
     * Convert this todo to an array of attributes.
     *
     * @return array  Array containing the details of the todo in a hash
     *                as used by Horde applications.
     */
    function toArray()
    {
        $todo = array();

        $name = $this->getAttribute('SUMMARY');
        if (!is_array($name) && !is_a($name, 'PEAR_Error')) {
            $todo['name'] = $name;
        }
        $desc = $this->getAttribute('DESCRIPTION');
        if (!is_array($desc) && !is_a($desc, 'PEAR_Error')) {
            $todo['desc'] = $desc;
        }

        $priority = $this->getAttribute('PRIORITY');
        if (!is_array($priority) && !is_a($priority, 'PEAR_Error')) {
            $todo['priority'] = $priority;
        }

        $due = $this->getAttribute('DTSTAMP');
        if (!is_array($due) && !is_a($due, 'PEAR_Error')) {
            $todo['due'] = $due;
        }

        return $todo;
    }

    /**
     * Set the attributes for this todo item from an array.
     *
     * @param array $todo  Array containing the details of the todo in
     *                     the same format that toArray() exports.
     */
    function fromArray($todo)
    {
        if (isset($todo['name'])) {
            $this->setAttribute('SUMMARY', $todo['name']);
        }
        if (isset($todo['desc'])) {
            $this->setAttribute('DESCRIPTION', $todo['desc']);
        }

        if (isset($todo['priority'])) {
            $this->setAttribute('PRIORITY', $todo['priority']);
        }

        if (isset($todo['due'])) {
            $this->setAttribute('DTSTAMP', $todo['due']);
        }
    }

}
