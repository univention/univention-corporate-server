<script type="text/javascript">
<!--
function resetHidden()
{
    var form = document.mapform;
    var tmp = '';
    for (i = 0; i < form.selectData.length; i++) {
        tmp += form.selectData[i].value;
        if (i < form.selectData.length - 1)
            tmp += "\t";
    }
    form.dataKeys.value = tmp;
    tmp = '';
    for (i = 0; i < form.selectApp.length; i++) {
        tmp += form.selectApp[i].value;
        if (i < form.selectApp.length - 1)
            tmp += "\t";
    }
    form.appKeys.value = tmp;
}

function addPair()
{
    var form = document.mapform;
    if (form.select1.selectedIndex >= 0 && form.select2.selectedIndex >= 0) {
        form.selectData[form.selectData.length] = new Option(form.select1[form.select1.selectedIndex].text, form.select1[form.select1.selectedIndex].value);
        form.selectApp[form.selectApp.length] = new Option(form.select2[form.select2.selectedIndex].text, form.select2[form.select2.selectedIndex].value);
        form.select1[form.select1.selectedIndex] = null;
        form.select2[form.select2.selectedIndex] = null;
    }
    resetHidden();
}

function removePair()
{
    var form = document.mapform;
    if (form.selectData.selectedIndex >= 0 || form.selectApp.selectedIndex >= 0) {
        form.select1[form.select1.length] = new Option(form.selectData[form.selectData.selectedIndex].text, form.selectData[form.selectData.selectedIndex].value);
        form.select2[form.select2.length] = new Option(form.selectApp[form.selectApp.selectedIndex].text, form.selectApp[form.selectApp.selectedIndex].value);
        form.selectData[form.selectData.selectedIndex] = null;
        form.selectApp[form.selectApp.selectedIndex] = null;
    }
    resetHidden();
}
//-->
</script>

<form method="post" name="mapform" action="data.php">
<?php echo Util::formInput() ?>
<input type="hidden" name="actionID" value="<?php echo (int)$next_step ?>" />
<input type="hidden" name="import_format" value="<?php echo htmlspecialchars(Util::getFormData('import_format')) ?>" />
<input type="hidden" name="import_step" value="<?php echo (int)$import_step ?>" />
<h1 class="header">
 <?php printf(_("Import, Step %d"), (int)$import_step) ?>
</h1>
<div class="item">
 <?php echo _("In the lists below select both, a field imported from the source file at the left, and the matching field available in your address book at the right. Then hit \"Add pair\" to mark them for the import. Once your are finished hit \"Next\".") ?><br /><br />
 <div class="leftFloat">
  <?php echo Horde::label('select1', _("Imported fields:")) ?> <br />
  <select id="select1" name="select1" size="10">
   <?php
   foreach ($_SESSION['import_data']['data'][0] as $key => $value):
   if (!isset($app_fields[$key])):
   ?>
   <option value="<?php echo htmlspecialchars($key) ?>"><?php echo ($_SESSION['import_data']['header']) ? htmlspecialchars($key) : htmlspecialchars($value) ?></option>
   <?php endif; endforeach; ?>
  </select>
 </div>
 <div class="leftFloat">
  <?php echo Horde::label('select2', _("Available fields:")) ?><br />
  <select id="select2" name="select2" size="10">
   <?php
   foreach ($app_fields as $key => $value):
   if (!isset($_SESSION['import_data']['data'][0][$key])):
   if (($key == 'alarm_time') || ($key == 'alarm_date')):
   if (!isset($_SESSION['import_data']['data'][0]['alarm'])):
   ?>
   <option value="<?php echo htmlspecialchars($key) ?>"><?php echo htmlspecialchars($value) ?></option>
   <?php
   endif;
   elseif ($key == 'alarm'):
   if (!(isset($_SESSION['import_data']['data'][0]['alarm_time']) &&
         isset($_SESSION['import_data']['data'][0]['alarm_date']))):
   ?>
   <option value="<?php echo htmlspecialchars($key) ?>"><?php echo htmlspecialchars($value) ?></option>
   <?php endif; else: ?>
   <option value="<?php echo htmlspecialchars($key) ?>"><?php echo htmlspecialchars($value) ?></option>
   <?php endif; endif; endforeach; ?>
  </select>
 </div>
 <br class="clear" />
 <input type="button" value="<?php echo _("Add pair") ?>" class="button" onclick="addPair()" />
 <br /><br />

 <?php echo _("To exclude a particular field form the import or to correct a wrong match select a field in the lists below and hit \"Remove pair\".") ?><br /><br />
 <?php echo _("Matching fields:") ?><br />

 <input type="hidden" name="dataKeys" />
 <input type="hidden" name="appKeys" />
 <input type="hidden" name="import_format" value="csv" />
 <label for="selectData" class="hidden"><?php echo _("Data") ?></label>
 <select id="selectData" name="selectData" size="10" onchange="document.mapform.selectApp[this.selectedIndex].selected=true">
  <?php
  $matching = array();
  foreach ($_SESSION['import_data']['data'][0] as $key => $value):
  if (isset($app_fields[$key])):
  $matching[] = array($key, $app_fields[$key]);
  ?>
  <option value="<?php echo htmlspecialchars($key) ?>"><?php echo ($_SESSION['import_data']['header']) ? htmlspecialchars($key) : htmlspecialchars($value) ?></option>
  <?php endif; endforeach; ?>
 </select>
 <label for="selectApp" class="hidden"><?php echo _("Application") ?></label>
 <select id="selectApp" name="selectApp" size="10" onchange="document.mapform.selectData[this.selectedIndex].selected=true">
  <?php foreach ($matching as $pair): ?>
  <option value="<?php echo htmlspecialchars($pair[0]) ?>"><?php echo htmlspecialchars($pair[1]) ?></option>
  <?php endforeach; ?>
 </select><br />
 <input type="button" value="<?php echo _("Remove pair") ?>" class="button" onclick="removePair()" /><br /><br />
 <input type="submit" value="<?php echo _("Next") ?>" class="button" />
</div>
</form>
<script type="text/javascript">
<!--
resetHidden();
//-->
</script>
