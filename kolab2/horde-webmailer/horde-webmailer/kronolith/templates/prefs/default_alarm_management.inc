<?php if (!$prefs->isLocked('default_alarm')):

$alarm_value = $prefs->getValue('default_alarm');
if (!$alarm_value) {
    $alarm_unit = 'min';
} else {
    if ($alarm_value % 10080 == 0) {
        $alarm_value /= 10080;
        $alarm_unit = 'week';
    } elseif ($alarm_value % 1440 == 0) {
        $alarm_value /= 1440;
        $alarm_unit = 'day';
    } elseif ($alarm_value % 60 == 0) {
        $alarm_value /= 60;
        $alarm_unit = 'hour';
    } else {
        $alarm_unit = 'min';
    }
}
?>
<?php echo _("Default Alarm Setting:") ?><br />
<label for="alarm_value" class="hidden"><?php echo _("Alarm Value") ?></label>
<input type="text" size="2" id="alarm_value" name="alarm_value" value="<?php echo (int)$alarm_value ?>" />&nbsp;
<label for="alarm_unit" class="hidden"><?php echo _("Alarm Unit") ?></label>
<select id="alarm_unit" name="alarm_unit">
 <option value="1"<?php echo ($alarm_unit == 'min') ? ' selected="selected"' : '' ?>><?php echo _("Minute(s)") ?></option>
 <option value="60"<?php echo ($alarm_unit == 'hour') ? ' selected="selected"' : '' ?>><?php echo _("Hour(s)") ?></option>
 <option value="1440"<?php echo ($alarm_unit == 'day') ? ' selected="selected"' : '' ?>><?php echo _("Day(s)") ?></option>
 <option value="10080"<?php echo ($alarm_unit == 'week') ? ' selected="selected"' : '' ?>><?php echo _("Week(s)") ?></option>
</select>
<?php echo _("before the event starts. A value of \"0\" means no default alarms.") ?>
<?php endif; ?>
