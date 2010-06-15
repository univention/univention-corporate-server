<!-- javascript action handling -->
<script language="JavaScript" type="text/javascript">
<!--
    function performAction(id, value)
    {
        document.attendeesForm.actionID.value = id;
        document.attendeesForm.actionValue.value = value;
        document.attendeesForm.submit();
        return false;
    }

    function switchTimestamp(timestamp)
    {
        document.attendeesForm.timestamp.value = timestamp;
        document.attendeesForm.submit();
        return false;
    }

    function switchView(view)
    {
        document.attendeesForm.view.value = view;
        document.attendeesForm.submit();
        return false;
    }
// -->
</script>

<form method="post" action="<?php echo $form_handler; ?>" name="attendeesForm">
<?php Util::pformInput(); ?>
<input type="hidden" name="actionID" value="" />
<input type="hidden" name="actionValue" value="" />
<input type="hidden" name="view" value="<?php echo $view ?>" />
<input type="hidden" name="timestamp" value="<?php echo $timestamp ?>" />

<div align="center">

<table border="0" width="500" cellspacing="0" cellpadding="2">

<!-- header -->
<tr><td colspan="2" class="header"><b><?php echo $title ?></b></td></tr>

<!-- attendee list header -->
<tr class="item">
 <td nowrap="nowrap" width="2%" align="center"><?php echo $delimg ?></td>
 <td nowrap="nowrap" width="48%"><b><?php echo htmlspecialchars(_("Email Address")) ?></b></td>
</tr>

<!-- attendees -->
<?php $i = 0 ?>
<?php if (count($attendees) < 1): ?>
 <tr class="item<?php echo ($i++ % 2) ?>"><td align="center" colspan="2"><i><?php echo htmlspecialchars('-- ' . _("No attendees") . ' --') ?></i></td></tr>
<?php else: foreach ($attendees as $email => $status): ?>
 <tr class="item<?php echo ($i++ % 2) ?>">
 <?php
  $statustext = sprintf(_("Remove %s"), $email);
  echo '<td align="center">', Horde::link("javascript:performAction(" . KRONOLITH_ACTIONID_REMOVE . ", '" . addslashes($email) . "')", $statustext), Horde::img('delete.gif', $statustext, null, $registry->getParam('graphics', 'horde')), "</a></td>";
 ?>
  <td><?php echo Horde::link('mailto:'.htmlspecialchars($email), sprintf(_("Send an email to %s"), $email)), htmlspecialchars($email) . '</a>'; ?></td>
 </tr>
<?php endforeach; endif; ?>
<tr>
<td align="center" class="item<?php echo ($i % 2) ?>">
 <input type="button" class="button" name="clearAll" value="<?php echo htmlspecialchars(_("Clear all attendees")) ?>" onclick="<?php echo "javascript:performAction(" . KRONOLITH_ACTIONID_CLEAR . ", '')" ?>" />
</td>
<td class="item<?php echo ($i++ % 2) ?>" >&nbsp;</td>
</tr>
</table>

<br /><br />

<?php $i = 0 ?>
<table border="0" width="500" cellspacing="0" cellpadding="2">
<tr><td align="right" class="light" nowrap="nowrap"><b><?php echo Horde::highlightAccessKey(_("Add attendees"), $ak = Horde::getAccessKey(_("Add attendees"))) ?>&nbsp;&nbsp;</b></td>
<td align="left" class="item<?php echo ($i++ % 2) ?>" colspan="2"><input type="text" name="newAttendees" size="50" maxlength="255" <?php echo (!empty($ak)) ? 'accesskey="' . $ak . '" ' : '' ?>/> <input type="submit" class="button" name="addNew" value="<?php echo htmlspecialchars(_("Add")) ?>" /></td></tr>
<?php if ($registry->hasMethod('contacts/search')): ?>
 <tr><td>&nbsp;</td>
 <td align="right" class="item<?php echo ($i++ % 2) ?>" colspan="2">
  <input type="button" class="button" name="contacts" value="<?php echo htmlspecialchars(_("Add people from my Address Book")) ?>" onclick="window.open('<?php echo Horde::applicationUrl('contacts.php') ?>', 'contacts', 'toolbar=no,location=no,status=yes,scrollbars=yes,resizable=yes,width=650,height=350,left=100,top=100'); return false;" />
 </td>
 </tr>
<?php endif; ?>
<tr>
<td>&nbsp;</td>
<td align="right" class="item<?php echo ($i++ % 2) ?>">
 <input type="button" name="loadattlist" class="button" value="<?php echo _("Load Attendee List") ?>" onclick="<?php echo $savedattlist_url ?>" />
</td>
<td align="left" class="item<?php echo ($i % 2) ?>">
 <input type="button" name="saveattlist" class="button" value="<?php echo _("Save Attendee List") ?>" onclick="<?php echo "javascript:performAction(" . KRONOLITH_ACTIONID_SAVE . ", '')"?>" />
</td>
</tr>
</table>

<?php if (count($attendees) >= 1): ?>
<br /><br />

<table border="0" width="500" cellspacing="0" cellpadding="2">
<tr>
  <td class="item" style="padding-left:10px; padding-right:10px; padding-top:10px">
    <?php echo $vfb_html ?><br/>
  </td>
</tr>
<?php if (!empty($legend_html)): ?>
<tr>
  <td style="padding-left:10px; padding-right:10px; padding-top:10px">
    <?php echo $legend_html ?><br/>
  </td>
</tr>
<?php endif; ?>
</table>

<br /><br />

<table border="0" width="500" cellspacing="0" cellpadding="2"><tr>
<td align="left">
<?php if ($view != 'day'): ?>
<input type="button" class="button" value="<?php echo htmlspecialchars(_("Day View")) ?>" onclick="switchView('day')" />
<?php endif; if ($view != 'workweek'): ?>
<input type="button" class="button" value="<?php echo htmlspecialchars(_("Work Week View")) ?>" onclick="switchView('workweek')" />
<?php endif; if ($view != 'week'): ?>
<input type="button" class="button" value="<?php echo htmlspecialchars(_("Week View")) ?>" onclick="switchView('week')" />
<?php endif; if ($view != 'month'): ?>
<input type="button" class="button" value="<?php echo htmlspecialchars(_("Month View")) ?>" onclick="switchView('month')" />
<?php endif; ?>
</td>
<?php if ($allow_dismiss): ?>
<td align="right"><input type="button" class="button" value="<?php echo htmlspecialchars(_("Dismiss")) ?>" onclick="performAction(<?php echo KRONOLITH_ACTIONID_DISMISS ?>, '')" /></td>
<?php endif; ?>
</tr></table>
<?php endif; ?>

</div>

</form>
