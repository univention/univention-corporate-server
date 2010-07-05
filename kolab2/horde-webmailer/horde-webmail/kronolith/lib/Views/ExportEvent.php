<?php
/**
 * The Kronolith_View_ExportEvent:: class provides an API for exporting
 * events.
 *
 * $Horde: kronolith/lib/Views/ExportEvent.php,v 1.1.2.2 2008-03-14 14:18:57 jan Exp $
 *
 * @author  Jan Schneider <chuck@horde.org>
 * @since   Kronolith 2.2
 * @package Kronolith
 */
class Kronolith_View_ExportEvent {

    /**
     * @param Kronolith_Event &$event
     */
    function Kronolith_View_ExportEvent(&$event)
    {
        require_once 'Horde/iCalendar.php';
        $iCal = new Horde_iCalendar('2.0');

        if (!$event->isRemote()) {
            $share = &$GLOBALS['kronolith_shares']->getShare($event->getCalendar());
            if (!is_a($share, 'PEAR_Error')) {
                $iCal->setAttribute('X-WR-CALNAME',
                                    String::convertCharset($share->get('name'),
                                                           NLS::getCharset(),
                                                           'utf-8'));
            }
        }

        $vEvent = &$event->toiCalendar($iCal);
        $iCal->addComponent($vEvent);
        $content = $iCal->exportvCalendar();

        $GLOBALS['browser']->downloadHeaders(
            $event->getTitle() . '.ics',
            'text/calendar; charset=' . NLS::getCharset(),
            true, strlen($content));
        echo $content;
        exit;
    }

}
