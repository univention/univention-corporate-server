<input type="hidden" name="remote_action" value="add">

<script language="JavaScript" type="text/javascript">
<!--
function deleteCal(id)
{
    document.prefs.remote_action.value = 'delete';
    document.prefs.remote_url.value = id;
    document.prefs.submit();
}
-->
</script>

<table border="0" cellpadding="1" cellspacing="2">
<tr>
  <td>&nbsp;</td>
  <td><b><?php echo _("Name") ?></b></td>
  <td><b><?php echo _("Location") ?></b></td>
</tr>

<?php $cals = unserialize($prefs->getValue('remote_cals')); foreach ($cals as $key => $cal): ?>
<tr>
  <td class="text"><a onclick="deleteCal('<?php echo $cal['url'] ?>'); return false;"><?php echo Horde::img('delete.gif', _("Delete"), '', $registry->getParam('graphics', 'horde')) ?></a></td>
  <td class="text"><?php echo $cal['name'] ?></td>
  <td class="text"><?php echo $cal['url'] ?></td>
</tr>
<?php endforeach; ?>

<tr>
 <td>&nbsp;</td>
</tr>

<tr>
 <td colspan="3">
  <b><?php echo _("Add a new Remote Calendar") ?></b>
 </td>
</tr>

<tr>
 <td colspan="3">
  <table border="0" cellpadding="1" cellspacing="1">
   <tr>
    <td align="right">
     <b><?php echo _("Name") ?></b>&nbsp;&nbsp;
    </td>
    <td>
     <input type="text" name="remote_name" value="">
    </td>
   </tr>
   <tr>
    <td align="right">
     <b><?php echo _("Location") ?></b>&nbsp;&nbsp;
    </td>
    <td>
     <input size="50" type="text" name="remote_url" value="">
    </td>
   </tr>
  </table>
 </td>
</tr>

</table>
