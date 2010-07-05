<?php
/**
 * $Horde: nag/lib/prefs.php,v 1.3.10.7 2009-01-06 15:25:05 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

function handle_tasklistselect($updated)
{
    $default_tasklist = Util::getFormData('default_tasklist');
    if (!is_null($default_tasklist)) {
        $tasklists = Nag::listTasklists();
        if (is_array($tasklists) && isset($tasklists[$default_tasklist])) {
            $GLOBALS['prefs']->setValue('default_tasklist', $default_tasklist);
            return true;
        }
    }

    return false;
}

function handle_showsummaryselect($updated)
{
    $GLOBAL['prefs']->setValue('summary_categories', Util::getFormData('summary_categories'));
    return true;
}

function handle_defaultduetimeselect($updated)
{
    $GLOBALS['prefs']->setValue('default_due_time', Util::getFormData('default_due_time'));
    return true;
}
