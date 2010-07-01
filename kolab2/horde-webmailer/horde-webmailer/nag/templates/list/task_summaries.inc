<tr class="<?php echo $style ?>">
  <td>
<?php
if (!is_a($share, 'PEAR_Error') &&
    $share->hasPermission(Auth::getAuth(), PERMS_EDIT)) {
    if (!$task->completed) {
        if (!$task->childrenCompleted()) {
            $label = _("Incomplete sub tasks, complete them first");
            echo Horde::img('unchecked.png', $label, array('title' => $label));
        } else {
            $label = sprintf(_("Complete \"%s\""), $task->name);
            echo Horde::link($task->complete_link, $label) . Horde::img('unchecked.png', $label) . '</a>';
        }
    } else {
        if ($task->parent && $task->parent->completed) {
            $label = _("Completed parent task, mark it as incomplete first");
            echo Horde::img('checked.png', $label, array('title' => $label));
        } else {
            $label = sprintf(_("Mark \"%s\" as incomplete"), $task->name);
            echo Horde::link($task->complete_link, $label) . Horde::img('checked.png', $label) . '</a>';
        }
    }
} else {
    echo Nag::formatCompletion($task->completed);
}
?>
  </td>

<?php if (in_array('tasklist', $columns)): ?>
  <td><?php echo htmlspecialchars($owner) ?></td>
<?php endif; if (in_array('priority', $columns)): ?>
  <td><?php echo Nag::formatPriority($task->priority) ?></td>
<?php endif; ?>
  <td>
    <?php
    if (!is_a($share, 'PEAR_Error') &&
        $share->hasPermission(Auth::getAuth(), PERMS_EDIT) &&
        (!$task->private || $task->owner == Auth::getAuth())) {
        $label = sprintf(_("Edit \"%s\""), $task->name);
        echo Horde::link($task->edit_link, $label) . Horde::img('edit.png', $label, null, $registry->getImageDir('horde')) . '</a>';
    }
    ?>
  </td>
  <td>
    <?php
    echo $task->treeIcons();
    $task_name = strlen($task->name)
        ? htmlspecialchars($task->name)
        : _("[none]");
    if (!is_a($share, 'PEAR_Error') &&
        $share->hasPermission(Auth::getAuth(), PERMS_READ)) {
        echo Horde::link($task->view_link, '', '', '', '', $task->desc)
            . $task_name . '</a>';
    } else {
        echo $task_name;
    }
    ?>
  </td>
  <td><?php echo strlen($task->desc) ? Horde::img('note.png', _("Task Note")) : '&nbsp;' ?></td>
  <td><?php echo ($task->alarm && $task->due) ?
    Horde::img('alarm_small.png', _("Task Alarm")) : '&nbsp;' ?>
  </td>
<?php if (in_array('due', $columns)): ?>
  <td class="nowrap" sortval="<?php echo $task->due ? (int)$task->due : PHP_INT_MAX ?>">
    <?php echo $task->due ? strftime($dateFormat, $task->due) : '&nbsp;' ?>
  </td>
<?php endif; if (in_array('estimate', $columns)): ?>
  <td class="nowrap" sortval="<?php echo htmlspecialchars($task->estimation()) ?>">
   <?php echo htmlspecialchars($task->estimation()) ?>
  </td>
<?php endif; if (in_array('assignee', $columns)): ?>
  <td>
    <?php echo Nag::formatAssignee($task->assignee) ?>
  </td>
<?php endif; if (in_array('category', $columns)): ?>
  <td class="category<?php echo md5($task->category) ?>"><?php echo strlen($task->category) ? htmlspecialchars($task->category) : _("Unfiled") ?></td>
<?php endif; ?>
</tr>
