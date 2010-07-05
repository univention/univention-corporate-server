<?php
/**
 * Class representing vEvents.
 *
 * $Horde: framework/iCalendar/iCalendar/vevent.php,v 1.31.10.16 2009-01-06 15:23:53 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @since   Horde 3.0
 * @package Horde_iCalendar
 */
class Horde_iCalendar_vevent extends Horde_iCalendar {

    function getType()
    {
        return 'vEvent';
    }

    function exportvCalendar()
    {
        // Default values.
        $requiredAttributes = array();
        $requiredAttributes['DTSTAMP'] = time();
        $requiredAttributes['UID'] = $this->_exportDateTime(time())
            . substr(str_pad(base_convert(microtime(), 10, 36), 16, uniqid(mt_rand()), STR_PAD_LEFT), -16)
            . '@' . (isset($_SERVER['SERVER_NAME']) ? $_SERVER['SERVER_NAME'] : 'localhost');

        $method = !empty($this->_container) ?
            $this->_container->getAttribute('METHOD') : 'PUBLISH';

        switch ($method) {
        case 'PUBLISH':
            $requiredAttributes['DTSTART'] = time();
            $requiredAttributes['SUMMARY'] = '';
            break;

        case 'REQUEST':
            $requiredAttributes['ATTENDEE'] = '';
            $requiredAttributes['DTSTART'] = time();
            $requiredAttributes['SUMMARY'] = '';
            break;

        case 'REPLY':
            $requiredAttributes['ATTENDEE'] = '';
            break;

        case 'ADD':
            $requiredAttributes['DTSTART'] = time();
            $requiredAttributes['SEQUENCE'] = 1;
            $requiredAttributes['SUMMARY'] = '';
            break;

        case 'CANCEL':
            $requiredAttributes['ATTENDEE'] = '';
            $requiredAttributes['SEQUENCE'] = 1;
            break;

        case 'REFRESH':
            $requiredAttributes['ATTENDEE'] = '';
            break;
        }

        foreach ($requiredAttributes as $name => $default_value) {
            if (is_a($this->getAttribute($name), 'PEAR_Error')) {
                $this->setAttribute($name, $default_value);
            }
        }

        return parent::_exportvData('VEVENT');
    }

    /**
     * Update the status of an attendee of an event.
     *
     * @param $email    The email address of the attendee.
     * @param $status   The participant status to set.
     * @param $fullname The full name of the participant to set.
     */
    function updateAttendee($email, $status, $fullname = '')
    {
        foreach ($this->_attributes as $key => $attribute) {
            if ($attribute['name'] == 'ATTENDEE' &&
                $attribute['value'] == 'mailto:' . $email) {
                $this->_attributes[$key]['params']['PARTSTAT'] = $status;
                if (!empty($fullname)) {
                    $this->_attributes[$key]['params']['CN'] = $fullname;
                }
                unset($this->_attributes[$key]['params']['RSVP']);
                return;
            }
        }
        $params = array('PARTSTAT' => $status);
        if (!empty($fullname)) {
            $params['CN'] = $fullname;
        }
        $this->setAttribute('ATTENDEE', 'mailto:' . $email, $params);
    }

    /**
     * Return the organizer display name or email.
     *
     * @return string  The organizer name to display for this event.
     */
    function organizerName()
    {
        $organizer = $this->getAttribute('ORGANIZER', true);
        if (is_a($organizer, 'PEAR_Error')) {
            return _("An unknown person");
        }

        if (isset($organizer[0]['CN'])) {
            return $organizer[0]['CN'];
        }

        $organizer = parse_url($this->getAttribute('ORGANIZER'));

        return $organizer['path'];
    }

    /**
     * Update this event with details from another event.
     *
     * @param Horde_iCalendar_vEvent $vevent  The vEvent with latest details.
     */
    function updateFromvEvent($vevent)
    {
        $newAttributes = $vevent->getAllAttributes();
        foreach ($newAttributes as $newAttribute) {
            $currentValue = $this->getAttribute($newAttribute['name']);
            if (is_a($currentValue, 'PEAR_error')) {
                // Already exists so just add it.
                $this->setAttribute($newAttribute['name'],
                                    $newAttribute['value'],
                                    $newAttribute['params']);
            } else {
                // Already exists so locate and modify.
                $found = false;

                // Try matching the attribte name and value incase
                // only the params changed (eg attendee updating
                // status).
                foreach ($this->_attributes as $id => $attr) {
                    if ($attr['name'] == $newAttribute['name'] &&
                        $attr['value'] == $newAttribute['value']) {
                        // merge the params
                        foreach ($newAttribute['params'] as $param_id => $param_name) {
                            $this->_attributes[$id]['params'][$param_id] = $param_name;
                        }
                        $found = true;
                        break;
                    }
                }
                if (!$found) {
                    // Else match the first attribute with the same
                    // name (eg changing start time).
                    foreach ($this->_attributes as $id => $attr) {
                        if ($attr['name'] == $newAttribute['name']) {
                            $this->_attributes[$id]['value'] = $newAttribute['value'];
                            // Merge the params.
                            foreach ($newAttribute['params'] as $param_id => $param_name) {
                                $this->_attributes[$id]['params'][$param_id] = $param_name;
                            }
                            break;
                        }
                    }
                }
            }
        }
    }

    /**
     * Update just the attendess of event with details from another
     * event.
     *
     * @param Horde_iCalendar_vEvent $vevent  The vEvent with latest details
     */
    function updateAttendeesFromvEvent($vevent)
    {
        $newAttributes = $vevent->getAllAttributes();
        foreach ($newAttributes as $newAttribute) {
            if ($newAttribute['name'] != 'ATTENDEE') {
                continue;
            }
            $currentValue = $this->getAttribute($newAttribute['name']);
            if (is_a($currentValue, 'PEAR_error')) {
                // Already exists so just add it.
                $this->setAttribute($newAttribute['name'],
                                    $newAttribute['value'],
                                    $newAttribute['params']);
            } else {
                // Already exists so locate and modify.
                $found = false;
                // Try matching the attribte name and value incase
                // only the params changed (eg attendee updating
                // status).
                foreach ($this->_attributes as $id => $attr) {
                    if ($attr['name'] == $newAttribute['name'] &&
                        $attr['value'] == $newAttribute['value']) {
                        // Merge the params.
                        foreach ($newAttribute['params'] as $param_id => $param_name) {
                            $this->_attributes[$id]['params'][$param_id] = $param_name;
                        }
                        $found = true;
                        break;
                    }
                }

                if (!$found) {
                    // Else match the first attribute with the same
                    // name (eg changing start time).
                    foreach ($this->_attributes as $id => $attr) {
                        if ($attr['name'] == $newAttribute['name']) {
                            $this->_attributes[$id]['value'] = $newAttribute['value'];
                            // Merge the params.
                            foreach ($newAttribute['params'] as $param_id => $param_name) {
                                $this->_attributes[$id]['params'][$param_id] = $param_name;
                            }
                            break;
                        }
                    }
                }
            }
        }
    }

}
