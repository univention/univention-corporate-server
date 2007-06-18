<form name="edit" method="post" action="<?php echo $_SERVER['PHP_SELF'] ?>">
<?php Util::pformInput() ?>
<input type="hidden" name="actionID" value="editform" />
<input type="hidden" name="cid" value="<?php echo $share->getId() ?>" />
<?php if (!empty($app)): ?>
<input type="hidden" name="app" value="<?php echo htmlspecialchars($app) ?>" />
<?php endif; ?>
<table border="0" width="100%" cellpadding="0" cellspacing="0">
<tr valign="middle">
  <td width="100%" colspan="7">
   <table border="0" cellpadding="0" cellspacing="0" width="100%">
    <tr>
     <td class="header">
      <?php echo Horde::img('perms.gif', '', '', $registry->getParam('graphics', 'horde')) ?>&nbsp;<b><?php echo sprintf(_("Edit permissions for %s"), $share->get('name')) ?></b>
     </td>
     <td align="right" class="header">
      <a onclick="javascript:window.close();" style="cursor: pointer;"><?php echo Horde::img('close.gif', _("Close Window"), '', $registry->getParam('graphics', 'horde')) ?></a>
     </td>
    </tr>
   </table>
  </td>
</tr>
<tr><td>&nbsp;</td></tr>

<?php $owner = $share->get('owner'); ?>
<?php $userperms = $perm->getUserPermissions(); ?>

<!-- Ownership -->
<?php if (isset($userperms[$owner])) {
          $operm = $userperms[$owner];
      } else {
          $operm = PERMS_SHOW & PERMS_READ & PERMS_EDIT & PERMS_DELETE;
      }
?>
<tr valign="middle">
  <td class="header" align="left" width="25%">
    <?php echo Horde::img('perms.gif', '', '', $registry->getParam('graphics', 'horde')) . '&nbsp;' . _("Owner Permissions") ?>
  </td>
  <td class="header" align="center" width="1%"><?php echo _("Show") ?></td>
  <td class="header" align="center" width="1%"><?php echo _("Read") ?></td>
  <td class="header" align="center" width="1%"><?php echo _("Edit") ?></td>
  <td class="header" align="center" width="1%"><?php echo _("Delete") ?></td>
  <td class="header" align="right" width="70%">&nbsp;</td>
</tr>
<tr>
<?php if ($auth->hasCapability('list')): ?>
  <td class="light">
    <select name="owner">
      <option value=""><?php echo _("Select a new owner") . ':'; ?></option>
      <option value="<?php echo $owner ?>" selected="selected"><?php echo Auth::removeHook($owner) ?></option>
    <?php foreach ($userList as $user) { if ($user != $owner) { ?>
      <option value="<?php echo $user ?>"><?php echo Auth::removeHook($user) ?></option>
    <?php } } ?>
    </select>
  </td>
<?php else: ?>
  <td class="light"><input type="text" name="owner" value="<?php echo ($owner) ?>" /></td>
<?php endif; ?>
  <td align="center"><input type="checkbox" name="owner_show"<?php echo ($operm & PERMS_SHOW) ? ' checked="checked"' : '' ?> /></td>
  <td align="center"><input type="checkbox" name="owner_read"<?php echo ($operm & PERMS_READ) ? ' checked="checked"' : '' ?> /></td>
  <td align="center"><input type="checkbox" name="owner_edit"<?php echo ($operm & PERMS_EDIT) ? ' checked="checked"' : '' ?> /></td>
  <td align="center"><input type="checkbox" name="owner_delete"<?php echo ($operm & PERMS_DELETE) ? ' checked="checked"' : '' ?> /></td>
</tr>

<!-- Spacer -->
<tr><td>&nbsp;</td></tr>

<!-- Default Permissions -->
<tr valign="middle">
  <td class="header" align="left" width="25%">
    <?php echo Horde::img('perms.gif', '', '', $registry->getParam('graphics', 'horde')) . '&nbsp;' . _("All Authenticated Users") ?>
  </td>
  <td class="header" align="center" width="1%"><?php echo _("Show") ?></td>
  <td class="header" align="center" width="1%"><?php echo _("Read") ?></td>
  <td class="header" align="center" width="1%"><?php echo _("Edit") ?></td>
  <td class="header" align="center" width="1%"><?php echo _("Delete") ?></td>
  <td class="header" align="right" width="70%">&nbsp;</td>
</tr>
<?php $dperm = $perm->getDefaultPermissions(); ?>
<tr>
  <td class="light">&nbsp;</td>
  <td align="center"><input type="checkbox" name="default_show"<?php echo ($dperm & PERMS_SHOW) ? ' checked="checked"' : '' ?> /></td>
  <td align="center"><input type="checkbox" name="default_read"<?php echo ($dperm & PERMS_READ) ? ' checked="checked"' : '' ?> /></td>
  <td align="center"><input type="checkbox" name="default_edit"<?php echo ($dperm & PERMS_EDIT) ? ' checked="checked"' : '' ?> /></td>
  <td align="center"><input type="checkbox" name="default_delete"<?php echo ($dperm & PERMS_DELETE) ? ' checked="checked"' : '' ?> /></td>
</tr>

<!-- Spacer -->
<tr><td>&nbsp;</td></tr>

<!-- Guest Permissions -->
<tr valign="middle">
  <td class="header" align="left" width="25%">
    <?php echo Horde::img('guest.gif', '', '', $registry->getParam('graphics', 'horde')) . '&nbsp;' . _("Guest Permissions") ?>
  </td>
  <td class="header" align="center" width="1%"><?php echo _("Show") ?></td>
  <td class="header" align="center" width="1%"><?php echo _("Read") ?></td>
  <td class="header" align="center" width="1%"><?php echo _("Edit") ?></td>
  <td class="header" align="center" width="1%"><?php echo _("Delete") ?></td>
  <td class="header" align="right" width="70%">&nbsp;</td>
</tr>
<?php $gperm = $perm->getGuestPermissions(); ?>
<tr>
  <td class="light">&nbsp;</td>
  <td align="center"><input type="checkbox" name="guest_show"<?php echo ($gperm & PERMS_SHOW) ? ' checked="checked"' : '' ?> /></td>
  <td align="center"><input type="checkbox" name="guest_read"<?php echo ($gperm & PERMS_READ) ? ' checked="checked"' : '' ?> /></td>
  <td align="center"><input type="checkbox" name="guest_edit"<?php echo ($gperm & PERMS_EDIT) ? ' checked="checked"' : '' ?> /></td>
  <td align="center"><input type="checkbox" name="guest_delete"<?php echo ($gperm & PERMS_DELETE) ? ' checked="checked"' : '' ?> /></td>
</tr>

<!-- Spacer -->
<tr><td>&nbsp;</td></tr>

<!-- Creator Permissions -->
<tr valign="middle">
  <td class="header" align="left" width="25%">
    <?php echo Horde::img('user.gif', '', '', $registry->getParam('graphics', 'horde')) . '&nbsp;' . _("Object Creator") ?>
  </td>
  <td class="header" align="center" width="1%"><?php echo _("Show") ?></td>
  <td class="header" align="center" width="1%"><?php echo _("Read") ?></td>
  <td class="header" align="center" width="1%"><?php echo _("Edit") ?></td>
  <td class="header" align="center" width="1%"><?php echo _("Delete") ?></td>
  <td class="header" align="right" width="70%"></td>
</tr>
<?php $cperm = $perm->getCreatorPermissions(); ?>
<tr>
  <td class="light">&nbsp;</td>
  <td align="center"><input type="checkbox" name="creator_show"<?php echo ($cperm & PERMS_SHOW) ? ' checked="checked"' : '' ?> /></td>
  <td align="center"><input type="checkbox" name="creator_read"<?php echo ($cperm & PERMS_READ) ? ' checked="checked"' : '' ?> /></td>
  <td align="center"><input type="checkbox" name="creator_edit"<?php echo ($cperm & PERMS_EDIT) ? ' checked="checked"' : '' ?> /></td>
  <td align="center"><input type="checkbox" name="creator_delete"<?php echo ($cperm & PERMS_DELETE) ? ' checked="checked"' : '' ?> /></td>
</tr>

<!-- Spacer -->
<tr><td>&nbsp;</td></tr>

<!-- User Permissions -->
<tr valign="middle">
  <td class="header" align="left" width="25%">
    <?php echo Horde::img('user.gif', '', '', $registry->getParam('graphics', 'horde')) . '&nbsp;' . _("Individual Users") ?>
  </td>
  <td class="header" align="center" width="1%"><?php echo _("Show") ?></td>
  <td class="header" align="center" width="1%"><?php echo _("Read") ?></td>
  <td class="header" align="center" width="1%"><?php echo _("Edit") ?></td>
  <td class="header" align="center" width="1%"><?php echo _("Delete") ?></td>
  <td class="header" align="right" width="70%"></td>
</tr>
<?php foreach ($userperms as $user => $uperm) { if ($user != $owner) { ?>
<tr>
  <td class="light"><?php echo Auth::removeHook($user) ?><input type="hidden" name="u_names[<?php echo $user ?>]" value="<?php echo $user ?>" /></td>
  <td align="center"><input type="checkbox" name="u_show[<?php echo $user ?>]"<?php echo ($uperm & PERMS_SHOW) ? ' checked="checked"' : '' ?> /></td>
  <td align="center"><input type="checkbox" name="u_read[<?php echo $user ?>]"<?php echo ($uperm & PERMS_READ) ? ' checked="checked"' : '' ?> /></td>
  <td align="center"><input type="checkbox" name="u_edit[<?php echo $user ?>]"<?php echo ($uperm & PERMS_EDIT) ? ' checked="checked"' : '' ?> /></td>
  <td align="center"><input type="checkbox" name="u_delete[<?php echo $user ?>]"<?php echo ($uperm & PERMS_DELETE) ? ' checked="checked"' : '' ?> /></td>
</tr>
<?php } } ?>
<!-- New user row -->
<tr>
<?php if ($auth->hasCapability('list')): ?>
  <td class="light">
    <select name="u_names[||new]">
      <option value=""><?php echo _("Select a user to add") . ':'; ?></option>
    <?php foreach ($userList as $user) { if (!isset($userperms[$user])) { ?>
      <option value="<?php echo $user ?>"><?php echo Auth::removeHook($user) ?></option>
    <?php } } ?>
    </select>
  </td>
<?php else: ?>
  <td class="light"><input type="text" name="u_names[||new]" /></td>
<?php endif; ?>
  <td align="center"><input type="checkbox" name="u_show[||new]" /></td>
  <td align="center"><input type="checkbox" name="u_read[||new]" /></td>
  <td align="center"><input type="checkbox" name="u_edit[||new]" /></td>
  <td align="center"><input type="checkbox" name="u_delete[||new]" /></td>
</tr>

<!-- Spacer -->
<tr><td>&nbsp;</td></tr>

<!-- Group Permissions -->
<tr valign="middle">
  <td class="header" align="left" width="25%">
    <?php echo Horde::img('group.gif', '', '', $registry->getParam('graphics', 'horde')) . '&nbsp;' . _("Groups") ?>
  </td>
  <td class="header" align="center" width="1%"><?php echo _("Show") ?></td>
  <td class="header" align="center" width="1%"><?php echo _("Read") ?></td>
  <td class="header" align="center" width="1%"><?php echo _("Edit") ?></td>
  <td class="header" align="center" width="1%"><?php echo _("Delete") ?></td>
  <td class="header" align="right" width="70%">&nbsp;</td>
</tr>
<?php $groupperms = $perm->getGroupPermissions(); foreach ($groupperms as $group => $gperm): if (!$groups->exists($groups->getGroupName($group))) continue; ?>
<tr>
  <td class="light"><?php echo $groups->getGroupName($group) ?><input type="hidden" name="g_names[<?php echo $group ?>]" value="<?php echo $group ?>" /></td>
  <td align="center"><input type="checkbox" name="g_show[<?php echo $group ?>]"<?php echo ($gperm & PERMS_SHOW) ? ' checked="checked"' : '' ?> /></td>
  <td align="center"><input type="checkbox" name="g_read[<?php echo $group ?>]"<?php echo ($gperm & PERMS_READ) ? ' checked="checked"' : '' ?> /></td>
  <td align="center"><input type="checkbox" name="g_edit[<?php echo $group ?>]"<?php echo ($gperm & PERMS_EDIT) ? ' checked="checked"' : '' ?> /></td>
  <td align="center"><input type="checkbox" name="g_delete[<?php echo $group ?>]"<?php echo ($gperm & PERMS_DELETE) ? ' checked="checked"' : '' ?> /></td>
</tr>
<?php endforeach; ?>
<!-- New group row -->
<tr>
  <td class="light">
    <select name="g_names[||new]">
      <option value=""><?php echo _("Select a group to add") . ':'; ?></option>
    <?php foreach ($groupList as $gid => $group) { if (!array_key_exists($gid, $groupperms)) { ?>
      <option value="<?php echo htmlspecialchars($gid) ?>"><?php echo htmlspecialchars($group) ?></option>
    <?php } } ?>
    </select>
  </td>
  <td align="center"><input type="checkbox" name="g_show[||new]" /></td>
  <td align="center"><input type="checkbox" name="g_read[||new]" /></td>
  <td align="center"><input type="checkbox" name="g_edit[||new]" /></td>
  <td align="center"><input type="checkbox" name="g_delete[||new]" /></td>
</tr>

<tr>
 <td>&nbsp;</td>
</tr>

<tr>
 <td colspan="7">
  <input type="submit" class="button" value="<?php printf(_("Save %s"), $share->get('name')) ?>" />
<?php if (@count($children)): ?>
  <input type="submit" class="button" onclick="document.edit.actionID.value = 'editforminherit';" value="<?php echo _("Apply to Child Shares") ?>" />
<?php endif; ?>
 </td>
</tr>

</table>
</form>
<br />
