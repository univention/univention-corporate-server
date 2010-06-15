<?php
/**
 * Horde_Data implementation for tab-separated data (TSV).
 *
 * $Horde: framework/Data/Data/tsv.php,v 1.22 2004/05/25 15:52:44 jan Exp $
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
class Horde_Data_tsv extends Horde_Data {

    var $_extension = 'tsv';
    var $_contentType = 'text/tab-separated-values';

    function importData($contents, $header = false, $delimiter = "\t")
    {
        $contents = explode("\n", $contents);
        $data = array();
        if ($header) {
            $head = explode($delimiter, array_shift($contents));
        }
        foreach ($contents as $line) {
            if (trim($line) == '') {
                continue;
            }
            $line = explode($delimiter, $line);
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
        return $data;
    }

    /**
     * Builds a TSV file from a given data structure and returns it as a
     * string.
     *
     * @access public
     * @param array $data        A two-dimensional array containing the data
     *                           set.
     * @param bool $header       If true, the rows of $data are associative
     *                           arrays with field names as their keys.
     * @return string            The TSV data.
     */
    function exportData($data, $header = false)
    {
        if (!is_array($data) || count($data) == 0) {
            return '';
        }
        $export = '';
        if ($header) {
            $export = implode("\t", array_keys(current($data))) . "\n";
        }
        foreach ($data as $row) {
            $export .= implode("\t", $row) . "\n";
        }
        return $export;
    }

    /**
     * Builds a TSV file from a given data structure and triggers its download.
     * It DOES NOT exit the current script but only outputs the correct headers
     * and data.
     *
     * @access public
     * @param string $filename   The name of the file to be downloaded.
     * @param array $data        A two-dimensional array containing the data set.
     * @param bool $header       If true, the rows of $data are associative arrays
     *                           with field names as their keys.
     */
    function exportFile($filename, $data, $header = false)
    {
        $export = $this->exportData($data, $header);
        $GLOBALS['browser']->downloadHeaders($filename, 'text/tab-separated-values', false, strlen($export));
        echo $export;
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

            if ($_SESSION['import_data']['format'] == 'mulberry' ||
                $_SESSION['import_data']['format'] == 'pine') {
                $_SESSION['import_data']['data'] = $this->importFile($_FILES['import_file']['tmp_name']);
                $format = $_SESSION['import_data']['format'];
                if ($format == 'mulberry') {
                    $appKeys  = array('alias', 'name', 'email', 'company', 'workAddress', 'workPhone', 'homePhone', 'fax', 'notes');
                    $dataKeys = array(0, 1, 2, 3, 4, 5, 6, 7, 9);
                } elseif ($format == 'pine') {
                    $appKeys = array('alias', 'name', 'email', 'notes');
                    $dataKeys = array(0, 1, 2, 4);
                }
                foreach ($appKeys as $key => $app) {
                    $map[$dataKeys[$key]] = $app;
                }
                $data = array();
                foreach ($_SESSION['import_data']['data'] as $row) {
                    $hash = array();
                    if ($format == 'mulberry') {
                        if (preg_match("/^Grp:/", $row[0])) {
                            continue;
                        }
                        $row[1] = preg_replace('/^([^,"]+),\s*(.*)$/', '$2 $1', $row[1]);
                        foreach ($dataKeys as $key) {
                            if (array_key_exists($key, $row)) {
                                $hash[$key] = stripslashes(preg_replace('/\\\\r/', "\n", $row[$key]));
                            }
                        }
                    } elseif ($format = 'pine') {
                        if (count($row) < 3 || preg_match("/^#DELETED/", $row[0]) || preg_match("/[()]/", $row[2])) {
                            continue;
                        }
                        $row[1] = preg_replace('/^([^,"]+),\s*(.*)$/', '$2 $1', $row[1]);
                        foreach ($dataKeys as $key) {
                            if (array_key_exists($key, $row)) {
                                $hash[$key] = $row[$key];
                            }
                        }
                    }
                    $data[] = $hash;
                }
                $_SESSION['import_data']['data'] = $data;
                $_SESSION['import_data']['map'] = $map;
                $ret = $this->nextStep(IMPORT_DATA, $param);
                return $ret;
            }

            /* Move uploaded file so that we can read it again in the next step
               after the user gave some format details. */
            $uploaded = Browser::wasFileUploaded('import_file', _("TSV file"));
            if (is_a($uploaded, 'PEAR_Error')) {
                return PEAR::raiseError($uploaded->getMessage());
            }
            $file_name = Horde::getTempFile('import', false);
            if (!move_uploaded_file($_FILES['import_file']['tmp_name'], $file_name)) {
                return PEAR::raiseError(_("The uploaded file could not be saved."));
            }
            $_SESSION['import_data']['file_name'] = $file_name;

            /* Read the file's first two lines to show them to the user. */
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
            return IMPORT_TSV;
            break;

        case IMPORT_TSV:
            $_SESSION['import_data']['header'] = Util::getFormData('header');
            $import_data = $this->importFile($_SESSION['import_data']['file_name'],
                                             $_SESSION['import_data']['header']);
            $_SESSION['import_data']['data'] = $import_data;
            unset($_SESSION['import_data']['map']);
            return IMPORT_MAPPED;
            break;

        default:
            return parent::nextStep($action, $param);
            break;
        }
    }

}
