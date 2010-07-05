<h1 class="header">
 <?php echo _("Manage Task Lists") ?>
</h1>

<?php if (!$prefs->isLocked('default_tasklist')): ?>
<div id="tasklist-list-buttons">
 <form method="get" action="create.php">
<?php echo Util::formInput() ?>
  <input type="submit" class="button" value="<?php echo _("Create a new Task List") ?>" />
 </form>
</div>
<?php endif; ?>

<table summary="<?php echo _("Task List List") ?>" cellspacing="0" id="tasklist-list" class="striped sortable">
 <thead>
  <tr>
   <th class="sortdown"><?php echo _("Task List") ?></th>
   <th class="tasklist-list-url nosort"><?php echo _("Display URL") ?></th>
   <th class="tasklist-list-url nosort"><?php echo _("Subscription URL") ?></th>
   <th class="tasklist-list-icon nosort" colspan="<?php echo empty($conf['share']['no_sharing']) ? 3 : 2 ?>">&nbsp;</th>
  </tr>
 </thead>

 <tbody>
<?php foreach (array_keys($sorted_tasklists) as $tasklist_id): ?>
 <?php $tasklist = $tasklists[$tasklist_id] ?>
  <tr>
   <td><?php echo htmlspecialchars($tasklist->get('name')) ?></td>
   <td><?php $url = Util::addParameter($display_url_base, 'display_cal', $tasklist->getName(), false) ?><a href="<?php echo htmlspecialchars($url) ?>" title="<?php echo _("Click or copy this URL to display this task list") ?>" target="_blank"><?php echo htmlspecialchars(shorten_url($url)) ?></a></td>
   <td><?php $url = $webdav ? $subscribe_url_base . $tasklist->get('owner') . '/' . $tasklist->getName() . '.ics' : Util::addParameter($subscribe_url_base, 't', $tasklist->getName(), false) ?><a href="<?php echo htmlspecialchars($url) ?>" title="<?php echo _("Click or copy this URL to display this task list") ?>" target="_blank"><?php echo htmlspecialchars(shorten_url($url)) ?></a></td>
   <td><a href="<?php echo Util::addParameter($edit_url_base, 't', $tasklist->getName()) ?>" title="<?php echo _("Edit") ?>"><?php echo $edit_img ?></a></td>
<?php if (empty($conf['share']['no_sharing'])): ?>
   <td><a onclick="return !popup(this.href);" href="<?php echo Util::addParameter($perms_url_base, 'share', $tasklist->getName()) ?>" target="_blank" title="<?php echo _("Change Permissions") ?>"><?php echo $perms_img ?></a></td>
<?php endif; ?>
   <td><a href="<?php echo Util::addParameter($delete_url_base, 't', $tasklist->getName()) ?>" title="<?php echo _("Delete") ?>"><?php echo $delete_img ?></a></td>
  </tr>
<?php endforeach; ?>
 </tbody>
</table>
