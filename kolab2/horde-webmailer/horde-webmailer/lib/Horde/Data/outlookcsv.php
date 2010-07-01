<?php

require_once 'Horde/Data/csv.php';

/**
 * Horde_Data implementation for Outlook comma-separated data (CSV).
 *
 * $Horde: framework/Data/Data/outlookcsv.php,v 1.3.10.4 2007-12-20 13:48:56 jan Exp $
 *
 * @package Horde_Data
 */
class Horde_Data_outlookcsv extends Horde_Data_csv {

    /**
     * Builds a CSV file from a given data structure and returns it as a
     * string.
     *
     * @param array   $data       A two-dimensional array containing the data
     *                            set.
     * @param boolean $header     If true, the rows of $data are associative
     *                            arrays with field names as their keys.
     *
     * @return string  The CSV data.
     */
    function exportData($data, $header = false, $export_mapping = array())
    {
        if (!is_array($data) || count($data) == 0) {
            return '';
        }

        $export = '';
        $eol = "\r\n";
        $head = array_keys(current($data));
        if ($header) {
            foreach ($head as $key) {
                if (!empty($key)) {
                    if (isset($export_mapping[$key])) {
                        $key = $export_mapping[$key];
                    }
                    $export .= '"' . $key . '"';
                }
                $export .= ',';
            }
            $export = substr($export, 0, -1) . $eol;
        }

        foreach ($data as $row) {
            foreach ($head as $key) {
                $cell = $row[$key];
                if (!empty($cell) || $cell === 0) {
                    $cell = preg_replace("/\"/", "\"\"", $cell);
                    $export .= '"' . $cell . '"';
                }
                $export .= ',';
            }
            $export = substr($export, 0, -1) . $eol;
        }

        return $export;
    }

}
