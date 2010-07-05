<?php
/**
 * Horde_Data implementation for LDAP Data Interchange Format (LDIF).
 *
 * $Horde: turba/lib/Data/ldif.php,v 1.2.2.5 2009-09-18 14:23:22 jan Exp $
 *
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Rita Selsky <ritaselsky@gmail.com>
 * @since   Horde 3.2
 * @package Horde_Data
 */
class Horde_Data_ldif extends Horde_Data {

    var $_extension = 'ldif';

    var $_contentType = 'text/ldif';

    /**
     * Useful Mozilla address book attribute names.
     *
     * @private
     * @var array
     */
    var $_mozillaAttr = array('cn', 'givenName', 'sn', 'mail', 'mozillaNickname',
                             'homeStreet', 'mozillaHomeStreet2', 'mozillaHomeLocalityName',
                             'mozillaHomeState', 'mozillaHomePostalCode',
                             'mozillaHomeCountryName', 'street',
                             'mozillaWorkStreet2', 'l', 'st', 'postalCode',
                             'c', 'homePhone', 'telephoneNumber', 'mobile',
                             'fax', 'title', 'company', 'description', 'mozillaWorkUrl',
                              'department', 'mozillaNickname');

    /**
     * Useful Turba address book attribute names.
     *
     * @private
     * @var array
     */
    var $_turbaAttr = array('name', 'firstname', 'lastname', 'email', 'alias',
                            'homeAddress', 'homeStreet', 'homeCity',
                            'homeProvince', 'homePostalCode', 'homeCountry',
                            'workAddress', 'workStreet', 'workCity', 'workProvince',
                            'workPostalCode', 'workCountry',
                            'homePhone', 'workPhone', 'cellPhone',
                            'fax', 'title', 'company', 'notes', 'website',
                            'department', 'nickname');
    /**
     * Turba address book attribute names and the corresponding Mozilla name.
     *
     * @private
     * @var array
     */
    var $_turbaMozillaMap = array('name' => 'cn',
                                  'firstname' => 'givenName',
                                  'lastname' => 'sn',
                                  'email' => 'mail',
                                  'alias' => 'mozillaNickname',
                                  'homePhone' => 'homePhone',
                                  'workPhone' => 'telephoneNumber',
                                  'cellPhone' => 'mobile',
                                  'fax' => 'fax',
                                  'title' => 'title',
                                  'company' => 'company',
                                  'notes' => 'description',
                                  'homeAddress' => 'homeStreet',
                                  'homeStreet' => 'mozillaHomeStreet2',
                                  'homeCity' => 'mozillaHomeLocalityName',
                                  'homeProvince' => 'mozillaHomeState',
                                  'homePostalCode' => 'mozillaHomePostalCode',
                                  'homeCountry' => 'mozillaHomeCountryName',
                                  'workAddress' => 'street',
                                  'workStreet' => 'mozillaWorkStreet2',
                                  'workCity' => 'l',
                                  'workProvince' => 'st',
                                  'workPostalCode' => 'postalCode',
                                  'workCountry' => 'c',
                                  'website' => 'mozillaWorkUrl',
                                  'department' => 'department',
                                  'nickname' => 'mozillaNickname');

    /**
     * Check if a string is safe according to RFC 2849, or if it needs to be
     * base64 encoded.
     *
     * @private
     *
     * @param string $str  The string to check.
     *
     * @return boolean  True if the string is safe, false otherwise.
     */
    function _is_safe_string($str)
    {
        /*  SAFE-CHAR         = %x01-09 / %x0B-0C / %x0E-7F
         *                     ; any value <= 127 decimal except NUL, LF,
         *                     ; and CR
         *
         *  SAFE-INIT-CHAR    = %x01-09 / %x0B-0C / %x0E-1F /
         *                     %x21-39 / %x3B / %x3D-7F
         *                     ; any value <= 127 except NUL, LF, CR,
         *                     ; SPACE, colon (":", ASCII 58 decimal)
         *                     ; and less-than ("<" , ASCII 60 decimal) */
        if (!strlen($str)) {
            return true;
        }
        if ($str[0] == ' ' || $str[0] == ':' || $str[0] == '<') {
            return false;
        }
        for ($i = 0; $i < strlen($str); ++$i) {
            if (ord($str[$i]) > 127 || $str[$i] == NULL || $str[$i] == "\n" ||
                $str[$i] == "\r") {
                return false;
            }
        }

        return true;
    }

    function importData($contents, $header = false)
    {
        $data = array();
        $records = preg_split('/(\r?\n){2}/', $contents);
        foreach ($records as $record) {
            if (trim($record) == '') {
                /* Ignore empty records */
                continue;
            }
            /* one key:value pair per line */
            $lines = preg_split('/\r?\n/', $record);
            $hash = array();
            foreach ($lines as $line) {
                list($key, $delimiter, $value) = preg_split('/(:[:<]?) */', $line, 2, PREG_SPLIT_DELIM_CAPTURE);
                if (in_array($key, $this->_mozillaAttr)) {
                    $hash[$key] = ($delimiter == '::' ? base64_decode($value) : $value);
                }
            }
            $data[] = $hash;
        }

        return $data;
    }

    /**
     * Builds a LDIF file from a given data structure and triggers its download.
     * It DOES NOT exit the current script but only outputs the correct headers
     * and data.
     *
     * @param string $filename  The name of the file to be downloaded.
     * @param array $data       A two-dimensional array containing the data
     *                          set.
     * @param boolean $header   If true, the rows of $data are associative
     *                          arrays with field names as their keys.
     */
    function exportFile($filename, $data, $header = false)
    {
        $export = $this->exportData($data, $header);
        $GLOBALS['browser']->downloadHeaders($filename, 'text/ldif', false, strlen($export));
        echo $export;
    }

    /**
     * Builds a LDIF file from a given data structure and returns it as a
     * string.
     *
     * @param array $data      A two-dimensional array containing the data set.
     * @param boolean $header  If true, the rows of $data are associative
     *                         arrays with field names as their keys.
     *
     * @return string  The LDIF data.
     */
    function exportData($data, $header = false)
    {
        if (!is_array($data) || !count($data)) {
            return '';
        }
        $export = '';
        $mozillaTurbaMap = array_flip($this->_turbaMozillaMap) ;
        foreach ($data as $row) {
            $recordData = '';
            foreach ($this->_mozillaAttr as $value) {
                if (isset($row[$mozillaTurbaMap[$value]])) {
                    // Base64 encode each value as necessary and store it.
                    // Store cn and mail separately for use in record dn
                    if (!$this->_is_safe_string($row[$mozillaTurbaMap[$value]])) {
                        $recordData .= $value . ':: ' . base64_encode($row[$mozillaTurbaMap[$value]]) . "\n";
                    } else {
                        $recordData .= $value . ': ' . $row[$mozillaTurbaMap[$value]] . "\n";
                    }
                }
            }

            $dn = 'cn=' . $row[$mozillaTurbaMap['cn']] . ',mail=' . $row[$mozillaTurbaMap['mail']];
            if (!$this->_is_safe_string($dn)) {
                $export .= 'dn:: ' . base64_encode($dn) . "\n";
            } else {
                $export .= 'dn: ' . $dn . "\n";
            }

            $export .= "objectclass: top\n"
                . "objectclass: person\n"
                . "objectclass: organizationalPerson\n"
                . "objectclass: inetOrgPerson\n"
                . "objectclass: mozillaAbPersonAlpha\n"
                . $recordData . "modifytimestamp: 0Z\n\n";
        }

        return $export;
    }

    /**
     * Takes all necessary actions for the given import step, parameters and
     * form values and returns the next necessary step.
     *
     * @param integer $action  The current step. One of the IMPORT_* constants.
     * @param array $param     An associative array containing needed
     *                         parameters for the current step.
     *
     * @return mixed  Either the next step as an integer constant or imported
     *                data set after the final step.
     */
    function nextStep($action, $param = array())
    {
        switch ($action) {
        case IMPORT_FILE:
            $next_step = parent::nextStep($action, $param);
            if (is_a($next_step, 'PEAR_Error')) {
                return $next_step;
            }

            $_SESSION['import_data']['data'] = $this->importFile($_FILES['import_file']['tmp_name']);
            $data = array();
            foreach ($_SESSION['import_data']['data'] as $record) {
                $turbaHash = array();
                foreach ($this->_turbaAttr as $value) {
                    switch ($value) {
                    case 'homeAddress':
                        // These are the keys we're interested in.
                        $keys = array('homeStreet', 'mozillaHomeStreet2',
                                      'mozillaHomeLocalityName', 'mozillaHomeState',
                                      'mozillaHomePostalCode', 'mozillaHomeCountryName');

                        // Grab all of them that exist in $record.
                        $values = array();
                        foreach ($keys as $key) {
                            if (isset($record[$key])) {
                                $values = $record[$key];
                            }
                        }

                        // Special handling for State if both State
                        // and Locality Name are set.
                        if (isset($values['mozillaHomeLocalityName'])
                            && isset($values['mozillaHomeState'])) {
                            $values['mozillaHomeLocalityName'] .= ', ' . $values['mozillaHomeState'];
                            unset($values['mozillaHomeState']);
                        }

                        if ($values) {
                            $turbaHash[$value] = implode("\n", $values);
                        }
                        break;

                    case 'workAddress':
                        // These are the keys we're interested in.
                        $keys = array('street', 'mozillaWorkStreet2', 'l',
                                      'st', 'postalCode', 'c');

                        // Grab all of them that exist in $record.
                        $values = array();
                        foreach ($keys as $key) {
                            if (isset($record[$key])) {
                                $values = $record[$key];
                            }
                        }

                        // Special handling for "st" if both "st" and
                        // "l" are set.
                        if (isset($values['l']) && isset($values['st'])) {
                            $values['l'] .= ', ' . $values['st'];
                            unset($values['st']);
                        }

                        if ($values) {
                            $turbaHash[$value] = implode("\n", $values);
                        }
                        break;

                    default:
                        if (isset($record[$this->_turbaMozillaMap[$value]])) {
                            $turbaHash[$value] = $record[$this->_turbaMozillaMap[$value]];
                        }
                        break;
                    }
                }

                $data[] = $turbaHash;
            }

            unset($_SESSION['import_data']['data']);
            return $data;

        default:
            return parent::nextStep($action, $param);
        }
    }

}
