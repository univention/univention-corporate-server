<form method="post" name="import_form" enctype="multipart/form-data" action="data.php">
<?php Util::pformInput() ?>
<input type="hidden" name="actionID" value="<?php echo htmlspecialchars($next_step) ?>" />
<input type="hidden" name="import_step" value="<?php echo (int)$import_step ?>" />

<h1 class="header">
 <?php printf(_("Import Address Book, Step %d"), (int)$import_step) ?>
</h1>

<div class="item">
 <?php echo Horde::label('import_format', _("Select the format of the source file:")) ?><br />
 <select name="import_format" id="import_format">
  <option value="csv"><?php echo _("Comma separated values") ?></option>
  <option value="tsv"><?php echo _("Tab separated values") ?></option>
  <option value="vcard"><?php echo _("vCard") ?></option>
  <option value="mulberry"><?php echo _("Mulberry Address Book") ?></option>
  <option value="pine"><?php echo _("Pine Address Book") ?></option>
  <option value="ldif"><?php echo _("LDIF Address Book") ?></option>
 </select><br />

 <input type="checkbox" align="middle" name="purge" id="purge" value="1" />
 <?php echo Horde::label('purge', _("Replace existing address book with the imported one? <strong>Warning: This deletes all entries in your current address book.</strong>")) ?>
 <br />

<?php if (count($dest_options) > 1): ?>
 <br />
 <?php echo Horde::label('dest', _("Select the address book to import to:")) ?><br />
 <select name="dest" id="dest">
  <?php echo implode('', $dest_options) ?>
 </select><br />
<?php else: ?>
 <input type="hidden" name="dest" value="<?php echo htmlspecialchars($unique_dest) ?>" />
<?php endif; ?>
 <br />

 <?php echo Horde::label('charset', _("Select the charset of the source file:")) ?><br />
 <select name="charset" id="charset" style="direction: ltr">
<?php foreach ($charsets as $charset => $charset_name): ?>
  <option value="<?php echo htmlspecialchars($charset) ?>"<?php if ($charset == $my_charset) echo ' selected="selected"' ?>><?php echo htmlspecialchars($charset_name) ?></option>
<?php endforeach; ?>
 </select>
 <br /><br />

 <?php echo Horde::label('import_file', _("Select the file to import:")) ?><br />
 <input type="file" name="import_file" id="import_file" size="40" /><br /><br />
 <input type="submit" value="<?php echo _("Next") ?>" class="button" />
</div>
</form>

<br class="spacer" />
