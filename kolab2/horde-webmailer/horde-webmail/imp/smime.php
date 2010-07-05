<?php
/**
 * $Horde: imp/smime.php,v 2.48.4.16 2009-02-10 18:47:40 slusarz Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Mike Cochrane <mike@graftonhall.co.nz>
 * @author Michael Slusarz <slusarz@horde.org>
 */

function _importKeyDialog($target)
{
    $title = _("Import S/MIME Key");
    require IMP_TEMPLATES . '/common-header.inc';
    IMP::status();

    $t = new IMP_Template();
    $t->setOption('gettext', true);
    $t->set('selfurl', Horde::applicationUrl('smime.php'));
    $t->set('broken_mp_form', $GLOBALS['browser']->hasQuirk('broken_multipart_form'));
    $t->set('reload', htmlspecialchars(Util::getFormData('reload')));
    $t->set('target', $target);
    $t->set('forminput', Util::formInput());
    $t->set('import_public_key', $target == 'process_import_public_key');
    $t->set('import_personal_certs', $target == 'process_import_personal_certs');
    echo $t->fetch(IMP_TEMPLATES . '/smime/import_key.html');
}

function _getImportKey()
{
    $key = Util::getFormData('import_key');
    if (!empty($key)) {
        return $key;
    }

    $res = Browser::wasFileUploaded('upload_key', _("key"));
    if (!is_a($res, 'PEAR_Error')) {
        return file_get_contents($_FILES['upload_key']['tmp_name']);
    } else {
        $GLOBALS['notification']->push($res, 'horde.error');
        return;
    }
}

function _outputPassphraseDialog($secure_check)
{
    if (is_a($secure_check, 'PEAR_Error')) {
        $GLOBALS['notification']->push($secure_check, 'horde.warning');
    }

    $title = _("S/MIME Passphrase Input");
    require IMP_TEMPLATES . '/common-header.inc';
    IMP::status();

    if (is_a($secure_check, 'PEAR_Error')) {
        return;
    }

    $t = new IMP_Template();
    $t->setOption('gettext', true);
    $t->set('submit_url', Util::addParameter(Horde::applicationUrl('smime.php'), 'actionID', 'process_passphrase_dialog'));
    $t->set('reload', htmlspecialchars(Util::getFormData('reload')));
    $t->set('action', htmlspecialchars(Util::getFormData('passphrase_action')));
    $t->set('locked_img', Horde::img('locked.png', _("S/MIME"), null, $GLOBALS['registry']->getImageDir('horde')));
    echo $t->fetch(IMP_TEMPLATES . '/smime/passphrase.html');
}

function _actionWindow()
{
    require_once 'Horde/SessionObjects.php';
    $oid = Util::getFormData('passphrase_action');
    $cacheSess = &Horde_SessionObjects::singleton();
    $cacheSess->setPruneFlag($oid, true);
    Util::closeWindowJS($cacheSess->query($oid));
}

function _reloadWindow()
{
    require_once 'Horde/SessionObjects.php';
    $cacheSess = &Horde_SessionObjects::singleton();
    $reload = Util::getFormData('reload');
    $url = $cacheSess->query($reload);
    $cacheSess->setPruneFlag($reload, true);
    Util::closeWindowJS('opener.focus();opener.location.href="' . $url . '";');
}

function _textWindowOutput($filename, $msg, $html = false)
{
    $type = ($html ? 'text/html' : 'text/plain') . '; charset=' . NLS::getCharset();
    $GLOBALS['browser']->downloadHeaders($filename, $type, true, strlen($msg));
    echo $msg;
}

function _printKeyInfo($cert)
{
    $key_info = $GLOBALS['imp_smime']->certToHTML($cert);
    if (empty($key_info)) {
        _textWindowOutput('S/MIME Key Information', _("Invalid key"));
    } else {
        _textWindowOutput('S/MIME Key Information', $key_info, true);
    }
}


@define('IMP_BASE', dirname(__FILE__));
require_once IMP_BASE . '/lib/base.php';
require_once IMP_BASE . '/lib/Crypt/SMIME.php';
require_once IMP_BASE . '/lib/Template.php';


$imp_smime = new IMP_SMIME();
$secure_check = $imp_smime->requireSecureConnection();

/* Run through the action handlers */
$actionID = Util::getFormData('actionID');
switch ($actionID) {
case 'open_passphrase_dialog':
    if ($imp_smime->getPassphrase() !== false) {
        Util::closeWindowJS();
    } else {
        _outputPassphraseDialog($secure_check);
    }
    exit;

case 'process_passphrase_dialog':
    if (is_a($secure_check, 'PEAR_Error')) {
        _outputPassphraseDialog($secure_check);
    } elseif (Util::getFormData('passphrase')) {
        if ($imp_smime->storePassphrase(Util::getFormData('passphrase'))) {
            if (Util::getFormData('passphrase_action')) {
                _actionWindow();
            } elseif (Util::getFormData('reload')) {
                _reloadWindow();
            } else {
                Util::closeWindowJS();
            }
        } else {
            $notification->push("Invalid passphrase entered.", 'horde.error');
            _outputPassphraseDialog($secure_check);
        }
    } else {
        $notification->push("No passphrase entered.", 'horde.error');
        _outputPassphraseDialog($secure_check);
    }
    exit;

case 'delete_key':
    $imp_smime->deletePersonalKeys();
    $notification->push(_("Personal S/MIME keys deleted successfully."), 'horde.success');
    break;

case 'delete_public_key':
    $result = $imp_smime->deletePublicKey(Util::getFormData('email'));
    if (is_a($result, 'PEAR_Error')) {
        $notification->push($result, $result->getCode());
    } else {
        $notification->push(sprintf(_("S/MIME Public Key for \"%s\" was successfully deleted."), Util::getFormData('email')), 'horde.success');
    }
    break;

case 'import_public_key':
    _importKeyDialog('process_import_public_key');
    exit;

case 'process_import_public_key':
    $publicKey = _getImportKey();
    if (empty($publicKey)) {
        $notification->push(_("No S/MIME public key imported."), 'horde.error');
        $actionID = 'import_public_key';
        _importKeyDialog('process_import_public_key');
    } else {
        /* Add the public key to the storage system. */
        $key_info = $imp_smime->addPublicKey($publicKey);
        if (is_a($key_info, 'PEAR_Error')) {
            $notification->push($key_info, 'horde.error');
            $actionID = 'import_public_key';
            _importKeyDialog('process_import_public_key');
        } else {
            $notification->push(_("S/MIME Public Key successfully added."), 'horde.success');
            _reloadWindow();
        }
    }
    exit;

case 'view_public_key':
    $key = $imp_smime->getPublicKey(Util::getFormData('email'));
    if (is_a($key, 'PEAR_Error')) {
        $key = $key->getMessage();
    }
    _textWindowOutput('S/MIME Public Key', $key);
    exit;

case 'info_public_key':
    $key = $imp_smime->getPublicKey(Util::getFormData('email'));
    if (is_a($key, 'PEAR_Error')) {
        $key = $key->getMessage();
    }
    _printKeyInfo($key);
    exit;

case 'view_personal_public_key':
    _textWindowOutput('S/MIME Personal Public Key', $imp_smime->getPersonalPublicKey());
    exit;
case 'info_personal_public_key':
    _printKeyInfo($imp_smime->getPersonalPublicKey());
    exit;

case 'view_personal_private_key':
    _textWindowOutput('S/MIME Personal Private Key', $imp_smime->getPersonalPrivateKey());
    exit;

case 'import_personal_certs':
    _importKeyDialog('process_import_personal_certs');
    exit;

case 'process_import_personal_certs':
    if (!($pkcs12 = _getImportKey())) {
        $notification->push(_("No personal S/MIME certificates imported."), 'horde.error');
        $actionID = 'import_personal_certs';
        _importKeyDialog('process_import_personal_certs');
    } else {
        $res = $imp_smime->addFromPKCS12($pkcs12, Util::getFormData('upload_key_pass'), Util::getFormData('upload_key_pk_pass'));
        if (is_a($res, 'PEAR_Error')) {
            $notification->push(_("Personal S/MIME certificates NOT imported: ") . $res->getMessage(), 'horde.error');
            $actionID = 'import_personal_certs';
            _importKeyDialog('process_import_personal_certs');
        } else {
            $notification->push(_("S/MIME Public/Private Keypair successfully added."), 'horde.success');
            _reloadWindow();
        }
    }
    exit;

case 'save_attachment_public_key':
    require_once 'Horde/SessionObjects.php';

    $cacheSess = &Horde_SessionObjects::singleton();
    $cert = $cacheSess->query(Util::getFormData('cert'));

    /* Add the public key to the storage system. */
    $cert = $imp_smime->addPublicKey($cert);
    if ($cert == false) {
        $notification->push(_("No Certificate found"), 'horde.error');
    } else {
        Util::closeWindowJS();
    }
    exit;

case 'unset_passphrase':
    if ($imp_smime->getPassphrase() !== false) {
        $imp_smime->unsetPassphrase();
        $notification->push(_("Passphrase successfully unloaded."), 'horde.success');
    }
    break;

case 'save_options':
    $prefs->setValue('use_smime', Util::getFormData('use_smime') ? 1 : 0);
    $prefs->setValue('smime_verify', Util::getFormData('smime_verify') ? 1 : 0);
    $notification->push(_("Preferences successfully updated."), 'horde.success');
    break;
}

/* Get list of Public Keys. */
$pubkey_list = $imp_smime->listPublicKeys();
if (is_a($pubkey_list, 'PEAR_Error')) {
    $notification->push($pubkey_list, $pubkey_list->getCode());
}

if (is_callable(array('Horde', 'loadConfiguration'))) {
    $result = Horde::loadConfiguration('prefs.php', array('prefGroups', '_prefs'), 'imp');
    if (!is_a($result, 'PEAR_Error')) {
        extract($result);
    }
} else {
    require IMP_BASE . '/config/prefs.php';
}
require_once 'Horde/Help.php';
require_once 'Horde/Prefs/UI.php';
$app = 'imp';
$chunk = Util::nonInputVar('chunk');
Prefs_UI::generateHeader('smime', $chunk);

$selfURL = Horde::applicationUrl('smime.php');

/* If S/MIME preference not active, or openssl PHP extension not available, do
 * NOT show S/MIME Admin screen. */
$openssl_check = $imp_smime->checkForOpenSSL();

/* If S/MIME preference not active, do NOT show S/MIME Admin screen. */
$t = new IMP_Template();
$t->setOption('gettext', true);
$t->set('use_smime_help', Help::link('imp', 'smime-overview'));
if (!is_a($openssl_check, 'PEAR_Error') && $prefs->getValue('use_smime')) {
    Horde::addScriptFile('popup.js', 'imp', true);
    $t->set('smimeactive', true);
    $opensmimewin = $imp_smime->getJSOpenWinCode('open_passphrase_dialog');
    $t->set('manage_pubkey-help', Help::link('imp', 'smime-manage-pubkey'));

    $t->set('verify_notlocked', !$prefs->isLocked('smime_verify'));
    if ($t->get('verify_notlocked')) {
        $t->set('smime_verify', $prefs->getValue('smime_verify'));
        $t->set('smime_verify-help', Help::link('imp', 'smime-option-verify'));
    }

    $t->set('empty_pubkey_list', empty($pubkey_list));
    if (!$t->get('empty_pubkey_list')) {
        $t->set('pubkey_error', is_a($pubkey_list, 'PEAR_Error') ? $pubkey_list->getMessage() : false);
        if (!$t->get('pubkey_error')) {
            $plist = array();
            foreach ($pubkey_list as $val) {
                $linkurl = Util::addParameter($selfURL, 'email', $val['email']);
                $plist[] = array(
                    'name' => $val['name'],
                    'email' => $val['email'],
                    'view' => Horde::link(Util::addParameter($linkurl, 'actionID', 'view_public_key'), sprintf(_("View %s Public Key"), $val['name']), null, 'view_key'),
                    'info' => Horde::link(Util::addParameter($linkurl, 'actionID', 'info_public_key'), sprintf(_("Information on %s Public Key"), $val['name']), null, 'info_key'),
                    'delete' => Horde::link(Util::addParameter($linkurl, 'actionID', 'delete_public_key'), sprintf(_("Delete %s Public Key"), $val['name']), null, null, "if (confirm('" . addslashes(_("Are you sure you want to delete this public key?")) . "')) { return true; } else { return false; }")
                );
            }
            $t->set('pubkey_list', $plist);
        }
    }

    $t->set('no_file_upload', !$_SESSION['imp']['file_upload']);
    if (!$t->get('no_file_upload')) {
        $t->set('no_source', !$GLOBALS['prefs']->getValue('add_source'));
        if (!$t->get('no_source')) {
            require_once 'Horde/SessionObjects.php';
            $cacheSess = &Horde_SessionObjects::singleton();
            $t->set('public_import_url', Util::addParameter(Util::addParameter($selfURL, 'actionID', 'import_public_key'), 'reload', $cacheSess->storeOid($selfURL, false)));
            $t->set('import_pubkey-help', Help::link('imp', 'smime-import-pubkey'));
        }
    }
    $t->set('personalkey-help', Help::link('imp', 'smime-overview-personalkey'));

    $t->set('secure_check', is_a($secure_check, 'PEAR_Error'));
    if (!$t->get('secure_check')) {
        $t->set('has_key', $prefs->getValue('smime_public_key') && $prefs->getValue('smime_private_key'));
        if ($t->get('has_key')) {
            $t->set('viewpublic', Horde::link(Util::addParameter($selfURL, 'actionID', 'view_personal_public_key'), _("View Personal Public Key"), null, 'view_key'));
            $t->set('infopublic', Horde::link(Util::addParameter($selfURL, 'actionID', 'info_personal_public_key'), _("Information on Personal Public Key"), null, 'info_key'));
            $passphrase = $imp_smime->getPassphrase();
            $t->set('passphrase', (empty($passphrase)) ? Horde::link('#', _("Enter Passphrase"), null, null, htmlspecialchars($imp_smime->getJSOpenWinCode('open_passphrase_dialog')) . ' return false;') . _("Enter Passphrase") : Horde::link(Util::addParameter($selfURL, 'actionID', 'unset_passphrase'), _("Unload Passphrase")) . _("Unload Passphrase"));
            $t->set('viewprivate', Horde::link(Util::addParameter($selfURL, 'actionID', 'view_personal_private_key'), _("View Personal Private Key"), null, 'view_key'));
            $t->set('deletekeypair', addslashes(_("Are you sure you want to delete your keypair? (This is NOT recommended!)")));
            $t->set('personalkey-delete-help', Help::link('imp', 'smime-delete-personal-certs'));
        } else {
            $t->set('personal_import_url', Util::addParameter($selfURL, 'actionID', 'import_personal_certs'));
            $t->set('import-cert-help', Help::link('imp', 'smime-import-personal-certs'));
        }
    }
} else {
    $t->set('use_smime_locked', $prefs->isLocked('use_smime'));
    if (!$t->get('use_smime_locked')) {
        $t->set('use_smime_label', Horde::label('use_smime', _("Enable S/MIME functionality?")));
    }
}
$t->set('prefsurl', IMP::prefsURL(true));

echo $t->fetch(IMP_TEMPLATES . '/smime/smime.html');
if (!$chunk) {
    require $registry->get('templates', 'horde') . '/common-footer.inc';
}
