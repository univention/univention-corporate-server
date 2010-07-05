<h1 class="header">
 <?php echo _("Users in the system:") ?>
 <?php if ($numitem): ?>
  <small>[<?php printf(_("%d to %d of %d"), $start, $end, $numitem) ?>]</small>
 <?php endif; ?>
</h1>

<div class="headerbox">

<div class="control">
 <form method="post" name="search" action="<?php echo Horde::selfUrl() ?>">
 <?php echo Util::formInput() ?>
 <input type="hidden" name="page" value="0" />
 <strong><?php echo Horde::label('search_pattern', _("Search:")) ?></strong>
 <input id="search_pattern" name="search_pattern" type="text" value="" size="50" maxlength="100" />
 <input type="submit" class="button" value="<?php echo _("Search") ?>" />
 </form>
</div>

<table class="striped" width="100%" cellspacing="0">
<?php
$remove = $auth->hasCapability('remove');
$total = 0;
foreach ($users as $user):
    if ($total++ < $min || $total > $max) {
        continue;
    }
?>
 <tr>
<?php if ($remove): ?>
  <td width="1%"><?php echo Horde::link(Horde::applicationUrl('admin/user.php?form=remove_f&user_name=' . $user), _("Delete")) . Horde::img('delete.png', _("Delete")) ?></a></td>
<?php endif; ?>
  <td width="1%"><?php echo Horde::link(Horde::applicationUrl('admin/user.php?form=update_f&user_name=' . $user), _("Update")) .  Horde::img('edit.png', _("Update")) ?></a></td>
  <td width="1%"><?php echo Horde::link(Horde::applicationUrl('admin/user.php?form=clear_f&user_name=' . $user), _("Clear user data")) .  Horde::img('reload.png', _("Clear user data")) ?></a></td>
  <td class="leftAlign"><?php echo $user ?></td>
 </tr>
<?php endforeach; ?>
</table>
<?php
if ($numitem) {
    $pager = &new Horde_UI_Pager('page', $vars, array('num' => $total, 'url' => $viewurl, 'page_count' => 10, 'perpage' => $perpage));
    echo $pager->render($page, $total, $viewurl);
}
?>
</div>
