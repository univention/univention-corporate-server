<?php
/**
 * Implementation for contacts in the Kolab XML format.
 *
 * $Horde: framework/Kolab_Format/lib/Horde/Kolab/Format/XML/contact.php,v 1.2.2.6 2008-12-12 11:39:04 wrobel Exp $
 *
 * @package Kolab_Format
 */

/**
 * Kolab XML handler for contact groupware objects
 *
 * $Horde: framework/Kolab_Format/lib/Horde/Kolab/Format/XML/contact.php,v 1.2.2.6 2008-12-12 11:39:04 wrobel Exp $
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
class Horde_Kolab_Format_XML_contact extends Horde_Kolab_Format_XML {

    /**
     * Specific data fields for the contact object
     *
     * @var array
     */
    var $_fields_specific;

    /**
     * Structure of the name field
     *
     * @var array
     */
    var $_fields_name = array(
        'given-name' => array (
            'type'    => HORDE_KOLAB_XML_TYPE_STRING,
            'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
        ),
        'middle-names' => array (
            'type'    => HORDE_KOLAB_XML_TYPE_STRING,
            'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
        ),
        'last-name' => array (
            'type'    => HORDE_KOLAB_XML_TYPE_STRING,
            'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
        ),
        'full-name' => array (
            'type'    => HORDE_KOLAB_XML_TYPE_STRING,
            'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
        ),
        'initials' => array (
            'type'    => HORDE_KOLAB_XML_TYPE_STRING,
            'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
        ),
        'prefix' => array (
            'type'    => HORDE_KOLAB_XML_TYPE_STRING,
            'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
        ),
        'suffix' => array (
            'type'    => HORDE_KOLAB_XML_TYPE_STRING,
            'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
        )
    );

    /**
     * Structure of an address field
     *
     * @var array
     */
    var $_fields_address = array(
        'type'    => HORDE_KOLAB_XML_TYPE_COMPOSITE,
        'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
        'array'   => array(
            'type' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_DEFAULT,
                'default' => 'home',
            ),
            'street' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'locality' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'region' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'postal-code' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'country' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
        )
    );

    /**
     * Structure of a phone field
     *
     * @var array
     */
    var $_fields_phone = array(
        'type'    => HORDE_KOLAB_XML_TYPE_COMPOSITE,
        'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
        'array'   => array(
            'type' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_DEFAULT,
                'default' => '',
            ),
            'number' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
        ),
    );

    /**
     * Address types
     *
     * @var array
     */
    var $_address_types = array(
        'business',
        'home',
        'other',
    );

    /**
     * Phone types
     *
     * @var array
     */
    var $_phone_types = array(
        'business1',
        'business2',
        'businessfax',
        'callback',
        'car',
        'company',
        'home1',
        'home2',
        'homefax',
        'isdn',
        'mobile',
        'pager',
        'primary',
        'radio',
        'telex',
        'ttytdd',
        'assistant',
        'other',
    );

    /**
     * Constructor
     */
    function Horde_Kolab_Format_XML_contact()
    {
        $this->_root_name = "contact";

        /** Specific task fields, in kolab format specification order
         */
        $this->_fields_specific = array(
            'name' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_COMPOSITE,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
                'array'   => $this->_fields_name,
            ),
            'free-busy-url' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'organization' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'web-page' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'im-address' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'department' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'office-location' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'profession' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'job-title' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'manager-name' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'assistant' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'nick-name' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'spouse-name' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'birthday' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'anniversary' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'picture' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'children' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'gender' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'language' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'address' => array(
                'type'    => HORDE_KOLAB_XML_TYPE_MULTIPLE,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
                'array'   => $this->_fields_address,
            ),
            'email' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_MULTIPLE,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
                'array'   => $this->_fields_simple_person,
            ),
            'phone' => array(
                'type'    => HORDE_KOLAB_XML_TYPE_MULTIPLE,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
                'array'   => $this->_fields_phone,
            ),
            'preferred-address' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'latitude' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'longitude' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            // Horde specific fields
            'pgp-publickey' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            // Support for broken clients
            'website' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
            ),
            'im-adress' => array (
                'type'    => HORDE_KOLAB_XML_TYPE_STRING,
                'value'   => HORDE_KOLAB_XML_VALUE_MAYBE_MISSING,
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
     * @return array|PEAR_Error Array with the object data.
     */
    function _load(&$children)
    {
        $object = $this->_loadArray($children, $this->_fields_specific);
        if (is_a($object, 'PEAR_Error')) {
            return $object;
        }

        // Handle name fields
        if (isset($object['name'])) {
            $object = array_merge($object['name'], $object);
            unset($object['name']);
        }

        // Handle email fields
        $emails = array();
        if (isset($object['email'])) {
            foreach ($object['email'] as $email) {
                $smtp_address = $email['smtp-address'];
                if (!empty($smtp_address)) {
                    $emails[] = $smtp_address;
                }
            }
        }
        $object['emails'] = implode(', ', $emails);

        // Handle phone fields
        if (isset($object['phone'])) {
            foreach ($object['phone'] as $phone) {
                if (isset($phone['number']) &&
                    in_array($phone['type'], $this->_phone_types)) {
                    $object["phone-" . $phone['type']] = $phone['number'];
                }
            }
        }

        // Handle address fields
        if (isset($object['address'])) {
            foreach ($object['address'] as $address) {
                if (in_array($address['type'], $this->_address_types)) {
                    foreach ($address as $name => $value) {
                        $object["addr-" . $address['type'] . "-" . $name] = $value;
                    }
                }
            }
        }

        // Handle gender field
        if (isset($object['gender'])) {
            $gender = $object['gender'];

            if ($gender == "female") {
                $object['gender'] = 1;
            } else if ($gender == "male") {
                $object['gender'] = 0;
            } else {
                // unspecified gender
                unset($object['gender']);
            }
        }

        // Compatibility with broken clients
        $broken_fields = array("website" => "web-page",
                               "im-adress" => "im-address");
        foreach ($broken_fields as $broken_field => $real_field) {
            if (!empty($object[$broken_field]) && empty($object[$real_field])) {
                $object[$real_field] = $object[$broken_field];
            }
            unset($object[$broken_field]);
        }

        $object['__type'] = 'Object';

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
        // Handle name fields
        $name = array();
        foreach (array_keys($this->_fields_name) as $key) {
            if (isset($object[$key])) {
                $name[$key] = $object[$key];
                unset($object[$key]);
            }
        }
        $object['name'] = $name;

        // Handle email fields
        if (!isset($object['emails'])) {
            $emails = array();
        } else {
            $emails = explode(',', $object['emails']);
        }

        if (isset($object['email']) && 
            !in_array($object['email'], $emails)) {
            $emails[] = $object['email'];
        }

        $object['email'] = array();

        foreach ($emails as $email) {
            $email = trim($email);
            if (!empty($email)) {
                $new_email = array('display-name' => $object['name']['full-name'],
                                   'smtp-address' => $email);
                $object['email'][] = $new_email;
            }
        }

        // Handle phone fields
        if (!isset($object['phone'])) {
            $object['phone'] = array();
        }
        foreach ($this->_phone_types as $type) {
            $key = 'phone-' . $type;
            if (array_key_exists($key, $object)) {
                $new_phone = array('type'   => $type,
                                   'number' => $object[$key]);

                // Update existing phone entry of this type
                $updated = false;
                foreach($object['phone'] as $index => $phone) {
                    if ($phone['type'] == $type) {
                        $object['phone'][$index] = $new_phone;
                        $updated = true;
                        break;
                    }
                }
                if (!$updated) {
                    $object['phone'][] = $new_phone;
                }
            }
        }

        // Phone cleanup: remove empty numbers
        foreach($object['phone'] as $index => $phone) {
            if (empty($phone['number'])) {
                unset($object['phone'][$index]);
            }
        }

        // Handle address fields
        if (!isset($object['address'])) {
            $object['address'] = array();
        }

        foreach ($this->_address_types as $type) {
            $basekey = 'addr-' . $type . '-';
            $new_address = array('type'   => $type);
            foreach (array_keys($this->_fields_address['array']) as $subkey) {
                $key = $basekey . $subkey;
                if (array_key_exists($key, $object)) {
                    $new_address[$subkey] = $object[$key];
                }
            }

            // Update existing address entry of this type
            $updated = false;
            foreach($object['address'] as $index => $address) {
                if ($address['type'] == $type) {
                    $object['address'][$index] = $new_address;
                    $updated = true;
                }
            }
            if (!$updated) {
                $object['address'][] = $new_address;
            }
        }

        // Address cleanup: remove empty addresses
        foreach($object['address'] as $index => $address) {
            $all_empty = true;
            foreach($address as $name => $value) {
                if (!empty($value) && $name != "type") {
                    $all_empty = false;
                    break;
                }
            }

            if ($all_empty) {
                unset($object['address'][$index]);
            }
        }

        // Handle gender field
        if (isset($object['gender'])) {
            $gender = $object['gender'];

            if ($gender == "0") {
                $object['gender'] = "male";
            } else if ($gender == "1") {
                $object['gender'] = "female";
            } else {
                // unspecified gender
                unset($object['gender']);
            }
        }

        // Do the actual saving
        return $this->_saveArray($root, $object, $this->_fields_specific);
    }
}
