<form method="post" name="export" action="<?php echo Horde::downloadUrl(_("contacts.csv"), null, Horde::applicationUrl('data.php')) ?>">
<?php echo Util::formInput() ?>
<input type="hidden" name="actionID" value="export" />

<h1 class="header">
 <?php echo _("Export Address Book") ?>
</h1>

<div class="item">
 <?php echo Horde::label('exportID', _("Select the export format:")) ?><br />
 <select name="exportID" id="exportID">
  <option value="<?php echo EXPORT_CSV ?>"><?php echo _("Comma separated values") ?></option>
  <option value="<?php echo EXPORT_OUTLOOKCSV ?>"><?php echo _("Comma separated values (Microsoft Outlook)") ?></option>
  <option value="<?php echo EXPORT_TSV ?>"><?php echo _("Tab separated values") ?></option>
  <option value="<?php echo EXPORT_VCARD ?>"><?php echo _("vCard") ?></option>
  <option value="ldif"><?php echo _("LDIF Address Book") ?></option>
 </select><br />

<?php if ($actionID == 'select' && Util::getFormData('objectkeys')): ?>
 <br />
 <input type="radio" name="selected" id="selected1" value="1" checked="checked" />
 <?php echo Horde::label('selected1', _("Export only the selected contacts.")) ?>
<?php foreach (Util::getFormData('objectkeys') as $key => $value): ?>
 <input type="hidden" name="objectkeys[<?php echo htmlspecialchars($key) ?>]" value="<?php echo htmlspecialchars($value) ?>" />
<?php endforeach; ?>
 <br />
 <input type="radio" name="selected" id="selected0" value="0" />
 <?php echo Horde::label('selected0', _("Export the following address book completely.")) ?>
 <br />
<?php endif; ?>
<?php if (count($source_options) > 1): ?>
 <br />
 <?php echo Horde::label('source', _("Select the address book to export from:")) ?><br />
 <select name="source" id="source">
  <?php echo implode('', $source_options) ?>
 </select><br />
<?php else: ?>
 <input type="hidden" name="source" value="<?php echo htmlspecialchars($unique_source) ?>" />
<?php endif; ?>
 <br />

 <input type="submit" value="<?php echo _("Export") ?>" class="button" />
</div>
</form>
