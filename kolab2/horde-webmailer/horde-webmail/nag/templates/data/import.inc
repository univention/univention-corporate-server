<form method="post" name="import_form" enctype="multipart/form-data" action="data.php">
<?php Util::pformInput() ?>
<input type="hidden" name="actionID" value="<?php echo htmlspecialchars($next_step) ?>" />
<input type="hidden" name="import_step" value="<?php echo (int)$import_step ?>" />

<h1 class="header">
 <?php printf(_("Import Tasks, Step %d"), (int)$import_step) ?>
</h1>

<div class="headerbox">
 <p>
  <?php echo Horde::label('import_format', _("Select the format of the source file:")) ?><br />
  <select id="import_format" name="import_format">
   <option value="csv">CSV</option>
   <option value="vtodo">iCalendar (vTodo)</option>
  </select>
 </p>

<?php if (!$prefs->isLocked('default_tasklist') && count($tasklists = Nag::listTasklists(false, PERMS_EDIT)) > 1): ?>
 <p>
  <?php echo Horde::label('tasklist_target', _("Which tasklist should the tasks be added to?")) ?><br />
  <select id="tasklist_target" name="tasklist_target">
  <?php
  $default = Nag::getDefaultTasklist(PERMS_EDIT);
  foreach ($tasklists as $id => $tasklist) {
      $sel = ($id == $default) ? ' selected="selected"' : '';
      printf('<option value="%s"%s>%s</option>',
             htmlspecialchars($id), $sel, htmlspecialchars($tasklist->get('name'))) . "\n";
  } ?>
  </select>
 </p>
<?php else: ?>
 <input type="hidden" name="tasklist_target" value="<?php echo htmlspecialchars(Nag::getDefaultTasklist(PERMS_EDIT)) ?>" />
<?php endif; ?>
 <p>
  <?php echo Horde::label('import_file', _("Select the file to import:")) ?><br />
  <input type="file" id="import_file" name="import_file" size="40" />
 </p>
 <input type="submit" value="<?php echo _("Next") ?>" class="button" />
</div>

</form>
