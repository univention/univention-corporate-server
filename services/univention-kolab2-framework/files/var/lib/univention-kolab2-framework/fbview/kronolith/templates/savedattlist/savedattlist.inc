<!-- javascript action handling -->
<script language="JavaScript" type="text/javascript">
<!--
    function performAction(id, value)
    {
        document.savedattlistForm.actionID.value = id;
        document.savedattlistForm.actionValue.value = value;
        document.savedattlistForm.submit();
        return false;
    }

    function updateMessage(list)
    {
        if (parent.opener.closed) {
            alert('<?php echo addslashes(_("The Edit Attendees screen is no longer present. Exiting.")) ?>');
            this.close();
            return;
        }

        if (!parent.opener.document.attendeesForm) {
            alert('<?php echo addslashes(_("You can only use this form from the Edit Attendees screen.")) ?>');
            this.close();
            return;
        }

        parent.opener.document.attendeesForm.newAttendees.value = list;
        this.close();
    }
// -->
</script>

<form method="post" action="<?php echo $form_handler; ?>" name="savedattlistForm">
<?php Util::pformInput(); ?>
<input type="hidden" name="actionID" value="" />
<input type="hidden" name="actionValue" value="" />

<div align="center">

<table border="0" width="500" cellspacing="0" cellpadding="2">

<!-- header -->
<tr><td colspan="4" class="header"><b><?php echo $title ?></b></td></tr>

<!-- attendee list header -->
<tr class="item">
 <td nowrap="nowrap" width="2%" align="center"><?php echo $loadimg ?></td>
 <td nowrap="nowrap" width="2%" align="center"><?php echo $delimg ?></td>
 <td nowrap="nowrap" width="96%"><b><?php echo htmlspecialchars(_("Attendees")) ?></b></td>
</tr>

<!-- attendees -->
<?php $i = 0 ?>
<?php if (empty($savedattlist)): ?>
 <tr class="item<?php echo ($i++ % 2) ?>"><td align="center" colspan="3"><i><?php echo htmlspecialchars('-- ' . _("No saved attendee lists are available") . ' --') ?></i></td></tr>
<?php else: foreach ($savedattlist as $index => $list): ?>
 <tr class="item<?php echo ($i++ % 2) ?>">
 <?php
  echo '<td align="center">', Horde::link("javascript:updateMessage('" . addslashes(implode(', ', $list)) . "')", _("Load this list")), $loadimg, "</a></td>";
 ?>
 <?php
  echo '<td align="center">', Horde::link("javascript:performAction(" . KRONOLITH_ACTIONID_REMOVE . ", '" . $index . "')", _("Remove this list")), $delimg, "</a></td>";
 ?>
  <td><?php echo implode(', ', $list); ?></td>
 </tr>
<?php endforeach; endif; ?>

</table>

</div>

</form>
