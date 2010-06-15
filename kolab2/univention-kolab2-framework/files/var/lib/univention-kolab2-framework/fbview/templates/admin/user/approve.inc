<table border="0" cellspacing="0" cellpadding="1" width="100%">
<tr>
  <td align="left" class="header">
    <b><?php echo _("Pending Signups:") ?></b>
  </td>
</tr>
<tr><td class="control"><table border="0" width="100%" cellpadding="1" cellspacing="0">
<tr class="item0">
  <td></td>
  <td></td>
  <td><?php echo _("Username") ?></td>
  <td><?php echo _("Date Received") ?></td>
</tr>
<?php
    $allQueued = $signup->getQueuedSignups();
    if (count($allQueued) == 0) {
?>
<tr>
  <td colspan="4" align="left"><?php echo _("No pending signups.") ?></td>
</tr>
<?php
    } else {
        $i = 1;
        foreach ($allQueued as $signup) {
            if ($signup->getName() != -1) {
                $data = $signup->getData()
?>
<tr class="item<?php echo ($i++ % 2) ?>">
  <td>
     <form method="post" action="<?php echo Horde::selfURL() ?>">
       <input type="hidden" name="user_name" value="<?php echo $signup->getName() ?>" />
       <input type="hidden" name="form" value="approve_f" />
       <input type="submit" class="button" value="<?php echo _("Approve") ?>" />
     </form>
  </td>
  <td>
     <form method="post" action="<?php echo Horde::selfURL() ?>">
       <input type="hidden" name="user_name" value="<?php echo $signup->getName() ?>" />
       <input type="hidden" name="form" value="removequeued_f" />
       <input type="submit" class="button" value="<?php echo _("Remove") ?>" />
     </form>
  </td>
  <td><?php echo $signup->getName() ?></a>&nbsp;</td>
  <td width="100%"><?php echo date('Y-M-d H:i:s', $data['dateReceived']) ?></td>
</tr>
<?php
            }
        }
    }
?>
</table></td></tr>
</table>
<br />
