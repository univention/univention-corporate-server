<?php
/**
 * Implementation for horde user preferences in the Kolab XML format.
 *
 * $Horde: framework/Kolab_Format/lib/Horde/Kolab/Format/XML/hprefs.php,v 1.2.2.7 2009-01-06 15:23:14 jan Exp $
 *
 * @package Kolab_Format
 */

/**
 * Kolab XML handler for client preferences.
 *
 * $Horde: framework/Kolab_Format/lib/Horde/Kolab/Format/XML/hprefs.php,v 1.2.2.7 2009-01-06 15:23:14 jan Exp $
 *
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @since   Horde 3.2
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @package Kolab_Format
 */
class Horde_Kolab_Format_XML_hprefs extends Horde_Kolab_Format_XML {
    /**
     * Specific data fields for the prefs object
     *
     * @var Kolab
     */
    var $_fields_specific;

    /**
     * Automatically create categories if they are missing?
     *
     * @var boolean
     */
    var $_create_categories = false;

    /**
     * Constructor
     */
    function Horde_Kolab_Format_XML_hprefs()
    {
        $this->_root_name = 'h-prefs';

        /** Specific preferences fields, in kolab format specification order
         */
        $this->_fields_specific = array(
            'application' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'pref' => array(
                'type'    => HORDE_KOLAB_XML_TYPE_MULTIPLE,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
                'array'   => array(
                    'type' => HORDE_KOLAB_XML_TYPE_STRING,
                    'value' => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
                ),
            ),
        );

        parent::Horde_Kolab_Format_XML();
    }

    /**
     * Load an object based on the given XML string.
     *
     * @param string $xmltext  The XML of the message as string.
     *
     * @return array|PEAR_Error The data array representing the object.
     */
    function load(&$xmltext)
    {
        $object = parent::load($xmltext);

        if (empty($object['application'])) {
            if (!empty($object['categories'])) {
                $object['application'] = $object['categories'];
                unset($object['categories']);
            } else {
                return PEAR::raiseError('Preferences XML object is missing an application setting.');
            }
        }

        return $object;
    }

    /**
     * Convert the data to a XML string.
     *
     * @param array $attributes  The data array representing the note.
     *
     * @return string|PEAR_Error The data as XML string.
     */
    function save($object)
    {
        if (empty($object['application'])) {
            if (!empty($object['categories'])) {
                $object['application'] = $object['categories'];
                unset($object['categories']);
            } else {
                return PEAR::raiseError('Preferences XML object is missing an application setting.');
            }
        }

        return parent::save($object);
    }
}
