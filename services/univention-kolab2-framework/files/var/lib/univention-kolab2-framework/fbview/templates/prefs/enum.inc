<?php echo Horde::label($pref, $_prefs[$pref]['desc']) ?>&nbsp;<?php echo $helplink ?><br />
<select id="<?php echo $pref ?>" name="<?php echo $pref ?>">
<?php foreach ($_prefs[$pref]['enum'] as $key => $val): ?>
<option<?php echo $prefs->getValue($pref) == $key ? ' selected="selected"' : '' ?> value="<?php echo $key ?>"><?php echo $val ?></option>
<?php endforeach ?>
</select>
<br />
