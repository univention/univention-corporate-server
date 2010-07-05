<?php

require_once 'Horde/iCalendar.php';

// The following were shamelessly yoinked from Contact_Vcard_Build
// Part numbers for N components.
define('VCARD_N_FAMILY',     0);
define('VCARD_N_GIVEN',      1);
define('VCARD_N_ADDL',       2);
define('VCARD_N_PREFIX',     3);
define('VCARD_N_SUFFIX',     4);

// Part numbers for ADR components.
define('VCARD_ADR_POB',      0);
define('VCARD_ADR_EXTEND',   1);
define('VCARD_ADR_STREET',   2);
define('VCARD_ADR_LOCALITY', 3);
define('VCARD_ADR_REGION',   4);
define('VCARD_ADR_POSTCODE', 5);
define('VCARD_ADR_COUNTRY',  6);

// Part numbers for GEO components.
define('VCARD_GEO_LAT',      0);
define('VCARD_GEO_LON',      1);

/**
 * Class representing vCard entries.
 *
 * $Horde: framework/iCalendar/iCalendar/vcard.php,v 1.3.10.19 2009-04-30 17:31:43 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Karsten Fourmont <karsten@horde.org>
 * @package Horde_iCalendar
 */
class Horde_iCalendar_vcard extends Horde_iCalendar {

    function Horde_iCalendar_vcard($version = '2.1')
    {
        return parent::Horde_iCalendar($version);
    }

    function getType()
    {
        return 'vcard';
    }

    /**
     * Unlike vevent and vtodo, a vcard is normally not enclosed in an
     * iCalendar container. (BEGIN..END)
     */
    function exportvCalendar()
    {
        $requiredAttributes['VERSION'] = $this->_version;
        $requiredAttributes['N'] = ';;;;;;';
        if ($this->_version == '3.0') {
            $requiredAttributes['FN'] = '';
        }

        foreach ($requiredAttributes as $name => $default_value) {
            if (is_a($this->getAttribute($name), 'PEAR_Error')) {
                $this->setAttribute($name, $default_value);
            }
        }

        return $this->_exportvData('VCARD');
    }

    /**
     * Returns the contents of the "N" tag as a printable Name:
     * i.e. converts:
     *
     *   N:Duck;Dagobert;T;Professor;Sen.
     * to
     *   "Professor Dagobert T Duck Sen"
     *
     * @return string  Full name of vcard "N" tag or null if no N tag.
     */
    function printableName()
    {
        $name_parts = $this->getAttributeValues('N');
        if (is_a($name_parts, 'PEAR_Error')) {
            return null;
        }

        $name_arr = array();

        if (!empty($name_parts[VCARD_N_PREFIX])) {
            $name_arr[] = $name_parts[VCARD_N_PREFIX];
        }
        if (!empty($name_parts[VCARD_N_GIVEN])) {
            $name_arr[] = $name_parts[VCARD_N_GIVEN];
        }
        if (!empty($name_parts[VCARD_N_ADDL])) {
            $name_arr[] = $name_parts[VCARD_N_ADDL];
        }
        if (!empty($name_parts[VCARD_N_FAMILY])) {
            $name_arr[] = $name_parts[VCARD_N_FAMILY];
        }
        if (!empty($name_parts[VCARD_N_SUFFIX])) {
            $name_arr[] = $name_parts[VCARD_N_SUFFIX];
        }

        return implode(' ', $name_arr);
    }

    /**
     * Static function to make a given email address rfc822 compliant.
     *
     * @param string $address  An email address.
     *
     * @return string  The RFC822-formatted email address.
     */
    function getBareEmail($address)
    {
        // Empty values are still empty.
        if (!$address) {
            return $address;
        }

        require_once 'Mail/RFC822.php';
        require_once 'Horde/MIME.php';

        static $rfc822;
        if (is_null($rfc822)) {
            $rfc822 = new Mail_RFC822();
        }

        if (!$rfc822->validateMailbox($address)) {
            return $address;
        }
        return MIME::rfc822WriteAddress($address->mailbox, $address->host);
    }

}
