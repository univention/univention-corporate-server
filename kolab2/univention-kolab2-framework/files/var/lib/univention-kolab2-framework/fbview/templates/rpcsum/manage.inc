<?php echo _("Your remote servers:") ?><br />
<select name="server" class="fixed" onchange="javascript:newChoice()">
  <option value="-1"><?php echo _("Select a server") ?></option>
<?php for ($i = 0; $i < count($rpc_servers); $i++): ?>
  <option value="<?php echo $i ?>"><?php echo $rpc_servers[$i]['url'] ?></option>
<?php endfor; ?>
</select>
</td></tr>

<noscript>
</table></td></tr>
<tr>
  <td valign="middle">
    <br />
    <input type="submit" name="edit" class="button" value="<?php echo _("Edit") ?>" />
    <input type="submit" name="delete" class="button" value="<?php echo _("Delete") ?>" />
    <br />&nbsp;
  </td>
</tr>

<tr><td class="item"><table border="0">
</noscript>

<tr valign="top"><td class="item">

<input type="hidden" name="edit_server" value="" />
<?php echo _("Remote URL (http://www.example.com/horde):") ?><br />
<input type="text" name="url" size="30" maxlength="60" class="fixed" /><br />

<?php echo _("Username:") ?><br />
<input type="text" name="user" size="30" maxlength="60" class="fixed" /><br />

<?php echo _("Password:") ?><br />
<input type="password" name="passwd" size="30" maxlength="60" class="fixed" /><br />

</td></tr></table></td></tr></table>

<br />
<table border="0" align="center" width="100%" cellspacing="0" cellpadding="0"><tr><td nowrap="nowrap">
  <input type="submit" name="save" class="button" onclick="document.prefs.actionID.value=<?php echo RPC_SAVE ?>;return true" value="<?php echo $actionID == RPC_EDIT ? _("Change") : _("Create") ?>" />&nbsp;
<script language="JavaScript" type="text/javascript">
document.write('<input type="submit" name="delete" class="button" onclick="document.prefs.actionID.value=<?php echo RPC_DELETE ?>" value="<?php echo _("Delete") ?>" />&nbsp;');
</script>
  <input type="submit" name="new" class="button" onclick="clearForm();document.prefs.save.value='<?php echo _("Create") ?>';" value="<?php echo _("Reset") ?>" />&nbsp;
  <input type="submit" name="back" class="button" onclick="cancelSubmit=true;document.location.href='<?php echo Horde::applicationUrl('services/prefs.php', true) ?>'" value="<?php echo _("Return to Options") ?>" />
</td></tr></table>

</form>
