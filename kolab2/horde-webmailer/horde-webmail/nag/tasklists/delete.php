<?php
/**
 * $Horde: nag/tasklists/delete.php,v 1.2.2.3 2009-01-06 15:25:09 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

@define('NAG_BASE', dirname(dirname(__FILE__)));
require_once NAG_BASE . '/lib/base.php';
require_once NAG_BASE . '/lib/Forms/DeleteTaskList.php';

// Exit if this isn't an authenticated user.
if (!Auth::getAuth()) {
    header('Location: ' . Horde::applicationUrl('list.php', true));
    exit;
}

$vars = Variables::getDefaultVariables();
$tasklist_id = $vars->get('t');
if ($tasklist_id == Auth::getAuth()) {
    $notification->push(_("This task list cannot be deleted."), 'horde.warning');
    header('Location: ' . Horde::applicationUrl('tasklists/', true));
    exit;
}

$tasklist = $nag_shares->getShare($tasklist_id);
if (is_a($tasklist, 'PEAR_Error')) {
    $notification->push($tasklist, 'horde.error');
    header('Location: ' . Horde::applicationUrl('tasklists/', true));
    exit;
} elseif ($tasklist->get('owner') != Auth::getAuth()) {
    $notification->push(_("You are not allowed to delete this task list."), 'horde.error');
    header('Location: ' . Horde::applicationUrl('tasklists/', true));
    exit;
}

$form = new Nag_DeleteTaskListForm($vars, $tasklist);

// Execute if the form is valid (must pass with POST variables only).
if ($form->validate(new Variables($_POST))) {
    $result = $form->execute();
    if (is_a($result, 'PEAR_Error')) {
        $notification->push($result, 'horde.error');
    } elseif ($result) {
        $notification->push(sprintf(_("The task list \"%s\" has been deleted."), $tasklist->get('name')), 'horde.success');
    }

    header('Location: ' . Horde::applicationUrl('tasklists/', true));
    exit;
}

$title = $form->getTitle();
require NAG_TEMPLATES . '/common-header.inc';
require NAG_TEMPLATES . '/menu.inc';
echo $form->renderActive($form->getRenderer(), $vars, 'delete.php', 'post');
require $registry->get('templates', 'horde') . '/common-footer.inc';
