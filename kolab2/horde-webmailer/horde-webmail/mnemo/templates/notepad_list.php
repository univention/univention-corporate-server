<h1 class="header">
 <?php echo _("Manage Notepads") ?>
</h1>

<?php if (!$prefs->isLocked('default_notepad')): ?>
<div id="notepad-list-buttons">
 <form method="get" action="create.php">
<?php echo Util::formInput() ?>
  <input type="submit" class="button" value="<?php echo _("Create a new Notepad") ?>" />
 </form>
</div>
<?php endif; ?>

<table summary="<?php echo _("Notepad List") ?>" cellspacing="0" id="notepad-list" class="striped sortable">
 <thead>
  <tr>
   <th class="sortdown"><?php echo _("Notepad") ?></th>
   <th class="notepad-list-icon nosort" colspan="<?php echo empty($conf['share']['no_sharing']) ? 3 : 2 ?>">&nbsp;</th>
  </tr>
 </thead>

 <tbody>
<?php foreach (array_keys($sorted_notepads) as $notepad_id): ?>
 <?php $notepad = $notepads[$notepad_id] ?>
  <tr>
   <td><?php echo htmlspecialchars($notepad->get('name')) ?></td>
   <td><a href="<?php echo Util::addParameter($edit_url_base, 'n', $notepad->getName()) ?>" title="<?php echo _("Edit") ?>"><?php echo $edit_img ?></a></td>
<?php if (empty($conf['share']['no_sharing'])): ?>
   <td><a onclick="return !popup(this.href);" href="<?php echo Util::addParameter($perms_url_base, 'share', $notepad->getName()) ?>" target="_blank" title="<?php echo _("Change Permissions") ?>"><?php echo $perms_img ?></a></td>
<?php endif; ?>
   <td><a href="<?php echo Util::addParameter($delete_url_base, 'n', $notepad->getName()) ?>" title="<?php echo _("Delete") ?>"><?php echo $delete_img ?></a></td>
  </tr>
<?php endforeach; ?>
 </tbody>
</table>
