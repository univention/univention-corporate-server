<?php
/**
 * Implementation for tasks in the Kolab XML format.
 *
 * $Horde: framework/Kolab_Format/lib/Horde/Kolab/Format/XML/task.php,v 1.2.2.6 2008-12-12 11:39:04 wrobel Exp $
 *
 * @package Kolab_Format
 */

/**
 * Kolab XML handler for task groupware objects.
 *
 * $Horde: framework/Kolab_Format/lib/Horde/Kolab/Format/XML/task.php,v 1.2.2.6 2008-12-12 11:39:04 wrobel Exp $
 *
 * Copyright 2007-2008 Klarälvdalens Datakonsult AB
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @since   Horde 3.2
 * @author  Thomas Jarosch <thomas.jarosch@intra2net.com>
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @package Kolab_Format
 */
class Horde_Kolab_Format_XML_task extends Horde_Kolab_Format_XML {
    /**
     * Specific data fields for the note object
     *
     * @var array
     */
    var $_fields_specific;

    /**
     * Constructor
     */
    function Horde_Kolab_Format_XML_task()
    {
        $this->_root_name = 'task';

        /** Specific task fields, in kolab format specification order
         */
        $this->_fields_specific = array(
            'summary' => array(
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_DEFAULT,
                'default' => '',
            ),
            'location' => array(
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_DEFAULT,
                'default' => '',
            ),
            'creator'   => $this->_fields_simple_person,
            'organizer' => $this->_fields_simple_person,
            'start-date' => array(
                'type'    => HORDE_KOLAB_XML_TYPE_DATE_OR_DATETIME,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'alarm' => array(
                'type'    => HORDE_KOLAB_XML_TYPE_INTEGER,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'recurrence' => array(
                'type'    => HORDE_KOLAB_XML_TYPE_COMPOSITE,
                'value'   => HORDE_KOLAB_XML_VALUE_CALCULATED,
                'load'    => 'Recurrence',
                'save'    => 'Recurrence',
            ),
            'attendee' => $this->_fields_attendee,
            'priority' => array(
                'type'    => HORDE_KOLAB_XML_TYPE_INTEGER,
                'value'   => HORDE_KOLAB_XML_VALUE_DEFAULT,
                'default' => 3,
            ),
            'completed' => array(
                'type'    => HORDE_KOLAB_XML_TYPE_INTEGER,
                'value'   => HORDE_KOLAB_XML_VALUE_DEFAULT,
                'default' => 0,
            ),
            'status' => array(
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_DEFAULT,
                'default' => 'not-started',
            ),
            'due-date' => array(
                'type'    => HORDE_KOLAB_XML_TYPE_DATE_OR_DATETIME,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'parent' => array(
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            // These are not part of the Kolab specification but it is
            // ok if the client supports additional entries
            'estimate' => array(
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'completed_date' => array(
                'type'    => HORDE_KOLAB_XML_TYPE_DATE_OR_DATETIME,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
        );

        parent::Horde_Kolab_Format_XML();
    }

    /**
     * Load the groupware object based on the specifc XML values.
     *
     * @param array $children An array of XML nodes.
     *
     * @return array|PEAR_Error Array with data.
     */
    function _load(&$children)
    {
        $object = $this->_loadArray($children, $this->_fields_specific);
        if (is_a($object, 'PEAR_Error')) {
            return $object;
        }

        $object['name'] = $object['summary'];
        unset($object['summary']);

        if (empty($object['completed-date'])) {
            $object['completed-date'] = null;
        }

        if (empty($object['alarm'])) {
            $object['alarm'] = null;
        }

        if (isset($object['due-date'])) {
            $object['due'] = $object['due-date'];
            unset($object['due-date']);
        } else {
            $object['due'] = null;
        }

        if (isset($object['start-date'])) {
            $object['start'] = $object['start-date'];
            unset($object['start-date']);
        } else {
            $object['start'] = null;
        }

        if (!isset($object['estimate'])) {
            $object['estimate'] = null;
        } else {
            $object['estimate'] = (float) $object['estimate'];
        }

        if (!isset($object['parent'])) {
            $object['parent'] = null;
        }

        $object['completed'] = (bool) Kolab::percentageToBoolean($object['completed']);

        if (isset($object['organizer']) && isset($object['organizer']['smtp-address'])) {
            $object['assignee'] = $object['organizer']['smtp-address'];
        }

        return $object;
    }

    /**
     * Save the specific XML values.
     *
     * @param array $root     The XML document root.
     * @param array $object   The resulting data array.
     *
     * @return boolean|PEAR_Error True on success.
     */
    function _save($root, $object)
    {
        $object['summary'] = $object['name'];
        unset($object['name']);

        $object['due-date'] = $object['due'];
        unset($object['due']);

        $object['start-date'] = $object['start'];
        unset($object['start']);

        $object['estimate'] = number_format($object['estimate'], 2);

        $object['completed'] = Kolab::BooleanToPercentage($object['completed']);

        return $this->_saveArray($root, $object, $this->_fields_specific);
    }
}
