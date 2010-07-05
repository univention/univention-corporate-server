<input type="text" id="<?php echo $pref ?>" name="<?php echo $pref ?>" size="3" maxlength="3" value="<?php echo htmlspecialchars($prefs->getValue($pref)) ?>" />
<?php echo Horde::label($pref, $_prefs[$pref]['desc']) ?>&nbsp;<?php echo $helplink ?><br />
