<?php $i = 0 ?>
<table border="0" width="400" cellspacing="0" cellpadding="0" style="padding-left:10px;">

<!-- header -->
<tr>
 <td class="header"><b><?php echo htmlspecialchars($event->getTitle()) ?></b></td>
 <td class="header" align="right">
  <?php if (!$print_view): ?>
  <span class="smallheader"><?php echo implode(' | ', $mylinks) ?></span>
  <?php endif; ?>
 </td>
</tr>

<tr>
 <td colspan="2" class="headerbox"><table border="0" cellpadding="1" cellspacing="0" width="100%">

<!-- category -->
<tr class="item<?php echo ($i++ % 2) ?>">
 <td align="right"><b><?php echo _("Category") ?>&nbsp;&nbsp;</b></td>
 <td align="left">
  <?php echo htmlspecialchars($category ? $category : _("Unfiled")) ?>
 </td>
</tr>

<!-- location -->
<tr class="item<?php echo ($i++ % 2) ?>">
 <td align="right"><b><?php echo _("Location") ?>&nbsp;&nbsp;</b></td>
 <td align="left"><?php echo empty($location) ? '&nbsp;' : htmlspecialchars($location) ?> </td>
</tr>

<!-- status -->
<tr class="item<?php echo ($i++ % 2) ?>">
 <td align="right"><b><?php echo _("Status") ?>&nbsp;&nbsp;</b></td>
 <td align="left"><?php echo empty($status) ? '&nbsp;' : $status ?> </td>
</tr>

<?php if (!empty($owner)): ?>
<!-- owner -->
<tr class="item<?php echo ($i++ % 2) ?>">
 <td align="right"><b><?php echo _("Owner") ?>&nbsp;&nbsp;</b></td>
 <td align="left"><?php echo htmlspecialchars($owner) ?> </td>
</tr>
<?php endif; ?>

<!-- start date -->
<tr class="item<?php echo ($i++ % 2) ?>">
 <td align="right"><b><?php echo _("Start On") ?>&nbsp;&nbsp;</b></td>
 <td align="left"><?php echo strftime($prefs->getValue('date_format'), $event->getStartTimestamp()) . date($prefs->getValue('twentyFour') ? ' G:i' : ' g:i a', $event->getStartTimestamp()) ?></td>
</tr>

<!-- end date -->
<tr class="item<?php echo ($i++ % 2) ?>">
 <td align="right"><b><?php echo _("End On") ?>&nbsp;&nbsp;</b></td>
 <td align="left"><?php echo strftime($prefs->getValue('date_format'), $event->getEndTimestamp()) . date($prefs->getValue('twentyFour') ? ' G:i' : ' g:i a', $event->getEndTimestamp()) ?></td>
</tr>

<!-- alarm -->
<tr class="item<?php echo ($i++ % 2) ?>">
 <td align="right"><b><?php echo _("Alarm") ?>&nbsp;&nbsp;</b></td>
 <td>
<?php
if ($event->isInitialized() && $event->alarm > 0):
    if ($event->alarm % 10080 == 0) {
        $alarm_value = $event->alarm / 10080;
        $alarm_unit = _("Week(s)");
    } elseif ($event->alarm % 1440 == 0) {
        $alarm_value = $event->alarm / 1440;
        $alarm_unit = _("Day(s)");
    } elseif ($event->alarm % 60 == 0) {
        $alarm_value = $event->alarm / 60;
        $alarm_unit = _("Hour(s)");
    } else {
        $alarm_value = $event->alarm;
        $alarm_unit = _("Minute(s)");
    }
?>
  <?php echo $alarm_value . ' ' . $alarm_unit ?>
<?php else: ?>
  <?php echo _("None") ?>
<?php endif; ?>
 </td>
</tr>

<?php if (isset($created)): ?>
<tr class="item<?php echo ($i++ % 2) ?>">
  <td nowrap="nowrap" align="right"><b><?php echo _("Created") ?></b>&nbsp;&nbsp;</td>
  <td nowrap="nowrap"><?php echo strftime($prefs->getValue('date_format'), $created) . ' ' . date($prefs->getValue('twentyFour') ? 'G:i' : 'g:i a', $created) ?></td>
</tr>
<?php endif; ?>

<?php if (isset($modified)): ?>
<tr class="item<?php echo ($i++ % 2) ?>">
  <td nowrap="nowrap" align="right"><b><?php echo _("Last Modified") ?></b>&nbsp;&nbsp;</td>
  <td nowrap="nowrap"><?php echo strftime($prefs->getValue('date_format'), $modified) . ' ' . date($prefs->getValue('twentyFour') ? 'G:i' : 'g:i a', $modified) ?></td>
</tr>
<?php endif; ?>


<?php if (!empty($description)): ?>
<!-- description -->
<tr><td style="font-size:1px;">&nbsp;</td></tr>
<tr>
 <td align="left" colspan="2" class="header"><span class="smallheader"><b><?php echo _("Description") ?></b></span></td>
</tr>
<tr class="item<?php echo ($i++ % 2) ?>">
 <td colspan="2" align="left"><?php echo Text::toHtml($description, TEXT_HTML_MICRO, null, 'text') ?></td>
</tr>
<?php endif; ?>

<?php if (!$event->hasRecurType(KRONOLITH_RECUR_NONE)): ?>
<!-- recurrence -->
<tr><td style="font-size:1px;">&nbsp;</td></tr>
<tr>
 <td align="left" colspan="2" class="header"><span class="smallheader"><b><?php echo _("Recurrence") ?></b></span></td>
</tr>
<tr class="item<?php echo ($i++ % 2) ?>">
 <td align="right" valign="top"><b><?php echo _("Pattern") ?>&nbsp;&nbsp;</b></td>
 <td align="left" valign="top">
<?php if ($event->hasRecurType(KRONOLITH_RECUR_DAILY)): ?>
   <?php echo _("Daily: Recurs every") . ' ' . $event->getRecurInterval() . ' ' . _("day(s)") ?>
<?php
elseif ($event->hasRecurType(KRONOLITH_RECUR_WEEKLY)):
    $weekdays = array();
    if ($event->recurOnDay(KRONOLITH_MASK_MONDAY))    $weekdays[] = _("Monday");
    if ($event->recurOnDay(KRONOLITH_MASK_TUESDAY))   $weekdays[] = _("Tuesday");
    if ($event->recurOnDay(KRONOLITH_MASK_WEDNESDAY)) $weekdays[] = _("Wednesday");
    if ($event->recurOnDay(KRONOLITH_MASK_THURSDAY))  $weekdays[] = _("Thursday");
    if ($event->recurOnDay(KRONOLITH_MASK_FRIDAY))    $weekdays[] = _("Friday");
    if ($event->recurOnDay(KRONOLITH_MASK_SATURDAY))  $weekdays[] = _("Saturday");
    if ($event->recurOnDay(KRONOLITH_MASK_SUNDAY))    $weekdays[] = _("Sunday");
?>
   <?php echo _("Weekly: Recurs every") . ' ' . $event->getRecurInterval() . ' ' . _("week(s) on:") . ' ' . implode(', ', $weekdays) ?>
<?php elseif ($event->hasRecurType(KRONOLITH_RECUR_DAY_OF_MONTH)): ?>
   <?php echo _("Monthly: Recurs every") . ' ' . $event->getRecurInterval() . ' ' . _("month(s)") . ' ' . _("on the same date") ?>
<?php elseif ($event->hasRecurType(KRONOLITH_RECUR_WEEK_OF_MONTH)): ?>
   <?php echo _("Monthly: Recurs every") . ' ' . $event->getRecurInterval() . ' ' . _("month(s)") . ' ' . _("on the same weekday") ?>
<?php elseif ($event->hasRecurType(KRONOLITH_RECUR_YEARLY)): ?>
   <?php echo _("Yearly: Recurs every") . ' ' . $event->getRecurInterval() . ' ' . _("year(s)") ?>
<?php endif; ?>
 </td>
</tr>

<!-- recur end date -->
<tr class="item<?php echo ($i++ % 2) ?>">
 <td align="right"><b><?php echo _("Recur Until") ?>&nbsp;&nbsp;</b></td>
 <td align="left"><?php echo $event->hasRecurEnd() ? strftime($prefs->getValue('date_format'), $event->getRecurEndTimestamp()) . date($prefs->getValue('twentyFour') ? ' G:i' : ' g:i a', $event->getRecurEndTimestamp()) : _("No end date") ?></td>
</tr>
<?php endif; ?>

<?php if ($conf['metadata']['keywords'] && count($keyword_list)): ?>
<tr><td style="font-size:1px;">&nbsp;</td></tr>
<tr>
 <td colspan="2" class="header" align="left"><span class="smallheader"><b><?php echo _("Keywords") ?></b></span></td>
</tr>
<?php foreach ($keyword_list as $cat => $list): ?>
<tr class="item<?php echo ($i++ % 2) ?>">
 <td align="right" valign="top"><b><?php echo $cat ?>&nbsp;&nbsp;</b></td>
 <td align="left">
<?php foreach ($list as $entry): ?>
  <?php echo $entry ?><br />
<?php endforeach; ?>
 </td>
</tr>
<?php endforeach; ?>
<?php endif; ?>

<?php $span = 2; if (!empty($attendees)): $span = 3; ?>
</table>

<table border="0" width="400" cellspacing="0" cellpadding="2">
<!-- attendees -->
<?php $i = 0 ?>
<tr><td style="font-size:1px;">&nbsp;</td></tr>
<tr>
 <td align="left" colspan="3" class="header"><span class="smallheader"><b><?php echo _("Attendees") ?></b></span></td>
</tr>
 <tr class="item">
  <td width="50%"><b><?php echo _("Email Address") ?>&nbsp;&nbsp;</b></td>
  <td width="25%"><b><?php echo _("Attendance") ?>&nbsp;&nbsp;</b></td>
  <td width="25%"><b><?php echo _("Response") ?>&nbsp;&nbsp;</b></td>
 </tr>
 <?php foreach ($attendees as $email => $status): ?>
  <tr class="item<?php echo ($i++ % 2) ?>">
   <td><?php echo Horde::link($registry->call('mail/compose', array(array('to' => addslashes($email)))), sprintf(_("Send an email to %s"), $email)), $email . '</a>' ?></td>
   <td><?php echo Kronolith::partToString($status['attendance']) ?></td>
   <td><?php echo Kronolith::responseToString($status['response']) ?></td>
  </tr>
 <?php endforeach; ?>
</tr>
<?php endif; ?>

   </table>
  </td>
 </tr>
</table>
