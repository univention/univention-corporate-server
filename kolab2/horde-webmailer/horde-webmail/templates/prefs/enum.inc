<?php echo Horde::label(htmlspecialchars($pref), $_prefs[$pref]['desc']) ?>&nbsp;<?php echo $helplink ?><br />
<select id="<?php echo htmlspecialchars($pref) ?>" name="<?php echo htmlspecialchars($pref) ?>">
<?php $esc = !empty($_prefs[$pref]['escaped']); $curval = $prefs->getValue($pref); foreach ($_prefs[$pref]['enum'] as $key => $val): ?>
<option<?php echo $curval == $key ? ' selected="selected"' : '' ?> value="<?php echo $esc ? $key : htmlspecialchars($key) ?>"><?php echo $esc ? $val : htmlspecialchars($val) ?></option>
<?php endforeach ?>
</select>
<br />
