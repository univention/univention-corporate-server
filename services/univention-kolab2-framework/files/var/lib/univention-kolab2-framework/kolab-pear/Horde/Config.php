<?php
/**
 * The Config:: package provides a framework for managing the
 * configuration of Horde applications, writing conf.php files from
 * conf.xml source files, generating user interfaces, etc.
 *
 * $Horde: framework/Horde/Horde/Config.php,v 1.69 2004/04/20 21:42:18 jan Exp $
 *
 * Copyright 2002-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Framework
 */
class Horde_Config {

    /**
     * The name of the configured application.
     *
     * @var string $_app
     */
    var $_app;

    /**
     * The XML tree of the configuration file traversed to an
     * associative array.
     *
     * @var array $_xmlConfigTree
     */
    var $_xmlConfigTree = null;

    /**
     * The content of the generated configuration file.
     *
     * @var string $_phpConfig
     */
    var $_phpConfig;

    /**
     * The content of the old configuration file.
     *
     * @var string $_oldConfig
     */
    var $_oldConfig;

    /**
     * The manual configuration in front of the generated
     * configuration.
     *
     * @var string $_preConfig
     */
    var $_preConfig;

    /**
     * The manual configuration after the generated configuration.
     *
     * @var string $_preConfig
     */
    var $_postConfig;

    /**
     * The current $conf array of the configured application.
     *
     * @var array $_currentConfig
     */
    var $_currentConfig = array();

    /**
     * The CVS version tag of the conf.xml file which will be copied
     * into the conf.php file.
     *
     * @var string $_versionTag
     */
    var $_versionTag = '';

    /**
     * The line marking the begin of the generated configuration.
     *
     * @var string $_configBegin
     */
    var $_configBegin = "/* CONFIG START. DO NOT CHANGE ANYTHING IN OR AFTER THIS LINE. */\n";

    /**
     * The line marking the end of the generated configuration.
     *
     * @var string $_configEnd
     */
    var $_configEnd = "/* CONFIG END. DO NOT CHANGE ANYTHING IN OR BEFORE THIS LINE. */\n";

    /**
     * Constructor.
     *
     * @param string $app  The name of the application to be configured.
     */
    function Horde_Config($app)
    {
        $this->_app = $app;
    }

    /**
     * Reads the application's conf.xml file and builds an associative
     * array from its XML tree.
     *
     * @return array  An associative array representing the configuration tree.
     */
    function readXMLConfig()
    {
        if (is_null($this->_xmlConfigTree)) {
            require_once 'Horde/Text.php';

            global $registry;
            $path = $registry->getParam('fileroot', $this->_app) . '/config';

            /* Fetch the current conf.php contents. */
            @eval($this->getPHPConfig());
            if (isset($conf)) {
                $this->_currentConfig = $conf;
            }

            /* Set up the domxml document. */
            $this->_xmlConfigTree = array();
            $doc = domxml_open_file($path . '/conf.xml');

            /* Check if there is a CVS version tag and store it. */
            $node = $doc->first_child();
            while (!empty($node)) {
                if ($node->node_type() == XML_COMMENT_NODE) {
                    if (preg_match('/\$.*?conf\.xml,v .*? .*\$/', $node->node_value(), $match)) {
                        $this->_versionTag = $match[0] . "\n";
                        break;
                    }
                }
                $node = $node->next_sibling();
            }

            /* Parse remaining config file. */
            $root = $doc->root();
            if ($root->has_child_nodes()) {
                $this->_parseLevel($this->_xmlConfigTree, $root->child_nodes(), '');
            }
        }

        return $this->_xmlConfigTree;
    }

    /**
     * Returns the file content of the current configuration file.
     *
     * @return string  The unparsed configuration file content.
     */
    function getPHPConfig()
    {
        if (is_null($this->_oldConfig)) {
            global $registry;
            $path = $registry->getParam('fileroot', $this->_app) . '/config';
            $size = @filesize($path . '/conf.php');
            if ($size && is_resource($fp = @fopen($path . '/conf.php', 'r'))) {
                $this->_oldConfig = @fread($fp, $size);
                $this->_oldConfig = preg_replace('/<\?php\n?/', '', $this->_oldConfig);
                $pos = strpos($this->_oldConfig, $this->_configBegin);
                if ($pos !== false) {
                    $this->_preConfig = substr($this->_oldConfig, 0, $pos);
                    $this->_oldConfig = substr($this->_oldConfig, $pos);
                }
                $pos = strpos($this->_oldConfig, $this->_configEnd);
                if ($pos !== false) {
                    $this->_postConfig = substr($this->_oldConfig, $pos + strlen($this->_configEnd));
                    $this->_oldConfig = substr($this->_oldConfig, 0, $pos);
                }
            } else {
                $this->_oldConfig = '';
            }
        }
        return $this->_oldConfig;
    }
            
    /**
     * Generates the content of the application's configuration file.
     *
     * @param Variables $formvars  The processed configuration form data.
     *
     * @return string  The content of the generated configuration file.
     */
    function generatePHPConfig($formvars)
    {
        $this->readXMLConfig();
        $this->getPHPConfig();

        $this->_phpConfig = "<?php\n";
        $this->_phpConfig .= $this->_preConfig;
        $this->_phpConfig .= $this->_configBegin;
        if (!empty($this->_versionTag)) {
            $this->_phpConfig .= '// ' . $this->_versionTag;
        }
        $this->_generatePHPConfig($this->_xmlConfigTree, '', $formvars);
        $this->_phpConfig .= $this->_configEnd;
        $this->_phpConfig .= $this->_postConfig;

        return $this->_phpConfig;
    }

    /**
     * Generates the configuration file items for a part of the configuration
     * tree.
     *
     * @access private
     *
     * @param array $section  An associative array containing the part of the
     *                        traversed XML configuration tree that should be
     *                        processed.
     * @param string $prefix  A configuration prefix determining the current
     *                        position inside the configuration file. This
     *                        prefix will be translated to keys of the $conf
     *                        array in the generated configuration file.
     * @param Variables $formvars  The processed configuration form data.
     */
    function _generatePHPConfig($section, $prefix, $formvars)
    {
        foreach ($section as $name => $configitem) {
            $prefixedname = empty($prefix) ? $name : $prefix . '|' . $name;
            $configname = $prefixedname;
            $quote = !isset($configitem['quote']) || $configitem['quote'] !== false;
            if ($configitem == 'placeholder') {
                $this->_phpConfig .= '$conf[\'' . str_replace('|', '\'][\'', $prefix) . "'] = array();\n";
            } elseif (isset($configitem['switch'])) {
                $val = $formvars->getExists($configname, $wasset);
                if (!$wasset) {
                    $val = isset($configitem['default']) ? $configitem['default'] : null;
                }
                if (isset($configitem['switch'][$val])) {
                    $value = $val;
                    if ($quote && $value != 'true' && $value != 'false') {
                        $value = "'" . $value . "'";
                    }
                    $this->_generatePHPConfig($configitem['switch'][$val]['fields'], $prefix, $formvars);
                }
            } elseif (isset($configitem['_type'])) {
                $val = $formvars->getExists($configname, $wasset);
                if (!$wasset) {
                    $val = isset($configitem['default']) ? $configitem['default'] : null;
                }

                $type = $configitem['_type'];
                switch ($type) {
                case 'multienum':
                    if (is_array($val)) {
                        $encvals = array();
                        foreach ($val as $v) {
                            $encvals[] = $this->_quote($v);
                        }
                        $arrayval = "'" . implode('\', \'', $encvals) . "'";
                        if ($arrayval == "''") {
                            $arrayval = '';
                        }
                    } else {
                        $arrayval = '';
                    }
                    $value = 'array(' . $arrayval . ')';
                    break;

                case 'boolean':
                    if (is_bool($val)) {
                        $value = $val ? 'true' : 'false';
                    } else {
                        $value = ($val == 'on') ? 'true' : 'false';
                    }
                    break;

                case 'stringlist':
                    $values = explode(',', $val);
                    if (!is_array($values)) {
                        $value = "array('" . $this->_quote(trim($values)) . "')";
                    } else {
                        $encvals = array();
                        foreach ($values as $v) {
                            $encvals[] = $this->_quote(trim($v));
                        }
                        $arrayval = "'" . implode('\', \'', $encvals) . "'";
                        if ($arrayval == "''") {
                            $arrayval = '';
                        }
                        $value = 'array(' . $arrayval . ')';
                    }
                    break;

                case 'int':
                    if ($val != '') {
                        $value = (int)$val;
                    }
                    break;

                case 'octal':
                    $value = sprintf('0%o', octdec($val));
                    break;

                case 'header':
                case 'description':
                    break;

                default:
                    if ($val != '') {
                        $value = $val;
                        if ($quote && $value != 'true' && $value != 'false') {
                            $value = "'" . $this->_quote($value) . "'";
                        }
                    }
                    break;
                }
            } else {
                $this->_generatePHPConfig($configitem, $prefixedname, $formvars);
            }

            if (isset($value)) {
                $this->_phpConfig .= '$conf[\'' . str_replace('|', '\'][\'', $configname) . '\'] = ' . $value . ";\n";
            }
            unset($value);
        }
    }

    /**
     * Parses one level of the configuration XML tree into the associative
     * array containing the traversed configuration tree.
     *
     * @access private
     *
     * @param array &$conf     The already existing array where the processed
     *                         XML tree portion should be appended to.
     * @param array $children  An array containing the XML nodes of the level
     *                         that should be parsed.
     * @param string $ctx      A string representing the current position
     *                         (context prefix) inside the configuration XML
     *                         file.
     */
    function _parseLevel(&$conf, $children, $ctx)
    {
        foreach ($children as $node) {
            if ($node->type != XML_ELEMENT_NODE) {
                continue;
            }
            $name = $node->get_attribute('name');
            $desc = Text::linkUrls($node->get_attribute('desc'));
            $required = !($node->get_attribute('required') == 'false');
            $quote = !($node->get_attribute('quote') == 'false');
            if (!empty($ctx)) {
                $curctx = $ctx . '|' . $name;
            } else {
                $curctx = $name;
            }

            switch ($node->tagname) {
            case 'configdescription':
                if (empty($name)) {
                    $name = md5(microtime());
                }
                $conf[$name] = array('_type' => 'description',
                                     'desc' => Text::linkUrls($this->_default($curctx, $this->_getNodeOnlyText($node))));
                break;

            case 'configheader':
                if (empty($name)) {
                    $name = md5(microtime());
                }
                $conf[$name] = array('_type' => 'header',
                                     'desc' => $this->_default($curctx, $this->_getNodeOnlyText($node)));
                break;

            case 'configswitch':
                if ($quote) {
                    $default = $this->_default($curctx, $this->_getNodeOnlyText($node));
                } else {
                    $default = $this->_defaultRaw($curctx, $this->_getNodeOnlyText($node));
                }
                $conf[$name] = array('desc' => $desc,
                                     'switch' => $this->_getSwitchValues($node, $ctx),
                                     'default' => $default);
                break;

            case 'configenum':
                $values = $this->_getEnumValues($node);
                if ($quote) {
                    $default = $this->_default($curctx, $this->_getNodeOnlyText($node));
                } else {
                    $default = $this->_defaultRaw($curctx, $this->_getNodeOnlyText($node));
                }
                $conf[$name] = array('_type' => 'enum',
                                     'required' => $required,
                                     'quote' => $quote,
                                     'values' => $values,
                                     'desc' => $desc,
                                     'default' => $default);
                break;

            case 'configlist':
                $default = $this->_default($curctx, null);
                if ($default === null) {
                    $default = $this->_getNodeOnlyText($node);
                } else {
                    $default = implode(', ', $default);
                }
                $conf[$name] = array('_type' => 'stringlist',
                                     'required' => $required,
                                     'desc' => $desc,
                                     'default' => $default);
                break;

            case 'configmultienum':
                $values = $this->_getEnumValues($node);
                require_once 'Horde/Array.php';
                $conf[$name] = array('_type' => 'multienum',
                                     'required' => $required,
                                     'values' => $values,
                                     'desc' => $desc,
                                     'default' => Horde_Array::valuesToKeys($this->_default($curctx,
                                                                                            explode(',', $this->_getNodeOnlyText($node)))));
                break;

            case 'configpassword':
                $conf[$name] = array('_type' => 'password',
                                     'required' => $required,
                                     'desc' => $desc,
                                     'default' => $this->_default($curctx, $this->_getNodeOnlyText($node)));
                break;

            case 'configstring':
                $conf[$name] = array('_type' => 'text',
                                     'required' => $required,
                                     'desc' => $desc,
                                     'default' => $this->_default($curctx, $this->_getNodeOnlyText($node)));
                if ($conf[$name]['default'] === false) {
                    $conf[$name]['default'] = 'false';
                } else if ($conf[$name]['default'] === true) {
                    $conf[$name]['default'] = 'true';
                }
                break;

            case 'configboolean':
                $default = $this->_getNodeOnlyText($node);
                if (empty($default) || $default === 'false') {
                    $default = false;
                } else {
                    $default = true;
                }
                $conf[$name] = array('_type' => 'boolean',
                                     'required' => $required,
                                     'desc' => $desc,
                                     'default' => $this->_default($curctx, $default));
                break;

            case 'configinteger':
                $values = $this->_getEnumValues($node);
                $conf[$name] = array('_type' => 'int',
                                     'required' => $required,
                                     'values' => $values,
                                     'desc' => $desc,
                                     'default' => $this->_default($curctx, $this->_getNodeOnlyText($node)));
                if ($node->get_attribute('octal') == 'true' &&
                    $conf[$name]['default'] != '') {
                    $conf[$name]['_type'] = 'octal';
                    $conf[$name]['default'] = sprintf('0%o', $this->_default($curctx, octdec($this->_getNodeOnlyText($node))));
                }
                break;

            case 'configphp':
                $conf[$name] = array('_type' => 'php',
                                     'required' => $required,
                                     'quote' => false,
                                     'desc' => $desc,
                                     'default' => $this->_defaultRaw($curctx, $this->_getNodeOnlyText($node)));
                break;

            case 'configsection':
                $conf[$name] = array();
                $cur = &$conf[$name];
                if ($node->has_child_nodes()) {
                    $this->_parseLevel($cur, $node->child_nodes(), $curctx);
                }
                break;

            case 'configtab':
                $key = md5(microtime());
                $conf[$key] = array('tab' => $name,
                                    'desc' => $desc);
                if ($node->has_child_nodes()) {
                    $this->_parseLevel($conf, $node->child_nodes(), $ctx);
                }
                break;

            case 'configplaceholder':
                $conf[md5(microtime())] = 'placeholder';
                break;

            default:
                $conf[$name] = array();
                $cur = &$conf[$name];
                if ($node->has_child_nodes()) {
                    $this->_parseLevel($cur, $node->child_nodes(), $curctx);
                }
                break;
            }
        }
    }

    /**
     * Returns a certain value from the current configuration array or
     * a default value, if not found.
     *
     * @access private
     *
     * @param string $ctx     A string representing the key of the
     *                        configuration array to return.
     * @param mixed $default  The default value to return if the key wasn't
     *                        found.
     *
     * @return mixed  Either the value of the configuration array's requested
     *                key or the default value if the key wasn't found.
     */
    function _default($ctx, $default)
    {
        $ctx = explode('|', $ctx);
        $ptr = $this->_currentConfig;
        for ($i = 0; $i < count($ctx); $i++) {
            if (!isset($ptr[$ctx[$i]])) {
                return $default;
            } else {
                $ptr = $ptr[$ctx[$i]];
            }
        }
        if (is_string($ptr)) {
            return String::convertCharset($ptr, 'iso-8859-1');
        } else {
            return $ptr;
        }
    }

    /**
     * Returns a certain value from the current configuration file or
     * a default value, if not found.
     * It does NOT return the actual value, but the PHP expression as used
     * in the configuration file.
     *
     * @access private
     *
     * @param string $ctx     A string representing the key of the
     *                        configuration array to return.
     * @param mixed $default  The default value to return if the key wasn't
     *                        found.
     *
     * @return mixed  Either the value of the configuration file's requested
     *                key or the default value if the key wasn't found.
     */
    function _defaultRaw($ctx, $default)
    {
        $ctx = explode('|', $ctx);
        $pattern = '/^\$conf\[\'' . implode("'\]\['", $ctx) . '\'\] = (.*);$/m';
        if (preg_match($pattern, $this->getPHPConfig(), $matches)) {
            return $matches[1];
        }
        return $default;
    }

    /**
     * Returns the content of all text node children of the specified node.
     *
     * @access private
     *
     * @param DomNode $node  A DomNode object whose text node children to return.
     *
     * @return string  The concatenated values of all text nodes.
     */
    function _getNodeOnlyText($node)
    {
        $text = '';
        if (!$node->has_child_nodes()) {
            return $node->get_content();
        }
        foreach ($node->children() as $tnode) {
            if ($tnode->type == XML_TEXT_NODE) {
                $text .= $tnode->content;
            }
        }

        return trim($text);
    }

    /**
     * Returns an associative array containing all possible values of the
     * specified <configenum> tag.
     * The keys contain the actual enum values while the values contain their
     * corresponding descriptions.
     *
     * @access private
     *
     * @param DomNode $node  The DomNode representation of the <configenum> tag
     *                       whose values should be returned.
     *
     * @return array  An associative array with all possible enum values.
     */
    function _getEnumValues($node)
    {
        $values = array();
        if (!$node->has_child_nodes()) {
            return array();
        }
        foreach ($node->children() as $vnode) {
            if ($vnode->type == XML_ELEMENT_NODE &&
                $vnode->tagname == 'values') {
                if (!$vnode->has_child_nodes()) {
                    return array();
                }
               foreach ($vnode->children() as $value) {
                    if ($value->type == XML_ELEMENT_NODE) {
                        if ($value->tagname == 'configspecial') {
                            return $this->_handleSpecials($value);
                        } elseif ($value->tagname == 'value') {
                            $text = $value->get_content();
                            $desc = $value->get_attribute('desc');
                            if (!empty($desc)) {
                                $values[$text] = $desc;
                            } else {
                                $values[$text] = $text;
                            }
                        }
                    }
                }
            }
        }
        return $values;
    }

    /**
     * Returns a multidimensional associative array representing the specified
     * <configswitch> tag.
     *
     * @access private
     *
     * @param DomNode &$node  The DomNode representation of the <configswitch>
     *                        tag to process.
     *
     * @return array  An associative array representing the node.
     */
    function _getSwitchValues(&$node, $curctx)
    {
        if (!$node->has_child_nodes()) {
            return array();
        }
        $values = array();
        foreach ($node->children() as $case) {
            if ($case->type == XML_ELEMENT_NODE) {
                $name = $case->get_attribute('name');
                $values[$name] = array();
                $values[$name]['desc'] = $case->get_attribute('desc');
                $values[$name]['fields'] = array();
                if ($case->has_child_nodes()) {
                    $this->_parseLevel($values[$name]['fields'], $case->child_nodes(), $curctx);
                }
            }
        }
        return $values;
    }

    /**
     * Returns an associative array containing the possible values of a
     * <configspecial> tag as used inside of enum configurations.
     *
     * @access private
     *
     * @param DomNode $node  The DomNode representation of the <configspecial>
     *                       tag.
     *
     * @return array  An associative array with the possible values.
     */
    function _handleSpecials($node)
    {
        switch ($node->get_attribute('name')) {
        case 'list-horde-apps':
            global $registry;
            require_once 'Horde/Array.php';
            $apps = Horde_Array::valuesToKeys($registry->listApps(array('hidden', 'notoolbar', 'active')));
            asort($apps);
            return $apps;
            break;

        case 'list-horde-languages':
            global $nls;
            return $nls['languages'];
            break;

        case 'list-client-fields':
            global $registry;
            $f = array();
            if ($registry->hasMethod('clients/getClientSource')) {
                $addressbook = $registry->call('clients/getClientSource');
                $fields = $registry->call('clients/fields', array($addressbook));
                if (!is_a($fields, 'PEAR_Error')) {
                    foreach ($fields as $field) {
                        $f[$field['name']] = $field['label'];
                    }
                }
            }
            return $f;
            break;
        }

        return array();
    }

    /**
     * Returns the specified string with escaped single quotes
     *
     * @access private
     *
     * @param string $string  A string to escape.
     *
     * @return string  The specified string with single quotes being escaped.
     */
    function _quote($string)
    {
        return str_replace("'", "\'", $string);
    }

}

/**
 * A Horde_Form:: form that implements a user interface for the config
 * system.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Framework
 */
class ConfigForm extends Horde_Form {

    /**
     * Contains the Horde_Config object that this form represents.
     *
     * @var Horde_Config $_xmlConfig
     */
    var $_xmlConfig;

    /**
     * Contains the Variables object of this form.
     *
     * @var Variables $_vars
     */
    var $_vars;

    /**
     * Constructor.
     *
     * @param Variables &$vars  The Variables object of this form.
     * @param string $app             The name of the application that this
     *                                configuration form is for.
     */
    function ConfigForm(&$vars, $app)
    {
        parent::Horde_Form($vars);

        $this->_xmlConfig = &new Horde_Config($app);
        $this->_vars = &$vars;
        $config = $this->_xmlConfig->readXMLConfig();
        $this->addHidden('', 'app', 'text', true);
        $this->_buildVariables($config);
    }

    /**
     * Builds the form based on the specified level of the configuration tree.
     *
     * @access private
     *
     * @param array $config   The portion of the configuration tree for that
     *                        the form fields should be created.
     * @param string $prefix  A string representing the current position
     *                        inside the configuration tree.
     */
    function _buildVariables($config, $prefix = '')
    {
        if (!is_array($config)) {
            return;
        }
        foreach ($config as $name => $configitem) {
            $prefixedname = empty($prefix) ? $name : $prefix . '|' . $name;
            $varname = $prefixedname;
            $description = null;
            if ($configitem == 'placeholder') {
                continue;
            } elseif (isset($configitem['tab'])) {
                $this->setSection($configitem['tab'], $configitem['desc']);
            } elseif (isset($configitem['switch'])) {
                $selected = $this->_vars->getExists($varname, $wasset);
                $var_params = array();
                $select_option = true;
                foreach ($configitem['switch'] as $option => $case) {
                    $var_params[$option] = $case['desc'];
                    if ($option == $configitem['default']) {
                        $select_option = false;
                        if (!$wasset) {
                            $selected = $option;
                        }
                    }
                }
                $v = &$this->addVariable($configitem['desc'], $varname, 'enum', true, false, null, array($var_params, $select_option));
                if (array_key_exists('default', $configitem)) {
                    $v->setDefault($configitem['default']);
                }
                $v_action = &Horde_Form_Action::factory('reload');
                $v->setAction($v_action);
                if (isset($selected) && isset($configitem['switch'][$selected])) {
                    $this->_buildVariables($configitem['switch'][$selected]['fields'], $prefix);
                }
            } elseif (isset($configitem['_type'])) {
                $required = (isset($configitem['required'])) ? $configitem['required'] : true;
                $type = $configitem['_type'];
                if ($type == 'multienum' || $type == 'header' ||
                    $type == 'description') {
                    $required = false;
                }
                if ($type == 'multienum' || $type == 'enum') {
                    $var_params = array($configitem['values']);
                } else {
                    $var_params = array();
                }
                if ($type == 'php') {
                    $type = 'text';
                    $description = 'Enter a valid PHP expression.';
                }
                $v = &$this->addVariable($configitem['desc'], $varname, $type, $required, false, $description, $var_params);
                if (isset($configitem['default'])) {
                    $v->setDefault($configitem['default']);
                }
            } else {
                $this->_buildVariables($configitem, $prefixedname);
            }
        }
    }

}
