<script type="text/javascript">
<!--

function validate_update()
{
    if (document.updateuser.user_name.value == "") {
        document.updateuser.user_name.focus();
        alert('<?php echo addslashes(_("You must specify the username to add.")) ?>');
        return false;
    } else if (document.updateuser.user_pass_1 &&
               document.updateuser.user_pass_1.value != document.updateuser.user_pass_2.value) {
        document.updateuser.user_pass_1.value = "";
        document.updateuser.user_pass_2.value = "";
        document.updateuser.user_pass_1.focus();
        alert('<?php echo addslashes(_("Passwords must match.")) ?>');
        return false;
    }

    return true;
}

//-->
</script>

<form name="updateuser" method="post" action="user.php">
<?php Util::pformInput() ?>
<input type="hidden" name="form" value="update" />
<input type="hidden" name="user_name" value="<?php echo htmlspecialchars($f_user_name) ?>" />
<h1 class="header">
 <?php printf(_("Update %s"), $f_user_name) ?>
</h1>
<table class="striped nowrap" cellspacing="0" width="100%">
<?php if ($auth->hasCapability('update')): ?>
 <tr>
  <td width="1%" class="light rightAlign">
   <?php echo Horde::label('user_name2', _("New Username (optional)")) ?>
  </td>
  <td>
   <input type="text" id="user_name2" name="user_name2" value="<?php echo htmlspecialchars($f_user_name) ?>" />
  </td>
 </tr>
 <tr>
  <td class="rightAlign">
   <?php echo Horde::label('user_pass_1', _("Password")) ?>
  </td>
  <td>
   <input type="password" id="user_pass_1" name="user_pass_1" />
  </td>
 </tr>
 <tr>
  <td class="rightAlign">
   <?php echo Horde::label('user_pass_2', _("Confirm Password")) ?>
  </td>
  <td>
   <input type="password" id="user_pass_2" name="user_pass_2" />
  </td>
 </tr>
<?php endif; ?>
 <tr>
  <td class="rightAlign">
   <?php echo Horde::label('user_fullname', _("Full Name")) ?>
  </td>
  <td>
   <input type="text" id="user_fullname" name="user_fullname" value="<?php echo htmlspecialchars($identity->getValue('fullname')) ?>" />
  </td>
 </tr>
 <tr>
  <td class="rightAlign">
   <?php echo Horde::label('user_email', _("Email Address")) ?>
  </td>
  <td>
   <input type="text" id="user_email" name="user_email"  value="<?php echo htmlspecialchars($identity->getValue('from_addr')) ?>" />
  </td>
 </tr>
 <tr>
  <td class="control leftAlign" colspan="2">
   <input type="submit" class="button" name="submit" onclick="return validate_update();" value="<?php echo _("Update user") ?>" />
   <input type="reset" class="button" name="reset" value="<?php echo _("Reset") ?>" />
  </td>
 </tr>
</table>
</form>
<br />
