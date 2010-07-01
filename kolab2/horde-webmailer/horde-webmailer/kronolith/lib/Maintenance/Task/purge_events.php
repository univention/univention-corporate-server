<?php
/**
 * $Horde: kronolith/lib/Maintenance/Task/purge_events.php,v 1.1.2.4 2009-01-06 15:24:46 jan Exp $
 *
 * Maintenance module that purges old events.
 *
 * Copyright 2008-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael J. Rubinsky <mrubinsk@horde.org>
 * @package Horde_Maintenance
 */
class Maintenance_Task_purge_events extends Maintenance_Task {

    /**
     * Purge old messages in the Trash folder.
     *
     * @return boolean  Whether any messages were purged from the Trash folder.
     */
    function doMaintenance()
    {
        global $prefs, $kronolith_driver, $notification;

        /* Get the current UNIX timestamp minus the number of days
           specified in 'purge_events_keep'.  An event will be deleted if it has
           an end time prior to this time. */
        $del_time = time() - ($prefs->getValue('purge_events_keep') * 86400);

        /* Need to have PERMS_DELETE on a calendar to delete events from it */
        $calendars = Kronolith::listCalendars(false, PERMS_DELETE);

        /* Start building an event object to use for the search */
        $query = &$kronolith_driver->getEvent();
        $query->start = null;
        $query->end = &new Horde_Date($del_time);
        $query->category = null;
        $query->status = null;
        $query->calendars = array_keys($calendars);
        $query->creatorID = Auth::getAuth();

        /* Perform the search */
        $events = Kronolith::search($query);
        $count = 0;
        foreach ($events as $event) {
            if (!$event->recurs()) {
                if ($event->getCalendar() != $kronolith_driver->getCalendar()) {
                    $kronolith_driver->open($event->getCalendar());
                }
                $results = $kronolith_driver->deleteEvent($event->getId(), true);
                ++$count;
                if (is_a($results, 'PEAR_Error')) {
                    Horde::logMessage($results, __FILE__, __LINE__, PEAR_LOG_ERR);
                    return $results;
                }
            }
        }
        $notification->push(sprintf(ngettext("Deleted %d event older than %d days.", "Deleted %d events older than %d days.", $count), $count, $prefs->getValue('purge_events_keep')));

        return true;
    }

    /**
     * Return information for the maintenance function.
     *
     * @return string  Description of what the operation is going to do during
     *                 this login.
     */
    function describeMaintenance()
    {
        return sprintf(_("All of your events older than %d days will be permanently deleted."),
                       $GLOBALS['prefs']->getValue('purge_events_keep'));
    }

}
