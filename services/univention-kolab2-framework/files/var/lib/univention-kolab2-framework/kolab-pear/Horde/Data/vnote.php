<?php

/** We rely on the Horde_Data_imc:: abstract class. */
require_once dirname(__FILE__) . '/imc.php';

/**
 * Implement the Horde_Data:: API for vNote data.
 *
 * $Horde: framework/Data/Data/vnote.php,v 1.6 2004/02/24 19:49:03 chuck Exp $
 *
 * Copyright 1999-2004 Jan Schneider <jan@horde.org>
 * Copyright 1999-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @package Horde_Data
 * @since   Horde 3.0
 */
class Horde_Data_vnote extends Horde_Data_imc {

    /**
     * The vNote version.
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
     * Builds a vNote file from a given data structure and returns it
     * as a string.
     *
     * @access public
     *
     * @param array $data  A two-dimensional array containing the data set.
     *
     * @return string  The vNote data.
     */
    function exportData($data)
    {
        /* According to RFC 2425, we should always use CRLF-terminated
         * lines. */
        $newline = "\r\n";

        $file = "BEGIN:VNOTE${newline}VERSION:1.1${newline}";
        foreach ($data as $key => $val) {
            if (!empty($val)) {
                // Basic encoding. Newlines for now; more work here to
                // make this RFC-compliant.
                $file .= $key . ':' .  $this->_quoteAndFold($val);
            }
        }
        $file .= "END:VNOTE$newline";

        return $file;
    }

    /**
     * Builds a vNote file from a given data structure and triggers
     * its download. It DOES NOT exit the current script but only
     * outputs the correct headers and data.
     *
     * @access public
     *
     * @param string $filename   The name of the file to be downloaded.
     * @param array  $data       A two-dimensional array containing the data set.
     */
    function exportFile($filename, $data)
    {
        $export = $this->exportData($data);
        $GLOBALS['browser']->downloadHeaders($filename, 'text/plain', false, strlen($export));
        echo $export;
    }

    /**
     * Return a data hash from a vNote object.
     *
     * @param array $note  The note to convert.
     *
     * @return array  The hashed data.
     *
     * @since Horde 3.0
     */
    function toHash($note)
    {
        $this->_version = isset($note['version']) ? $note['version'] : null;
        $hash = array();
        foreach ($note['params'] as $item) {
            switch ($item['name']) {
            case 'DCREATED':
                $hash['created'] = $this->mapDate($this->read($item));
                break;

            case 'LAST-MODIFIED':
                $hash['modified'] = $this->mapDate($this->read($item));
                break;

            case 'BODY':
                $hash['body'] = $this->readAll($item);
                break;
            }
        }

        return $hash;
    }

    /**
     * Turn a hash (of the same format that we output in
     * Horde_Data_vnote) into an array of vNote data.
     *
     * @param array $hash  The hash of attributes.
     *
     * @return array  The array of vNote attributes -> vNote values.
     *
     * @since Horde 3.0
     */
    function fromHash($hash)
    {
        $note = array();
        foreach ($hash as $key => $val) {
            switch ($key) {
            case 'created':
                $note['DCREATED'] = $this->makeDate((object)$val);
                break;

            case 'modified':
                $note['LAST-MODIFIED'] = $this->makeDate((object)$val);
                break;

            case 'body':
                $note['BODY'] = $val;
                break;
            }
        }

        return $note;
    }

    /**
     * Takes all necessary actions for the given import step,
     * parameters and form values and returns the next necessary step.
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
                if ($object['type'] == 'VNOTE') {
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

}
