<h1 class="header">
 <?php echo _("Pending Signups:") ?>
</h1>

<?php $allQueued = $signup->getQueuedSignups() ?>
<?php if (is_a($allQueued, 'PEAR_Error')): ?>
 <div class="text"><em><?php echo htmlspecialchars($allQueued->getMessage()) ?></em></div>
<?php elseif (!count($allQueued)): ?>
 <div class="text"><em><?php echo _("No pending signups.") ?></em></div>
<?php else: ?>
<table class="striped horde-table" id="signup-pending" cellspacing="0">
<thead>
 <tr>
  <th>&nbsp;</th>
  <th>&nbsp;</th>
  <th class="leftAlign"><?php echo _("Username") ?></th>
  <th class="leftAlign"><?php echo _("Date Received") ?></th>
 </tr>
</thead>
<tbody>
<?php foreach ($allQueued as $signup): $data = $signup->getData(); ?>
 <tr>
  <td>
   <form method="post" action="<?php echo Horde::selfUrl() ?>">
    <input type="hidden" name="user_name" value="<?php echo $signup->getName() ?>" />
    <input type="hidden" name="form" value="approve_f" />
    <input type="submit" class="button" value="<?php echo _("Approve") ?>" />
   </form>
  </td>
  <td>
   <form method="post" action="<?php echo Horde::selfUrl() ?>">
    <input type="hidden" name="user_name" value="<?php echo $signup->getName() ?>" />
    <input type="hidden" name="form" value="removequeued_f" />
    <input type="submit" class="button" value="<?php echo _("Remove") ?>" />
   </form>
  </td>
  <td><?php echo htmlspecialchars($signup->getName()) ?></td>
  <td><?php echo date('Y-m-d H:i:s', $data['dateReceived']) ?></td>
 </tr>
<?php endforeach; ?>
</tbody>
</table>
<?php endif; ?>
<br class="spacer" />
