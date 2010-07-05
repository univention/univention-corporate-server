<?php
/**
 * $Horde: nag/data.php,v 1.39.8.19 2009-01-06 15:25:04 jan Exp $
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

@define('NAG_BASE', dirname(__FILE__));
require_once NAG_BASE . '/lib/base.php';
require_once 'Horde/Data.php';

if (!$conf['menu']['import_export']) {
    require NAG_BASE . '/index.php';
    exit;
}

/* Importable file types. */
$file_types = array('csv' => _("CSV"),
                    'vtodo' => _("iCalendar (vTodo)"));

/* Templates for the different import steps. */
$templates = array(
    IMPORT_CSV => array($registry->get('templates', 'horde') . '/data/csvinfo.inc'),
    IMPORT_MAPPED => array($registry->get('templates', 'horde') . '/data/csvmap.inc'),
    IMPORT_DATETIME => array($registry->get('templates', 'horde') . '/data/datemap.inc')
);
if (Nag::hasPermission('max_tasks') !== true &&
    Nag::hasPermission('max_tasks') <= Nag::countTasks()) {
    $message = @htmlspecialchars(sprintf(_("You are not allowed to create more than %d tasks."), Nag::hasPermission('max_tasks')), ENT_COMPAT, NLS::getCharset());
    if (!empty($conf['hooks']['permsdenied'])) {
        $message = Horde::callHook('_perms_hook_denied', array('nag:max_tasks'), 'horde', $message);
    }
    $notification->push($message, 'horde.warning', array('content.raw'));
    $templates[IMPORT_FILE] = array(NAG_TEMPLATES . '/data/export.inc');
} else {
    $templates[IMPORT_FILE] = array(NAG_TEMPLATES . '/data/import.inc', NAG_TEMPLATES . '/data/export.inc');
}

/* Field/clear name mapping. */
$app_fields = array('name'           => _("Name"),
                    'desc'           => _("Description"),
                    'category'       => _("Category"),
                    'assignee'       => _("Assignee"),
                    'due'            => _("Due By"),
                    'alarm'          => _("Alarm"),
                    'start'          => _("Start"),
                    'priority'       => _("Priority"),
                    'private'        => _("Private Task"),
                    'estimate'       => _("Estimated Time"),
                    'completed'      => _("Completion Status"),
                    'completed_date' => _("Completion Date"),
                    'uid'            => _("Unique ID"));

/* Date/time fields. */
$time_fields = array('due' => 'datetime');

/* Initial values. */
$param = array('time_fields' => $time_fields,
               'file_types'  => $file_types);
$import_format = Util::getFormData('import_format', '');
$import_step   = Util::getFormData('import_step', 0) + 1;
$next_step     = IMPORT_FILE;
$actionID      = Util::getFormData('actionID');
$error         = false;

/* Loop through the action handlers. */
switch ($actionID) {
case 'export':
    $exportID = Util::getFormData('exportID');
    $tasklists = Util::getFormData('exportList', $display_tasklists);
    if (!is_array($tasklists)) {
        $tasklists = array($tasklists);
    }

    /* Get the full, sorted task list. */
    $tasks = Nag::listTasks(null, null, null, $tasklists,
                            Util::getFormData('exportTasks'));
    if (is_a($tasks, 'PEAR_Error')) {
        $notification->push($tasks);
        $error = true;
    } elseif (!$tasks->hasTasks()) {
        $notification->push(_("There were no tasks to export."), 'horde.message');
        $error = true;
    } else {
        $tasks->reset();
        switch ($exportID) {
        case EXPORT_CSV:
            $data = array();
            while ($task = $tasks->each()) {
                $task = $task->toHash();
                unset($task['task_id']);
                $task['desc'] = str_replace(',', '', $task['desc']);
                unset($task['tasklist_id']);
                unset($task['parent']);
                unset($task['view_link']);
                unset($task['complete_link']);
                unset($task['edit_link']);
                unset($task['delete_link']);
                $data[] = $task;
            }
            $csv = &Horde_Data::singleton('csv');
            $csv->exportFile(_("tasks.csv"), $data, true);
            exit;

        case EXPORT_ICALENDAR:
            require_once NAG_BASE . '/lib/version.php';
            require_once 'Horde/iCalendar.php';
            $iCal = new Horde_iCalendar();
            $iCal->setAttribute(
                'PRODID',
                '-//The Horde Project//Nag ' . NAG_VERSION . '//EN');
            while ($task = $tasks->each()) {
                $iCal->addComponent($task->toiCalendar($iCal));
            }
            $data = $iCal->exportvCalendar();
            $browser->downloadHeaders(_("tasks.ics"), 'text/calendar', false, strlen($data));
            echo $data;
            exit;
        }
    }
    break;

case IMPORT_FILE:
    $_SESSION['import_data']['target'] = Util::getFormData('tasklist_target');
    break;
}

if (!$error) {
    $data = &Horde_Data::singleton($import_format);
    if (is_a($data, 'PEAR_Error')) {
        $notification->push(_("This file format is not supported."), 'horde.error');
        $next_step = IMPORT_FILE;
    } else {
        $next_step = $data->nextStep($actionID, $param);
        if (is_a($next_step, 'PEAR_Error')) {
            $notification->push($next_step->getMessage(), 'horde.error');
            $next_step = $data->cleanup();
        }
    }
}

/* We have a final result set. */
if (is_array($next_step)) {
    /* Create a category manager. */
    require_once 'Horde/Prefs/CategoryManager.php';
    $cManager = new Prefs_CategoryManager();
    $categories = $cManager->get();

    /* Create a Nag storage instance. */
    $storage = &Nag_Driver::singleton($_SESSION['import_data']['target']);
    $max_tasks = Nag::hasPermission('max_tasks');
    $num_tasks = Nag::countTasks();
    $result = null;
    foreach ($next_step as $row) {
        if ($max_tasks !== true && $num_tasks >= $max_tasks) {
            $message = @htmlspecialchars(sprintf(_("You are not allowed to create more than %d tasks."), Nag::hasPermission('max_tasks')), ENT_COMPAT, NLS::getCharset());
            if (!empty($conf['hooks']['permsdenied'])) {
                $message = Horde::callHook('_perms_hook_denied', array('nag:max_tasks'), 'horde', $message);
            }
            $notification->push($message, 'horde.error', array('content.raw'));
            break;
        }

        if (!is_array($row)) {
            if (!is_a($row, 'Horde_iCalendar_vtodo')) {
                continue;
            }
            $task = new Nag_Task();
            $task->fromiCalendar($row);
            $row = $task->toHash();
            foreach ($app_fields as $field => $null) {
                if (!isset($row[$field])) {
                    $row[$field] = '';
                }
            }
        }

        $result = $storage->add($row['name'], $row['desc'], $row['start'],
                                $row['due'], $row['priority'],
                                $row['estimate'], $row['completed'],
                                $row['category'], $row['alarm'], $row['uid'],
                                isset($row['parent']) ? $row['parent'] : '',
                                $row['private'], Auth::getAuth(),
                                $row['assignee']);
        if (is_a($result, 'PEAR_Error')) {
            break;
        }

        if (!empty($row['category']) &&
            !in_array($row['category'], $categories)) {
            $cManager->add($row['category']);
            $categories[] = $row['category'];
        }

        $num_tasks++;
    }


    if (!count($next_step)) {
        $notification->push(sprintf(_("The %s file didn't contain any tasks."),
                                    $file_types[$_SESSION['import_data']['format']]), 'horde.error');
    } elseif (is_a($result, 'PEAR_Error')) {
        $notification->push(sprintf(_("There was an error importing the data: %s"),
                                    $result->getMessage()), 'horde.error');
    } else {
        $notification->push(sprintf(_("%s successfully imported"),
                                    $file_types[$_SESSION['import_data']['format']]), 'horde.success');
    }
    $next_step = $data->cleanup();
}

$title = _("Import/Export Tasks");
require NAG_TEMPLATES . '/common-header.inc';
require NAG_TEMPLATES . '/menu.inc';

foreach ($templates[$next_step] as $template) {
    require $template;
    echo '<br />';
}

require $registry->get('templates', 'horde') . '/common-footer.inc';
