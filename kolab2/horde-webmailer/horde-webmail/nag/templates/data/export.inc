<form method="post" name="export" action="<?php echo Horde::downloadUrl(_("tasks.csv"), null, 'data.php') ?>">
<?php Util::pformInput() ?>
<input type="hidden" name="actionID" value="export" />

<h1 class="header">
 <?php echo _("Export Tasks") ?>
</h1>

<div class="headerbox">
 <p>
  <?php echo Horde::label('exportID', _("Select the export format:")) ?><br />
  <select id="exportID" name="exportID">
   <option value="<?php echo EXPORT_ICALENDAR ?>">iCalendar (vTodo)</option>
   <option value="<?php echo EXPORT_CSV ?>">CSV</option>
  </select>
 </p>

 <?php if (count($tasklists = Nag::listTasklists(false, PERMS_READ)) > 1): ?>
 <p>
  <?php echo Horde::label('exportList', _("Select the task list(s) to export from:")) ?><br />
  <select id="exportList" name="exportList[]" multiple="multiple">
    <?php foreach ($tasklists as $id => $tasklist) {
        printf('<option value="%s">%s</option>', htmlspecialchars($id), htmlspecialchars($tasklist->get('name'))) . "\n";
    } ?>
  </select>
 </p>
 <?php else: ?>
 <input type="hidden" name="exportList[]" value="<?php echo htmlspecialchars(Nag::getDefaultTasklist(PERMS_READ)) ?>" />
 <?php endif; ?>

 <p>
  <?php echo Horde::label('exportTasks', _("Select the task states to export:")) ?><br />
  <select id="exportTasks" name="exportTasks">
   <option value="1"><?php echo _("All tasks") ?></option>
   <option value="0"><?php echo _("Incomplete tasks") ?></option>
   <option value="3"><?php echo _("Future tasks") ?></option>
   <option value="2"><?php echo _("Completed tasks") ?></option>
  </select>
 </p>

 <input type="submit" value="<?php echo _("Export") ?>" class="button" />
</div>

</form>
