 <tr style="vertical-align:top">
<?php if ($cond_num > 0): ?>
  <td>
   <strong><?php echo ($rule['combine'] == INGO_STORAGE_COMBINE_ALL) ? _("and") : _("or") ?></strong>
  </td>
<?php elseif (($cond_num == 0) && !$lastfield): ?>
  <td>&nbsp;</td>
<?php endif; ?>
  <td>
   <label for="field_<?php echo (int)$cond_num ?>" class="hidden"><?php echo _("Field") ?></label>
   <select onchange="document.rule.submit(); return true;" id="field_<?php echo (int)$cond_num ?>" name="field[<?php echo (int)$cond_num ?>]">
    <?php echo $field_select ?>
   </select>
<?php if ($header_entry): ?>
   <label for="userheader_<?php echo (int)$cond_num ?>" class="hidden"><?php echo _("User header") ?></label>
   <input id="userheader_<?php echo (int)$cond_num ?>" name="userheader[<?php echo (int)$cond_num ?>]" value="<?php echo htmlspecialchars($userheader) ?>" />
<?php endif; ?>
  </td>
<?php if ($lastfield): ?>
  <td colspan="2">&nbsp;</td>
<?php else: ?>
  <td>
   <label for="match_<?php echo (int)$cond_num ?>" class="hidden"><?php echo _("Match type") ?></label>
   <select onchange="document.rule.submit(); return true;" id="match_<?php echo (int)$cond_num ?>" name="match[<?php echo (int)$cond_num ?>]">
    <?php echo $match_select ?>
   </select>
  </td>
  <td>
   <?php echo $match_value ?>
  </td>
<?php endif; ?>
<?php if (!$lastfield): ?>
  <td><?php echo Horde::link('javascript:delete_condition(' . (int)$cond_num . ');', _("Delete Condition")) . Horde::img('delete.png', _("Delete Condition"), null, $registry->getImageDir('horde')) ?></a></td>
<?php elseif ($cond_num != 0): ?>
  <td>&nbsp;</td>
<?php endif; ?>
 </tr>
