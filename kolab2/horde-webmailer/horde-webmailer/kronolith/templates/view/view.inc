<table cellspacing="0" width="100%" class="striped">

<?php if (!$private): ?>
<!-- category -->
<tr>
 <td class="rightAlign"><strong><?php echo _("Category") ?>&nbsp;&nbsp;</strong></td>
 <td>
  <?php echo @htmlspecialchars($category ? $category : _("Unfiled"), ENT_COMPAT, NLS::getCharset()) ?>
 </td>
</tr>

<!-- location -->
<tr>
 <td class="rightAlign"><strong><?php echo _("Location") ?>&nbsp;&nbsp;</strong></td>
 <td><?php echo empty($location) ? '&nbsp;' : Text_Filter::filter($location, 'text2html', array('parselevel' => TEXT_HTML_MICRO, 'class' => 'text')) ?> </td>
</tr>
<?php endif; ?>

<!-- status -->
<tr>
 <td width="10%" class="rightAlign"><strong><?php echo _("Status") ?>&nbsp;&nbsp;</strong></td>
 <td width="90%"><?php echo empty($status) ? '&nbsp;' : htmlspecialchars($status) ?> </td>
</tr>

<?php if (!empty($owner)): ?>
<!-- owner -->
<tr>
 <td class="rightAlign"><strong><?php echo _("Owner") ?>&nbsp;&nbsp;</strong></td>
 <td><?php echo @htmlspecialchars($owner, ENT_COMPAT, NLS::getCharset()) ?> </td>
</tr>
<?php endif; ?>

<!-- start date -->
<tr>
 <td class="rightAlign"><strong><?php echo _("Start On") ?>&nbsp;&nbsp;</strong></td>
 <td><?php echo strftime($prefs->getValue('date_format'), $this->event->start->timestamp()) . ' '; echo $this->event->isAllDay() ? _("All day event") : date($prefs->getValue('twentyFour') ? 'G:i' : 'g:i a', $this->event->start->timestamp()) ?></td>
</tr>

<?php if (!$this->event->isAllDay()): ?>
<!-- end date -->
<tr>
 <td class="rightAlign"><strong><?php echo _("End On") ?>&nbsp;&nbsp;</strong></td>
 <td><?php echo strftime($prefs->getValue('date_format'), $this->event->end->timestamp()) . date($prefs->getValue('twentyFour') ? ' G:i' : ' g:i a', $this->event->end->timestamp()) ?></td>
</tr>
<?php endif; ?>

<!-- alarm -->
<tr>
 <td class="rightAlign"><strong><?php echo _("Alarm") ?>&nbsp;&nbsp;</strong></td>
 <td>
<?php
if ($this->event->isInitialized() && $this->event->alarm > 0):
    if ($this->event->alarm % 10080 == 0) {
        $alarm_value = $this->event->alarm / 10080;
        $alarm_unit = _("Week(s)");
    } elseif ($this->event->alarm % 1440 == 0) {
        $alarm_value = $this->event->alarm / 1440;
        $alarm_unit = _("Day(s)");
    } elseif ($this->event->alarm % 60 == 0) {
        $alarm_value = $this->event->alarm / 60;
        $alarm_unit = _("Hour(s)");
    } else {
        $alarm_value = $this->event->alarm;
        $alarm_unit = _("Minute(s)");
    }
?>
  <?php echo $alarm_value . ' ' . $alarm_unit ?>
<?php else: ?>
  <?php echo _("No alarm") ?>
<?php endif; ?>
 </td>
</tr>

<?php if (isset($created)): ?>
<tr>
  <td class="nowrap rightAlign"><strong><?php echo _("Created") ?></strong>&nbsp;&nbsp;</td>
  <td class="nowrap"><?php echo strftime($prefs->getValue('date_format'), $created) . ' ' . date($prefs->getValue('twentyFour') ? 'G:i' : 'g:i a', $created) . ' ' . @htmlspecialchars($createdby, ENT_COMPAT, NLS::getCharset()) ?></td>
</tr>
<?php endif; ?>

<?php if (isset($modified)): ?>
<tr>
  <td class="nowrap rightAlign"><strong><?php echo _("Last Modified") ?></strong>&nbsp;&nbsp;</td>
  <td class="nowrap"><?php echo strftime($prefs->getValue('date_format'), $modified) . ' ' . date($prefs->getValue('twentyFour') ? 'G:i' : 'g:i a', $modified) . ' ' . @htmlspecialchars($modifiedby, ENT_COMPAT, NLS::getCharset()) ?></td>
</tr>
<?php endif; ?>


<?php if ($this->event->recurs()): ?>
<!-- recurrence -->
<tr>
 <td colspan="2" class="control"><strong><?php echo _("Recurrence") ?></strong></td>
</tr>
<tr>
 <td class="rightAlign" valign="top"><strong><?php echo _("Pattern") ?>&nbsp;&nbsp;</strong></td>
 <td valign="top">
<?php if ($this->event->recurrence->hasRecurType(HORDE_DATE_RECUR_DAILY)): ?>
   <?php echo _("Daily: Recurs every") . ' ' . $this->event->recurrence->getRecurInterval() . ' ' . _("day(s)") ?>
<?php elseif ($this->event->recurrence->hasRecurType(HORDE_DATE_RECUR_WEEKLY)):
    $weekdays = array();
    if ($this->event->recurrence->recurOnDay(HORDE_DATE_MASK_MONDAY))    $weekdays[] = _("Monday");
    if ($this->event->recurrence->recurOnDay(HORDE_DATE_MASK_TUESDAY))   $weekdays[] = _("Tuesday");
    if ($this->event->recurrence->recurOnDay(HORDE_DATE_MASK_WEDNESDAY)) $weekdays[] = _("Wednesday");
    if ($this->event->recurrence->recurOnDay(HORDE_DATE_MASK_THURSDAY))  $weekdays[] = _("Thursday");
    if ($this->event->recurrence->recurOnDay(HORDE_DATE_MASK_FRIDAY))    $weekdays[] = _("Friday");
    if ($this->event->recurrence->recurOnDay(HORDE_DATE_MASK_SATURDAY))  $weekdays[] = _("Saturday");
    if ($this->event->recurrence->recurOnDay(HORDE_DATE_MASK_SUNDAY))    $weekdays[] = _("Sunday");
    echo _("Weekly: Recurs every") . ' ' . $this->event->recurrence->getRecurInterval() . ' ' . _("week(s) on:") . ' ' . implode(', ', $weekdays) ?>
<?php elseif ($this->event->recurrence->hasRecurType(HORDE_DATE_RECUR_MONTHLY_DATE)): ?>
   <?php echo _("Monthly: Recurs every") . ' ' . $this->event->recurrence->getRecurInterval() . ' ' . _("month(s)") . ' ' . _("on the same date") ?>
<?php elseif ($this->event->recurrence->hasRecurType(HORDE_DATE_RECUR_MONTHLY_WEEKDAY)): ?>
   <?php echo _("Monthly: Recurs every") . ' ' . $this->event->recurrence->getRecurInterval() . ' ' . _("month(s)") . ' ' . _("on the same weekday") ?>
<?php elseif ($this->event->recurrence->hasRecurType(HORDE_DATE_RECUR_YEARLY_DATE)): ?>
   <?php echo _("Yearly: Recurs every") . ' ' . $this->event->recurrence->getRecurInterval() . ' ' . _("year(s) on the same date") ?>
<?php elseif ($this->event->recurrence->hasRecurType(HORDE_DATE_RECUR_YEARLY_DAY)): ?>
   <?php echo _("Yearly: Recurs every") . ' ' . $this->event->recurrence->getRecurInterval() . ' ' . _("year(s) on the same day of the year") ?>
<?php elseif ($this->event->recurrence->hasRecurType(HORDE_DATE_RECUR_YEARLY_WEEKDAY)): ?>
   <?php echo _("Yearly: Recurs every") . ' ' . $this->event->recurrence->getRecurInterval() . ' ' . _("year(s) on the same weekday and month of the year") ?>
<?php endif; ?>
 </td>
</tr>

<!-- recur end date -->
<tr>
 <td class="rightAlign"><strong><?php echo _("Recur Until") ?>&nbsp;&nbsp;</strong></td>
 <td><?php echo $this->event->recurrence->hasRecurEnd() ? strftime($prefs->getValue('date_format'), $this->event->recurrence->recurEnd->timestamp()) . date($prefs->getValue('twentyFour') ? ' G:i' : ' g:i a', $this->event->recurrence->recurEnd->timestamp()) : ($this->event->recurrence->getRecurCount() ? sprintf(_("%d times"), $this->event->recurrence->getRecurCount()) : _("No end date")) ?></td>
</tr>

<?php if ($this->event->recurrence->getExceptions()): ?>
<!-- exceptions -->
<tr>
 <td class="rightAlign"><strong><?php echo _("Exceptions") ?>&nbsp;&nbsp;</strong></td>
 <td><?php echo $this->event->exceptionsList(); ?></td>
</tr>
<?php endif; endif; ?>

<?php if ($conf['metadata']['keywords'] && count($keyword_list)): ?>
<!-- keywords -->
<tr>
 <td colspan="2" class="control"><strong><?php echo _("Keywords") ?></strong></td>
</tr>
<?php foreach ($keyword_list as $cat => $list): ?>
<tr>
 <td class="rightAlign" valign="top"><?php echo htmlspecialchars($cat) ?></td>
 <td>
<?php foreach ($list as $entry): ?>
  <?php echo htmlspecialchars($entry) ?><br />
<?php endforeach; ?>
 </td>
</tr>
<?php endforeach; ?>
<?php endif; ?>

<?php if (!$private && !empty($description)): ?>
<!-- description -->
<tr>
 <td colspan="2" class="control"><strong><?php echo _("Description") ?></strong></td>
</tr>
<tr>
 <td colspan="2" class="description"><?php require_once 'Horde/Text/Filter.php'; echo Text_Filter::filter($description, 'text2html', array('parselevel' => TEXT_HTML_MICRO, 'class' => 'text')) ?></td>
</tr>
<?php endif; ?>

</table>

<?php if (!empty($attendees)): ?>
<table cellspacing="0">
<!-- attendees -->
 <tr>
  <td colspan="3" class="control"><strong><?php echo _("Attendees") ?></strong></td>
 </tr>
 <tr class="item leftAlign">
  <th width="50%"><?php echo _("Attendee") ?></th>
  <th width="25%"><?php echo _("Attendance") ?></th>
  <th width="25%"><?php echo _("Response") ?></th>
 </tr>
 <?php $link_emails = $GLOBALS['registry']->hasMethod('mail/compose'); foreach ($attendees as $email => $status): $full = empty($status['name']) ? $email : MIME::trimEmailAddress($status['name'] . (strpos($email, '@') === false ? '' : ' <' . $email . '>')) ?>
 <tr>
  <td class="nowrap"><?php echo ($link_emails && strpos($email, '@') !== false) ? (Horde::link($GLOBALS['registry']->call('mail/compose', array(array('to' => $full))), sprintf(_("Send an email to %s"), empty($status['name']) ? $email : $status['name'])) . htmlspecialchars($full) . '</a>') : htmlspecialchars($full) ?></td>
  <td><?php echo Kronolith::partToString($status['attendance']) ?></td>
  <td><?php echo Kronolith::responseToString($status['response']) ?></td>
 </tr>
 <?php endforeach; ?>
</table>
<?php endif; ?>
