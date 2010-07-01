<?php
/**
 * $Horde: kronolith/delete.php,v 1.9.2.6 2009-01-06 15:24:43 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

@define('KRONOLITH_BASE', dirname(__FILE__));
require_once KRONOLITH_BASE . '/lib/base.php';

$kronolith_driver->open(Util::getFormData('calendar'));
if ($eventID = Util::getFormData('eventID')) {
    $event = &$kronolith_driver->getEvent($eventID);
    if (is_a($event, 'PEAR_Error')) {
        if (($url = Util::getFormData('url')) === null) {
            $url = Horde::applicationUrl($prefs->getValue('defaultview') . '.php', true);
        }
        header('Location: ' . $url);
        exit;
    }
    $share = &$kronolith_shares->getShare($event->getCalendar());
    if (!$share->hasPermission(Auth::getAuth(), PERMS_DELETE, $event->getCreatorID())) {
        $notification->push(_("You do not have permission to delete this event."), 'horde.warning');
    } else {
        $notification_type = KRONOLITH_ITIP_CANCEL;
        $instance = null;
        if (Util::getFormData('future')) {
            $recurEnd = new Horde_Date(array('hour' => 0, 'min' => 0, 'sec' => 0,
                                             'month' => Util::getFormData('month', date('n')),
                                             'mday' => Util::getFormData('mday', date('j')) - 1,
                                             'year' => Util::getFormData('year', date('Y'))));
            $recurEnd->correct();
            if ($event->end->compareDate($recurEnd) > 0) {
                $result = $kronolith_driver->deleteEvent($event->getId());
                if (is_a($result, 'PEAR_Error')) {
                    $notification->push($result, 'horde.error');
                }
            } else {
                $event->recurrence->setRecurEnd($recurEnd);
                $event->save();
            }
            $notification_type = KRONOLITH_ITIP_REQUEST;
        } elseif (Util::getFormData('current')) {
            $event->recurrence->addException(Util::getFormData('year'),
                                             Util::getFormData('month'),
                                             Util::getFormData('mday'));
            $event->save();
            $instance = new Horde_Date(array('year' => Util::getFormData('year'),
                                             'month' => Util::getFormData('month'),
                                             'mday' => Util::getFormData('mday')));
        }

        if (!$event->recurs() ||
            Util::getFormData('all') ||
            !$event->recurrence->hasActiveRecurrence()) {
            $result = $kronolith_driver->deleteEvent($event->getId());
            if (is_a($result, 'PEAR_Error')) {
                $notification->push($result, 'horde.error');
            }
        }

        if (Util::getFormData('sendupdates', false)) {
            Kronolith::sendITipNotifications($event, $notification, $notification_type, $instance);
        }
    }
}

if ($url = Util::getFormData('url')) {
    $location = $url;
} else {
    if ($timestamp = Util::getFormData('timestamp')) {
        $month = date('n', $timestamp);
        $day = date('j', $timestamp);
        $year = date('Y', $timestamp);
    } else {
        $month = Util::getFormData('month', date('n'));
        $day = Util::getFormData('mday', date('j'));
        $year = Util::getFormData('year', date('Y'));
    }

    $url = Util::addParameter($prefs->getValue('defaultview') . '.php', array('month' => $month,
                                                                              'mday' => $day,
                                                                              'year' => $year));
    $location = Horde::applicationUrl($url, true);
}

header('Location: ' . $location);
