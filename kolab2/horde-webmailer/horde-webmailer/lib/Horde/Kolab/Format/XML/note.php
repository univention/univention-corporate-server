<?php
/**
 * Implementation for notes in the Kolab XML format.
 *
 * $Horde: framework/Kolab_Format/lib/Horde/Kolab/Format/XML/note.php,v 1.2.2.5 2008-12-12 11:39:04 wrobel Exp $
 *
 * @package Kolab_Format
 */

/**
 * Kolab XML handler for note groupware objects.
 *
 * $Horde: framework/Kolab_Format/lib/Horde/Kolab/Format/XML/note.php,v 1.2.2.5 2008-12-12 11:39:04 wrobel Exp $
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
class Horde_Kolab_Format_XML_note extends Horde_Kolab_Format_XML {
    /**
     * Specific data fields for the note object
     *
     * @var Kolab
     */
    var $_fields_specific;

    /**
     * Constructor
     */
    function Horde_Kolab_Format_XML_note()
    {
        $this->_root_name = 'note';

        /** Specific note fields, in kolab format specification order
         */
        $this->_fields_specific = array(
            'summary' => array(
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_DEFAULT,
                'default' => '',
            ),
            'background-color' => array(
                'type'    => HORDE_KOLAB_XML_TYPE_COLOR,
                'value'   => HORDE_KOLAB_XML_VALUE_DEFAULT,
                'default' => '#000000',
            ),
            'foreground-color' => array(
                'type'    => HORDE_KOLAB_XML_TYPE_COLOR,
                'value'   => HORDE_KOLAB_XML_VALUE_DEFAULT,
                'default' => '#ffff00',
            ),
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
     * @return array|PEAR_Error Array with the object data
     */
    function _load(&$children)
    {
        $object = $this->_loadArray($children, $this->_fields_specific);
        if (is_a($object, 'PEAR_Error')) {
            return $object;
        }

        $object['desc'] = $object['summary'];
        unset($object['summary']);

        return $object;
    }

    /**
     * Save the specific XML values.
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
        $object['summary'] = $object['desc'];
        unset($object['desc']);

        return $this->_saveArray($root, $object, $this->_fields_specific);
    }
}
