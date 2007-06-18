<table border="0" cellspacing="0" cellpadding="1" width="100%">
<tr>
  <td align="left" class="header">
    <b><?php echo _("Users in the system:") ?></b>
<?php if ($numitem): ?>
    <span class="smallheader">[<?php echo sprintf(_("%s to %s of %s"), $start, $end, $numitem) ?>]</span>
<?php endif; ?>
  </td>
</tr>
<tr>
  <td class="item">
    <form method="post" name="search" action="<?php echo Horde::selfURL() ?>">
    <?php Util::pformInput() ?>
    <input type="hidden" name="page" value="0">
    <b><?php echo _("Search") ?>:</b>&nbsp;
    <input name="search_pattern" type="text" value="" size="50" maxlength="100" /> 
    <input type="submit" class="button" value="<?php echo _("Search") ?>" />
    </form>
  </td>
</tr>
<tr><td>&nbsp;</td></tr>
<tr><td class="control"><table border="0" width="100%" cellpadding="1" cellspacing="0">
<?php
$_i = 0;
$remove = $auth->hasCapability('remove');
$total = 0;
foreach ($users as $user):
    if ($total++ < $min || $total > $max) {
        continue;
    }
?>
<tr class="item<?php echo $_i++%2 ?>">
<?php if ($remove): ?>
  <td width="1%"><?php echo Horde::link(Horde::applicationUrl('admin/user.php?form=remove_f&user_name=' . $user), _("Delete")) . Horde::img('delete.gif', _("Delete")) ?></a></td>
<?php endif; ?>
  <td width="1%"><?php echo Horde::link(Horde::applicationUrl('admin/user.php?form=update_f&user_name=' . $user . '&do_update=1'), _("Update")) .  Horde::img('edit.gif', _("Update")) ?></a></td>
  <td align="left"><?php echo $user ?></td>
</tr>
<?php
endforeach;
if ($numitem) {
    $pager = &new Horde_UI_Pager('page', $vars, array('num' => $total, 'url' => $viewurl, 'page_count' => 10, 'perpage' => $perpage));        
    echo $pager->render($page, $total, $viewurl);
}
?>
</table></td></tr>
</table>
