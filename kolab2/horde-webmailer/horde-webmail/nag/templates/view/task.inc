<div class="header">
 <span class="smallheader rightFloat"><?php echo implode(' | ', $links) ?></span>
 <?php echo htmlspecialchars($task->name) ?>
</div>

<table cellspacing="0" width="100%" class="headerbox striped nowrap task">
 <tr>
  <td class="rightAlign" valign="top"><strong><?php echo _("Category") ?></strong></td>
  <td width="100%"><?php echo htmlspecialchars($task->category ? $task->category : _("Unfiled")) ?></td>
 </tr>
 <tr>
  <td class="rightAlign" valign="top"><strong><?php echo _("Assignee") ?></strong></td>
  <td><?php echo Nag::formatAssignee($task->assignee, true) ?></td>
 </tr>
 <tr>
  <td class="rightAlign"><strong><?php echo _("Private?") ?></strong></td>
  <td>
   <?php echo $task->private ? Horde::img('checked.png', _("Private")) : Horde::img('unchecked.png', _("Not Private")) ?>
  </td>
 </tr>
 <tr>
  <td class="rightAlign" valign="top"><strong><?php echo _("Start Date") ?></strong></td>
  <td><?php echo Nag::formatDate($task->start, false) ?></td>
 </tr>
 <tr>
  <td class="rightAlign" valign="top"><strong><?php echo _("Due By") ?></strong></td>
  <td><?php echo Nag::formatDate($task->due) ?></td>
 </tr>
 <tr>
  <td class="rightAlign" valign="top"><strong><?php echo _("Alarm") ?></strong></td>
  <td><?php echo htmlspecialchars($alarm_text) ?></td>
 </tr>
 <tr>
  <td class="rightAlign" valign="top"><strong><?php echo _("Priority") ?></strong></td>
  <td><?php echo Nag::formatPriority($task->priority) ?></td>
 </tr>
 <tr>
  <td class="rightAlign" valign="top"><strong><?php echo _("Estimated Time") ?></strong></td>
  <td><?php echo htmlspecialchars($task->estimate); if ($task->hasSubTasks()) echo htmlspecialchars(sprintf(_(" (%s including sub-tasks)"), $task->estimation())) ?></td>
 </tr>
 <tr>
  <td class="rightAlign" valign="top"><strong><?php echo _("Completed?") ?></strong></td>
  <td>
  <?php if (!$print_view && !is_a($share, 'PEAR_Error') && $share->hasPermission(Auth::getAuth(), PERMS_EDIT)) {
            if (empty($task->completed)) {
                echo Horde::link(Horde::applicationUrl(Util::addParameter($taskurl, 'actionID', 'complete_task')), _("Complete Task"), 'widget') . Horde::img('unchecked.png', _("Complete Task")) . '</a>';
            } else {
                echo Horde::link(Horde::applicationUrl(Util::addParameter($taskurl, 'actionID', 'complete_task')), _("Mark as incomplete"), 'widget') . Horde::img('checked.png', _("Mark as incomplete")) . '</a>';
            }
        } else {
            echo Nag::formatCompletion($task->completed) . '</a></td>';
        }
        if (isset($completed)) {
            echo ' <small>' . strftime($prefs->getValue('date_format'), $completed) . ' ' . date($prefs->getValue('twentyFour') ? 'G:i' : 'g:i a', $completed) . '</small>';
        } ?>
  </td>
 </tr>

<?php if (isset($created)): ?>
 <tr>
  <td class="rightAlign"><strong><?php echo _("Created") ?></strong></td>
  <td><?php echo strftime($prefs->getValue('date_format'), $created) . ' ' . date($prefs->getValue('twentyFour') ? 'G:i' : 'g:i a', $created) . ' ' . @htmlspecialchars($createdby, ENT_COMPAT, NLS::getCharset()) ?></td>
 </tr>
<?php endif; ?>

<?php if (isset($modified)): ?>
 <tr>
  <td class="rightAlign"><strong><?php echo _("Last Modified") ?></strong></td>
  <td><?php echo strftime($prefs->getValue('date_format'), $modified) . ' ' . date($prefs->getValue('twentyFour') ? 'G:i' : 'g:i a', $modified) . ' ' . @htmlspecialchars($modifiedby, ENT_COMPAT, NLS::getCharset()) ?></td>
 </tr>
<?php endif; ?>

<?php if (strlen($task->desc)): ?>
 <tr>
  <td colspan="2" class="taskBody">
   <?php echo $task->getFormattedDescription() ?>
  </td>
 </tr>
<?php endif; ?>
</table>
