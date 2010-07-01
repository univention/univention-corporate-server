<?php

/**
 * Driver for using mkisofs for creating ISO images.
 *
 * $Horde: framework/VFS_ISOWriter/ISOWriter/mkisofs.php,v 1.1.8.9 2009-01-06 15:23:48 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jason M. Felice <jason.m.felice@gmail.com>
 * @package VFS_ISO
 * @since   Horde 3.0
 */
class VFS_ISOWriter_mkisofs extends VFS_ISOWriter {

    function process()
    {
        require_once dirname(__FILE__) . '/RealInputStrategy.php';
        $inputStrategy = &VFS_ISOWriter_RealInputStrategy::factory($this->_sourceVfs, $this->_params['sourceRoot']);
        if (is_a($inputStrategy, 'PEAR_Error')) {
            return $inputStrategy;
        }

        require_once dirname(__FILE__) . '/RealOutputStrategy.php';
        $outputStrategy = &VFS_ISOWriter_RealOutputStrategy::factory($this->_targetVfs, $this->_params['targetFile']);
        if (is_a($outputStrategy, 'PEAR_Error')) {
            return $outputStrategy;
        }

        $cmd = sprintf('mkisofs -quiet -r -J -o %s %s >/dev/null',
                       escapeshellarg($outputStrategy->getRealFilename()),
                       escapeshellarg($inputStrategy->getRealPath()));
        $res = system($cmd, $ec);

        /* Could be a lot of space used.  Give both a chance to clean up even
         * if one errors out. */
        $finRes1 = $inputStrategy->finished();
        $finRes2 = $outputStrategy->finished();
        if (is_a($finRes1, 'PEAR_Error')) {
            return $finRes1;
        }
        if (is_a($finRes2, 'PEAR_Error')) {
            return $finRes2;
        }

        if ($res === false) {
            return PEAR::raiseError(_("Unable to run 'mkisofs'."));
        }
        if ($ec != 0) {
            return PEAR::raiseError(sprintf(_("mkisofs error code %d while making ISO."), $ec));
        }
    }

    /**
     * Determine if we can use this driver to make images
     *
     * @static
     *
     * @return boolean  Whether we can use this strategy for making ISO images.
     */
    function strategyAvailable()
    {
        /* Check if we can find and execute the `mkisofs' command. */
        $res = system("mkisofs -help >/dev/null 2>&1", $ec);
        if ($res === false) {
            return false;
        }
        if ($ec != 0) {
            return false;
        }
        return true;
    }

}

