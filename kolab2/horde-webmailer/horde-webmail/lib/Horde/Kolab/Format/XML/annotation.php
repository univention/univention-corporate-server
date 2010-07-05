<?php
/**
 * Implementation for IMAP folder annotations in the Kolab XML format.
 *
 * $Horde: framework/Kolab_Format/lib/Horde/Kolab/Format/XML/annotation.php,v 1.1.2.5 2009-01-06 15:23:14 jan Exp $
 *
 * @package Kolab_Format
 */

/**
 * Kolab XML handler for IMAP folder annotations.
 *
 * $Horde: framework/Kolab_Format/lib/Horde/Kolab/Format/XML/annotation.php,v 1.1.2.5 2009-01-06 15:23:14 jan Exp $
 *
 * Copyright 2008-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @since   Horde 3.2
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @package Kolab_Format
 */
class Horde_Kolab_Format_XML_annotation extends Horde_Kolab_Format_XML {
    /**
     * Specific data fields for the prefs object
     *
     * @var Kolab
     */
    var $_fields_specific;

    /**
     * Constructor
     */
    function Horde_Kolab_Format_XML_annotation()
    {
        $this->_root_name = 'annotations';

        /** Specific preferences fields, in kolab format specification order
         */
        $this->_fields_specific = array(
            'annotation' => array(
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

        $result = array();
        foreach ($object['annotation'] as $annotation) {
            list($key, $value) = split('#', $annotation, 2);
            $result[base64_decode($key)] = base64_decode($value);
        }

        return $result;
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
        $annotations = array();
        foreach ($object as $key => $value) {
            if ($key != 'uid') {
                $annotations['annotation'][] = base64_encode($key) . '#' . base64_encode($value);
            }
        }

        return $this->_saveArray($root, $annotations, $this->_fields_specific);
    }
}
