<?php

require NAG_TEMPLATES . '/list/header.inc';

if ($tasks->hasTasks()) {
    $sortby = $prefs->getValue('sortby');
    $sortdir = $prefs->getValue('sortdir');
    $dateFormat = $prefs->getValue('date_format');
    $columns = @unserialize($prefs->getValue('tasklist_columns'));
    $dynamic_sort = true;

    $baseurl = 'list.php';
    if ($actionID == 'search_tasks') {
        $baseurl = Util::addParameter(
            $baseurl,
            array('actionID' => 'search_tasks',
                  'search_pattern' => $search_pattern,
                  'search_name' => $search_name ? 'on' : 'off',
                  'search_desc' => $search_desc ? 'on' : 'off',
                  'search_category' => $search_category ? 'on' : 'off'));
    }

    require NAG_TEMPLATES . '/list/task_headers.inc';

    $tasks->reset();
    while ($task = $tasks->each()) {
        $dynamic_sort &= !$task->hasSubTasks();

        if (!empty($task->completed)) {
            $style = 'linedRow closed';
        } elseif (!empty($task->due) && $task->due < time()) {
            $style = 'linedRow overdue';
        } else {
            $style = 'linedRow';
        }

        if ($task->tasklist == '**EXTERNAL**') {
            // Just use a new share that this user owns for tasks from
            // external calls - if the API gives them back, we'll trust it.
            $share = $GLOBALS['nag_shares']->newShare('**EXTERNAL**');
            $owner = $task->tasklist_name;
        } else {
            $share = $GLOBALS['nag_shares']->getShare($task->tasklist);
            $owner = is_a($share, 'PEAR_Error') ? $task->tasklist : $share->get('name');
        }

        require NAG_TEMPLATES . '/list/task_summaries.inc';
    }

    require NAG_TEMPLATES . '/list/task_footers.inc';

    if (!$print_view && $dynamic_sort) {
        Horde::addScriptFile('tables.js', 'nag', true);
    }
} else {
    require NAG_TEMPLATES . '/list/empty.inc';
}
