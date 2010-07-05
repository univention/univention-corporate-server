<?php
/**
 * The Horde_Form_Renderer class provides HTML and other renderings of
 * forms for the Horde_Form:: package.
 *
 * $Horde: framework/Form/Form/Renderer.php,v 1.185.4.22 2008-06-15 21:12:17 chuck Exp $
 *
 * Copyright 2001-2007 Robert E. Coyle <robertecoyle@hotmail.com>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Robert E. Coyle <robertecoyle@hotmail.com>
 * @package Horde_Form
 */
class Horde_Form_Renderer {

    var $_name;
    var $_requiredLegend = false;
    var $_requiredMarker = '*';
    var $_helpMarker = '?';
    var $_showHeader = true;
    var $_cols = 2;
    var $_varRenderer = null;
    var $_firstField = null;
    var $_stripedRows = true;

    /**
     * Does the title of the form contain HTML? If so, you are responsible for
     * doing any needed escaping/sanitization yourself. Otherwise the title
     * will be run through htmlspecialchars() before being output.
     *
     * @var boolean
     */
    var $_encodeTitle = true;

    /**
     * Width of the attributes column.
     *
     * @access private
     * @var string
     */
    var $_attrColumnWidth = '15%';

    /**
     * Construct a new Horde_Form_Renderer::.
     *
     * @param array $params  This is a hash of renderer-specific parameters.
     *                       Possible keys:<code>
     *                       'varrenderer_driver': specifies the driver
     *                           parameter to Horde_UI_VarRenderer::factory().
     *                       'encode_title': @see $_encodeTitle</code>
     */
    function Horde_Form_Renderer($params = array())
    {
        global $registry;
        if (isset($registry) && is_a($registry, 'Registry')) {
            /* Registry available, so use a pretty image. */
            $this->_requiredMarker = Horde::img('required.png', '*', '', $registry->getImageDir('horde'));
        } else {
            /* No registry available, use something plain. */
            $this->_requiredMarker = '*';
        }

        if (isset($params['encode_title'])) {
            $this->encodeTitle($params['encode_title']);
        }

        $driver = 'html';
        if (isset($params['varrenderer_driver'])) {
            $driver = $params['varrenderer_driver'];
        }
        require_once 'Horde/UI/VarRenderer.php';
        $this->_varRenderer = &Horde_UI_VarRenderer::factory($driver, $params);
    }

    function showHeader($bool)
    {
        $this->_showHeader = $bool;
    }

    /**
     * Sets or returns whether the form title should be encoded with
     * htmlspecialchars().
     *
     * @param boolean $encode  If true, the form title gets encoded.  If false
     *                         the title can contain HTML, but the class user
     *                         is responsible to encode any special characters.
     *
     * @return boolean  Whether the form title should be encoded.
     */
    function encodeTitle($encode = null)
    {
        if (!is_null($encode)) {
            $this->_encodeTitle = $encode;
        }
        return $this->_encodeTitle = $encode;
    }

    /**
     * @deprecated
     */
    function setAttrColumnWidth($width)
    {
    }

    function open($action, $method, $name, $enctype = null)
    {
        $this->_name = $name;
        $name = htmlspecialchars($name);
        $action = htmlspecialchars($action);
        $method = htmlspecialchars($method);
        echo "<form action=\"$action\" method=\"$method\"" . (empty($name) ? '' : " name=\"$name\" id=\"$name\"") . (is_null($enctype) ? '' : " enctype=\"$enctype\"") . ">\n";
        Util::pformInput();
    }

    function beginActive($name, $extra = null)
    {
        $this->_renderBeginActive($name, $extra);
    }

    function beginInactive($name, $extra = null)
    {
        $this->_renderBeginInactive($name, $extra);
    }

    function _renderSectionTabs(&$form)
    {
        /* If javascript is not available, do not render tabs. */
        if (!$GLOBALS['browser']->hasFeature('javascript')) {
            return;
        }

        $open_section = $form->getOpenSection();

        /* Add the javascript for the toggling the sections. */
        Horde::addScriptFile('form_sections.js', 'horde', true);
        echo '<script type="text/javascript">' . "\n";
        printf('var sections_%1$s = new Horde_Form_Sections(\'%1$s\', \'%2$s\');',
               $form->getName(),
               $open_section);
        echo "\n" . '</script>';

        /* Loop through the sections and print out a tab for each. */
        echo "<div class=\"tabset\"><ul>\n";
        foreach ($form->_sections as $section => $val) {
            $class = ($section == $open_section) ? ' class="activeTab"' : '';
            $js = sprintf('onclick="sections_%s.toggle(\'%s\'); return false;"',
                          $form->getName(),
                          $section);
            printf('<li%s id="%s"><a href="#" %s>%s%s</a> </li>' . "\n",
                   $class, htmlspecialchars($form->getName() . '_tab_' . $section), $js,
                   $form->getSectionImage($section),
                   $form->getSectionDesc($section));
        }
        echo "</ul></div><br class=\"clear\" />\n";
    }

    function _renderSectionBegin(&$form, $section)
    {
        // Stripe alternate rows if that option is turned on.
        if ($this->_stripedRows && class_exists('Horde')) {
            Horde::addScriptFile('stripe.js', 'horde', true);
            $class = ' class="striped"';
        } else {
            $class = '';
        }

        $open_section = $form->getOpenSection();
        if (empty($open_section)) {
            $open_section = '__base';
        }
        printf('<div id="%s" style="display:%s;"><table%s cellspacing="0">',
               htmlspecialchars($form->getName() . '_section_' . $section),
               ($open_section == $section ? 'block' : 'none'),
               $class);
    }

    function _renderSectionEnd()
    {
        echo '</table></div>';
    }

    function end()
    {
        $this->_renderEnd();
    }

    function close($focus = true)
    {
        echo "</form>\n";
        if ($focus && !empty($this->_firstField)) {
            echo '<script type="text/javascript">
<!--
try {
    document.getElementById("' . $this->_firstField . '").focus();
} catch(e) {}
//-->
</script>
';
        }
    }

    function listFormVars(&$form)
    {
        $variables = &$form->getVariables(true, true);
        $vars = array();
        if ($variables) {
            foreach ($variables as $var) {
                if (is_object($var)) {
                    if (!$var->isReadonly()) {
                        $vars[$var->getVarName()] = 1;
                    }
                } else {
                    $vars[$var] = 1;
                }
            }
        }
        require_once 'Horde/NLS.php';
        echo '<input type="hidden" name="_formvars" value="' . @htmlspecialchars(serialize($vars), ENT_QUOTES, NLS::getCharset()) . '" />';
    }

    function renderFormActive(&$form, &$vars)
    {
        $this->_renderForm($form, $vars, true);
    }

    function renderFormInactive(&$form, &$vars)
    {
        $this->_renderForm($form, $vars, false);
    }

    function _renderForm(&$form, &$vars, $active)
    {
        /* If help is present 3 columns are needed. */
        $this->_cols = $form->hasHelp() ? 3 : 2;

        $variables = &$form->getVariables(false);

        /* Check for a form token error. */
        if (($tokenError = $form->getError('_formToken')) !== null) {
            echo '<p class="form-error">' . htmlspecialchars($tokenError) . '</p>';
        }

        /* Check for a form secret error. */
        if (($secretError = $form->getError('_formSecret')) !== null) {
            echo '<p class="form-error">' . htmlspecialchars($secretError) . '</p>';
        }

        if (count($form->_sections)) {
            $this->_renderSectionTabs($form);
        }

        $error_section = null;
        foreach ($variables as $section_id => $section) {
            $this->_renderSectionBegin($form, $section_id);
            foreach ($section as $var) {
                $type = $var->getTypeName();

                switch ($type) {
                case 'header':
                    $this->_renderHeader($var->getHumanName(), $form->getError($var->getVarName()));
                    break;

                case 'description':
                    $this->_renderDescription($var->getHumanName());
                    break;

                case 'spacer':
                    $this->_renderSpacer();
                    break;

                default:
                    $isInput = ($active && !$var->isReadonly());
                    $format = $isInput ? 'Input' : 'Display';
                    $begin = "_renderVar${format}Begin";
                    $end = "_renderVar${format}End";

                    $this->$begin($form, $var, $vars);
                    echo $this->_varRenderer->render($form, $var, $vars, $isInput);
                    $this->$end($form, $var, $vars);

                    /* Print any javascript if actions present. */
                    if ($var->hasAction()) {
                        $var->_action->printJavaScript();
                    }

                    /* Keep first field. */
                    if ($active && empty($this->_firstField) && !$var->isReadonly() && !$var->isHidden()) {
                        $this->_firstField = $var->getVarName();
                    }

                    /* Keep section with first error. */
                    if (is_null($error_section) && $form->getError($var)) {
                        $error_section = $section_id;
                    }
                }
            }

            $this->_renderSectionEnd();
        }

        if (!is_null($error_section) && $form->_sections) {
            echo '<script type="text/javascript">' .
                "\n" . sprintf('sections_%s.toggle(\'%s\');',
                               $form->getName(),
                               $error_section) .
                "\n</script>";
        }
    }

    function submit($submit = null, $reset = false)
    {
        if (is_null($submit) || empty($submit)) {
            $submit = _("Submit");
        }
        if ($reset === true) {
            $reset = _("Reset");
        }
        $this->_renderSubmit($submit, $reset);
    }

    /**
     * Implementation specific begin function.
     */
    function _renderBeginActive($name, $extra)
    {
        echo '<div class="form" id="' . htmlspecialchars($this->_name) . '_active">';
        if ($this->_showHeader) {
            $this->_sectionHeader($name, $extra);
        }
        if ($this->_requiredLegend) {
            echo '<span class="form-error">' . $this->_requiredMarker . '</span> = ' . _("Required Field");
        }
    }

    /**
     * Implementation specific begin function.
     */
    function _renderBeginInactive($name, $extra)
    {
        echo '<div class="form" id="' . htmlspecialchars($this->_name) . '_inactive">';
        if ($this->_showHeader) {
            $this->_sectionHeader($name, $extra);
        }
    }

    /**
     * Implementation specific end function.
     */
    function _renderEnd()
    {
        echo '</div>' . $this->_varRenderer->renderEnd();
    }

    function _renderHeader($header, $error = '')
    {
?><tr><td class="control" width="100%" colspan="<?php echo $this->_cols ?>" valign="bottom"><strong><?php echo $header ?></strong><?php
        if (!empty($error)) {
?><br /><span class="form-error"><?php echo $error ?></span><?php
        }
?></td></tr>
<?php
    }

    function _renderDescription($text)
    {
?><tr><td width="100%" colspan="<?php echo $this->_cols ?>"><p style="padding:8px"><?php echo $text ?></p></td></tr>
<?php
    }

    function _renderSpacer()
    {
?><tr><td colspan="<?php echo $this->_cols ?>">&nbsp;</td></tr>
<?php
    }

    function _renderSubmit($submit, $reset)
    {
?><div class="control">
  <?php if (!is_array($submit)) $submit = array($submit); foreach ($submit as $submitbutton): ?>
    <input class="button" name="submitbutton" type="submit" value="<?php echo $submitbutton ?>" />
  <?php endforeach; ?>
  <?php if (!empty($reset)): ?>
    <input class="button" name="resetbutton" type="reset" value="<?php echo $reset ?>" />
  <?php endif; ?>
</div>
<?php
    }

    // Implementation specifics -- input variables.
    function _renderVarInputBegin(&$form, &$var, &$vars)
    {
        $message = $form->getError($var);
        $isvalid = empty($message);
        echo "<tr valign=\"top\">\n";
        printf('  <td%s align="right">%s%s%s%s</td>' . "\n",
               empty($this->_attrColumnWidth) ? '' : ' width="' . $this->_attrColumnWidth . '"',
               $isvalid ? '' : '<span class="form-error">',
               $var->isRequired() ? '<span class="form-error">' . $this->_requiredMarker . '</span>&nbsp;' : '',
               $var->getHumanName(),
               $isvalid ? '' : '<br />' . $message . '</span>');
        printf('  <td%s%s>',
               ((!$var->hasHelp() && $form->hasHelp()) ? ' colspan="2"' : ''),
               ($var->isDisabled() ? ' class="form-disabled"' : ''));
    }

    function _renderVarInputEnd(&$form, &$var, &$vars)
    {
        /* Display any description for the field. */
        if ($var->hasDescription()) {
            echo '<br />' . $var->getDescription();
        }

        /* Display any help for the field. */
        if ($var->hasHelp()) {
            global $registry;
            if (isset($registry) && is_a($registry, 'Registry')) {
                $link = Help::link($GLOBALS['registry']->getApp(), $var->getHelp());
            } else {
                $link = '<a href="#" onclick="alert(\'' . addslashes(@htmlspecialchars($var->getHelp())) . '\');return false;">' . $this->_helpMarker . '</a>';
            }
            echo "</td>\n  <td style=\"text-align:right\">$link&nbsp;";
        }

        echo "</td>\n</tr>\n";
    }

    // Implementation specifics -- display variables.
    function _renderVarDisplayBegin(&$form, &$var, &$vars)
    {
        $message = $form->getError($var);
        $isvalid = empty($message);
        echo "<tr valign=\"top\">\n";
        printf('  <td%s align="right">%s<strong>%s</strong>%s</td>' . "\n",
               empty($this->_attrColumnWidth) ? '' : ' width="' . $this->_attrColumnWidth . '"',
               $isvalid ? '' : '<span class="form-error">',
               $var->getHumanName(),
               $isvalid ? '' : '<br />' . $message . '</span>');
        echo '  <td>';
    }

    function _renderVarDisplayEnd(&$form, &$var, &$vars)
    {
        if ($var->hasHelp()) {
            echo '</td><td>&nbsp;';
        }
        echo "</td>\n</tr>\n";
    }

    function _sectionHeader($title, $extra = '')
    {
        if (strlen($title)) {
            echo '<div class="header">';
            if (!empty($extra)) {
                echo '<span class="rightFloat">' . $extra . '</span>';
            }
            echo $this->_encodeTitle ? htmlspecialchars($title) : $title;
            echo '</div>';
        }
    }

    /**
     * Attempts to return a concrete Horde_Form_Renderer instance based on
     * $renderer.
     *
     * @param mixed $renderer  The type of concrete Horde_Form_Renderer
     *                         subclass to return. The code is dynamically
     *                         included. If $renderer is an array, then we will
     *                         look in $renderer[0]/lib/Form/Renderer/ for the
     *                         subclass implementation named $renderer[1].php.
     * @param array $params    A hash containing any additional configuration a
     *                         form might need.
     *
     * @return Horde_Form_Renderer  The concrete Horde_Form_Renderer reference,
     *                              or false on an error.
     */
    function factory($renderer = '', $params = null)
    {
        if (is_array($renderer)) {
            $app = $renderer[0];
            $renderer = $renderer[1];
        }

        /* Return a base Horde_Form_Renderer object if no driver is
         * specified. */
        $renderer = basename($renderer);
        if (!empty($renderer) && $renderer != 'none') {
            $class = 'Horde_Form_Renderer_' . $renderer;
        } else {
            $class = 'Horde_Form_Renderer';
        }

        if (!class_exists($class)) {
            if (!empty($app)) {
                include_once $GLOBALS['registry']->get('fileroot', $app) . '/lib/Form/Renderer/' . $renderer . '.php';
            } else {
                include_once 'Horde/Form/Renderer/' . $renderer . '.php';
            }
        }

        if (class_exists($class)) {
            return new $class($params);
        } else {
            return PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }
    }

    /**
     * Attempts to return a reference to a concrete Horde_Form_Renderer
     * instance based on $renderer. It will only create a new instance if no
     * Horde_Form_Renderer instance with the same parameters currently exists.
     *
     * This should be used if multiple types of form renderers (and,
     * thus, multiple Horde_Form_Renderer instances) are required.
     *
     * This method must be invoked as: $var = &Horde_Form_Renderer::singleton()
     *
     * @param mixed $renderer  The type of concrete Horde_Form_Renderer
     *                         subclass to return. The code is dynamically
     *                         included. If $renderer is an array, then we will
     *                         look in $renderer[0]/lib/Form/Renderer/ for the
     *                         subclass implementation named $renderer[1].php.
     * @param array $params  A hash containing any additional configuration a
     *                       form might need.
     *
     * @return Horde_Form_Renderer  The concrete Horde_Form_Renderer reference,
     *                              or false on an error.
     */
    function &singleton($renderer, $params = null)
    {
        static $instances = array();

        $signature = serialize(array($renderer, $params));
        if (!isset($instances[$signature])) {
            $instances[$signature] = Horde_Form_Renderer::factory($renderer, $params);
        }

        return $instances[$signature];
    }

}
