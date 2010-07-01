<?php echo Horde::label(htmlspecialchars($pref), $_prefs[$pref]['desc']) ?>&nbsp;<?php echo $helplink ?><br />
<select id="<?php echo htmlspecialchars($pref) ?>" name="<?php echo htmlspecialchars($pref) ?>">
<?php $esc = !empty($_prefs[$pref]['escaped']); $curval = $prefs->getValue($pref); $select_var = Util::nonInputVar($pref . '_options'); foreach ($select_var as $select_key => $select_val): ?>
 <option value="<?php echo $esc ? $select_key : htmlspecialchars($select_key) ?>"<?php if ($select_key == $curval) echo ' selected="selected"' ?>><?php echo $esc ? $select_val : htmlspecialchars($select_val) ?></option>
<?php endforeach; ?>
</select>
<br />
