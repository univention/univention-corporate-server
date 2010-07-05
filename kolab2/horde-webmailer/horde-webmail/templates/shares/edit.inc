<form name="edit" method="post" action="<?php echo htmlspecialchars($_SERVER['PHP_SELF']) ?>">
<?php Util::pformInput() ?>
<input type="hidden" name="actionID" value="editform" />
<input type="hidden" name="cid" value="<?php echo htmlspecialchars($share->getId()) ?>" />
<?php if (!empty($app)): ?>
<input type="hidden" name="app" value="<?php echo htmlspecialchars($app) ?>" />
<?php endif; ?>
<table width="100%" cellspacing="0">
<tr valign="middle">
  <td width="100%" colspan="6" class="header">
    <span class="rightFloat">
      <a href="#" onclick="javascript:window.close();" style="cursor:pointer"><?php echo Horde::img('close.png', _("Close Window"), '', $registry->getImageDir('horde')) ?></a>
    </span>
    <?php echo Horde::img('perms.png', '', '', $registry->getImageDir('horde')) . '&nbsp;' . sprintf(_("Edit permissions for \"%s\""), htmlspecialchars($share->get('name'))); if (!empty($help)) echo '&nbsp;' . Help::link($app, $help) ?>
  </td>
</tr>
<tr><td>&nbsp;</td></tr>

<?php $owner = $share->get('owner'); ?>
<?php $userperms = $perm->getUserPermissions(); ?>

<!-- Ownership -->
<?php
if (isset($userperms[$owner])) {
    $operm = $userperms[$owner];
} else {
    $operm = PERMS_SHOW | PERMS_READ | PERMS_EDIT | PERMS_DELETE;
}
?>
<tr valign="middle">
  <td class="header leftAlign" colspan="6">
    <?php echo Horde::img('perms.png', '', '', $registry->getImageDir('horde')) . '&nbsp;' . _("Owner") ?>
  </td>
</tr>
<tr>
  <td class="light" colspan="6">
<?php if ($auth->hasCapability('list') && ($GLOBALS['conf']['auth']['list_users'] == 'list' || $GLOBALS['conf']['auth']['list_users'] == 'both')): ?>
    <label for="owner_select" class="hidden"><?php echo _("Owner:") ?></label>
    <select id="owner_select" name="owner_select">
      <option value=""><?php echo _("Select a new owner:") ?></option>
      <option value="<?php echo htmlspecialchars(Auth::removeHook($owner)) ?>" selected="selected"><?php echo htmlspecialchars(Auth::removeHook($owner)) ?></option>
<?php foreach ($userList as $user) { if ($user != Auth::removeHook($owner)) { ?>
      <option value="<?php echo htmlspecialchars($user) ?>"><?php echo htmlspecialchars(Auth::removeHook($user)) ?></option>
<?php } } ?>
    </select>
<?php else: ?>
    <label for="owner_input" class="hidden"><?php echo _("Owner:") ?></label>
    <input type="text" id="owner_input" name="owner_input" value="<?php echo htmlspecialchars(Auth::removeHook($owner)) ?>" />
<?php endif; ?>
  </td>
</tr>

<!-- Spacer -->
<tr><td>&nbsp;</td></tr>

<!-- Default Permissions -->
<tr valign="middle">
  <td class="header leftAlign" width="55%">
    <?php echo Horde::img('perms.png', '', '', $registry->getImageDir('horde')) . '&nbsp;' . _("All Authenticated Users") ?>
  </td>
  <td class="header" align="center"><?php echo _("Show") ?></td>
  <td class="header" align="center"><?php echo _("Read") ?></td>
  <td class="header" align="center"><?php echo _("Edit") ?></td>
  <td class="header" align="center"><?php echo _("Delete") ?></td>
  <td class="header rightAlign">&nbsp;</td>
</tr>
<?php $dperm = $perm->getDefaultPermissions(); ?>
<tr>
  <td class="light">&nbsp;</td>
  <td align="center">
    <input type="checkbox" id="default_show" name="default_show"<?php echo ($dperm & PERMS_SHOW) ? ' checked="checked"' : '' ?> />
    <label for="default_show" class="hidden"><?php echo _("Show") ?></label>
  </td>
  <td align="center">
    <input type="checkbox" id="default_read" name="default_read"<?php echo ($dperm & PERMS_READ) ? ' checked="checked"' : '' ?> />
    <label for="default_read" class="hidden"><?php echo _("Read") ?></label>
  </td>
  <td align="center">
    <input type="checkbox" id="default_edit" name="default_edit"<?php echo ($dperm & PERMS_EDIT) ? ' checked="checked"' : '' ?> />
    <label for="default_edit" class="hidden"><?php echo _("Edit") ?></label>
  </td>
  <td align="center">
    <input type="checkbox" id="default_delete" name="default_delete"<?php echo ($dperm & PERMS_DELETE) ? ' checked="checked"' : '' ?> />
    <label for="default_delete" class="hidden"><?php echo _("Delete") ?></label>
  </td>
</tr>

<!-- Spacer -->
<tr><td>&nbsp;</td></tr>

<!-- Guest Permissions -->
<tr valign="middle">
  <td class="header leftAlign">
    <?php echo _("Guest Permissions") ?>
  </td>
  <td class="header" align="center"><?php echo _("Show") ?></td>
  <td class="header" align="center"><?php echo _("Read") ?></td>
  <td class="header" align="center"><?php echo _("Edit") ?></td>
  <td class="header" align="center"><?php echo _("Delete") ?></td>
  <td class="header rightAlign">&nbsp;</td>
</tr>
<?php $gperm = $perm->getGuestPermissions(); ?>
<tr>
  <td class="light">&nbsp;</td>
  <td align="center">
    <input type="checkbox" id="guest_show" name="guest_show"<?php echo ($gperm & PERMS_SHOW) ? ' checked="checked"' : '' ?> />
    <label for="guest_show" class="hidden"><?php echo _("Show") ?></label>
  </td>
  <td align="center">
    <input type="checkbox" id="guest_read" name="guest_read"<?php echo ($gperm & PERMS_READ) ? ' checked="checked"' : '' ?> />
    <label for="guest_read" class="hidden"><?php echo _("Read") ?></label>
  </td>
  <td align="center">
    <input type="checkbox" id="guest_edit" name="guest_edit"<?php echo ($gperm & PERMS_EDIT) ? ' checked="checked"' : '' ?> />
    <label for="guest_edit" class="hidden"><?php echo _("Edit") ?></label>
  </td>
  <td align="center">
    <input type="checkbox" id="guest_delete" name="guest_delete"<?php echo ($gperm & PERMS_DELETE) ? ' checked="checked"' : '' ?> />
    <label for="guest_delete" class="hidden"><?php echo _("Delete") ?></label>
  </td>
</tr>

<!-- Spacer -->
<tr><td>&nbsp;</td></tr>

<!-- Creator Permissions -->
<tr valign="middle">
  <td class="header leftAlign">
    <?php echo Horde::img('user.png', '', '', $registry->getImageDir('horde')) . '&nbsp;' . _("Object Creator") ?>
  </td>
  <td class="header" align="center"><?php echo _("Show") ?></td>
  <td class="header" align="center"><?php echo _("Read") ?></td>
  <td class="header" align="center"><?php echo _("Edit") ?></td>
  <td class="header" align="center"><?php echo _("Delete") ?></td>
  <td class="header rightAlign"></td>
</tr>
<?php $cperm = $perm->getCreatorPermissions(); ?>
<tr>
  <td class="light">&nbsp;</td>
  <td align="center">
    <input type="checkbox" id="creator_show" name="creator_show"<?php echo ($cperm & PERMS_SHOW) ? ' checked="checked"' : '' ?> />
    <label for="creator_show" class="hidden"><?php echo _("Show") ?></label>
  </td>
  <td align="center">
    <input type="checkbox" id="creator_read" name="creator_read"<?php echo ($cperm & PERMS_READ) ? ' checked="checked"' : '' ?> />
    <label for="creator_read" class="hidden"><?php echo _("Read") ?></label>
  </td>
  <td align="center">
    <input type="checkbox" id="creator_edit" name="creator_edit"<?php echo ($cperm & PERMS_EDIT) ? ' checked="checked"' : '' ?> />
    <label for="creator_edit" class="hidden"><?php echo _("Edit") ?></label>
  </td>
  <td align="center">
    <input type="checkbox" id="creator_delete" name="creator_delete"<?php echo ($cperm & PERMS_DELETE) ? ' checked="checked"' : '' ?> />
    <label for="creator_delete" class="hidden"><?php echo _("Delete") ?></label>
  </td>
</tr>

<!-- Spacer -->
<tr><td>&nbsp;</td></tr>

<!-- User Permissions -->
<tr valign="middle">
  <td class="header leftAlign">
    <?php echo Horde::img('user.png', '', '', $registry->getImageDir('horde')) . '&nbsp;' . _("Individual Users") ?>
  </td>
  <td class="header" align="center"><?php echo _("Show") ?></td>
  <td class="header" align="center"><?php echo _("Read") ?></td>
  <td class="header" align="center"><?php echo _("Edit") ?></td>
  <td class="header" align="center"><?php echo _("Delete") ?></td>
  <td class="header rightAlign"></td>
</tr>
<?php
foreach ($userperms as $user => $uperm) {
    if ($user != $owner) {
        $user = Auth::removeHook($user);
?>
<tr>
  <td class="light"><?php echo htmlspecialchars($user) ?><input type="hidden" name="u_names[<?php echo htmlspecialchars($user) ?>]" value="<?php echo htmlspecialchars($user) ?>" /></td>
  <td align="center">
    <input type="checkbox" id="u_show_<?php echo str_replace('@', '_', htmlspecialchars($user)) ?>" name="u_show[<?php echo htmlspecialchars($user) ?>]"<?php echo ($uperm & PERMS_SHOW) ? ' checked="checked"' : '' ?> />
    <label for="u_show_<?php echo str_replace('@', '_', htmlspecialchars($user)) ?>" class="hidden"><?php echo _("Show") ?></label>
  </td>
  <td align="center">
    <input type="checkbox" id="u_read_<?php echo str_replace('@', '_', htmlspecialchars($user)) ?>" name="u_read[<?php echo htmlspecialchars($user) ?>]"<?php echo ($uperm & PERMS_READ) ? ' checked="checked"' : '' ?> />
    <label for="u_read_<?php echo str_replace('@', '_', htmlspecialchars($user)) ?>" class="hidden"><?php echo _("Read") ?></label>
  </td>
  <td align="center">
    <input type="checkbox" id="u_edit_<?php echo str_replace('@', '_', htmlspecialchars($user)) ?>" name="u_edit[<?php echo htmlspecialchars($user) ?>]"<?php echo ($uperm & PERMS_EDIT) ? ' checked="checked"' : '' ?> />
    <label for="u_edit_<?php echo str_replace('@', '_', htmlspecialchars($user)) ?>" class="hidden"><?php echo _("Edit") ?></label>
  </td>
  <td align="center">
    <input type="checkbox" id="u_delete_<?php echo str_replace('@', '_', htmlspecialchars($user)) ?>" name="u_delete[<?php echo htmlspecialchars($user) ?>]"<?php echo ($uperm & PERMS_DELETE) ? ' checked="checked"' : '' ?> />
    <label for="u_delete_<?php echo str_replace('@', '_', htmlspecialchars($user)) ?>" class="hidden"><?php echo _("Delete") ?></label>
  </td>
</tr>
<?php } } ?>

<!-- New user rows -->
<?php if ($auth->hasCapability('list') && ($GLOBALS['conf']['auth']['list_users'] == 'list' || $GLOBALS['conf']['auth']['list_users'] == 'both')): ?>
<tr>
  <td class="light">
    <label for="u_names_new_select" class="hidden"><?php echo _("Select a user to add:") ?></label>
    <select id="u_names_new_select" name="u_names[||new_select]">
      <option value=""><?php echo _("Select a user to add:") ?></option>
<?php
foreach ($userList as $user) {
    if (!isset($userperms[Auth::addHook($user)]) &&
        $user != Auth::removeHook($owner)) {
?>
      <option value="<?php echo htmlspecialchars($user) ?>"><?php echo htmlspecialchars($user) ?></option>
<?php } } ?>
    </select>
  </td>
  <td align="center">
    <input type="checkbox" id="u_show_new_select" name="u_show[||new_select]" />
    <label for="u_show_new_select" class="hidden"><?php echo _("Show") ?></label>
  </td>
  <td align="center">
    <input type="checkbox" id="u_read_new_select" name="u_read[||new_select]" />
    <label for="u_read_new_select" class="hidden"><?php echo _("Read") ?></label>
  </td>
  <td align="center">
    <input type="checkbox" id="u_edit_new_select" name="u_edit[||new_select]" />
    <label for="u_edit_new_select" class="hidden"><?php echo _("Edit") ?></label>
  </td>
  <td align="center">
    <input type="checkbox" id="u_delete_new_select" name="u_delete[||new_select]" />
    <label for="u_delete_new_select" class="hidden"><?php echo _("Delete") ?></label>
  </td>
</tr>
<?php endif; ?>
<?php if (!$auth->hasCapability('list') || ($GLOBALS['conf']['auth']['list_users'] == 'input' || $GLOBALS['conf']['auth']['list_users'] == 'both')): ?>
<tr>
  <td class="light">
<?php if ($auth->hasCapability('list') && $GLOBALS['conf']['auth']['list_users'] == 'both'): ?>
    <?php echo _("Or enter a user name:") ?>
<?php endif; ?>
    <label for="u_names_new_input" class="hidden"><?php echo _("User to add:") ?></label>
    <input type="text" id="u_names_new_input" name="u_names[||new_input]" />
  </td>
  <td align="center">
    <input type="checkbox" id="u_show_new_input" name="u_show[||new_input]" />
    <label for="u_show_new_input" class="hidden"><?php echo _("Show") ?></label>
  </td>
  <td align="center">
    <input type="checkbox" id="u_read_new_input" name="u_read[||new_input]" />
    <label for="u_read_new_input" class="hidden"><?php echo _("Read") ?></label>
  </td>
  <td align="center">
    <input type="checkbox" id="u_edit_new_input" name="u_edit[||new_input]" />
    <label for="u_edit_new_input" class="hidden"><?php echo _("Edit") ?></label>
  </td>
  <td align="center">
    <input type="checkbox" id="u_delete_new_input" name="u_delete[||new_input]" />
    <label for="u_delete_new_input" class="hidden"><?php echo _("Delete") ?></label>
  </td>
</tr>
<?php endif; ?>

<!-- Spacer -->
<tr><td>&nbsp;</td></tr>

<!-- Group Permissions -->
<tr valign="middle">
  <td class="header leftAlign">
    <?php echo Horde::img('group.png', '', '', $registry->getImageDir('horde')) . '&nbsp;' . _("Groups") ?>
  </td>
  <td class="header" align="center"><?php echo _("Show") ?></td>
  <td class="header" align="center"><?php echo _("Read") ?></td>
  <td class="header" align="center"><?php echo _("Edit") ?></td>
  <td class="header" align="center"><?php echo _("Delete") ?></td>
  <td class="header rightAlign">&nbsp;</td>
</tr>
<?php $groupperms = $perm->getGroupPermissions(); foreach ($groupperms as $group => $gperm): if (!$groups->exists($groups->getGroupName($group))) continue; ?>
<tr>
  <td class="light"><?php echo htmlspecialchars($groups->getGroupName($group)) ?><input type="hidden" name="g_names[<?php echo htmlspecialchars($group) ?>]" value="<?php echo htmlspecialchars($group) ?>" /></td>
  <td align="center">
    <input type="checkbox" id="g_show_<?php echo htmlspecialchars($group) ?>" name="g_show[<?php echo htmlspecialchars($group) ?>]"<?php echo ($gperm & PERMS_SHOW) ? ' checked="checked"' : '' ?> />
    <label for="g_show_<?php echo htmlspecialchars($group) ?>" class="hidden"><?php echo _("Show") ?></label>
  </td>
  <td align="center">
    <input type="checkbox" id="g_read_<?php echo htmlspecialchars($group) ?>" name="g_read[<?php echo htmlspecialchars($group) ?>]"<?php echo ($gperm & PERMS_READ) ? ' checked="checked"' : '' ?> />
    <label for="g_read_<?php echo htmlspecialchars($group) ?>" class="hidden"><?php echo _("Read") ?></label>
  </td>
  <td align="center">
    <input type="checkbox" id="g_edit_<?php echo htmlspecialchars($group) ?>" name="g_edit[<?php echo htmlspecialchars($group) ?>]"<?php echo ($gperm & PERMS_EDIT) ? ' checked="checked"' : '' ?> />
    <label for="g_edit_<?php echo htmlspecialchars($group) ?>" class="hidden"><?php echo _("Edit") ?></label>
  </td>
  <td align="center">
    <input type="checkbox" id="g_delete_<?php echo htmlspecialchars($group) ?>" name="g_delete[<?php echo htmlspecialchars($group) ?>]"<?php echo ($gperm & PERMS_DELETE) ? ' checked="checked"' : '' ?> />
    <label for="g_delete_<?php echo htmlspecialchars($group) ?>" class="hidden"><?php echo _("Delete") ?></label>
  </td>
</tr>
<?php endforeach; ?>
<!-- New group row -->
<tr>
  <td class="light">
    <label for="g_names_new" class="hidden"><?php echo _("Select a group to add:") ?></label>
    <select id="g_names_new" name="g_names[||new]">
      <option value=""><?php echo _("Select a group to add:") ?></option>
    <?php foreach ($groupList as $gid => $group) { if (empty($groupperms[$gid])) { ?>
      <option value="<?php echo htmlspecialchars($gid) ?>"><?php echo htmlspecialchars($group) ?></option>
    <?php } } ?>
    </select>
  </td>
  <td align="center">
    <input type="checkbox" id="g_show_new" name="g_show[||new]" />
    <label for="g_show_new" class="hidden"><?php echo _("Show") ?></label>
  </td>
  <td align="center">
    <input type="checkbox" id="g_read_new" name="g_read[||new]" />
    <label for="g_read_new" class="hidden"><?php echo _("Read") ?></label>
  </td>
  <td align="center">
    <input type="checkbox" id="g_edit_new" name="g_edit[||new]" />
    <label for="g_edit_new" class="hidden"><?php echo _("Edit") ?></label>
  </td>
  <td align="center">
    <input type="checkbox" id="g_delete_new" name="g_delete[||new]" />
    <label for="g_delete_new" class="hidden"><?php echo _("Delete") ?></label>
  </td>
</tr>

<tr>
 <td>&nbsp;</td>
</tr>

<tr>
 <td colspan="7">
  <input type="submit" class="button" value="<?php echo htmlspecialchars(sprintf(_("Save \"%s\""), $share->get('name'))) ?>" />
  <input type="submit" class="button" name="save_and_finish" value="<?php echo htmlspecialchars(_("Save and Finish")) ?>" />
 </td>
</tr>

</table>
</form>
<br />
