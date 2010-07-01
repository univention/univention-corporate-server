<?php
/**
 * $Horde: kronolith/lib/prefs.php,v 1.5.10.11 2009-01-06 15:24:45 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @package Kronolith
 */

function handle_remote_cal_management($updated)
{
    global $prefs;

    $calName = Util::getFormData('remote_name');
    $calUrl  = trim(Util::getFormData('remote_url'));
    $calUser = trim(Util::getFormData('remote_user'));
    $calPasswd = trim(Util::getFormData('remote_password'));

    $key = Auth::getCredential('password');
    if ($key) {
        require_once 'Horde/Secret.php';
        $calUser = base64_encode(Secret::write($key, $calUser));
        $calPasswd = base64_encode(Secret::write($key, $calPasswd));
    }

    $calActionID = Util::getFormData('remote_action', 'add');

    if ($calActionID == 'add') {
        if (!empty($calName) && !empty($calUrl)) {
            $cals = unserialize($prefs->getValue('remote_cals'));
            $cals[] = array('name' => $calName,
                            'url'  => $calUrl,
                            'user' => $calUser,
                            'password' => $calPasswd);
            $prefs->setValue('remote_cals', serialize($cals));
            return $updated;
        }
    } elseif ($calActionID == 'delete') {
        $cals = unserialize($prefs->getValue('remote_cals'));
        foreach ($cals as $key => $cal) {
            if ($cal['url'] == $calUrl) {
                unset($cals[$key]);
                break;
            }
        }
        $prefs->setValue('remote_cals', serialize($cals));
        return $updated;
    } elseif ($calActionID == 'edit') {
        $cals = unserialize($prefs->getValue('remote_cals'));
        foreach ($cals as $key => $cal) {
            if ($cal['url'] == $calUrl) {
                $cals[$key]['name'] = $calName;
                $cals[$key]['url'] = $calUrl;
                $cals[$key]['user'] = $calUser;
                $cals[$key]['password'] = $calPasswd;
                break;
            }
        }
        $prefs->setValue('remote_cals', serialize($cals));
        return $updated;
    }

    return false;
}

function handle_shareselect($updated)
{
    $default_share = Util::getFormData('default_share');
    if (!is_null($default_share)) {
        $sharelist = Kronolith::listCalendars();
        if ((is_array($sharelist)) > 0 && isset($sharelist[$default_share])) {
            $GLOBALS['prefs']->setValue('default_share', $default_share);
            return true;
        }
    }

    return $updated;
}

function handle_holiday_drivers($updated)
{
    $holiday_driversSelected = Util::getFormData('holiday_drivers');
    $holiday_driversFiltered = array();

    if (is_array($holiday_driversSelected)) {
        foreach($holiday_driversSelected as $holiday_driver) {
        $holiday_driversFiltered[] = $holiday_driver;
        }
    }

    $GLOBALS['prefs']->setValue('holiday_drivers', serialize($holiday_driversFiltered));
    return true;
}

function handle_sourceselect($updated)
{
    global $prefs;

    $search_sources = Util::getFormData('search_sources');
    if ($search_sources !== null) {
        $prefs->setValue('search_sources', $search_sources);
        $updated = true;
    }

    $search_fields_string = Util::getFormData('search_fields_string');
    if ($search_fields_string !== null) {
        $prefs->setValue('search_fields', $search_fields_string);
        $updated = true;
    }

    return $updated;
}

function handle_fb_cals_select($updated)
{
    $fb_calsSelected = Util::getFormData('fb_cals');
    $fb_cals = Kronolith::listCalendars();
    $fb_calsFiltered = array();

    if (isset($fb_calsSelected) && is_array($fb_calsSelected)) {
        foreach ($fb_calsSelected as $fb_cal) {
            $fb_calsFiltered[] = $fb_cal;
        }
    }

    $GLOBALS['prefs']->setValue('fb_cals', serialize($fb_calsFiltered));
    return true;
}

function handle_default_alarm_management($updated)
{
    $GLOBALS['prefs']->setValue('default_alarm',
                                (int)Util::getFormData('alarm_value') * (int)Util::getFormData('alarm_unit'));
    return true;
}

if (!$prefs->isLocked('day_hour_start') || !$prefs->isLocked('day_hour_end')) {
    $day_hour_start_options = array();
    for ($i = 0; $i <= 48; ++$i) {
        $day_hour_start_options[$i] = date(($prefs->getValue('twentyFour')) ? 'G:i' : 'g:ia', mktime(0, $i * 30, 0));
    }
    $day_hour_end_options = $day_hour_start_options;
}

/**
 * Do anything that we need to do as a result of certain preferences
 * changing.
 */
function prefs_callback()
{
    global $prefs;

    if ($GLOBALS['prefs']->isDirty('event_alarms')) {
        $alarms = $GLOBALS['registry']->callByPackage('kronolith', 'listAlarms', array($_SERVER['REQUEST_TIME']));
        if (!is_a($alarms, 'PEAR_Error') && !empty($alarms)) {
            require_once 'Horde/Alarm.php';
            $horde_alarm = Horde_Alarm::factory();
            foreach ($alarms as $alarm) {
                $alarm['start'] = new Horde_Date($alarm['start']);
                $alarm['end'] = new Horde_Date($alarm['end']);
                $horde_alarm->set($alarm);
            }
        }
    }

    /* If a maintenance option has been activated, we need to make sure the
     * global Horde 'do_maintenance' pref is also active. */
    if (!$prefs->isLocked('do_maintenance') &&
        !$prefs->getValue('do_maintenance')) {
        foreach (array('purge_events') as $val) {
            if ($prefs->getValue($val)) {
                $prefs->setValue('do_maintenance', true);
                break;
            }
        }
    }

}

/* Get the interval variables for the prefs */
require_once KRONOLITH_BASE . '/lib/Maintenance/kronolith.php';
$maint = &new Maintenance_Kronolith();
foreach (($maint->exportIntervalPrefs()) as $val) {
    $$val = &$intervals;
}

if (!empty($GLOBALS['conf']['holidays']['enable']) &&
    @include_once('Date/Holidays.php')) {
    foreach (Date_Holidays::getInstalledDrivers() as $driver) {
        if ($driver['id'] == 'Composite') {
            continue;
        }
        $_prefs['holiday_drivers']['enum'][$driver['id']] = $driver['title'];
    }
    asort($_prefs['holiday_drivers']['enum']);
}
