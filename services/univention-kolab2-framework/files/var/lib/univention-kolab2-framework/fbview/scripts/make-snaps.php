#!/usr/local/bin/php -f
<?php
// $Horde: horde/scripts/make-snaps.php,v 1.17 2004/03/12 15:18:58 chuck Exp $

$modules = array('accounts',
                 'agora',
                 'ansel',
                 'babel',
                 'chora',
                 'forwards',
                 'framework',
                 'genie',
                 'giapeto',
                 'gollem',
                 'hermes',
                 'horde',
                 'HordeConduit',
                 'imapproxy',
                 'imp',
                 'ingo',
                 'jeta',
                 'jonah',
                 'juno',
                 'klutz',
                 'kronolith',
                 'luxor',
                 'midas',
                 'mimp',
                 'mnemo',
                 'mottle',
                 'nag',
                 'nic',
                 'odin',
                 'orator',
                 'passwd',
                 'rakim',
                 'sam',
                 'scry',
                 'skeleton',
                 'swoosh',
                 'thor',
                 'trean',
                 'troll',
                 'turba',
                 'ulaform',
                 'vacation',
                 'vilma',
                 'whups',
                 'whupsey',
                 'wicked');

$stable = array('accounts'  => 'RELENG_2',
                'chora'     => 'RELENG_1',
                'forwards'  => 'RELENG_2',
                'horde'     => 'RELENG_2',
                'imp'       => 'RELENG_3',
                'ingo'      => 'RELENG_1',
                'klutz'     => 'RELENG_1',
                'kronolith' => 'RELENG_1',
                'mnemo'     => 'RELENG_1',
                'nag'       => 'RELENG_1',
                'passwd'    => 'RELENG_2',
                'turba'     => 'RELENG_1',
                'vacation'  => 'RELENG_2');

$dir = date('Y-m-d');
if (!is_dir($dir)) {
    mkdir($dir);
}

exportCVS();
makeTarballs();
cleanup();
prune(7);

// Update latest/ symlink.
system("ln -sfh $dir latest");


/**
 * Functions
 */
function exportCVS()
{
    global $dir, $modules, $stable;

    foreach ($modules as $module) {
        system("cd $dir; cvs -Q export -r HEAD $module > /dev/null");
        if (array_key_exists($module, $stable)) {
            system("cd $dir; cvs -Q export -r $stable[$module] -d ${module}-RELENG $module");
        }
    }
}

function makeTarballs()
{
    global $dir, $modules, $stable;

    foreach ($modules as $module) {
        system("cd $dir; tar -zcf ${module}-HEAD-${dir}.tar.gz $module");
        if (array_key_exists($module, $stable)) {
            system("cd $dir; tar -zcf ${module}-RELENG-${dir}.tar.gz ${module}-RELENG");
        }
    }
}

function cleanup()
{
    global $dir, $modules;

    foreach ($modules as $module) {
        system("rm -rf $dir/$module");
        system("rm -rf $dir/${module}-RELENG");
    }
}

function prune($keep)
{
    if ($cwd = opendir(getcwd())) {
        $dirs = array();

        # Build a list of all the YYYY-MM-DD directories in this directory.
        while (false !== ($entry = readdir($cwd))) {
            if (is_dir($entry) && preg_match('/^\d+\-\d+\-\d+/', $entry)) {
                array_push($dirs, $entry);
            }
        }
        closedir($cwd);

        # Reverse-sort the list and remove the number of directories that we
        # want to keep (which will be the first $keep number of elements).
        rsort($dirs);
        $dirs = array_slice($dirs, $keep);

        # Prune (recursively delete) the rest of the directories in the list.
        foreach ($dirs as $dir) {
            system("rm -rf $dir");
        }
    }
}
