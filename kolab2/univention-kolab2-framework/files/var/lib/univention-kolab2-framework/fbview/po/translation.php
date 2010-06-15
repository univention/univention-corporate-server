#!/usr/bin/php -c /etc/php4/apache/php.ini
<?php
/**
 * Translation helper application for the Horde framework.
 *
 * For usage information call:
 * ./translation.php help
 *
 * $Horde: horde/po/translation.php,v 1.84 2004/04/29 19:18:15 jan Exp $
 */

/* Fix include_path to pick up our modified Horde classes */
$include_path = ini_get('include_path');
ini_set( 'include_path',
         '.:/kolab/var/kolab/php:/kolab/var/kolab/php/pear:'.$include_path);


function footer()
{
    global $c, $curdir;

    $c->writeln();
    $c->writeln(_("Please report any bugs to i18n@lists.horde.org."));

    chdir($curdir);
    exit;
}

function usage()
{
    global $options, $c;

    if (count($options[1]) &&
        ($options[1][0] == 'help' && !empty($options[1][1]) ||
        !empty($options[1][0]) && in_array($options[1][0], array('commit', 'compendium', 'extract', 'init', 'make', 'merge')))) {
        if ($options[1][0] == 'help') {
            $cmd = $options[1][1];
        } else {
            $cmd = $options[1][0];
        }
        $c->writeln(_("Usage:") . ' translation.php [options] ' . $cmd . ' [command-options]');
        if (!empty($cmd)) {
            $c->writeln();
            $c->writeln(_("Command options:"));
        }
        switch ($cmd) {
            case 'cleanup':
                $c->writeln(_("  -l, --locale=ll_CC     Use only this locale."));
                $c->writeln(_("  -m, --module=MODULE    Cleanup PO files only for this (Horde) module."));
                break;
            case 'commit':
            case 'commit-help':
                $c->writeln(_("  -l, --locale=ll_CC     Use this locale."));
                $c->writeln(_("  -m, --module=MODULE    Commit translations only for this (Horde) module."));
                $c->writeln(_("  -M, --message=MESSAGE  Use this commit message instead of the default ones."));
                $c->writeln(_("  -n, --new              This is a new translation, commit also C$C->REDITS,\n                         CHANGES and nls.php.dist."));
                break;
            case 'compendium':
                $c->writeln(_("  -a, --add=FILE        Add this PO file to the compendium. Useful to\n                        include a compendium from a different branch to\n                        the generated compendium."));
                $c->writeln(_("  -d, --directory=DIR   Create compendium in this directory."));
                $c->writeln(_("  -l, --locale=ll_CC    Use this locale."));
                break;
            case 'extract':
                $c->writeln(_("  -m, --module=MODULE  Generate POT file only for this (Horde) module."));
                break;
            case 'init':
                $c->writeln(_("  -l, --locale=ll_CC     Use this locale."));
                $c->writeln(_("  -m, --module=MODULE    Create a PO file only for this (Horde) module."));
                $c->writeln(_("  -c, --compendium=FILE  Use this compendium file instead of the default\n                         one (compendium.po in the horde/po directory)."));
                $c->writeln(_("  -n, --no-compendium    Don't use a compendium."));
                break;
            case 'make':
                $c->writeln(_("  -l, --locale=ll_CC     Use only this locale."));
                $c->writeln(_("  -m, --module=MODULE    Build MO files only for this (Horde) module."));
                $c->writeln(_("  -c, --compendium=FILE  Merge new translations to this compendium file\n                         instead of the default one (compendium.po in the\n                         horde/po directory."));
                $c->writeln(_("  -n, --no-compendium    Don't merge new translations to the compendium."));
                $c->writeln(_("  -s, --statistics       Save translation statistics in a local file."));
                break;
            case 'make-help':
            case 'update-help':
                $c->writeln(_("  -l, --locale=ll_CC     Use only this locale."));
                $c->writeln(_("  -m, --module=MODULE    Update help files only for this (Horde) module."));
                break;
            case 'merge':
                $c->writeln(_("  -l, --locale=ll_CC     Use this locale."));
                $c->writeln(_("  -m, --module=MODULE    Merge PO files only for this (Horde) module."));
                $c->writeln(_("  -c, --compendium=FILE  Use this compendium file instead of the default\n                         one (compendium.po in the horde/po directory)."));
                $c->writeln(_("  -n, --no-compendium    Don't use a compendium."));
                break;
            case 'update':
                $c->writeln(_("  -l, --locale=ll_CC     Use this locale."));
                $c->writeln(_("  -m, --module=MODULE    Update only this (Horde) module."));
                $c->writeln(_("  -c, --compendium=FILE  Use this compendium file instead of the default\n                         one (compendium.po in the horde/po directory)."));
                $c->writeln(_("  -n, --no-compendium    Don't use a compendium."));
                break;
        }
    } else {
        $c->writeln(_("Usage:") . ' translation.php [options] command [command-options]');
        $c->writeln(str_repeat(' ', String::length(_("Usage:"))) . ' translation.php [help|-h|--help] [command]');
        $c->writeln();
        $c->writeln(_("Helper application to create and maintain translations for the Horde\nframework and its applications.\nFor an introduction read the file README in this directory."));
        $c->writeln();
        $c->writeln(_("Commands:"));
        $c->writeln(_("  help        Show this help message."));
        $c->writeln(_("  compendium  Rebuild the compendium file. Warning: This overwrites the\n              current compendium."));
        $c->writeln(_("  extract     Generate PO template (.pot) files."));
        $c->writeln(_("  init        Create one or more PO files for a new locale. Warning: This\n              overwrites the existing PO files of this locale."));
        $c->writeln(_("  merge       Merge the current PO file with the current PO template file."));
        $c->writeln(_("  update      Run extract and merge sequent."));
        $c->writeln(_("  update-help Extract all new and changed entries from the English XML help\n              file and merge them with the existing ones."));
        $c->writeln(_("  cleanup     Cleans the PO files up from untranslated and obsolete entries."));
        $c->writeln(_("  make        Build binary MO files from the specified PO files."));
        $c->writeln(_("  make-help   Mark all entries in the XML help file being up-to-date and\n              prepare the file for the next execution of update-help. You\n              should only run make-help AFTER update-help and revising the\n              help file."));
        $c->writeln(_("  commit      Commit translations to the CVS server."));
        $c->writeln(_("  commit-help Commit help files to the CVS server."));
    }
    $c->writeln();
    $c->writeln(_("Options:"));
    $c->writeln(_("  -b, --base=/PATH  Full path to the (Horde) base directory that should be\n                    used."));
    $c->writeln(_("  -d, --debug       Show error messages from the executed binaries."));
    $c->writeln(_("  -h, --help        Show this help message."));
    $c->writeln(_("  -t, --test        Show the executed commands but don't run anything."));
}

function check_binaries()
{
    global $gettext_version, $c;

    $c->writeln(_("Searching gettext binaries..."));
    require_once 'System.php';
    foreach (array('gettext', 'msgattrib', 'msgcat', 'msgcomm', 'msgfmt', 'msginit', 'msgmerge', 'xgettext') as $binary) {
        echo $binary . '... ';
        $GLOBALS[$binary] = System::which($binary);
        if ($GLOBALS[$binary]) {
            $c->writeln($c->green(_("found: ")) . $GLOBALS[$binary]);
        } else {
            $c->writeln($c->red(_("not found")));
            footer();
        }
    }
    $c->writeln();

    $out = '';
    exec($GLOBALS['gettext'] . ' --version', $out, $ret);
    $split = explode(' ', $out[0]);
    echo 'gettext version: ' . $split[count($split) - 1];
    $gettext_version = explode('.', $split[count($split) - 1]);
    if ($gettext_version[0] == 0 && $gettext_version[1] < 12) {
        $GLOBALS['php_support'] = false;
        $c->writeln();
        $c->writeln($c->red(_("Warning: ")) . _("Your gettext version is too old and does not support PHP natively.\nNot all strings will be extracted."));
    } else {
        $GLOBALS['php_support'] = true;
        $c->writeln($c->green(' ' . _("OK")));
    }
    $c->writeln();
}

function search_file($file, $dir = '.', $local = false)
{
    static $ff;
    if (!isset($ff)) {
        $ff = &new File_Find();
    }

    if (substr($file, 0, 1) != DS) {
        $file = "/$file/";
    }

    if ($local) {
        $files = $ff->glob($file, $dir, 'perl');
        $files = array_map(create_function('$file', 'return "' . $dir . DS . '" . $file;'), $files);
        return $files;
    } else {
        return $ff->search($file, $dir, 'perl');
    }
}

function search_ext($ext, $dir = '.', $local = false)
{
    return search_file(".+\\.$ext\$", $dir, $local);
}

function get_po_files($dir)
{
    $langs = search_ext('po', $dir);
    if (($key = array_search($dir . DS . 'messages.po', $langs)) !== false) {
        unset($langs[$key]);
    }
    if (($key = array_search($dir . DS . 'compendium.po', $langs)) !== false) {
        unset($langs[$key]);
    }
    return $langs;
}

function get_languages($dir)
{
    global $curdir;

    chdir($dir);
    $langs = get_po_files('po');
    $langs = array_map(create_function('$lang', 'return str_replace("po" . DS, "", str_replace(".po", "", $lang));'), $langs);
    chdir($curdir);
    return $langs;
}

function search_applications()
{
    $dirs = array(HORDE_BASE);

    $dh = @opendir(BASE);
    if ($dh) {
        while ($entry = @readdir($dh)) {
            $dir = BASE . DS . $entry;
            if (is_dir($dir) &&
                substr($entry, 0, 1) != '.' &&
                fileinode(HORDE_BASE) != fileinode($dir)) {
                $sub = opendir($dir);
                if ($sub) {
                    while ($subentry = readdir($sub)) {
                        if ($subentry == 'po' && is_dir($dir . DS . $subentry)) {
                            $dirs[] = $dir;
                            break;
                        }
                    }
                }
            }
        }
    }

    return $dirs;
}

function strip_horde($file)
{
    if (is_array($file)) {
        return array_map(create_function('$file', 'return strip_horde($file);'), $file);
    } else {
        return str_replace(BASE . DS, '', $file);
    }
}

function xtract()
{
    global $cmd_options, $apps, $dirs, $debug, $test, $c, $gettext_version, $silence, $curdir;

    foreach ($cmd_options[0] as $option) {
        switch ($option[0]) {
            case 'h':
                usage();
                footer();
            case 'm':
            case '--module':
                $module = $option[1];
                break;
        }
    }
    require_once 'Horde/Array.php';
    if ($GLOBALS['php_support']) {
        $language = 'PHP';
    } else {
        $language = 'C++';
    }
    for ($i = 0; $i < count($dirs); $i++) {
        if (!empty($module) && $module != $apps[$i]) {
            continue;
        }
        echo sprintf(_("Extracting from %s... "), $apps[$i]);
        chdir($dirs[$i]);
        if ($apps[$i] == 'horde') {
            $files = search_ext('php', '.', true);
            foreach(array('admin', 'framework', 'lib', 'services', 'templates', 'util', 'config' . DS . 'themes') as $search_dir) {
                $files = array_merge($files, search_ext('(php|inc|js)', $search_dir));
            }
            $files = array_merge($files, search_ext('dist', 'config'));
            $sh = $GLOBALS['xgettext'] . ' --language=' . $language .
                  ' --from-code=iso-8859-1 --keyword=_ --sort-output --copyright-holder="Horde Project"';
            if ($gettext_version[0] > 0 || $gettext_version[1] > 11) {
                $sh .= ' --msgid-bugs-address="dev@lists.horde.org"';
            }
            $file = $dirs[$i] . DS . 'po' . DS . $apps[$i] . '.pot';
            $sh .= ' -o ' . $file . '.tmp ' . implode(' ', $files);
            if (@file_exists($dirs[$i] . '/po/translation.php')) {
                $sh .= ' po/translation.php';
            }
            if (!$debug) {
                $sh .= $silence;
            }
            if ($debug || $test) {
                $c->writeln(_("Executing:"));
                $c->writeln($sh);
            }
            if (!$test) exec($sh);
        } else {
            $files = search_ext('(php|inc|js)');
            $files = array_filter($files, create_function('$file', 'return substr($file, 0, 9) != "." . DS . "config" . DS;'));
            $files = array_merge($files, search_ext('dist', 'config'));
            $sh = $GLOBALS['xgettext'] . ' --language=' . $language .
                  ' --keyword=_ --sort-output --copyright-holder="Horde Project"';
            if ($gettext_version[0] > 0 || $gettext_version[1] > 11) {
                $sh .= ' --msgid-bugs-address="dev@lists.horde.org"';
            }
            $file = 'po' . DS . $apps[$i] . '.pot';
            $sh .= ' -o ' . $file . '.tmp ' . implode(' ', $files) . ($debug ? '' : $silence);
            if ($debug || $test) {
                $c->writeln(_("Executing:"));
                $c->writeln($sh);
            }
            if (!$test) exec($sh);
        }
        if (file_exists($file)) {
            $files = search_ext('html', 'templates');
            if (!$test) $tmp = fopen($file . '.templates', 'w');
            foreach ($files as $template) {
                $fp = fopen($template, 'r');
                $lineno = 0;
                while (($line = fgets($fp, 4096)) !== false) {
                    $lineno++;
                    $offset = 0;
                    while (($left = strpos($line, '<gettext>', $offset)) !== false) {
                        $left += 9;
                        $buffer = '';
                        $linespan = 0;
                        while (($end = strpos($line, '</gettext>', $left)) === false) {
                            $buffer .= substr($line, $left);
                            $left = 0;
                            $line = fgets($fp, 4096);
                            $linespan++;
                            if ($line === false) {
                                $c->writeln($c->red(sprintf(_("<gettext> tag not closed in file %s.\nOpening tag found in line %d."), $template, $lineno)));
                                break 2;
                            }
                        }
                        $buffer .= substr($line, $left, $end - $left);
                        if (!$test) {
                            fwrite($tmp, '#: ' . $template . "\n");
                            fwrite($tmp, 'msgid "' . str_replace('"', '\"', $buffer) . "\"\n");
                            fwrite($tmp, 'msgstr ""' . "\n\n");
                        }
                        $offset = $end + 10;
                    }
                }
                fclose($fp);
            }
            fclose($tmp);
            $sh = $GLOBALS['msgcomm'] . " --more-than=0 --sort-output \"$file.tmp\" \"$file.templates\" --output-file \"$file.tmp\"" . $silence;
            if ($debug || $test) {
                $c->writeln(_("Executing:"));
                $c->writeln($sh);
            }
            if (!$test) {
                exec($sh);
                unlink($file . '.templates');
            }
            $diff = array_diff(file($file . '.tmp'), file($file));
            $diff = preg_grep('/^"POT-Creation-Date:/', $diff, PREG_GREP_INVERT);
        }
        if (!file_exists($file) || count($diff)) {
            @unlink($file);
            rename($file . '.tmp', $file);
            $c->writeln($c->green(_("updated")));
        } else {
            @unlink($file . '.tmp');
            $c->writeln($c->bold(_("not changed")));
        }
        chdir($curdir);
    }
}

function merge()
{
    global $cmd_options, $apps, $dirs, $debug, $test, $c;

    $compendium = ' --compendium="' . BASE . DS . 'po' . DS . 'compendium.po"';
    foreach ($cmd_options[0] as $option) {
        switch ($option[0]) {
            case 'h':
                usage();
                footer();
            case 'l':
            case '--locale':
                $lang = $option[1];
                break;
            case 'm':
            case '--module':
                $module = $option[1];
                break;
            case 'c':
            case '--compendium':
                $compendium = ' --compendium=' . $option[1];
                break;
            case 'n':
            case '--no-compendium':
                $compendium = '';
                break;
        }
    }
    if (!isset($lang) && !empty($compendium)) {
        $c->writeln($c->red(_("Error: ") . _("No locale specified.")));
        $c->writeln();
        usage();
        footer();
    }

    cleanup();

    for ($i = 0; $i < count($dirs); $i++) {
        if (!empty($module) && $module != $apps[$i]) {
            continue;
        }
        $c->writeln(sprintf(_("Merging translation for module %s..."), $apps[$i]));
        $dir = $dirs[$i] . DS . 'po' . DS;
        if (empty($lang)) {
            $langs = get_languages($dirs[$i]);
        } else {
            if (!@file_exists($dir . $lang . '.po')) {
                $c->writeln(_("Skipped..."));
                $c->writeln();
                continue;
            }
            $langs = array($lang);
        }
        foreach ($langs as $locale) {
            $c->writeln(sprintf(_("Merging locale %s... "), $c->bold($locale)));
            $sh = $GLOBALS['msgmerge'] . ' --update -v' . $compendium . ' "' . $dir . $locale . '.po" "' . $dir . $apps[$i] . '.pot"';
            if ($debug || $test) {
                $c->writeln(_("Executing:"));
                $c->writeln($sh);
            }
            if (!$test) exec($sh);
            $c->writeln($c->green(_("done")));
        }
    }
}

function status()
{
    return;
    global $cmd_options, $apps, $dirs, $debug, $test, $c;

    $output = "status.html";
    foreach ($cmd_options[0] as $option) {
        switch ($option[0]) {
            case 'h':
                usage();
                footer();
            case 'l':
            case '--locale':
                $lang = $option[1];
                break;
            case 'm':
            case '--module':
                $module = $option[1];
                break;
            case 'o':
            case '--output':
                $output = $option[1];
                break;
       }
    }
    for ($i = 0; $i < count($dirs); $i++) {
        if (!empty($module) && $module != $apps[$i]) {
            continue;
        }
        $c->writeln(sprintf(_("Generating status for module %s..."), $c->bold($apps[$i])));
        if (empty($lang)) {
            $langs = get_languages($dirs[$i]);
        } else {
            if (!@file_exists($dirs[$i] . DS . 'po' . DS . $lang . '.po')) {
                $c->writeln(_("Skipped..."));
                $c->writeln();
                continue;
            }
            $langs = array($lang);
        }
        foreach ($langs as $locale) {
            $c->writeln(sprintf(_("Status for locale %s... "), $c->bold($locale)));
        }
    }
}

function compendium()
{
    global $cmd_options, $dirs, $debug, $test, $c, $silence;

    $dir = BASE . DS . 'po' . DS;
    $add = '';
    foreach ($cmd_options[0] as $option) {
        switch ($option[0]) {
            case 'h':
                usage();
                footer();
            case 'l':
            case '--locale':
                $lang = $option[1];
                break;
            case 'd':
            case '--directory':
                $dir = $option[1];
                break;
            case 'a':
            case '--add':
                $add = ' ' . $option[1];
                break;
        }
    }
    if (!isset($lang)) {
        $c->writeln($c->red(_("Error: ") . _("No locale specified.")));
        $c->writeln();
        usage();
        footer();
    }
    echo sprintf(_("Merging all %s.po files to the compendium... "), $lang);
    $pofiles = array();
    for ($i = 0; $i < count($dirs); $i++) {
        $pofile = $dirs[$i] . DS . 'po' . DS . $lang . '.po';
        if (file_exists($pofile)) {
            $pofiles[] = $pofile;
        }
    }
    if (!empty($dir) && substr($dir, -1) != DS) {
        $dir .= DS;
    }
    $sh = $GLOBALS['msgcat'] . ' --sort-output ' . implode(' ', $pofiles) . $add . ' > ' . $dir . 'compendium.po ' . ($debug ? '' : $silence);
    if ($debug || $test) {
        $c->writeln();
        $c->writeln(_("Executing:"));
        $c->writeln($sh);
    }
    if ($test) {
        $ret = 0;
    } else {
        exec($sh, $out, $ret);
    }
    if ($ret == 0) {
        $c->writeln($c->green(_("done")));
    } else {
        $c->writeln($c->red(_("failed")));
    }
}

function init()
{
    global $cmd_options, $apps, $dirs, $debug, $test, $c, $silence;

    foreach ($cmd_options[0] as $option) {
        switch ($option[0]) {
            case 'h':
                usage();
                footer();
            case 'l':
            case '--locale':
                $lang = $option[1];
                break;
            case 'm':
            case '--module':
                $module = $option[1];
                break;
        }
    }
    if (empty($lang)) { $lang = getenv('LANG'); }
    for ($i = 0; $i < count($dirs); $i++) {
        if (!empty($module) && $module != $apps[$i]) { continue; }
        $package = ucfirst($apps[$i]);
        $package_u = String::upper($apps[$i]);
        @include $dirs[$i] . '/lib/version.php';
        $version = eval('return(defined("' . $package_u . '_VERSION") ? ' . $package_u . '_VERSION : "???");');
        echo sprintf(_("Initializing module %s... "), $apps[$i]);
        if (!@file_exists($dirs[$i] . '/po/' . $apps[$i] . '.pot')) {
            $c->writeln($c->red(_("failed")));
            $c->writeln(sprintf(_("%s not found. Run 'translation extract' first."), $dirs[$i] . DS . 'po' . DS . $apps[$i] . '.pot'));
            continue;
        }
        $dir = $dirs[$i] . DS . 'po' . DS;
        $sh = $GLOBALS['msginit'] . ' --no-translator -i ' . $dir . $apps[$i] . '.pot ' .
              (!empty($lang) ? ' -o ' . $dir . $lang . '.po --locale=' . $lang : '') .
              ($debug ? '' : $silence);
        if (!empty($lang) && !OS_WINDOWS) {
            $pofile = $dirs[$i] . '/po/' . $lang . '.po';
            $sh .= "; sed 's/PACKAGE package/$package package/' $pofile " .
                   "| sed 's/PACKAGE VERSION/$package $version/' " .
                   "| sed 's/messages for PACKAGE/messages for $package/' " .
                   "| sed 's/Language-Team: none/Language-Team: i18n@lists.horde.org/' " .
                   "> $pofile.tmp";
        }
        if ($debug || $test) {
            $c->writeln(_("Executing:"));
            $c->writeln($sh);
        }
        if ($test) {
            $ret = 0;
        } else {
            exec($sh, $out, $ret);
        }
        rename($pofile . '.tmp', $pofile);
        if ($ret == 0) {
            $c->writeln($c->green(_("done")));
        } else {
            $c->writeln($c->red(_("failed")));
        }
    }
}

function make()
{
    global $cmd_options, $apps, $dirs, $debug, $test, $c, $silence, $redir_err;

    $compendium = BASE . DS . 'po' . DS . 'compendium.po';
    $save_stats = false;
    foreach ($cmd_options[0] as $option) {
        switch ($option[0]) {
            case 'h':
                usage();
                footer();
            case 'l':
            case '--locale':
                $lang = $option[1];
                break;
            case 'm':
            case '--module':
                $module = $option[1];
                break;
            case 'c':
            case '--compendium':
                $compendium = $option[1];
                break;
            case 'n':
            case '--no-compendium':
                $compendium = '';
                break;
            case 's':
            case '--statistics':
                $save_stats = true;
                break;
        }
    }
    $horde = array_search('horde', $dirs);
    $horde_msg = array();
    $stats_array = array();

    require_once 'Console/Table.php';
    $stats = new Console_Table();
    $stats->setHeaders(array(_("Module"), _("Language"), _("Translated"), _("Fuzzy"), _("Untranslated")));

    for ($i = 0; $i < count($dirs); $i++) {
        if (!empty($module) && $module != $apps[$i]) continue;
        $c->writeln(sprintf(_("Building MO files for module %s..."), $c->bold($apps[$i])));
        if (empty($lang)) {
            $langs = get_languages($dirs[$i]);
        } else {
            if (!@file_exists($dirs[$i] . DS . 'po' . DS . $lang . '.po')) {
                $c->writeln(_("Skipped..."));
                $c->writeln();
                continue;
            }
            $langs = array($lang);
        }
        foreach ($langs as $locale) {
            $c->writeln(sprintf(_("Building locale %s... "), $c->bold($locale)));
            $dir = $dirs[$i] . DS . 'locale' . DS . $locale . DS . 'LC_MESSAGES';
            if (!is_dir($dir)) {
                require_once 'System.php';
                if ($debug) {
                    $c->writeln(sprintf(_("Making directory %s"), $dir));
                }
                if (!$test && !@System::mkdir("-p $dir")) {
                    $c->writeln($c->red(_("Warning: ")) . sprintf(_("Could not create locale directory for locale %s:"), $locale));
                    $c->writeln($dir);
                    $c->writeln();
                    continue;
                }
            }

            /* Convert to unix linebreaks. */
            $pofile = $dirs[$i] . DS . 'po' . DS . $locale . '.po';
            $fp = fopen($pofile, 'r');
            $content = fread($fp, filesize($pofile));
            fclose($fp);

            $content = str_replace("\r", '', $content);
            $fp = fopen($pofile, 'wb');
            fwrite($fp, $content);
            fclose($fp);

            /* Check PO file sanity. */
            $sh = $GLOBALS['msgfmt'] . " --check \"$pofile\"$redir_err";
            if ($debug || $test) {
                $c->writeln(_("Executing:"));
                $c->writeln($sh);
            }
            if ($test) {
                $ret = 0;
            } else {
                exec($sh, $out, $ret);
            }
            if ($ret != 0) {
                $c->writeln($c->red(_("Warning: ")) . _("an error has occured:"));
                $c->writeln(implode("\n", $out));
                $c->writeln();
                if ($apps[$i] == 'horde') {
                    continue 3;
                }
                continue;
            }

            /* Compile MO file. */
            $sh = $GLOBALS['msgfmt'] . ' --statistics -o "' . $dir . DS . $apps[$i] . '.mo" ';
            if ($apps[$i] != 'horde') {
                $horde_po = $dirs[$horde] . DS . 'po' . DS . $locale . '.po';
                if (!@is_readable($horde_po)) {
                    $c->writeln($c->red(_("Warning: ")) . sprintf(_("the Horde PO file for the locale %s does not exist:"), $locale));
                    $c->writeln($horde_po);
                    $c->writeln();
                    $sh .= $dirs[$i] . DS . 'po' . DS . $locale . '.po';
                } else {
                    $sh = $GLOBALS['msgcomm'] . " --more-than=0 --sort-output \"$pofile\" \"$horde_po\" | $sh -";
                }
            } else {
                $sh .= $pofile;
            }
            $sh .= $redir_err;
            if ($debug || $test) {
                $c->writeln(_("Executing:"));
                $c->writeln($sh);
            }
            $out = '';
            if ($test) {
                $ret = 0;
            } else {
                putenv('LANG=en');
                exec($sh, $out, $ret);
                putenv('LANG=' . $GLOBALS['language']);
            }
            if ($ret == 0) {
                $c->writeln($c->green(_("done")));
                $messages = array(0, 0, 0);
                if (preg_match('/(\d+) translated/', $out[0], $match)) {
                    $messages[0] = $match[1];
                    if (isset($horde_msg[$locale])) {
                        $messages[0] -= $horde_msg[$locale][0];
                        if ($messages[0] < 0) $messages[0] = 0;
                    }
                }
                if (preg_match('/(\d+) fuzzy/', $out[0], $match)) {
                    $messages[1] = $match[1];
                    if (isset($horde_msg[$locale])) {
                        $messages[1] -= $horde_msg[$locale][1];
                        if ($messages[1] < 0) $messages[1] = 0;
                    }
                }
                if (preg_match('/(\d+) untranslated/', $out[0], $match)) {
                    $messages[2] = $match[1];
                    if (isset($horde_msg[$locale])) {
                        $messages[2] -= $horde_msg[$locale][2];
                        if ($messages[2] < 0) $messages[2] = 0;
                    }
                }
                if ($apps[$i] == 'horde') {
                    $horde_msg[$locale] = $messages;
                }
                $stats_array[$apps[$i]][$locale] = $messages;
                $stats->addRow(array($apps[$i], $locale, $messages[0], $messages[1], $messages[2]));
            } else {
                $c->writeln($c->red(_("failed")));
                exec($sh, $out, $ret);
                $c->writeln(implode("\n", $out));
            }
            if (count($langs) > 1) {
                continue;
            }

            /* Merge translation into compendium. */
            if (!empty($compendium)) {
                echo sprintf(_("Merging the PO file for %s to the compendium... "), $c->bold($apps[$i]));
                if (!empty($dir) && substr($dir, -1) != DS) {
                    $dir .= DS;
                }
                $sh = $GLOBALS['msgcat'] . " --sort-output \"$compendium\" \"$pofile\" > \"$compendium.tmp\"";
                if (!$debug) {
                    $sh .= $silence;
                }
                if ($debug || $test) {
                    $c->writeln();
                    $c->writeln(_("Executing:"));
                    $c->writeln($sh);
                }
                $out = '';
                if ($test) {
                    $ret = 0;
                } else {
                    exec($sh, $out, $ret);
                }
                @unlink($compendium);
                rename($compendium . '.tmp', $compendium);
                if ($ret == 0) {
                    $c->writeln($c->green(_("done")));
                } else {
                    $c->writeln($c->red(_("failed")));
                }
            }
            $c->writeln();
        }
    }
    if (empty($module)) {
        $c->writeln(_("Results:"));
    } else {
        $c->writeln(_("Results (including Horde):"));
    }
    $c->writeln($stats->getTable());
    if ($save_stats) {
        $fp = @fopen('translation_stats.txt', 'w');
        if ($fp) {
            fwrite($fp, serialize($stats_array));
            fclose($fp);
        }
    }
}

function cleanup($keep_untranslated = false)
{
    global $cmd_options, $apps, $dirs, $debug, $test, $c;

    foreach ($cmd_options[0] as $option) {
        switch ($option[0]) {
            case 'h':
                usage();
                footer();
            case 'l':
            case '--locale':
                $lang = $option[1];
                break;
            case 'm':
            case '--module':
                $module = $option[1];
                break;
        }
    }

    for ($i = 0; $i < count($dirs); $i++) {
        if (!empty($module) && $module != $apps[$i]) { continue; }
        $c->writeln(sprintf(_("Cleaning up PO files for module %s..."), $c->bold($apps[$i])));
        if (empty($lang)) {
            $langs = get_languages($dirs[$i]);
        } else {
            if (!@file_exists($dirs[$i] . DS . 'po' . DS . $lang . '.po')) {
                $c->writeln(_("Skipped..."));
                $c->writeln();
                continue;
            }
            $langs = array($lang);
        }
        foreach ($langs as $locale) {
            $c->writeln(sprintf(_("Cleaning up locale %s... "), $c->bold($locale)));
            $pofile = $dirs[$i] . DS . 'po' . DS . $locale . '.po';
            $sh = $GLOBALS['msgattrib'] . ($keep_untranslated ? '' : ' --translated') . " --no-obsolete --force-po $pofile > $pofile.tmp";
            if (!$debug) {
                $sh .= $silence;
            }
            if ($debug || $test) {
                $c->writeln();
                $c->writeln(_("Executing:"));
                $c->writeln($sh);
            }
            $out = '';
            if ($test) {
                $ret = 0;
            } else {
                exec($sh, $out, $ret);
            }
            @unlink($pofile);
            rename($pofile . '.tmp', $pofile);
            if ($ret == 0) {
                $c->writeln($c->green(_("done")));
            } else {
                $c->writeln($c->red(_("failed")));
            }
            $c->writeln();
        }
    }
}

function commit($help_only = false)
{
    global $cmd_options, $apps, $dirs, $debug, $test, $c;

    $docs = false;
    foreach ($cmd_options[0] as $option) {
        switch ($option[0]) {
            case 'h':
                usage();
                footer();
            case 'l':
            case '--locale':
                $lang = $option[1];
                break;
            case 'm':
            case '--module':
                $module = $option[1];
                break;
            case 'n':
            case '--new':
                $docs = true;
                break;
            case 'M':
            case '--message':
                $msg = $option[1];
                break;
        }
    }
    $files = array();
    for ($i = 0; $i < count($dirs); $i++) {
        if (!empty($module) && $module != $apps[$i]) continue;
        if (empty($lang)) {
            if ($help_only) {
                $files = array_merge($files, strip_horde(search_ext('xml', $dirs[$i] . DS . 'locale')));
            } else {
                $files = array_merge($files, strip_horde(get_po_files($dirs[$i] . DS . 'po')));
                $files = array_merge($files, strip_horde(search_file('^[a-z]{2}_[A-Z]{2}', $dirs[$i] . DS . 'locale', true)));
            }
        } else {
            if (!@file_exists($dirs[$i] . '/po/' . $lang . '.po')) continue;
            if ($help_only) {
                $file = $dirs[$i] . DS . 'locale' . DS . $lang . DS . 'help.xml';
                if (!@file_exists($file)) continue;
                $files[] = strip_horde($file);
            } else {
                $files[] = strip_horde($dirs[$i] . DS . 'po' . DS . $lang . '.po');
                $files[] = strip_horde($dirs[$i] . DS . 'locale' . DS . $lang);
            }
        }
        if ($docs && !$help_only) {
            $files[] = strip_horde($dirs[$i] . DS . 'docs');
            if ($apps[$i] == 'horde') {
                $horde_conf = $dirs[array_search('horde', $dirs)] . DS . 'config' . DS;
                $files[] = strip_horde($horde_conf . 'nls.php.dist');
            }
        }
    }
    chdir(BASE);
    if (count($files)) {
        if ($docs) {
            $c->writeln(_("Adding new files to repository:"));
            $sh = 'cvs add';
            foreach ($files as $file) {
                if (strstr($file, 'locale') || strstr($file, '.po')) {
                    $sh .= " $file";
                    $c->writeln($file);
                }
            }
            $sh .= '; cvs add';
            foreach ($files as $file) {
                if (strstr($file, 'locale')) {
                    if ($help_only) {
                        $add = $file . DS . '*.xml';
                        $sh .= ' ' . $add;
                        $c->writeln($add);
                    } else {
                        $sh .= ' ' . $file . DS . '*.xml ' . $file . DS . 'LC_MESSAGES';
                        $c->writeln($file . DS . "*.xml\n$file" . DS . 'LC_MESSAGES ');
                    }
                }
            }
            if (!$help_only) {
                $sh .= '; cvs add';
                foreach ($files as $file) {
                    if (strstr($file, 'locale')) {
                        $add = $file . DS . 'LC_MESSAGES' . DS . '*.mo';
                        $sh .= ' ' . $add;
                        $c->writeln($add);
                    }
                }
            }
            $c->writeln();
            if ($debug || $test) {
                $c->writeln(_("Executing:"));
                $c->writeln($sh);
            }
            if (!$test) system($sh);
            $c->writeln();
        }
        $c->writeln(_("Committing:"));
        $c->writeln(implode(' ', $files));
        if (!empty($lang)) {
            $lang = ' ' . $lang;
        }
        if (empty($msg)) {
            if ($docs) {
                $msg = "Add$lang translation.";
            } elseif ($help_only) {
                $msg = "Update$lang help file.";
            } else {
                $msg = "Update$lang translation.";
            }
        }
        $sh = 'cvs commit -m "' . $msg . '" ' . implode(' ', $files);
        if ($debug || $test) {
            $c->writeln(_("Executing:"));
            $c->writeln($sh);
        }
        if (!$test) system($sh);
    }
}

function update_help()
{
    global $cmd_options, $dirs, $apps, $debug, $test, $last_error_msg, $c;

    foreach ($cmd_options[0] as $option) {
        switch ($option[0]) {
            case 'h':
                usage();
                footer();
            case 'l':
            case '--locale':
                $lang = $option[1];
                break;
            case 'm':
            case '--module':
                $module = $option[1];
                break;
        }
    }
    $files = array();
    for ($i = 0; $i < count($dirs); $i++) {
        if (!empty($module) && $module != $apps[$i]) { continue; }
        if (!is_dir("$dirs[$i]/locale")) continue;
        if (empty($lang)) {
            $files = search_file('help.xml', $dirs[$i] . DS . 'locale');
        } else {
            $files = array($dirs[$i] . DS . 'locale' . DS . $lang . DS . 'help.xml');
        }
        $file_en  = $dirs[$i] . DS . 'locale' . DS . 'en_US' . DS . 'help.xml';
        if (!@file_exists($file_en)) {
            $c->writeln(wordwrap($c->red(_("Warning: ")) . sprintf(_("There doesn't yet exist a help file for %s."), $c->bold($apps[$i]))));
            $c->writeln();
            continue;
        }
        foreach ($files as $file_loc) {
            $locale = substr($file_loc, 0, strrpos($file_loc, DS));
            $locale = substr($locale, strrpos($locale, DS) + 1);
            if ($locale == 'en_US') continue;
            if (!@file_exists($file_loc)) {
                $c->writeln(wordwrap($c->red(_("Warning: ")) . sprintf(_("The %s help file for %s doesn't yet exist. Creating a new one."), $c->bold($locale), $c->bold($apps[$i]))));
                $dir_loc = substr($file_loc, 0, -9);
                if (!is_dir($dir_loc)) {
                    require_once 'System.php';
                    if ($debug || $test) {
                        $c->writeln(sprintf(_("Making directory %s"), $dir_loc));
                    }
                    if (!$test && !@System::mkdir("-p $dir_loc")) {
                        $c->writeln($c->red(_("Warning: ")) . sprintf(_("Could not create locale directory for locale %s:"), $locale));
                        $c->writeln($dir_loc);
                        $c->writeln();
                        continue;
                    }
                }
                if ($debug || $test) {
                    $c->writeln(wordwrap(sprintf(_("Copying %s to %s"), $file_en, $file_loc)));
                }
                if (!$test && !@copy($file_en, $file_loc)) {
                    $c->writeln($c->red(_("Warning: ")) . sprintf(_("Could not copy %s to %s"), $file_en, $file_loc));
                }
                $c->writeln();
                continue;
            }
            $c->writeln(sprintf(_("Updating %s help file for %s."), $c->bold($locale), $c->bold($apps[$i])));
            $fp = fopen($file_loc, 'r');
            $line = fgets($fp);
            fclose($fp);
            if (!strstr($line, '<?xml')) {
                $c->writeln(wordwrap($c->red(_("Warning: ")) . sprintf(_("The help file %s didn't start with <?xml"), $file_loc)));
                $c->writeln();
                continue;
            }
            $encoding = '';
            if (preg_match('/encoding=(["\'])([^\\1]+)\\1/', $line, $match)) {
                $encoding = $match[2];
            }
            $doc_en = domxml_open_file($file_en);
            if (!is_object($doc_en)) {
                $c->writeln(wordwrap($c->red(_("Warning: ")) . sprintf(_("There was an error opening the file %s. Try running translation.php with the flag -d to see any error messages from the xml parser."), $file_en)));
                $c->writeln();
                continue 2;
            }
            $doc_loc = domxml_open_file($file_loc);
            if (!is_object($doc_loc)) {
                $c->writeln(wordwrap($c->red(_("Warning: ")) . sprintf(_("There was an error opening the file %s. Try running translation.php with the flag -d to see any error messages from the xml parser."), $file_loc)));
                $c->writeln();
                continue;
            }
            $doc_new  = domxml_new_doc('1.0');
            $help_en  = $doc_en->document_element();
            $help_loc = $doc_loc->document_element();
            $help_new = $help_loc->clone_node();
            $entries_loc = array();
            $entries_new = array();
            $count_uptodate = 0;
            $count_new      = 0;
            $count_changed  = 0;
            $count_unknown  = 0;
            foreach ($doc_loc->get_elements_by_tagname('entry') as $entry) {
                $entries_loc[$entry->get_attribute('id')] = $entry;
            }
            foreach ($doc_en->get_elements_by_tagname('entry') as $entry) {
                $id = $entry->get_attribute('id');
                if (array_key_exists($id, $entries_loc)) {
                    if ($entries_loc[$id]->has_attribute('md5') &&
                        md5($entry->get_content()) != $entries_loc[$id]->get_attribute('md5')) {
                        $comment = $doc_loc->create_comment(" English entry:\n" . str_replace('--', '&#45;&#45;', $doc_loc->dump_node($entry)));
                        $entries_loc[$id]->append_child($comment);
                        $entry_new = $entries_loc[$id]->clone_node(true);
                        $entry_new->set_attribute('state', 'changed');
                        $count_changed++;
                    } else {
                        if (!$entries_loc[$id]->has_attribute('state')) {
                            $comment = $doc_loc->create_comment(" English entry:\n" . str_replace('--', '&#45;&#45;', $doc_loc->dump_node($entry)));
                            $entries_loc[$id]->append_child($comment);
                            $entry_new = $entries_loc[$id]->clone_node(true);
                            $entry_new->set_attribute('state', 'unknown');
                            $count_unknown++;
                        } else {
                            $entry_new = $entries_loc[$id]->clone_node(true);
                            $count_uptodate++;
                        }
                    }
                } else {
                    $entry_new = $entry->clone_node(true);
                    $entry_new->set_attribute('state', 'new');
                    $count_new++;
                }
                $entries_new[] = $entry_new;
            }
            $doc_new->append_child($doc_new->create_comment(' $' . 'Horde$ '));
            foreach ($entries_new as $entry) {
                $help_new->append_child($entry);
            }
            $c->writeln(wordwrap(sprintf(_("Entries: %d total, %d up-to-date, %d new, %d changed, %d unknown"),
                                     $count_uptodate + $count_new + $count_changed + $count_unknown,
                                     $count_uptodate, $count_new, $count_changed, $count_unknown)));
            $doc_new->append_child($help_new);
            $output = $doc_new->dump_mem(true, $encoding);
            if ($debug || $test) {
                $c->writeln(wordwrap(sprintf(_("Writing updated help file to %s."), $file_loc)));
            }
            if (!$test) {
                $fp = fopen($file_loc, 'w');
                $line = fwrite($fp, $output);
                fclose($fp);
            }
            $c->writeln(sprintf(_("%d bytes written."), strlen($output)));
            $c->writeln();
        }
    }
}

function make_help()
{
    global $cmd_options, $dirs, $apps, $debug, $test, $c;

    foreach ($cmd_options[0] as $option) {
        switch ($option[0]) {
            case 'h':
                usage();
                footer();
            case 'l':
            case '--locale':
                $lang = $option[1];
                break;
            case 'm':
            case '--module':
                $module = $option[1];
                break;
        }
    }
    $files = array();
    for ($i = 0; $i < count($dirs); $i++) {
        if (!empty($module) && $module != $apps[$i]) continue;
        if (!is_dir("$dirs[$i]/locale")) continue;
        if (empty($lang)) {
            $files = search_file('help.xml', $dirs[$i] . DS . 'locale');
        } else {
            $files = array($dirs[$i] . DS . 'locale' . DS . $lang . DS . 'help.xml');
        }
        $file_en  = $dirs[$i] . DS . 'locale' . DS . 'en_US' . DS . 'help.xml';
        if (!@file_exists($file_en)) {
            continue;
        }
        foreach ($files as $file_loc) {
            $locale = substr($file_loc, 0, strrpos($file_loc, DS));
            $locale = substr($locale, strrpos($locale, DS) + 1);
            if ($locale == 'en_US') continue;
            $c->writeln(sprintf(_("Updating %s help file for %s."), $c->bold($locale), $c->bold($apps[$i])));
            $fp = fopen($file_loc, 'r');
            $line = fgets($fp);
            fclose($fp);
            if (!strstr($line, '<?xml')) {
                $c->writeln(wordwrap($c->red(_("Warning: ")) . sprintf(_("The help file %s didn't start with <?xml"), $file_loc)));
                $c->writeln();
                continue;
            }
            $encoding = '';
            if (preg_match('/encoding=(["\'])([^\\1]+)\\1/', $line, $match)) {
                $encoding = $match[2];
            }
            $doc_en   = domxml_open_file($file_en);
            if (!is_object($doc_en)) {
                $c->writeln(wordwrap($c->red(_("Warning: ")) . sprintf(_("There was an error opening the file %s. Try running translation.php with the flag -d to see any error messages from the xml parser."), $file_en)));
                $c->writeln();
                continue 2;
            }
            $doc_loc  = domxml_open_file($file_loc);
            if (!is_object($doc_loc)) {
                $c->writeln(wordwrap($c->red(_("Warning: ")) . sprintf(_("There was an error opening the file %s. Try running translation.php with the flag -d to see any error messages from the xml parser."), $file_loc)));
                $c->writeln();
                continue;
            }
            $help_loc = $doc_loc->document_element();
            $md5_en   = array();
            $count_all = 0;
            $count     = 0;
            foreach ($doc_en->get_elements_by_tagname('entry') as $entry) {
                $md5_en[$entry->get_attribute('id')] = md5($entry->get_content());
            }
            foreach ($doc_loc->get_elements_by_tagname('entry') as $entry) {
                foreach ($entry->child_nodes() as $child) {
                    if ($child->node_type() == XML_COMMENT_NODE && strstr($child->node_value(), 'English entry')) {
                        $entry->remove_child($child);
                    }
                }
                $count_all++;
                $id = $entry->get_attribute('id');
                if (!array_key_exists($id, $md5_en)) {
                    $c->writeln(wordwrap($c->red(_("Warning: ")) . sprintf(_("No entry with the id '%s' exists in the original help file."), $id)));
                } else {
                    $entry->set_attribute('md5', $md5_en[$id]);
                    $entry->set_attribute('state', 'uptodate');
                    $count++;
                }
            }
            $output = $doc_loc->dump_mem(true, $encoding);
            if (!$test) {
                $fp = fopen($file_loc, 'w');
                $line = fwrite($fp, $output);
                fclose($fp);
            }
            $c->writeln(sprintf(_("%d of %d entries marked as up-to-date"), $count, $count_all));
            $c->writeln();
        }
    }
}

$curdir = getcwd();
define('DS', DIRECTORY_SEPARATOR);

$language = getenv('LANG');
if (empty($language)) {
    $language = getenv('LANGUAGE');
}

@define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once HORDE_BASE . '/lib/core.php';
require_once 'Horde/CLI.php';

$c = &new Horde_CLI();
if (!$c->runningFromCLI()) {
    $c->fatal(_("This script must be run from the command line."));
}
$c->init();

require HORDE_BASE . '/config/nls.php';
require_once 'Horde/NLS.php';
if (!empty($language)) {
    $tmp = explode('.', $language);
    $language = $tmp[0];
    $language = NLS::_map(trim($language));
    if (!NLS::isValid($language)) {
        $language = NLS::_map(substr($language, 0, 2));
    }
    if (NLS::isValid($language)) {
        setlocale(LC_ALL, $language);
        bindtextdomain('horde', HORDE_BASE . '/locale');
        textdomain('horde');
        if (array_key_exists(1, $tmp) && 
            function_exists('bind_textdomain_codeset')) {
            bind_textdomain_codeset('horde', $tmp[1]);
        }
    }
}

$c->writeln($c->bold(_("---------------------------")));
$c->writeln($c->bold(_("Horde translation generator")));
$c->writeln($c->bold(_("---------------------------")));

/* Sanity checks */
if (!extension_loaded('gettext')) {
    $c->writeln($c->red('Gettext extension not found!'));
    footer();
}

$c->writeln(_("Loading libraries..."));
$libs_found = true;

foreach (array('Console_Getopt' => 'Console/Getopt.php',
               'Console_Table'  => 'Console/Table.php',
               'File_Find'      => 'File/Find.php')
         as $class => $file) {
    echo $class . '... ';
    @include $file;
    if (class_exists($class)) {
        $c->writeln($c->green(_("OK")));
    } else {
        $c->writeln($c->red(sprintf(_("%s not found."), $class)));
        $libs_found = false;
    }
}

if (!$libs_found) {
    $c->writeln();
    $c->writeln(_("Make sure that you have PEAR installed and in your include path."));
    $c->writeln('include_path: ' . ini_get('include_path'));
    footer();
}
$c->writeln();

/* Commandline parameters */
$args    = Console_Getopt::readPHPArgv();
$options = Console_Getopt::getopt($args, 'b:dht', array('base=', 'debug', 'help', 'test'));
if (PEAR::isError($options) && $args[0] == $_SERVER['PHP_SELF']) {
    array_shift($args);
    $options = Console_Getopt::getopt($args, 'b:dht', array('base=', 'debug', 'help', 'test'));
}
if (PEAR::isError($options)) {
    $c->writeln($c->red(_("Getopt Error: ") . str_replace('Console_Getopt:', '', $options->getMessage())));
    $c->writeln();
    usage();
    footer();
}
if (empty($options[1][0])) {
    $c->writeln($c->red(_("Error: ") . _("No command specified.")));
    $c->writeln();
    usage();
    footer();
}
$debug = false;
$test  = false;
foreach ($options[0] as $option) {
    switch ($option[0]) {
        case 'b':
        case '--base':
            if (substr($option[1], -1) == DS) {
                $option[1] = substr($option[1], 0, -1);
            }
            define('BASE', $option[1]);
            break;
        case 'd':
        case '--debug':
            $debug = true;
            break;
        case 't':
        case '--test':
            $test = true;
            break;
        case 'h':
        case '--help':
            usage();
            footer();
    }
}
if (!$debug) {
    ini_set('error_reporting', false);
}
if (!defined('BASE')) {
    define('BASE', HORDE_BASE);
}
if ($options[1][0] == 'help') {
    usage();
    footer();
}
$silence = $debug || OS_WINDOWS ? '' : ' 2> /dev/null';
$redir_err = OS_WINDOWS ? '' : ' 2>&1';
$options_list = array(
    'cleanup'    => array('hl:m:', array('module=', 'locale=')),
    'commit'     => array('hl:m:nM:', array('module=', 'locale=', 'new', 'message=')),
    'commit-help'=> array('hl:m:nM:', array('module=', 'locale=', 'new', 'message=')),
    'compendium' => array('hl:d:a:', array('locale=', 'directory=', 'add=')),
    'extract'    => array('hm:', array('module=')),
    'init'       => array('hl:m:', array('module=', 'locale=')),
    'merge'      => array('hl:m:c:n', array('module=', 'locale=', 'compendium=', 'no-compendium')),
    'make'       => array('hl:m:c:ns', array('module=', 'locale=', 'compendium=', 'no-compendium', 'statistics')),
    'make-help'  => array('hl:m:', array('module=', 'locale=')),
    'update'     => array('hl:m:c:n', array('module=', 'locale=', 'compendium=', 'no-compendium')),
    'update-help'=> array('hl:m:', array('module=', 'locale=')),
    'status'     => array('hl:m:o:', array('module=', 'locale=', 'output='))
);
$options_arr = $options[1];
$cmd         = array_shift($options_arr);
if (array_key_exists($cmd, $options_list)) {
    $cmd_options = Console_Getopt::getopt($options_arr, $options_list[$cmd][0], $options_list[$cmd][1]);
    if (PEAR::isError($cmd_options)) {
        $c->writeln($c->red(_("Error: ") . str_replace('Console_Getopt:', '', $cmd_options->getMessage())));
        $c->writeln();
        usage();
        footer();
    }
}

/* Searching applications */
check_binaries();

$c->writeln(sprintf(_("Searching Horde applications in %s"), BASE));
$dirs = search_applications();

if ($debug) {
    $c->writeln(_("Found directories:"));
    $c->writeln(implode("\n", $dirs));
}

$apps = strip_horde($dirs);
$apps[0] = 'horde';
$c->writeln(wordwrap(sprintf(_("Found applications: %s"), implode(', ', $apps))));
$c->writeln();

switch ($cmd) {
    case 'cleanup':
    case 'commit':
    case 'compendium':
    case 'merge':
        $cmd();
        break;
    case 'commit-help':
        commit(true);
        break;
    case 'extract':
        xtract();
        break;
    case 'init':
        init();
        $c->writeln();
        merge();
        break;
    case 'make':
        cleanup(true);
        $c->writeln();
        make();
        break;
    case 'make-help':
        make_help();
        break;
    case 'update':
        xtract();
        $c->writeln();
        merge();
        break;
    case 'update-help':
        update_help();
        break;
    case 'status':
//        xtract();
        merge();
//        status();
        break;
    default:
        $c->writeln($c->red(_("Error: ")) . sprintf(_("Unknown command: %s"), $cmd));
        $c->writeln();
        usage();
        footer();
}

footer();
