<form name="edit_group" method="post" action="groups.php">
<input type="hidden" name="actionID" value="editform" />
<input type="hidden" name="cid" value="<?php echo $group->getId() ?>" />
<?php Util::pformInput() ?>
<table border="0" width="100%" cellpadding="1" cellspacing="0">
<tr valign="middle">
  <td class="header" width="100%" colspan="3">
    <b><?php echo $group->getShortName() ?></b>
  </td>
</tr>
<tr>
  <td class="light" nowrap="nowrap"><?php echo _("Email Address") ?></td>
  <td colspan="2"><input type="text" name="email" size="50" value="<?php echo htmlspecialchars($group->get('email')) ?>" /></td>
</tr>
<tr><td>&nbsp;</td></tr>

<tr valign="middle">
  <td class="header" width="1%">
    <?php echo Horde::img('group.gif') . '&nbsp;' . _("Members") ?>
  </td>
  <td class="header" align="center" nowrap="nowrap" width="1%"><?php echo _("Remove") ?></td>
  <td class="header" width="100%"></td>
</tr>
<?php
$users = $group->listUsers();
foreach ($users as $user):
?>
<tr>
  <td nowrap="nowrap" class="light"><?php echo htmlspecialchars($user) ?></td>
  <td class="light" align="center"><input type="checkbox" name="remove[<?php echo htmlspecialchars($user) ?>]" /></td>
</tr>
<?php endforeach; ?>

<tr><td>&nbsp;</td></tr>

<!-- New user form -->
<tr valign="middle">
  <td class="header" colspan="3">
    <?php echo Horde::img('user.gif') . '&nbsp;' . _("Add new members") ?>
  </td>
</tr>
<tr>
<?php if ($auth->hasCapability('list')): ?>
  <td class="light">
    <select name="new_user[]" multiple="multiple">
    <?php foreach ($auth->listUsers() as $user) { if (!in_array($user, $users)) { ?>
      <option value="<?php echo $user ?>"><?php echo $user ?></option>
    <?php } } ?>
    </select>
<?php else: ?>
  <td class="light"><input type="text" name="new_user" />
<?php endif; ?>
    <input type="submit" class="button" value="<?php printf(_("Save '%s'"), $group->getShortName()) ?>" />
  </td>
</tr>
<tr>
  <td>
</tr>
</table>
<br />
