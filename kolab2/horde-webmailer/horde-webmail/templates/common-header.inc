<?php
global $language;
if (isset($language)) {
    header('Content-type: text/html; charset=' . NLS::getCharset());
    header('Vary: Accept-Language');
}
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "DTD/xhtml1-transitional.dtd">
<!-- Horde: Copyright 2000-2009 The Horde Project.  Horde is under the LGPL. -->
<!--                  Horde Project: http://www.horde.org/                   -->
<!--    GNU Library Public License: http://www.fsf.org/copyleft/lgpl.html    -->
<?php
echo (!empty($language)) ? '<html lang="' . strtr($language, '_', '-') . '"' : '<html';
echo ($hi = Util::nonInputVar('htmlId')) ? ' id="' . $hi . '"' : '';
echo (!empty($ie_clientcaps)) ? ' xmlns:IE>' : '>';
?>
<head>
<?php

$page_title = $GLOBALS['registry']->get('name');
if (!empty($title)) $page_title .= ' :: ' . $title;
if (!empty($refresh_time) && !empty($refresh_url)) {
    echo "<meta http-equiv=\"refresh\" content=\"$refresh_time;url=$refresh_url\" />\n";
}

Horde::includeScriptFiles();
?>
<title><?php echo htmlspecialchars($page_title) ?></title>
<link href="<?php echo $GLOBALS['registry']->getImageDir() ?>/favicon.ico" rel="SHORTCUT ICON" />
<?php echo Horde::stylesheetLink(Util::nonInputVar('cssApps')) ?>
<?php echo implode("\n", Util::nonInputVar('linkTags', array())) ?>
<?php if (!empty($ie_clientcaps)): ?><style>IE\:clientcaps {behavior:url(#default#clientcaps)}</style><?php endif; ?>
</head>

<body<?php if ($bc = Util::nonInputVar('bodyClass')) echo ' class="' . $bc . '"' ?><?php if ($bi = Util::nonInputVar('bodyId')) echo ' id="' . $bi . '"'; ?>>
<?php if (!empty($ie_clientcaps)): ?><IE:clientcaps ID="objCCaps" /><?php endif; ?>
