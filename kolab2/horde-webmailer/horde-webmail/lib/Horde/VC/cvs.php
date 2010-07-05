<?php

require_once dirname(__FILE__) . '/rcs.php';

/**
 * VC_cvs implementation.
 *
 * Copyright 2000-2009 The Horde Project (http://www.horde.org/)
 *
 * $Horde: framework/VC/VC/cvs.php,v 1.32.2.28 2009-01-06 15:23:46 jan Exp $
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
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
        return @is_file($where . ',v') || @is_file(dirname($where) . '/Attic/' . basename($where) . ',v');
    }

    function &queryDir($where)
    {
        $dir = new VC_Directory_cvs($this, $where);
        return $dir;
    }

    function getCheckout($file, $rev)
    {
        return VC_Checkout_cvs::get($this, $file->queryFullPath(), $rev);
    }

    function getDiff($file, $rev1, $rev2, $type = 'context', $num = 3, $ws = true)
    {
        return VC_Diff_cvs::get($this, $file, $rev1, $rev2, $type, $num, $ws);
    }

    function &getFileObject($filename, $cache = null, $quicklog = false)
    {
        if (substr($filename, 0, 1) != '/') {
            $filename = '/' . $filename;
        }
        $fo = &VC_File_cvs::getFileObject($this, $this->sourceroot() . $filename, $cache, $quicklog);
        return $fo;
    }

    function &getAnnotateObject($filename)
    {
        $blame = new VC_Annotate_cvs($this, $filename, Util::getTempFile('vc', true, $this->_paths['temp']));
        return $blame;
    }

    function &getPatchsetObject($filename, $cache = null)
    {
        $po = &VC_Patchset_cvs::getPatchsetObject($this, $this->sourceroot() . '/' . $filename, $cache);
        return $po;
    }

}

/**
 * VC_cvs annotate class.
 *
 * Anil Madhavapeddy, <anil@recoil.org>
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @package VC
 */
class VC_Annotate_cvs {

    var $file;
    var $rep;
    var $tmpfile;

    function VC_Annotate_cvs($rep, $file, $tmpfile)
    {
        $this->rep = $rep;
        $this->file = $file;
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

        $pipe = popen($this->rep->getPath('cvs') . ' -n server > ' . $this->tmpfile, VC_WINDOWS ? 'wb' : 'w');

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

        if (!($fl = fopen($this->tmpfile, VC_WINDOWS ? 'rb' : 'r'))) {
            return false;
        }

        $lines = array();
        $line = fgets($fl, 4096);

        // Windows versions of cvs always return $where with forwards slashes.
        if (VC_WINDOWS) {
            $where = str_replace(DIRECTORY_SEPARATOR, '/', $where);
        }

        while ($line && !preg_match("|^E\s+Annotations for $where|", $line)) {
            $line = fgets($fl, 4096);
        }

        if (!$line) {
            return PEAR::raiseError('Unable to annotate; server said: ' . $line);
        }

        $lineno = 1;
        while ($line = fgets($fl, 4096)) {
            if (preg_match('/^M\s+([\d\.]+)\s+\((.+)\s+(\d+-\w+-\d+)\):.(.*)$/', $line, $regs)) {
                $entry = array();
                $entry['rev']    = $regs[1];
                $entry['author'] = trim($regs[2]);
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
 * @package VC
 */
class VC_Checkout_cvs {

    /**
     * Static function which returns a file pointing to the head of the
     * requested revision of an RCS file.
     *
     * @param VC_cvs $rep       A repository object
     * @param string $fullname  Fully qualified pathname of the desired RCS
     *                          file to checkout
     * @param string $rev       RCS revision number to check out
     *
     * @return resource|object  Either a PEAR_Error object, or a stream
     *                          pointer to the head of the checkout
     */
    function get($rep, $fullname, $rev)
    {
        if (!VC_Revision::valid($rev)) {
            return PEAR::raiseError('Invalid revision number');
        }

        if (VC_WINDOWS) {
            $mode = 'rb';
            $q_name = '"' . escapeshellcmd(str_replace('\\', '/', $fullname)) . '"';
        } else {
            $mode = 'r';
            $q_name = escapeshellarg($fullname);
        }

        if (!($RCS = popen($rep->getPath('co') . " -p$rev $q_name 2>&1", $mode))) {
            return PEAR::raiseError('Couldn\'t perform checkout of the requested file');
        }

        /* First line from co should be of the form :
         * /path/to/filename,v  -->  standard out
         * and we check that this is the case and error otherwise
         */

        $co = fgets($RCS, 1024);
        if (!preg_match('/^([\S ]+),v\s+-->\s+st(andar)?d ?out(put)?\s*$/', $co, $regs) || $regs[1].',v' != $fullname) {
            return PEAR::raiseError('Unexpected output from checkout: ' . $co);
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
     * Obtain the differences between two revisions of a file.
     *
     * @param VC_cvs $rep        A repository object.
     * @param VC_File_cvs $file  The desired file.
     * @param string $rev1       Original revision number to compare from.
     * @param string $rev2       New revision number to compare against.
     * @param string $type       The type of diff (e.g. 'unified').
     * @param integer $num       Number of lines to be used in context and
     *                           unified diffs.
     * @param boolean $ws        Show whitespace in the diff?
     *
     * @return string|boolean  False on failure, or a string containing the
     *                         diff on success.
     */
    function get($rep, $file, $rev1, $rev2, $type = 'context', $num = 3,
                 $ws = true)
    {
        /* Make sure that the file parameter is valid. */
        if (is_a($file, 'PEAR_Error')) {
            return false;
        }

        /* Check that the revision numbers are valid. */
        $rev1 = VC_Revision::valid($rev1) ? $rev1 : '1.1';
        $rev2 = VC_Revision::valid($rev1) ? $rev2 : '1.1';

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
            $options = $opts . '-p --context=' . (int)$num;
            break;

        case 'unified':
            $options = $opts . '-p --unified=' . (int)$num;
            break;

        case 'column':
            $options = $opts . '--side-by-side --width=120';
            break;

        case 'ed':
            $options = $opts . '-e';
            break;
        }

        // Windows versions of cvs always return $where with forwards slashes.
        if (VC_WINDOWS) {
            $fullName = str_replace(DIRECTORY_SEPARATOR, '/', $fullName);
        }

        // TODO: add options for $hr options - however these may not be
        // compatible with some diffs.
        $command = $rep->getPath('rcsdiff') . " $options -r$rev1 -r$rev2 \"" . escapeshellcmd($fullName) . '" 2>&1';
        if (VC_WINDOWS) {
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
     * @param VC_cvs $rep           A repository object
     * @param string $dn            Path to the directory.
     * @param VC_Directory_cvs $pn  The parent VC_Directory to this one.
     */
    function VC_Directory_cvs($rep, $dn, $pn = '')
    {
        $this->rep = $rep;
        $this->parent = $pn;
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
     * @return boolean|object  PEAR_Error object on an error, true on success.
     */
    function browseDir($cache = null, $quicklog = true, $showattic = false)
    {
        /* Make sure we are trying to list a directory */
        if (!@is_dir($this->dirName)) {
            return PEAR::raiseError('Unable to find directory ' . $this->dirName);
        }

        /* Open the directory for reading its contents */
        if (!($DIR = @opendir($this->dirName))) {
            $errmsg = (!empty($php_errormsg)) ? $php_errormsg : 'Permission denied';
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
                $fl = $this->rep->getFileObject(substr($path, strlen($this->rep->sourceroot()), -2), $cache, $quicklog);
                if (is_a($fl, 'PEAR_Error')) {
                    return $fl;
                } else {
                    $this->files[] = $fl;
                }
            }
        }

        /* Close the filehandle; we've now got a list of dirs and
         * files. */
        closedir($DIR);

        /* If we want to merge the attic, add it in here. */
        if ($showattic) {
            $atticDir = new VC_Directory_cvs($this->rep, $this->moduleName . '/Attic', $this);
            if (!is_a($atticDir->browseDir($cache, $quicklog), 'PEAR_Error')) {
                $this->atticFiles = $atticDir->queryFileList();
                $this->mergedFiles = array_merge($this->files, $this->atticFiles);
            }
        }

        return true;
    }

    /**
     * Sort the contents of the directory in a given fashion and
     * order.
     *
     * @param integer $how  Of the form VC_SORT_* where * can be:
     *                      NONE, NAME, AGE, REV for sorting by name, age or
     *                      revision.
     * @param integer $dir  Of the form VC_SORT_* where * can be:
     *                      ASCENDING, DESCENDING for the order of the sort.
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
        } elseif ($this->sortDir == VC_SORT_ASCENDING) {
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

    function &getFileObject($rep, $filename, $cache = null, $quicklog = false)
    {
        /* Assume file is in the Attic if it doesn't exist. */
        if (!@is_file($filename . ',v')) {
            $filename = dirname($filename) . '/Attic/' . basename($filename);
        }

        /* The version of the cached data. Increment this whenever the
         * internal storage format changes, such that we must
         * invalidate prior cached data. */
        $cacheVersion = 2;
        $cacheId = $rep->sourceroot() . '_n' . $filename . '_f' . (int)$quicklog . '_v' . $cacheVersion;

        $ctime = time() - filemtime($filename . ',v');
        if ($cache &&
            $cache->exists($cacheId, $ctime)) {
            $fileOb = unserialize($cache->get($cacheId, $ctime));
            $fileOb->setRepository($rep);
        } else {
            $fileOb = new VC_File_cvs($filename, $quicklog);
            $fileOb->setRepository($rep);
            if (is_a(($result = $fileOb->getBrowseInfo()), 'PEAR_Error')) {
                return $result;
            }
            $fileOb->applySort(VC_SORT_AGE);

            if ($cache) {
                $cache->set($cacheId, serialize($fileOb));
            }
        }

        return $fileOb;
    }

    /**
     * If this file is present in an Attic directory, this indicates
     * it.
     *
     * @return boolean  True if file is in the Attic, and false otherwise
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
            return PEAR::raiseError('No revisions');
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
            return PEAR::raiseError('No revisions');
        }
        return $this->logs[$this->revs[0]];
    }

    /**
     * Sort the list of VC_log objects that this file contains.
     *
     * @param integer $how  VC_SORT_REV (sort by revision),
     *                      VC_SORT_NAME (sort by author name),
     *                      VC_SORT_AGE (sort by commit date)
     */
    function applySort($how = VC_SORT_REV)
    {
        switch ($how) {
        case VC_SORT_NAME:
            $func = 'Name';
            break;

        case VC_SORT_AGE:
            $func = 'Age';
            break;

        case VC_SORT_REV:
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
     * Populate the object with information about the revisions logs and dates
     * of the file.
     *
     * @return boolean|object  PEAR_Error object on error, or true on success
     */
    function getBrowseInfo()
    {
        /* Check that we are actually in the filesystem. */
        $file = $this->queryFullPath();
        if (!is_file($file)) {
            return PEAR::raiseError('File Not Found: ' . $file);
        }

        /* Call the RCS rlog command to retrieve the file
         * information. */
        $flag = $this->quicklog ? ' -r ' : ' ';
        $q_file = VC_WINDOWS ? '"' . escapeshellcmd($file) . '"' : escapeshellarg($file);

        $cmd = $this->rep->getPath('rlog') . $flag . $q_file;
        exec($cmd, $return_array, $retval);

        if ($retval) {
            return PEAR::raiseError('Failed to spawn rlog to retrieve file log information for ' . $file);
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
                } elseif (!strncmp('branch:', $line, 7)) {
                    $state = 'rev';
                }
                break;

            case 'rev':
                if (!strncmp('----------', $line, 10)) {
                    $state = 'info';
                    $this->symrev = $symrev;
                    $this->revsym = $revsym;
                } elseif (preg_match("/^\s+([^:]+):\s+([\d\.]+)/", $line, $regs)) {
                    // Check to see if this is a branch
                    if (preg_match('/^(\d+(\.\d+)+)\.0\.(\d+)$/', $regs[2])) {
                        $branchRev = $this->toBranch($regs[2]);
                        if (!isset($this->branches[$branchRev])) {
                            $this->branches[$branchRev] = $regs[1];
                        }
                    } else {
                        $symrev[$regs[1]] = $regs[2];
                        if (empty($revsym[$regs[2]])) {
                            $revsym[$regs[2]] = array();
                        }
                        $revsym[$regs[2]][] = $regs[1];
                    }
                }
                break;

            case 'info':
                if (strncmp('==============================', $line, 30) &&
                    strcmp('----------------------------', $line)) {
                    $accum[] = $line;
                } elseif (count($accum)) {
                    // spawn a new VC_log object and add it to the logs hash
                    $log = new VC_Log_cvs($this);
                    $err = $log->processLog($accum);
                    // TODO: error checks - avsm
                    $this->logs[$log->queryRevision()] = $log;
                    $this->revs[] = $log->queryRevision();
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

    /**
     * Given a revision number of the form x.y.0.z, this remaps it
     * into the appropriate branch number, which is x.y.z
     *
     * @param string $rev  Even-digit revision number of a branch
     *
     * @return string  Odd-digit Branch number
     */
    function toBranch($rev)
    {
        /* Check if we have a valid revision number */
        if (!VC_Revision::valid($rev)) {
            return false;
        }

        if (($end = strrpos($rev, '.')) === false) {
            return false;
        }

        $rev[$end] = 0;
        if (($end2 = strrpos($rev, '.')) === false) {
            return substr($rev, ++$end);
        }

        return substr_replace($rev, '.', $end2, ($end - $end2 + 1));
    }

}

/**
 * VC_cvs log class.
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @package VC
 */
class VC_Log_cvs {

    var $rep;
    var $file;
    var $tags;
    var $rev;
    var $date;
    var $log;
    var $author;
    var $state;
    var $lines;
    var $branches;

    /**
     *
     */
    function VC_Log_cvs($fl)
    {
        $this->file = $fl;
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

            /* Look for a branch point here - format is 'branches:
             * x.y.z; a.b.c;' */
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
            }
        }

        /* Assume the rest of the lines are the log message */
        $this->log = implode("\n", $raw);
        $this->tags = isset($this->file->revsym[$this->rev]) ?
            $this->file->revsym[$this->rev] :
            array();
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
class VC_Patchset_cvs extends VC_Patchset {

    var $_dir;
    var $_name;

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

    function &getPatchsetObject($rep, $filename, $cache = null)
    {
        /* The version of the cached data. Increment this whenever the
         * internal storage format changes, such that we must
         * invalidate prior cached data. */
        $cacheVersion = 1;
        $cacheId = $rep->sourceroot() . '_n' . $filename . '_f_v' . $cacheVersion;

        $ctime = time() - filemtime($filename . ',v');
        if ($cache &&
            $cache->exists($cacheId, $ctime)) {
            $psOb = unserialize($cache->get($cacheId, $ctime));
            $psOb->setRepository($rep);
        } else {
            $psOb = new VC_Patchset_cvs($filename);
            $psOb->setRepository($rep);
            if (is_a(($result = $psOb->getPatchsets()), 'PEAR_Error')) {
                return $result;
            }

            if ($cache) {
                $cache->set($cacheId, serialize($psOb));
            }
        }

        return $psOb;
    }

    /**
     * Populate the object with information about the patchsets that
     * this file is involved in.
     *
     * @return boolean|object  PEAR_Error object on error, or true on success.
     */
    function getPatchsets()
    {
        /* Check that we are actually in the filesystem. */
        if (!is_file($this->getFullPath() . ',v')) {
            return PEAR::raiseError('File Not Found');
        }

        /* Call cvsps to retrieve all patchsets for this file. */
        $q_root = $this->_rep->sourceroot();
        $q_root = VC_WINDOWS ? '"' . escapeshellcmd($q_root) . '"' : escapeshellarg($q_root);

        $cvsps_home = $this->_rep->getPath('cvsps_home');
        $HOME = !empty($cvsps_home) ?
            'HOME=' . $cvsps_home . ' ' :
            '';

        $cmd = $HOME . $this->_rep->getPath('cvsps') . ' -u --cvs-direct --root ' . $q_root . ' -f ' . escapeshellarg($this->_name) . ' ' . escapeshellarg($this->_dir);
        exec($cmd, $return_array, $retval);
        if ($retval) {
            return PEAR::raiseError('Failed to spawn cvsps to retrieve patchset information');
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
                    if (preg_match('|(\d{4})/(\d{2})/(\d{2}) (\d{2}):(\d{2}):(\d{2})|', $info[1], $date)) {
                        $this->_patchsets[$id]['date'] = gmmktime($date[4], $date[5], $date[6], $date[2], $date[3], $date[1]);
                    }
                    break;

                case 'Author':
                    $this->_patchsets[$id]['author'] = trim($info[1]);
                    break;

                case 'Branch':
                    if (trim($info[1]) != 'HEAD') {
                        $this->_patchsets[$id]['branch'] = trim($info[1]);
                    }
                    break;

                case 'Tag':
                    if (trim($info[1]) != '(none)') {
                        $this->_patchsets[$id]['tag'] = trim($info[1]);
                    }
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
