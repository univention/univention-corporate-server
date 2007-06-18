<?php
/**
 * Class representing vTimezones.
 *
 * $Horde: framework/iCalendar/iCalendar/vtimezone.php,v 1.6 2004/01/01 15:14:48 jan Exp $
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
 class Horde_iCalendar_vtimezone extends Horde_iCalendar {

    function getType()
    {
        return 'vTimeZone';
    }

    function parsevCalendar($data)
    {
        parent::parsevCalendar($data, 'VTIMEZONE');
    }

    function exportvCalendar(&$container)
    {
        return parent::_exportvData('VTIMEZONE');
    }

}

class Horde_iCalendar_standard extends Horde_iCalendar {

    function getType()
    {
        return 'standard';
    }

    function parsevCalendar($data)
    {
        parent::parsevCalendar($data, 'STANDARD');
    }

    function exportvCalendar(&$container)
    {
        return parent::_exportvData('STANDARD');
    }

}

class Horde_iCalendar_daylight extends Horde_iCalendar {

    function getType()
    {
        return 'daylight';
    }

    function parsevCalendar($data)
    {
        parent::parsevCalendar($data, 'DAYLIGHT');
    }

    function exportvCalendar(&$container)
    {
        return parent::_exportvData('DAYLIGHT');
    }

}
