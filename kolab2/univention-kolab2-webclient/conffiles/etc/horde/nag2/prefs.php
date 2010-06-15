<?php

@%@BCWARNING=// @%@

/**
 * $Horde: nag/config/prefs.php.dist,v 1.51 2007/07/16 22:22:02 chuck Exp $
 *
 * See horde/config/prefs.php for documentation on the structure of this file.
 */

// Make sure that constants are defined.
@define('NAG_BASE', '/usr/share/horde3/nag/');
require_once NAG_BASE . '/lib/Nag.php';

$prefGroups['display'] = array(
    'column' => _("General Options"),
    'label' => _("Display Options"),
    'desc' => _("Change your task sorting and display options."),
    'members' => array('show_tasklist', 'show_panel', 'sortby', 'altsortby', 'sortdir'),
);

$prefGroups['deletion'] = array(
    'column' => _("General Options"),
    'label' => _("Delete Confirmation"),
    'desc' => _("Delete button behaviour"),
    'members' => array('delete_opt'),
);

$prefGroups['tasks'] = array(
    'column' => _("General Options"),
    'label' => _("Task Defaults"),
    'desc' => _("Defaults for new tasks"),
    'members' => array('default_due', 'default_due_days', 'defaultduetimeselect'),
);

$prefGroups['share'] = array(
    'column' => _("Task List and Share Options"),
    'label' => _("Default Task List"),
    'desc' => _("Choose your default task list."),
    'members' => array('tasklistselect'),
);

$prefGroups['notification'] = array(
    'column' => _("Task List and Share Options"),
    'label' => _("Notifications"),
    'desc' => _("Choose if you want to be notified of task changes and task alarms."),
    'members' => array('task_notification'),
);
if (!empty($GLOBALS['conf']['alarms']['driver'])) {
    $prefGroups['notification']['members'][] = 'task_alarms';
}

$_show_external = array();
if ($GLOBALS['registry']->hasMethod('getListTypes', 'whups')) {
    $_show_external['whups'] = $GLOBALS['registry']->get('name', 'whups');
}
if (count($_show_external)) {
    $prefGroups['external'] = array(
        'column'  => _("Task List and Share Options"),
        'label'   => _("External Data"),
        'desc'    => _("Show data from other applications or sources."),
        'members' => array('show_external'),
    );
}

// show a tasklist column in the list view?
$_prefs['show_tasklist'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Should the Task List be shown in its own column in the List view?")
);

// show the tasklist options panel?
// a value of 0 = no, 1 = yes
$_prefs['show_panel'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Show task list options panel?"),
);

// user preferred sorting column
$_prefs['sortby'] = array(
    'value' => NAG_SORT_PRIORITY,
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array(NAG_SORT_PRIORITY => _("Priority"),
                    NAG_SORT_NAME => _("Task Name"),
                    NAG_SORT_CATEGORY => _("Category"),
                    NAG_SORT_DUE => _("Due Date"),
                    NAG_SORT_COMPLETION => _("Completed?"),
                    NAG_SORT_OWNER => _("Tasklist")),
    'desc' => _("Sort tasks by:"),
);

// alternate sort column
$_prefs['altsortby'] = array(
    'value' => NAG_SORT_CATEGORY,
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array(NAG_SORT_PRIORITY => _("Priority"),
                    NAG_SORT_NAME => _("Task Name"),
                    NAG_SORT_CATEGORY => _("Category"),
                    NAG_SORT_DUE => _("Due Date"),
                    NAG_SORT_COMPLETION => _("Completed?"),
                    NAG_SORT_OWNER => _("Tasklist")),
    'desc' => _("Then:"),
);

// user preferred sorting direction
$_prefs['sortdir'] = array(
    'value' => NAG_SORT_ASCEND,
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array(NAG_SORT_ASCEND => _("Ascending"),
                    NAG_SORT_DESCEND => _("Descending")),
    'desc' => _("Sort direction:"),
);

// preference for delete confirmation dialog.
$_prefs['delete_opt'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Do you want to confirm deleting entries?"),
);

// default to tasks having a due date?
$_prefs['default_due'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("When creating a new task, should it default to having a due date?"),
);

// default number of days out for due dates
$_prefs['default_due_days'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'number',
    'desc' => _("When creating a new task, how many days in the future should the default due date be (0 means today)?"),
);

// default due time
$_prefs['default_due_time'] = array(
    'value' => 'now',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit',
);

// default due time selection widget
$_prefs['defaultduetimeselect'] = array('type' => 'special');

// new task notifications
$_prefs['task_notification'] = array(
    'value' => '',
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array('' => _("No"),
                    'owner' => _("On my tasklists only"),
                    'show' => _("On all shown tasklists"),
                    'read' => _("On all tasklists I have read access to")),
    'desc' => _("Choose if you want to be notified of new, edited, and deleted tasks by email:"),
);

// alarm methods
$_prefs['task_alarms'] = array(
    'value' => 'a:1:{s:6:"notify";a:0:{}}',
    'locked' => false,
    'shared' => false,
    'type' => 'alarm',
    'desc' => _("Choose how you want to receive reminders for tasks with alarms:"),
);

// show data from other applications that can be listed as tasks?
if (count($_show_external)) {
    $_prefs['show_external'] = array(
        'value' => 'a:0:{}',
        'locked' => false,
        'shared' => false,
        'type' => 'multienum',
        'enum' => $_show_external,
        'desc' => _("Show data from any of these other applications in your task list?"),
    );
}

// show complete/incomplete tasks?
$_prefs['show_completed'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array(1 => _("All tasks"),
                    0 => _("Incomplete tasks"),
                    2 => _("Complete tasks")),
    'desc' => _("Show complete, incomplete, or all tasks in the task list?"),
);

// user task categories
$_prefs['task_categories'] = array(
    'value' => '',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit'
);

// default tasklist selection widget
$_prefs['tasklistselect'] = array('type' => 'special');

// default tasklists
// Set locked to true if you don't want users to have multiple tasklists.
$_prefs['default_tasklist'] = array(
    'value' => Auth::getAuth() ? Auth::getAuth() : 0,
    'locked' => false,
    'shared' => true,
    'type' => 'implicit',
);

// store the tasklists to diplay
$_prefs['display_tasklists'] = array(
    'value' => 'a:0:{}',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit',
);
