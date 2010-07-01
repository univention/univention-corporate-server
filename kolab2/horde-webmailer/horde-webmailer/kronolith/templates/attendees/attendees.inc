<script type="text/javascript">
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

function switchDateView(view, timestamp)
{
    document.attendeesForm.view.value = view;
    document.attendeesForm.timestamp.value = timestamp;
    document.attendeesForm.submit();
    return false;
}
</script>

<form method="post" action="attendees.php" name="attendeesForm">
<?php Util::pformInput() ?>
<input type="hidden" name="actionID" value="add" />
<input type="hidden" name="actionValue" value="" />
<input type="hidden" name="view" value="<?php echo htmlspecialchars($view) ?>" />
<input type="hidden" name="timestamp" value="<?php echo htmlspecialchars($timestamp) ?>" />

<h1 class="header"><?php echo htmlspecialchars($title) ?></h1>

<table width="100%" cellspacing="0" class="linedRow">

<!-- attendee list header -->
<tr class="item nowrap leftAlign">
 <th width="2%">&nbsp;</th>
 <th width="48%"><?php echo htmlspecialchars(_("Attendee")) ?></th>
 <th width="25%"><?php echo htmlspecialchars(_("Attendance")) ?></th>
 <th width="25%"><?php echo htmlspecialchars(_("Response")) ?></th>
</tr>

<!-- attendees -->
<?php $i = 0; if (empty($attendees)): ?>
 <tr><td colspan="4"><em><?php echo _("No attendees") ?></em></td></tr>
<?php else: foreach ($attendees as $email => $status): ?>
 <tr>
  <td class="nowrap"><?php $name = strpos($email, '@') === false ? $status['name'] : $email; echo Horde::link('#', sprintf(_("Remove %s"), $name), '', '', "performAction('remove', decodeURIComponent('" . rawurlencode($email) . "')); return false;") . Horde::img('delete.png', '', null, $registry->getImageDir('horde')) . '</a> ' . Horde::link('#', sprintf(_("Edit %s"), $name), '', '', "performAction('edit', decodeURIComponent('" . rawurlencode($email) . "')); return false;") . Horde::img('edit.png', '', null, $registry->getImageDir('horde')) . '</a>' ?></td>
  <td><?php echo htmlspecialchars(empty($status['name']) ? $email : MIME::trimEmailAddress($status['name'] . (strpos($email, '@') === false ? '' : ' <' . $email . '>'))) ?></td>
  <td>
<label for="<?php echo "attendance_$i" ?>" class="hidden"><?php echo _("Attendance") ?></label>
   <select id="<?php echo "attendance_$i" ?>" name="<?php echo "attendance_$i" ?>" onchange="performAction('changeatt', document.attendeesForm.<?php echo "attendance_$i" ?>.value + ' ' + decodeURIComponent('<?php echo rawurlencode($email) ?>'));">
    <option value="<?php echo KRONOLITH_PART_REQUIRED ?>"<?php if ($status['attendance'] == KRONOLITH_PART_REQUIRED)  echo ' selected="selected"' ?>><?php echo Kronolith::partToString(KRONOLITH_PART_REQUIRED) ?></option>
    <option value="<?php echo KRONOLITH_PART_OPTIONAL ?>"<?php if ($status['attendance'] == KRONOLITH_PART_OPTIONAL)  echo ' selected="selected"' ?>><?php echo Kronolith::partToString(KRONOLITH_PART_OPTIONAL) ?></option>
    <option value="<?php echo KRONOLITH_PART_NONE ?>"<?php if ($status['attendance'] == KRONOLITH_PART_NONE)  echo ' selected="selected"' ?>><?php echo Kronolith::partToString(KRONOLITH_PART_NONE) ?></option>
   </select>
  </td>
  <td>
   <select name="<?php echo "response_$i" ?>" onchange="performAction('changeresp', document.attendeesForm.<?php echo "response_$i" ?>.value + ' ' + decodeURIComponent('<?php echo rawurlencode($email) ?>'));">
    <option value="<?php echo KRONOLITH_RESPONSE_ACCEPTED ?>"<?php if ($status['response'] == KRONOLITH_RESPONSE_ACCEPTED)  echo ' selected="selected"' ?>><?php echo Kronolith::responseToString(KRONOLITH_RESPONSE_ACCEPTED) ?></option>
    <option value="<?php echo KRONOLITH_RESPONSE_DECLINED ?>"<?php if ($status['response'] == KRONOLITH_RESPONSE_DECLINED)  echo ' selected="selected"' ?>><?php echo Kronolith::responseToString(KRONOLITH_RESPONSE_DECLINED) ?></option>
    <option value="<?php echo KRONOLITH_RESPONSE_TENTATIVE ?>"<?php if ($status['response'] == KRONOLITH_RESPONSE_TENTATIVE)  echo ' selected="selected"' ?>><?php echo Kronolith::responseToString(KRONOLITH_RESPONSE_TENTATIVE) ?></option>
    <option value="<?php echo KRONOLITH_RESPONSE_NONE ?>"<?php if ($status['response'] == KRONOLITH_RESPONSE_NONE)  echo ' selected="selected"' ?>><?php echo Kronolith::responsetoString(KRONOLITH_RESPONSE_NONE) ?></option>
   </select>
  </td>
 </tr>
 <?php $i++; ?>
<?php endforeach; ?>
<?php endif; ?>
</table>

<br />

<table width="100%" cellspacing="2" class="nowrap control">
 <tr>
  <td class="rightAlign">&nbsp;<strong><?php $label = empty($editAttendee) ? _("Add attendees") : _("Edit attendee"); echo Horde::highlightAccessKey($label, $ak = Horde::getAccessKey($label)) ?></strong></td>
  <td>
   <input type="text" id="newAttendees" name="newAttendees" autocomplete="off" size="40" <?php if (!empty($ak)) echo 'accesskey="' . $ak . '" '; if (!empty($editAttendee)) echo 'value="' . htmlspecialchars($editAttendee) . '" '; ?>/>
   <span id="newAttendees_loading_img" style="display:none;"><?php echo Horde::img('loading.gif', _("Loading...")) ?></span>
   <div id="newAttendees_results" class="autocomplete"></div>
  </td>
<?php if ($registry->hasMethod('contacts/search')): ?>
  <td align="center"><?php echo Horde::link('#', '', 'widget', null, 'window.open(\'' . Horde::applicationUrl('contacts.php') . '\', \'contacts\', \'toolbar=no,location=no,status=no,scrollbars=yes,resizable=yes,width=550,height=270,left=100,top=100\'); return false;') . Horde::img('addressbook_browse.png') . '<br />' . _("Address Book") . '</a>' ?></td>
  <td width="100%">&nbsp;</td>
<?php endif; ?>
 </tr>
</table>

<br />
<div>
 <input type="submit" class="button" name="addNew" value="<?php echo htmlspecialchars(_("Save Attendees")) ?>" />
 <input type="submit" class="button" name="addNewClose" value="<?php echo htmlspecialchars(_("Save and Finish")) ?>" />
 <input type="button" class="button" name="loadAttList" value="<?php echo htmlspecialchars(_("Load Attendee List")) ?>" onclick="<?php echo $savedattlist_url ?>" />
 <?php if (!empty($attendees)): ?><input type="button" class="button" name="saveAttList" value="<?php echo htmlspecialchars(_("Save Attendee List")) ?>" onclick="performAction('save', '');" /><?php endif; ?>
 <?php if (!empty($attendees)): ?><input type="submit" class="button" name="clearAll" value="<?php echo htmlspecialchars(_("Clear all attendees")) ?>" /><?php endif; ?>
</div>

<br />
<?php echo $tabs->render($view) . $vfb_html ?>
</form>
