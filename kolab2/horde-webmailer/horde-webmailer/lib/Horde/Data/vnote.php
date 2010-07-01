<?php

require_once dirname(__FILE__) . '/imc.php';

/**
 * Implement the Horde_Data:: API for vNote data.
 *
 * $Horde: framework/Data/Data/vnote.php,v 1.8.10.9 2009-01-06 15:23:01 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @package Horde_Data
 * @since   Horde 3.0
 */
class Horde_Data_vnote extends Horde_Data_imc {

    /**
     * Exports vcalendar data as a string. Unlike vEvent, vNote data
     * is not enclosed in BEGIN|END:vCalendar.
     *
     * @param array $data     An array containing Horde_iCalendar_vnote
     *                        objects.
     * @param string $method  The iTip method to use.
     *
     * @return string  The iCalendar data.
     */
    function exportData($data, $method = 'REQUEST')
    {
        global $prefs;

        $this->_iCal = &new Horde_iCalendar();

        $this->_iCal->setAttribute('METHOD', $method);
        $s = '';
        foreach ($data as $event) {
            $s.= $event->exportvCalendar();
        }
        return $s;
    }

}
