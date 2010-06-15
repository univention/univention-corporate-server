<?php
/**
 * Class representing iCalendar files.
 *
 * $Horde: framework/iCalendar/iCalendar.php,v 1.43 2004/04/26 19:57:18 chuck Exp $
 *
 * Copyright 2003-2004 Mike Cochrane <mike@graftonhall.co.nz>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_iCalendar
 */
class Horde_iCalendar {

    var $_container = null;

    var $_attributes = array();

    var $_components = array();

    /**
     * According to RFC 2425, we should always use CRLF-terminated
     * lines.
     * @var string $_newline
     */
    var $_newline = "\r\n";

    /**
     * Return a reference to a new component.
     *
     * @param string $type       The type of component to return
     * @param object $container  A container that this component
     *                           will be associtated with.
     *
     * @return object  Reference to a Horde_iCalendar_* object as specified.
     */
    function &newComponent($type, &$container)
    {
        $type = String::lower($type);
        $class = 'Horde_iCalendar_' . $type;
        @include_once dirname(__FILE__) . '/iCalendar/' . $type . '.php';
        if (class_exists($class)) {
            return $ret = &new $class($container);
        } else {
            // Should return an dummy x-unknown type class here.
            return false;
        }
    }

    /**
     * Set the value of an attribute.
     *
     * @param string  $name   The name of the attribute.
     * @param string  $value  The value of the attribute.
     * @param array   $params (optional) Array containing any addition
     *                        parameters for this attribute.
     * @param boolean $append (optional) True to append the attribute, False
     *                        to replace the first matching attribute found.
     */
    function setAttribute($name, $value, $params = array(), $append = true)
    {
        $found = $append;
        $keys = array_keys($this->_attributes);
        foreach ($keys as $key) {
            if ($found) break;
            if ($this->_attributes[$key]['name'] == $name) {
                $this->_attributes[$key]['params'] = $params;
                $this->_attributes[$key]['value'] = $value;
                $found = true;
            }
        }

        if ($append || !$found) {
            $this->_attributes[] = array(
                'name'      => $name,
                'params'    => $params,
                'value'     => $value
            );
        }
    }

    /**
     * Get the value of an attribute.
     *
     * @param string  $name    The name of the attribute.
     * @param boolean $params  Return the parameters for this attribute
     *                         instead of its value.
     *
     * @return mixed (object)  PEAR_Error if the attribute does not exist.
     *               (string)  The value of the attribute.
     *               (array)   The parameters for the attribute or
     *                         multiple values for an attribute.
     */
    function getAttribute($name, $params = false)
    {
        $result = array();
        foreach ($this->_attributes as $attribute) {
            if ($attribute['name'] == $name) {
                if ($params) {
                    $result[] = $attribute['params'];
                } else {
                    $result[] = $attribute['value'];
                }
            }
        }
        if (count($result) == 0) {
            return PEAR::raiseError('Attribute "' . $name . '" Not Found');
        } if (count($result) == 1 && !$params) {
            return $result[0];
        } else {
            return $result;
        }
    }

    /**
     * Returns the value of an attribute, or a specified default value
     * if the attribute does not exist.
     *
     * @param string $name     The name of the attribute.
     * @param mixed  $default  (optional) What to return if the attribute
     *                         specified by $name does not exist.
     *
     * @return mixed (string) The value of $name.
     *               (mixed)  $default if $name does not exist.
     */
    function getAttributeDefault($name, $default = '')
    {
        $value = $this->getAttribute($name);
        return is_a($value, 'PEAR_Error') ? $default : $value;
    }

    /**
     * Remove all occurences of an attribute.
     *
     * @param string  $name   The name of the attribute.
     */
    function removeAttribute($name)
    {
        $keys = array_keys($this->_attributes);
        foreach ($keys as $key) {
            if ($this->_attributes[$key]['name'] == $name) {
                unset($this->_attributes[$key]);
            }
        }
    }

    /**
     * Get all attributes.
     *
     * @return array  Array containing all the attributes and their types.
     *
     */
    function getAllAttributes()
    {
        return $this->_attributes;
    }

    /**
     * Add a vCalendar component (eg vEvent, vTimezone, etc.).
     *
     * @param object Horde_iCalendar $component  Component (subclass) to add.
     */
    function addComponent($component)
    {
        if (is_a($component, 'Horde_iCalendar')) {
            $this->_components[] = &$component;
        }
    }

    /**
     * Retrieve all the components.
     *
     * @return array  Array of Horde_iCalendar objects.
     */
    function getComponents()
    {
        return $this->_components;
    }

    /**
     * Retrieve a specific component.
     *
     * @param integer $idx  The index of the object to retrieve.
     *
     * @return mixed    (boolean) False if the index does not exist.
     *                  (Horde_iCalendar_*) The requested component.
     */
    function getComponent($idx)
    {
        if (isset($this->_components[$idx])) {
            return $this->_components[$idx];
        } else {
            return false;
        }
    }

    /**
     * Locates the first child component of the specified class, and
     * returns a reference to this component.
     *
     * @param string $type  The type of component to find.
     *
     * @return mixed    (boolean) False if no subcomponent of the specified
     *                            class exists.
     *                  (Horde_iCalendar_*) A reference to the requested component.
     */
    function &findComponent($childclass)
    {
        $childclass = 'Horde_iCalendar_' . String::lower($childclass);
        $keys = array_keys($this->_components);
        foreach ($keys as $key) {
            if (is_a($this->_components[$key], $childclass)) {
                return $this->_components[$key];
            }
        }

        return false;
    }

    /**
     * Clears the iCalendar object (resets the components and
     * attributes arrays).
     */
    function clear()
    {
        $this->_components = array();
        $this->_attributes = array();
    }

    /**
     * Export as vCalendar format.
     */
    function exportvCalendar()
    {
        // Default values.
        $requiredAttributes['VERSION'] = '2.0';
        $requiredAttributes['PRODID'] = '-//The Horde Project//Horde_iCalendar Library, Horde 3.0-cvs //EN';
        $requiredAttributes['METHOD'] = 'PUBLISH';

        foreach ($requiredAttributes as $name => $default_value) {
            if (is_a($this->getattribute($name), 'PEAR_Error')) {
                $this->setAttribute($name, $default_value);
            }
        }

        return $this->_exportvData('VCALENDAR') . $this->_newline;
    }

    /**
     * Parse a string containing vCalendar data.
     *
     * @param string  $text  The data to parse.
     * @param string  $base  The type of the base object.
     * @param boolean $clear (optional) True to clear() the iCal object before parsing.
     */
    function parsevCalendar($text, $base = 'VCALENDAR', $clear = true)
    {
        if ($clear) {
            $this->clear();
        }

        if (preg_match('/(BEGIN:' . $base . '\r?\n)([\W\w]*)(END:' . $base . '\r?\n?)/', $text, $matches)) {
            $vCal = $matches[2];
        } else {
            return false;
        }

        // All subcomponents.
        $matches = null;
        if (preg_match_all('/BEGIN:([\W\w]*)(\r\n|\r|\n)([\W\w]*)END:\1(\r\n|\r|\n)/U', $vCal, $matches)) {
            foreach ($matches[0] as $key => $data) {
                $type = $matches[1][$key];

                $component = &Horde_iCalendar::newComponent(trim($type), $this);
                $component->parsevCalendar($data);

                $this->addComponent($component);

                // Remove from the vCalendar data.
                $vCal = str_replace($data, '', $vCal);
            }
        }

        // Unfold any folded lines.
        $vCal = preg_replace ('/(\r|\n)+ /', '', $vCal);

        // Parse the remaining attributes.
        if (preg_match_all('/(.*):(.*)(\r|\n)+/', $vCal, $matches)) {
            foreach ($matches[0] as $attribute) {
                preg_match('/([^;^:]*)((;[^:]*)?):(.*)/', $attribute, $parts);
                $tag = $parts[1];
                $value = $parts[4];
                $params = array();

                if (!empty($parts[2])) {
                    preg_match_all('/;(([^;=]*)(=([^;]*))?)/', $parts[2], $param_parts);
                    foreach ($param_parts[2] as $key => $paramName) {
                        $paramValue = $param_parts[4][$key];
                        $params[$paramName] = $paramValue;
                    }
                }

                switch ($tag) {
                case 'DESCRIPTION':
		case 'SUMMARY':
		case 'LOCATION':
                    $value = preg_replace('/\\\\,/', ',', $value);
                    $value = preg_replace('/\\\\;/', ';', $value);
                    $value = preg_replace('/\\\\n/', $this->_newline, $value);
                    $value = preg_replace('/\\\\N/', $this->_newline, $value);
                    $value = preg_replace('/\\\\\\\\/', '\\\\', $value);
                    $this->setAttribute($tag, $value, $params);
                    break;

                // Date fields.
                case 'DTSTAMP':
                case 'COMPLETED':
                case 'CREATED':
                case 'LAST-MODIFIED':
                    $this->setAttribute($tag, $this->_parseDateTime($value), $params);
                    break;

                case 'DTEND':
                case 'DTSTART':
                case 'DUE':
                case 'RECURRENCE-ID':
                    if (isset($params['VALUE']) && $params['VALUE'] == 'DATE') {
                        $this->setAttribute($tag, $this->_parseDate($value), $params);
                    } else {
                        $this->setAttribute($tag, $this->_parseDateTime($value), $params);
                    }
                    break;

                case 'RDATE':
                    if (isset($params['VALUE'])) {
                        if ($params['VALUE'] == 'DATE') {
                            $this->setAttribute($tag, $this->_parseDate($value), $params);
                        } elseif ($params['VALUE'] == 'PERIOD') {
                            $this->setAttribute($tag, $this->_parsePeriod($value), $params);
                        } else {
                            $this->setAttribute($tag, $this->_parseDateTime($value), $params);
                        }
                    } else {
                        $this->setAttribute($tag, $this->_parseDateTime($value), $params);
                    }
                    break;

                case 'TRIGGER':
                    if (isset($params['VALUE'])) {
                        if ($params['VALUE'] == 'DATE-TIME') {
                            $this->setAttribute($tag, $this->_parseDateTime($value), $params);
                        } else {
                            $this->setAttribute($tag, $this->_parseDuration($value), $params);
                        }
                    } else {
                        $this->setAttribute($tag, $this->_parseDuration($value), $params);
                    }
                    break;

                // Comma seperated dates.
                case 'EXDATE':
                    $values = array();
                    $dates = array();
                    preg_match_all('/,([^,]*)/', ',' . $value, $values, PREG_PATTERN_ORDER );
                    foreach ($values[1] as $value) {
                        if (isset($params['VALUE'])) {
                            if ($params['VALUE'] == 'DATE-TIME') {
                                $dates[] = $this->_parseDateTime($value);
                            } elseif ($params['VALUE'] == 'DATE') {
                                $dates[] = $this->_parseDate($value);
                            }
                        } else {
                            $dates[] = $this->_parseDateTime($value);
                        }
                    }
                    $this->setAttribute($tag, $dates, $params);
                    break;

                // Duration fields.
                case 'DURATION':
                    $this->setAttribute($tag, $this->_parseDuration($value), $params);
                    break;

                // Period of time fields.
                case 'FREEBUSY':
                    $values = array();
                    $periods = array();
                    preg_match_all('/,([^,]*)/', ',' . $value, $values);
                    foreach ($values[1] as $value) {
                        $periods[] = $this->_parsePeriod($value);
                    }

                    $this->setAttribute($tag, $periods, $params);
                    break;

                // UTC offset fields.
                case 'TZOFFSETFROM':
                case 'TZOFFSETTO':
                    $this->setAttribute($tag, $this->_parseUtcOffset($value), $params);
                    break;

                // Integer fields.
                case 'PERCENT-COMPLETE':
                case 'PRIORITY':
                case 'REPEAT':
                case 'SEQUENCE':
                    $this->setAttribute($tag, intval($value), $params);
                    break;

                // Geo fields.
                case 'GEO':
                    $floats = split(';', $value);
                    $value['latitude'] = floatval($floats[0]);
                    $value['longitude'] = floatval($floats[1]);
                    $this->setAttribute($tag, $value, $params);
                    break;

                // Recursion fields.
                case 'EXRULE':
                case 'RRULE':

                // String fields.
                default:
                    $this->setAttribute($tag, trim($value), $params);
                    break;
                }
            }
        }

        return true;
    }

    /**
     * Export this component in vCal format.
     *
     * @param string $base  (optional) The type of the base object.
     *
     * @return string  vCal format data.
     */
    function _exportvData($base = 'VCALENDAR')
    {
        $result  = 'BEGIN:' . $base . $this->_newline;

        foreach ($this->_attributes as $attribute) {
            $name = $attribute['name'];
            $params = $attribute['params'];
            $params_str = '';

            if (count($params) > 0) {
                foreach ($params as $param_name => $param_value) {
                    $params_str .= ";$param_name=$param_value";
                }
            }

            $value = $attribute['value'];
            switch ($name) {
            // Date fields.
            case 'DTSTAMP':
            case 'COMPLETED':
            case 'CREATED':
            case 'LAST-MODIFIED':
                $value = $this->_exportDateTime($value);
                break;

            case 'DTEND':
            case 'DTSTART':
            case 'DUE':
            case 'RECURRENCE-ID':
                if (isset($params['VALUE'])) {
                    if ($params['VALUE'] == 'DATE') {
                        $value = $this->_exportDate($value);
                    } else {
                        $value = $this->_exportDateTime($value);
                    }
                } else {
                    $value = $this->_exportDateTime($value);
                }
                break;

            case 'RDATE':
                if (isset($params['VALUE'])) {
                    if ($params['VALUE'] == 'DATE') {
                        $value = $this->_exportDate($value);
                    } elseif ($params['VALUE'] == 'PERIOD') {
                        $value = $this->_exportPeriod($value);
                    } else {
                        $value = $this->_exportDateTime($value);
                    }
                } else {
                    $value = $this->_exportDateTime($value);
                }
                break;

            case 'TRIGGER':
                if (isset($params['VALUE'])) {
                    if ($params['VALUE'] == 'DATE-TIME') {
                        $value = $this->_exportDateTime($value);
                    } elseif ($params['VALUE'] == 'DURATION') {
                        $value = $this->_exportDuration($value);
                    }
                } else {
                    $value = $this->_exportDuration($value);
                }
                break;

            // Duration fields.
            case 'DURATION':
                $value = $this->_exportDuration($value);
                break;

            // Period of time fields.
            case 'FREEBUSY':
                $value_str = '';
                foreach ($value as $period) {
                    $value_str .= empty($value_str) ? '' : ',';
                    $value_str .= $this->_exportPeriod($period);
                }
                $value = $value_str;
                break;

            // UTC offset fields.
            case 'TZOFFSETFROM':
            case 'TZOFFSETTO':
                $value = $this->_exportUtcOffset($value);
                break;

            // Integer fields.
            case 'PERCENT-COMPLETE':
            case 'PRIORITY':
            case 'REPEAT':
            case 'SEQUENCE':
                $value = "$value";
                break;

            // Geo fields.
            case 'GEO':
                $value = $value['latitude'] . ',' . $value['longitude'];
                break;

            // Recurrence fields.
            case 'EXRULE':
            case 'RRULE':
            }
	    $value = preg_replace('/\\\\/', '\\\\\\\\', $value);
	    $value = preg_replace('/,/', '\\,', $value);
	    $value = preg_replace('/;/', '\\;', $value);
	    $value = preg_replace('/'.$this->_newline.'/', '\\n', $value);

            $attr_string = "$name$params_str:$value";
            $result .= $this->_foldLine($attr_string) . $this->_newline;
        }

        foreach ($this->getComponents() as $component) {
            $result .= $component->exportvCalendar($this) . $this->_newline;
        }

        $result .= 'END:' . $base;

        return $result;
    }

    /**
     * Parse a UTC Offset field.
     */
    function _parseUtcOffset($text)
    {
        $offset = array();
        if (preg_match('/(\+|-)([0-9]{2})([0-9]{2})([0-9]{2})?/', $text, $timeParts)) {
            $offset['ahead']  = (boolean)($timeParts[1] == '+');
            $offset['hour']   = intval($timeParts[2]);
            $offset['minute'] = intval($timeParts[3]);
            if (isset($timeParts[4])) {
                $offset['second'] = intval($timeParts[4]);
            }
            return $offset;
        } else {
            return false;
        }
    }

    /**
     * Export a UTC Offset field.
     */
    function _exportUtcOffset($value)
    {
        $offset = $value['ahead'] ? '+' : '-';
        $offset .= sprintf('%02d%02d',
                           $value['hour'], $value['minute']);
        if (isset($value['second'])) {
            $offset .= sprintf('%02d', $value['second']);
        }

        return $offset;
    }

    /**
     * Parse a Time Period field.
     */
    function _parsePeriod($text)
    {
        $periodParts = split('/', $text);

        $start = $this->_parseDateTime($periodParts[0]);

        if ($duration = $this->_parseDuration($periodParts[1])) {
            return array('start' => $start, 'duration' => $duration);
        } elseif ($end = $this->_parseDateTime($periodParts[1])) {
            return array('start' => $start, 'end' => $end);
        }
    }

    /**
     * Export a Time Period field.
     */
    function _exportPeriod($value)
    {
        $period = $this->_exportDateTime($value['start']);
        $period .= '/';
        if (isset($value['duration'])) {
            $period .= $this->_exportDuration($value['duration']);
        } else {
            $period .= $this->_exportDateTime($value['end']);
        }
        return $period;
    }

    /**
     * Parse a DateTime field into a unix timestamp.
     */
    function _parseDateTime($text)
    {
        $dateParts = split('T', $text);
        if (count($dateParts) != 2 && !empty($text)) {
            // Not a datetime field but may be just a date field.
            if (!$date = $this->_parseDate($text)) {
                return $date;
            }
            return @gmmktime(0, 0, 0, $date['month'], $date['mday'], $date['year']);
        }

        if (!$date = $this->_parseDate($dateParts[0])) {
            return $date;
        }
        if (!$time = $this->_parseTime($dateParts[1])) {
            return $time;
        }

        if ($time['zone'] == 'UTC') {
            return @gmmktime($time['hour'], $time['minute'], $time['second'],
                             $date['month'], $date['mday'], $date['year']);
        } else {
            return @mktime($time['hour'], $time['minute'], $time['second'],
                           $date['month'], $date['mday'], $date['year']);
        }
    }

    /**
     * Export a DateTime field.
     */
    function _exportDateTime($value)
    {
        $temp = array();
        if (!is_object($value) || is_array($value)) {
	  // NOTE(steffen): We store time in UTC only(!)
	  /*
            $TZOffset  = 3600 * substr(date('O',$value), 0, 3);
            $TZOffset += 60 * substr(date('O',$value), 3, 2);
            $value -= $TZOffset;
	  */
            $temp['zone']   = 'UTC';
            $temp['year']   = gmdate('Y', $value);
            $temp['month']  = gmdate('n', $value);
            $temp['mday']   = gmdate('j', $value);
            $temp['hour']   = gmdate('G', $value);
            $temp['minute'] = gmdate('i', $value);
            $temp['second'] = gmdate('s', $value);
        } else {
            $dateOb = (object)$value;

            // Minutes.
            $TZOffset = substr(date('O'), 3, 2);
            $thisMin = $dateOb->min - $TZOffset;

            // Hours.
            $TZOffset = substr(date('O'), 0, 3);
            $thisHour = $dateOb->hour - $TZOffset;

            if ($thisMin < 0) {
                $thisHour -= 1;
                $thisMin += 60;
            }

            if ($thisHour < 0) {
                require_once 'Date/Calc.php';
                $prevday = Date_Calc::prevDay($dateOb->mday, $dateOb->month, $dateOb->year);
                $dateOb->mday  = substr($prevday, 6, 2);
                $dateOb->month = substr($prevday, 4, 2);
                $dateOb->year  = substr($prevday, 0, 4);
                $thisHour += 24;
            }

            $temp['zone']   = 'UTC';
            $temp['year']   = $dateOb->year;
            $temp['month']  = $dateOb->month;
            $temp['mday']   = $dateOb->mday;
            $temp['hour']   = $thisHour;
            $temp['minute'] = $dateOb->min;
            $temp['second'] = $dateOb->sec;
        }

        return Horde_iCalendar::_exportDate($temp) . 'T' . Horde_iCalendar::_exportTime($temp);
    }

    /**
     * Parse a Time field.
     */
    function _parseTime($text)
    {
        if (preg_match('/([0-9]{2})([0-9]{2})([0-9]{2})(Z)?/', $text, $timeParts)) {
            $time['hour'] = intval($timeParts[1]);
            $time['minute'] = intval($timeParts[2]);
            $time['second'] = intval($timeParts[3]);
            if (isset($timeParts[4])) {
                $time['zone'] = 'UTC';
            } else {
                $time['zone'] = 'Local';
            }
            return $time;
        } else {
            return false;
        }
    }

    /**
     * Export a Time field.
     */
    function _exportTime($value)
    {
        $time = sprintf('%02d%02d%02d',
                        $value['hour'], $value['minute'], $value['second']);
        if ($value['zone'] == 'UTC') {
            $time .= 'Z';
        }
        return $time;
    }

    /**
     * Parse a Date field.
     */
    function _parseDate($text)
    {
        if (strlen($text) != 8) {
            return false;
        }

        $date['year']  = intval(substr($text, 0, 4));
        $date['month'] = intval(substr($text, 4, 2));
        $date['mday']  = intval(substr($text, 6, 2));

        return $date;
    }

    /**
     * Export a Date field.
     */
    function _exportDate($value)
    {
        return sprintf('%04d%02d%02d',
                       $value['year'], $value['month'], $value['mday']);
    }

    /**
     * Parse a Duration Value field.
     */
    function _parseDuration($text)
    {
        if (preg_match('/([+]?|[-])P(([0-9]+W)|([0-9]+D)|)(T(([0-9]+H)|([0-9]+M)|([0-9]+S))+)?/', trim($text), $durvalue)) {
            // Weeks.
            $duration = 7 * 86400 * intval($durvalue[3]);

            if (count($durvalue) > 4) {
                // Days.
                $duration += 86400 * intval($durvalue[4]);
            }
            if (count($durvalue) > 5) {
                // Hours.
                $duration += 3600 * intval($durvalue[7]);

                // Mins.
                if (isset($durvalue[8])) {
                    $duration += 60 * intval($durvalue[8]);
                }

                // Secs.
                if (isset($durvalue[9])) {
                    $duration += intval($durvalue[9]);
                }
            }

            // Sign.
            if ($durvalue[1] == "-") {
                $duration *= -1;
            }

            return $duration;
        } else {
            return false;
        }
    }

    /**
     * Export a duration value.
     */
    function _exportDuration($value)
    {
        $duration = '';
        if ($value < 0) {
            $value *= -1;
            $duration .= '-';
        }
        $duration .= 'P';

        $weeks = floor($value / (7 * 86400));
        $value = $value % (7 * 86400);
        if ($weeks) {
            $duration .= $weeks . 'W';
        }

        $days = floor($value / (86400));
        $value = $value % (86400);
        if ($days) {
            $duration .= $days . 'D';
        }

        if ($value) {
            $duration .= 'T';

            $hours = floor($value / 3600);
            $value = $value % 3600;
            if ($hours) {
                $duration .= $hours . 'H';
            }

            $mins = floor($value / 60);
            $value = $value % 60;
            if ($mins) {
                $duration .= $mins . 'M';
            }

            if ($value) {
                $duration .= $value . 'S';
            }
        }

        return $duration;
    }

    /**
     * Return the folded version of a line.
     */
    function _foldLine($line)
    {
        $line = preg_replace("/\r\n|\n|\r/", '\n', $line);
        if (strlen($line) > 75) {
            $foldedline = '';
            while (!empty($line)) {
                $maxLine = substr($line, 0, 75);
                $cutPoint = max(60, max(strrpos($maxLine, ';'), strrpos($maxLine, ':')) + 1);

                $foldedline .= (empty($foldedline)) ?
                    substr($line, 0, $cutPoint) :
                    $this->_newline . ' ' . substr($line, 0, $cutPoint);

                $line = (strlen($line) <= $cutPoint) ? '' : substr($line, $cutPoint);
            }
            return $foldedline;
        }
        return $line;
    }

}
