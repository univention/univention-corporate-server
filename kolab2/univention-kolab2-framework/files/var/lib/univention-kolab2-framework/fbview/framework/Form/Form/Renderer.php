<?php
/**
 * The Horde_Form_Renderer class provides HTML and other renderings of
 * forms for the Horde_Form:: package.
 *
 * $Horde: framework/Form/Form/Renderer.php,v 1.158 2004/04/28 13:22:15 mdjukic Exp $
 *
 * Copyright 2001-2004 Robert E. Coyle <robertecoyle@hotmail.com>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Robert E. Coyle <robertecoyle@hotmail.com>
 * @version $Revision: 1.1.2.1 $
 * @package Horde_Form
 */
class Horde_Form_Renderer {

    var $_name;
    var $_requiredLegend = false;
    var $_requiredMarker = '*';
    var $_onLoadJS = array();
    var $_showHeader = true;
    var $_cols = 2;
    var $_varRenderer = null;

    /**
     * Width of the attributes column.
     *
     * @access private
     * @var string $_attrColumnWidth
     */
    var $_attrColumnWidth = '15%';

    /**
     * Construct a new Horde_Form_Renderer::.
     *
     * @param optional array $params    This is a hash of renderer-specific
     *                                  parameters.  We currently only accept
     *                                  the 'varrenderer_driver' key, which
     *                                  specifies the driver parameter to
     *                                  Horde_UI_VarRenderer::factory().
     */
    function Horde_Form_Renderer($params = array())
    {
        $this->_requiredMarker = Horde::img('required.gif', '*', '', $GLOBALS['registry']->getParam('graphics', 'horde'));

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
     * Specify the width of the attribute column in the rendered form.
     *
     * @param string $width  The width of the attribute column.
     *
     * @return void
     */
    function setAttrColumnWidth($width)
    {
        $this->_attrColumnWidth = $width;
    }

    function open($action, $method, $name, $enctype = null)
    {
        $this->_name = $name;
        echo "<form action=\"$action\" method=\"$method\"" . (empty($name) ? '' : " name=\"$name\"") . (is_null($enctype) ? '' : " enctype=\"$enctype\"") . ">\n";
        Util::pformInput();
    }

    function beginActive($name)
    {
        $this->_renderBeginActive($name);
    }

    function beginInactive($name)
    {
        $this->_renderBeginInactive($name);
    }

    function _renderSectionTabs(&$form)
    {
        /* If javascript is not available, do not render tabs. */
        if (!$GLOBALS['browser']->hasFeature('javascript')) {
            return;
        }

        $open_section = $form->getOpenSection();

        /* Add the javascript for the toggling the sections. */
        Horde::addScriptFile('form_sections.js', 'horde');
        $js  = '<script language="JavaScript" type="text/javascript">' . "\n";
        $js .= sprintf('sections_%1$s = new Horde_Form_Sections(\'%1$s\', \'%2$s\');' . "\n",
                       $form->getName(),
                       $open_section);
        $js .= "\n" . '</script>';

        echo $js;

        /* Print out the tabs for all the sections. */
        printf('<tr><td>&nbsp;</td></tr><tr valign="bottom"><td colspan="%s">', $this->_cols);
        echo '<table width="100%" border="0" cellpadding="1" cellspacing="0" class="tabset"><tr>';

        $tabs_in_row = 0;
        /* Loop through the sections and print out a tab for each. */
        foreach ($form->_sections as $section => $val) {
            $class = ($section == $open_section) ? 'tab-hi' : 'tab';
            $js = sprintf('onclick="sections_%s.toggle(\'%s\'); return false;"',
                          $form->getName(),
                          $section);
            printf('<td style="padding-left:10px;">&nbsp;</td><td id="_tab_' . $section . '" align="center" class="' . $class . '" ' . $js . '><a id="_tabLink_' . $section . '" class="' . $class . '" href="" %s><b>%s</b></a></td><td width="3">&nbsp;</td>',
                   $js, $form->getSectionDesc($section));
            $tabs_in_row++;
            if ($tabs_in_row > 5) {
                echo '<td style="padding-left:10px;">&nbsp;</td></tr></table><table width="100%" border="0" cellpadding="1" cellspacing="0" class="tabset"><tr>';
                $tabs_in_row = 0;
            }
        }

        echo '<td style="padding-left:10px;">&nbsp;</td></tr></table></td></tr>';
    }

    function _renderSectionBegin(&$form, $section)
    {
        static $first_section = '';
        if (empty($first_section)) {
            /* If this is the first section being rendered, set it as
             * open and and render the section tabs. */
            $first_section = $section;
            $form->setOpenSection($section);
            $this->_renderSectionTabs($form);
        }

        $open_section = $form->getOpenSection();
        printf('</table><div id="%s" style="display:%s;"><table class="item" border="0" width="100%%" cellspacing="0" cellpadding="1">',
               '_section_' . $section,
               ($open_section == $section ? 'block' : 'none'));
    }

    function _renderSectionEnd()
    {
        echo '</table></div><table border="0" width="100%" cellspacing="0" cellpadding="1">';
    }

    function end()
    {
        $this->_renderEnd();
    }

    function close()
    {
        echo "</form>\n";
    }

    function listFormVars(&$form)
    {
        $variables = &$form->getVariables(true, true);
        $vars = array();
        if ($variables) {
            foreach ($variables as $var) {
                if (is_object($var)) {
                    $vars[$var->getVarName()] = 1;
                } else {
                    $vars[$var] = 1;
                }
            }
        }
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
        if (($tokenError = $form->getError('__formToken')) !== null) {
?><tr class="<?php echo $this->getRowClass() ?>" valign="top"><td colspan="<?php echo $this->_cols; ?>"><span class="form-error"><?php echo $tokenError ?></span></td></tr><?php
        }

        foreach ($variables as $section_id => $section) {
            if ($section_id != '__base') {
                $this->_renderSectionBegin($form, $section_id);
            }
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
                }
            }
            if ($section_id != '__base') {
                $this->_renderSectionEnd();
            }
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

    /* Implementation specifics -- begin / end functions. */
    function _renderBeginActive($name)
    {
        if ($this->_showHeader) {
            $this->_sectionHeader($name);
        }
?><table border="0" width="100%" cellspacing="0" cellpadding="2">
<?php if ($this->_requiredLegend): ?><tr><td></td><td><span class="form-error"><?php echo $this->_requiredMarker ?></span> = Required Field</td></tr><?php endif; ?>
<?php
    }

    function _renderBeginInactive($name)
    {
        if ($this->_showHeader) {
            $this->_sectionHeader($name);
        }
?><table border="0" width="100%" cellspacing="0" cellpadding="1"><?php
    }

    function _renderEnd()
    {
?></table><?php
        echo $this->_varRenderer->renderEnd();
    }

    function _renderHeader($header, $error = '')
    {
?><tr><td class="control" width="100%" colspan="<?php echo $this->_cols; ?>" valign="bottom"><b><?php echo $header ?></b><?php
        if (!empty($error)) {
?><br /><span class="form-error"><?php echo $error ?></span><?php
        }
?></td></tr>
<?php
    }

    function _renderDescription($text)
    {
?><tr><td width="100%" colspan="<?php echo $this->_cols; ?>" class="<?php echo $this->getRowClass() ?>"><table cellpadding="8" border="0"><tr><td><?php echo $text ?></td></tr></table></td></tr>
<?php
    }

    function _renderSpacer()
    {
?><tr><td colspan="<?php echo $this->_cols; ?>">&nbsp;</td></tr>
<?php
    }

    function _renderSubmit($submit, $reset)
    {
?><tr><td colspan="<?php echo $this->_cols; ?>" class="control">
  <?php if (!is_array($submit)) $submit = array($submit); foreach ($submit as $submitbutton): ?>
    <input class="button" name="submitbutton" type="submit" value="<?php echo $submitbutton ?>" />
  <?php endforeach; ?>
  <?php if (!empty($reset)): ?>
    <input class="button" name="resetbutton" type="reset" value="<?php echo $reset ?>" />
  <?php endif; ?>
</td></tr>
<?php
    }

    // Implementation specifics -- input variables.
    function _renderVarInputBegin(&$form, &$var, &$vars)
    {
        $message = $form->getError($var);
        $isvalid = empty($message);
        $class = $this->getRowClass();
        echo '<tr valign="top">';
        printf('  <td%s align="right" class="%s">%s%s%s%s</td>',
               empty($this->_attrColumnWidth) ? '' : ' width="' . $this->_attrColumnWidth . '"',
               $class,
               $isvalid ? '' : '<span class="form-error">',
               $var->isRequired() ? '<span class="form-error">' . $this->_requiredMarker . '</span>&nbsp;' : '',
               $var->getHumanName(),
               $isvalid ? '' : '<br />' . $message . '</span>');
        printf('  <td%s class="%s">',
               ((!$var->hasHelp() && $form->hasHelp()) ? ' colspan="2"' : ''),
               $class);
    }

    function _renderVarInputEnd(&$form, &$var, &$vars)
    {
        /* Display any description for the field. */
        if ($var->hasDescription()) {
            echo '<br />' . $var->getDescription();
        }

        /* Display any help for the field. */
        if ($var->hasHelp()) {
            $class = $this->getRowClass(false);
            echo '</td><td align="right" class="' . $class . '">' . Help::link($GLOBALS['registry']->getApp(), $var->getHelp()) . '&nbsp';
        }
?></td></tr>
<?php
    }

    // Implementation specifics -- display variables.
    function _renderVarDisplayBegin(&$form, &$var, &$vars)
    {
        $class = $this->getRowClass();
?><tr valign="top">
  <td<?php if (!empty($this->_attrColumnWidth)) echo ' width="' . $this->_attrColumnWidth . '"' ?> align="right" class="<?php echo $class ?>"><b><?php echo $var->getHumanName() ?></b></td>
  <td class="<?php echo $class ?>"><?php
    }

    function _renderVarDisplayEnd(&$form, &$var, &$vars)
    {
?></td></tr>
<?php
    }

    function getRowClass($increment = true)
    {
        static $i = 1;

        if (!$increment) {
            return 'item' . ($i % 2);
        }

        return 'item' . (++$i % 2);
    }

    function _sectionHeader($title)
    {
        if (!empty($title)) {
?><table border="0" cellpadding="2" cellspacing="0" width="100%">
<tr><td align="left" class="header"><b><?php echo $title ?></b></td></tr>
</table><?php
        }
    }

    /**
     * Attempts to return a concrete Horde_Form_Renderer instance
     * based on $renderer.
     *
     * @param mixed $renderer  The type of concrete Horde_Form_Renderer subclass to return.
     *                         The code is dynamically included. If $renderer is an array,
     *                         then we will look in $renderer[0]/lib/Form/Renderer/ for
     *                         the subclass implementation named $renderer[1].php.
     * @param array $params    (optional) A hash containing any additional
     *                         configuration a form might need.
     *
     * @return object Horde_Form_Renderer  The concrete Horde_Form_Renderer reference,
     *                                     or false on an error.
     */
    function &factory($renderer, $params = null)
    {
        if (is_array($renderer)) {
            $app = $renderer[0];
            $renderer = $renderer[1];
        }

        /* Return a base Horde_Form_Renderer object if no driver is
         * specified. */
        $renderer = basename($renderer);
        if (empty($renderer) || (strcmp($renderer, 'none') == 0)) {
            return $ret = &new Horde_Form_Renderer($params);
        }

        if (!empty($app)) {
            include_once $GLOBALS['registry']->getParam('fileroot', $app) . '/lib/Form/Renderer/' . $renderer . '.php';
        } elseif (@file_exists(dirname(__FILE__) . '/Renderer/' . $renderer . '.php')) {
            include_once dirname(__FILE__) . '/Renderer/' . $renderer . '.php';
        } else {
            @include_once 'Horde/Form/Renderer/' . $renderer . '.php';
        }
        $class = 'Horde_Form_Renderer_' . $renderer;
        if (class_exists($class)) {
            return $ret = &new $class($params);
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
     * @param mixed $renderer         The type of concrete Horde_Form_Renderer
     *                                subclass to return. The code is
     *                                dynamically included. If $renderer is an
     *                                array, then we will look in
     *                                $renderer[0]/lib/Form/Renderer/ for the
     *                                subclass implementation named
     *                                $renderer[1].php.
     * @param optional array $params  A hash containing any additional
     *                                configuration a form might need.
     *
     * @return object Horde_Form_Renderer  The concrete Horde_Form_Renderer
     *                                     reference, or false on an error.
     */
    function &singleton($renderer, $params = null)
    {
        static $instances;
        if (!isset($instances)) {
            $instances = array();
        }

        $signature = serialize(array($renderer, $params));
        if (!isset($instances[$signature])) {
            $instances[$signature] = &Horde_Form_Renderer::factory($renderer, $params);
        }

        return $instances[$signature];
    }

}
