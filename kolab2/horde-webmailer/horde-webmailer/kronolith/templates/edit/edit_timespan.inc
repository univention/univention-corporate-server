<!-- timespan header -->
<tr>
 <td colspan="5" class="control">
  <strong><?php echo _("Time span") ?></strong>
 </td>
</tr>

<!-- start date -->
<tr>
 <td class="rightAlign">
    <strong><?php echo Horde::label('start_year', _("Sta_rt")) ?></strong>
 </td>
 <td colspan="2" class="rightAlign"><?php echo _("On") ?>&nbsp;</td>
 <td>
 <?php
     $dateorder = $GLOBALS['prefs']->getValue('date_input_format');
     $dateorder = $dateorder != "" ? $dateorder : "year-month-day";
     $dateorder = explode("-", $dateorder );
     $datefields = array();
     foreach ($dateorder as $fld) {
	   $datefields[] = $event->html('start['.$fld.']');
	 }
     echo implode("-", $datefields);
 ?>
<?php if ($GLOBALS['browser']->hasFeature('dom')): ?>
  <span id="start_wday"></span>
  <script type="text/javascript">
   updateWday('start_wday');
  </script>
 </td>
 <td>
<?php Horde::addScriptFile('open_calendar.js', 'horde'); ?>
  <div id="goto" style="display:none"></div>
<?php echo Horde::link('#', _("Select a date"), '', '', 'openCalendar(\'startimg\', \'start\', \'' . addslashes($event->js('start')) . '\'); return false;') . Horde::img('calendar.png', _("Set start date"), 'id="startimg"', $GLOBALS['registry']->getImageDir('horde')) . '</a>'; endif; ?>
 </td>
</tr>

<!-- start time -->
<tr>
 <td>&nbsp;</td>
 <td colspan="2" class="rightAlign"><?php echo Horde::label('start_hour', _("At")) ?>&nbsp;</td>
 <td colspan="2">
  <?php echo $event->html('start_hour') ?>&nbsp;:&nbsp;<?php echo $event->html('start_min') ?>
  <?php
  if (!$GLOBALS['prefs']->getValue('twentyFour')) {
      if ($event->start->hour < 12) {
          $am = ' checked="checked"';
          $pm = '';
      } else {
          $am = '';
          $pm = ' checked="checked"';
      }
  ?>
  <input id="am" type="radio" class="checkbox" name="am_pm" value="AM"<?php echo $am ?> onclick="$('allday').checked=false;updateEndDate();" /><label for="am" onclick="$('allday').checked=false;updateEndDate();">AM</label>
  <input id="pm" type="radio" class="checkbox" name="am_pm" value="PM"<?php echo $pm ?> onclick="$('allday').checked=false;updateEndDate();" /><label for="pm" onclick="$('allday').checked=false;updateEndDate();">PM</label>
  <?php } ?>
 </td>
</tr>

<!-- end date -->
<tr>
 <td class="rightAlign"><strong><?php echo Horde::label('end', _("En_d")) ?></strong></td>
 <td>
  <input type="radio" class="checkbox" name="end_or_dur" id="end" value="0" checked="checked" />
 </td>
 <td class="rightAlign">
  <?php echo Horde::label('end_year', _("On")) ?>&nbsp;
 </td>
 <td>
 <?php
     $dateorder = $GLOBALS['prefs']->getValue('date_input_format');
     $dateorder = $dateorder != "" ? $dateorder : "year-month-day";
     $dateorder = explode("-", $dateorder );
     $datefields = array();
     foreach ($dateorder as $fld) {
	   $datefields[] = $event->html('end['.$fld.']');
	 }
     echo implode("-", $datefields);
 ?>
<?php if ($GLOBALS['browser']->hasFeature('dom')): ?>
  <span id="end_wday"></span>
  <script type="text/javascript">
   updateWday('end_wday');
  </script>
  </td>
  <td rowspan="2" valign="top">
<?php
    Horde::addScriptFile('open_calendar.js', 'horde');
    echo Horde::link('#', _("Select a date"), '', '', 'openCalendar(\'endimg\', \'end\', \'' . addslashes($event->js('end')) . '\'); return false;') . Horde::img('calendar.png', _("Set end date"), 'id="endimg"', $GLOBALS['registry']->getImageDir('horde')) . '</a>';
endif;
?>
 </td>
</tr>

<!-- end time -->
<tr>
 <td>&nbsp;</td>
 <td>&nbsp;</td>
 <td class="rightAlign">
  <?php echo _("At") ?>&nbsp;
 </td>
 <td colspan="2">
  <?php echo $event->html('end_hour') ?>&nbsp;:&nbsp;<?php echo $event->html('end_min') ?>
  <?php
  if (!$GLOBALS['prefs']->getValue('twentyFour')) {
      if ($event->end->hour < 12) {
          $am = ' checked="checked"';
          $pm = '';
      } else {
          $am = '';
          $pm = ' checked="checked"';
      }
  ?>
  <input id="eam" type="radio" class="checkbox" name="end_am_pm" value="AM"<?php echo $am ?> onclick="$('end').checked=true;updateDuration()" /><label for="eam" onclick="$('end').checked=true;updateDuration()">AM</label>
  <input id="epm" type="radio" class="checkbox" name="end_am_pm" value="PM"<?php echo $pm ?> onclick="$('end').checked=true;updateDuration()" /><label for="epm" onclick="$('end').checked=true;updateDuration()">PM</label>
  <?php } ?>
 </td>
</tr>

<!-- duration -->
<tr>
 <td valign="top" class="rightAlign"><strong><?php echo Horde::label('duration', _("Duration")) ?></strong></td>
 <td valign="top">
  <input type="radio" class="checkbox" name="end_or_dur" id="duration" value="1" />
 </td>
 <td>&nbsp;</td>
 <td valign="top">
  <input id="allday" name="whole_day" type="checkbox" class="checkbox" value="1" onclick="setWholeDay(this.value); updateEndDate(); $('duration').checked = true"<?php $dur = $event->getDuration(); if ($dur->wholeDay) echo ' checked="checked"' ?> />
  <?php echo Horde::label('allday', _("All day")) ?><br />
  <?php printf(_("%s Day(s) %s Hour(s) %s Minutes"), $event->html('dur_day'), $event->html('dur_hour'), $event->html('dur_min')) ?>
<?php if ($GLOBALS['browser']->hasFeature('dom')): ?>
 </td>
 <td rowspan="2">&nbsp;
<?php endif; ?>
 </td>
</tr>
