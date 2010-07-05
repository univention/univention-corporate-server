<?php
/**
 * $Horde: kronolith/data.php,v 1.72.2.17 2009-01-06 15:24:43 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Jan Schneider <jan@horde.org>
 */

function _cleanup()
{
    global $import_step;
    $import_step = 1;
    return IMPORT_FILE;
}

@define('KRONOLITH_BASE', dirname(__FILE__));
require_once KRONOLITH_BASE . '/lib/base.php';
require_once 'Horde/Data.php';

if (!$conf['menu']['import_export']) {
    require KRONOLITH_BASE . '/index.php';
    exit;
}

/* Importable file types. */
$file_types = array('csv'       => _("Comma separated values"),
                    'icalendar' => _("vCalendar/iCalendar"));

/* Templates for the different import steps. */
$templates = array(
    IMPORT_CSV => array($registry->get('templates', 'horde') . '/data/csvinfo.inc'),
    IMPORT_MAPPED => array($registry->get('templates', 'horde') . '/data/csvmap.inc'),
    IMPORT_DATETIME => array($registry->get('templates', 'horde') . '/data/datemap.inc')
);
if (Kronolith::hasPermission('max_events') !== true &&
    Kronolith::hasPermission('max_events') <= Kronolith::countEvents()) {
    $message = @htmlspecialchars(sprintf(_("You are not allowed to create more than %d events."), Kronolith::hasPermission('max_events')), ENT_COMPAT, NLS::getCharset());
    if (!empty($conf['hooks']['permsdenied'])) {
        $message = Horde::callHook('_perms_hook_denied', array('kronolith:max_events'), 'horde', $message);
    }
    $notification->push($message, 'horde.warning', array('content.raw'));
    $templates[IMPORT_FILE] = array(KRONOLITH_TEMPLATES . '/data/export.inc');
} else {
    $templates[IMPORT_FILE] = array(KRONOLITH_TEMPLATES . '/data/import.inc', KRONOLITH_TEMPLATES . '/data/export.inc');
}

/* Initial values. */
$import_step   = Util::getFormData('import_step', 0) + 1;
$actionID      = Util::getFormData('actionID');
$next_step     = IMPORT_FILE;
$app_fields    = array('title' => _("Title"),
                       'start_date' => _("Start Date"),
                       'start_time' => _("Start Time"),
                       'end_date' => _("End Date"),
                       'end_time' => _("End Time"),
                       'alarm' => _("Alarm Span (minutes)"),
                       'alarm_date' => _("Alarm Date"),
                       'alarm_time' => _("Alarm Time"),
                       'description' => _("Description"),
                       'category' => _("Category"),
                       'location' => _("Location"),
                       'keywords' => _("Keywords"),
                       'recur_type' => _("Recurrence Type"),
                       'recur_end_date' => _("Recurrence End Date"),
                       'recur_interval' => _("Recurrence Interval"),
                       'recur_data' => _("Recurrence Data"));
$time_fields   = array('start_date'     => 'date',
                       'start_time'     => 'time',
                       'end_date'       => 'date',
                       'end_time'       => 'time',
                       'recur_end_date' => 'date');
$param         = array('time_fields' => $time_fields,
                       'file_types'  => $file_types);
$import_format = Util::getFormData('import_format', '');
$error         = false;

/* Loop through the action handlers. */
switch ($actionID) {
case 'export':
    if (Util::getFormData('all_events')) {
        $start = null;
        $end = null;
    } else {
        $start->mday = Util::getFormData('start_day');
        $start->month = Util::getFormData('start_month');
        $start->year = Util::getFormData('start_year');
        $end->mday = Util::getFormData('end_day');
        $end->month = Util::getFormData('end_month');
        $end->year = Util::getFormData('end_year');
    }

    $events = array();
    $calendars = Util::getFormData('exportCal', $display_calendars);
    if (!is_array($calendars)) {
        $calendars = array($calendars);
    }
    foreach ($calendars as $cal) {
        if ($kronolith_driver->getCalendar() != $cal) {
            $kronolith_driver->open($cal);
        }
        $events[$cal] = $kronolith_driver->listEvents($start, $end);
    }

    if (!$events) {
        $notification->push(_("There were no events to export."), 'horde.message');
        $error = true;
        break;
    }

    $exportID = Util::getFormData('exportID');
    switch ($exportID) {
    case EXPORT_CSV:
        $data = array();
        foreach ($events as $cal => $calevents) {
            if ($kronolith_driver->getCalendar() != $cal) {
                $kronolith_driver->open($cal);
            }
            foreach ($calevents as $eventId) {
                $event = &$kronolith_driver->getEvent($eventId);
                if (is_a($event, 'PEAR_Error')) {
                    continue;
                }

                $row = array();
                $row['title'] = $event->getTitle();
                $row['category'] = $event->category;
                $row['location'] = $event->location;
                $row['description'] = $event->description;
                $row['keywords'] = implode(',', $event->keywords);
                $row['start_date'] = sprintf('%d-%02d-%02d', $event->start->year, $event->start->month, $event->start->mday);
                $row['start_time'] = sprintf('%02d:%02d:%02d', $event->start->hour, $event->start->min, $event->start->sec);
                $row['end_date'] = sprintf('%d-%02d-%02d', $event->end->year, $event->end->month, $event->end->mday);
                $row['end_time'] = sprintf('%02d:%02d:%02d', $event->end->hour, $event->end->min, $event->end->sec);
                $row['alarm'] = $event->alarm;
                if ($event->recurs()) {
                    $row['recur_type'] = $event->recurrence->getRecurType();
                    $row['recur_end_date'] = sprintf('%d-%02d-%02d',
                                                     $event->recurrence->recurEnd->year,
                                                     $event->recurrence->recurEnd->month,
                                                     $event->recurrence->recurEnd->mday);
                    $row['recur_interval'] = $event->recurrence->getRecurInterval();
                    $row['recur_data'] = $event->recurrence->recurData;
                } else {
                    $row['recur_type'] = null;
                    $row['recur_end_date'] = null;
                    $row['recur_interval'] = null;
                    $row['recur_data'] = null;
                }
                $data[] = $row;
            }
        }

        $csv = &Horde_Data::singleton('csv');
        $csv->exportFile(_("events.csv"), $data, true);
        exit;

    case EXPORT_ICALENDAR:
        require_once 'Horde/Identity.php';
        require_once 'Horde/iCalendar.php';
        $iCal = new Horde_iCalendar();

        $calNames = array();
        foreach ($events as $cal => $calevents) {
            if ($kronolith_driver->getCalendar() != $cal) {
                $kronolith_driver->open($cal);
            }

            $share = &$kronolith_shares->getShare($cal);
            $calNames[] = $share->get('name');
            foreach ($calevents as $id) {
                $event = &$kronolith_driver->getEvent($id);
                if (is_a($event, 'PEAR_Error')) {
                    continue;
                }
                $iCal->addComponent($event->toiCalendar($iCal));
            }
        }

        $iCal->setAttribute('X-WR-CALNAME', String::convertCharset(implode(', ', $calNames), NLS::getCharset(), 'utf-8'));
        $data = $iCal->exportvCalendar();
        $browser->downloadHeaders(_("events.ics"), 'text/calendar', false, strlen($data));
        echo $data;
        exit;
    }
    break;

case IMPORT_FILE:
    $_SESSION['import_data']['import_cal'] = Util::getFormData('importCal');
    $_SESSION['import_data']['purge'] = Util::getFormData('purge');
    break;
}

if (!$error) {
    $data = &Horde_Data::singleton($import_format);
    if (is_a($data, 'PEAR_Error')) {
        $notification->push(_("This file format is not supported."), 'horde.error');
        $next_step = IMPORT_FILE;
    } else {
        if ($actionID == IMPORT_FILE) {
            $share = &$kronolith_shares->getShare($_SESSION['import_data']['import_cal']);
            if (is_a($share, 'PEAR_Error')) {
                $notification->push(_("You have specified an invalid calendar."), 'horde.error');
                $next_step = $data->cleanup();
            } elseif (!$share->hasPermission(Auth::getAuth(), PERMS_EDIT)) {
                $notification->push(_("You do not have permission to add events to the selected calendar."), 'horde.error');
                $next_step = $data->cleanup();
            } else {
                $next_step = $data->nextStep($actionID, $param);
                if (is_a($next_step, 'PEAR_Error')) {
                    $notification->push($next_step->getMessage(), 'horde.error');
                    $next_step = $data->cleanup();
                }
            }
        } else {
            $next_step = $data->nextStep($actionID, $param);
            if (is_a($next_step, 'PEAR_Error')) {
                $notification->push($next_step->getMessage(), 'horde.error');
                $next_step = $data->cleanup();
            }
        }
    }
}

/* We have a final result set. */
if (is_array($next_step)) {
    /* Create a category manager. */
    require_once 'Horde/Prefs/CategoryManager.php';
    $cManager = new Prefs_CategoryManager();
    $categories = $cManager->get();

    $events = array();
    $error = false;
    $max_events = Kronolith::hasPermission('max_events');
    if ($max_events !== true) {
        $num_events = Kronolith::countEvents();
    }
    $kronolith_driver->open($_SESSION['import_data']['import_cal']);

    if (!count($next_step)) {
        $notification->push(sprintf(_("The %s file didn't contain any events."),
                                    $file_types[$_SESSION['import_data']['format']]), 'horde.error');
        $error = true;
    } else {
        /* Purge old calendar if requested. */
        if ($_SESSION['import_data']['purge']) {
            $result = $kronolith_driver->delete($_SESSION['import_data']['import_cal']);
            if (is_a($result, 'PEAR_Error')) {
                $notification->push(sprintf(_("The calendar could not be purged: %s"), $result->getMessage()), 'horde.error');
            } else {
                $notification->push(_("Calendar successfully purged."), 'horde.success');
            }
        }
    }

    foreach ($next_step as $row) {
        if ($max_events !== true && $num_events >= $max_events) {
            $message = @htmlspecialchars(sprintf(_("You are not allowed to create more than %d events."), Kronolith::hasPermission('max_events')), ENT_COMPAT, NLS::getCharset());
            if (!empty($conf['hooks']['permsdenied'])) {
                $message = Horde::callHook('_perms_hook_denied', array('kronolith:max_events'), 'horde', $message);
            }
            $notification->push($message, 'horde.error', array('content.raw'));
            break;
        }
        $event = &$kronolith_driver->getEvent();
        if (!$event || is_a($event, 'PEAR_Error')) {
            $msg = _("Can't create a new event.");
            if (is_a($event, 'PEAR_Error')) {
                $msg .= ' ' . sprintf(_("This is what the server said: %s"), $event->getMessage());
            }
            $notification->push($msg, 'horde.error');
            $error = true;
            break;
        }
        if (is_a($row, 'Horde_iCalendar_vevent')) {
            $event->fromiCalendar($row);
        } elseif (is_a($row, 'Horde_iCalendar')) {
            // Skip other iCalendar components for now.
            continue;
        } else {
            $valid = $event->fromHash($row);
            if (is_a($valid, 'PEAR_Error')) {
                $notification->push($valid, 'horde.error');
                $error = true;
                break;
            }
        }

        $success = $event->save();
        if (is_a($success, 'PEAR_Error')) {
            $notification->push($success, 'horde.error');
            $error = true;
            break;
        }

        $category = $event->getCategory();
        if (!empty($category) && !in_array($category, $categories)) {
            $cManager->add($category);
            $categories[] = $category;
        }

        if ($max_events !== true) {
            $num_events++;
        }
    }
    if (!$error) {
        $notification->push(sprintf(_("%s file successfully imported"),
                                    $file_types[$_SESSION['import_data']['format']]), 'horde.success');
    }
    $next_step = $data->cleanup();
}

$title = _("Import/Export Calendar");
require KRONOLITH_TEMPLATES . '/common-header.inc';
require KRONOLITH_TEMPLATES . '/menu.inc';

echo '<div id="page">';
foreach ($templates[$next_step] as $template) {
    require $template;
}
echo '</div>';

require $registry->get('templates', 'horde') . '/common-footer.inc';
