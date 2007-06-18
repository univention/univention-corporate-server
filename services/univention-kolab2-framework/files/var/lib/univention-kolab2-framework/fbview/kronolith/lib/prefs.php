<?php
/**
 * $Horde: kronolith/lib/prefs.php,v 1.3 2004/05/18 19:57:58 chuck Exp $
 *
 * Copyright 2001-2004 Jon Parise <jon@horde.org>
 *
 * See the enclosed file COPYING for license information (GPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

function handle_remote_cal_management($updated)
{
    global $prefs;

    $calName = Util::getFormData('remote_name');
    $calUrl  = Util::getFormData('remote_url');
    $calActionID = Util::getFormData('remote_action', 'add');

    if ($calActionID == 'add') {
        if (!empty($calName) && !empty($calUrl)) {
            $cals = unserialize($prefs->getValue('remote_cals'));
            $cals[] = array('name' => $calName,
                            'url'  => $calUrl);
            $prefs->setValue('remote_cals', serialize($cals));                
            $updated = true;
            return false;
        }
    } else if ($calActionID == 'delete') {
        $cals = unserialize($prefs->getValue('remote_cals'));
        foreach ($cals as $key => $cal) {
            if ($cal['url'] == $calUrl) {
                unset($cals[$key]);
                break;
            }
        }
        $prefs->setValue('remote_cals', serialize($cals));                
        $updated = true;
        return false;
    }
    return true;
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

    return false;
}

if (!$prefs->isLocked('day_hour_start') || !$prefs->isLocked('day_hour_end')) {
    $day_hour_start_options = array();
    for ($i = 0; $i <= 48; $i++) {
        $day_hour_start_options[$i] = date(($prefs->getValue('twentyFour')) ? 'G:i' : 'g:ia', mktime(0, $i * 30, 0));
    }
    $day_hour_end_options = $day_hour_start_options;
}
