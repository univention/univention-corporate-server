<?php
if (!$prefs->isLocked('default_due_time')):
    $default_due_time = $prefs->getValue('default_due_time');
?>

<?php echo Horde::label('default_due_time', _("What do you want to be the default due time for tasks?")) ?><br />
<select id="default_due_time" name="default_due_time">
 <option value="now"<?php if ($default_due_time == 'now') echo ' selected="selected"' ?>><?php echo _("The current hour") ?></option>
<?php
for ($i = 0; $i < 24; ++$i) {
    $value = sprintf('%02d:00', $i);
    if ($GLOBALS['prefs']->getValue('twentyFour')) {
        echo '<option value="' . $value . '"' . ($value == $default_due_time ? ' selected="selected"' : '') . '>' . $value . '</option>';
    } else {
        echo '<option value="' . $value . '"' . ($value == $default_due_time ? ' selected="selected"' : '') . '>' . sprintf('%02d:00 ' . ($i >= 12 ? _("pm") : _("am")), ($i % 12 ? $i % 12 : 12)) . '</option>';
    }
}
?>
</select><br /><br />
<?php endif; ?>
