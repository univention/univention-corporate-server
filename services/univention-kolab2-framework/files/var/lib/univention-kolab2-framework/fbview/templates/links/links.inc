<table border="0" cellpadding="2" cellspacing="0" width="100%">
<tr>
 <td class="header">
  <?php echo $definition['description']; if ($this->_definitions[$type]['readonly']) echo _(" (Read only)") ?>
 </td>
 <td class="header" align="right">
  <?php if ($registry->hasMethod($app . '/addLink') && !$this->_definitions[$type]['readonly']): ?>
  <input type="button" onclick="document.location = '<?php echo Horde::url($registry->link($app . '/addLink',
        array('url' => Horde::selfUrl(true, false, true),
              'from_parameters' => serialize($link_data['from_params']),
              'from_application' => $registry->getParam('provides'),
              'link_type' => $type . $reverse,
             ))) ?>';" class="button" value="<?php printf(_("Add %s"), $definition['description']) ?>" />
 <?php endif; ?>
 </td>
</tr>

<?php $i = 0; foreach ($this->listLinks($link_data) as $id => $link): ?>
<tr>
 <td class="item<?php echo ($i++ % 2) ?>" colspan="2">
  <?php $this->display($type, $link) ?>
 </td>
</tr>
<?php endforeach; ?>

</table>
<br />
