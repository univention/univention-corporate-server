<?php
/**
 * Class representing vJournals.
 *
 * $Horde: framework/iCalendar/iCalendar/vjournal.php,v 1.6 2004/01/01 15:14:48 jan Exp $
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
class Horde_iCalendar_vjournal extends Horde_iCalendar {

    function getType()
    {
        return 'vJournal';
    }

    function parsevCalendar($data)
    {
        parent::parsevCalendar($data, 'VJOURNAL');
    }

    function exportvCalendar(&$container)
    {
        return parent::_exportvData('VJOURNAL');
    }

}
