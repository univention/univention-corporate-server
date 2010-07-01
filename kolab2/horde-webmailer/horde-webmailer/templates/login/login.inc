<script type="text/javascript">

function setFocus()
{
    try {
        if (document.horde_login.horde_user.value == "") {
            document.horde_login.horde_user.focus();
        } else {
            document.horde_login.horde_pass.focus();
        }
    } catch (e) {}
}

function submit_login()
{
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
<?php if (!empty($ie_clientcaps)): ?>
        try {
            document.horde_login.ie_version.value = objCCaps.getComponentVersion("{89820200-ECBD-11CF-8B85-00AA005B4383}", "componentid");
        } catch (e) {}
<?php endif; ?>
        document.horde_login.submit();
        return true;
    }
}

</script>

<form name="horde_login" method="post" action="<?php echo Horde::selfUrl(false, true, false, true) ?>"<?php echo $conf['menu']['always'] ? ' target="_parent"' : '' ?>>
<input type="hidden" name="url" value="<?php echo htmlspecialchars(Util::getFormData('url')) ?>" />
<input type="hidden" name="anchor_string" id="anchor_string" value="<?php echo htmlspecialchars(Util::getFormData('anchor_string')) ?>" />
<?php if (!empty($ie_clientcaps)): ?>
<input type="hidden" name="ie_version" value="" />
<?php endif; ?>

<div id="menu">
<?php
$menu = new Menu(HORDE_MENU_MASK_NONE);
$hmenu = $menu->render();
if ($hmenu): ?>
 <span class="leftFloat"><?php echo $hmenu ?></span>
<?php endif; ?>
 <h1 style="text-align:center"><?php printf(_("Welcome to %s"), $registry->get('name')) ?></h1>
</div>
<?php $notification->notify(array('listeners' => 'status')) ?>

<table width="100%"><tr><td align="center"><table width="300" align="center">

<tr>
    <td class="light rightAlign"><strong><?php echo Horde::label('horde_user', _("Username")) ?></strong>&nbsp;</td>
    <td class="leftAlign"><input type="text" id="horde_user" name="horde_user" value="<?php echo htmlspecialchars(Util::getFormData('horde_user')) ?>" style="direction:ltr" /></td>
</tr>

<tr>
    <td class="light rightAlign"><strong><?php echo Horde::label('horde_pass', _("Password")) ?></strong>&nbsp;</td>
    <td class="leftAlign"><input type="password" id="horde_pass" name="horde_pass" value="" style="direction:ltr" /></td>
</tr>

<?php if (!$prefs->isLocked('language')): ?>
<tr>
    <td class="light rightAlign"><strong><?php echo Horde::label('new_lang', _("Language")) ?></strong></td>
    <td class="light leftAlign"><?php echo $langs ?></td>
</tr>
<?php endif; ?>

<tr>
    <td>&nbsp;</td>
    <td class="light leftAlign"><input name="loginButton" class="button" value="<?php echo _("Log in") ?>" type="submit" onclick="return submit_login();" /></td>
</tr>

<?php if (!empty($conf['signup']['allow']) && $auth->hasCapability('add')): ?>
<tr>
    <td>&nbsp;</td>
    <td class="light leftAlign"><?php echo Horde::link(Util::addParameter(Horde::url($registry->get('webroot', 'horde') . '/signup.php'), 'url', Util::getFormData('url')), _("Don't have an account? Sign up."), 'light') . _("Don't have an account? Sign up.") ?></a></td>
</tr>
<?php endif; ?>
<?php if ($auth->hasCapability('resetpassword')): ?>
<tr>
    <td>&nbsp;</td>
    <td class="light"><?php echo Horde::link(Util::addParameter(Horde::url($registry->get('webroot', 'horde') . '/services/resetpassword.php'), 'url', Util::getFormData('url')), _("Forgot your password?"), 'light') . _("Forgot your password?") ?></a></td>
</tr>
<?php endif; ?>

</table></td></tr></table>
</form>

<?php Horde::loadConfiguration('motd.php', null, null, true); ?>

<script type="text/javascript">
<?php if (!$prefs->isLocked('language')):
    $lang_url = Horde::applicationUrl('login.php', true);
    if (($url = Util::getFormData('url'))) {
        $lang_url = Util::addParameter($lang_url, 'url', $url, false);
    }
    $lang_url = Util::addParameter($lang_url, 'new_lang', '', false);
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

if (parent.frames.horde_main) {
<?php if (empty($conf['menu']['always'])): ?>
    parent.location = self.location;
<?php else: ?>
    document.horde_login.target = '_parent';
<?php endif; ?>
}

/* Removes any leading hash that might be on a location string. */
function removeHash(h) {
    if (h == null || h == undefined) {
        return null;
    } else if (h.length && h.charAt(0) == '#') {
        if (h.length == 1) {
            return "";
        } else {
            return h.substring(1);
        }
    }
    return h;
}

// Need to capture hash information if it exists in URL
if (location.hash) {
    document.horde_login.anchor_string.value = removeHash(location.hash);
}
</script>
