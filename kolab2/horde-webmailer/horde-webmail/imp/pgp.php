<?php
/**
 * $Horde: imp/pgp.php,v 2.79.6.21 2009-02-10 18:47:40 slusarz Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Michael Slusarz <slusarz@horde.org>
 */

function _printKeyInfo($key = '')
{
    $key_info = $GLOBALS['imp_pgp']->pgpPrettyKey($key);

    if (empty($key_info)) {
        _textWindowOutput('PGP Key Information', _("Invalid key"));
    } else {
        _textWindowOutput('PGP Key Information', $key_info);
    }
}

function _outputPassphraseDialog($secure_check, $symmetric = false)
{
    if (is_a($secure_check, 'PEAR_Error')) {
        $GLOBALS['notification']->push($secure_check, 'horde.warning');
    }

    $title = _("PGP Passphrase Input");
    require IMP_TEMPLATES . '/common-header.inc';
    IMP::status();

    if (is_a($secure_check, 'PEAR_Error')) {
        return;
    }

    $t = new IMP_Template();
    $t->setOption('gettext', true);
    $t->set('symmetric', $symmetric);
    $t->set('submit_url', Util::addParameter(Horde::applicationUrl('pgp.php'), 'actionID', $symmetric ? 'process_symmetric_passphrase_dialog' : 'process_passphrase_dialog'));
    $t->set('reload', htmlspecialchars(Util::getFormData('reload')));
    $t->set('action', htmlspecialchars(Util::getFormData('passphrase_action')));
    $t->set('locked_img', Horde::img('locked.png', _("PGP"), null, $GLOBALS['registry']->getImageDir('horde')));
    echo $t->fetch(IMP_TEMPLATES . '/pgp/passphrase.html');
}

function _importKeyDialog($target)
{
    $title = _("Import PGP Key");
    require IMP_TEMPLATES . '/common-header.inc';
    IMP::status();

    $t = new IMP_Template();
    $t->setOption('gettext', true);
    $t->set('selfurl', Horde::applicationUrl('pgp.php'));
    $t->set('broken_mp_form', $GLOBALS['browser']->hasQuirk('broken_multipart_form'));
    $t->set('reload', htmlspecialchars(Util::getFormData('reload')));
    $t->set('target', $target);
    $t->set('forminput', Util::formInput());
    $t->set('import_public_key', $target == 'process_import_public_key');
    $t->set('import_personal_public_key', $target == 'process_import_personal_public_key');
    $t->set('import_personal_private_key', $target == 'process_import_personal_private_key');
    echo $t->fetch(IMP_TEMPLATES . '/pgp/import_key.html');
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

function _textWindowOutput($filename, $msg)
{
    $GLOBALS['browser']->downloadHeaders($filename, 'text/plain; charset=' . NLS::getCharset(), true, strlen($msg));
    echo $msg;
}

require_once dirname(__FILE__) . '/lib/base.php';
require_once IMP_BASE . '/lib/Crypt/PGP.php';
require_once IMP_BASE . '/lib/Template.php';

$imp_pgp = new IMP_PGP();
$secure_check = $imp_pgp->requireSecureConnection();

/* Run through the action handlers */
$actionID = Util::getFormData('actionID');
switch ($actionID) {
case 'generate_key':
    /* Check that fields are filled out (except for Comment) and that the
       passphrases match. */
    $realname = Util::getFormData('generate_realname');
    $email = Util::getFormData('generate_email');
    $comment = Util::getFormData('generate_comment');
    $keylength = Util::getFormData('generate_keylength');
    $passphrase1 = Util::getFormData('generate_passphrase1');
    $passphrase2 = Util::getFormData('generate_passphrase2');

    if (empty($realname) || empty($email)) {
        $notification->push(_("Name and/or email cannot be empty"), 'horde.error');
    } elseif (empty($passphrase1) || empty($passphrase2)) {
        $notification->push(_("Passphrases cannot be empty"), 'horde.error');
    } elseif ($passphrase1 !== $passphrase2) {
        $notification->push(_("Passphrases do not match"), 'horde.error');
    } else {
        $result = $imp_pgp->generatePersonalKeys($realname, $email, $passphrase1, $comment, $keylength);
        if (is_a($result, 'PEAR_Error')) {
            $notification->push($result, $result->getCode());
        } else {
            $notification->push(_("Personal PGP keypair generated successfully."), 'horde.success');
        }
    }
    break;

case 'delete_key':
    $imp_pgp->deletePersonalKeys();
    $notification->push(_("Personal PGP keys deleted successfully."), 'horde.success');
    break;

case 'import_public_key':
    _importKeyDialog('process_import_public_key');
    exit;

case 'process_import_public_key':
    $publicKey = _getImportKey();
    if (empty($publicKey)) {
        $notification->push(_("No PGP public key imported."), 'horde.error');
        $actionID = 'import_public_key';
        _importKeyDialog('process_import_public_key');
    } else {
        /* Add the public key to the storage system. */
        $key_info = $imp_pgp->addPublicKey($publicKey);
        if (is_a($key_info, 'PEAR_Error')) {
            $notification->push($key_info, 'horde.error');
            $actionID = 'import_public_key';
            _importKeyDialog('process_import_public_key');
        } else {
            foreach ($key_info['signature'] as $sig) {
                $notification->push(sprintf(_("PGP Public Key for \"%s (%s)\" was successfully added."), $sig['name'], $sig['email']), 'horde.success');
            }
            _reloadWindow();
        }
    }
    exit;

case 'import_personal_public_key':
    _importKeyDialog('process_import_personal_public_key');
    exit;

case 'process_import_personal_public_key':
    $actionID = 'import_personal_public_key';
    /* Check the public key. */
    if ($publicKey = _getImportKey()) {
        if (($key_info = $imp_pgp->pgpPacketInformation($publicKey)) &&
            isset($key_info['public_key'])) {
            if (isset($key_info['secret_key'])) {
                /* Key contains private key too, don't allow to add this as
                 * public key. */
                $notification->push(_("Imported key contains your PGP private key. Only add your public key in the first step!"), 'horde.error');
                _importKeyDialog('process_import_personal_public_key');
            } else {
                /* Success in importing public key - Move on to private key
                 * now. */
                $imp_pgp->addPersonalPublicKey($publicKey);
                $notification->push(_("PGP public key successfully added."), 'horde.success');
                $actionID = 'import_personal_private_key';
                _importKeyDialog('process_import_personal_private_key');
            }
        } else {
            /* Invalid public key imported - Redo public key import screen. */
            $notification->push(_("Invalid personal PGP public key."), 'horde.error');
            _importKeyDialog('process_import_personal_public_key');
        }
    } else {
        /* No public key imported - Redo public key import screen. */
        $notification->push(_("No personal PGP public key imported."), 'horde.error');
        _importKeyDialog('process_import_personal_public_key');
    }
    exit;

case 'process_import_personal_private_key':
    $actionID = 'import_personal_private_key';
    /* Check the private key. */
    if ($privateKey = _getImportKey()) {
        if (($key_info = $imp_pgp->pgpPacketInformation($privateKey)) &&
            isset($key_info['secret_key'])) {
            /* Personal public and private keys have been imported
             * successfully - close the import popup window. */
            $imp_pgp->addPersonalPrivateKey($privateKey);
            $notification->push(_("PGP private key successfully added."), 'horde.success');
            _reloadWindow();
        } else {
            /* Invalid private key imported - Redo private key import
             * screen. */
            $notification->push(_("Invalid personal PGP private key."), 'horde.error');
            _importKeyDialog('process_import_personal_private_key');
        }
    } else {
        /* No private key imported - Redo private key import screen. */
        $notification->push(_("No personal PGP private key imported."), 'horde.error');
        _importKeyDialog('process_import_personal_private_key');
    }
    exit;

case 'view_public_key':
    $key = $imp_pgp->getPublicKey(Util::getFormData('email'), null, false);
    if (is_a($key, 'PEAR_Error')) {
        $key = $key->getMessage();
    }
    _textWindowOutput('PGP Public Key', $key);
    exit;

case 'view_personal_public_key':
    _textWindowOutput('PGP Personal Public Key', $imp_pgp->getPersonalPublicKey());
    exit;

case 'info_public_key':
    $key = $imp_pgp->getPublicKey(Util::getFormData('email'), null, false);
    if (is_a($key, 'PEAR_Error')) {
        $key = $key->getMessage();
    }
    _printKeyInfo($key);
    exit;

case 'info_personal_public_key':
    _printKeyInfo($imp_pgp->getPersonalPublicKey());
    exit;

case 'view_personal_private_key':
    _textWindowOutput('PGP Personal Private Key', $imp_pgp->getPersonalPrivateKey());
    exit;

case 'info_personal_private_key':
    _printKeyInfo($imp_pgp->getPersonalPrivateKey());
    exit;

case 'delete_public_key':
    $result = $imp_pgp->deletePublicKey(Util::getFormData('email'));
    if (is_a($result, 'PEAR_Error')) {
        $notification->push($result, $result->getCode());
    } else {
        $notification->push(sprintf(_("PGP Public Key for \"%s\" was successfully deleted."), Util::getFormData('email')), 'horde.success');
    }
    break;

case 'save_options':
    $prefs->setValue('use_pgp', Util::getFormData('use_pgp') ? 1 : 0);
    $prefs->setValue('pgp_attach_pubkey', Util::getFormData('pgp_attach_pubkey') ? 1 : 0);
    $prefs->setValue('pgp_scan_body', Util::getFormData('pgp_scan_body') ? 1 : 0);
    $prefs->setValue('pgp_verify', Util::getFormData('pgp_verify') ? 1 : 0);
    $notification->push(_("Preferences successfully updated."), 'horde.success');
    break;

case 'save_attachment_public_key':
    require_once 'Horde/SessionObjects.php';
    require_once 'Horde/MIME/Part.php';

    /* Retrieve the key from the cache. */
    $cache = &Horde_SessionObjects::singleton();
    $mime_part = $cache->query(Util::getFormData('mimecache'));
    if (empty($mime_part)) {
        Horde::fatal(_("Cannot retrieve public key from cache."), __FILE__, __LINE__);
    }
    $mime_part->transferDecodeContents();

    /* Add the public key to the storage system. */
    $key_info = $imp_pgp->addPublicKey($mime_part->getContents());
    if (is_a($key_info, 'PEAR_Error')) {
        $notification->push($key_info, $key_info->getCode());
    } else {
        Util::closeWindowJS();
    }
    exit;

case 'open_passphrase_dialog':
    if ($imp_pgp->getPassphrase()) {
        Util::closeWindowJS();
    } else {
        _outputPassphraseDialog($secure_check);
    }
    exit;

case 'open_symmetric_passphrase_dialog':
    if ($imp_pgp->getSymmetricPassphrase()) {
        Util::closeWindowJS();
    } else {
        _outputPassphraseDialog($secure_check, true);
    }
    exit;

case 'process_passphrase_dialog':
case 'process_symmetric_passphrase_dialog':
    $symmetric = $actionID == 'process_symmetric_passphrase_dialog';
    $passphrase = Util::getFormData('passphrase');
    if (is_a($secure_check, 'PEAR_Error')) {
        _outputPassphraseDialog($secure_check, $symmetric);
    } elseif ($passphrase) {
        if ($symmetric) {
            $success = $imp_pgp->storeSymmetricPassphrase($passphrase);
        } else {
            $success = $imp_pgp->storePassphrase($passphrase);
        }
        if ($success) {
            if (Util::getFormData('passphrase_action')) {
                require_once 'Horde/SessionObjects.php';
                $oid = Util::getFormData('passphrase_action');
                $cacheSess = &Horde_SessionObjects::singleton();
                $cacheSess->setPruneFlag($oid, true);
                Util::closeWindowJS($cacheSess->query($oid));
            } elseif (Util::getFormData('reload')) {
                _reloadWindow();
            } else {
                Util::closeWindowJS();
            }
        } else {
            $notification->push("Invalid passphrase entered.", 'horde.error');
            _outputPassphraseDialog($secure_check, $symmetric);
        }
    } else {
        $notification->push("No passphrase entered.", 'horde.error');
        _outputPassphraseDialog($secure_check, $symmetric);
    }
    exit;

case 'unset_passphrase':
    $imp_pgp->unsetPassphrase();
    $notification->push(_("Passphrase successfully unloaded."), 'horde.success');
    break;

case 'send_public_key':
    $result = $imp_pgp->sendToPublicKeyserver($imp_pgp->getPersonalPublicKey());
    if (is_a($result, 'PEAR_Error')) {
        $notification->push($result, $result->getCode());
    } else {
        $notification->push(_("Key successfully sent to the public keyserver."), 'horde.success');
    }
    break;
}

$selfURL = Horde::applicationUrl('pgp.php');

/* Get list of Public Keys on keyring. */
$pubkey_list = $imp_pgp->listPublicKeys();
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
Prefs_UI::generateHeader('pgp', $chunk);

/* If PGP preference not active, do NOT show PGP Admin screen. */
$t = new IMP_Template();
$t->setOption('gettext', true);
if ($prefs->getValue('use_pgp')) {
    Horde::addScriptFile('prototype.js', 'imp', true);
    Horde::addScriptFile('popup.js', 'imp', true);
    $t->set('pgpactive', true);
    $t->set('overview-help', Help::link('imp', 'pgp-overview'));
    $t->set('attach_pubkey_notlocked', !$prefs->isLocked('pgp_attach_pubkey'));
    if ($t->get('attach_pubkey_notlocked')) {
        $t->set('attach_pubkey', $prefs->getValue('pgp_attach_pubkey'));
        $t->set('attach_pubkey-help', Help::link('imp', 'pgp-option-attach-pubkey'));
    }
    $t->set('scan_body_notlocked', !$prefs->isLocked('pgp_scan_body'));
    if ($t->get('scan_body_notlocked')) {
        $t->set('scan_body', $prefs->getValue('pgp_scan_body'));
        $t->set('scan_body-help', Help::link('imp', 'pgp-option-scan-body'));
    }
    $t->set('verify_notlocked', !$prefs->isLocked('pgp_verify'));
    if ($t->get('verify_notlocked')) {
        $t->set('pgp_verify', $prefs->getValue('pgp_verify'));
        $t->set('pgp_verify-help', Help::link('imp', 'pgp-option-verify'));
    }
    $t->set('manage_pubkey-help', Help::link('imp', 'pgp-manage-pubkey'));

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
            $t->set('import_pubkey-help', Help::link('imp', 'pgp-import-pubkey'));
        }
    }
    $t->set('personalkey-help', Help::link('imp', 'pgp-overview-personalkey'));

    $t->set('secure_check', is_a($secure_check, 'PEAR_Error'));
    if (!$t->get('secure_check')) {
        $t->set('has_key', $prefs->getValue('pgp_public_key') && $prefs->getValue('pgp_private_key'));
        if ($t->get('has_key')) {
            $t->set('viewpublic', Horde::link(Util::addParameter($selfURL, 'actionID', 'view_personal_public_key'), _("View Personal Public Key"), null, 'view_key'));
            $t->set('infopublic', Horde::link(Util::addParameter($selfURL, 'actionID', 'info_personal_public_key'), _("Information on Personal Public Key"), null, 'info_key'));
            $t->set('sendkey', Horde::link(Util::addParameter($selfURL, 'actionID', 'send_public_key'), _("Send Key to Public Keyserver")));
            $t->set('personalkey-public-help', Help::link('imp', 'pgp-personalkey-public'));
            $passphrase = $imp_pgp->getPassphrase();
            $t->set('passphrase', (empty($passphrase)) ? Horde::link('#', _("Enter Passphrase"), null, null, htmlspecialchars($imp_pgp->getJSOpenWinCode('open_passphrase_dialog')) . ' return false;') . _("Enter Passphrase") : Horde::link(Util::addParameter($selfURL, 'actionID', 'unset_passphrase'), _("Unload Passphrase")) . _("Unload Passphrase"));
            $t->set('viewprivate', Horde::link(Util::addParameter($selfURL, 'actionID', 'view_personal_private_key'), _("View Personal Private Key"), null, 'view_key'));
            $t->set('infoprivate', Horde::link(Util::addParameter($selfURL, 'actionID', 'info_personal_private_key'), _("Information on Personal Private Key"), null, 'info_key'));
            $t->set('personalkey-private-help', Help::link('imp', 'pgp-personalkey-private'));
            $t->set('deletekeypair', addslashes(_("Are you sure you want to delete your keypair? (This is NOT recommended!)")));
            $t->set('personalkey-delete-help', Help::link('imp', 'pgp-personalkey-delete'));
        } else {
            require_once 'Horde/Identity.php';
            $imp_identity = &Identity::singleton(array('imp', 'imp'));
            $t->set('fullname', $imp_identity->getFullname());
            $t->set('personalkey-create-name-help', Help::link('imp', 'pgp-personalkey-create-name'));
            $t->set('personalkey-create-comment-help', Help::link('imp', 'pgp-personalkey-create-comment'));
            $t->set('fromaddr', $imp_identity->getFromAddress());
            $t->set('personalkey-create-email-help', Help::link('imp', 'pgp-personalkey-create-email'));
            $t->set('personalkey-create-keylength-help', Help::link('imp', 'pgp-personalkey-create-keylength'));
            $t->set('personalkey-create-passphrase-help', Help::link('imp', 'pgp-personalkey-create-passphrase'));
            $t->set('keygen',  addslashes(_("Key generation may take a long time to complete.  Continue with key generation?")));
            $t->set('personal_import_url', Util::addParameter($selfURL, 'actionID', 'import_personal_public_key'));
            $t->set('personalkey-create-actions-help', Help::link('imp', 'pgp-personalkey-create-actions'));
        }
    }

} else {
    $t->set('use_pgp_locked', $prefs->isLocked('use_pgp'));
    if (!$t->get('use_pgp_locked')) {
        $t->set('use_pgp_label', Horde::label('use_pgp', _("Enable PGP functionality?")));
        $t->set('use_pgp_help', Help::link('imp', 'pgp-overview'));
    }
}
$t->set('prefsurl', IMP::prefsURL(true));

echo $t->fetch(IMP_TEMPLATES . '/pgp/pgp.html');
if (!$chunk) {
    require $registry->get('templates', 'horde') . '/common-footer.inc';
}
