#!/usr/bin/php -q
<?php
/**
 * Translation helper application for the Horde framework.
 *
 * For usage information call:
 * ./translation.php help
 *
 * $Horde: horde/po/translation.php,v 1.91.2.25 2008-07-29 06:55:09 jan Exp $
 */

function footer()
{
    global $c, $curdir;

    $c->writeln();
    $c->writeln('Please report any bugs to i18n@lists.horde.org.');

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
        $c->writeln('Usage:' . ' translation.php [options] ' . $cmd . ' [command-options]');
        if (!empty($cmd)) {
            $c->writeln();
            $c->writeln('Command options:');
        }
        switch ($cmd) {
        case 'cleanup':
            $c->writeln('  -l, --locale=ll_CC     Use only this locale.');
            $c->writeln('  -m, --module=MODULE    Cleanup PO files only for this (Horde) module.');
            break;
        case 'commit':
        case 'commit-help':
            $c->writeln('  -l, --locale=ll_CC     Use this locale.');
            $c->writeln('  -m, --module=MODULE    Commit translations only for this (Horde) module.');
            $c->writeln('  -M, --message=MESSAGE  Use this commit message instead of the default ones.');
            $c->writeln('  -n, --new              This is a new translation, commit also CREDITS,');
            $c->writeln('                         CHANGES and nls.php.dist.');
            break;
        case 'compendium':
            $c->writeln('  -a, --add=FILE        Add this PO file to the compendium. Useful to');
            $c->writeln('                        include a compendium from a different branch to');
            $c->writeln('                        the generated compendium.');
            $c->writeln('  -d, --directory=DIR   Create compendium in this directory.');
            $c->writeln('  -l, --locale=ll_CC    Use this locale.');
            break;
        case 'extract':
            $c->writeln('  -m, --module=MODULE  Generate POT file only for this (Horde) module.');
            break;
        case 'init':
            $c->writeln('  -l, --locale=ll_CC     Use this locale.');
            $c->writeln('  -m, --module=MODULE    Create a PO file only for this (Horde) module.');
            $c->writeln('  -c, --compendium=FILE  Use this compendium file instead of the default');
            $c->writeln('                         one (compendium.po in the horde/po directory).');
            $c->writeln('  -n, --no-compendium    Don\'t use a compendium.');
            break;
        case 'make':
            $c->writeln('  -l, --locale=ll_CC     Use only this locale.');
            $c->writeln('  -m, --module=MODULE    Build MO files only for this (Horde) module.');
            $c->writeln('  -c, --compendium=FILE  Merge new translations to this compendium file');
            $c->writeln('                         instead of the default one (compendium.po in the');
            $c->writeln('                         horde/po directory.');
            $c->writeln('  -n, --no-compendium    Don\'t merge new translations to the compendium.');
            $c->writeln('  -s, --statistics       Save translation statistics in a local file.');
            break;
        case 'make-help':
        case 'update-help':
            $c->writeln('  -l, --locale=ll_CC     Use only this locale.');
            $c->writeln('  -m, --module=MODULE    Update help files only for this (Horde) module.');
            break;
        case 'merge':
            $c->writeln('  -l, --locale=ll_CC     Use this locale.');
            $c->writeln('  -m, --module=MODULE    Merge PO files only for this (Horde) module.');
            $c->writeln('  -c, --compendium=FILE  Use this compendium file instead of the default');
            $c->writeln('                         one (compendium.po in the horde/po directory).');
            $c->writeln('  -n, --no-compendium    Don\'t use a compendium.');
            break;
        case 'update':
            $c->writeln('  -l, --locale=ll_CC     Use this locale.');
            $c->writeln('  -m, --module=MODULE    Update only this (Horde) module.');
            $c->writeln('  -c, --compendium=FILE  Use this compendium file instead of the default');
            $c->writeln('                         one (compendium.po in the horde/po directory).');
            $c->writeln('  -n, --no-compendium    Don\'t use a compendium.');
            break;
        }
    } else {
        $c->writeln('Usage:' . ' translation.php [options] command [command-options]');
        $c->writeln(str_repeat(' ', String::length('Usage:')) . ' translation.php [help|-h|--help] [command]');
        $c->writeln();
        $c->writeln('Helper application to create and maintain translations for the Horde');
        $c->writeln('framework and its applications.');
        $c->writeln('For an introduction read the file README in this directory.');
        $c->writeln();
        $c->writeln('Commands:');
        $c->writeln('  help        Show this help message.');
        $c->writeln('  compendium  Rebuild the compendium file. Warning: This overwrites the');
        $c->writeln('              current compendium.');
        $c->writeln('  extract     Generate PO template (.pot) files.');
        $c->writeln('  init        Create one or more PO files for a new locale. Warning: This');
        $c->writeln('              overwrites the existing PO files of this locale.');
        $c->writeln('  merge       Merge the current PO file with the current PO template file.');
        $c->writeln('  update      Run extract and merge sequent.');
        $c->writeln('  update-help Extract all new and changed entries from the English XML help');
        $c->writeln('              file and merge them with the existing ones.');
        $c->writeln('  cleanup     Cleans the PO files up from untranslated and obsolete entries.');
        $c->writeln('  make        Build binary MO files from the specified PO files.');
        $c->writeln('  make-help   Mark all entries in the XML help file being up-to-date and');
        $c->writeln('              prepare the file for the next execution of update-help. You');
        $c->writeln('              should only run make-help AFTER update-help and revising the');
        $c->writeln('              help file.');
        $c->writeln('  commit      Commit translations to the CVS server.');
        $c->writeln('  commit-help Commit help files to the CVS server.');
    }

    $c->writeln();
    $c->writeln('Options:');
    $c->writeln('  -b, --base=/PATH  Full path to the (Horde) base directory that should be');
    $c->writeln('                    used.');
    $c->writeln('  -d, --debug       Show error messages from the executed binaries.');
    $c->writeln('  -h, --help        Show this help message.');
    $c->writeln('  -t, --test        Show the executed commands but don\'t run anything.');
}

function check_binaries()
{
    global $gettext_version, $c;

    $c->writeln('Searching gettext binaries...');
    require_once 'System.php';
    foreach (array('gettext', 'msgattrib', 'msgcat', 'msgcomm', 'msgfmt', 'msginit', 'msgmerge', 'xgettext') as $binary) {
        echo $binary . '... ';
        $GLOBALS[$binary] = System::which($binary);
        if ($GLOBALS[$binary]) {
            $c->writeln($c->green('found: ') . $GLOBALS[$binary]);
        } else {
            $c->writeln($c->red('not found'));
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
        $c->writeln($c->red('Warning: ') . 'Your gettext version is too old and does not support PHP natively.');
        $c->writeln('Not all strings will be extracted.');
    } else {
        $GLOBALS['php_support'] = true;
        $c->writeln($c->green(' ' . 'OK'));
    }
    $c->writeln();
}

function search_file($file, $dir = '.', $local = false)
{
    static $ff;
    if (!isset($ff)) {
        $ff = new File_Find();
    }

    if (substr($file, 0, 1) != DS) {
        $file = "/$file/";
    }

    if ($local) {
        $files = $ff->glob($file, $dir, 'perl');
        $files = array_map(create_function('$file', 'return "' . $dir . DS . '" . $file;'), $files);
        return $files;
    } else {
        return $ff->search($file, $dir, 'perl', false);
    }
}

function search_ext($ext, $dir = '.', $local = false)
{
    return search_file("^[^.].*\\.$ext\$", $dir, $local);
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
    $dirs = array();
    $horde = false;
    if (is_dir(BASE . DS . 'po')) {
        $dirs[] = BASE;
        $horde = true;
    }
    $dh = opendir(BASE);
    if ($dh) {
        while ($entry = readdir($dh)) {
            $dir = BASE . DS . $entry;
            if (is_dir($dir) &&
                substr($entry, 0, 1) != '.' &&
                fileinode(HORDE_BASE) != fileinode($dir)) {
                $sub = opendir($dir);
                if ($sub) {
                    while ($subentry = readdir($sub)) {
                        if ($subentry == 'po' && is_dir($dir . DS . $subentry)) {
                            $dirs[] = $dir;
                            switch ($entry) {
                                case 'horde': $horde = true; break;
                                case 'imp': $imp_pos = count($dirs) - 1; break;
                                case 'dimp': $dimp_pos = count($dirs) - 1; break;
                                case 'mimp': $mimp_pos = count($dirs) - 1; break;
                            }
                            break;
                        }
                    }
                }
            }
        }
        if (!$horde) {
            array_unshift($dirs, HORDE_BASE);
        }
        if (isset($imp_pos)) {
            if (isset($dimp_pos) && $imp_pos < $dimp_pos) {
                $tmp = $dirs[$imp_pos];
                $dirs[$imp_pos] = $dirs[$dimp_pos];
                $dirs[$dimp_pos] = $tmp;
            } elseif (isset($mimp_pos) && $imp_pos < $mimp_pos) {
                $tmp = $dirs[$imp_pos];
                $dirs[$imp_pos] = $dirs[$mimp_pos];
                $dirs[$mimp_pos] = $tmp;
            }
        }
    }

    return $dirs;
}

function strip_horde($file)
{
    if (is_array($file)) {
        return array_map('strip_horde', $file);
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
        if (!empty($module) && $module != $apps[$i] &&
            (!in_array($module, array('dimp', 'mimp')) || $apps[$i] != 'imp')) {
            continue;
        }
        printf('Extracting from %s... ', $apps[$i]);
        chdir($dirs[$i]);
        if ($apps[$i] == 'horde') {
            $files = search_ext('php', '.', true);
            foreach (array('admin', 'framework', 'lib', 'services', 'templates', 'util', 'themes') as $search_dir) {
                $files = array_merge($files, search_ext('(php|inc|js)', $search_dir));
            }
            $files = array_merge($files, search_ext('dist', 'config'));
            $sh = $GLOBALS['xgettext'] . ' --language=' . $language .
                  ' --from-code=iso-8859-1 --keyword=_ --sort-output --copyright-holder="Horde Project"';
            if ($gettext_version[0] > 0 || $gettext_version[1] > 11) {
                $sh .= ' --msgid-bugs-address="dev@lists.horde.org"';
            }
            $file = $dirs[$i] . DS . 'po' . DS . $apps[$i] . '.pot';
            if (file_exists($file) && !is_writable($file)) {
                $c->writeln($c->red(sprintf('%s is not writable.', $file)));
                footer();
            }
            $tmp_file = $file . '.tmp.pot';
            $sh .= ' -o ' . $tmp_file . ' ' . implode(' ', $files);
            if (file_exists($dirs[$i] . '/po/translation.php')) {
                $sh .= ' po/translation.php';
            }
            if (!$debug) {
                $sh .= $silence;
            }
            if ($debug || $test) {
                $c->writeln('Executing:');
                $c->writeln($sh);
            }
            if (!$test) {
                exec($sh);
            }
        } else {
            $files = search_ext('(php|inc|js)');
            $files = array_filter($files, create_function('$file', 'return substr($file, 0, 9) != "." . DS . "config" . DS;'));
            $files = array_merge($files, search_ext('dist', 'config'));
            $sh = $GLOBALS['xgettext'] . ' --language=' . $language .
                  ' --keyword=_ --sort-output --force-po --copyright-holder="Horde Project"';
            if ($gettext_version[0] > 0 || $gettext_version[1] > 11) {
                $sh .= ' --msgid-bugs-address="dev@lists.horde.org"';
            }
            $file = 'po' . DS . $apps[$i] . '.pot';
            if (file_exists($file) && !is_writable($file)) {
                $c->writeln($c->red(sprintf('%s is not writable.', $file)));
                footer();
            }
            $tmp_file = $file . '.tmp.pot';
            $sh .= ' -o ' . $tmp_file . ' ' . implode(' ', $files) . ($debug ? '' : $silence);
            if ($debug || $test) {
                $c->writeln('Executing:');
                $c->writeln($sh);
            }
            if (!$test) {
                exec($sh);
            }
        }
        $diff = array();
        if (file_exists($tmp_file)) {
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
                                $c->writeln($c->red(sprintf("<gettext> tag not closed in file %s.\nOpening tag found in line %d.", $template, $lineno)));
                                break 2;
                            }
                        }
                        $buffer .= substr($line, $left, $end - $left);
                        if (!$test) {
                            fwrite($tmp, "#: $template:$lineno\n");
                            fwrite($tmp, 'msgid "' . str_replace(array('"', "\n"), array('\"', "\\n\"\n\""), $buffer) . "\"\n");
                            fwrite($tmp, 'msgstr ""' . "\n\n");
                        }
                        $offset = $end + 10;
                    }
                }
                fclose($fp);
            }
            if (!$test) fclose($tmp);
            $sh = $GLOBALS['msgcomm'] . " --more-than=0 --sort-output \"$tmp_file\" \"$file.templates\" --output-file \"$tmp_file\"" . $silence;
            if ($debug || $test) {
                $c->writeln('Executing:');
                $c->writeln($sh);
            }
            if (!$test) {
                exec($sh);
                unlink($file . '.templates');
            }

            /* Parse conf.xml files for <configphp> tags. */
            if (!$test) $tmp = fopen($file . '.config', 'w');
            $conf_content = file_get_contents('config/conf.xml');
            if (preg_match_all('/<configphp .*?>([^<]*_\(".+?"\)[^<]*)<\/configphp>/s',
                               $conf_content, $matches)) {
                foreach ($matches[1] as $configphp) {
                    if (preg_match_all('/_\("(.+?)"\)/', $configphp, $strings)) {
                        if (!$test) {
                            foreach ($strings[1] as $string) {
                                fwrite($tmp, "#: config/conf.xml\n");
                                fwrite($tmp, 'msgid "' . $string . "\"\n");
                                fwrite($tmp, 'msgstr ""' . "\n\n");
                            }
                        }
                    }
                }
            }
            if (!$test) fclose($tmp);
            $sh = $GLOBALS['msgcomm'] . " --more-than=0 --sort-output \"$tmp_file\" \"$file.config\" --output-file \"$tmp_file\"" . $silence;
            if ($debug || $test) {
                $c->writeln('Executing:');
                $c->writeln($sh);
            }
            if (!$test) {
                exec($sh);
                unlink($file . '.config');
            }

            /* Check if the new .pot file has any changed content at all. */
            if (file_exists($file)) {
                $diff = array_merge(array_diff(file($tmp_file), file($file)),
                                    array_diff(file($file), file($tmp_file)));
                $diff = preg_grep('/^"POT-Creation-Date:/', $diff, PREG_GREP_INVERT);
            }
        }
        if (!file_exists($file) || count($diff)) {
            if (file_exists($file)) {
                unlink($file);
            }
            rename($tmp_file, $file);
            $c->writeln($c->green('updated'));
        } else {
            if (file_exists($tmp_file)) {
                unlink($tmp_file);
            }
            $c->writeln($c->bold('not changed'));
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
        $c->writeln($c->red('Error: ' . 'No locale specified.'));
        $c->writeln();
        usage();
        footer();
    }

    cleanup();

    for ($i = 0; $i < count($dirs); $i++) {
        if (!empty($module) && $module != $apps[$i] &&
            (!in_array($module, array('dimp', 'mimp')) || $apps[$i] != 'imp')) {
            continue;
        }
        $c->writeln(sprintf('Merging translation for module %s...', $c->bold($apps[$i])));
        $dir = $dirs[$i] . DS . 'po' . DS;
        if (empty($lang)) {
            $langs = get_languages($dirs[$i]);
        } else {
            if (!file_exists($dir . $lang . '.po')) {
                $c->writeln('Skipped...');
                $c->writeln();
                continue;
            }
            $langs = array($lang);
        }
        foreach ($langs as $locale) {
            $c->writeln(sprintf('Merging locale %s... ', $c->bold($locale)));
            $sh = $GLOBALS['msgmerge'] . ' --update -v' . $compendium . ' "' . $dir . $locale . '.po" "' . $dir . $apps[$i] . '.pot"';
            if ($debug || $test) {
                $c->writeln('Executing:');
                $c->writeln($sh);
            }
            if (!$test) exec($sh);
            $c->writeln($c->green('done'));
        }
    }
}

function status()
{
    return;
    global $cmd_options, $apps, $dirs, $debug, $test, $c;

    $output = 'status.html';
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
        if (!empty($module) && $module != $apps[$i] &&
            (!in_array($module, array('dimp', 'mimp')) || $apps[$i] != 'imp')) {
            continue;
        }
        $c->writeln(sprintf('Generating status for module %s...', $c->bold($apps[$i])));
        if (empty($lang)) {
            $langs = get_languages($dirs[$i]);
        } else {
            if (!file_exists($dirs[$i] . DS . 'po' . DS . $lang . '.po')) {
                $c->writeln('Skipped...');
                $c->writeln();
                continue;
            }
            $langs = array($lang);
        }
        foreach ($langs as $locale) {
            $c->writeln(sprintf('Status for locale %s... ', $c->bold($locale)));
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
            $add .= ' ' . $option[1];
            break;
        }
    }
    if (!isset($lang)) {
        $c->writeln($c->red('Error: ' . 'No locale specified.'));
        $c->writeln();
        usage();
        footer();
    }
    printf('Merging all %s.po files to the compendium... ', $lang);
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
        $c->writeln('Executing:');
        $c->writeln($sh);
    }
    if ($test) {
        $ret = 0;
    } else {
        exec($sh, $out, $ret);
    }
    if ($ret == 0) {
        $c->writeln($c->green('done'));
    } else {
        $c->writeln($c->red('failed'));
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
    if (empty($lang)) {
        $lang = getenv('LANG');
    }
    for ($i = 0; $i < count($dirs); $i++) {
        if (!empty($module) && $module != $apps[$i] &&
            (!in_array($module, array('dimp', 'mimp')) || $apps[$i] != 'imp')) {
            continue;
        }
        $package = ucfirst($apps[$i]);
        $package_u = String::upper($apps[$i]);
        include $dirs[$i] . '/lib/version.php';
        $version = defined($package_u . '_VERSION') ? constant($package_u . '_VERSION') : '???';
        printf('Initializing module %s... ', $apps[$i]);
        if (!file_exists($dirs[$i] . '/po/' . $apps[$i] . '.pot')) {
            $c->writeln($c->red('failed'));
            $c->writeln(sprintf('%s not found. Run \'translation extract\' first.', $dirs[$i] . DS . 'po' . DS . $apps[$i] . '.pot'));
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
            $c->writeln('Executing:');
            $c->writeln($sh);
        }
        if ($test) {
            $ret = 0;
        } else {
            exec($sh, $out, $ret);
        }
        rename($pofile . '.tmp', $pofile);
        if ($ret == 0) {
            $c->writeln($c->green('done'));
        } else {
            $c->writeln($c->red('failed'));
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
    $horde = array_search('horde', $apps);
    $horde_msg = array();
    $stats_array = array();

    require_once 'Console/Table.php';
    $stats = new Console_Table();
    $stats->setHeaders(array('Module', 'Language', 'Translated', 'Fuzzy', 'Untranslated', 'Updated'));

    for ($i = 0; $i < count($dirs); $i++) {
        if (!empty($module) && $module != $apps[$i] &&
            (!in_array($module, array('dimp', 'mimp')) || $apps[$i] != 'imp')) {
            continue;
        }
        $c->writeln(sprintf('Building MO files for module %s...', $c->bold($apps[$i])));
        if (empty($lang)) {
            $langs = get_languages($dirs[$i]);
        } else {
            if (!file_exists($dirs[$i] . DS . 'po' . DS . $lang . '.po')) {
                $c->writeln('Skipped...');
                $c->writeln();
                continue;
            }
            $langs = array($lang);
        }
        foreach ($langs as $locale) {
            $c->writeln(sprintf('Building locale %s... ', $c->bold($locale)));
            $dir = $dirs[$i] . DS . 'locale' . DS . $locale . DS . 'LC_MESSAGES';
            if (!is_dir($dir)) {
                require_once 'System.php';
                if ($debug) {
                    $c->writeln(sprintf('Making directory %s', $dir));
                }
                if (!$test && !System::mkdir("-p $dir")) {
                    $c->writeln($c->red('Warning: ') . sprintf('Could not create locale directory for locale %s:', $locale));
                    $c->writeln($dir);
                    $c->writeln();
                    continue;
                }
            }

            /* Convert to unix linebreaks. */
            $pofile = $dirs[$i] . DS . 'po' . DS . $locale . '.po';
            $content = file_get_contents($pofile);
            $content = str_replace("\r", '', $content);
            $fp = fopen($pofile, 'wb');
            fwrite($fp, $content);
            fclose($fp);

            /* Remember update date. */
            $last_update = preg_match(
                '/^"PO-Revision-Date: (\d{4}-\d{2}-\d{2})/m',
                $content, $matches)
                ? $matches[1] : '';

            /* Check PO file sanity. */
            $sh = $GLOBALS['msgfmt'] . " --check \"$pofile\"$redir_err";
            if ($debug || $test) {
                $c->writeln('Executing:');
                $c->writeln($sh);
            }
            if ($test) {
                $ret = 0;
            } else {
                exec($sh, $out, $ret);
            }
            if ($ret != 0) {
                $c->writeln($c->red('Warning: ') . 'an error has occured:');
                $c->writeln(implode("\n", $out));
                $c->writeln();
                if ($apps[$i] == 'horde') {
                    continue 2;
                }
                continue;
            }

            /* Compile MO file. */
            $sh = $GLOBALS['msgfmt'] . ' --statistics -o "' . $dir . DS . $apps[$i] . '.mo" ';
            if ($apps[$i] != 'horde') {
                $horde_po = $dirs[$horde] . DS . 'po' . DS . $locale . '.po';
                if (!is_readable($horde_po)) {
                    $c->writeln($c->red('Warning: ') . sprintf('the Horde PO file for the locale %s does not exist:', $locale));
                    $c->writeln($horde_po);
                    $c->writeln();
                    $sh .= $dirs[$i] . DS . 'po' . DS . $locale . '.po';
                } else {
                    $comm = $GLOBALS['msgcomm'] . " --more-than=0 --sort-output \"$pofile\"";
                    if ($apps[$i] == 'imp') {
                        $dimp = array_search('dimp', $apps);
                        if ($dimp !== false) {
                            $dimp_po = $dirs[$dimp] . DS . 'po' . DS . $locale . '.po';
                            if (is_readable($dimp_po)) {
                                $comm .= ' "' . $dimp_po . '"';
                            }
                        }

                        $mimp = array_search('mimp', $apps);
                        if ($mimp !== false) {
                            $mimp_po = $dirs[$mimp] . DS . 'po' . DS . $locale . '.po';
                            if (is_readable($mimp_po)) {
                                $comm .= ' "' . $mimp_po . '"';
                            }
                        }
                    }
                    $sh = $comm . " \"$horde_po\" | $sh -";
                }
            } else {
                $sh .= $pofile;
            }
            $sh .= $redir_err;
            if ($debug || $test) {
                $c->writeln('Executing:');
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
                $c->writeln($c->green('done'));
                $messages = array(0, 0, 0, $last_update);
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
                $stats->addRow(array($apps[$i], $locale, $messages[0], $messages[1], $messages[2], $messages[3]));
            } else {
                $c->writeln($c->red('failed'));
                exec($sh, $out, $ret);
                $c->writeln(implode("\n", $out));
            }
            if (count($langs) > 1) {
                continue;
            }

            /* Merge translation into compendium. */
            if (!empty($compendium)) {
                printf('Merging the PO file for %s to the compendium... ', $c->bold($apps[$i]));
                if (!empty($dir) && substr($dir, -1) != DS) {
                    $dir .= DS;
                }
                $sh = $GLOBALS['msgcat'] . " --sort-output \"$compendium\" \"$pofile\" > \"$compendium.tmp\"";
                if (!$debug) {
                    $sh .= $silence;
                }
                if ($debug || $test) {
                    $c->writeln();
                    $c->writeln('Executing:');
                    $c->writeln($sh);
                }
                $out = '';
                if ($test) {
                    $ret = 0;
                } else {
                    exec($sh, $out, $ret);
                }
                unlink($compendium);
                rename($compendium . '.tmp', $compendium);
                if ($ret == 0) {
                    $c->writeln($c->green('done'));
                } else {
                    $c->writeln($c->red('failed'));
                }
            }
            $c->writeln();
        }
    }
    if (empty($module)) {
        $c->writeln('Results:');
    } else {
        $c->writeln('Results (including Horde):');
    }
    $c->writeln($stats->getTable());
    if ($save_stats) {
        $fp = fopen('translation_stats.txt', 'w');
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
        if (!empty($module) && $module != $apps[$i] &&
            (!in_array($module, array('dimp', 'mimp')) || $apps[$i] != 'imp')) {
            continue;
        }
        $c->writeln(sprintf('Cleaning up PO files for module %s...', $c->bold($apps[$i])));
        if (empty($lang)) {
            $langs = get_languages($dirs[$i]);
        } else {
            if (!file_exists($dirs[$i] . DS . 'po' . DS . $lang . '.po')) {
                $c->writeln('Skipped...');
                $c->writeln();
                continue;
            }
            $langs = array($lang);
        }
        foreach ($langs as $locale) {
            $c->writeln(sprintf('Cleaning up locale %s... ', $c->bold($locale)));
            $pofile = $dirs[$i] . DS . 'po' . DS . $locale . '.po';
            $sh = $GLOBALS['msgattrib'] . ($keep_untranslated ? '' : ' --translated') . " --no-obsolete --force-po $pofile > $pofile.tmp";
            if (!$debug) {
                $sh .= $silence;
            }
            if ($debug || $test) {
                $c->writeln();
                $c->writeln('Executing:');
                $c->writeln($sh);
            }
            $out = '';
            if ($test) {
                $ret = 0;
            } else {
                exec($sh, $out, $ret);
            }
            if ($ret == 0) {
                unlink($pofile);
                rename($pofile . '.tmp', $pofile);
                $c->writeln($c->green('done'));
            } else {
                unlink($pofile . '.tmp', $pofile);
                $c->writeln($c->red('failed'));
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
        if (!empty($module) && $module != $apps[$i] &&
            (!in_array($module, array('dimp', 'mimp')) || $apps[$i] != 'imp')) {
            continue;
        }
        if ($apps[$i] == 'horde') {
            $dirs[] = $dirs[$i] . DS . 'admin';
            $apps[] = 'horde/admin';
            if (!empty($module)) {
                $module = 'horde/admin';
            }
        }
        if (empty($lang)) {
            if ($help_only) {
                $files = array_merge($files, strip_horde(search_ext('xml', $dirs[$i] . DS . 'locale')));
            } else {
                $files = array_merge($files, strip_horde(get_po_files($dirs[$i] . DS . 'po')));
                $files = array_merge($files, strip_horde(search_file('^[a-z]{2}_[A-Z]{2}', $dirs[$i] . DS . 'locale', true)));
            }
        } else {
            if ($help_only) {
                if (!file_exists($dirs[$i] . DS . 'locale' . DS . $lang . DS . 'help.xml')) {
                    continue;
                }
            } else {
                if (!file_exists($dirs[$i] . '/po/' . $lang . '.po')) {
                    continue;
                }
                $files[] = strip_horde($dirs[$i] . DS . 'po' . DS . $lang . '.po');
            }
            $files[] = strip_horde($dirs[$i] . DS . 'locale' . DS . $lang);
        }
        if ($docs && !$help_only && $apps[$i]) {
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
            $c->writeln('Adding new files to repository:');
            $add_files = array();
            foreach ($files as $file) {
                if (strstr($file, 'locale') || strstr($file, '.po')) {
                    $add_files[] = $file;
                    $c->writeln($file);
                }
            }
            foreach ($files as $file) {
                if (strstr($file, 'locale')) {
                    if ($help_only) {
                        $add_files[] = $file . DS . '*.xml';
                        $c->writeln($file . DS . '*.xml');
                    } else {
                        $add_files[] = $file . DS . '*.xml ' . $file . DS . 'LC_MESSAGES';
                        $c->writeln($file . DS . "*.xml\n$file" . DS . 'LC_MESSAGES');
                    }
                }
            }
            if (!$help_only) {
                foreach ($files as $file) {
                    if (strstr($file, 'locale')) {
                        $add = $file . DS . 'LC_MESSAGES' . DS . '*.mo';
                        $add_files[] = $add;
                        $c->writeln($add);
                    }
                }
            }
            $c->writeln();
            foreach ($add_files as $add_file) {
                if ($debug || $test) {
                    $c->writeln('Executing:');
                    $c->writeln('cvs add ' . $add_file);
                }
                if (!$test) {
                    system('cvs add ' . $add_file);
                }
            }
            $c->writeln();
        }
        $c->writeln('Committing:');
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
            $c->writeln('Executing:');
            $c->writeln($sh);
        }
        if (!$test) system($sh);
    }
}

function update_help()
{
    global $cmd_options, $dirs, $apps, $debug, $test, $last_error_msg, $c;

    require_once 'Horde/DOM.php';

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
        if (!empty($module) && $module != $apps[$i] &&
            (!in_array($module, array('dimp', 'mimp')) || $apps[$i] != 'imp')) {
            continue;
        }
        if (!is_dir("$dirs[$i]/locale")) {
            continue;
        }
        if ($apps[$i] == 'horde') {
            $dirs[] = $dirs[$i] . DS . 'admin';
            $apps[] = 'horde/admin';
            if (!empty($module)) {
                $module = 'horde/admin';
            }
        }
        if (empty($lang)) {
            $files = search_file('help.xml', $dirs[$i] . DS . 'locale');
        } else {
            $files = array($dirs[$i] . DS . 'locale' . DS . $lang . DS . 'help.xml');
        }
        $file_en  = $dirs[$i] . DS . 'locale' . DS . 'en_US' . DS . 'help.xml';
        if (!file_exists($file_en)) {
            $c->writeln(wordwrap($c->red('Warning: ') . sprintf('There doesn\'t yet exist a help file for %s.', $c->bold($apps[$i]))));
            $c->writeln();
            continue;
        }
        foreach ($files as $file_loc) {
            $locale = substr($file_loc, 0, strrpos($file_loc, DS));
            $locale = substr($locale, strrpos($locale, DS) + 1);
            if ($locale == 'en_US') {
                continue;
            }
            if (!file_exists($file_loc)) {
                $c->writeln(wordwrap($c->red('Warning: ') . sprintf('The %s help file for %s doesn\'t yet exist. Creating a new one.', $c->bold($locale), $c->bold($apps[$i]))));
                $dir_loc = substr($file_loc, 0, -9);
                if (!is_dir($dir_loc)) {
                    require_once 'System.php';
                    if ($debug || $test) {
                        $c->writeln(sprintf('Making directory %s', $dir_loc));
                    }
                    if (!$test && !System::mkdir("-p $dir_loc")) {
                        $c->writeln($c->red('Warning: ') . sprintf('Could not create locale directory for locale %s:', $locale));
                        $c->writeln($dir_loc);
                        $c->writeln();
                        continue;
                    }
                }
                if ($debug || $test) {
                    $c->writeln(wordwrap(sprintf('Copying %s to %s', $file_en, $file_loc)));
                }
                if (!$test && !copy($file_en, $file_loc)) {
                    $c->writeln($c->red('Warning: ') . sprintf('Could not copy %s to %s', $file_en, $file_loc));
                }
                $c->writeln();
                continue;
            }
            $c->writeln(sprintf('Updating %s help file for %s.', $c->bold($locale), $c->bold($apps[$i])));
            $fp = fopen($file_loc, 'r');
            $line = fgets($fp);
            fclose($fp);
            if (!strstr($line, '<?xml')) {
                $c->writeln(wordwrap($c->red('Warning: ') . sprintf('The help file %s didn\'t start with <?xml', $file_loc)));
                $c->writeln();
                continue;
            }
            $encoding = '';
            if (preg_match('/encoding=(["\'])([^\\1]+)\\1/', $line, $match)) {
                $encoding = $match[2];
            }
            $doc_en = Horde_DOM_Document::factory(array('filename' => $file_en));
            if (!is_object($doc_en)) {
                $c->writeln(wordwrap($c->red('Warning: ') . sprintf('There was an error opening the file %s. Try running translation.php with the flag -d to see any error messages from the xml parser.', $file_en)));
                $c->writeln();
                continue 2;
            }
            $doc_loc = Horde_DOM_Document::factory(array('filename' => $file_loc));
            if (!is_object($doc_loc)) {
                $c->writeln(wordwrap($c->red('Warning: ') . sprintf('There was an error opening the file %s. Try running translation.php with the flag -d to see any error messages from the xml parser.', $file_loc)));
                $c->writeln();
                continue;
            }
            $doc_new  = Horde_DOM_Document::factory();
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
            $c->writeln(wordwrap(sprintf('Entries: %d total, %d up-to-date, %d new, %d changed, %d unknown',
                                     $count_uptodate + $count_new + $count_changed + $count_unknown,
                                     $count_uptodate, $count_new, $count_changed, $count_unknown)));
            $doc_new->append_child($help_new);
            $output = $doc_new->dump_mem(true, $encoding);
            if ($debug || $test) {
                $c->writeln(wordwrap(sprintf('Writing updated help file to %s.', $file_loc)));
            }
            if (!$test) {
                $fp = fopen($file_loc, 'w');
                $line = fwrite($fp, $output);
                fclose($fp);
            }
            $c->writeln(sprintf('%d bytes written.', strlen($output)));
            $c->writeln();
        }
    }
}

function make_help()
{
    global $cmd_options, $dirs, $apps, $debug, $test, $c;

    require_once 'Horde/DOM.php';

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
        if (!empty($module) && $module != $apps[$i] &&
            (!in_array($module, array('dimp', 'mimp')) || $apps[$i] != 'imp')) {
            continue;
        }
        if (!is_dir("$dirs[$i]/locale")) continue;
        if ($apps[$i] == 'horde') {
            $dirs[] = $dirs[$i] . DS . 'admin';
            $apps[] = 'horde/admin';
            if (!empty($module)) {
                $module = 'horde/admin';
            }
        }
        if (empty($lang)) {
            $files = search_file('help.xml', $dirs[$i] . DS . 'locale');
        } else {
            $files = array($dirs[$i] . DS . 'locale' . DS . $lang . DS . 'help.xml');
        }
        $file_en  = $dirs[$i] . DS . 'locale' . DS . 'en_US' . DS . 'help.xml';
        if (!file_exists($file_en)) {
            continue;
        }
        foreach ($files as $file_loc) {
            if (!file_exists($file_loc)) {
                $c->writeln('Skipped...');
                $c->writeln();
                continue;
            }
            $locale = substr($file_loc, 0, strrpos($file_loc, DS));
            $locale = substr($locale, strrpos($locale, DS) + 1);
            if ($locale == 'en_US') continue;
            $c->writeln(sprintf('Updating %s help file for %s.', $c->bold($locale), $c->bold($apps[$i])));
            $fp = fopen($file_loc, 'r');
            $line = fgets($fp);
            fclose($fp);
            if (!strstr($line, '<?xml')) {
                $c->writeln(wordwrap($c->red('Warning: ') . sprintf('The help file %s didn\'t start with <?xml', $file_loc)));
                $c->writeln();
                continue;
            }
            $encoding = '';
            if (preg_match('/encoding=(["\'])([^\\1]+)\\1/', $line, $match)) {
                $encoding = $match[2];
            }
            $doc_en = Horde_DOM_Document::factory(array('filename' => $file_en));
            if (!is_object($doc_en)) {
                $c->writeln(wordwrap($c->red('Warning: ') . sprintf('There was an error opening the file %s. Try running translation.php with the flag -d to see any error messages from the xml parser.', $file_en)));
                $c->writeln();
                continue 2;
            }
            $doc_loc = Horde_DOM_Document::factory(array('filename' => $file_loc));
            if (!is_object($doc_loc)) {
                $c->writeln(wordwrap($c->red('Warning: ') . sprintf('There was an error opening the file %s. Try running translation.php with the flag -d to see any error messages from the xml parser.', $file_loc)));
                $c->writeln();
                continue;
            }
            $help_loc  = $doc_loc->document_element();
            $md5_en    = array();
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
                    $c->writeln(wordwrap($c->red('Warning: ') . sprintf('No entry with the id "%s" exists in the original help file.', $id)));
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
            $c->writeln(sprintf('%d of %d entries marked as up-to-date', $count, $count_all));
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
    $c->fatal('This script must be run from the command line.');
}
$c->init();

$c->writeln($c->bold('---------------------------'));
$c->writeln($c->bold('Horde translation generator'));
$c->writeln($c->bold('---------------------------'));

/* Sanity checks */
if (!extension_loaded('gettext')) {
    $c->writeln($c->red('Gettext extension not found!'));
    footer();
}

$c->writeln('Loading libraries...');
$libs_found = true;

foreach (array('Console_Getopt' => 'Console/Getopt.php',
               'Console_Table'  => 'Console/Table.php',
               'File_Find'      => 'File/Find.php')
         as $class => $file) {
    echo $class . '... ';
    include $file;
    if (class_exists($class)) {
        $c->writeln($c->green('OK'));
    } else {
        $c->writeln($c->red(sprintf('%s not found.', $class)));
        $libs_found = false;
    }
}

if (!$libs_found) {
    $c->writeln();
    $c->writeln('Make sure that you have PEAR installed and in your include path.');
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
    $c->writeln($c->red('Getopt Error: ' . str_replace('Console_Getopt:', '', $options->getMessage())));
    $c->writeln();
    usage();
    footer();
}
if (empty($options[0][0]) && empty($options[1][0])) {
    $c->writeln($c->red('Error: ' . 'No command specified.'));
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
    'init'       => array('hl:m:nc:', array('module=', 'locale=', 'no-compendium', 'compendium=')),
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
        $c->writeln($c->red('Error: ' . str_replace('Console_Getopt:', '', $cmd_options->getMessage())));
        $c->writeln();
        usage();
        footer();
    }
}

/* Searching applications */
check_binaries();

$c->writeln(sprintf('Searching Horde applications in %s', BASE));
$dirs = search_applications();

if ($debug) {
    $c->writeln('Found directories:');
    $c->writeln(implode("\n", $dirs));
}

$apps = strip_horde($dirs);
$apps[0] = 'horde';
$c->writeln(wordwrap(sprintf('Found applications: %s', implode(', ', $apps))));
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
    merge();
    break;
default:
    $c->writeln($c->red('Error: ') . sprintf('Unknown command: %s', $cmd));
    $c->writeln();
    usage();
    footer();
}

footer();
