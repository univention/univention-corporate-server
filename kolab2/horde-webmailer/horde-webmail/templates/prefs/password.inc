<?php echo Horde::label($pref, $_prefs[$pref]['desc']) ?>&nbsp;<?php echo $helplink ?><br />
<input type="password" id="<?php echo $pref ?>" name="<?php echo $pref ?>" size="30" maxlength="60" value="<?php echo htmlspecialchars($prefs->getValue($pref)) ?>" /><br />
