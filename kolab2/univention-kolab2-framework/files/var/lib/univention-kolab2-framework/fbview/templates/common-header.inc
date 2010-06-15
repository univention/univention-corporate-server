<?php
if (isset($language)) {
    header('Content-type: text/html; charset=' . NLS::getCharset());
    header('Vary: Accept-Language');
}
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "DTD/xhtml1-transitional.dtd">
<!-- Horde: Copyright 2000-2004, The Horde Project. Horde is under the LGPL. -->
<!--                    Horde Project: http://horde.org/                     -->
<!--    GNU Library Public License: http://www.fsf.org/copyleft/lgpl.html    -->
<?php echo !empty($language) ? '<html lang="' . strtr($language, '_', '-') . '">' : '<html>' ?>
<head>
<?php

$page_title = $GLOBALS['registry']->getParam('name');
if (!empty($title)) $page_title .= ' :: ' . $title;
if (!empty($refresh_time) && !empty($refresh_url)) {
    echo "<meta http-equiv=\"refresh\" content=\"$refresh_time;url=$refresh_url\" />\n";
}

Horde::includeScriptFiles();

$stylesheetApp = null;
if (isset($cssApp)) {
    $stylesheetApp = basename($cssApp);
}
?>
<title><?php echo $page_title ?></title>
<?php echo Horde::stylesheetLink($stylesheetApp) ?>
<link rel="SHORTCUT ICON" href="<?php echo $GLOBALS['registry']->getParam('graphics')?>/favicon.ico" />
</head>

<body<?php if (Util::nonInputVar('js_onLoad')) echo ' onload="' . $js_onLoad . '"'; if (Util::nonInputVar('bodyClass')) echo ' class="' . $bodyClass . '"' ?>>
