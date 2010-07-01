<?php

if (!$prefs->isLocked('imsp_opt')):
    global $cfgSources;
    $source_count = 0;
    $imsp_souces = array();

    foreach ($cfgSources as $key => $value) {
        if (($value['type'] == 'imsp') && (!$value['params']['is_root']) &&
            (strpos($value['params']['my_rights'], 'd') != false)) {
            $source_count++;
            $imsp_sources[$key] = $value;
        }
    }

?>
<script type="text/javascript">
<!--
function showAlert()
{
    if (document.prefs.imsp_books_delete.value != 'none') {
        window.alert('<?php echo addslashes(_("Once you save this option page, the address book will be permanently deleted. If this is not what you want, then you must change your selection to \"None\".")) ?>');
    }
}
//-->
</script>
<table>
 <tr>
  <td><?php echo Horde::label('imsp_books_delete', _(" Delete IMSP Address Book")) ?></td>
  <td>
   <select id="imsp_books_delete" name="imsp_books_delete" style="width:200px" onchange="showAlert();">
    <option value="none"><?php echo _("none") ?></option>
    <?php foreach ($imsp_sources as $key => $value): ?>
    <option value="<?php echo htmlspecialchars($key) ?>"><?php echo htmlspecialchars($value['title']) ?></option>
    <?php endforeach ?>
   </select>
  </td>
 </tr>
 <tr>
  <td><?php echo Horde::label('imsp_name', _(" Add an IMSP Address Book")) ?></td>
  <td><input id="imsp_name" name="imsp_name" type="text" style="width:200px" /></td>
 </tr>
</table>
<?php endif; ?>
