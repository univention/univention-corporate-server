<?php

require_once dirname(__FILE__) . '/imc.php';
require_once 'Horde/iCalendar.php';

/**
 * Implement the Horde_Data:: API for vCard data.
 *
 * $Horde: framework/Data/Data/vcard.php,v 1.33.10.11 2009-01-06 15:23:01 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.0
 * @package Horde_Data
 */
class Horde_Data_vcard extends Horde_Data_imc {

    /**
     * Exports vcalendar data as a string. Unlike vEvent, vCard data
     * is not enclosed in BEGIN|END:vCalendar.
     *
     * @param array $data     An array containing Horde_iCalendar_vcard
     *                        objects.
     * @param string $method  The iTip method to use.
     *
     * @return string  The iCalendar data.
     */
    function exportData($data, $method = 'REQUEST')
    {
        $s = '';
        foreach ($data as $vcard) {
            $s.= $vcard->exportvCalendar();
        }
        return $s;
    }

}
