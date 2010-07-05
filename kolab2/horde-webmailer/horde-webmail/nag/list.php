<?php
/**
 * $Horde: nag/list.php,v 1.93.8.11 2009-01-06 15:25:04 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

@define('NAG_BASE', dirname(__FILE__));
require_once NAG_BASE . '/lib/base.php';
require_once 'Horde/Variables.php';

$vars = Variables::getDefaultVariables();

/* Get the current action ID. */
$actionID = Util::getFormData('actionID');

/* Sort out the sorting values and task filtering. */
if (($sortby = Util::getFormData('sortby')) !== null) {
    $prefs->setValue('sortby', $sortby);
}
if (($sortdir = Util::getFormData('sortdir')) !== null) {
    $prefs->setValue('sortdir', $sortdir);
}
if ($vars->exists('show_completed')) {
    $prefs->setValue('show_completed', $vars->get('show_completed'));
} else {
    $vars->set('show_completed', $prefs->getValue('show_completed'));
}

/* Page variables. */
$title = _("My Tasks");

switch ($actionID) {
case 'search_tasks':
    /* Get the search parameters. */
    $search_pattern = Util::getFormData('search_pattern');
    $search_name = (Util::getFormData('search_name') == 'on');
    $search_desc = (Util::getFormData('search_desc') == 'on');
    $search_category = (Util::getFormData('search_category') == 'on');
    $search_completed = Util::getFormData('search_completed');

    $vars->set('show_completed', $search_completed);

    /* Get the full, sorted task list. */
    $tasks = Nag::listTasks($prefs->getValue('sortby'),
                            $prefs->getValue('sortdir'),
                            $prefs->getValue('altsortby'),
                            null,
                            $search_completed);
    if (is_a($tasks, 'PEAR_Error')) {
        $notification->push($tasks, 'horde.error');
        $tasks = new Nag_Task();
    }

    if (!empty($search_pattern) &&
        ($search_name || $search_desc || $search_category)) {
        $pattern = '/' . preg_quote($search_pattern, '/') . '/i';
        $search_results = new Nag_Task();
        $tasks->reset();
        while ($task = &$tasks->each()) {
            if (($search_name && preg_match($pattern, $task->name)) ||
                ($search_desc && preg_match($pattern, $task->desc)) ||
                ($search_category && preg_match($pattern, $task->category))) {
                $search_results->add($task);
            }
        }

        /* Reassign $tasks to the search result. */
        $tasks = $search_results;
        $title = sprintf(_("Search: Results for \"%s\""), $search_pattern);
    }
    break;

default:
    /* Get the full, sorted task list. */
    $tasks = Nag::listTasks($prefs->getValue('sortby'),
                            $prefs->getValue('sortdir'),
                            $prefs->getValue('altsortby'));
    if (is_a($tasks, 'PEAR_Error')) {
        $notification->push($tasks, 'horde.error');
        $tasks = new Nag_Task();
    }
    break;
}

$print_view = (bool)Util::getFormData('print');
if (!$print_view) {
    Horde::addScriptFile('popup.js', 'horde', true);
    Horde::addScriptFile('tooltip.js', 'horde', true);
    Horde::addScriptFile('prototype.js', 'nag', true);
    Horde::addScriptFile('effects.js', 'nag', true);
    Horde::addScriptFile('QuickFinder.js', 'nag', true);
    $print_link = Horde::applicationUrl(Util::addParameter('list.php', array('print' => 1)));
}

require NAG_TEMPLATES . '/common-header.inc';

if ($print_view) {
    require_once $registry->get('templates', 'horde') . '/javascript/print.js';
} else {
    require NAG_TEMPLATES . '/menu.inc';
    echo '<div id="page">';

    if (!$prefs->isLocked('show_completed')) {
        require_once 'Horde/UI/Tabs.php';
        $listurl = Horde::applicationUrl('list.php');
        $tabs = new Horde_UI_Tabs('show_completed', $vars);
        $tabs->addTab(_("_All tasks"), $listurl, 1);
        $tabs->addTab(_("Incom_plete tasks"), $listurl, 0);
        $tabs->addTab(_("_Future tasks"), $listurl, 3);
        $tabs->addTab(_("_Completed tasks"), $listurl, 2);
        echo $tabs->render($vars->get('show_completed'));
    }
}

require NAG_TEMPLATES . '/list.html.php';

if (!$print_view) {
    require NAG_TEMPLATES . '/panel.inc';
}
require $registry->get('templates', 'horde') . '/common-footer.inc';
