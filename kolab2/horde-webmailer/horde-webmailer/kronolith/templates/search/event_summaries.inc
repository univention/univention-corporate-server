<tr class="text">
 <td nowrap="nowrap" class="category<?php echo md5($found->getCategory()) ?>">
  <?php echo $found->getLink() ?>
 </td>
 <td class="nowrap"><?php echo htmlspecialchars($found->getCategory()) ?></td>
 <td class="nowrap"><?php echo htmlspecialchars($found->getLocation()) ?></td>
 <td class="nowrap"><?php echo Kronolith::statusToString($found->getStatus()) ?></td>
 <td class="nowrap"><?php echo strftime($prefs->getValue('date_format'), $start->timestamp()) . date($prefs->getValue('twentyFour') ? ' G:i' : ' g:i a', $start->timestamp()) ?></td>
 <td class="nowrap"><?php echo strftime($prefs->getValue('date_format'), $end->timestamp()) . date($prefs->getValue('twentyFour') ? ' G:i' : ' g:i a', $end->timestamp()) ?></td>
</tr>
