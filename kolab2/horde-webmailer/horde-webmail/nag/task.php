<?php
/**
 * $Horde: nag/task.php,v 1.80.8.14 2009-01-06 15:25:04 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Jon Parise <jon@horde.org>
 * @author Jan Schneider <jan@horde.org>
 */

function _delete($task_id, $tasklist_id)
{
    if (!empty($task_id)) {
        $task = Nag::getTask($tasklist_id, $task_id);
        if (is_a($task, 'PEAR_Error')) {
            $GLOBALS['notification']->push(
                sprintf(_("Error deleting task: %s"),
                        $task->getMessage()), 'horde.error');
        } else {
            $share = $GLOBALS['nag_shares']->getShare($tasklist_id);
            if (is_a($share, 'PEAR_Error') ||
                !$share->hasPermission(Auth::getAuth(), PERMS_DELETE)) {
                $GLOBALS['notification']->push(
                    _("Access denied deleting task."), 'horde.error');
            } else {
                $storage = &Nag_Driver::singleton($tasklist_id);
                $result = $storage->delete($task_id);
                if (is_a($result, 'PEAR_Error')) {
                    $GLOBALS['notification']->push(
                        sprintf(_("There was a problem deleting %s: %s"),
                                $task->name, $result->getMessage()),
                        'horde.error');
                } else {
                    $GLOBALS['notification']->push(sprintf(_("Deleted %s."),
                                                           $task->name),
                                                   'horde.success');
                }
            }
        }
    }

    /* Return to the task list. */
    header('Location: ' . Horde::applicationUrl('list.php', true));
    exit;
}

@define('NAG_BASE', dirname(__FILE__));
require_once NAG_BASE . '/lib/base.php';
require_once NAG_BASE . '/lib/Forms/task.php';
$vars = Variables::getDefaultVariables();

/* Redirect to the task list if no action has been requested. */
$actionID = $vars->get('actionID');
if (is_null($actionID)) {
    header('Location: ' . Horde::applicationUrl('list.php', true));
    exit;
}

/* Run through the action handlers. */
switch ($actionID) {
case 'add_task':
    /* Check permissions. */
    if (Nag::hasPermission('max_tasks') !== true &&
        Nag::hasPermission('max_tasks') <= Nag::countTasks()) {
        $message = @htmlspecialchars(sprintf(_("You are not allowed to create more than %d tasks."), Nag::hasPermission('max_tasks')), ENT_COMPAT, NLS::getCharset());
        if (!empty($conf['hooks']['permsdenied'])) {
            $message = Horde::callHook('_perms_hook_denied', array('nag:max_tasks'), 'horde', $message);
        }
        $notification->push($message, 'horde.error', array('content.raw'));
        header('Location: ' . Horde::applicationUrl('list.php', true));
        exit;
    }

    $vars->set('actionID', 'save_task');
    if (!$vars->exists('tasklist_id')) {
        $vars->set('tasklist_id', Nag::getDefaultTasklist(PERMS_EDIT));
    }
    $form = new Nag_TaskForm($vars, _("New Task"));
    break;

case 'modify_task':
    $task_id = $vars->get('task');
    $tasklist_id = $vars->get('tasklist');
    $share = $GLOBALS['nag_shares']->getShare($tasklist_id);
    if (is_a($share, 'PEAR_Error')) {
        $notification->push(sprintf(_("Access denied editing task: %s"), $share->getMessage()), 'horde.error');
    } elseif (!$share->hasPermission(Auth::getAuth(), PERMS_EDIT)) {
        $notification->push(_("Access denied editing task."), 'horde.error');
    } else {
        $task = Nag::getTask($tasklist_id, $task_id);
        if (!isset($task) || !isset($task->id)) {
            $notification->push(_("Task not found."), 'horde.error');
        } elseif ($task->private && $task->owner != Auth::getAuth()) {
            $notification->push(_("Access denied editing task."), 'horde.error');
        } else {
            $vars = new Variables($task->toHash());
            $vars->set('actionID', 'save_task');
            $vars->set('old_tasklist', $task->tasklist);
            $form = new Nag_TaskForm($vars, sprintf(_("Edit: %s"), $task->name), $share->hasPermission(Auth::getAuth(), PERMS_DELETE));
            break;
        }
    }

    /* Return to the task list. */
    header('Location: ' . Horde::applicationUrl('list.php', true));
    exit;

case 'save_task':
    if ($vars->get('submitbutton') == _("Delete this task")) {
        _delete($vars->get('task_id'), $vars->get('old_tasklist'));
    }

    $form = new Nag_TaskForm($vars, $vars->get('task_id') ? sprintf(_("Edit: %s"), $vars->get('name')) : _("New Task"));
    if (!$form->validate($vars)) {
        break;
    }

    $form->getInfo($vars, $info);
    if ($prefs->isLocked('default_tasklist') ||
        count(Nag::listTasklists(false, PERMS_EDIT)) <= 1) {
        $info['tasklist_id'] = $info['old_tasklist'] = Nag::getDefaultTasklist(PERMS_EDIT);
    }
    $share = $GLOBALS['nag_shares']->getShare($info['tasklist_id']);
    if (is_a($share, 'PEAR_Error')) {
        $notification->push(sprintf(_("Access denied saving task: %s"), $share->getMessage()), 'horde.error');
        header('Location: ' . Horde::applicationUrl('list.php', true));
        exit;
    } elseif (!$share->hasPermission(Auth::getAuth(), PERMS_EDIT)) {
        $notification->push(sprintf(_("Access denied saving task to %s."), $share->get('name')), 'horde.error');
        header('Location: ' . Horde::applicationUrl('list.php', true));
        exit;
    }

    /* Add new category. */
    if ($info['category']['new']) {
        require_once 'Horde/Prefs/CategoryManager.php';
        $cManager = new Prefs_CategoryManager();
        $cManager->add($info['category']['value']);
    }

    /* If a task id is set, we're modifying an existing task.
     * Otherwise, we're adding a new task with the provided
     * attributes. */
    if (!empty($info['task_id']) && !empty($info['old_tasklist'])) {
        $storage = &Nag_Driver::singleton($info['old_tasklist']);
        $result = $storage->modify($info['task_id'], $info['name'],
                                   $info['desc'], $info['start'],
                                   $info['due'], $info['priority'],
                                   (float)$info['estimate'],
                                   (int)$info['completed'],
                                   $info['category']['value'],
                                   $info['alarm'], $info['parent'],
                                   (int)$info['private'], Auth::getAuth(),
                                   $info['assignee'], null,
                                   $info['tasklist_id']);
    } else {
        /* Check permissions. */
        if (Nag::hasPermission('max_tasks') !== true &&
            Nag::hasPermission('max_tasks') <= Nag::countTasks()) {
            header('Location: ' . Horde::applicationUrl('list.php', true));
            exit;
        }

        /* Creating a new task. */
        $storage = &Nag_Driver::singleton($info['tasklist_id']);
        $result = $storage->add($info['name'], $info['desc'],
                                $info['start'], $info['due'],
                                $info['priority'],
                                (float)$info['estimate'],
                                (int)$info['completed'],
                                $info['category']['value'],
                                $info['alarm'], null, $info['parent'],
                                (int)$info['private'],
                                Auth::getAuth(),
                                $info['assignee']);
    }

    /* Check our results. */
    if (is_a($result, 'PEAR_Error')) {
        $notification->push(sprintf(_("There was a problem saving the task: %s."), $result->getMessage()), 'horde.error');
    } else {
        $notification->push(sprintf(_("Saved %s."), $info['name']), 'horde.success');
        /* Return to the task list. */
        header('Location: ' . Horde::applicationUrl('list.php', true));
        exit;
    }

    break;

case 'delete_tasks':
    /* Delete the task if we're provided with a valid task ID. */
    _delete(Util::getFormData('task'), Util::getFormData('tasklist'));

case 'complete_task':
    /* Toggle the task's completion status if we're provided with a
     * valid task ID. */
    $task_id = Util::getFormData('task');
    $tasklist_id = Util::getFormData('tasklist');
    if (isset($task_id)) {
        $share = $GLOBALS['nag_shares']->getShare($tasklist_id);
        $task = Nag::getTask($tasklist_id, $task_id);
        if (is_a($share, 'PEAR_Error') || !$share->hasPermission(Auth::getAuth(), PERMS_EDIT)) {
            $notification->push(sprintf(_("Access denied completing task %s."), $task->name), 'horde.error');
        } else {
            $task->completed = !$task->completed;
            if ($task->completed) {
                $task->completed_date = time();
            } else {
                $task->completed_date = null;
            }
            $result = $task->save();
            if (is_a($result, 'PEAR_Error')) {
                $notification->push(sprintf(_("There was a problem completing %s: %s"),
                                            $task->name, $result->getMessage()), 'horde.error');
            } else {
                if ($task->completed) {
                    $notification->push(sprintf(_("Completed %s."), $task->name), 'horde.success');
                } else {
                    $notification->push(sprintf(_("%s is now incomplete."), $task->name), 'horde.success');
                }
            }
        }
    }

    $url = $vars->get('url');
    if (!empty($url)) {
        header('Location: ' . $url);
    } else {
        header('Location: ' . Horde::applicationUrl('list.php', true));
    }
    exit;

default:
    header('Location: ' . Horde::applicationUrl('list.php', true));
    exit;
}

$title = $form->getTitle();
require NAG_TEMPLATES . '/common-header.inc';
require NAG_TEMPLATES . '/menu.inc';
$form->renderActive();
require $registry->get('templates', 'horde') . '/common-footer.inc';
