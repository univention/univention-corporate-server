<?php

/** We rely on the Horde_Data_imc:: abstract class. */
require_once dirname(__FILE__) . '/imc.php';

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
 * Implement the Horde_Data:: API for vCard data.
 *
 * $Horde: framework/Data/Data/vcard.php,v 1.31 2004/05/10 13:41:07 jan Exp $
 *
 * Copyright 1999-2004 Jan Schneider <jan@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @version $Horde: framework/Data/Data/vcard.php,v 1.31 2004/05/10 13:41:07 jan Exp $
 * @since   Horde 3.0
 * @package Horde_Data
 */
class Horde_Data_vcard extends Horde_Data_imc {

    /**
     * The vCard version.
     *
     * @access private
     * @var string $_version
     */
    var $_version;

    function importData($text)
    {
        $res = parent::importData($text);
        if (is_a($res, 'PEAR_Error')) {
            return $res;
        }
        return $this->_objects;
    }

    /**
     * Builds a vCard file from a given data structure and returns it
     * as a string.
     *
     * @access public
     *
     * @param array $data  A two-dimensional array containing the data set.
     *
     * @return string  The vCard data.
     */
    function exportData($data)
    {
        /* According to RFC 2425, we should always use CRLF-terminated
           lines. */
        $newline = "\r\n";

        $file = "BEGIN:VCARD${newline}VERSION:3.0${newline}";
        foreach ($data as $key => $val) {
            if (!empty($val)) {
                // Basic encoding. Newlines for now; more work here to
                // make this RFC-compliant.
                $file .= $key . ':' .  $this->_quoteAndFold($val);
            }
        }
        $file .= "END:VCARD$newline";

        return $file;
    }

    /**
     * Builds a vCard file from a given data structure and triggers
     * its download. It DOES NOT exit the current script but only
     * outputs the correct headers and data.
     *
     * @access public
     *
     * @param string $filename   The name of the file to be downloaded.
     * @param array  $data       A two-dimensional array containing the data set.
     */
    function exportFile($filename, $data, $charset = null)
    {
        $export = $this->exportData($data);
        $cType = 'text/x-vcard';
        if (!empty($charset)) {
            $cType .= '; charset="' . $charset . '"';
        }
        $GLOBALS['browser']->downloadHeaders($filename, $cType, false, strlen($export));
        echo $export;
    }

    function _build($data, &$i)
    {
        $objects = array();

        while (isset($data[$i])) {
            if (String::upper($data[$i]['name']) != 'BEGIN') {
                return PEAR::raiseError(sprintf(_("Import Error: Expected \"BEGIN\" on line %d."), $i));
            }
            $type = String::upper($data[$i]['values'][0]);
            $object = array('type' => $type);
            $object['objects'] = array();
            $object['params'] = array();
            $i++;
            while (isset($data[$i]) && String::upper($data[$i]['name']) != 'END') {
                if (String::upper($data[$i]['name']) == 'BEGIN') {
                    $object['objects'][] = $this->_build($data, $i);
                } else {
                    $object['params'][] = $data[$i];
                    if (String::upper($data[$i]['name']) == 'VERSION') {
                        $object['version'] = $data[$i]['values'][0];
                    }
                }
                $i++;
            }
            if (!isset($data[$i])) {
                return PEAR::raiseError(_("Import Error: Unexpected end of file."));
            }
            if (String::upper($data[$i]['values'][0]) != $type) {
                return PEAR::raiseError(sprintf(_("Import Error: Type mismatch. Expected \"END:%s\" on line %d."), $type, $i));
            }
            $objects[] = $object;
            $i++;
        }

        $this->_objects = $objects;
    }

    function read($attribute, $index = 0)
    {
        if (($index == 0) && ($this->_version < 3.0)) {
            $value = $attribute['value21'];
        } else {
            $value = $attribute['values'][$index];
        }

        if (isset($attribute['params']['ENCODING'])) {
            switch ($attribute['params']['ENCODING'][0]) {
            case 'QUOTED-PRINTABLE':
                $value = quoted_printable_decode($value);
                break;
            }
        }

        return $value;
    }

    function getValues($attribute, $card = 0)
    {
        $values = array();
        $attribute = String::upper($attribute);

        if (isset($this->_objects[$card])) {
            for ($i = 0; $i < count($this->_objects[$card]['params']); $i++) {
                $param = $this->_objects[$card]['params'][$i];
                if (String::upper($param['name']) == $attribute) {
                    for ($j = 0; $j < count($param['values']); $j++) {
                        $values[] = array('value' => $this->read($param, $j), 'params' => $param['params']);
                    }
                }
            }
        }

        return $values;
    }

    function getBareEmail($address)
    {
        require_once 'Mail/RFC822.php';
        require_once 'Horde/MIME.php';

        static $rfc822;
        if (is_null($rfc822)) {
            $rfc822 = &new Mail_RFC822();
        }

        $rfc822->validateMailbox($address);

        return MIME::rfc822WriteAddress($address->mailbox, $address->host);
    }

    /**
     * Return a data hash from a vCard object.
     *
     * @param array $card  The card to convert.
     *
     * @return array  The hashed data.
     *
     * @since Horde 3.0
     */
    function toHash($card)
    {
        $this->_version = isset($card['version']) ? $card['version'] : null;
        $hash = array();
        foreach ($card['params'] as $item) {
            switch ($item['name']) {
            case 'FN':
                $hash['name'] = $this->read($item);
                break;

            case 'N':
                $name = explode(';', $this->read($item));
                $hash['lastname'] = $name[VCARD_N_FAMILY];
                $hash['firstname'] = $name[VCARD_N_GIVEN];
                break;

            case 'NICKNAME':
                $hash['nickname'] = $this->read($item);
                break;

            // We use LABEL but also support ADR.
            case 'LABEL':
                if (isset($item['params']['HOME'])) {
                    $hash['homeAddress'] = $this->read($item);
                } elseif (isset($item['params']['WORK'])) {
                    $hash['workAddress'] = $this->read($item);
                } else {
                    $hash['workAddress'] = $this->read($item);
                }
                break;

            // for vCard 3.0
            case 'ADR':
                if (isset($item['params']['TYPE'])) {
                    foreach ($item['params']['TYPE'] as $adr) {
                        if (String::upper($adr) == 'HOME') {
                            $address = explode(';', $this->read($item));
                            $hash['homeAddress'] = $address[VCARD_ADR_STREET];
                            $hash['homeCity'] = $address[VCARD_ADR_LOCALITY];
                            $hash['homeProvince'] = $address[VCARD_ADR_REGION];
                            $hash['homePostalCode'] = $address[VCARD_ADR_POSTCODE];
                            $hash['homeCountry'] = $address[VCARD_ADR_COUNTRY];
                        } elseif (String::upper($adr) == 'WORK') {
                            $address = explode(';', $this->read($item));
                            $hash['workAddress'] = $address[VCARD_ADR_STREET];
                            $hash['workCity'] = $address[VCARD_ADR_LOCALITY];
                            $hash['workProvince'] = $address[VCARD_ADR_REGION];
                            $hash['workPostalCode'] = $address[VCARD_ADR_POSTCODE];
                            $hash['workCountry'] = $address[VCARD_ADR_COUNTRY];
                        }
                    }
                }
                break;

            case 'TEL':
                if (isset($item['params']['VOICE'])) {
                    if (isset($item['params']['HOME'])) {
                        $hash['homePhone'] = $this->read($item);
                    } elseif (isset($item['params']['WORK'])) {
                        $hash['workPhone'] = $this->read($item);
                    } elseif (isset($item['params']['CELL'])) {
                        $hash['cellPhone'] = $this->read($item);
                    }
                } elseif (isset($item['params']['FAX'])) {
                    $hash['fax'] = $this->read($item);
                } elseif (isset($item['params']['TYPE'])) {
                    // for vCard 3.0
                    foreach ($item['params']['TYPE'] as $tel) {
                        if (String::upper($tel) == 'WORK') {
                            $hash['workPhone'] = $this->read($item);
                        } elseif (String::upper($tel) == 'HOME') {
                            $hash['homePhone'] = $this->read($item);
                        } elseif (String::upper($tel) == 'CELL') {
                            $hash['cellPhone'] = $this->read($item);
                        } elseif (String::upper($tel) == 'FAX') {
                            $hash['fax'] = $this->read($item);
                        }
                    }
                }
                break;

            case 'EMAIL':
                if (isset($item['params']['PREF']) || !isset($hash['email'])) {
                    $hash['email'] = $this->getBareEmail($this->read($item));
                }
                break;

            case 'TITLE':
                $hash['title'] = $this->read($item);
                break;

            case 'ORG':
                $units = array();
                for ($i = 0; $i < count($item['values']); $i++) {
                    $units[] = $this->read($item, $i);
                }
                $hash['company'] = implode(', ', $units);
                break;

            case 'NOTE':
                $hash['notes'] = $this->read($item);
                break;

            case 'URL':
                $hash['website'] = $this->read($item);
                break;
            }
        }

        return $hash;
    }

    /**
     * Return an array of vCard properties -> values from a hash of
     * attributes.
     *
     * @param array $hash  The hash of values to convert.
     *
     * @return array  The vCard format data.
     *
     * @since Horde 3.0
     */
    function fromHash($hash)
    {
        $card = array();
        foreach ($hash as $key => $val) {
            switch ($key) {
            case 'name':
                $card['FN'] = $val;
                break;

            case 'nickname':
                $card['NICKNAME'] = $val;
                break;

            case 'homePhone':
                $card['TEL;TYPE=HOME'] = $val;
                break;

            case 'workPhone':
                $card['TEL;TYPE=WORK'] = $val;
                break;

            case 'cellPhone':
                $card['TEL;TYPE=CELL'] = $val;
                break;

            case 'fax':
                $card['TEL;TYPE=FAX'] = $val;
                break;

            case 'email':
                $card['EMAIL'] = $this->getBareEmail($val);
                break;

            case 'title':
                $card['TITLE'] = $val;
                break;

            case 'company':
                $card['ORG'] = $val;
                break;

            case 'notes':
                $card['NOTE'] = $val;
                break;

            case 'website':
                $card['URL'] = $val;
                break;
            }
        }

        $card['N'] = implode(';', array(
            VCARD_N_FAMILY          => isset($hash['lastname']) ? $hash['lastname'] : '',
            VCARD_N_GIVEN           => isset($hash['firstname']) ? $hash['firstname'] : '',
            VCARD_N_ADDL            => '',
            VCARD_N_PREFIX          => '',
            VCARD_N_SUFFIX          => '',
        ));

        $card['ADR;TYPE=HOME'] = implode(';', array(
            VCARD_ADR_POB           => '',
            VCARD_ADR_EXTEND        => '',
            VCARD_ADR_STREET        => isset($hash['homeAddress']) ? $hash['homeAddress'] : '',
            VCARD_ADR_LOCALITY      => isset($hash['homeCity']) ? $hash['homeCity'] : '',
            VCARD_ADR_REGION        => isset($hash['homeProvince']) ? $hash['homeProvince'] : '',
            VCARD_ADR_POSTCODE      => isset($hash['homePostalCode']) ? $hash['homePostalCode'] : '',
            VCARD_ADR_COUNTRY       => isset($hash['homeCountry']) ? $hash['homeCountry'] : '',
        ));

        $card['ADR;TYPE=WORK'] = implode(';', array(
            VCARD_ADR_POB           => '',
            VCARD_ADR_EXTEND        => '',
            VCARD_ADR_STREET        => isset($hash['workAddress']) ? $hash['workAddress'] : '',
            VCARD_ADR_LOCALITY      => isset($hash['workCity']) ? $hash['workCity'] : '',
            VCARD_ADR_REGION        => isset($hash['workProvince']) ? $hash['workProvince'] : '',
            VCARD_ADR_POSTCODE      => isset($hash['workPostalCode']) ? $hash['workPostalCode'] : '',
            VCARD_ADR_COUNTRY       => isset($hash['workCountry']) ? $hash['workCountry'] : '',
        ));

        return $card;
    }

    /**
     * Takes all necessary actions for the given import step, parameters and
     * form values and returns the next necessary step.
     *
     * @access public
     *
     * @param integer $action        The current step. One of the IMPORT_*
     *                               constants.
     * @param optional array $param  An associative array containing needed
     *                               parameters for the current step.
     *
     * @return mixed        Either the next step as an integer constant or imported
     *                      data set after the final step.
     */
    function nextStep($action, $param = array())
    {
        switch ($action) {
        case IMPORT_FILE:
            $res = parent::nextStep($action, $param);
            if (is_a($res, 'PEAR_Error')) {
                return $res;
            }

            $import_data = $this->importFile($_FILES['import_file']['tmp_name']);
            if (is_a($import_data, 'PEAR_Error')) {
                return $import_data;
            }

            /* Build the result data set as an associative array. */
            $data = array();
            foreach ($import_data as $object) {
                if ($object['type'] == 'VCARD') {
                    $data[] = $this->toHash($object);
                }
            }
            return $data;
            break;

        default:
            return parent::nextStep($action, $param);
            break;
        }
    }

}
