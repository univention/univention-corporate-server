<?php

require_once 'Horde/Block.php';

/**
 * The Horde_Block_Collection:: class provides an API to the blocks
 * (applets) framework.
 *
 * $Horde: framework/Block/Block/Collection.php,v 1.36.4.22 2009-01-06 15:22:53 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.0
 * @package Horde_Block
 */
class Horde_Block_Collection {

    /**
     * What kind of blocks are we collecting? Defaults to any.
     *
     * @var string
     */
    var $_type = 'portal';

    /**
     * A hash storing the information about all available blocks from
     * all applications.
     *
     * @var array
     */
    var $_blocks = array();

    /**
     * Constructor.
     *
     * @param string $type  The kind of blocks to list.
     * @param array $apps   The applications whose blocks to list.
     */
    function Horde_Block_Collection($type = null, $apps = array())
    {
        if (!is_null($type)) {
            $this->_type = $type;
        }

        $signature = serialize($apps);
        if (isset($_SESSION['horde']['blocks'][$signature])) {
            $this->_blocks = &$_SESSION['horde']['blocks'][$signature];
            return;
        }

        global $registry;
        require_once 'Horde/Block.php';

        foreach ($registry->listApps() as $app) {
            if (count($apps) && !in_array($app, $apps)) {
                continue;
            }
            if (is_a($pushed = $registry->pushApp($app), 'PEAR_Error')) {
                continue;
            }
            $blockdir = $registry->get('fileroot', $app) . '/lib/Block';
            $dh = @opendir($blockdir);
            if (is_resource($dh)) {
                while (($file = readdir($dh)) !== false) {
                    if (substr($file, -4) == '.php') {
                        $block_name = null;
                        $block_type = null;
                        if (is_readable($blockdir . '/' . $file)) {
                            include_once $blockdir . '/' . $file;
                        }
                        if (!is_null($block_type) && !is_null($this->_type) &&
                            $block_type != $this->_type) {
                            continue;
                        }
                        if (!empty($block_name)) {
                            $this->_blocks[$app][substr($file, 0, -4)]['name'] = $block_name;
                        }
                    }
                }
                closedir($dh);
            }
            // Don't pop an application if we didn't have to push one.
            if ($pushed) {
                $registry->popApp($app);
            }
        }

        uksort($this->_blocks, array($this, '_sortBlockCollection'));
        $_SESSION['horde']['blocks'][$signature] = &$this->_blocks;
    }

    /**
     * Block sorting helper
     */
    function _sortBlockCollection($a, $b)
    {
        return strcasecmp($GLOBALS['registry']->get('name', $a), $GLOBALS['registry']->get('name', $b));
    }

    /**
     * Returns a single instance of the Horde_Blocks class.
     *
     * @static
     *
     * @param string $type  The kind of blocks to list.
     * @param array $apps   The applications whose blocks to list.
     *
     * @return Horde_Block_Collection  The Horde_Block_Collection instance.
     */
    function &singleton($type = null, $apps = array())
    {
        static $instances = array();

        $signature = serialize(array($type, $apps));
        if (!isset($instances[$signature])) {
            $instances[$signature] = new Horde_Block_Collection($type, $apps);
        }

        return $instances[$signature];
    }

    function &getBlock($app, $name, $params = null, $row = null, $col = null)
    {
        if ($GLOBALS['registry']->get('status', $app) == 'inactive' ||
            ($GLOBALS['registry']->get('status', $app) == 'admin' &&
             !Auth::isAdmin())) {
            $error = PEAR::raiseError(sprintf(_("%s is not activated."), $GLOBALS['registry']->get('name', $app)));
            return $error;
        }

        $path = $GLOBALS['registry']->get('fileroot', $app) . '/lib/Block/' . $name . '.php';
        if (is_readable($path)) {
            include_once $path;
        }
        $class = 'Horde_Block_' . $app . '_' . $name;
        if (!class_exists($class)) {
            $error = PEAR::raiseError(sprintf(_("%s not found."), $class));
            return $error;
        }

        $block = &new $class($params, $row, $col);
        return $block;
    }

    /**
     * Returns a pretty printed list of all available blocks.
     *
     * @return array  A hash with block IDs as keys and application plus block
     *                block names as values.
     */
    function getBlocksList()
    {
        static $blocks = array();
        if (!empty($blocks)) {
            return $blocks;
        }

        global $registry;

        /* Get available blocks from all apps. */
        foreach ($this->_blocks as $app => $app_blocks) {
            foreach ($app_blocks as $block_id => $block) {
                if (isset($block['name'])) {
                    $blocks[$app . ':' . $block_id] = $registry->get('name', $app) . ': ' . $block['name'];
                }
            }
        }

        return $blocks;
    }

    /**
     * Returns a layout with all fixed blocks as per configuration.
     *
     * @return string  A default serialized block layout.
     */
    function getFixedBlocks()
    {
        global $conf;

        $layout = array();
        if (isset($conf['portal']['fixed_blocks'])) {
            foreach ($conf['portal']['fixed_blocks'] as $block) {
                list($app, $type) = explode(':', $block, 2);
                $layout[] = array(array('app' => $app,
                                        'params' => array('type' => $type,
                                                          'params' => false),
                                        'height' => 1,
                                        'width' => 1));
            }
        }

        return $layout;
    }

    /**
     * Returns a select widget with all available blocks.
     *
     * @param string $cur_app    The block from this application gets selected.
     * @param string $cur_block  The block with this name gets selected.
     *
     * @return string  The select tag with all available blocks.
     */
    function getBlocksWidget($cur_app = null, $cur_block = null, $onchange = false)
    {
        global $registry;

        $widget = '<select name="app"';
        if ($onchange) {
            $widget .= ' onchange="document.blockform.action.value=\'save-resume\';document.blockform.submit()"';
        }
        $widget .= ">\n";
        $blocks_list = $this->getBlocksList();
        foreach ($blocks_list as $id => $name) {
            $widget .= sprintf("<option value=\"%s\"%s>%s</option>\n",
                                   $id,
                                   ($id == $cur_app . ':' . $cur_block) ? ' selected="selected"' : '',
                                   $name);
        }
        $widget .= "</select>\n";

        return $widget;
    }

    /**
     * Returns the option type.
     */
    function getOptionType($app, $block, $param_id)
    {
        $this->getParams($app, $block);
        return $this->_blocks[$app][$block]['params'][$param_id]['type'];
    }

    /**
     * Returns whether the option is required or not. Defaults to true.
     */
    function getOptionRequired($app, $block, $param_id)
    {
        $this->getParams($app, $block);
        if (!isset($this->_blocks[$app][$block]['params'][$param_id]['required'])) {
            return true;
        } else {
            return $this->_blocks[$app][$block]['params'][$param_id]['required'];
        }
    }

    /**
     * Returns the values for an option.
     */
    function &getOptionValues($app, $block, $param_id)
    {
        $this->getParams($app, $block);
        return $this->_blocks[$app][$block]['params'][$param_id]['values'];
    }

    /**
     * Returns the widget necessary to configure this block.
     */
    function getOptionsWidget($app, $block, $param_id, $val = null)
    {
        $widget = '';

        $this->getParams($app, $block);
        $param = $this->_blocks[$app][$block]['params'][$param_id];
        if (!isset($param['default'])) {
            $param['default'] = '';
        }

        switch ($param['type']) {
        case 'boolean':
        case 'checkbox':
            $checked = !empty($val[$param_id]) ? ' checked="checked"' : '';
            $widget = sprintf('<input type="checkbox" name="params[%s]"%s />', $param_id, $checked);
            break;

        case 'enum':
            $widget = sprintf('<select name="params[%s]">', $param_id);
            foreach ($param['values'] as $key => $name) {
                if (String::length($name) > 30) {
                    $name = substr($name, 0, 27) . '...';
                }
                $widget .= sprintf("<option value=\"%s\"%s>%s</option>\n",
                                   htmlspecialchars($key),
                                   (isset($val[$param_id]) && $val[$param_id] == $key) ? ' selected="selected"' : '',
                                   htmlspecialchars($name));
            }

            $widget .= '</select>';
            break;

        case 'multienum':
            $widget = sprintf('<select multiple="multiple" name="params[%s][]">', $param_id);
            foreach ($param['values'] as $key => $name) {
                if (String::length($name) > 30) {
                    $name = substr($name, 0, 27) . '...';
                }
                $widget .= sprintf("<option value=\"%s\"%s>%s</option>\n",
                                   htmlspecialchars($key),
                                   (isset($val[$param_id]) && in_array($key, $val[$param_id])) ? ' selected="selected"' : '',
                                   htmlspecialchars($name));
            }

            $widget .= '</select>';
            break;

        case 'mlenum':
            // Multi-level enum.
            if (is_array($val) && isset($val['__' . $param_id])) {
                $firstval = $val['__' . $param_id];
            } else {
                $tmp = array_keys($param['values']);
                $firstval = current($tmp);
            }
            $blockvalues = $param['values'][$firstval];
            asort($blockvalues);

            $widget = sprintf('<select name="params[__%s]" onchange="document.blockform.action.value=\'save-resume\';document.blockform.submit()">', $param_id) . "\n";
            foreach ($param['values'] as $key => $values) {
                $name = String::length($key) > 30 ? String::substr($key, 0, 27) . '...' : $key;
                $widget .= sprintf("<option value=\"%s\"%s>%s</option>\n",
                                   htmlspecialchars($key),
                                   $key == $firstval ? ' selected="selected"' : '',
                                   htmlspecialchars($name));
            }
            $widget .= "</select><br />\n";

            $widget .= sprintf("<select name=\"params[%s]\">\n", $param_id);
            foreach ($blockvalues as $key => $name) {
                $name = (String::length($name) > 30) ? String::substr($name, 0, 27) . '...' : $name;
                $widget .= sprintf("<option value=\"%s\"%s>%s</option>\n",
                                   htmlspecialchars($key),
                                   $val[$param_id] == $key ? ' selected="selected"' : '',
                                   htmlspecialchars($name));
            }
            $widget .= "</select><br />\n";
            break;

        case 'int':
        case 'text':
            $widget = sprintf('<input type="text" name="params[%s]" value="%s" />', $param_id, !isset($val[$param_id]) ? $param['default'] : $val[$param_id]);
            break;

        case 'error':
            $widget = '<span class="form-error">' . $param['default'] . '</span>';
            break;
        }

        return $widget;
    }

    /**
     * Returns the name of the specified block.
     *
     * @param string $app    An application name.
     * @param string $block  A block name.
     *
     * @return string  The name of the specified block.
     */
    function getName($app, $block)
    {
        if (!isset($this->_blocks[$app][$block])) {
            return sprintf(_("Block \"%s\" of application \"%s\" not found."), $block, $app);
        }
        return $this->_blocks[$app][$block]['name'];
    }

    /**
     * Returns the parameter list of the specified block.
     *
     * @param string $app    An application name.
     * @param string $block  A block name.
     *
     * @return array  An array with all paramter names.
     */
    function getParams($app, $block)
    {
        if (!isset($this->_blocks[$app][$block]['params'])) {
            $blockOb = &$this->getBlock($app, $block);
            if (is_a($blockOb, 'PEAR_Error')) {
                return $blockOb;
            }
            $this->_blocks[$app][$block]['params'] = $blockOb->getParams();
        }

        if (isset($this->_blocks[$app][$block]['params']) &&
            is_array($this->_blocks[$app][$block]['params'])) {
            return array_keys($this->_blocks[$app][$block]['params']);
        } else {
            return array();
        }
    }

    /**
     * Returns the (clear text) name of the specified parameter.
     *
     * @param string $app    An application name.
     * @param string $block  A block name.
     * @param string $param  A parameter name.
     *
     * @return string  The name of the specified parameter.
     */
    function getParamName($app, $block, $param)
    {
        $this->getParams($app, $block);
        return $this->_blocks[$app][$block]['params'][$param]['name'];
    }

    /**
     * Returns the default value of the specified parameter.
     *
     * @param string $app    An application name.
     * @param string $block  A block name.
     * @param string $param  A parameter name.
     *
     * @return string  The default value of the specified parameter or null.
     */
    function getDefaultValue($app, $block, $param)
    {
        $this->getParams($app, $block);
        if (isset($this->_blocks[$app][$block]['params'][$param]['default'])) {
            return $this->_blocks[$app][$block]['params'][$param]['default'];
        }
        return null;
    }

    /**
     * Returns if the specified block is customizeable by the user.
     *
     * @param string $app    An application name.
     * @param string $block  A block name.
     *
     * @return boolean  True is the block is customizeable.
     */
    function isEditable($app, $block)
    {
        $this->getParams($app, $block);
        return isset($this->_blocks[$app][$block]['params']) &&
            count($this->_blocks[$app][$block]['params']);
    }

}
