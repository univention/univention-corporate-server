<?php echo Horde::label($pref, $_prefs[$pref]['desc']) ?>&nbsp;<?php echo $helplink ?><br />
<select id="<?php echo $pref ?>" name="<?php echo $pref ?>">
    <option value=""<?php if (!$prefs->getValue($pref)) echo ' selected="selected"'; ?>><?php echo _("Use Default Value") ?></option>
<?php $select_var = $pref . '_options'; foreach ($GLOBALS[$select_var] as $select_key => $select_val): ?>
    <option value="<?php echo htmlspecialchars($select_key) ?>"<?php if ($select_key == $prefs->getValue($pref)) echo ' selected="selected"' ?>><?php echo $select_val ?></option>
<?php endforeach; ?>
</select>
<br />
