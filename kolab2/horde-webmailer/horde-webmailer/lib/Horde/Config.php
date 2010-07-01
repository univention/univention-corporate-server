<?php
/**
 * @package Horde_Framework
 */

/**
 * Horde_DOM
 */
include_once 'Horde/DOM.php';

/**
 * Horde_Form
 */
include_once 'Horde/Form.php';

/**
 * Horde_Form_Renderer
 */
include_once 'Horde/Form/Renderer.php';

/**
 * The Config:: package provides a framework for managing the
 * configuration of Horde applications, writing conf.php files from
 * conf.xml source files, generating user interfaces, etc.
 *
 * $Horde: framework/Horde/Horde/Config.php,v 1.80.2.40 2009-02-25 05:35:42 chuck Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Horde 3.0
 * @package Horde_Framework
 */
class Horde_Config {

    /**
     * The name of the configured application.
     *
     * @var string
     */
    var $_app;

    /**
     * The XML tree of the configuration file traversed to an
     * associative array.
     *
     * @var array
     */
    var $_xmlConfigTree = null;

    /**
     * The content of the generated configuration file.
     *
     * @var string
     */
    var $_phpConfig;

    /**
     * The content of the old configuration file.
     *
     * @var string
     */
    var $_oldConfig;

    /**
     * The manual configuration in front of the generated configuration.
     *
     * @var string
     */
    var $_preConfig;

    /**
     * The manual configuration after the generated configuration.
     *
     * @var string
     */
    var $_postConfig;

    /**
     * The current $conf array of the configured application.
     *
     * @var array
     */
    var $_currentConfig = array();

    /**
     * The CVS version tag of the conf.xml file which will be copied into the
     * conf.php file.
     *
     * @var string
     */
    var $_versionTag = '';

    /**
     * The line marking the begin of the generated configuration.
     *
     * @var string
     */
    var $_configBegin = "/* CONFIG START. DO NOT CHANGE ANYTHING IN OR AFTER THIS LINE. */\n";

    /**
     * The line marking the end of the generated configuration.
     *
     * @var string
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
     * Reads the application's conf.xml file and builds an associative array
     * from its XML tree.
     *
     * @param array $custom_conf   Any settings that shall be included in the
     *                             generated configuration.
     *
     * @return array  An associative array representing the configuration tree.
     */
    function readXMLConfig($custom_conf = null)
    {
        if (is_null($this->_xmlConfigTree) || $custom_conf) {
            require_once 'Horde/Text.php';

            global $registry;
            $path = $registry->get('fileroot', $this->_app) . '/config';

            if ($custom_conf) {
                $this->_currentConfig = $custom_conf;
            } else {
                /* Fetch the current conf.php contents. */
                @eval($this->getPHPConfig());
                if (isset($conf)) {
                    $this->_currentConfig = $conf;
                }
            }

            /* Load the DOM object. */
            $doc = Horde_DOM_Document::factory(array('filename' => $path . '/conf.xml'));

            /* Check if there is a CVS version tag and store it. */
            $node = $doc->first_child();
            while (!empty($node)) {
                if ($node->type == XML_COMMENT_NODE) {
                    if (preg_match('/\$.*?conf\.xml,v .*? .*\$/', $node->node_value(), $match)) {
                        $this->_versionTag = $match[0] . "\n";
                        break;
                    }
                }
                $node = $node->next_sibling();
            }

            /* Parse the config file. */
            $this->_xmlConfigTree = array();
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
            $path = $registry->get('fileroot', $this->_app) . '/config';
            if (file_exists($path . '/conf.php')) {
                $this->_oldConfig = file_get_contents($path . '/conf.php');
                if (!empty($this->_oldConfig)) {
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
     * @param array $custom_conf   Any settings that shall be included in the
     *                             generated configuration.
     *
     * @return string  The content of the generated configuration file.
     */
    function generatePHPConfig($formvars, $custom_conf = null)
    {
        $this->readXMLConfig($custom_conf);
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
        if (!is_array($section)) {
            return;
        }

        foreach ($section as $name => $configitem) {
            $prefixedname = empty($prefix) ? $name : $prefix . '|' . $name;
            $configname = str_replace('|', '__', $prefixedname);
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
                    if ($val !== '') {
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
                $this->_phpConfig .= '$conf[\'' . str_replace('__', '\'][\'', $configname) . '\'] = ' . $value . ";\n";
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
        require_once 'Horde/Text/Filter.php';

        foreach ($children as $node) {
            if ($node->type != XML_ELEMENT_NODE) {
                continue;
            }
            $name = $node->get_attribute('name');
            $desc = Text_Filter::filter($node->get_attribute('desc'), 'linkurls', array('callback' => 'Horde::externalUrl'));
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
                    $name = md5(uniqid(mt_rand(), true));
                }
                $conf[$name] = array('_type' => 'description',
                                     'desc' => Text_Filter::filter($this->_default($curctx, $this->_getNodeOnlyText($node)), 'linkurls', array('callback' => 'Horde::externalUrl')));
                break;

            case 'configheader':
                if (empty($name)) {
                    $name = md5(uniqid(mt_rand(), true));
                }
                $conf[$name] = array('_type' => 'header',
                                     'desc' => $this->_default($curctx, $this->_getNodeOnlyText($node)));
                break;

            case 'configswitch':
                $values = $this->_getSwitchValues($node, $ctx);
                if ($quote) {
                    list($default, $isDefault) = $this->__default($curctx, $this->_getNodeOnlyText($node));
                } else {
                    list($default, $isDefault) = $this->__defaultRaw($curctx, $this->_getNodeOnlyText($node));
                }
                if ($default === '') {
                    $default = key($values);
                }
                if (is_bool($default)) {
                    $default = $default ? 'true' : 'false';
                }
                $conf[$name] = array('desc' => $desc,
                                     'switch' => $values,
                                     'default' => $default,
                                     'is_default' => $isDefault);
                break;

            case 'configenum':
                $values = $this->_getEnumValues($node);
                if ($quote) {
                    list($default, $isDefault) = $this->__default($curctx, $this->_getNodeOnlyText($node));
                } else {
                    list($default, $isDefault) = $this->__defaultRaw($curctx, $this->_getNodeOnlyText($node));
                }
                if ($default === '') {
                    $default = key($values);
                }
                if (is_bool($default)) {
                    $default = $default ? 'true' : 'false';
                }
                $conf[$name] = array('_type' => 'enum',
                                     'required' => $required,
                                     'quote' => $quote,
                                     'values' => $values,
                                     'desc' => $desc,
                                     'default' => $default,
                                     'is_default' => $isDefault);
                break;

            case 'configlist':
                list($default, $isDefault) = $this->__default($curctx, null);
                if ($default === null) {
                    $default = $this->_getNodeOnlyText($node);
                } elseif (is_array($default)) {
                    $default = implode(', ', $default);
                }
                $conf[$name] = array('_type' => 'stringlist',
                                     'required' => $required,
                                     'desc' => $desc,
                                     'default' => $default,
                                     'is_default' => $isDefault);
                break;

            case 'configmultienum':
                $values = $this->_getEnumValues($node);
                require_once 'Horde/Array.php';
                list($default, $isDefault) = $this->__default($curctx, explode(',', $this->_getNodeOnlyText($node)));
                $conf[$name] = array('_type' => 'multienum',
                                     'required' => $required,
                                     'values' => $values,
                                     'desc' => $desc,
                                     'default' => Horde_Array::valuesToKeys($default),
                                     'is_default' => $isDefault);
                break;

            case 'configpassword':
                $conf[$name] = array('_type' => 'password',
                                     'required' => $required,
                                     'desc' => $desc,
                                     'default' => $this->_default($curctx, $this->_getNodeOnlyText($node)),
                                     'is_default' => $this->_isDefault($curctx, $this->_getNodeOnlyText($node)));
                break;

            case 'configstring':
                $conf[$name] = array('_type' => 'text',
                                     'required' => $required,
                                     'desc' => $desc,
                                     'default' => $this->_default($curctx, $this->_getNodeOnlyText($node)),
                                     'is_default' => $this->_isDefault($curctx, $this->_getNodeOnlyText($node)));
                if ($conf[$name]['default'] === false) {
                    $conf[$name]['default'] = 'false';
                } elseif ($conf[$name]['default'] === true) {
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
                                     'default' => $this->_default($curctx, $default),
                                     'is_default' => $this->_isDefault($curctx, $default));
                break;

            case 'configinteger':
                $values = $this->_getEnumValues($node);
                $conf[$name] = array('_type' => 'int',
                                     'required' => $required,
                                     'values' => $values,
                                     'desc' => $desc,
                                     'default' => $this->_default($curctx, $this->_getNodeOnlyText($node)),
                                     'is_default' => $this->_isDefault($curctx, $this->_getNodeOnlyText($node)));
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
                                     'default' => $this->_defaultRaw($curctx, $this->_getNodeOnlyText($node)),
                                     'is_default' => $this->_isDefaultRaw($curctx, $this->_getNodeOnlyText($node)));
                break;

            case 'configsecret':
                $conf[$name] = array('_type' => 'text',
                                     'required' => true,
                                     'desc' => $desc,
                                     'default' => $this->_default($curctx, sha1(uniqid(mt_rand(), true))),
                                     'is_default' => $this->_isDefault($curctx, $this->_getNodeOnlyText($node)));
                break;

            case 'configsql':
                $conf[$node->get_attribute('switchname')] = $this->_configSQL($ctx, $node);
                break;

            case 'configvfs':
                $conf[$node->get_attribute('switchname')] = $this->_configVFS($ctx, $node);
                break;

            case 'configsection':
                $conf[$name] = array();
                $cur = &$conf[$name];
                if ($node->has_child_nodes()) {
                    $this->_parseLevel($cur, $node->child_nodes(), $curctx);
                }
                break;

            case 'configtab':
                $key = md5(uniqid(mt_rand(), true));
                $conf[$key] = array('tab' => $name,
                                    'desc' => $desc);
                if ($node->has_child_nodes()) {
                    $this->_parseLevel($conf, $node->child_nodes(), $ctx);
                }
                break;

            case 'configplaceholder':
                $conf[md5(uniqid(mt_rand(), true))] = 'placeholder';
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
     * Returns the configuration tree for an SQL backend configuration to
     * replace a <configsql> tag.
     * Subnodes will be parsed and added to both the Horde defaults and the
     * Custom configuration parts.
     *
     * @access private
     *
     * @param string $ctx         The context of the <configsql> tag.
     * @param DomNode $node       The DomNode representation of the <configsql>
     *                            tag.
     * @param string $switchname  If DomNode is not set, the value of the
     *                            tag's switchname attribute.
     *
     * @return array  An associative array with the SQL configuration tree.
     */
    function _configSQL($ctx, $node = null, $switchname = 'driverconfig')
    {
        $persistent = array(
            '_type' => 'boolean',
            'required' => false,
            'desc' => 'Request persistent connections?',
            'default' => $this->_default($ctx . '|persistent', false));
        $hostspec = array(
            '_type' => 'text',
            'required' => true,
            'desc' => 'Database server/host',
            'default' => $this->_default($ctx . '|hostspec', ''));
        $username = array(
            '_type' => 'text',
            'required' => true,
            'desc' => 'Username to connect to the database as',
            'default' => $this->_default($ctx . '|username', ''));
        $password = array(
            '_type' => 'text',
            'required' => false,
            'desc' => 'Password to connect with',
            'default' => $this->_default($ctx . '|password', ''));
        $database = array(
            '_type' => 'text',
            'required' => true,
            'desc' => 'Database name to use',
            'default' => $this->_default($ctx . '|database', ''));
        $socket = array(
            '_type' => 'text',
            'required' => false,
            'desc' => 'Location of UNIX socket',
            'default' => $this->_default($ctx . '|socket', ''));
        $port = array(
            '_type' => 'int',
            'required' => false,
            'desc' => 'Port the DB is running on, if non-standard',
            'default' => $this->_default($ctx . '|port', null));
        $protocol = array(
            'desc' => 'How should we connect to the database?',
            'default' => $this->_default($ctx . '|protocol', 'unix'),
            'switch' => array(
                'unix' => array(
                    'desc' => 'UNIX Sockets',
                    'fields' => array(
                        'socket' => $socket)),
                'tcp' => array(
                    'desc' => 'TCP/IP',
                    'fields' => array(
                        'hostspec' => $hostspec,
                        'port' => $port))));
        $mysql_protocol = $protocol;
        $mysql_protocol['switch']['tcp']['fields']['port']['default'] = $this->_default($ctx . '|port', 3306);
        $charset = array(
            '_type' => 'text',
            'required' => true,
            'desc' => 'Internally used charset',
            'default' => $this->_default($ctx . '|charset', 'utf-8'));
        $ssl = array(
            '_type' => 'boolean',
            'required' => false,
            'desc' => 'Use SSL to connect to the server?',
            'default' => $this->_default($ctx . '|ssl', false));
        $ca = array(
            '_type' => 'text',
            'required' => false,
            'desc' => 'Certification Authority to use for SSL connections',
            'default' => $this->_default($ctx . '|ca', ''));
        $oci8_fields = array(
            'persistent' => $persistent,
            'username' => $username,
            'password' => $password);
        if (function_exists('oci_connect')) {
            $oci8_fields['database'] = array(
                '_type' => 'text',
                'required' => true,
                'desc' => 'Database name or Easy Connect parameter',
                'default' => $this->_default($ctx . '|database', 'horde'));
        } else {
            $oci8_fields['hostspec'] = array(
                '_type' => 'text',
                'required' => true,
                'desc' => 'Database name or Easy Connect parameter',
                'default' => $this->_default($ctx . '|hostspec', 'horde'));
        }
        $oci8_fields['charset'] = $charset;

        $read_hostspec = array(
            '_type' => 'text',
            'required' => true,
            'desc' => 'Read database server/host',
            'default' => $this->_default($ctx . '|read|hostspec', ''));
        $read_port = array(
            '_type' => 'int',
            'required' => false,
            'desc' => 'Port the read DB is running on, if non-standard',
            'default' => $this->_default($ctx . '|read|port', null));
        $splitread = array(
            '_type' => 'boolean',
            'required' => false,
            'desc' => 'Split reads to a different server?',
            'default' => $this->_default($ctx . '|splitread', 'false'),
            'switch' => array(
                'false' => array(
                    'desc' => 'Disabled',
                    'fields' => array()),
                'true' => array(
                    'desc' => 'Enabled',
                    'fields' => array(
                        'read' => array(
                            'persistent' => $persistent,
                            'username' => $username,
                            'password' => $password,
                            'protocol' => $mysql_protocol,
                            'database' => $database,
                            'charset' => $charset)))));

        $custom_fields = array(
            'required' => true,
            'desc' => 'What database backend should we use?',
            'default' => $this->_default($ctx . '|phptype', 'false'),
            'switch' => array(
                'false' => array(
                    'desc' => '[None]',
                    'fields' => array()),
                'dbase' => array(
                    'desc' => 'dBase',
                    'fields' => array(
                        'database' => array(
                            '_type' => 'text',
                            'required' => true,
                            'desc' => 'Absolute path to the database file',
                            'default' => $this->_default($ctx . '|database', '')),
                        'mode' => array(
                            '_type' => 'enum',
                            'desc' => 'The mode to open the file with',
                            'values' => array(
                                0 => 'Read Only',
                                2 => 'Read Write'),
                            'default' => $this->_default($ctx . '|mode', 2)),

                        'charset' => $charset)),
                'ibase' => array(
                    'desc' => 'Firebird/InterBase',
                    'fields' => array(
                        'dbsyntax' => array(
                            '_type' => 'enum',
                            'desc' => 'The database syntax variant to use',
                            'required' => false,
                            'values' => array(
                                'ibase' => 'InterBase',
                                'firebird' => 'Firebird'),
                            'default' => $this->_default($ctx . '|dbsyntax', 'firebird')),
                        'persistent' => $persistent,
                        'hostspec' => $hostspec,
                        'username' => $username,
                        'password' => $password,
                        'database' => $database,
                        'buffers' => array(
                            '_type' => 'int',
                            'desc' => 'The number of database buffers to allocate',
                            'required' => false,
                            'default' => $this->_default($ctx . '|buffers', null)),
                        'dialect' => array(
                            '_type' => 'int',
                            'desc' => 'The default SQL dialect for any statement executed within a connection.',
                            'required' => false,
                            'default' => $this->_default($ctx . '|dialect', null)),
                        'role' => array(
                            '_type' => 'text',
                            'desc' => 'Role',
                            'required' => false,
                            'default' => $this->_default($ctx . '|role', null)),
                        'charset' => $charset)),
                'fbsql' => array(
                    'desc' => 'Frontbase',
                    'fields' => array(
                        'persistent' => $persistent,
                        'hostspec' => $hostspec,
                        'username' => $username,
                        'password' => $password,
                        'database' => $database,
                        'charset' => $charset)),
                'ifx' => array(
                    'desc' => 'Informix',
                    'fields' => array(
                        'persistent' => $persistent,
                        'username' => $username,
                        'password' => $password,
                        'database' => $database,
                        'charset' => $charset)),
                'msql' => array(
                    'desc' => 'mSQL',
                    'fields' => array(
                        'persistent' => $persistent,
                        'hostspec' => $hostspec,
                        'username' => $username,
                        'password' => $password,
                        'port' => $port,
                        'database' => $database,
                        'charset' => $charset)),
                'mssql' => array(
                    'desc' => 'MS SQL Server',
                    'fields' => array(
                        'persistent' => $persistent,
                        'hostspec' => $hostspec,
                        'username' => $username,
                        'password' => $password,
                        'port' => $port,
                        'database' => $database,
                        'charset' => $charset)),
                'mysql' => array(
                    'desc' => 'MySQL',
                    'fields' => array(
                        'persistent' => $persistent,
                        'username' => $username,
                        'password' => $password,
                        'protocol' => $mysql_protocol,
                        'database' => $database,
                        'charset' => $charset,
                        'ssl' => $ssl,
                        'ca' => $ca,
                        'splitread' => $splitread)),
                'mysqli' => array(
                    'desc' => 'MySQL (mysqli)',
                    'fields' => array(
                        'username' => $username,
                        'password' => $password,
                        'protocol' => $mysql_protocol,
                        'database' => $database,
                        'charset' => $charset,
                        'splitread' => $splitread,
                        'ssl' => $ssl,
                        'ca' => $ca
            )),
                'oci8' => array(
                    'desc' => 'Oracle',
                    'fields' => $oci8_fields),
                'odbc' => array(
                    'desc' => 'ODBC',
                    'fields' => array(
                        'persistent' => $persistent,
                        'username' => $username,
                        'password' => $password,
                        'hostspec' => array(
                            '_type' => 'text',
                            'desc' => 'DSN',
                            'default' => $this->_default($ctx . '|hostspec', '')),
                        'dbsyntax' => array(
                            '_type' => 'enum',
                            'desc' => 'The database syntax variant to use',
                            'required' => false,
                            'values' => array(
                                'sql92' => 'SQL92',
                                'access' => 'Access',
                                'db2' => 'DB2',
                                'solid' => 'Solid',
                                'navision' => 'Navision',
                                'mssql' => 'MS SQL Server',
                                'sybase' => 'Sybase',
                                'mysql' => 'MySQL',
                                'mysqli' => 'MySQL (mysqli)',
                                ),
                            'default' => $this->_default($ctx . '|dbsyntax', 'sql92')),
                        'cursor' => array(
                            '_type' => 'enum',
                            'desc' => 'Cursor type',
                            'quote' => false,
                            'required' => false,
                            'values' => array(
                                'null' => 'None',
                                'SQL_CUR_DEFAULT' => 'Default',
                                'SQL_CUR_USE_DRIVER' => 'Use Driver',
                                'SQL_CUR_USE_ODBC' => 'Use ODBC',
                                'SQL_CUR_USE_IF_NEEDED' => 'Use If Needed'),
                            'default' => $this->_default($ctx . '|cursor', null)),
                        'charset' => $charset)),
                'pgsql' => array(
                    'desc' => 'PostgreSQL',
                    'fields' => array(
                        'persistent' => $persistent,
                        'username' => $username,
                        'password' => $password,
                        'protocol' => $protocol,
                        'database' => $database,
                        'charset' => $charset)),
                'sqlite' => array(
                    'desc' => 'SQLite',
                    'fields' => array(
                        'database' => array(
                            '_type' => 'text',
                            'required' => true,
                            'desc' => 'Absolute path to the database file',
                            'default' => $this->_default($ctx . '|database', '')),
                        'mode' => array(
                            '_type' => 'text',
                            'desc' => 'The mode to open the file with',
                            'default' => $this->_default($ctx . '|mode', '0644')),
                        'charset' => $charset)),
                'sybase' => array(
                    'desc' => 'Sybase',
                    'fields' => array(
                        'persistent' => $persistent,
                        'hostspec' => $hostspec,
                        'username' => $username,
                        'password' => $password,
                        'database' => $database,
                        'appname' => array(
                            '_type' => 'text',
                            'desc' => 'Application Name',
                            'required' => false,
                            'default' => $this->_default($ctx . '|appname', '')),
                        'charset' => $charset))));

        if (isset($node) && $node->get_attribute('baseconfig') == 'true') {
            return $custom_fields;
        }

        list($default, $isDefault) = $this->__default($ctx . '|' . (isset($node) ? $node->get_attribute('switchname') : $switchname), 'horde');
        $config = array(
            'desc' => 'Driver configuration',
            'default' => $default,
            'is_default' => $isDefault,
            'switch' => array(
                'horde' => array(
                    'desc' => 'Horde defaults',
                    'fields' => array()),
                'custom' => array(
                    'desc' => 'Custom parameters',
                    'fields' => array(
                        'phptype' => $custom_fields))));

        if (isset($node) && $node->has_child_nodes()) {
            $cur = array();
            $this->_parseLevel($cur, $node->child_nodes(), $ctx);
            $config['switch']['horde']['fields'] = array_merge($config['switch']['horde']['fields'], $cur);
            $config['switch']['custom']['fields'] = array_merge($config['switch']['custom']['fields'], $cur);
        }

        return $config;
    }

    /**
     * Returns the configuration tree for a VFS backend configuration to
     * replace a <configvfs> tag.
     * Subnodes will be parsed and added to both the Horde defaults and the
     * Custom configuration parts.
     *
     * @access private
     *
     * @param string $ctx    The context of the <configvfs> tag.
     * @param DomNode $node  The DomNode representation of the <configvfs>
     *                       tag.
     *
     * @return array  An associative array with the VFS configuration tree.
     */
    function _configVFS($ctx, $node)
    {
        $sql = $this->_configSQL($ctx . '|params');
        $default = $node->get_attribute('default');
        $default = (empty($default)) ? 'none' : $default;
        list($default, $isDefault) = $this->__default($ctx . '|' . $node->get_attribute('switchname'), $default);
        $config =
            array(
                'desc' => 'What VFS driver should we use?',
                'default' => $default,
                'is_default' => $isDefault,
                'switch' => array(
                    'none' => array(
                        'desc' => 'None',
                        'fields' => array()),
                    'file' => array(
                        'desc' => 'Files on the local system',
                        'fields' => array(
                            'params' => array(
                                'vfsroot' => array(
                                    '_type' => 'text',
                                    'desc' => 'Where on the real filesystem should Horde use as root of the virtual filesystem?',
                                    'default' => $this->_default($ctx . '|params|vfsroot', '/tmp'))))),
                    'sql' => array(
                        'desc' => 'SQL database',
                        'fields' => array(
                            'params' => array(
                                'driverconfig' => $sql)))));

        if (isset($node) && $node->get_attribute('baseconfig') != 'true') {
            $config['switch']['horde'] = array(
                                          'desc' => 'Horde defaults',
                                          'fields' => array());
        }
        $cases = $this->_getSwitchValues($node, $ctx . '|params');
        foreach ($cases as $case => $fields) {
            if (isset($config['switch'][$case])) {
                $config['switch'][$case]['fields']['params'] = array_merge($config['switch'][$case]['fields']['params'], $fields['fields']);
            }
        }

        return $config;
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
        list ($ptr,) = $this->__default($ctx, $default);
        return $ptr;
    }

    /**
     * Returns whether a certain value from the current configuration array
     * exists or a default value will be used.
     *
     * @access private
     *
     * @param string $ctx     A string representing the key of the
     *                        configuration array to return.
     * @param mixed $default  The default value to return if the key wasn't
     *                        found.
     *
     * @return boolean  Whether the default value will be used.
     */
    function _isDefault($ctx, $default)
    {
        list (,$isDefault) = $this->__default($ctx, $default);
        return $isDefault;
    }

    /**
     * Returns a certain value from the current configuration array or a
     * default value, if not found, and which of the values have been
     * returned.
     *
     * @access private
     *
     * @param string $ctx     A string representing the key of the
     *                        configuration array to return.
     * @param mixed $default  The default value to return if the key wasn't
     *                        found.
     *
     * @return array  First element: either the value of the configuration
     *                array's requested key or the default value if the key
     *                wasn't found.
     *                Second element: whether the returned value was the
     *                default value.
     */
    function __default($ctx, $default)
    {
        $ctx = explode('|', $ctx);
        $ptr = $this->_currentConfig;
        for ($i = 0; $i < count($ctx); $i++) {
            if (!isset($ptr[$ctx[$i]])) {
                return array($default, true);
            } else {
                $ptr = $ptr[$ctx[$i]];
            }
        }
        if (is_string($ptr)) {
            $ptr = String::convertCharset($ptr, 'iso-8859-1');
        }

        return array($ptr, false);
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
        list ($ptr,) = $this->__defaultRaw($ctx, $default);
        return $ptr;
    }

    /**
     * Returns whether a certain value from the current configuration array
     * exists or a default value will be used.
     *
     * @access private
     *
     * @param string $ctx     A string representing the key of the
     *                        configuration array to return.
     * @param mixed $default  The default value to return if the key wasn't
     *                        found.
     *
     * @return boolean  Whether the default value will be used.
     */
    function _isDefaultRaw($ctx, $default)
    {
        list (,$isDefault) = $this->__defaultRaw($ctx, $default);
        return $isDefault;
    }

    /**
     * Returns a certain value from the current configuration file or
     * a default value, if not found, and which of the values have been
     * returned.
     *
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
     * @return array  First element: either the value of the configuration
     *                array's requested key or the default value if the key
     *                wasn't found.
     *                Second element: whether the returned value was the
     *                default value.
     */
    function __defaultRaw($ctx, $default)
    {
        $ctx = explode('|', $ctx);
        $pattern = '/^\$conf\[\'' . implode("'\]\['", $ctx) . '\'\] = (.*);\r?$/m';
        if (preg_match($pattern, $this->getPHPConfig(), $matches)) {
            return array($matches[1], false);
        }
        return array($default, true);
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
        foreach ($node->child_nodes() as $tnode) {
            if ($tnode->type == XML_TEXT_NODE) {
                $text .= $tnode->content;
            }
        }

        return trim($text);
    }

    /**
     * Returns an associative array containing all possible values of the
     * specified <configenum> tag.
     *
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
        foreach ($node->child_nodes() as $vnode) {
            if ($vnode->type == XML_ELEMENT_NODE &&
                $vnode->tagname == 'values') {
                if (!$vnode->has_child_nodes()) {
                    return array();
                }
                foreach ($vnode->child_nodes() as $value) {
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
        foreach ($node->child_nodes() as $case) {
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
            return array_map(create_function('$val', 'return preg_replace(array("/&#x([0-9a-f]{4});/ie", "/(&[^;]+;)/e"), array("String::convertCharset(pack(\"H*\", \"$1\"), \"ucs-2\", \"' . NLS::getCharset() . '\")", "String::convertCharset(html_entity_decode(\"$1\", ENT_COMPAT, \"iso-8859-1\"), \"iso-8859-1\", \"' . NLS::getCharset() . '\")"), $val);'), $GLOBALS['nls']['languages']);
            break;

        case 'list-blocks':
            require_once 'Horde/Block/Collection.php';
            $collection = &Horde_Block_Collection::singleton('portal');
            return $collection->getBlocksList();

        case 'list-client-fields':
            global $registry;
            $f = array();
            if ($registry->hasMethod('clients/getClientSource')) {
                $addressbook = $registry->call('clients/getClientSource');
                $fields = $registry->call('clients/clientFields', array($addressbook));
                if (is_a($fields, 'PEAR_Error')) {
                    $fields = $registry->call('clients/fields', array($addressbook));
                }
                if (!is_a($fields, 'PEAR_Error')) {
                    foreach ($fields as $field) {
                        $f[$field['name']] = $field['label'];
                    }
                }
            }
            return $f;
            break;

        case 'list-contact-sources':
            global $registry;
            $res = $registry->call('contacts/sources');
            return $res;
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
 * @since   Horde 3.0
 * @package Horde_Framework
 */
class ConfigForm extends Horde_Form {

    /**
     * Don't use form tokens for the configuration form - while
     * generating configuration info, things like the Token system
     * might not work correctly. This saves some headaches.
     *
     * @var boolean
     */
    var $_useFormToken = false;

    /**
     * Contains the Horde_Config object that this form represents.
     *
     * @var Horde_Config
     */
    var $_xmlConfig;

    /**
     * Contains the Variables object of this form.
     *
     * @var Variables
     */
    var $_vars;

    /**
     * Constructor.
     *
     * @param Variables &$vars  The Variables object of this form.
     * @param string $app       The name of the application that this
     *                          configuration form is for.
     */
    function ConfigForm(&$vars, $app)
    {
        parent::Horde_Form($vars);

        $this->_xmlConfig = new Horde_Config($app);
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
            $varname = str_replace('|', '__', $prefixedname);
            if ($configitem == 'placeholder') {
                continue;
            } elseif (isset($configitem['tab'])) {
                $this->setSection($configitem['tab'], $configitem['desc']);
            } elseif (isset($configitem['switch'])) {
                $selected = $this->_vars->getExists($varname, $wasset);
                $var_params = array();
                $select_option = true;
                if (is_bool($configitem['default'])) {
                    $configitem['default'] = $configitem['default'] ? 'true' : 'false';
                }
                foreach ($configitem['switch'] as $option => $case) {
                    $var_params[$option] = $case['desc'];
                    if ($option == $configitem['default']) {
                        $select_option = false;
                        if (!$wasset) {
                            $selected = $option;
                        }
                    }
                }

                $name = '$conf[' . implode('][', explode('|', $prefixedname)) . ']';
                $desc = $configitem['desc'];

                $v = &$this->addVariable($name, $varname, 'enum', true, false, $desc, array($var_params, $select_option));
                if (array_key_exists('default', $configitem)) {
                    $v->setDefault($configitem['default']);
                }
                if (!empty($configitem['is_default'])) {
                    $v->_new = true;
                }
                $v_action = &Horde_Form_Action::factory('reload');
                $v->setAction($v_action);
                if (isset($selected) && isset($configitem['switch'][$selected])) {
                    $this->_buildVariables($configitem['switch'][$selected]['fields'], $prefix);
                }
            } elseif (isset($configitem['_type'])) {
                $required = (isset($configitem['required'])) ? $configitem['required'] : true;
                $type = $configitem['_type'];

                // FIXME: multienum fields can well be required, meaning that
                // you need to select at least one entry. Changing this before
                // Horde 4.0 would break a lot of configuration files though.
                if ($type == 'multienum' || $type == 'header' ||
                    $type == 'description') {
                    $required = false;
                }

                if ($type == 'multienum' || $type == 'enum') {
                    $var_params = array($configitem['values']);
                } else {
                    $var_params = array();
                }

                if ($type == 'header' || $type == 'description') {
                    $name = $configitem['desc'];
                    $desc = null;
                } else {
                    $name = '$conf[' . implode('][', explode('|', $prefixedname)) . ']';
                    $desc = $configitem['desc'];
                    if ($type == 'php') {
                        $type = 'text';
                        $desc .= "\nEnter a valid PHP expression.";
                    }
                }

                $v = &$this->addVariable($name, $varname, $type, $required, false, $desc, $var_params);
                if (isset($configitem['default'])) {
                    $v->setDefault($configitem['default']);
                }
                if (!empty($configitem['is_default'])) {
                    $v->_new = true;
                }
            } else {
                $this->_buildVariables($configitem, $prefixedname);
            }
        }
    }

}
