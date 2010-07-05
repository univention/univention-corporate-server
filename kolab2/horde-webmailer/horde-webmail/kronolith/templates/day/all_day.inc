 <tr>
<?php if ($first_row): ?>
  <td class="nowrap rightAlignt"<?php echo $rowspan ?>><strong><?php echo $newEventUrl ?></strong></td>
  <td<?php echo $rowspan ?> style="height:<?php echo round(20 / $this->_slotsPerHour) ?>px">&nbsp;</td>
  <td<?php echo $rowspan ?>>&nbsp;</td>
<?php endif; ?>
  <?php echo $row ?>
 </tr>
