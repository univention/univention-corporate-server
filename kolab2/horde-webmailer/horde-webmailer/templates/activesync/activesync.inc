<div class="smallheader">
 <?php echo _("Known ActiveSync synchronisation devices") ?>
</div>
<?php if (!$devices): ?>
<em><?php echo _("None") ?></em>
<?php else: ?>
<table class="striped">
<tr>
 <th><?php echo _("Device") ?></th>
 <th><?php echo _("Type") ?></th>
 <th><?php echo _("Mode") ?></th>
</tr>
<?php
foreach ($devices as $device => $data) {
?>
<tr>
 <td><?php echo htmlspecialchars($device) ?></td>
 <td><?php echo htmlspecialchars($data['TYPE']) ?></td>
 <td>
   <select id="mode_select[<?php echo $device; ?>]" name="mode_select[<?php echo $device; ?>]">
     <option value=""><?php echo _("Select the device mode:"); ?></option>
     <option value="-1" <?php echo ($data['MODE'] === null || $data['MODE'] === '-1') ? 'selected="selected"' : ''; ?>>Default</option>
     <option value="0" <?php echo ($data['MODE'] === '0') ? 'selected="selected"' : ''; ?>>Flat mode</option>
     <option value="1" <?php echo ($data['MODE'] === '1') ? 'selected="selected"' : ''; ?>>Folder mode</option>
   </select>
 </td>
 <td>
   <input type="submit" class="button" value="<?php echo _("Delete") ?>" name="delete[<?php echo htmlspecialchars($device) ?>]"/>
 </td>
</tr>
<?php } ?>
</table>
<?php endif; ?>
<p>
 <input type="hidden" name="actionID" value="save" />
 <input type="submit" class="button" value="<?php echo _("Store device modes") ?>" />
 <input id="prefs_return" type="button" class="button" onclick="cancelSubmit=true;document.location.href='<?php echo Horde::applicationUrl(Util::addParameter('services/prefs.php', 'app', 'horde'), true) ?>'" value="<?php echo _("Return to Options") ?>" />
</p>

</div>
</form>
