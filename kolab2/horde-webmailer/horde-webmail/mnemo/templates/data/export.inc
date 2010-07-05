<br />
<h1 class="header"><?php echo _("Export Notes") ?></h1>

<form method="post" name="export" action="<?php echo Horde::downloadUrl(_("notes.csv"), null, Horde::applicationUrl('data.php')) ?>">
<input type="hidden" name="actionID" value="export" />

<div class="item" style="padding:.5em">
 <p>
  <?php echo Horde::label('exportID', _("Select the export format:")) ?><br />
  <select id="exportID" name="exportID">
   <option value="<?php echo EXPORT_CSV ?>">CSV</option>
  </select>
 </p>

 <p>
  <input type="submit" value="<?php echo _("Export") ?>" class="button" />
 </p>
</div>

</form>
