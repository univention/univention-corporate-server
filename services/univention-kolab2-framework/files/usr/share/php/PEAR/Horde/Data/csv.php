<?php
/**
 * Horde_Data implementation for comma-separated data (CSV).
 *
 * $Horde: framework/Data/Data/csv.php,v 1.28 2004/04/16 17:20:03 jan Exp $
 *
 * Copyright 1999-2004 Jan Schneider <jan@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3
 * @package Horde_Data
 */
class Horde_Data_csv extends Horde_Data {

    var $_extension = 'csv';
    var $_contentType = 'text/comma-separated-values';

    /**
     * Tries to dicover the CSV file's parameters.
     *
     * @access public
     * @param string $filename  The name of the file to investigate
     * @return array            An associative array with the following
     *                          possible keys:
     * 'sep':    The field seperator
     * 'quote':  The quoting character
     * 'fields': The number of fields (columns)
     */
    function discoverFormat($filename)
    {
        @include_once('File/CSV.php');
        if (class_exists('File_CSV')) {
            return File_CSV::discoverFormat($filename);
        } else {
            return array('sep' => ',');
        }
    }

    /**
     * Imports and parses a CSV file.
     *
     * @access public
     *
     * @param string  $filename  The name of the file to parse
     * @param boolean $header    Does the first line contain the field/column names?
     * @param string  $sep       The field/column seperator
     * @param string  $quote     The quoting character
     * @param integer $fields    The number or fields/columns
     *
     * @return array             A two-dimensional array of all imported data rows.
     *                           If $header was true the rows are associative arrays
     *                           with the field/column names as the keys.
     */
    function importFile($filename, $header = false, $sep = '', $quote = '', $fields = null)
    {
        @include_once('File/CSV.php');

        $data = array();

        /* File_CSV is present. */
        if (class_exists('File_CSV')) {
            /* File_CSV is a bit picky at what parameter it
               expects. */
            $conf = array();
            if (!empty($quote)) {
                $conf['quote'] = $quote;
            }
            if (empty($sep)) {
                $conf['sep'] = ',';
            } else {
                $conf['sep'] = $sep;
            }
            if ($fields) {
                $conf['fields'] = $fields;
            } else {
                return $data;
            }

            /* Strip and keep the first line if it contains the field
               names. */
            if ($header) {
                $head = File_CSV::read($filename, $conf);
            }

            while ($line = File_CSV::read($filename, $conf)) {
                if (!isset($head)) {
                    $data[] = $line;
                } else {
                    $newline = array();
                    for ($i = 0; $i < count($head); $i++) {
                        $newline[$head[$i]] = empty($line[$i]) ? '' : $line[$i];
                    }
                    $data[] = $newline;
                }
            }

            $fp = File_CSV::getPointer($filename, $conf);
            if ($fp) {
                rewind($fp);
            }

        /* Fall back to fgetcsv(). */
        } else {
            $fp = fopen($filename, 'r');
            if (!$fp) {
                return false;
            }

            /* Strip and keep the first line if it contains the field
               names. */
            if ($header) {
                $head = fgetcsv($fp, 1024, $sep);
            }
            while ($line = fgetcsv($fp, 1024, $sep)) {
                if (!isset($head)) {
                    $data[] = $line;
                } else {
                    $newline = array();
                    for ($i = 0; $i < count($head); $i++) {
                        $newline[$head[$i]] = empty($line[$i]) ? '' : $line[$i];
                    }
                    $data[] = $newline;
                }
            }

            fclose($fp);
        }
        return $data;
    }

    /**
     * Builds a CSV file from a given data structure and returns it as
     * a string.
     *
     * @access public
     *
     * @param array   $data       A two-dimensional array containing the data
     *                            set.
     * @param boolean $header     If true, the rows of $data are associative
     *                            arrays with field names as their keys.
     *
     * @return string  The CSV data.
     */
    function exportData($data, $header = false)
    {
        if (!is_array($data) || count($data) == 0) {
            return '';
        }

        $export = '';
        if ($header) {
            $head = current($data);
            foreach (array_keys($head) as $key) {
                if (!empty($key)) {
                    $export .= '"' . $key . '"';
                }
                $export .= ',';
            }
            $export = substr($export, 0, -1) . "\n";
        }

        foreach ($data as $row) {
            foreach ($row as $cell) {
                if (!empty($cell) || $cell === 0) {
                    $export .= '"' . $cell . '"';
                }
                $export .= ',';
            }
            $export = substr($export, 0, -1) . "\n";
        }

        return $export;
    }

    /**
     * Builds a CSV file from a given data structure and triggers its
     * download. It DOES NOT exit the current script but only outputs
     * the correct headers and data.
     *
     * @access public
     *
     * @param string  $filename   The name of the file to be downloaded.
     * @param array   $data       A two-dimensional array containing the data set.
     * @param boolean $header     If true, the rows of $data are associative arrays
     *                            with field names as their keys.
     */
    function exportFile($filename, $data, $header = false)
    {
        $export = $this->exportData($data, $header);
        $GLOBALS['browser']->downloadHeaders($filename, 'application/csv', false, strlen($export));
        echo $export;
    }

    /**
     * Takes all necessary actions for the given import step,
     * parameters and form values and returns the next necessary step.
     *
     * @access public
     *
     * @param integer $action        The current step. One of the IMPORT_*
     *                               constants.
     * @param optonal array $param   An associative array containing needed
     *                               parameters for the current step.
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

            /* Move uploaded file so that we can read it again in the
               next step after the user gave some format details. */
            $file_name = Horde::getTempFile('import', false);
            if (!move_uploaded_file($_FILES['import_file']['tmp_name'], $file_name)) {
                return PEAR::raiseError(_("The uploaded file could not be saved."));
            }
            $_SESSION['import_data']['file_name'] = $file_name;

            /* Try to discover the file format ourselves. */
            $conf = $this->discoverFormat($file_name);
            if (!$conf) {
                $conf = array('sep' => ',');
            }
            $_SESSION['import_data'] = array_merge($_SESSION['import_data'], $conf);

            /* Read the file's first two lines to show them to the
               user. */
            $_SESSION['import_data']['first_lines'] = '';
            $fp = @fopen($file_name, 'r');
            if ($fp) {
                $line_no = 1;
                while ($line_no < 3 && $line = fgets($fp)) {
                    $newline = String::length($line) > 100 ? "\n" : '';
                    $_SESSION['import_data']['first_lines'] .= substr($line, 0, 100) . $newline;
                    $line_no++;
                }
            }
            return IMPORT_CSV;

        case IMPORT_CSV:
            $_SESSION['import_data']['header'] = Util::getFormData('header');
            $import_data = $this->importFile($_SESSION['import_data']['file_name'],
                                             $_SESSION['import_data']['header'],
                                             Util::getFormData('sep'),
                                             Util::getFormData('quote'),
                                             Util::getFormData('fields'));
            $_SESSION['import_data']['data'] = $import_data;
            unset($_SESSION['import_data']['map']);
            return IMPORT_MAPPED;

        default:
            return parent::nextStep($action, $param);
        }
    }

}
