<?php
/**
 * $Horde: kronolith/edit.php,v 1.10.2.4 2009-01-06 15:24:43 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

function _save(&$event)
{
    $res = $event->save();
    if (is_a($res, 'PEAR_Error')) {
        $GLOBALS['notification']->push(sprintf(_("There was an error editing the event: %s"), $res->getMessage()), 'horde.error');
    } elseif (Util::getFormData('sendupdates', false)) {
        Kronolith::sendITipNotifications($event, $GLOBALS['notification'], KRONOLITH_ITIP_REQUEST);
    }
}

function _check_max()
{
    if (Kronolith::hasPermission('max_events') !== true &&
        Kronolith::hasPermission('max_events') <= Kronolith::countEvents()) {
        $message = @htmlspecialchars(sprintf(_("You are not allowed to create more than %d events."), Kronolith::hasPermission('max_events')), ENT_COMPAT, NLS::getCharset());
        if (!empty($GLOBALS['conf']['hooks']['permsdenied'])) {
            $message = Horde::callHook('_perms_hook_denied', array('kronolith:max_events'), 'horde', $message);
        }
        $GLOBALS['notification']->push($message, 'horde.error', array('content.raw'));
        return false;
    }
    return true;
}

@define('KRONOLITH_BASE', dirname(__FILE__));
require_once KRONOLITH_BASE . '/lib/base.php';

$url = Util::getFormData('url');

if ($exception = Util::getFormData('del_exception')) {
    $calendar = Util::getFormData('calendar');
    $share = &$kronolith_shares->getShare($calendar);
    if (is_a($share, 'PEAR_Error')) {
        $notification->push(sprintf(_("There was an error accessing the calendar: %s"), $share->getMessage()), 'horde.error');
    } else {
        $kronolith_driver->open($calendar);
        $event = &$kronolith_driver->getEvent(Util::getFormData('eventID'));
        $result = sscanf($exception, '%04d%02d%02d', $year, $month, $day);
        if ($result == 3 && !is_a($event, 'PEAR_Error') && $event->recurs()) {
            $event->recurrence->deleteException($year, $month, $day);
            _save($event);
        }
    }
} elseif (!Util::getFormData('cancel')) {
    $source = Util::getFormData('existingcalendar');
    $targetcalendar = Util::getFormData('targetcalendar');
    if (strpos($targetcalendar, ':')) {
        list($target, $user) = explode(':', $targetcalendar, 2);
    } else {
        $target = $targetcalendar;
        $user = Auth::getAuth();
    }
    $share = &$kronolith_shares->getShare($target);

    if (is_a($share, 'PEAR_Error')) {
        $notification->push(sprintf(_("There was an error accessing the calendar: %s"), $share->getMessage()), 'horde.error');
    } else {
        $event = false;

        if (($edit_recur = Util::getFormData('edit_recur')) &&
            $edit_recur != 'all' && $edit_recur != 'copy' &&
            _check_max()) {
            /* Get event details. */
            $kronolith_driver->open($source);
            $event = &$kronolith_driver->getEvent(Util::getFormData('eventID'));
            $recur_ex = Util::getFormData('recur_ex');
            $exception = new Horde_Date($recur_ex);

            switch ($edit_recur) {
            case 'current':
                /* Add exception. */
                $event->recurrence->addException($exception->year,
                                                 $exception->month,
                                                 $exception->mday);
                $event->save();

                /* Create one-time event. */
                $kronolith_driver->open($target);
                $event = &$kronolith_driver->getEvent();
                $event->readForm();
                $event->recurrence->setRecurType(HORDE_DATE_RECUR_NONE);

                break;

            case 'future':
                /* Set recurrence end. */
                $exception->mday--;
                $exception->correct();
                if ($event->end->compareDate($exception) > 0) {
                    $result = $kronolith_driver->deleteEvent($event->getId());
                    if (is_a($result, 'PEAR_Error')) {
                        $notification->push($result, 'horde.error');
                    }
                } else {
                    $event->recurrence->setRecurEnd($exception);
                    $event->save();
                }

                /* Create new event. */
                $kronolith_driver->open($target);
                $event = &$kronolith_driver->getEvent();
                $event->readForm();

                break;
            }

            $event->setUID(null);
            _save($event);
            $event = null;
        } elseif (Util::getFormData('saveAsNew') ||
                  $edit_recur == 'copy') {
            if (_check_max()) {
                $kronolith_driver->open($target);
                $event = &$kronolith_driver->getEvent();
            }
        } else {
            $event_load_from = $source;

            if ($target != $source) {
                // Only delete the event from the source calendar if this user
                // has permissions to do so.
                $sourceShare = &$kronolith_shares->getShare($source);
                if (!is_a($share, 'PEAR_Error') &&
                    !is_a($sourceShare, 'PEAR_Error') &&
                    $sourceShare->hasPermission(Auth::getAuth(), PERMS_DELETE) &&
                    (($user == Auth::getAuth() &&
                      $share->hasPermission(Auth::getAuth(), PERMS_EDIT)) ||
                     ($user != Auth::getAuth() &&
                      $share->hasPermission(Auth::getAuth(), PERMS_DELEGATE)))) {
                    $kronolith_driver->open($source);
                    $res = $kronolith_driver->move(Util::getFormData('eventID'), $target);
                    if (is_a($res, 'PEAR_Error')) {
                        $notification->push(sprintf(_("There was an error moving the event: %s"), $res->getMessage()), 'horde.error');
                    } else {
                        $event_load_from = $target;
                    }
                }
            }

            $kronolith_driver->open($event_load_from);
            $event = &$kronolith_driver->getEvent(Util::getFormData('eventID'));
        }

        if ($event && !is_a($event, 'PEAR_Error')) {
            if (isset($sourceShare) && !is_a($sourceShare, 'PEAR_Error')
                && !$sourceShare->hasPermission(Auth::getAuth(), PERMS_DELETE)) {
                $notification->push(_("You do not have permission to move this event."), 'horde.warning');
            } elseif ($user != Auth::getAuth() &&
                      !$share->hasPermission(Auth::getAuth(), PERMS_DELEGATE, $event->getCreatorID())) {
                $notification->push(sprintf(_("You do not have permission to delegate events to %s."), Kronolith::getUserName($user)), 'horde.warning');
            } elseif ($user == Auth::getAuth() &&
                      !$share->hasPermission(Auth::getAuth(), PERMS_EDIT, $event->getCreatorID())) {
                $notification->push(_("You do not have permission to edit this event."), 'horde.warning');
            } else {
                $event->readForm();
                _save($event);
            }
        }
    }
}

if (!empty($url)) {
    $location = $url;
} else {
    $url = Util::addParameter($prefs->getValue('defaultview') . '.php',
                              array('month' => Util::getFormData('month'),
                                    'year' => Util::getFormData('year')));
    $location = Horde::applicationUrl($url, true);
}

// Make sure URL is unique.
$location = Util::addParameter($location, 'unique', md5(microtime()), false);
header('Location: ' . $location);
