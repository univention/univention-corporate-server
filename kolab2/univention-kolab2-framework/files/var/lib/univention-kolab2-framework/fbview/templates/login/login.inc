<script language="JavaScript" type="text/javascript">
<!--
function setFocus()
{
    if (document.horde_login.horde_user.value == "") {
        document.horde_login.horde_user.focus();
    } else {
        document.horde_login.horde_pass.focus();
    }
}
function submit_login(e)
{
    if (e != undefined && !enter_key_trap(e)) {
        return;
    }

    if (document.horde_login.horde_user.value == "") {
        alert("<?php echo addslashes(_("Please provide your username and password")) ?>");
        document.horde_login.horde_user.focus();
        return false;
    } else if (document.horde_login.horde_pass.value == "") {
        alert("<?php echo addslashes(_("Please provide your username and password")) ?>");
        document.horde_login.horde_pass.focus();
        return false;
    } else {
        document.horde_login.loginButton.disabled = true;
        document.horde_login.submit();
        return true;
    }
}
//-->
</script>

<form name="horde_login" method="post" action="<?php echo Horde::selfURL() ?>"<?php echo $conf['menu']['always'] ? ' target="_parent"' : '' ?>>
<input type="hidden" name="url" value="<?php echo Util::getFormData('url') ?>" />
<input type="hidden" name="frameset" value="0" />

<table border="0" width="100%" cellpadding="0" cellspacing="0">
<tr>
 <td class="menu" width="100%">
  <table border="0" width="100%">
   <tr>
    <td width="33%">&nbsp;</td>
    <td width="33%" align="center" class="menuheader"><?php printf(_("Welcome to %s"), $registry->getParam('name')) ?></td>
    <td width="33%" align="right">
     <table border="0">
      <tr>
<?php
if ($perms->exists('problem') ? $perms->hasPermission('problem', Auth::getAuth(), PERMS_READ) : Auth::getAuth()) {
    echo Menu::createItem(Horde::url($registry->getParam('webroot', 'problem') . '/problem.php'), $registry->getParam('name', 'problem'), $registry->getParam('icon', 'problem'), '');
}
?>
      </tr>
     </table>
    </td>
   </tr>
  </table>
 </td>
</tr>

<!-- Slimmer inner table -->
<tr><td align="center"><table border="0" width="300">

<?php if (!empty($reason)): ?>
<tr>
    <td align="center" colspan="2"><p class="light"><?php echo $reason ?></p></td>
</tr>
<?php endif; ?>

<tr>
    <td align="right" class="light"><b><?php echo _("Username") ?></b>&nbsp;</td>
    <td align="left"><input class="fixed" type="text" name="horde_user" value="<?php echo Util::getFormData('horde_user') ?>" /></td>
</tr>

<tr>
    <td align="right" class="light"><b><?php echo _("Password") ?></b>&nbsp;</td>
    <td align="left"><input class="fixed" type="password" name="horde_pass" value="" /></td>
</tr>

<?php if (!$prefs->isLocked('language')): ?>
<tr>
    <td align="right" class="light"><b><?php echo _("Language") ?></b></td>
    <td align="left" class="light"><?php echo $langs ?></td>
</tr>
<?php endif; ?>

<tr>
    <td>&nbsp;</td>
    <td class="light"><input name="loginButton" class="button" value="<?php echo _("Log in") ?>" type="submit" onclick="return submit_login();" /></td>
</tr>

<?php if ($conf['signup']['allow'] && $auth->hasCapability('add')): ?>
<tr>
    <td>&nbsp;</td>
    <td class="light"><?php echo Horde::link(Util::addParameter(Horde::url($registry->getParam('webroot', 'horde') . '/signup.php'), 'url', Util::getFormData('url')), _("Sign up if not registered"), 'light') . _("Sign up if not registered") ?></a></td>
</tr>
<?php endif; ?>
<?php if ($auth->hasCapability('resetpassword')): ?>
<tr>
    <td>&nbsp;</td>
    <td class="light"><?php echo Horde::link(Util::addParameter(Horde::url($registry->getParam('webroot', 'horde') . '/services/resetpassword.php'), 'url', Util::getFormData('url')), _("Forgot your password?"), 'light') . _("Forgot your password?") ?></a></td>
</tr>
<?php endif; ?>

</table>
</form>

<?php if (@is_readable(HORDE_BASE . '/config/motd.php')) require HORDE_BASE . '/config/motd.php'; ?>

<script language="JavaScript" type="text/javascript">
<!--
<?php if (!$prefs->isLocked('language')):
    $lang_url = Horde::applicationUrl('login.php');
    if (($url = Util::getFormData('url'))) {
        $lang_url = Util::addParameter($lang_url, 'url', $url);
    }
    $lang_url = Util::addParameter($lang_url, 'new_lang', '');
?>
function selectLang()
{
    // We need to reload the login page here, but only if the user
    // hasn't already entered a username and password.
    if (document.horde_login.horde_user.value == '' &&
        document.horde_login.horde_pass.value == '') {
        var lang_page = '<?php echo $lang_url ?>' + document.horde_login.new_lang[document.horde_login.new_lang.selectedIndex].value;
        self.location = lang_page;
    }
}
<?php endif; ?>

<?php
// Try to detect the frameset (or lack thereof). If
// $conf['menu']['always'] is true, though, the frameset will be
// present, but we want to go back to the main index.php in the parent
// frame so that it gets reloaded with the authenticated menus.
?>
if (parent.frames.horde_main) {
<?php if (!$conf['menu']['always']): ?>
    document.horde_login.frameset.value = 1;
<?php else: ?>
    parent.frames.horde_menu.location.reload();
<?php endif; ?>
}
//-->
</script>

<script language="JavaScript1.2" type="text/javascript">
<!--
// Setup the enter keytrap code.
if (window.document.captureEvents != null) {
    window.document.captureEvents(Event.KEYPRESS);
    window.document.onkeypress = submit_login;
}
//-->
</script>
