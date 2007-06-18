<script language="JavaScript" type="text/javascript">
<!--

function validate_update()
{
    if (document.updateuser.user_name.value == "") {
        document.updateuser.user_name.focus();
        alert('<?php echo _("You must specify the username to add.") ?>');
        return false;
    } else if (document.updateuser.user_pass_1.value != document.updateuser.user_pass_2.value) {
        document.updateuser.user_pass_1.value = "";
        document.updateuser.user_pass_2.value = "";
        document.updateuser.user_pass_1.focus();
        alert('<?php echo _("Passwords must match.") ?>');
        return false;
    }

    return true;
}

//-->
</script>

<form name="updateuser" method="post">
<input type="hidden" name="form" value="update">
<input type="hidden" name="user_name" value="<?php echo htmlspecialchars($f_user_name) ?>" />
<table border="0" cellspacing="0" cellpadding="2" width="100%">
<tr>
  <td align="left" class="header" colspan="2">
    <b><?php printf(_("Update %s"), $f_user_name) ?></b>
  </td>
</tr>
<?php if ($auth->hasCapability('update')): ?>
<tr><td width="1%" nowrap="nowrap" align="right" class="light"><?php echo _("New Username (optional)") ?></td><td class="item0"><input type="text" name="user_name2" value="<?php echo htmlspecialchars($f_user_name) ?>" /></td></tr>
<tr><td nowrap="nowrap" align="right" class="light"><?php echo _("Password") ?></td><td class="item1"><input type="password" name="user_pass_1" /></td></tr>
<tr><td nowrap="nowrap" align="right" class="light"><?php echo _("Confirm Password") ?></td><td class="item0"><input type="password" name="user_pass_2" /></td></tr>
<?php endif; ?>
<tr><td nowrap="nowrap" align="right" class="light"><?php echo _("Full Name") ?></td><td class="item1"><input type="text" name="user_fullname" value="<?php echo htmlspecialchars($identity->getValue('fullname')) ?>" /></td></tr>
<tr><td nowrap="nowrap" align="right" class="light"><?php echo _("Email Address") ?></td><td class="item0"><input type="text" name="user_email"  value="<?php echo htmlspecialchars($identity->getValue('from_addr')) ?>" /></td></tr>
<tr>
  <td class="smallheader" align="left" colspan="2">
    <input type="submit" class="button" name="submit" onclick="return validate_update();" value="<?php echo _("Update user") ?>" />
    <input type="reset" class="button" name="reset" value="<?php echo _("Reset") ?>" />
  </td>
</table>
</form>
<br />
