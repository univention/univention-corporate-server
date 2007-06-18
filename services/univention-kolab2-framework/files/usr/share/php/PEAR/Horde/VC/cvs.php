<?php

require_once dirname(__FILE__) . '/rcs.php';

/**
 * VC_cvs implementation.
 *
 * Copyright 2000-2004 Anil Madhavapeddy, <anil@recoil.org>
 *
 * $Horde: framework/VC/VC/cvs.php,v 1.22 2004/05/28 18:41:21 chuck Exp $
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @version $Revision: 1.1.2.1 $
 * @package VC
 */
class VC_cvs extends VC_rcs {

    /**
     * Constructor.
     *
     * @param array $params  Any parameter the class expects.
     *                       <pre>
     *                       Current parameters:
     *                       'sourceroot': The source root for this
     *                                     repository
     *                       'paths': Hash with the locations of all
     *                                necessary binaries: 'rcsdiff', 'rlog',
     *                                'cvsps', 'cvsps_home' and the temp
     *                                path: 'temp'
     *                       </pre>
     */
    function VC_cvs($params)
    {
        $this->_sourceroot = $params['sourceroot'];
        $this->_paths = $params['paths'];
    }

    function isFile($where)
    {
        return @is_file($where . ',v');
    }

    function &queryDir($where)
    {
        return new VC_Directory_cvs($this, $where);
    }

    function getCheckout($file, $rev)
    {
        return VC_Checkout_cvs::get($this, $file->queryFullPath(), $rev);
    }

    function &getDiff(&$file, $rev1, $rev2, $type = 'context', $num = 3, $ws = true)
    {
        return VC_Diff_cvs::get($this, $file, $rev1, $rev2, $type, $num, $ws);
    }

    function &getFileObject($filename, $cache = null, $quicklog = false)
    {
        if (substr($filename, 0, 1) != '/') {
            $filename = '/' . $filename;
        }
        return VC_File_cvs::getFileObject($this, $this->sourceroot() . $filename, $cache, $quicklog);
    }

    function &getAnnotateObject($filename)
    {
        return new VC_Annotate_cvs($this, $filename, Util::getTempFile('vc', true, $this->_paths['temp']));
    }

    function &getPatchsetObject($filename, $cache = null)
    {
        return VC_Patchset_cvs::getPatchsetObject($this, $this->sourceroot() . '/' . $filename, $cache);
    }

}

/**
 * VC_cvs annotate class.
 *
 * Anil Madhavapeddy, <anil@recoil.org>
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @version $Revision: 1.1.2.1 $
 * @package VC
 */
class VC_Annotate_cvs {

    var $file;
    var $rep;
    var $tmpfile;

    function VC_Annotate_cvs(&$rep, $file, $tmpfile)
    {
        $this->rep = &$rep;
        $this->file = &$file;
        $this->tmpfile = $tmpfile;
    }

    function doAnnotate($rev)
    {
        /* Make sure that the file values for this object is valid. */
        if (is_a($this->file, 'PEAR_Error')) {
            return false;
        }

        /* Make sure that the cvsrep parameter is valid. */
        if (is_a($this->rep, 'PEAR_Error')) {
            return false;
        }

        if (!VC_Revision::valid($rev)) {
            return false;
        }

        $where = $this->file->queryModulePath();
        $sourceroot = $this->rep->sourceroot();

        $pipe = popen($this->rep->getPath('cvs') . ' -n server > ' . $this->tmpfile, OS_WINDOWS ? 'wb' : 'w');

        $out = array();
        $out[] = "Root $sourceroot";
        $out[] = 'Valid-responses ok error Valid-requests Checked-in Updated Merged Removed M E';
        $out[] = 'UseUnchanged';
        $out[] = 'Argument -r';
        $out[] = "Argument $rev";
        $out[] = "Argument $where";
        $dirs = explode('/', dirname($where));
        while (count($dirs)) {
            $out[] = 'Directory ' . implode('/', $dirs);
            $out[] = "$sourceroot/" . implode('/', $dirs);
            array_pop($dirs);
        }
        $out[] = 'Directory .';
        $out[] = $sourceroot;
        $out[] = 'annotate';

        foreach ($out as $line) {
            fwrite($pipe, "$line\n");
        }
        pclose($pipe);

        if (!($fl = fopen($this->tmpfile, OS_WINDOWS ? 'rb' : 'r'))) {
            return false;
        }

        $lines = array();
        $line = fgets($fl, 4096);

        // Windows versions of cvs always return $where with forwards
        // slashes.
        if (OS_WINDOWS) {
            $where = str_replace(DIRECTORY_SEPARATOR, '/', $where);
        }

        while ($line && !preg_match("|^E\s+Annotations for $where|", $line)) {
            $line = fgets($fl, 4096);
        }

        if (!$line) {
            return PEAR::raiseError(sprintf(_("Unable to annotate; server said: %s"), $line));
        }

        $lineno = 1;
        while ($line = fgets($fl, 4096)) {
            if (preg_match('/^M\s+([\d\.]+)\s+\((.+)\s+(\d+-\w+-\d+)\):.(.*)$/', $line, $regs)) {
                $entry = array();
                $entry['rev']    = $regs[1];
                $entry['author'] = $regs[2];
                $entry['date']   = $regs[3];
                $entry['line']   = $regs[4];
                $entry['lineno'] = $lineno++;
                $lines[] = $entry;
            }
        }

        fclose($fl);
        return $lines;
    }

}

/**
 * VC_cvs checkout class.
 *
 * See the README file that came with this library for more
 * information, and read the inline documentation.
 *
 * Anil Madhavapeddy, <anil@recoil.org>
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @version $Revision: 1.1.2.1 $
 * @package VC
 */
class VC_Checkout_cvs {

    /**
     * Static function which returns a file pointing to the head of the
     * requested revision of an RCS file.
     *
     * @param object VC_cvs $rep  A repository object
     * @param string $fullname    Fully qualified pathname of the desired RCS
     *                            file to checkout
     * @param string $rev         RCS revision number to check out
     *
     * @return resource|object  Either a PEAR_Error object, or a stream
     *                          pointer to the head of the checkout
     */
    function get(&$rep, $fullname, $rev)
    {
        if (!VC_Revision::valid($rev)) {
            return PEAR::raiseError(_("Invalid revision number"));
        }

        if (OS_WINDOWS) {
            $Q = '"';
            $mode = 'rb';
            $fullname = str_replace('\\', '/', $fullname);
        } else {
            $Q = "'";
            $mode = 'r';
        }

        if (!($RCS = popen($rep->getPath('co') . " -p$rev $Q$fullname$Q 2>&1", $mode))) {
            return PEAR::raiseError(_("Couldn't perform checkout of the requested file"));
        }

        /* First line from co should be of the form :
         * /path/to/filename,v  -->  standard out
         * and we check that this is the case and error otherwise
         */

        $co = fgets($RCS, 1024);
        if (!preg_match('/^([\S ]+),v\s+-->\s+st(andar)?d ?out(put)?\s*$/', $co, $regs) || $regs[1].',v' != $fullname) {
            return PEAR::raiseError(sprintf(_("Unexpected output from Checkout: %s"), $co));
        }

        /* Next line from co is of the form:
         * revision 1.2.3
         * TODO: compare this to $rev for consistency, atm we just
         *       discard the value to move input pointer along - avsm
         */
        $co = fgets($RCS, 1024);

        return $RCS;
    }

}

/**
 * VC_cvs diff class.
 *
 * Copyright Anil Madhavapeddy, <anil@recoil.org>
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @package VC
 */
class VC_Diff_cvs {

    /**
     * Obtain the differences between two revisions within a file.
     *
     * @param object VC_cvs $rep        A repository object
     * @param object VC_File_cvs $file  The desired file
     * @param strint $rev1              Original revision number to compare
     *                                  from
     * @param string $rev2              New revision number to compare against
     * @param string $type              The type of diff (e.g. 'unified')
     * @param int $num                  Number of lines to be used in context
     *                                  and unified diff
     * @param bool $ws                  Show whitespace in the diff?
     *
     * @return string|bool  False on failure, or a string containing the diff
     *                      on success
     */
    function get(&$rep, &$file, $rev1, $rev2, $type = 'context', $num = 3, $ws = true)
    {
        /* Make sure that the file parameter is valid */
        if (is_a($file, 'PEAR_Error')) {
            return false;
        }

        /* Check that the revision numbers are valid */
        $rev1 = VC_Revision::valid($rev1)?$rev1:'1.1';
        $rev2 = VC_Revision::valid($rev1)?$rev2:'1.1';

        $fullName = $file->queryFullPath();
        $diff = array();
        $options = '-kk ';
        if (!$ws) {
            $opts = ' -bB ';
            $options .= $opts;
        } else {
            $opts = '';
        }
        switch ($type) {
        case 'context':
            $options = $opts . '-p --context=' . $num;
            break;

        case 'unified':
            $options = $opts . '-p --unified=' . $num;
            break;

        case 'column':
            $options = $opts . '--side-by-side --width=120';
            break;

        case 'ed':
            $options = $opts . '-e';
            break;
        }

        // TODO: add options for $hr options - however these may not
        // be compatible with some diffs - avsm
        $command = $rep->getPath('rcsdiff') . " $options -r$rev1 -r$rev2 \"" . escapeshellcmd($fullName) . '" 2>&1';
        if (OS_WINDOWS) {
            $command .= ' < "' . __FILE__ . '"';
        }

        exec($command, $diff, $retval);
        return ($retval > 0) ? $diff : array();
    }

}

/**
 * VC_cvs directory class.
 *
 * Copyright Anil Madhavapeddy, <anil@recoil.org>
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @package VC
 */
class VC_Directory_cvs {

    var $rep;
    var $dirName;
    var $files;
    var $atticFiles;
    var $mergedFiles;
    var $dirs;
    var $parent;
    var $moduleName;
    var $sortDir;

    /**
     * Creates a CVS Directory object to store information
     * about the files in a single directory in the repository.
     *
     * @param object VC_cvs $rep           A repository object
     * @param string                  $dn  Path to the directory.
     * @param object VC_Directory_cvs $pn  The parent VC_Directory to this one.
     */
    function VC_Directory_cvs($rep, $dn, $pn = '')
    {
        $this->rep = &$rep;
        $this->parent = &$pn;
        $this->moduleName = $dn;
        $this->dirName = $rep->sourceroot() . "/$dn";
        $this->files = array();
        $this->dirs = array();
    }

    /**
     * Return fully qualified pathname to this directory with no
     * trailing /.
     *
     * @return string  Pathname of this directory
     */
    function queryDir()
    {
        return $this->dirName;
    }

    function &queryDirList()
    {
        reset($this->dirs);
        return $this->dirs;
    }

    function &queryFileList($showattic = false)
    {
        if ($showattic && isset($this->mergedFiles)) {
            return $this->mergedFiles;
        } else {
            return $this->files;
        }
    }

    /**
     * Tell the object to open and browse its current directory, and
     * retrieve a list of all the objects in there.  It then populates
     * the file/directory stack and makes it available for retrieval.
     *
     * @return bool|object  PEAR_Error object on an error, true on success.
     */
    function browseDir($cache = null, $quicklog = true, $showattic = false)
    {
        /* Make sure we are trying to list a directory */
        if (!@is_dir($this->dirName)) {
            return PEAR::raiseError(_("Unable to find directory"));
        }

        /* Open the directory for reading its contents */
        if (!($DIR = @opendir($this->dirName))) {
            $errmsg = (!empty($php_errormsg)) ? $php_errormsg : _("Permission Denied");
            return PEAR::raiseError($errmsg);
        }

        /* Create two arrays - one of all the files, and the other of
         * all the directories. */
        while (($name = readdir($DIR)) !== false) {
            if ($name == '.' || $name == '..') {
                continue;
            }

            $path = $this->dirName . '/' . $name;
            if (@is_dir($path)) {
                /* Skip Attic directory. */
                if ($name != 'Attic') {
                    $this->dirs[] = $name;
                }
            } elseif (@is_file($path) && substr($name, -2) == ',v') {
                /* Spawn a new file object to represent this file. */
                $fl = &$this->rep->getFileObject(substr($path, strlen($this->rep->sourceroot()), -2), $cache, $quicklog);
                if (!is_a($fl, 'PEAR_Error')) {
                    $this->files[] = $fl;
                }
            }
        }

        /* Close the filehandle; we've now got a list of dirs and
         * files. */
        closedir($DIR);

        /* If we want to merge the attic, add it in here. */
        if ($showattic) {
            $atticDir = &new VC_Directory_cvs($this->rep, $this->moduleName . '/Attic', $this);
            if ($atticDir->browseDir($cache, $quicklog) == 1) {
                $this->atticFiles = &$atticDir->queryFileList();
                $this->mergedFiles = array_merge($this->files, $this->atticFiles);
            }
        }

        return true;
    }

    /**
     * Sort the contents of the directory in a given fashion and
     * order.
     *
     * @param int $how  Of the form VC_SORT_* where * can be:
     *                  NONE, NAME, AGE, REV for sorting by name, age or
     *                  revision.
     * @param int $dir  Of the form VC_SORT_* where * can be:
     *                  ASCENDING, DESCENDING for the order of the sort.
     */
    function applySort($how = VC_SORT_NONE, $dir = VC_SORT_ASCENDING)
    {
        // Always sort directories by name.
        natcasesort($this->dirs);

        $this->doFileSort($this->files, $how, $dir);
        if (isset($this->atticFiles)) {
            $this->doFileSort($this->atticFiles, $how, $dir);
        }
        if (isset($this->mergedFiles)) {
            $this->doFileSort($this->mergedFiles, $how, $dir);
        }
    }

    function doFileSort(&$fileList, $how = VC_SORT_NONE, $dir = VC_SORT_ASCENDING)
    {
        $this->sortDir = $dir;

        switch ($how) {
        case VC_SORT_AGE:
            usort($fileList, array($this, 'fileAgeSort'));
            break;

        case VC_SORT_NAME:
            usort($fileList, array($this, 'fileNameSort'));
            break;

        case VC_SORT_AUTHOR:
            usort($fileList, array($this, 'fileAuthorSort'));
            break;

        case VC_SORT_REV:
            usort($fileList, array($this, 'fileRevSort'));
            break;
        }

        unset($this->sortDir);
    }

    /**
     * Sort function for file age.
     */
    function fileAgeSort($a, $b)
    {
        $aa = $a->queryLastLog();
        $bb = $b->queryLastLog();
        if ($aa->queryDate() == $bb->queryDate()) {
            return 0;
        } elseif ($this->sortDir = VC_SORT_ASCENDING) {
            return ($aa->queryDate() < $bb->queryDate()) ? 1 : -1;
        } else {
            return ($bb->queryDate() < $aa->queryDate()) ? 1 : -1;
        }
    }

    /**
     * Sort function by author name.
     */
    function fileAuthorSort($a, $b)
    {
        $aa = $a->queryLastLog();
        $bb = $b->queryLastLog();
        if ($aa->queryAuthor() == $bb->queryAuthor()) {
            return 0;
        } elseif ($this->sortDir == VC_SORT_ASCENDING) {
            return ($aa->queryAuthor() > $bb->queryAuthor()) ? 1 : -1;
        } else {
            return ($bb->queryAuthor() > $aa->queryAuthor()) ? 1 : -1;
        }
    }

    /**
     * Sort function for filename.
     */
    function fileNameSort($a, $b)
    {
        if ($this->sortDir == VC_SORT_ASCENDING) {
            return strcasecmp($a->name, $b->name);
        } else {
            return strcasecmp($b->name, $a->name);
        }
    }

    /**
     * Sort function for revision.
     */
    function fileRevSort($a, $b)
    {
        if ($this->sortDir == VC_SORT_ASCENDING) {
            return VC_Revision::cmp($a->queryHead(), $b->queryHead());
        } else {
            return VC_Revision::cmp($b->queryHead(), $a->queryHead());
        }
    }

}

/**
 * VC_cvs file class.
 *
 * Copyright Anil Madhavapeddy, <anil@recoil.org>
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @package VC
 */
class VC_File_cvs extends VC_File {

    /**
     * Create a repository file object, and give it information about
     * what its parent directory and repository objects are.
     *
     * @param string $fl  Full path to this file.
     */
    function VC_File_cvs($fl, $quicklog = false)
    {
        $fl .= ',v';
        $this->name = basename($fl);
        $this->dir = dirname($fl);
        $this->logs = array();
        $this->quicklog = $quicklog;
        $this->revs = array();
        $this->branches = array();
    }

    function &getFileObject(&$rep, $filename, $cache = null, $quicklog = false)
    {
        /**
         * The version of the cached data. Increment this whenever the
         * internal storage format changes, such that we must
         * invalidate prior cached data.
         *
         * @var integer $_cacheVersion
         */
        $_cacheVersion = 2;

        if ($cache) {
            $cacheId = $filename . '_f' . (int)$quicklog . '_v' . $_cacheVersion;
            $fileOb = unserialize($cache->getData($cacheId, "serialize(VC_File_cvs::_getFileObject('$filename', '$quicklog'))",
                                                  time() - @filemtime($filename . ',v')));
        } else {
            $fileOb = &VC_File_cvs::_getFileObject($filename, $quicklog);
        }

        $fileOb->setRepository($rep);

        if (is_a(($result = $fileOb->getBrowseInfo()), 'PEAR_Error')) {
            return $result;
        }

        return $fileOb;
    }

    function &_getFileObject($filename, $quicklog = false)
    {
        $fileOb = &new VC_File_cvs($filename, $quicklog);
        $fileOb->applySort(VC_SORT_AGE);
        return $fileOb;
    }

    /**
     * If this file is present in an Attic directory, this indicates
     * it.
     *
     * @return bool  True if file is in the Attic, and false otherwise
     */
    function isAtticFile()
    {
        return substr($this->dir, -5) == 'Attic';
    }

    /**
     * Returns the name of the current file as in the repository
     *
     * @return string  Filename (without the path)
     */
    function queryRepositoryName()
    {
        return $this->name;
    }

    /**
     * Returns name of the current file without the repository
     * extensions (usually ,v)
     *
     * @return string  Filename without repository extension
     */
    function queryName()
    {
        return preg_replace('/,v$/', '', $this->name);
    }

    /**
     * Return the last revision of the current file on the HEAD branch
     *
     * @return string|object  Last revision of the current file or PEAR_Error
     *                        on failure.
     */
    function queryRevision()
    {
        if (!isset($this->revs[0])) {
            return PEAR::raiseError(_("No revisions"));
        }
        return $this->revs[0];
    }

    function queryPreviousRevision($rev)
    {
        return VC_Revision::prev($rev);
    }

    /**
     * Return the HEAD (most recent) revision number for this file.
     *
     * @return string  HEAD revision number
     */
    function queryHead()
    {
        return $this->head;
    }

    /**
     * Return the last VC_log object in the file.
     *
     * @return VC_log of the last entry in the file
     */
    function queryLastLog()
    {
        if (!isset($this->revs[0]) || !isset($this->logs[$this->revs[0]])) {
            return PEAR::raiseError(_("No revisions"));
        }
        return $this->logs[$this->revs[0]];
    }

    /**
     * Sort the list of VC_log objects that this file contains.
     *
     * @param int $how  VC_SORT_REV (sort by revision),
     *                  VC_SORT_NAME (sort by author name),
     *                  VC_SORT_AGE (sort by commit date)
     */
    function applySort($how = VC_SORT_REV)
    {
        switch ($how) {
        case VC_SORT_REV:
            $func = 'Revision';
            break;

        case VC_SORT_NAME:
            $func = 'Name';
            break;

        case VC_SORT_AGE:
            $func = 'Age';
            break;

        default:
            $func = 'Revision';
        }
        uasort($this->logs, array($this, "sortBy$func"));
        return true;
    }

    /**
     * The sortBy*() functions are internally used by applySort.
     */
    function sortByRevision($a, $b)
    {
        return VC_Revision::cmp($b->rev, $a->rev);
    }

    function sortByAge($a, $b)
    {
        return $b->date - $a->date;
    }

    function sortByName($a, $b)
    {
        return strcmp($a->author, $b->author);
    }

    /**
     * Populate the object with information about the revisions logs
     * and dates of the file.
     *
     * @return bool|object  PEAR_Error object on error, or true on success
     */
    function getBrowseInfo()
    {
        /* Check that we are actually in the filesystem. */
        if (!is_file($this->queryFullPath())) {
            return PEAR::raiseError(_("File Not Found"));
        }

        /* Call the RCS rlog command to retrieve the file
         * information. */
        $flag = $this->quicklog ? ' -r ' : ' ';
        $Q = OS_WINDOWS ? '"' : "'" ;

        $cmd = $this->rep->getPath('rlog') . $flag . $Q . $this->queryFullPath() . $Q;
        exec($cmd, $return_array, $retval);

        if ($retval) {
            return PEAR::raiseError(_("Failed to spawn rlog to retrieve file log information"));
        }

        $accum = array();
        $symrev = array();
        $revsym = array();
        $state = 'init';
        foreach ($return_array as $line) {
            switch ($state) {
            case 'init':
                if (!strncmp('head: ', $line, 6)) {
                    $this->head = substr($line, 6);
                } else if (!strncmp('branch:', $line, 7)) {
                    $state = 'rev';
                }
                break;

            case 'rev':
                if (!strncmp('----------', $line, 10)) {
                    $state = 'info';
                    $this->symrev = $symrev;
                    $this->revsym = $revsym;
                } else if (preg_match("/^\s+([^:]+):\s+([\d\.]+)/", $line ,$regs)) {
                    // Check to see if this is a branch
                    if (preg_match('/^(\d+(\.\d+)+)\.0\.(\d+)$/',$regs[2])) {
                        $branchRev = VC_Revision::toBranch($regs[2]);
                        if (!isset($this->branches[$branchRev])) {
                            $this->branches[$branchRev] = $regs[1];
                        }
                    } else {
                        $symrev[$regs[1]] = $regs[2];
                        if (empty($revsym[$regs[2]])) $revsym[$regs[2]]=array();
                        array_push($revsym[$regs[2]], $regs[1]);
                    }
                }
                break;

            case 'info':
                if (strncmp('==============================', $line, 30) &&
                    strcmp('----------------------------', $line)) {
                    $accum[] = $line;
                } else if (count($accum)) {
                    // spawn a new VC_log object and add it to the logs hash
                    $log = &new VC_Log_cvs($this);
                    $err = $log->processLog($accum);
                    // TODO: error checks - avsm
                    $this->logs[$log->queryRevision()] = $log;
                    array_push($this->revs, $log->queryRevision());
                    $accum = array();
                }
                break;
            }
        }

        return true;
    }

    /**
     * Return the fully qualified filename of this object.
     *
     * @return Fully qualified filename of this object
     */
    function queryFullPath()
    {
        return $this->dir . '/' . $this->name;
    }

    /**
     * Return the name of this file relative to its sourceroot.
     *
     * @return string  Pathname relative to the sourceroot.
     */
    function queryModulePath()
    {
        return preg_replace('|^'. $this->rep->sourceroot() . '/?(.*),v$|', '\1', $this->queryFullPath());
    }

}

/**
 * VC_cvs log class.
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @package VC
 */
class VC_Log_cvs {

    var $rep, $file, $tags, $rev, $date, $log, $author, $state, $lines, $branches;

    /**
     *
     */
    function VC_Log_cvs(&$fl)
    {
        $this->file = &$fl;
        $this->branches = array();
    }

    function processLog($raw)
    {
        /* Initialise a simple state machine to parse the output of rlog */
        $state = 'init';
        while (!empty($raw) && $state != 'done') {
            switch ($state) {
            /* Found filename, now looking for the revision number */
            case 'init':
                $line = array_shift($raw);
                if (preg_match("/revision (.+)$/", $line, $parts)) {
                    $this->rev = $parts[1];
                    $state = 'date';
                }
                break;

            /* Found revision and filename, now looking for date */
            case 'date':
                $line = array_shift($raw);
                if (preg_match("|^date:\s+(\d+)[-/](\d+)[-/](\d+)\s+(\d+):(\d+):(\d+).*?;\s+author:\s+(.+);\s+state:\s+(\S+);(\s+lines:\s+([0-9\s+-]+))?|", $line, $parts)) {
                    $this->date = gmmktime($parts[4], $parts[5], $parts[6], $parts[2], $parts[3], $parts[1]);
                    $this->author = $parts[7];
                    $this->state = $parts[8];
                    $this->lines = isset($parts[10]) ? $parts[10] : '';
                    $state = 'branches';
                }
                break;

            /* Look for a branch point here - format is 'branches:  x.y.z;  a.b.c;' */
            case 'branches':
                /* If we find a branch tag, process and pop it,
                   otherwise leave input stream untouched */
                if (!empty($raw) && preg_match("/^branches:\s+(.*)/", $raw[0], $br)) {
                    /* Get the list of branches from the string, and
                     * push valid revisions into the branches array */
                    $brs = preg_split('/;\s*/', $br[1]);
                    foreach ($brs as $brpoint) {
                        if (VC_Revision::valid($brpoint)) {
                            $this->branches[] = $brpoint;
                        }
                    }
                    array_shift($raw);

                }

                $state = 'done';
                break;

            default:
            }
        }

        /* Assume the rest of the lines are the log message */
        $this->log = implode("\n", $raw);
        $this->tags = @$this->file->revsym[$this->rev];
        if (empty($this->tags)) {
            $this->tags = array();
        }
    }

    function queryDate()
    {
        return $this->date;
    }

    function queryRevision()
    {
        return $this->rev;
    }

    function queryAuthor()
    {
        return $this->author;
    }

    function queryLog()
    {
        return $this->log;
    }

    function queryChangedLines()
    {
        return isset($this->lines) ? ($this->lines) : '';
    }

    /**
     * Given a branch revision number, this function remaps it
     * accordingly, and performs a lookup on the file object to
     * return the symbolic name(s) of that branch in the tree.
     *
     * @return array  Hash of symbolic names => branch numbers
     */
    function querySymbolicBranches()
    {
        $symBranches = array();
        foreach ($this->branches as $branch) {
            $parts = explode('.', $branch);
            $last = array_pop($parts);
            $parts[] = '0';
            $parts[] = $last;
            $rev = implode('.', $parts);
            if (isset($this->file->branches[$branch])) {
                $symBranches[$this->file->branches[$branch]] = $branch;
            }
        }
        return $symBranches;
    }

}

/**
 * VC_cvs Patchset class.
 *
 * Copyright Anil Madhavapeddy, <anil@recoil.org>
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @package VC
 */
class VC_Patchset_cvs {

    var $_rep;
    var $_dir;
    var $_name;
    var $_patchsets = array();

    /**
     * Create a patchset object.
     *
     * @param string $file  The filename to get patchsets for.
     */
    function VC_Patchset_cvs($file)
    {
        $this->_name = basename($file);
        $this->_dir = dirname($file);
    }

    function &getPatchsetObject(&$rep, $filename, $cache = null)
    {
        /**
         * The version of the cached data. Increment this whenever the
         * internal storage format changes, such that we must
         * invalidate prior cached data.
         *
         * @var integer $_cacheVersion
         */
        $_cacheVersion = 1;

        if ($cache) {
            $cacheId = $filename . '_f' . '_v' . $_cacheVersion;
            $psOb = unserialize($cache->getData($cacheId, "serialize(VC_Patchset_cvs::_getPatchsetObject('$filename', '" . $rep->sourceroot() . "'))",
                                                time() - @filemtime($filename . ',v')));
        } else {
            $psOb = &VC_Patchset_cvs::_getPatchsetObject($filename, $rep->sourceroot());
        }

        $psOb->_rep = &$rep;

        if (is_a(($result = $psOb->getPatchsets($rep)), 'PEAR_Error')) {
            return $result;
        }

        return $psOb;
    }

    function &_getPatchsetObject($filename, $repository)
    {
        return new VC_Patchset_cvs($filename);
    }

    /**
     * Populate the object with information about the patchsets that
     * this file is involved in.
     *
     * @param string $repository  The full repository location.
     *
     * @return bool|object  PEAR_Error object on error, or true on success.
     */
    function getPatchsets($repository)
    {
        /* Check that we are actually in the filesystem. */
        if (!is_file($this->getFullPath() . ',v')) {
            return PEAR::raiseError(_("File Not Found"));
        }

        /* Call cvsps to retrieve all patchsets for this file. */
        $Q = OS_WINDOWS ? '"' : "'";

        $cvsps_home = $repository->getPath('cvsps_home');
        $HOME = !empty($cvsps_home) ?
            'HOME=' . $cvsps_home . ' ' :
            '';

        $cmd = $HOME . $repository->getPath('cvsps') . ' -u --cvs-direct --root ' . $Q . $repository->sourceroot() . $Q . ' -f ' . $Q . $this->_name . $Q . ' ' . $Q . $this->_dir . $Q;
        exec($cmd, $return_array, $retval);
        if ($retval) {
            return PEAR::raiseError(_("Failed to spawn cvsps to retrieve patchset information"));
        }

        $this->_patchsets = array();
        $state = 'begin';
        foreach ($return_array as $line) {
            $line = trim($line);
            if ($line == '---------------------') {
                $state = 'begin';
                continue;
            }

            switch ($state) {
            case 'begin':
                $id = str_replace('PatchSet ', '', $line);
                $this->_patchsets[$id] = array();
                $state = 'info';
                break;

            case 'info':
                $info = explode(':', $line, 2);
                switch ($info[0]) {
                case 'Date':
                    $this->_patchsets[$id]['date'] = trim($info[1]);
                    break;

                case 'Author':
                    $this->_patchsets[$id]['author'] = trim($info[1]);
                    break;

                case 'Branch':
                    $this->_patchsets[$id]['branch'] = trim($info[1]);
                    break;

                case 'Tag':
                    $this->_patchsets[$id]['tag'] = trim($info[1]);
                    break;

                case 'Log':
                    $state = 'log';
                    $this->_patchsets[$id]['log'] = '';
                    break;
                }
                break;

            case 'log':
                if ($line == 'Members:') {
                    $state = 'members';
                    $this->_patchsets[$id]['log'] = trim($this->_patchsets[$id]['log']);
                    $this->_patchsets[$id]['members'] = array();
                } else {
                    $this->_patchsets[$id]['log'] .= $line . "\n";
                }
                break;

            case 'members':
                if (!empty($line)) {
                    $parts = explode(':', $line);
                    $revs = explode('->', $parts[1]);
                    $this->_patchsets[$id]['members'][] = array('file' => $parts[0],
                                                                'from' => $revs[0],
                                                                'to' => $revs[1]);
                }
                break;
            }
        }

        return true;
    }

    /**
     * Return the fully qualified filename of this object.
     *
     * @return string  Fully qualified filename of this object
     */
    function getFullPath()
    {
        return $this->_dir . '/' . $this->_name;
    }

}
