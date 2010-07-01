<?php
/**
 * Implementation for events in the Kolab XML format.
 *
 * $Horde: framework/Kolab_Format/lib/Horde/Kolab/Format/XML/event.php,v 1.2.2.3 2008-12-12 11:39:04 wrobel Exp $
 *
 * @package Kolab_Format
 */

/** Kolab date handling functions. */
require_once 'Horde/Kolab/Format/Date.php';

/**
 * Kolab XML handler for event groupware objects.
 *
 * $Horde: framework/Kolab_Format/lib/Horde/Kolab/Format/XML/event.php,v 1.2.2.3 2008-12-12 11:39:04 wrobel Exp $
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
class Horde_Kolab_Format_XML_event extends Horde_Kolab_Format_XML {
    /**
     * Specific data fields for the contact object
     *
     * @var array
     */
    var $_fields_specific;

    /**
     * Constructor
     */
    function Horde_Kolab_Format_XML_event()
    {
        $this->_root_name = 'event';

        /** Specific event fields, in kolab format specification order
         */
        $this->_fields_specific = array(
            'summary' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'location' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'organizer' => $this->_fields_simple_person,
            'start-date' => array(
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_NOT_EMPTY,
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
            'show-time-as' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'color-label' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'end-date' => array(
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_NOT_EMPTY,
            ),
        );

        parent::Horde_Kolab_Format_XML();
    }

    /**
     * Load event XML values and translate start/end date.
     *
     * @access protected
     *
     * @param array $children An array of XML nodes.
     *
     * @return array|PEAR_Error Array with the object data.
     */
    function _load(&$children)
    {
        $object = parent::_load($children);
        if (is_a($object, 'PEAR_Error')) {
            return $object;
        }

        // Translate start/end date including full day events
        if (strlen($object['start-date']) == 10) {
            $object['start-date'] = Horde_Kolab_Format_Date::decodeDate($object['start-date']);
            $object['end-date'] = Horde_Kolab_Format_Date::decodeDate($object['end-date']) + 24*60*60;
        } else {
            $object['start-date'] = Horde_Kolab_Format_Date::decodeDateTime($object['start-date']);
            $object['end-date'] = Horde_Kolab_Format_Date::decodeDateTime($object['end-date']);
        }

        return $object;
    }

    /**
     * Save event XML values and translate start/end date.
     *
     * @access protected
     *
     * @param array $root     The XML document root.
     * @param array $object   The resulting data array.
     *
     * @return boolean|PEAR_Error True on success.
     */
    function _save($root, $object)
    {
        // Translate start/end date including full day events
        if (!empty($object['_is_all_day'])) {
            $object['start-date'] = Horde_Kolab_Format_Date::encodeDate($object['start-date']);
            $object['end-date'] = Horde_Kolab_Format_Date::encodeDate($object['end-date'] - 24*60*60);
        } else {
            $object['start-date'] = Horde_Kolab_Format_Date::encodeDateTime($object['start-date']);
            $object['end-date'] = Horde_Kolab_Format_Date::encodeDateTime($object['end-date']);
        }

        return parent::_save($root, $object);
    }
}
