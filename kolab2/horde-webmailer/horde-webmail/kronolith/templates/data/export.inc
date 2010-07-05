<form method="post" name="export" action="<?php echo Horde::downloadUrl(_("events.csv"), null, 'data.php') ?>">
<?php Util::pformInput() ?>
<input type="hidden" name="actionID" value="export" />

<br class="spacer" />

<h1 class="header">
 <?php echo _("Export Calendar") ?>
</h1>

<div class="item">
    <?php echo Horde::label('exportID', _("Select the export format:")) ?><br />
    <select id="exportID" name="exportID">
      <option value="<?php echo EXPORT_CSV ?>">CSV</option>
      <option value="<?php echo EXPORT_ICALENDAR ?>">iCalendar</option>
    </select><br /><br />

    <?php if (count($calendars = Kronolith::listCalendars(false, PERMS_READ)) > 1): ?>
    <?php echo Horde::label('exportCal', _("Select the calendar(s) to export from")) ?><br />
    <select id="exportCal" name="exportCal[]" multiple="multiple">
      <?php foreach ($calendars as $id => $cal) {
          printf('<option value="%s">%s</option>', htmlspecialchars($id), htmlspecialchars($cal->get('name'))) . "\n";
      } ?>
    </select><br /><br />
    <?php else: ?>
    <input type="hidden" name="exportCal[]" value="<?php echo htmlspecialchars(Kronolith::getDefaultCalendar(PERMS_READ)) ?>" />
    <?php endif; ?>

    <?php echo _("Limit the time span to export:") ?><br />
    <table>
    <tr>
      <td><input type="radio" class="checkbox" name="all_events" id="all" value="1" checked="checked" /></td>
      <td colspan="2"><?php echo Horde::label('all', _("All events")) ?></td>
    </tr>
    <tr>
      <td rowspan="4" valign="top"><input type="radio" class="checkbox" name="all_events" id="some" value="0" /></td>
      <td class="rightAlign"><?php echo Horde::label('some', _("Start On")) ?></td>
      <td colspan="3">
        <label for="start_year" class="hidden"><?php echo _("Start Year") ?></label>
        <select id="start_year" name="start_year" onchange="document.getElementById('some').checked = true;">
<?php
$start_year_match = date('Y');
for ($i = -1; $i < 6; $i++):
    $yr = date('Y') + $i;
    $sel = '';
    if ($yr == $start_year_match) {
        $sel = ' selected="selected"';
    }
?>
          <option value="<?php echo $yr ?>"<?php echo $sel ?>><?php echo $yr ?></option>
<?php endfor; ?>
        </select>
        -
        <label for="start_month" class="hidden"><?php echo _("Start Month") ?></label>
        <select id="start_month" name="start_month" onchange="document.getElementById('some').checked = true;">
<?php
$start_month_match = date('n') - 1;
for ($i = 1; $i < 13; $i++):
    $sel = '';
    if ($i == $start_month_match) {
        $sel = ' selected="selected"';
    }
?>
          <option value="<?php echo $i ?>"<?php echo $sel ?>><?php echo strftime('%b', mktime(1, 1, 1, $i, 1)) ?></option>
<?php endfor; ?>
        </select>
        -
        <label for="start_day" class="hidden"><?php echo _("Start Day") ?></label>
        <select id="start_day" name="start_day" onchange="document.getElementById('some').checked = true;">
<?php
$start_day_match = date('j');
for ($i = 1; $i < 32; $i++):
    $sel = '';
    if ($i == $start_day_match) {
        $sel = ' selected="selected"';
    }
?>
          <option value="<?php echo $i ?>"<?php echo $sel ?>><?php echo $i ?></option>
<?php endfor; ?>
        </select>
      </td>
    </tr>
    <!-- start time -->
    <tr>
      <td class="rightAlign"><?php echo _("At") ?></td>
      <td colspan="3">
        <label for="start_hour" class="hidden"><?php echo _("Start Hour") ?></label>
        <select id="start_hour" name="start_hour" onchange="document.getElementById('some').checked = true;">
<?php
$start_hour_match = $prefs->getValue('twentyFour') ? 0 : 10;
$hour_min = ($prefs->getValue('twentyFour')) ? 0 : 1;
$hour_max = ($prefs->getValue('twentyFour')) ? 24 : 13;
for ($i = $hour_min; $i < $hour_max; $i++):
    $sel = '';
    if ($i == $start_hour_match)
        $sel = ' selected="selected"';
?>
          <option value="<?php echo $i ?>"<?php echo $sel ?>><?php echo $i ?></option>
<?php endfor; ?>
        </select>
        &nbsp;:&nbsp;
        <label for="start_min" class="hidden"><?php echo _("Start Minute") ?></label>
        <select id="start_min" name="start_min" onchange="document.getElementById('some').checked = true;">
<?php
$start_min_match = 0;
for ($i = 0; $i < 12; $i++):
    $sel = '';
    $min = sprintf('%02d', $i * 5);
    if ($min == $start_min_match)
        $sel = ' selected="selected"';
?>
          <option value="<?php echo $min ?>"<?php echo $sel ?>><?php echo $min ?></option>
<?php endfor; ?>
        </select>
<?php
if (!$prefs->getValue('twentyFour')) {
?>
        <input type="radio" class="checkbox" name="am_pm" id="sam" value="AM" checked="checked" /><?php echo Horde::label('sam', _("AM")) ?>
        <input type="radio" class="checkbox" name="am_pm" id="spm" value="PM" /><?php echo Horde::label('spm', _("PM")) ?>
<?php } ?>
      </td>
    </tr>
    <!-- end date -->
    <tr>
      <td class="rightAlign"><?php echo _("End On") ?></td>
      <td>
<?php
$end_year_match = $start_year_match;
$end_month_match = $start_month_match + 1;
$end_day_match = $start_day_match;
$end_hour_match = $start_hour_match;
$end_min_match = $start_min_match;
?>
        <label for="end_year" class="hidden"><?php echo _("End Year") ?></label>
        <select id="end_year" name="end_year" onchange="document.getElementById('some').checked = true;">
<?php
for ($i = -1; $i < 6; $i++):
    $yr = date('Y') + $i;
    $sel = '';
    if ($yr == $end_year_match) {
        $sel = ' selected="selected"';
    }
?>
          <option value="<?php echo $yr ?>"<?php echo $sel ?>><?php echo $yr ?></option>
<?php endfor; ?>
        </select>
        -
        <label for="end_month" class="hidden"><?php echo _("End Month") ?></label>
        <select id="end_month" name="end_month" onchange="document.getElementById('some').checked = true;">
<?php
for ($i = 1; $i < 13; $i++):
    $sel = '';
    if ($i == $end_month_match) {
        $sel = ' selected="selected"';
    }
?>
          <option value="<?php echo $i ?>"<?php echo $sel ?>><?php echo strftime('%b', mktime(1,1,1,$i,1)) ?></option>
<?php endfor; ?>
        </select>
        -
        <label for="end_day" class="hidden"><?php echo _("End Day") ?></label>
        <select id="end_day" name="end_day" onchange="document.getElementById('some').checked = true;">
<?php
for ($i = 1; $i < 32; $i++):
    $sel = '';
    if ($i == $end_day_match)
        $sel = ' selected="selected"';
?>
          <option value="<?php echo $i ?>"<?php echo $sel ?>><?php echo $i ?></option>
<?php endfor; ?>
        </select>
      </td>
    </tr>
    <!-- end time -->
    <tr>
      <td class="rightAlign"><?php echo _("At") ?></td>
      <td>
        <label for="end_hour" class="hidden"><?php echo _("End Hour") ?></label>
        <select id="end_hour" name="end_hour" onchange="document.getElementById('some').checked = true;">
<?php
for ($i = $hour_min; $i < $hour_max; $i++):
    $sel = '';
    if ($i == $end_hour_match)
        $sel = ' selected="selected"';
?>
          <option value="<?php echo $i ?>"<?php echo $sel ?>><?php echo $i ?></option>
<?php endfor; ?>
        </select>
        &nbsp;:&nbsp;
        <label for="end_min" class="hidden"><?php echo _("End Minute") ?></label>
        <select id="end_min" name="end_min" onchange="document.getElementById('some').checked = true;">
<?php
for ($i = 0; $i < 12; $i++):
    $sel = '';
    $min = sprintf('%02d', $i * 5);
    if ($min == $end_min_match)
        $sel = ' selected="selected"';
?>
          <option value="<?php echo $min ?>"<?php echo $sel ?>><?php echo $min ?></option>
<?php endfor; ?>
        </select>
<?php if (!$prefs->getValue('twentyFour')): ?>
        <input type="radio" class="checkbox" name="end_am_pm" id="eam" value="AM" checked="checked" /><?php echo Horde::label('eam', _("AM")) ?>
        <input type="radio" class="checkbox" name="end_am_pm" id="epm" value="PM" /><?php echo Horde::label('epm', _("PM")) ?>
<?php endif; ?>
      </td>
    </tr>
    </table><br />
    <input type="submit" value="<?php echo _("Export") ?>" class="button" />
</div>
</form>
