<?php
/**
 * The Horde_Editor_tinymce:: class provides an WYSIWYG editor for use
 * in the Horde Framework.
 *
 * $Horde: framework/Editor/Editor/tinymce.php,v 1.15.2.3 2009-01-06 15:23:03 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 * Copyright 2005-2007 Ryan Miller <rmiller@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Nuno Loureiro <nuno@co.sapo.pt>
 * @author  Jan Schneider <jan@horde.org>
 * @author  Ryan Miller <rmiller@horde.org>
 * @since   Horde 3.2
 * @package Horde_Editor
 */
class Horde_Editor_tinymce extends Horde_Editor {

    /**
     * Constructor.
     *
     * @param array $params  The following configuration parameters:
     * <pre>
     * 'buttons' - The list of buttons to show. An array of strings - each
     *             string should contain the list of buttons to displayed on
     *             that row.
     * 'config' - Config params to pass to tinymce.
     * 'id' - The ID of the text area to turn into an editor.
     * 'no_autoload' - Don't load tinymce by default on pageload.
     * 'no_notify' - Don't output JS code via notification library. Code will
     *               be stored for access via getJS().
     * </pre>
     */
    function Horde_Editor_tinymce($params = array())
    {
        $params['config'] = isset($params['config']) ? $params['config'] : array();

        if (!empty($params['buttons'])) {
            $params['config']['theme'] = 'advanced';
            for ($i = 0, $ilength = count($params['buttons']); $i <= $ilength; ++$i) {
                $params['config']['theme_advanced_buttons' . ($i + 1)] = ($i == $ilength) ? '' : $params['buttons'][$i];
            }
        }

        if (empty($params['no_autoload'])) {
            $params['config'] = array_merge($params['config'], array('elements' => $params['id'], 'mode' => 'exact'));
        } else {
            $params['config'] = array_merge($params['config'], array('mode' => 'none'));
        }

        $p = array();
        foreach ($params['config'] as $config => $value) {
            if (is_bool($value)) {
                $value = ($value) ? 'true' : 'false';
            } else {
                $value = '\'' . addslashes($value) . '\'';
            }

            $p[] = $config . ':' . $value . '';
        }
        $js = 'tinyMCE.init({' . implode(',', $p) . '});';

        $mce_path = '/services/editor/tinymce/tiny_mce.js';
        if (!empty($params['no_notify'])) {
            $mce_path = $GLOBALS['registry']->get('webroot', 'horde') . $mce_path;
            $this->_js = '<script type="text/javascript" src="' . $mce_path . '"></script><script type="text/javascript">' . $js . '</script>';
        } else {
            Horde::addScriptFile($mce_path, 'horde', true);
            $GLOBALS['notification']->push($js, 'javascript');
        }
    }

}
