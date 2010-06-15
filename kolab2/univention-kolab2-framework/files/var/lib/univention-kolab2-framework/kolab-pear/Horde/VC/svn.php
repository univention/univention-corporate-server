<?php
/**
 * VC_svn implementation.
 *
 * Copyright 2000-2004 Anil Madhavapeddy, <anil@recoil.org>
 *
 * $Horde: framework/VC/VC/svn.php,v 1.16 2004/05/28 18:51:29 chuck Exp $
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package VC
 */
class VC_svn extends VC {

    /**
     * Constructor.
     *
     * @param array $params  Any parameter the class expects.
     *                       Current parameters:
     *                       'sourceroot': The source root for this
     *                                     repository
     *                       'paths': Hash with the locations of all
     *                                necessary binaries: 'svn', 'diff'
     */
    function VC_svn($params)
    {
        $this->_sourceroot = $params['sourceroot'];
        $this->_paths = $params['paths'];
    }

    function isFile($where)
    {
        return true;
    }

    function &queryDir($where)
    {
        return new VC_Directory_svn($this, $where);
    }

    function getCheckout($file, $rev)
    {
        return VC_Checkout_svn::get($this, $file->queryFullPath(), $rev);
    }

    function &getDiff(&$file, $rev1, $rev2, $type = 'context', $num = 3, $ws = true)
    {
        return VC_Diff_svn::get($this, $file, $rev1, $rev2, $type, $num, $ws);
    }

    function &getFileObject($filename, $cache = null, $quicklog = false)
    {
        return VC_File_svn::getFileObject($this, $filename, $cache, $quicklog);
    }

    function &getAnnotateObject($filename)
    {
        return new VC_Annotate_svn($this, $filename);
    }

    function &getPatchsetObject($filename, $cache = null)
    {
        return VC_Patchset_svn::getPatchsetObject($this, $filename, $cache);
    }

}

/**
 * VC_svn annotate class.
 *
 * Anil Madhavapeddy, <anil@recoil.org>
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @package VC
 */
class VC_Annotate_svn {

    var $file;
    var $SVN;
    var $tmpfile;

    function VC_Annotate_svn(&$rep, $file)
    {
        $this->SVN = &$rep;
        $this->file = &$file;
    }

    function doAnnotate($rev)
    {
        /* Make sure that the file values for this object is valid */
        if (is_a($this->file, 'PEAR_Error')) {
            return false;
        }

        if (!VC_Revision::valid($rev)) {
            return false;
        }

        $pipe = popen($this->SVN->getPath('svn') . ' annotate -r 1:' . $rev . ' ' . $this->file->queryFullPath() . ' 2>&1', 'r');

        $lines = array();
        $lineno = 1;
        while (!feof($pipe)) {
            $line = fgets($pipe, 4096);
            if (preg_match('/^\s+(\d+)\s+(\w+)\s(.*)$/', $line, $regs)) {
                $entry = array();
                $entry['rev']    = $regs[1];
                $entry['author'] = $regs[2];
                $entry['date']   = _("Not Implemented");
                $entry['line']   = $regs[3];
                $entry['lineno'] = $lineno++;
                $lines[] = $entry;
            }
        }

        pclose($pipe);
        return $lines;
    }

}

/**
 * VC_svn checkout class.
 *
 * Anil Madhavapeddy, <anil@recoil.org>
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @package VC
 */
class VC_Checkout_svn {

    /**
      * Static function which returns a file pointing to the head of the requested
      * revision of an RCS file.
      * @param fullname Fully qualified pathname of the desired RCS file to checkout
      * @param rev RCS revision number to check out
      * @return Either a PEAR_Error object, or a stream pointer to the head of the checkout
      */
    function get(&$rep, $fullname, $rev)
    {
        if (!VC_Revision::valid($rev)) {
            return PEAR::raiseError(_("Invalid revision number"));
        }

        if (!($RCS = popen($rep->getPath('svn') . ' cat -r ' . $rev . ' ' . $fullname . ' 2>&1', 'r'))) {
            return PEAR::raiseError(_("Couldn't perform checkout of the requested file"));
        }

        return $RCS;
    }

}

/**
 * VC_svn diff class.
 *
 * Copyright Anil Madhavapeddy, <anil@recoil.org>
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @package VC
 */
class VC_Diff_svn {

    /**
     * Obtain the differences between two revisions within a file.
     *
     * @param file VC_File_svn object for the desired file
     * @param rev1 Original revision number to compare from
     * @param rev2 New revision number to compare against
     * @param type Constant which indicates the type of diff (e.g. unified)
     * @param num  Number of lines to be used in context and unified diff
     * @param ws   Show whitespace in the diff?
     *
     * @return false on failure, or a string containing the diff on success
     */
    function get(&$rep, &$file, $rev1, $rev2, $type, $num, $ws = 'context', $num = 3, $ws = true)
    {
        /* Make sure that the file parameter is valid */
        if (is_a($file, 'PEAR_Error')) {
            return false;
        }

        /* Check that the revision numbers are valid */
        $rev1 = VC_Revision::valid($rev1) ? $rev1 : '0';
        $rev2 = VC_Revision::valid($rev1) ? $rev2 : '0';

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
        $command = $rep->getPath('svn') . " diff --diff-cmd " . $rep->getPath('diff') . " -r $rev1:$rev2 -x '$options' " . $file->queryFullPath() . ' 2>&1';

        exec($command, $diff, $retval);
        return $diff;
    }

}

/**
 * VC_svn directory class.
 *
 * Copyright Anil Madhavapeddy, <anil@recoil.org>
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @package VC
 */
class VC_Directory_svn {

    var $rep;
    var $dirName;
    var $files;
    var $atticFiles;
    var $mergedFiles;
    var $dirs;
    var $parent;
    var $moduleName;

    /**
     * Create a SVN Directory object to store information about the
     * files in a single directory in the repository
     *
     * @param object VC_Repository_svn $rp  The VC_Repository object this directory is part of.
     * @param string                   $dn  Path to the directory.
     * @param object VC_Directory_svn  $pn  (optional) The parent VC_Directory to this one.
     */
    function VC_Directory_svn(&$rep, $dn, $pn = '')
    {
        $this->rep = &$rep;
        $this->parent = &$pn;
        $this->moduleName = $dn;
        $this->dirName = "/$dn";
        $this->files = array();
        $this->dirs = array();
    }

    /**
     * Return fully qualified pathname to this directory with no
     * trailing /.
     *
     * @return Pathname of this directory
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
     * @return PEAR_Error object on an error, 1 on success.
     */
    function browseDir($cache = null, $quicklog = true, $showattic = false)
    {
        $cmd = $this->rep->getPath('svn') . ' ls ' . $this->rep->sourceroot() . $this->queryDir() . ' 2>&1';
        $dir = popen($cmd, 'r');

        /* Create two arrays - one of all the files, and the other of
         * all the dirs. */
        while (!feof($dir)) {
            $line = fgets($dir, 1024);
            $name = chop($line);
            if (strlen($name) != 0) {
                if (substr($name, -1) == '/') {
                    $this->dirs[] = substr($name, 0, -1);
                } else {
                    $this->files[] = &$this->rep->getFileObject($this->queryDir() . "/$name", $cache, $quicklog);
                }
            }
        }

        pclose($dir);

        return 1;
    }

    /**
     * Sort the contents of the directory in a given fashion and
     * order.
     *
     * @param $how Of the form VC_SORT_* where * can be:
     *             NONE, NAME, AGE, REV for sorting by name, age or revision.
     * @param $dir Of the form VC_SORT_* where * can be:
     *             ASCENDING, DESCENDING for the order of the sort.
     */
    function applySort($how = VC_SORT_NONE, $dir = VC_SORT_ASCENDING)
    {
        /* TODO: this code looks very inefficient! optimise... -
         * avsm. */

        // Assume by name for the moment.
        natcasesort($this->dirs);
        $this->doFileSort($this->files, $how, $dir);
        if (isset($this->atticFiles)) {
            $this->doFileSort($this->atticFiles, $how, $dir);
        }
        if (isset($this->mergedFiles)) {
            $this->doFileSort($this->mergedFiles, $how, $dir);
        }
        if ($dir == VC_SORT_DESCENDING) {
            $this->dirs = array_reverse($this->dirs);
            $this->files = array_reverse($this->files);
            if (isset($this->mergedFiles)) {
                $this->mergedFiles = array_reverse($this->mergedFiles);
            }
        }
    }

    function doFileSort(&$fileList, $how = VC_SORT_NONE, $dir = VC_SORT_ASCENDING)
    {
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

        case VC_SORT_NONE:
        default:
            break;
        }
    }

    /**
     * Sort function for ascending age.
     */
    function fileAgeSort($a, $b)
    {
        $aa = $a->queryLastLog();
        $bb = $b->queryLastLog();
        if ($aa->queryDate() == $bb->queryDate()) {
            return 0;
        } else {
            return ($aa->queryDate() < $bb->queryDate()) ? 1 : -1;
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
        } else {
            return ($aa->queryAuthor() > $bb->queryAuthor()) ? 1 : -1;
        }
    }

    /**
     * Sort function for ascending filename.
     */
    function fileNameSort($a, $b)
    {
        return strcasecmp($a->name, $b->name);
    }

    /**
     * Sort function for ascending revision.
     */
    function fileRevSort($a, $b)
    {
        return VC_Revision::cmp($a->queryHead(), $b->queryHead());
    }

}

/**
 * VC_svn file class.
 *
 * Copyright Anil Madhavapeddy, <anil@recoil.org>
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @package VC
 */
class VC_File_svn extends VC_File {

    /**
     * Create a repository file object, and give it information about
     * what its parent directory and repository objects are.
     *
     * @param string $fl  Full path to this file.
     */
    function VC_File_svn(&$rep, $fl, $quicklog = false)
    {
        $this->rep = &$rep;
        $this->name = basename($fl);
        $this->dir = dirname($fl);
        $this->logs = array();
        $this->quicklog = $quicklog;
        $this->revs = array();
        $this->revsym = array();
        $this->symrev = array();
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
            // The file is cached for one hour no matter what, because
            // there is no way to determine with Subversion the time
            // the file last changed.
            $fileOb = unserialize($cache->getData($cacheId, "serialize(VC_File_svn::_getFileObject('$filename', '$quicklog'))", time() - 360));
        } else {
            $fileOb = &VC_File_svn::_getFileObject($filename, $quicklog);
        }

        $fileOb->setRepository($rep);

        if (is_a(($result = $fileOb->getBrowseInfo()), 'PEAR_Error')) {
            return $result;
        }

        return $fileOb;
    }

    function &_getFileObject($filename, $quicklog = false)
    {
        $fileOb = &new VC_File_svn($rep, $filename, $quicklog);
        $fileOb->applySort(VC_SORT_AGE);
        return $fileOb;
    }

    /**
     * If this file is present in an Attic directory, this indicates
     * it.
     *
     * @return true if file is in the Attic, and false otherwise
     */
    function isAtticFile()
    {
        // Not implemented yet
        return false;
    }

    /**
     * Returns the name of the current file as in the repository
     *
     * @return Filename (without the path)
     */
    function queryRepositoryName()
    {
        return $this->name;
    }

    /**
     * Returns name of the current file without the repository
     * extensions (usually ,v)
     *
     * @return Filename without repository extension
     */
    function queryName()
    {
       return preg_replace('/,v$/', '', $this->name);
    }

    /**
     * Return the last revision of the current file on the HEAD branch
     *
     * @return Last revision of the current file
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
        $last = false;
        foreach ($this->revs as $entry) {
            if ($last)
                return $entry;
            if ($entry == $rev)
                $last = true;
        }

        return false;
    }

    /**
     * Return the HEAD (most recent) revision number for this file.
     *
     * @return HEAD revision number
     */
    function queryHead()
    {
        return $this->queryRevision();
    }

    /**
     * Return the last VC_Log object in the file.
     *
     * @return VC_Log of the last entry in the file
     */
    function queryLastLog()
    {
        if (!isset($this->revs[0]) || !isset($this->logs[$this->revs[0]])) {
            return PEAR::raiseError(_("No revisions"));
        }
        return $this->logs[$this->revs[0]];
    }

    /**
     * Sort the list of VC_Log objects that this file contains.
     *
     * @param how VC_SORT_REV (sort by revision),
     *            VC_SORT_NAME (sort by author name),
     *            VC_SORT_AGE (sort by commit date)
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
     * @return PEAR_Error object on error, or true on success
     */
    function getBrowseInfo()
    {
        /* XXX: $flag = ($this->quicklog ? '-r HEAD ' : ''; */
        $flag = '';
        $cmd = $this->rep->getPath('svn') . ' log -v ' . $flag . $this->queryFullPath() . ' 2>&1';
        $pipe = popen($cmd, 'r');
        fgets($pipe);
        while (!feof($pipe)) {
            $log = &new VC_Log_svn($this->rep, $this);
            $err = $log->processLog($pipe);
            if ($err) {
                $rev = $log->queryRevision();
                $this->logs[$rev] = $log;
                $this->revs[] = $rev;
            }

            if ($this->quicklog) {
                break;
            }
        }

        pclose($pipe);
        return true;
    }

    /**
     * Return the fully qualified filename of this object.
     *
     * @return Fully qualified filename of this object
     */
    function queryFullPath()
    {
        return $this->rep->sourceroot() . '/' . $this->queryModulePath();
    }

    /**
     * Return the name of this file relative to its sourceroot.
     *
     * @return string  Pathname relative to the sourceroot.
     */
    function queryModulePath()
    {
        return $this->dir . '/' . $this->name;
    }

}

/**
 * VC_svn log class.
 *
 * Anil Madhavapeddy, <anil@recoil.org>
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @package VC
 */
class VC_Log_svn {

    var $rep, $file, $files, $tags, $rev, $date, $log, $author, $state, $lines, $branches;

    /**
     *
     */
    function VC_Log_svn($rep, &$fl)
    {
        $this->rep = $rep;
        $this->file = &$fl;
        $this->branches = array();
    }

    function processLog($pipe)
    {
        $line = fgets($pipe);

        if (feof($pipe)) {
            return false;
        }

        preg_match('/^r([0-9]*) \| ([^ ]*) \| (.*) \(.*\) \| ([0-9]*) lines?$/', $line, $matches);
        $this->rev = $matches[1];
        $this->author = $matches[2];
        $this->date = strtotime($matches[3]);
        $size = $matches[4];

        fgets($pipe);

        $this->files = array();
        while (($line = trim(fgets($pipe))) != '') {
            $this->files[] = $line;
        }

        for ($i = 0; $i != $size; ++$i) {
            $this->log = $this->log . chop(fgets($pipe)) . "\n";
        }

        $this->log = chop($this->log);
        fgets($pipe);

        return true;
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
     * @return hash of symbolic names => branch numbers
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
 * VC_svn Patchset class.
 *
 * Copyright Anil Madhavapeddy, <anil@recoil.org>
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @package VC
 */
class VC_Patchset_svn {

    var $_rep;
    var $_file;
    var $_patchsets = array();

    /**
     * Create a patchset object.
     *
     * @param string $file  The filename to get patchsets for.
     */
    function VC_Patchset_svn($file)
    {
        $this->_file = $file;
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
            $cacheId = $filename . '_f_v' . $_cacheVersion;
            // The file is cached for one hour no matter what, because there
            // is no way to determine with svn the time the file last changed.
            $psOb = unserialize($cache->getData($cacheId, "serialize(VC_Patchset_svn::_getPatchsetObject('$filename'))", time() - 360));
        } else {
            $psOb = &VC_Patchset_svn::_getPatchsetObject($filename);
        }

        $psOb->_rep = &$rep;

        if (is_a(($result = $psOb->getPatchsets($rep)), 'PEAR_Error')) {
            return $result;
        }

        return $psOb;
    }

    function &_getPatchsetObject($filename)
    {
        return new VC_Patchset_svn($filename);
    }

    /**
     * Populate the object with information about the patchsets that
     * this file is involved in.
     *
     * @param string $repository  The full repository location.
     *
     * @return mixed  PEAR_Error object on error, or true on success.
     */
    function getPatchsets($repository)
    {
        $fileOb = &new VC_File_svn($this->_rep, $this->_file);
        if (is_a(($result = $fileOb->getBrowseInfo()), 'PEAR_Error')) {
            return $result;
        }

        $this->_patchsets = array();
        foreach ($fileOb->logs as $rev => $log) {
            $this->_patchsets[$rev] = array();
            $this->_patchsets[$rev]['date'] = $log->queryDate();
            $this->_patchsets[$rev]['author'] = $log->queryAuthor();
            $this->_patchsets[$rev]['branch'] = '';
            $this->_patchsets[$rev]['tag'] = '';
            $this->_patchsets[$rev]['log'] = $log->queryLog();
            $this->_patchsets[$rev]['members'] = array();
            foreach ($log->files as $file) {
                $action = substr($file, 0, 1);
                $file = preg_replace('/.*?\s(.*?)(\s|$).*/', '\\1', $file);
                $to = $rev;
                if ($action == 'A') {
                    $from = 'INITIAL';
                } elseif ($action == 'D') {
                    $from = $to;
                    $to = '(DEAD)';
                } else {
                    // This technically isn't the previous revision,
                    // but it works for diffing purposes.
                    $from = $to - 1;
                }

                $this->_patchsets[$rev]['members'][] = array('file' => $file,
                                                             'from' => $from,
                                                             'to' => $to);
            }
        }

        return true;
    }

}
