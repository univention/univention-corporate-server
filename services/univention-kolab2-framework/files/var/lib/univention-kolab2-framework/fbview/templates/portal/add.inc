<?php if ($layout->isChanged($row, $col)): ?>
<a name="block"></a>
<?php endif; ?>
<table cellspacing="0" width="100%">
  <tr>
    <td class="header"><?php echo _("Add Here:") ?></td>
  </tr>
</table>
<table cellspacing="0" cellpadding="3" width="100%" height="100%">
  <tr>
    <td width="100%" height="100%">
      <form action="<?php echo Horde::selfUrl() ?>#block" method="post">
        <?php Util::pformInput() ?>
        <input type="hidden" name="row" value="<?php echo $row ?>" />
        <input type="hidden" name="col" value="<?php echo $col ?>" />
        <input type="hidden" name="action" value="save-resume" />
        <?php echo $blocks->getBlocksWidget() ?>
        <input type="submit" class="button" value="<?php echo _("Add") ?>" />
      </form>
    </td>
  </tr>
</table>
