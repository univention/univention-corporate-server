<?php

/**
 * Strategy for directly accessing input tree in a 'file' VFS
 *
 * $Horde: framework/VFS_ISOWriter/ISOWriter/RealInputStrategy/direct.php,v 1.1.8.8 2009-01-06 15:23:48 jan Exp $
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
class VFS_ISOWriter_RealInputStrategy_direct extends VFS_ISOWriter_RealInputStrategy {

    function getRealPath()
    {
        return $this->_sourceVfs->_getNativePath($this->_sourceRoot);
    }

    function finished()
    {
    }

}
