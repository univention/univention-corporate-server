<?php
/**
 * $Horde: nag/tasks/index.php,v 1.1.2.2 2009-01-06 15:25:10 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

require_once dirname(__FILE__) . '/../lib/base.php';

$search = Util::getGet('q');
if (!$search) {
    header('HTTP/1.0 204 No Content');
    exit;
}

$tasks = Nag::listTasks(
    $prefs->getValue('sortby'),
    $prefs->getValue('sortdir'),
    $prefs->getValue('altsortby'),
    null,
    1);
if (is_a($tasks, 'PEAR_Error')) {
    Horde::fatal($tasks);
}

$search_pattern = '/^' . preg_quote($search, '/') . '/i';
$search_results = new Nag_Task();
$tasks->reset();
while ($task = &$tasks->each()) {
    if (preg_match($search_pattern, $task->name)) {
        $search_results->add($task);
    }
}

$search_results->reset();
if ($search_results->count() == 1) {
    $task = $search_results->each();
    header('Location: ' . Horde::url($task->view_link, true));
    exit;
}

$tasks = $search_results;
$title = sprintf(_("Search: Results for \"%s\""), $search);
$print_view = null;
$actionID = null;

Horde::addScriptFile('popup.js', 'horde', true);
Horde::addScriptFile('tooltip.js', 'horde', true);
Horde::addScriptFile('prototype.js', 'horde', true);
Horde::addScriptFile('effects.js', 'horde', true);
Horde::addScriptFile('QuickFinder.js', 'horde', true);

require NAG_TEMPLATES . '/common-header.inc';
require NAG_TEMPLATES . '/menu.inc';
echo '<div id="page">';
require NAG_TEMPLATES . '/list.html.php';
require NAG_TEMPLATES . '/panel.inc';
require $registry->get('templates', 'horde') . '/common-footer.inc';
