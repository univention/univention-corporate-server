<?php
/**
 * A library for reading/writing the Kolab format.
 *
 * $Horde: framework/Kolab_Format/lib/Horde/Kolab/Format.php,v 1.4.2.4 2008-12-12 11:39:03 wrobel Exp $
 *
 * @package Kolab_Format
 */

/** We need PEAR */
require_once 'PEAR.php';

/**
 * The Horde_Kolab_Format:: class provides the means to read/write the
 * Kolab format.
 *
 * $Horde: framework/Kolab_Format/lib/Horde/Kolab/Format.php,v 1.4.2.4 2008-12-12 11:39:03 wrobel Exp $
 *
 * Copyright 2007-2008 Klarälvdalens Datakonsult AB
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @since   Horde 3.2
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @package Kolab_Format
 */
class Horde_Kolab_Format
{

    /**
     * Attempts to return a concrete Horde_Kolab_Format instance based on $format_type.
     *
     * @param string    $format_type    The format type that should be handled.
     * @param string    $object_type    The object type that should be handled.
     * @param array     $params         An array of  additional parameters.
     *
     *                                  Supported parameters:
     *
     *                                    'version' - The format version.
     *
     * @return mixed    The newly created concrete Horde_Kolab_Format_XML instance, or
     *                  a PEAR error.
     */
    function &factory($format_type = '', $object_type = '', $params = null)
    {
        @include_once dirname(__FILE__) . '/Format/' . $format_type . '.php';
        $class = 'Horde_Kolab_Format_' . $format_type;
        if (class_exists($class)) {
            $driver = call_user_func(array($class, 'factory'), $object_type, $params);
        } else {
            return PEAR::raiseError(sprintf(_("Failed to load Kolab Format driver %s"), $format_type));
        }

        return $driver;
    }

}
