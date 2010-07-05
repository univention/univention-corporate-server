<?php
/**
 * Implementation for distributionlists in the Kolab XML format.
 *
 * $Horde: framework/Kolab_Format/lib/Horde/Kolab/Format/XML/distributionlist.php,v 1.2.2.5 2008-12-12 11:39:04 wrobel Exp $
 *
 * @package Kolab_Format
 */

/**
 * Kolab XML handler for distributionlist groupware objects
 *
 * $Horde: framework/Kolab_Format/lib/Horde/Kolab/Format/XML/distributionlist.php,v 1.2.2.5 2008-12-12 11:39:04 wrobel Exp $
 *
 * Copyright 2007-2008 Klarälvdalens Datakonsult AB
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @since   Horde 3.2
 * @author  Thomas Jarosch <thomas.jarosch@intra2net.com>
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @author  Mike Gabriel <m.gabriel@das-netzwerkteam.de>
 * @package Kolab_Format
 */
class Horde_Kolab_Format_XML_distributionlist extends Horde_Kolab_Format_XML {

    /**
     * Specific data fields for the contact object
     *
     * @var array
     */
    var $_fields_specific;

    /**
     * Constructor
     */
    function Horde_Kolab_Format_XML_distributionlist()
    {
        $this->_root_name = "distribution-list";

        /** Specific task fields, in kolab format specification order
         */
        $this->_fields_specific = array(
                'display-name' => array(
                    'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                    'value'   => HORDE_KOLAB_XML_VALUE_NOT_EMPTY
                ),
                'member' => array(
                    'type'    => HORDE_KOLAB_XML_TYPE_MULTIPLE,
                    'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
                    'array'   => $this->_fields_simple_person,
                )
            );

        parent::Horde_Kolab_Format_XML();
    }

    /**
     * Load the groupware object based on the specifc XML values.
     *
     * @access protected
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

        // Map the display-name of a kolab dist list to horde's lastname attribute
        if (isset($object['display-name'])) {
            $object['last-name'] = $object['display-name'];
            unset($object['display-name']);
        }

        // the mapping from $object['member'] as stored in XML back to Turba_Objects (contacts)
        // must be performed in the Kolab_IMAP storage driver as we need access to the search
        // facilities of the kolab storage driver.

        $object['__type'] = 'Group';
        return $object;
    }

    /**
     * Save the  specifc XML values.
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
        // Map the display-name of a kolab dist list to horde's lastname attribute
        if (isset($object['last-name'])) {
            $object['display-name'] = $object['last-name'];
            unset($object['last-name']);
        }

        return $this->_saveArray($root, $object, $this->_fields_specific);
    }
}
