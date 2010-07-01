<?php $showCalSelect = (!$GLOBALS['prefs']->isLocked('default_share') && count($calendars) > 1); ?>
<form action="<?php echo ($event->isInitialized() && !$event->isRemote() ? 'edit.php' : 'add.php') ?>" method="post" name="eventform" id="eventform">
<?php Util::pformInput() ?>
<input type="hidden" name="year" value="<?php if (isset($year)) echo htmlspecialchars($year) ?>" />
<input type="hidden" name="month" value="<?php if (isset($month)) echo htmlspecialchars($month) ?>" />
<input type="hidden" name="mday" value="<?php if (isset($day)) echo htmlspecialchars($day) ?>" />
<input type="hidden" name="timestamp" value="<?php if (isset($timestamp)) echo htmlspecialchars($timestamp) ?>" />
<input type="hidden" name="new_category" value="" />
<?php if (isset($url)): ?>
<input type="hidden" name="url" value="<?php echo htmlspecialchars($url) ?>" />
<?php endif; ?>
<?php if ($event->isInitialized() && !$event->isRemote()): ?>
<input type="hidden" name="eventID" value="<?php echo htmlspecialchars($event->getId()) ?>" />
<input type="hidden" name="existingcalendar" value="<?php echo htmlspecialchars($event->getCalendar()) ?>" />
<?php endif; ?>
<?php if (!$showCalSelect): ?>
<input type="hidden" name="targetcalendar" value="<?php echo htmlspecialchars($calendar_id) ?>" />
<?php endif; ?>

<?php if (!$event->isInitialized()): ?>
<!-- header -->
<h1 class="header">
 <?php echo _("Add Event") ?>
</h1>
<?php endif; ?>

<table class="striped" cellspacing="0">
<?php if ($event->recurs() &&
          (!empty($conf['hooks']['permsdenied']) ||
           Kronolith::hasPermission('max_events') === true ||
           Kronolith::hasPermission('max_events') > Kronolith::countEvents())): ?>
<!-- recurrence editing -->
<tr>
 <td></td>
 <td colspan="4" class="warning">
  <?php echo _("This is a recurring event. Edit the current event only, this occurrence<br />and all future occurences, all occurences, or save this event as new?") ?><br /><br />
  <input type="radio" name="edit_recur" value="current" id="edit_current" onclick="setStartDate($F('recur_ex'))" /> <?php echo Horde::label('edit_current', _("Current")) ?>
  <input type="radio" name="edit_recur" value="future" id="edit_future" onclick="setStartDate($F('recur_ex'))" /> <?php echo Horde::label('edit_future', _("Future")) ?>
  <input type="radio" name="edit_recur" value="all" id="edit_all" checked="checked" /> <?php echo Horde::label('edit_all', _("All")) ?>
  <input type="radio" name="edit_recur" value="copy" id="edit_copy" /> <?php echo Horde::label('edit_copy', _("Save As New")) ?>
  <input type="hidden" name="recur_ex" id="recur_ex" value="<?php echo Util::getFormData('timestamp') ?>" />
 </td>
</tr>
<?php endif; ?>

<!-- buttons -->
<tr>
 <td></td>
 <td colspan="4">
  <?php echo implode("\n", $buttons) ?>
  <?php echo Horde::link(htmlspecialchars($cancelurl), '', 'button') . _("Cancel") . '</a>' ?>
  <input type="button" name="resetButton" class="button" value="<?php echo _("Reset to Defaults") ?>" onclick="document.eventform.reset(); updateWday('start_wday'); updateWday('end_wday');" />
 </td>
</tr>

<!-- title -->
<tr>
 <td class="rightAlign"><strong><?php echo Horde::label('title', _("Tit_le")) ?></strong></td>
 <td colspan="4">
  <input type="text" name="title" id="title" value="<?php echo htmlspecialchars($event->getTitle()) ?>" size="40" maxlength="255" />
 </td>
</tr>

<!-- calendar -->
<?php if ($showCalSelect): ?>
<tr>
 <td class="rightAlign"><strong><?php echo Horde::label('targetcalendar', _("Cal_endar")) ?></strong></td>
 <td colspan="4">
    <select id="targetcalendar" name="targetcalendar">
    <?php
    $creator = $event->getCreatorId();
    foreach ($calendars as $id => $cal) {
        $delegates = array();
        if ($cal->hasPermission(Auth::getAuth(), PERMS_EDIT, $creator)) {
            $delegates[$id] = htmlspecialchars($cal->get('name'));
        } else {
            $delegates[$id . ':' . $cal->get('owner')] = htmlspecialchars($cal->get('name'). ' (' . sprintf(_("as %s"), Kronolith::getUserName($cal->get('owner'))) . ')');
        }
        foreach ($delegates as $delegate_id => $cal_name) {
            $sel = ($delegate_id == $calendar_id) ? ' selected="selected"' : '';
            printf('<option value="%s"%s>%s</option>',
                   htmlspecialchars($delegate_id), $sel, $cal_name) . "\n";
        }
    } ?>
    </select>

 </td>
</tr>
<?php endif; ?>

<!-- category -->
<tr>
 <td class="rightAlign">
    <strong><?php echo Horde::label('category', _("Categor_y")) ?></strong>
 </td>
 <td colspan="4"><?php echo $GLOBALS['cManager']->getSelect('category', $event->getCategory()) ?></td>
</tr>

<!-- location -->
<tr>
 <td class="rightAlign"><strong><?php echo Horde::label('location', _("Lo_cation")) ?></strong></td>
 <td colspan="4">
  <input type="text" name="location" id="location" value="<?php echo htmlspecialchars($event->getLocation()) ?>" size="40" maxlength="255" />
 </td>
</tr>

<!-- status -->
<tr>
 <td class="rightAlign">
    <strong><?php echo Horde::label('status', _("Stat_us")) ?></strong>
 </td>
 <td colspan="4">
  <?php echo Kronolith::buildStatusWidget('status', $event->getStatus()) ?>
 </td>
</tr>

<!-- private -->
<tr>
 <td class="rightAlign">
    <strong><?php echo Horde::label('private', _("Private?")) ?></strong>
 </td>
 <td colspan="4">
  <input type="checkbox" class="checkbox" id="private" name="private"<?php if ($event->isPrivate()) echo ' checked="checked"' ?> />
 </td>
</tr>

<?php require KRONOLITH_TEMPLATES . '/edit/edit_timespan.inc' ?>

<!-- alarm -->
<tr>
 <td class="rightAlign" valign="top">
    <strong><?php $ak = Horde::getAccessKey(_("_Alarm")); echo Horde::highlightAccessKey(_("_Alarm"), $ak) ?></strong>
 </td>
 <td valign="top">
  <?php
  if ($event->alarm) {
      $alarm_set = true;
      if ($event->alarm % 10080 == 0) {
          $alarm_value = $event->alarm / 10080;
          $alarm_unit = 'week';
      } elseif ($event->alarm % 1440 == 0) {
          $alarm_value = $event->alarm / 1440;
          $alarm_unit = 'day';
      } elseif ($event->alarm % 60 == 0) {
          $alarm_value = $event->alarm / 60;
          $alarm_unit = 'hour';
      } else {
          $alarm_value = $event->alarm;
          $alarm_unit = 'min';
      }
  } else {
      $alarm_value = 15;
      $alarm_unit = 'min';
      $alarm_set = false;
  }
  ?>
  <input id="noalarm" name="alarm" type="radio" class="checkbox" value="0"<?php if (!$alarm_set) echo ' checked="checked"' ?> /><br />
  <input id="yesalarm" name="alarm" type="radio" class="checkbox" value="1"<?php if ($alarm_set) echo ' checked="checked"' ?> />
  <label for="yesalarm" class="hidden"><?php echo _("Alarm enabled") ?></label>
 </td>
 <td>&nbsp;</td>
 <td valign="top" colspan="2">
  <label for="noalarm" accesskey="<?php echo $ak ?>"> <?php echo _("No alarm") ?></label><br />
  <label for="alarm_value" class="hidden"><?php echo _("Alarm Value") ?></label>
  <input type="text" size="2" id="alarm_value" name="alarm_value" value="<?php echo $alarm_value ?>" onchange="document.eventform.alarm[1].checked=true" />&nbsp;
  <label for="alarm_unit" class="hidden"><?php echo _("Alarm Unit") ?></label>
  <select id="alarm_unit" name="alarm_unit" onchange="document.eventform.alarm[1].checked=true">
   <option value="1"<?php echo ($alarm_unit == 'min') ? ' selected="selected"' : '' ?>><?php echo _("Minute(s)") ?></option>
   <option value="60"<?php echo ($alarm_unit == 'hour') ? ' selected="selected"' : '' ?>><?php echo _("Hour(s)") ?></option>
   <option value="1440"<?php echo ($alarm_unit == 'day') ? ' selected="selected"' : '' ?>><?php echo _("Day(s)") ?></option>
   <option value="10080"<?php echo ($alarm_unit == 'week') ? ' selected="selected"' : '' ?>><?php echo _("Week(s)") ?></option>
  </select>
  <?php echo _("before the event starts") ?>
 </td>
</tr>

<!-- description -->
<tr>
 <td colspan="5" class="control toggle" onclick="toggleSection('description')">
  <?php echo Horde::img('tree/blank.png', '', array('id' => 'toggle_description'), $GLOBALS['registry']->getImageDir('horde')) . ' <strong>' . Horde::label('description', _("Descri_ption")) ?></strong>
  <span class="extra" id="extra_description"><?php echo htmlspecialchars(substr(str_replace(array("\r", "\n"), '  ', $event->getDescription()), 0, 80)) ?></span>
</td>
</tr>
<tr id="section_description">
 <td colspan="5">
  <textarea id="description" name="description" rows="4"><?php echo htmlspecialchars($event->getDescription()) ?></textarea>
 </td>
</tr>

<!-- attendees -->
<tr>
 <td colspan="5" class="control toggle" onclick="toggleSection('attendees')">
  <?php echo Horde::img('tree/blank.png', '', array('id' => 'toggle_attendees'), $GLOBALS['registry']->getImageDir('horde')) . ' <strong>' . _("Attendees") ?></strong>
  <span class="extra"><?php echo htmlspecialchars(Kronolith::attendeeList()) ?></span>
 </td>
</tr>

<tbody id="section_attendees">
<tr>
 <td></td>
 <td colspan="4">
  <?php echo Horde::link(Horde::applicationUrl('attendees.php'), '', 'button', '_blank', 'date = $H({ year: $F(\'start_year\'), month: $F(\'start_month\'), mday: $F(\'start_day\') }); this.href += (this.href.indexOf(\'?\') == -1 ? \'?\' : \'&\') + date.toQueryString(); return !popup(this.href);') . _("Edit Attendees") . '</a>' ?>
 </td>
</tr>
</tbody>

<!-- recurrence -->
<tr>
 <td colspan="5" class="control toggle" onclick="toggleSection('recurrence')">
  <?php echo Horde::img('tree/blank.png', '', array('id' => 'toggle_recurrence'), $GLOBALS['registry']->getImageDir('horde')) . ' <strong>' . _("Recurrence") ?></strong>
  <span class="extra" id="extra_recurrence"><?php echo $event->getRecurName(); if ($event->recurs()) echo $event->recurrence->hasRecurEnd() ? sprintf(_(" until %s"), strftime($GLOBALS['prefs']->getValue('date_format'), $event->recurrence->recurEnd->timestamp())) : ($event->recurrence->getRecurCount() ? sprintf(_(", %d times"), $event->recurrence->getRecurCount()) : _(" without end")) ?></span>
 </td>
</tr>
<tbody id="section_recurrence">
<tr>
 <td class="rightAlign" valign="top"><strong><?php echo Horde::label('recurnone', _("Pattern")) ?></strong></td>
 <td valign="top" colspan="4">
  <table cellspacing="0" width="100%">
   <tr>
    <td class="nowrap">
     <input id="recurnone" type="radio" class="checkbox" name="recur" onclick="clearFields(0);" value="<?php echo HORDE_DATE_RECUR_NONE ?>"<?php if (!$event->recurs()) echo ' checked="checked"' ?> /><label for="recurnone"> <?php echo _("No recurrence") ?></label>
    </td>
   </tr>
   <tr>
    <td class="nowrap">
     <input id="recurdaily" type="radio" class="checkbox" name="recur" onclick="setInterval('recur_daily_interval');" value="<?php echo HORDE_DATE_RECUR_DAILY ?>"<?php if ($event->recurs() && $event->recurrence->hasRecurType(HORDE_DATE_RECUR_DAILY)) echo ' checked="checked"' ?> /><label for="recurdaily"> <?php echo _("Daily: Recurs every") ?>&nbsp;</label>
     <input type="text" id="recur_daily_interval" name="recur_daily_interval" size="2" onkeypress="setRecur(1);" onchange="setRecur(1);" value="<?php echo $event->recurs() && $event->recurrence->hasRecurType(HORDE_DATE_RECUR_DAILY) ? $event->recurrence->getRecurInterval() : '' ?>" />&nbsp;<?php echo Horde::label('recur_daily_interval', _("day(s)")) ?>
    </td>
   </tr>
   <tr>
    <td class="nowrap">
     <input id="recurweekly" type="radio" class="checkbox" name="recur" onclick="setInterval('recur_weekly_interval');" value="<?php echo HORDE_DATE_RECUR_WEEKLY ?>"<?php if ($event->recurs() && $event->recurrence->hasRecurType(HORDE_DATE_RECUR_WEEKLY)) echo ' checked="checked"' ?> /><label for="recurweekly"> <?php echo _("Weekly: Recurs every") ?>&nbsp;</label>
     <input type="text" id="recur_weekly_interval" name="recur_weekly_interval" size="2" onkeypress="setRecur(2);" onchange="setRecur(2);" value="<?php echo $event->recurs() && $event->recurrence->hasRecurType(HORDE_DATE_RECUR_WEEKLY) ? $event->recurrence->getRecurInterval() : '' ?>" />&nbsp;
     <?php echo Horde::label('recur_weekly_interval', _("week(s) on:")) ?><br />
     <label for="mo"><?php echo _("Mo") ?></label><input id="mo" type="checkbox" class="checkbox" name="weekly[]" onclick="setInterval('recur_weekly_interval');setRecur(2);" value="<?php echo HORDE_DATE_MASK_MONDAY ?>"<?php if ($event->recurs() && $event->recurrence->recurOnDay(HORDE_DATE_MASK_MONDAY)) echo ' checked="checked"' ?> />&nbsp;
     <label for="tu"><?php echo _("Tu") ?></label><input id="tu" type="checkbox" class="checkbox" name="weekly[]" onclick="setInterval('recur_weekly_interval');setRecur(2);" value="<?php echo HORDE_DATE_MASK_TUESDAY ?>"<?php if ($event->recurs() && $event->recurrence->recurOnDay(HORDE_DATE_MASK_TUESDAY)) echo ' checked="checked"' ?> />&nbsp;
     <label for="we"><?php echo _("We") ?></label><input id="we" type="checkbox" class="checkbox" name="weekly[]" onclick="setInterval('recur_weekly_interval');setRecur(2);" value="<?php echo HORDE_DATE_MASK_WEDNESDAY ?>"<?php if ($event->recurs() && $event->recurrence->recurOnDay(HORDE_DATE_MASK_WEDNESDAY)) echo ' checked="checked"' ?> />&nbsp;
     <label for="th"><?php echo _("Th") ?></label><input id="th" type="checkbox" class="checkbox" name="weekly[]" onclick="setInterval('recur_weekly_interval');setRecur(2);" value="<?php echo HORDE_DATE_MASK_THURSDAY ?>"<?php if ($event->recurs() && $event->recurrence->recurOnDay(HORDE_DATE_MASK_THURSDAY)) echo ' checked="checked"' ?> />&nbsp;
     <label for="fr"><?php echo _("Fr") ?></label><input id="fr" type="checkbox" class="checkbox" name="weekly[]" onclick="setInterval('recur_weekly_interval');setRecur(2);" value="<?php echo HORDE_DATE_MASK_FRIDAY ?>"<?php if ($event->recurs() && $event->recurrence->recurOnDay(HORDE_DATE_MASK_FRIDAY)) echo ' checked="checked"' ?> />&nbsp;
     <label for="sa"><?php echo _("Sa") ?></label><input id="sa" type="checkbox" class="checkbox" name="weekly[]" onclick="setInterval('recur_weekly_interval');setRecur(2);" value="<?php echo HORDE_DATE_MASK_SATURDAY ?>"<?php if ($event->recurs() && $event->recurrence->recurOnDay(HORDE_DATE_MASK_SATURDAY)) echo ' checked="checked"' ?> />&nbsp;
     <label for="su"><?php echo _("Su") ?></label><input id="su" type="checkbox" class="checkbox" name="weekly[]" onclick="setInterval('recur_weekly_interval');setRecur(2);" value="<?php echo HORDE_DATE_MASK_SUNDAY ?>"<?php if ($event->recurs() && $event->recurrence->recurOnDay(HORDE_DATE_MASK_SUNDAY)) echo ' checked="checked"' ?> />&nbsp;
    </td>
   </tr>
   <tr>
    <td class="nowrap">
     <input id="recurmonthday" type="radio" class="checkbox" name="recur" onclick="setInterval('recur_day_of_month_interval');" value="<?php echo HORDE_DATE_RECUR_MONTHLY_DATE ?>"<?php if ($event->recurs() && $event->recurrence->hasRecurType(HORDE_DATE_RECUR_MONTHLY_DATE)) echo ' checked="checked"' ?> /><label for="recurmonthday"> <?php echo _("Monthly: Recurs every") ?>&nbsp;</label>
     <input type="text" id="recur_day_of_month_interval" name="recur_day_of_month_interval" size="2" onkeypress="setRecur(3);" onchange="setRecur(3);" value="<?php echo $event->recurs() && $event->recurrence->hasRecurType(HORDE_DATE_RECUR_MONTHLY_DATE) ? $event->recurrence->getRecurInterval() : '' ?>" />&nbsp;<?php echo Horde::label('recur_day_of_month_interval', _("month(s)") . ' ' . _("on the same date")) ?>
    </td>
   </tr>
   <tr>
    <td class="nowrap">
     <input id="recurmonthweek" type="radio" class="checkbox" name="recur" onclick="setInterval('recur_week_of_month_interval');" value="<?php echo HORDE_DATE_RECUR_MONTHLY_WEEKDAY ?>"<?php if ($event->recurs() && $event->recurrence->hasRecurType(HORDE_DATE_RECUR_MONTHLY_WEEKDAY)) echo ' checked="checked"' ?> /><label for="recurmonthweek"> <?php echo _("Monthly: Recurs every") ?>&nbsp;</label>
     <input type="text" id="recur_week_of_month_interval" name="recur_week_of_month_interval" size="2" onkeypress="setRecur(4);" onchange="setRecur(4);" value="<?php echo $event->recurs() && $event->recurrence->hasRecurType(HORDE_DATE_RECUR_MONTHLY_WEEKDAY) ? $event->recurrence->getRecurInterval() : '' ?>" />&nbsp;<?php echo Horde::label('recur_week_of_month_interval', _("month(s)") . ' ' . _("on the same weekday")) ?>
    </td>
   </tr>
   <tr>
    <td class="nowrap">
     <input id="recuryear" type="radio" class="checkbox" name="recur" onclick="setInterval('recur_yearly_interval');" value="<?php echo HORDE_DATE_RECUR_YEARLY_DATE ?>"<?php if ($event->recurs() && $event->recurrence->hasRecurType(HORDE_DATE_RECUR_YEARLY_DATE)) echo ' checked="checked"' ?> /><label for="recuryear"> <?php echo _("Yearly: Recurs every") ?>&nbsp;</label>
     <input type="text" id="recur_yearly_interval" name="recur_yearly_interval" size="2" onkeypress="setRecur(5);" onchange="setRecur(5);" value="<?php echo $event->recurs() && $event->recurrence->hasRecurType(HORDE_DATE_RECUR_YEARLY_DATE) ? $event->recurrence->getRecurInterval() : '' ?>" />&nbsp;<?php echo Horde::label('recur_yearly_interval', _("year(s) on the same date")) ?>
    </td>
   </tr>
   <tr>
    <td class="nowrap">
     <input id="recuryearday" type="radio" class="checkbox" name="recur" onclick="setInterval('recur_yearly_day_interval');" value="<?php echo HORDE_DATE_RECUR_YEARLY_DAY ?>"<?php if ($event->recurs() && $event->recurrence->hasRecurType(HORDE_DATE_RECUR_YEARLY_DAY)) echo ' checked="checked"' ?> /><label for="recuryearday"> <?php echo _("Yearly: Recurs every") ?>&nbsp;</label>
     <input type="text" id="recur_yearly_day_interval" name="recur_yearly_day_interval" size="2" onkeypress="setRecur(6);" onchange="setRecur(6);" value="<?php echo $event->recurs() && $event->recurrence->hasRecurType(HORDE_DATE_RECUR_YEARLY_DAY) ? $event->recurrence->getRecurInterval() : '' ?>" />&nbsp;<?php echo Horde::label('recur_yearly_day_interval', _("year(s) on the same day of the year")) ?>
    </td>
   </tr>
   <tr>
    <td class="nowrap">
     <input id="recuryearweekday" type="radio" class="checkbox" name="recur" onclick="setInterval('recur_yearly_weekday_interval');" value="<?php echo HORDE_DATE_RECUR_YEARLY_WEEKDAY ?>"<?php if ($event->recurs() && $event->recurrence->hasRecurType(HORDE_DATE_RECUR_YEARLY_WEEKDAY)) echo ' checked="checked"' ?> /><label for="recuryearweekday"> <?php echo _("Yearly: Recurs every") ?>&nbsp;</label>
     <input type="text" id="recur_yearly_weekday_interval" name="recur_yearly_weekday_interval" size="2" onkeypress="setRecur(7);" onchange="setRecur(7);" value="<?php echo $event->recurs() && $event->recurrence->hasRecurType(HORDE_DATE_RECUR_YEARLY_WEEKDAY) ? $event->recurrence->getRecurInterval() : '' ?>" />&nbsp;<?php echo Horde::label('recur_yearly_weekday_interval', _("year(s) on the same weekday and month of the year")) ?>
    </td>
   </tr>
  </table>
 </td>
</tr>

<!-- recur end date -->
<tr>
 <td class="rightAlign" valign="top">
  <strong><?php echo Horde::label('recur_enddate_type', _("Recur Until")) ?></strong>
 </td>
 <td colspan="3">
  <input id="recurnoend" type="radio" class="checkbox" name="recur_enddate_type" value="none"<?php echo ($event->recurs() && ($event->recurrence->hasRecurEnd() || $event->recurrence->hasRecurCount()) ? '' : ' checked="checked"') ?> /><label for="recurnoend"> <?php echo _("No end date") ?></label>
 </td>
<?php if ($GLOBALS['browser']->hasFeature('dom')): ?>
 <td>&nbsp;</td>
<?php endif; ?>
</tr>
<tr>
 <td>&nbsp;</td>
 <td colspan="3">
  <input type="radio" class="checkbox" id="recur_enddate_type" name="recur_enddate_type" value="date"<?php echo ($event->recurs() && $event->recurrence->hasRecurEnd() ? ' checked="checked"' : '') ?> />
  <?php echo $event->html('recur_enddate[year]') ?> - <?php echo $event->html('recur_enddate[month]') ?> - <?php echo $event->html('recur_enddate[day]') ?>
<?php if ($GLOBALS['browser']->hasFeature('dom')): ?>
  <span id="recur_end_wday"></span>
  <script type="text/javascript">updateWday('recur_end_wday');</script>
 </td>
 <td>
<?php
    Horde::addScriptFile('open_calendar.js', 'horde');
    echo Horde::link('#', _("Select a date"), '', '', 'openCalendar(\'recur_enddateimg\', \'recur_enddate\', \'' . addslashes($event->js('recur_enddate')) . '\'); return false;') . Horde::img('calendar.png', _("Set recurrence end date"), 'id="recur_enddateimg"', $GLOBALS['registry']->getImageDir('horde')) . '</a>';
endif;
?>
 </td>
</tr>
<tr>
 <td>&nbsp;</td>
 <td colspan="3">
  <input type="radio" class="checkbox" name="recur_enddate_type" value="count"<?php echo ($event->recurs() && $event->recurrence->getRecurCount() ? ' checked="checked"' : '') ?> />
  <input type="text" id="recur_count" name="recur_count" size="2" onkeypress="document.eventform.recur_enddate_type[2].checked = true;" onchange="document.eventform.recur_enddate_type[2].checked = true;" value="<?php if ($event->recurs() && $event->recurrence->getRecurCount()) echo $event->recurrence->getRecurCount() ?>" />
  <label for="recur_count"><?php echo _("recurrences") ?></label>
 </td>
<?php if ($GLOBALS['browser']->hasFeature('dom')): ?>
 <td>&nbsp;</td>
<?php endif; ?>
</tr>

<?php if ($event->recurs() && ($exceptions = $event->recurrence->getExceptions())): ?>
<!-- exceptions -->
<tr>
 <td class="rightAlign" valign="top">
  <strong><?php echo _("Exceptions") ?></strong>
 </td>
 <td colspan="4">
 <?php echo $event->exceptionsList(); foreach($exceptions as $exception): ?>
 <input type="hidden" name="exceptions[]" value="<?php echo $exception ?>" />
 <?php endforeach; ?>
 </td>
</tr>
<?php endif; ?>
</tbody>

<?php if ($GLOBALS['conf']['metadata']['keywords']): ?>
<!-- keywords -->
<tr>
 <td colspan="5" class="control toggle" onclick="toggleSection('keywords')">
  <?php echo Horde::img('tree/blank.png', '', array('id' => 'toggle_keywords'), $GLOBALS['registry']->getImageDir('horde')) . ' <strong>' . _("Keywords") ?></strong>
  <span class="extra" id="extra_keywords"><?php echo implode(', ', $event->getKeywords()) ?></span>
 </td>
</tr>
<tr id="section_keywords">
 <td></td>
 <td colspan="4">
  <table cellspacing="2">
   <?php include KRONOLITH_BASE . '/config/keywords.php'; $count = 0 ?>
   <?php foreach ($keywords as $cat => $list):
       if ($count % 3 == 0): ?>
   <tr>
   <?php endif; ?>
    <td valign="top">
     <strong><?php echo $cat ?></strong><br />
    <?php for ($k = 0; $k < count($list); ++$k): ?>
     <input type="checkbox" class="checkbox" id="keyword<?php echo htmlspecialchars($k) ?>" name="keywords[]" value="<?php echo htmlspecialchars($list[$k]) ?>"<?php if ($event->hasKeyword($list[$k])) echo ' checked="checked"' ?> />
     <?php echo Horde::label('keyword' . $k, htmlspecialchars($list[$k])) ?><br />
    <?php endfor; ?>
    </td>
   <?php if (($count % 3 == 2) || ($count == count($keywords) - 1)): ?>
   </tr>
   <?php endif; ++$count ?>
   <?php endforeach; ?>
  </table>
 </td>
</tr>
<?php endif; ?>

<!-- spacer -->
<tr>
 <td style="line-height:4px;">&nbsp;</td>
</tr>

<!-- invitations/updates and buttons -->
<tr>
 <td></td>
 <td colspan="4">
  <input id="sendupdates" type="checkbox" class="checkbox" name="sendupdates" checked="checked" />
  <label for="sendupdates"><?php echo $event->isInitialized() ? _("Send updates to all attendees?") : _("Send invitations to all attendees?") ?></label>
 </td>
</tr>
<tr>
 <td></td>
 <td colspan="4">
  <?php echo implode("\n", $buttons) ?>
  <?php echo Horde::link(htmlspecialchars($cancelurl), '', 'button') . _("Cancel") . '</a>' ?>
  <input type="button" name="resetButton" class="button" value="<?php echo _("Reset to Defaults") ?>" onclick="document.eventform.reset(); updateWday('start_wday'); updateWday('end_wday');" />
  </td>
 </tr>
</table>
</form>
<script type="text/javascript">
document.eventform.title.focus();
</script>
