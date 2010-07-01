<?php
if (isset($GLOBALS['language'])) {
    header('Content-type: text/html; charset=' . NLS::getCharset());
    header('Vary: Accept-Language');
}
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "DTD/xhtml1-transitional.dtd">
<!--   IMP: Copyright 2001-2009 The Horde Project.  IMP is under the GPL.  -->
<!-- Horde Project: http://www.horde.org/ | IMP: http://www.horde.org/imp/ -->
<!--        GNU Public License: http://www.fsf.org/copyleft/gpl.html       -->
<?php
echo (!empty($GLOBALS['language'])) ? '<html lang="' . strtr($GLOBALS['language'], '_', '-') . '"' : '<html';
echo ((!empty($ie_clientcaps)) ? ' xmlns:IE>' : '>') . '<head>';
$page_title = $GLOBALS['registry']->get('name');
if (!empty($title)) $page_title .= ' :: ' . $title;
if (!empty($refresh_time) && !empty($refresh_url)) {
    echo "<meta http-equiv=\"refresh\" content=\"$refresh_time;url=$refresh_url\" />\n";
}
if ($GLOBALS['browser']->isBrowser('msie') &&
    ($GLOBALS['browser']->getMajor() == 8)) {
    echo '<meta http-equiv="X-UA-Compatible" content="IE=EmulateIE7" />' . "\n";
}
echo Util::bufferOutput('require', IMP_TEMPLATES . '/javascript_defs.php');
IMP::includeScriptFiles();
IMP::includeStylesheetFiles(!empty($printer_friendly));
?>
<title><?php echo htmlspecialchars($page_title) ?></title>
<link href="<?php echo $GLOBALS['registry']->getImageDir() ?>/favicon.ico" rel="SHORTCUT ICON" />
<?php if ($mailbox_url = Util::nonInputVar('mailbox_url')): ?>
<link href="<?php echo $mailbox_url ?>" rel="Up" />
<?php elseif (!Util::nonInputVar('login_page')): ?>
<link href="<?php echo Util::addParameter(Horde::applicationUrl('mailbox.php'), 'mailbox', 'INBOX') ?>" rel="Top" />
<?php endif; ?>
<?php if ($first_url = Util::nonInputVar('first_url')): ?>
<link href="<?php echo $first_url ?>" rel="First" />
<?php endif; ?>
<?php if ($prev_url = Util::nonInputVar('prev_url')): ?>
<link href="<?php echo $prev_url ?>" rel="Previous" id="prev" />
<?php endif; ?>
<?php if ($next_url = Util::nonInputVar('next_url')): ?>
<link href="<?php echo $next_url ?>" rel="Next" id="next" />
<?php endif; ?>
<?php if ($last_url = Util::nonInputVar('last_url')): ?>
<link href="<?php echo $last_url ?>" rel="Last" />
<?php endif; ?>
<?php if ($alternate_url = Util::nonInputVar('alternate_url')): ?>
<link rel="alternate" type="application/rss+xml" href="<?php echo $alternate_url ?>" />
<?php endif; ?>
<?php if (!Util::nonInputVar('login_page')): ?>
<link href="<?php echo Horde::applicationUrl('search.php') ?>" rel="search" />
<?php endif ?>
<?php if (!empty($ie_clientcaps)): ?><style>IE\:clientcaps {behavior:url(#default#clientcaps)}</style><?php endif; ?>
<?php IMP::outputInlineScript(); ?>
</head>

<body<?php if ($bc = Util::nonInputVar('bodyClass')) echo ' class="' . $bc . '"' ?><?php if ($bi = Util::nonInputVar('bodyId')) echo ' id="' . $bi . '"'; ?>>
<?php if (!empty($ie_clientcaps)): ?><IE:clientcaps ID="objCCaps" /><?php endif; ?>
