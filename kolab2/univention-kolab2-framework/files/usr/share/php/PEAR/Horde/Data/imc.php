<?php
/**
 * Abstract implementation of the Horde_Data:: API for IMC data -
 * vCards and iCalendar data, etc. Provides a number of utility
 * methods that vCard and iCalendar implementation can share and rely
 * on.
 *
 * $Horde: framework/Data/Data/imc.php,v 1.29 2004/03/16 21:39:41 chuck Exp $
 *
 * Copyright 1999-2004 Jan Schneider <jan@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @package Horde_Data
 * @since   Horde 3.0
 */
class Horde_Data_imc extends Horde_Data {

    var $_objects = array();

    /**
     * According to RFC 2425, we should always use CRLF-terminated
     * lines.
     * @var string $_newline
     */
    var $_newline = "\r\n";

    function importData($text)
    {
        $lines = preg_split('/(\r\n|\n|\r)/', $text);
        $data = array();

        // Unfolding.
        $countData = 0;
        foreach ($lines as $line) {
            if (preg_match('/^[ \t]/', $line) && $countData > 1) {
                $data[$countData - 1] .= substr($line, 1);
            } elseif (trim($line) != '') {
                $data[] = $line;
                $countData++;
            }
            $data[$countData - 1] = trim($data[$countData - 1]);
        }

        $lines = $data;
        $data = array();
        foreach ($lines as $line) {
            $line = preg_replace('/"([^":]*):([^":]*)"/', "\"\\1\x00\\2\"", $line);
            if (!strstr($line, ':')) {
                return PEAR::raiseError(_("Import Error: Malformed line."));
            }
            list($name, $value) = explode(':', $line, 2);
            $name = preg_replace('/\0/', ':', $name);
            $value = preg_replace('/\0/', ':', $value);
            $name = explode(';', $name);
            $params = array();
            if (isset($name[1])) {
                $iMax = count($name);
                for ($i = 1; $i < $iMax; $i++) {
                    $name_value = explode('=', $name[$i]);
                    $paramname = $name_value[0];
                    $paramvalue = isset($name_value[1]) ? $name_value[1] : null;
                    if (isset($paramvalue)) {
                        preg_match_all('/("((\\\\"|[^"])*)"|[^,]*)(,|$)/', $paramvalue, $split);
                        for ($j = 0; $j < count($split[1]) - 1; $j++) {
                            $params[$paramname][] = stripslashes($split[1][$j]);
                        }
                    } else {
                        $params[$paramname] = true;
                    }
                }
            }

            // Store unsplitted value for vCard 2.1.
            $value21 = $value;

            $value = preg_replace('/\\\\,/', "\x00", $value);
            $values = explode(',', $value);
            for ($i = 0; $i < count($values); $i++) {
                $values[$i] = preg_replace('/\0/', ',', $values[$i]);
                $values[$i] = preg_replace('/\\\\n/', "\n", $values[$i]);
                $values[$i] = preg_replace('/\\\\,/', ',', $values[$i]);
                $values[$i] = preg_replace('/\\\\\\\\/', '\\', $values[$i]);
            }

            $data[] = array('name' => $name[0],
                            'params' => $params,
                            'values' => $values,
                            'value21' => $value21);
        }
        $start = 0;
        $this->_build($data, $start);
        return $this->_objects;
    }

    function read($attribute, $index = 0)
    {
        $value = $attribute['values'][$index];

        if (isset($attribute['params']['ENCODING'])) {
            switch ($attribute['params']['ENCODING'][0]) {
            case 'QUOTED-PRINTABLE':
                $value = quoted_printable_decode($value);
                break;
            }
        }

        if (isset($attribute['params']['QUOTED-PRINTABLE']) && ($attribute['params']['QUOTED-PRINTABLE'] == true)) {
            $value = quoted_printable_decode($value);
        }

        if (isset($attribute['params']['CHARSET'])) {
            $value = String::convertCharset($value, $attribute['params']['CHARSET'][0]);
        } else {
            // As per RFC 2279, assume UTF8 if we don't have an
            // explicit charset parameter.
            $value = String::convertCharset($value, 'utf-8');
        }

        return $value;
    }

    function readAll($attribute)
    {
        $count = count($attribute['values']);
        $value = '';
        for ($i = 0; $i < $count; $i++) {
            $value .= $this->read($attribute, $i) . $this->_newline;
        }

        return substr($value, 0, -(strlen($this->_newline)));
    }

    function makeDate($dateOb)
    {
        // FIXME: We currently handle only "full" offsets, not TZs
        // like +1030.
        $TZOffset = substr(date('O'), 0, 3);
        $thisHour = $dateOb->hour - $TZOffset;
        if ($thisHour < 0) {
            require_once 'Date/Calc.php';
            $prevday = Date_Calc::prevDay($dateOb->mday, $dateOb->month, $dateOb->year);
            $dateOb->mday = substr($prevday, 6, 2);
            $dateOb->month = substr($prevday, 4, 2);
            $dateOb->year = substr($prevday, 0, 4);
            $thisHour += 24;
        }
        return sprintf('%04d%02d%02dT%02d%02d%02dZ',
                       $dateOb->year,
                       $dateOb->month,
                       $dateOb->mday,
                       $thisHour,
                       $dateOb->min,
                       $dateOb->sec);
    }

    function makeDuration($seconds)
    {
        $duration = '';
        if ($seconds < 0) {
            $duration .= '-';
            $seconds *= -1;
        }
        $duration .= 'P';
        $days = floor($seconds / 86400);
        $seconds = $seconds % 86400;
        $weeks = floor($days / 7);
        $days = $days % 7;
        if ($weeks) {
            $duration .= $weeks . "W";
        }
        if ($days) {
            $duration .= $days . "D";
        }
        if ($seconds) {
            $duration .= 'T';
            $hours = floor($seconds / 3600);
            $seconds = $seconds % 3600;
            if ($hours > 0) {
                $duration .= $hours . 'H';
            }
            $minutes = floor($seconds / 60);
            $seconds = $seconds % 60;
            if ($minutes) {
                $duration .= $minutes . 'M';
            }
            if ($seconds) {
                $seconds .= $seconds . 'S';
            }
        }
        return $duration;
    }

    function mapDate($datestring)
    {
        if (strpos($datestring, 'T') !== false) {
            list($date, $time) = explode('T', $datestring);
        } else {
            $date = $datestring;
        }

        if (strlen($date) == 10) {
            $dates = explode('-', $date);
        } else {
            $dates = array();
            $dates[] = substr($date, 0, 4);
            $dates[] = substr($date, 4, 2);
            $dates[] = substr($date, 6, 2);
        }

        $dateOb = array('mday' => $dates[2],
                        'month' => $dates[1],
                        'year' => $dates[0]);

        if (isset($time)) {
            @list($time, $zone) = explode('Z', $time);
            if (strstr($time, ':') !== false) {
                $times = explode(':', $time);
            } else {
                $times = array(substr($time, 0, 2),
                               substr($time, 2, 2),
                               substr($time, 4));
            }
            if (isset($zone)) {
                // Map the timezone here.
            }

            $TZOffset = substr(date('O'), 0, 3);
            $dateOb['hour'] = $times[0] + $TZOffset;
            $dateOb['min'] = $times[1];
            $dateOb['sec'] = $times[2];
        } else {
            $dateOb['hour'] = 0;
            $dateOb['min'] = 0;
            $dateOb['sec'] = 0;
        }

        // Put a timestamp in here, too.
        $func = isset($zone) ? 'gmmktime' : 'mktime';
        $dateOb['ts'] = $func($dateOb['hour'], $dateOb['min'], $dateOb['sec'],
                              $dateOb['month'], $dateOb['mday'], $dateOb['year']);

        return $dateOb;
    }

    function count()
    {
        return count($this->_objects);
    }

    function toHash()
    {
        return array();
    }

    function fromHash()
    {
        return array();
    }

    function _quoteAndFold($string)
    {
        $lines = preg_split('/(\r\n|\n|\r)/', rtrim($string));
        $valueLines = array();
        foreach ($lines as $line) {
            if (strlen($line) > 75) {
                $foldedline = '';
                $firstline = true;
                while (!empty($line)) {
                    /* Make first line shorter to allow for the field
                     * name. */
                    if ($firstline) {
                        $len = 60;
                        $firstline = false;
                    } else {
                        $len = 75;
                    }

                    $foldedline .= (empty($foldedline)) ? substr($line, 0, $len) : $this->_newline . ' ' . substr($line, 0, $len);
                    if (strlen($line) <= $len) {
                        $line = '';
                    } else {
                        $line = substr($line, $len);
                    }
                }
                $valueLines[] = $foldedline;
            } else {
                $valueLines[] = $line;
            }
        }

        return implode($this->_newline . ' ', $valueLines) . $this->_newline;
    }

}
