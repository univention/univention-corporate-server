<?php echo Horde::label($pref, $_prefs[$pref]['desc']) ?>&nbsp;<?php echo $helplink ?><br />
<div class="fixed">
<textarea id="<?php echo $pref ?>" name="<?php echo $pref ?>" rows="6" cols="80" class="fixed"><?php echo htmlspecialchars($prefs->getValue($pref)) ?></textarea><br />
</div>
