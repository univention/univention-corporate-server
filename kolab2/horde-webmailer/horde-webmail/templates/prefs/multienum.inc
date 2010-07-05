<?php echo Horde::label($pref, $_prefs[$pref]['desc']) ?>&nbsp;<?php echo $helplink ?><br />
<select id="<?php echo $pref ?>" multiple="multiple" size="<?php echo min(4, count($_prefs[$pref]['enum'])) ?>" name="<?php echo $pref ?>[]">
<?php $selected = @unserialize($prefs->getValue($pref)); if (!$selected) $selected = array(); foreach ($_prefs[$pref]['enum'] as $key => $val): ?>
<option<?php echo in_array($key, $selected) ? ' selected="selected" ' : '' ?> value="<?php echo htmlspecialchars($key) ?>"><?php echo htmlspecialchars($val) ?></option>
<?php endforeach ?>
</select>
<br />
