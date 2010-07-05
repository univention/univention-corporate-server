/**
 * Provides the javascript for the login.php script.
 *
 * $Horde: imp/js/src/login.js,v 1.6.2.2 2008-05-20 16:33:02 slusarz Exp $
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

function setFocus()
{
    if (!$F('imapuser')) {
        $('imapuser').focus();
    } else {
        $('pass').focus();
    }
}

function imp_reload()
{
    window.top.document.location = autologin_url + $F('server_key');
}

function submit_login()
{
    if (show_list && $F('server').startsWith("_")) {
        return false;
    }
    if (!$F('imapuser')) {
        alert(IMP.text.login_username);
        $('imapuser').focus();
        return false;
    } else if (!$F('pass')) {
        alert(IMP.text.login_password);
        $('pass').focus();
        return false;
    } else {
        $('loginButton').disable();
        if (ie_clientcaps) {
            try {
                $('ie_version').setValue(objCCaps.getComponentVersion("{89820200-ECBD-11CF-8B85-00AA005B4383}","componentid"));
            } catch (e) { }
        }
        $('imp_login').submit();
        return true;
    }
}

function selectLang()
{
    // We need to reload the login page here, but only if the user hasn't
    // already entered a username and password.
    if (!$F('imapuser') && !$F('pass')) {
        var params = { new_lang: $F('new_lang') };
        if (lang_url !== null) {
            params.url = lang_url;
        }
        self.location = 'login.php?' + Object.toQueryString(params);
    }
}

function updatePort()
{
    var v = $F('protocol');
    if (protocols[v]) {
        $('port').setValue(protocols[v]);
    }
}

function serverChangeHandler()
{
    if (change_smtphost) {
        $('smtphost').setValue($F('server'));
    }
}

/* Removes any leading hash that might be on a location string. */
function removeHash(h)
{
    return (Object.isString(h) && h.startsWith("#")) ? h.substring(1) : h;
}

document.observe('dom:loaded', function() {
    if (imp_auth) {
        if (parent.frames.horde_main) {
            if (nomenu) {
                parent.location = self.location;
            } else {
                document.imp_login.target = '_parent';
            }
        }
    }

    // Need to capture hash information if it exists in URL
    if (location.hash) {
        $('anchor_string').setValue(removeHash(location.hash));
    }
});
