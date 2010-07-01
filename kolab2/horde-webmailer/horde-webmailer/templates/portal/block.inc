<td class="headerbox" valign="top" style="width:<?php echo ($width * $colspan) ?>%" rowspan="<?php echo $rowspan ?>" colspan="<?php echo $colspan ?>">
 <div class="blockHeader">
  <span class="rightFloat blockIcons">
   <?php echo $this->getHeaderIcons($row_num, $col_num, true) ?>
  </span>
  <h1 class="header"><?php echo $header ?></h1>
 </div>
 <div id="block_<?php echo $row_num . '_' . $col_num ?>">
  <?php echo $content ?>
 </div>
<?php if (!empty($block->updateable) && !empty($refresh_time)): ?>
 <script type="text/javascript">
 setTimeout(function() {
     new Ajax.PeriodicalUpdater('block_<?php echo (int)$row_num ?>_<?php echo (int)$col_num ?>',
                                '<?php echo Horde::applicationUrl('services/portal/index.php') ?>',
             { parameters: { httpclient: 1, row: <?php echo (int)$row_num ?>, col: <?php echo (int)$col_num ?> },
               method: 'get',
               evalScripts: true,
               frequency: <?php echo (int)$refresh_time ?> });
 }, <?php echo (int)$refresh_time * 1000 ?>);
 </script>
<?php endif; ?>
</td>
