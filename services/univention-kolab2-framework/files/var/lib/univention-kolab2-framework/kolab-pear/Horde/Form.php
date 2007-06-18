<?php
/**
 * Horde_Form Master Class.
 *
 * The Horde_Form:: package provides form rendering, validation, and
 * other functionality for the Horde Application Framework.
 *
 * $Horde: framework/Form/Form.php,v 1.246 2004/05/25 15:52:44 jan Exp $
 *
 * Copyright 2001-2004 Robert E. Coyle <robertecoyle@hotmail.com>
 * Copyright 2001-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Robert E. Coyle <robertecoyle@hotmail.com>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Form
 */
class Horde_Form {

    var $_name = '';
    var $_title = '';
    var $_vars;
    var $_submit = array();
    var $_reset = false;
    var $_errors = array();
    var $_submitted = null;
    var $_sections = array();
    var $_open_section = null;
    var $_currentSection = array();
    var $_variables = array();
    var $_hiddenVariables = array();
    var $_useFormToken = true;
    var $_autofilled = false;
    var $_enctype = null;
    var $_help = false;

    function Horde_Form(&$vars, $title = '', $name = null)
    {
        if (is_null($name)) {
            $name = get_class($this);
        }

        $this->_vars = &$vars;
        $this->_title = $title;
        $this->_name = $name;
    }

    function &factory($form, &$vars, $title = '', $name = null)
    {
        if (class_exists($form)) {
            return $ret = &new $form($vars, $title, $name);
        } else {
            return $ret = &new Horde_Form($vars, $title, $name);
        }
    }

    function &singleton($form, &$vars, $title = '', $name = null)
    {
        static $instances;

        $signature = serialize(array($form, $vars, $title, $name));
        if (!isset($instances[$signature])) {
            $instances[$signature] = &Horde_Form::factory($form, $vars, $title, $name);
        }

        return $instances[$signature];
    }

    function setVars(&$vars)
    {
        $this->_vars = &$vars;
    }

    function getTitle()
    {
        return $this->_title;
    }

    function setTitle($title)
    {
        $this->_title = $title;
    }

    function getName()
    {
        return $this->_name;
    }

    /**
     * Get the renderer for this form, either a custom renderer or the
     * standard one.
     *
     * To use a custom form renderer, your form class needs to
     * override this function:
     *
     * function &getRenderer()
     * {
     *     return $r = &new CustomFormRenderer();
     * }
     *
     * ... where CustomFormRenderer is the classname of the custom
     * renderer class, which should extend Horde_Form_Renderer.
     *
     * @return object Horde_Form_Renderer  The form renderer.
     */
    function &getRenderer()
    {
        require_once 'Horde/Form/Renderer.php';
        return new Horde_Form_Renderer();
    }

    function &getType($type, $params = array())
    {
        $type_class = 'Horde_Form_Type_' . $type;
        if (!class_exists($type_class)) {
            Horde::fatal(PEAR::raiseError(sprintf('Nonexistant class "%s" for field type "%s"', $type_class, $type)), __FILE__, __LINE__);
        }
        $type_ob = &new $type_class();
        call_user_func_array(array(&$type_ob, 'init'), $params);
        return $type_ob;
    }

    function setSection($section = '', $desc = '', $expanded = true)
    {
        $this->_currentSection = $section;
        $this->_sections[$section]['desc'] = $desc;
        $this->_sections[$section]['expanded'] = $expanded;

    }

    function getSectionDesc($section)
    {
        return $this->_sections[$section]['desc'];
    }

    function setOpenSection($section)
    {
        $_SESSION['horde_form'][$this->_name]['open_section'] = $section;
    }

    function getOpenSection()
    {
        if (isset($_COOKIE[$this->_name . '_open'])) {
            return $_SESSION['horde_form'][$this->_name]['open_section'] = $_COOKIE[$this->_name . '_open'];
        } elseif (isset($_SESSION['horde_form'][$this->_name]['open_section'])) {
            return $_SESSION['horde_form'][$this->_name]['open_section'];
        }
        return null;
    }

    function getSectionExpandedState($section)
    {
        if ($boolean) {
            /* Only the boolean value is required. */
            return $this->_sections[$section]['expanded'];
        }

        /* Need to return the values for use in styles. */
        if ($this->_sections[$section]['expanded']) {
            return 'block';
        } else {
            return 'none';
        }
    }

    /**
     * @access protected
     */
    function &addVariable($humanName, $varName, $type, $required,
                          $readonly = false, $description = null,
                          $params = array())
    {
        $type = $this->getType($type, $params);
        $var = &new Horde_Form_Variable($humanName, $varName, $type,
                                        $required, $readonly, $description);

        /* Set the form object reference in the var. */
        $var->setFormOb($this);

        if ($var->getTypeName() == 'enum' &&
            count($var->getValues()) == 1) {
            $vals = array_keys($var->getValues());
            $this->_vars->add($var->varName, $vals[0]);
            $var->_autofilled = true;
        } elseif ($var->getTypeName() == 'file' ||
                  $var->getTypeName() == 'image') {
            $this->_enctype = 'multipart/form-data';
        }
        if (empty($this->_currentSection)) {
            $this->_currentSection = '__base';
        }
        $this->_variables[$this->_currentSection][] = &$var;

        return $var;
    }

    /**
     * @access protected
     */
    function &addHidden($humanName, $varName, $type, $required,
                        $readonly = false, $description = null)
    {
        $type = $this->getType($type);
        $var = &new Horde_Form_Variable($humanName, $varName, $type,
                                       $required, $readonly, $description);
        $this->_hiddenVariables[] = &$var;
        return $var;
    }

    function &getVariables($flat = true, $withHidden = false)
    {
        if ($flat) {
            $vars = array();
            foreach ($this->_variables as $section) {
                foreach ($section as $var) {
                    $vars[] = $var;
                }
            }
            if ($withHidden) {
                foreach ($this->_hiddenVariables as $var) {
                    $vars[] = $var;
                }
            }
            return $vars;
        } else {
            return $this->_variables;
        }
    }

    function setButtons($submit, $reset = false)
    {
        if ($submit === true || is_null($submit) || empty($submit)) {
            /* Default to 'Submit'. */
            $submit = array(_("Submit"));
        } elseif (!is_array($submit)) {
            /* Default to array if not passed. */
            $submit = array($submit);
        }
        /* Only if $reset is strictly true insert default 'Reset'. */
        if ($reset === true) {
            $reset = _("Reset");
        }

        $this->_submit = $submit;
        $this->_reset = $reset;
    }

    function appendButtons($submit)
    {
        if (!is_array($submit)) {
            $submit = array($submit);
        }

        $this->_submit = array_merge($this->_submit, $submit);
    }

    function preserveVarByPost(&$vars, $varname, $alt_varname = '')
    {
        $value = $vars->getExists($varname, $wasset);

        /* If an alternate name is given under which to preserve use that. */
        if ($alt_varname) {
            $varname = $alt_varname;
        }

        if ($wasset) {
            $this->_preserveVarByPost($varname, $value);
        }
    }


    /**
     * @access private
     */
    function _preserveVarByPost($varname, $value)
    {
        if (is_array($value)) {
            foreach ($value as $id => $val) {
                $this->_preserveVarByPost($varname . '[' . $id . ']', $val);
            }
        } else {
            $varname = htmlspecialchars($varname);
            $value = htmlspecialchars($value);
            printf('<input type="hidden" name="%s" value="%s" />' . "\n",
                   $varname,
                   $value);
        }
    }

    function open(&$renderer, &$vars, $action, $method = 'get', $enctype = null)
    {
        if (is_null($enctype) && !is_null($this->_enctype)) {
            $enctype = $this->_enctype;
        }
        $renderer->open($action, $method, $this->_name, $enctype);
        $renderer->listFormVars($this);

        if (!empty($this->_name)) {
            $this->_preserveVarByPost('formname', $this->_name);
        }

        if ($this->_useFormToken) {
            require_once 'Horde/Token.php';
            $this->_preserveVarByPost('__formToken_' . $this->_name, Horde_Token::generateId($this->_name));
        }

        /* Loop through vars and check for any special cases to preserve. */
        $variables = $this->getVariables();
        foreach ($variables as $var) {
            /* Preserve value if change has to be tracked. */
            if ($var->getOption('trackchange')) {
                $varname = $var->getVarName();
                $this->preserveVarByPost($vars, $varname, '__old_' . $varname);
            }
        }

        foreach ($this->_hiddenVariables as $var) {
            $this->preserveVarByPost($vars, $var->getVarName());
        }
    }

    function close(&$renderer)
    {
        $renderer->close();
    }

    function renderActive(&$renderer, &$vars, $action, $method = 'get', $enctype = null)
    {
        if (is_null($enctype) && !is_null($this->_enctype)) {
            $enctype = $this->_enctype;
        }
        $renderer->open($action, $method, $this->getName(), $enctype);
        $renderer->listFormVars($this);

        if (!empty($this->_name)) {
            $this->_preserveVarByPost('formname', $this->_name);
        }

        if ($this->_useFormToken) {
            require_once 'Horde/Token.php';
            $this->_preserveVarByPost('__formToken_' . $this->_name, Horde_Token::generateId($this->_name));
        }

        /* Loop through vars and check for any special cases to
         * preserve. */
        $variables = $this->getVariables();
        foreach ($variables as $var) {
            /* Preserve value if change has to be tracked. */
            if ($var->getOption('trackchange')) {
                $varname = $var->getVarName();
                $this->preserveVarByPost($vars, $varname, '__old_' . $varname);
            }
        }

        foreach ($this->_hiddenVariables as $var) {
            $this->preserveVarByPost($vars, $var->getVarName());
        }

        $renderer->beginActive($this->getTitle());
        $renderer->renderFormActive($this, $vars);
        $renderer->submit($this->_submit, $this->_reset);
        $renderer->end();
        $renderer->close();
    }

    function renderInactive(&$renderer, $vars)
    {
        $renderer->beginInactive($this->getTitle());
        $renderer->renderFormInactive($this, $vars);
        $renderer->end();
    }

    function preserve($vars)
    {
        if ($this->_useFormToken) {
            require_once 'Horde/Token.php';
            $this->_preserveVarByPost('__formToken_' . $this->_name, Horde_Token::generateId($this->_name));
        }

        $variables = $this->getVariables();
        foreach ($variables as $var) {
            $varname = $var->getVarName();

            /* Save value of individual components. */
            switch ($var->getTypeName()) {
            case 'passwordconfirm':
            case 'emailconfirm':
                $this->preserveVarByPost($vars, $varname . '[original]');
                $this->preserveVarByPost($vars, $varname . '[confirm]');
                break;

            case 'monthyear':
                $this->preserveVarByPost($vars, $varname . '[month]');
                $this->preserveVarByPost($vars, $varname . '[year]');
                break;

            case 'monthdayyear':
                $this->preserveVarByPost($vars, $varname . '[month]');
                $this->preserveVarByPost($vars, $varname . '[day]');
                $this->preserveVarByPost($vars, $varname . '[year]');
                break;
            }

            $this->preserveVarByPost($vars, $varname);
        }
        foreach ($this->_hiddenVariables as $var) {
            $this->preserveVarByPost($vars, $var->getVarName());
        }
    }

    function unsetVars(&$vars)
    {
        foreach ($this->getVariables() as $var) {
            $vars->remove($var->getVarName());
        }
    }

    /**
     * Does the action of validating the form, checking if it really
     * has been submitted by calling isSubmitted() and if true does
     * any onSubmit() calls for var types in the form. The _submitted
     * var is then rechecked.
     *
     * @returns bool  True or false indicating if the form is valid.
     */
    function validate(&$vars)
    {
        /* Get submitted status. */
        if ($this->isSubmitted()) {
            /* Form was submitted; check for any variable types'
             * onSubmit(). */
            $this->onSubmit($vars);

            /* Recheck submitted status. */
            if (!$this->isSubmitted()) {
                return false;
            }
        } else {
            /* Form has not been submitted; return false. */
            return false;
        }

        $message = '';
        $this->_autofilled = true;

        if ($this->_useFormToken) {
            require_once 'Horde/Token.php';
            $tokenSource = &Horde_Token::singleton($GLOBALS['conf']['token']['driver'], Horde::getDriverConfig('token', $GLOBALS['conf']['token']['driver']));
            if (!$tokenSource->verify($vars->get('__formToken_' . $this->_name))) {
                $this->_errors['__formToken'] = _("This form has already been processed.");
            }
        }

        foreach ($this->getVariables() as $var) {
            $this->_autofilled = $var->_autofilled && $this->_autofilled;
            if (!$var->validate($vars, $message)) {
                $this->_errors[$var->getVarName()] = $message;
            }
        }

        if ($this->_autofilled) {
            unset($this->_errors['__formToken']);
        }

        foreach ($this->_hiddenVariables as $var) {
            if (!$var->validate($vars, $message)) {
                $this->_errors[$var->getVarName()] = $message;
            }
        }

        return $this->isValid();
    }

    function clearValidation()
    {
        $this->_errors = array();
    }

    function getError($var)
    {
        if (is_a($var, 'Horde_Form_Variable')) {
            $name = $var->getVarName();
        } else {
            $name = $var;
        }
        return isset($this->_errors[$name]) ? $this->_errors[$name] : null;
    }

    function setError($var, $message)
    {
        if (is_a($var, 'Horde_Form_Variable')) {
            $name = $var->getVarName();
        } else {
            $name = $var;
        }
        $this->_errors[$name] = $message;
    }

    function clearError($var)
    {
        if (is_a($var, 'Horde_Form_Variable')) {
            $name = $var->getVarName();
        } else {
            $name = $var;
        }
        unset($this->_errors[$name]);
    }

    function isValid()
    {
        return ($this->_autofilled || count($this->_errors) == 0);
    }

    function execute(&$vars)
    {
        Horde::logMessage('Warning: Horde_Form::execute() called, should be overridden', __FILE__, __LINE__, PEAR_LOG_DEBUG);
    }

    /**
     * Fetch the field values of the submitted form.
     *
     * @access public
     *
     * @params object $vars  The Variables object.
     * @params array  $info  Array to be filled with the submitted field values.
     */
    function getInfo(&$vars, &$info)
    {
        $this->_getInfoFromVariables($this->getVariables(), $vars, $info);
        $this->_getInfoFromVariables($this->_hiddenVariables, $vars, $info);
    }

    /**
     * Fetch the field values from a given array of variables.
     *
     * @access private
     *
     * @params array  $variables  An array of Horde_Form_Variable objects to
     *                            fetch from.
     * @params object $vars       The Variables object.
     * @params array  $info       The array to be filled with the submitted
     *                            field values.
     */
    function _getInfoFromVariables($variables, &$vars, &$info)
    {
        foreach ($variables as $var) {
            if ($var->isArrayVal()) {
                $var->getInfo($vars, $values);
                if (is_array($values)) {
                    $varName = str_replace('[]', '', $var->getVarName());
                    foreach ($values as $i => $val) {
                        $info[$i][$varName] = $val;
                    }
                }
            } else {
                require_once 'Horde/Array.php';
                if (Horde_Array::getArrayParts($var->getVarName(), $base, $keys)) {
                    if (!isset($info[$base])) {
                        $info[$base] = array();
                    }
                    $pointer = &$info[$base];
                    while (count($keys)) {
                        $key = array_shift($keys);
                        if (!isset($pointer[$key])) {
                            $pointer[$key] = array();
                        }
                        $pointer = &$pointer[$key];
                    }
                    $var->getInfo($vars, $pointer);
                } else {
                    $var->getInfo($vars, $info[$var->getVarName()]);
                }
            }
        }
    }

    function hasHelp()
    {
        return $this->_help;
    }

    /**
     * Determines if this form has been submitted or not. If the class
     * var _submitted is null then it will check for the presence of
     * the formname in the form variables.
     *
     * Other events can explicitly set the _submitted variable to
     * false to indicate a form submit but not for actual posting of
     * data (eg. onChange events to update the display of fields).
     *
     * @returns boolean  True or false indicating if the form has been submitted.
     */
    function isSubmitted()
    {
        if (is_null($this->_submitted)) {
            if ($this->_vars->get('formname')) {
                $this->_submitted = true;
            } else {
                $this->_submitted = false;
            }
        }

        return $this->_submitted;
    }

    /**
     * Check if there is anything to do on the submission of the form
     * by looping through each variable's onSubmit() function.
     */
    function onSubmit(&$vars)
    {
        $variables = $this->getVariables();
        /* Loop through all vars and check if anything to do on submit. */
        foreach ($variables as $var) {
            $var->type->onSubmit($var, $vars);
            /* If changes to var being tracked don't register the form as
             * submitted if old value and new value differ. */
            if ($var->getOption('trackchange')) {
                $varname = $var->getVarName();
                if (!is_null($vars->get('formname')) &&
                    $vars->get($varname) != $vars->get('__old_' . $varname)) {
                    $this->_submitted = false;
                }
            }
        }
    }

    /**
     * Explicit setting of the state of the form submit. An event can override
     * the automatic determination of the submit state in the isSubmitted()
     * function.
     *
     * @params optional bool  True or false to indicate the submit state of the
     *                        form.
     */
    function setSubmitted($state = true)
    {
        $this->_submitted = $state;
    }

}

/**
 * Horde_Form_Type Class
 *
 * @author  Robert E. Coyle <robertecoyle@hotmail.com>
 * @package Horde_Form
 */
class Horde_Form_Type {

    function Horde_Form_Type()
    {
    }

    function init()
    {
    }

    function onSubmit()
    {
    }

    function isValid(&$var, &$vars, $value, &$message)
    {
        $message = "<b>Error:</b> Horde_Form_Type::isValid() called - should be overridden<br />";
        return false;
    }

    function getTypeName()
    {
        require_once 'Horde/String.php';
        return str_replace('horde_form_type_', '', String::lower(get_class($this)));
    }

    function getValues()
    {
        return null;
    }

    function getInfo(&$vars, &$var, &$info)
    {
        $info = $var->getValue($vars);
    }

}

class Horde_Form_Type_spacer extends Horde_Form_Type {

    function isValid(&$var, &$vars, $value, &$message)
    {
        return true;
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Spacer");
        return $about;
    }

}

class Horde_Form_Type_weatherdotcom extends Horde_Form_Type {

    var $_regex;
    var $_size;
    var $_maxlength;

    /**
     * The initialisation function for the text variable type.
     *
     * @access private
     *
     * @param optional string $regex   Any valid PHP PCRE pattern syntax that
     *                                 needs to be matched for the field to be
     *                                 considered valid. If left empty validity
     *                                 will be checked only for required fields
     *                                 whether they are empty or not.
     *                                 If using this regex test it is advisable
     *                                 to enter a description for this field to
     *                                 warn the user what is expected, as the
     *                                 generated error message is quite generic
     *                                 and will not give any indication where
     *                                 the regex failed.
     * @param optional int $size       The size of the input field.
     * @param optional int $maxlength  The max number of characters.
     */
    function init($regex = '', $size = 40, $maxlength = null)
    {
        $this->_regex     = $regex;
        $this->_size      = $size;
        $this->_maxlength = $maxlength;
    }

    function isValid(&$var, &$vars, $value, &$message)
    {
        require_once 'Services/Weather.php';
        $weatherDotCom = &Services_Weather::service('WeatherDotCom');
        $weatherDotCom->setAccountData('<PartnerID>', '<LicenseKey>');
        $search = $weatherDotCom->searchLocation($value);

        if (is_array($search)) {
            $message = _("Valid locations found include: ") . implode(', ', $search);
            return false;
        } elseif (is_a($search, 'PEAR_Error')) {
            $message = PEAR::raiseError(_('PEAR Error'));
            return false;
        } else {
            return true;
        }
    }

    function getSize()
    {
        return $this->_size;
    }

    function getMaxLength()
    {
        return $this->_maxlength;
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Text");
        $about['params'] = array(
            'regex'     => array('label' => _("Regex"),
                                 'type'  => 'text'),
            'size'      => array('label' => _("Size"),
                                 'type'  => 'int'),
            'maxlength' => array('label' => _("Maximum length"),
                                 'type'  => 'int'),
        );
        return $about;
    }

}

class Horde_Form_Type_header extends Horde_Form_Type {

    function isValid(&$var, &$vars, $value, &$message)
    {
        return true;
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Header");
        return $about;
    }

}

class Horde_Form_Type_description extends Horde_Form_Type {

    function isValid(&$var, &$vars, $value, &$message)
    {
        return true;
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Description");
        return $about;
    }

}

class Horde_Form_Type_html extends Horde_Form_Type {

    function isValid(&$var, &$vars, $value, &$message)
    {
        return true;
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("HTML");
        return $about;
    }

}

class Horde_Form_Type_number extends Horde_Form_Type {

    function isValid(&$var, &$vars, $value, &$message)
    {
        if ($var->isRequired() && empty($value) && ((string)(double)$value !== $value)) {
            $message = _("This field is required.");
            return false;
        } elseif (empty($value)) {
            return true;
        }

        /* If matched, then this is a correct numeric value. */
        if (preg_match($this->_getValidationPattern(), $value)) {
            return true;
        }

        $message = _("This field must be a valid number.");
        return false;
    }

    function _getValidationPattern()
    {
        static $pattern = '';
        if (!empty($pattern)) {
            return $pattern;
        }

        /* Get current locale information. */
        $linfo = NLS::getLocaleInfo();

        /* Build the pattern. */
        $pattern = '(-)?';

        /* Only check thousands separators if locale has any. */
        if (!empty($linfo['mon_thousands_sep'])) {
            /* Regex to check for correct thousands separators (if any). */
            $pattern .= '((\d+)|((\d{0,3}?)([' . $linfo['mon_thousands_sep'] . ']\d{3})*?))';
        } else {
            /* No locale thousands separator, check for only digits. */
            $pattern .= '(\d+)';
        }
        /* If no decimal point specified default to dot. */
        if (empty($linfo['mon_decimal_point'])) {
            $linfo['mon_decimal_point'] = '.';
        }
        /* Regex to check for correct decimals (if any). */
        $pattern .= '([' . $linfo['mon_decimal_point'] . '](\d*))?';

        /* Put together the whole regex pattern. */
        $pattern = '/^' . $pattern . '$/';

        return $pattern;
    }

    function getInfo(&$vars, &$var, &$info)
    {
        $value = $vars->get($var->getVarName());
        $linfo = NLS::getLocaleInfo();
        $value = str_replace($linfo['mon_thousands_sep'], '', $value);
        $info = str_replace($linfo['mon_decimal_point'], '.', $value);
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Number");
        return $about;
    }

}

class Horde_Form_Type_int extends Horde_Form_Type {

    function isValid(&$var, &$vars, $value, &$message)
    {
        if ($var->isRequired() && empty($value) && ((string)(int)$value !== $value)) {
            $message = _("This field is required.");
            return false;
        }

        if (empty($value) || preg_match('/^[0-9]+$/', $value)) {
            return true;
        }

        $message = _("This field may only contain integers.");
        return false;
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Integer");
        return $about;
    }

}

class Horde_Form_Type_octal extends Horde_Form_Type {

    function isValid(&$var, &$vars, $value, &$message)
    {
        if ($var->isRequired() && empty($value) && ((string)(int)$value !== $value)) {
            $message = _("This field is required.");
            return false;
        }

        if (empty($value) || preg_match('/^[0-7]+$/', $value)) {
            return true;
        }

        $message = _("This field may only contain octal values.");
        return false;
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Octal");
        return $about;
    }

}

class Horde_Form_Type_intList extends Horde_Form_Type {

    function isValid(&$var, &$vars, $value, &$message)
    {
        if (empty($value) && $var->isRequired()) {
            $message = _("This field is required.");
            return false;
        }

        if (empty($value) || preg_match('/^[0-9 ,]+$/', $value)) {
            return true;
        }

        $message = _("This field must be a comma or space separated list of integers");
        return false;
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Integer list");
        return $about;
    }

}

class Horde_Form_Type_text extends Horde_Form_Type {

    var $_regex;
    var $_size;
    var $_maxlength;

    /**
     * The initialisation function for the text variable type.
     *
     * @access private
     *
     * @param optional string $regex   Any valid PHP PCRE pattern syntax that
     *                                 needs to be matched for the field to be
     *                                 considered valid. If left empty validity
     *                                 will be checked only for required fields
     *                                 whether they are empty or not.
     *                                 If using this regex test it is advisable
     *                                 to enter a description for this field to
     *                                 warn the user what is expected, as the
     *                                 generated error message is quite generic
     *                                 and will not give any indication where
     *                                 the regex failed.
     * @param optional int $size       The size of the input field.
     * @param optional int $maxlength  The max number of characters.
     */
    function init($regex = '', $size = 40, $maxlength = null)
    {
        $this->_regex     = $regex;
        $this->_size      = $size;
        $this->_maxlength = $maxlength;
    }

    function isValid(&$var, &$vars, $value, &$message)
    {
        $valid = true;

        if ($var->isRequired() && empty($this->_regex)) {
            $valid = strlen(trim($value)) > 0;

            if (!$valid) {
                $message = _("This field is required.");
            }
        } elseif (!empty($this->_regex)) {
            $valid = preg_match($this->_regex, $value);

            if (!$valid) {
                $message = _("You have to enter a valid value.");
            }
        }

        return $valid;
    }

    function getSize()
    {
        return $this->_size;
    }

    function getMaxLength()
    {
        return $this->_maxlength;
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Text");
        $about['params'] = array(
            'regex'     => array('label' => _("Regex"),
                                 'type'  => 'text'),
            'size'      => array('label' => _("Size"),
                                 'type'  => 'int'),
            'maxlength' => array('label' => _("Maximum length"),
                                 'type'  => 'int'),
        );
        return $about;
    }

}

class Horde_Form_Type_stringlist extends Horde_Form_Type_text {

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("String list");
        $about['params'] = array(
            'regex'     => array('label' => _("Regex"),
                                 'type'  => 'text'),
            'size'      => array('label' => _("Size"),
                                 'type'  => 'int'),
            'maxlength' => array('label' => _("Maximum length"),
                                 'type'  => 'int'),
        );
        return $about;
    }

}

class Horde_Form_Type_cellphone extends Horde_Form_Type {

    function isValid(&$var, &$vars, $value, &$message)
    {
        $valid = true;

        if ($var->isRequired()) {
            $valid = strlen(trim($value)) > 0;

            if (!$valid) {
                $message = _("This field is required.");
            }
        } else {
            $valid = preg_match('/^\+?\d*$/', $value);

            if (!$valid) {
                $message = _("You have to enter a valid cellphone number, digits only with an optional '+' for the international dialing prefix.");
            }
        }

        return $valid;
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Cellphone");
        return $about;
    }

}

class Horde_Form_Type_longText extends Horde_Form_Type_text {

    var $_rows;
    var $_cols;
    var $_helper = array();

    function init($rows = 8, $cols = 80, $helper = '')
    {
        $this->_rows = $rows;
        $this->_cols = $cols;
        $this->_helper = $helper;
    }

    function getRows()
    {
        return $this->_rows;
    }

    function getCols()
    {
        return $this->_cols;
    }

    function hasHelper($option = '')
    {
        if (empty($option)) {
            /* No option specified, check if any helpers have been
             * activated. */
            return !empty($this->_helper);
        } elseif (empty($this->_helper)) {
            /* No helpers activated at all, return false. */
            return false;
        } else {
            /* Check if given helper has been activated. */
            return in_array($option, $this->_helper);
        }
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Long text");
        $about['params'] = array(
            'rows'   => array('label' => _("Number of rows"),
                              'type'  => 'int'),
            'cols'   => array('label' => _("Number of columns"),
                              'type'  => 'int'),
            'helper' => array('label' => _("Helper"),
                              'type'  => 'boolean')
        );
        return $about;
    }

}

class Horde_Form_Type_countedText extends Horde_Form_Type_longText {

    var $_chars;

    function init($rows = null, $cols = null, $chars = 1000)
    {
        parent::init($rows, $cols);
        $this->_chars = $chars;
    }

    function isValid(&$var, &$vars, $value, &$message)
    {
        $valid = true;

        if ($var->isRequired()) {
            $length = String::length(trim($value));

            if ($length <= 0) {
                $valid = false;
                $message = _("This field is required.");
            } elseif ($length > $this->_chars) {
                $valid = false;
                $message = sprintf(_("There are too many characters in this field. You have entered %s characters; you must enter less than %s."), String::length(trim($value)), $this->_chars);
            }
        }

        return $valid;
    }

    function getChars()
    {
        return $this->_chars;
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Counted text");
        $about['params'] = array(
            'rows'  => array('label' => _("Number of rows"),
                             'type'  => 'int'),
            'cols'  => array('label' => _("Number of columns"),
                             'type'  => 'int'),
            'chars' => array('label' => _("Number of characters"),
                             'type'  => 'int')
        );
        return $about;
    }

}

class Horde_Form_Type_address extends Horde_Form_Type_longText {

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Address");
        $about['params'] = array(
            'rows' => array('label' => _("Number of rows"),
                            'type'  => 'int'),
            'cols' => array('label' => _("Number of columns"),
                            'type'  => 'int'));
        return $about;
    }

}

class Horde_Form_Type_file extends Horde_Form_Type {

    function isValid(&$var, &$vars, $value, &$message)
    {
        if ($var->isRequired()) {
            $uploaded = &Browser::wasFileUploaded($var->getVarName());
            if (is_a($uploaded, 'PEAR_Error')) {
                $message = $uploaded->getMessage();
                return false;
            }
        }

        return true;
    }

    function getInfo(&$vars, &$var, &$info)
    {
        $name = $var->getVarName();
        $uploaded = &Browser::wasFileUploaded($name);
        if ($uploaded === true) {
            $info['name'] = $_FILES[$name]['name'];
            $info['type'] = $_FILES[$name]['type'];
            $info['tmp_name'] = $_FILES[$name]['tmp_name'];
            $info['file'] = $_FILES[$name]['tmp_name'];
            $info['error'] = $_FILES[$name]['error'];
            $info['size'] = $_FILES[$name]['size'];
        }
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("File upload");
        return $about;
    }

}

class Horde_Form_Type_image extends Horde_Form_Type {

    /**
     * Has a file been uploaded on this submit.
     * @var bool $_uploaded
     */
    var $_uploaded = null;

    /**
     * Show the upload button?
     * @var boolean $_show_upload
     */
    var $_show_upload = true;

    /**
     * Show the option to upload also original non-modified image?
     * @var boolean $_show_keeporig
     */
    var $_show_keeporig= false;

    /**
     * Hash containing the previously uploaded image info.
     * @var array $_img
     */
    var $_img = array();

    function init($show_upload = true, $show_keeporig = false)
    {
        $this->_show_upload   = $show_upload;
        $this->_show_keeporig = $show_keeporig;
    }

    function onSubmit(&$var, &$vars)
    {
        /* Get the upload. */
        $this->_getUpload($vars, $var);

        /* If this was done through the upload button override the submitted
         * value of the form. */
        if ($vars->get('_do_' . $var->getVarName())) {
            $var->form->setSubmitted(false);
        }
    }

    function isValid(&$var, &$vars, $value, &$message)
    {
        $field = $vars->get($var->getVarName());

        /* The upload generated a PEAR Error. */
        if (is_a($this->_uploaded, 'PEAR_Error')) {
            /* Not required and no image upload attempted. */
            if (!$var->isRequired() && empty($field['img']) &&
                $this->_uploaded->getCode() == 4) {
                return true;
            }

            /* TODO: Change error value to upload error constants when
             * PHP4.3.0 is required. Error 4: UPLOAD_ERR_NO_FILE, */
            if ($this->_uploaded->getCode() == 4 && empty($field['img'])) {
                /* Nothing uploaded and no older upload. */
                $message = _("This field is required.");
                return false;
            } elseif (!empty($field['img'])) {
                /* Nothing uploaded but older upload present. */
                return true;
            } else {
                /* Some other error message. */
                $message = $this->_uploaded->getMessage();
                return false;
            }
        }

        return true;
    }

    function getInfo(&$vars, &$var, &$info)
    {
        /* Get the upload. */
        $this->_getUpload($vars, $var);

        /* Get image params stored in the hidden field. */
        $value = $var->getValue($vars);
        $info = $this->_img;
        if (empty($info['file'])) {
            unset($info['file']);
            return;
        }
        if ($this->_show_keeporig) {
            $info['keep_orig'] = !empty($value['keep_orig']);
        }

        /* Set the uploaded value (either true or PEAR_Error). */
        $info['uploaded'] = &$this->_uploaded;

        /* If a modified file exists move it over the original. */
        if ($this->_show_keeporig && $info['keep_orig']) {
            /* Requested the saving of original file also. */
            $info['orig_file'] = Horde::getTempDir() . '/' . $info['file'];
            $info['file'] = Horde::getTempDir() . '/mod_' . $info['file'];
            /* Check if a modified file actually exists. */
            if (!file_exists($info['file'])) {
                $info['file'] = $info['orig_file'];
                unset($info['orig_file']);
            }
        } else {
            /* Saving of original not required. */
            $mod_file = Horde::getTempDir() . '/mod_' . $info['file'];
            $info['file'] = Horde::getTempDir() . '/' . $info['file'];

            if (file_exists($mod_file)) {
                /* Unlink first (has to be done on Windows machines?) */
                unlink($info['file']);
                rename($mod_file, $info['file']);
            }
        }
    }

    /**
     * Gets the upload and sets up the upload data array. Either
     * fetches an upload done with this submit or retries stored
     * upload info.
     */
    function _getUpload(&$vars, &$var)
    {
        /* Don't bother with this function if already called and set up vars. */
        if (!empty($this->_img)) {
            return true;
        }

        /* Check if file has been uploaded. */
        $varname = $var->getVarName();
        $this->_uploaded = &Browser::wasFileUploaded($varname . '[new]');

        if ($this->_uploaded === true) {
            /* A file has been uploaded on this submit. Save to temp dir for
             * preview work. */
            $this->_img['type'] = $this->getUploadedFileType($varname . '[new]');

            /* Get the other parts of the upload. */
            require_once 'Horde/Array.php';
            Horde_Array::getArrayParts($varname . '[new]', $base, $keys);

            /* Get the temporary file name. */
            $keys_path = array_merge(array($base, 'tmp_name'), $keys);
            $this->_img['file'] = Horde_Array::getElement($_FILES, $keys_path);

            /* Get the actual file name. */
            $keys_path= array_merge(array($base, 'name'), $keys);
            $this->_img['name'] = Horde_Array::getElement($_FILES, $keys_path);

            /* Get the file size. */
            $keys_path= array_merge(array($base, 'size'), $keys);
            $this->_img['size'] = Horde_Array::getElement($_FILES, $keys_path);

            /* Get any existing values for the image upload field. */
            $upload = $vars->get($var->getVarName());
            $upload['img'] = @unserialize($upload['img']);

            /* Get the temp file if already one uploaded, otherwise create a
             * new temporary file. */
            if (!empty($upload['img']['file'])) {
                $tmp_file = Horde::getTempDir() . '/' . $upload['img']['file'];
            } else {
                $tmp_file = Horde::getTempFile('Horde', false);
            }

            /* Move the browser created temp file to the new temp file. */
            move_uploaded_file($this->_img['file'], $tmp_file);
            $this->_img['file'] = basename($tmp_file);

            /* Store the uploaded image file data to the hidden field. */
            $upload['img'] = serialize($this->_img);
            $vars->set($var->getVarName(), $upload);
        } elseif ($this->_uploaded) {
            /* File has not been uploaded. */
            $upload = $vars->get($var->getVarName());
            if ($this->_uploaded->getCode() == 4 && !empty($upload['img'])) {
                $this->_img = @unserialize($upload['img']);
            }
        }
    }

    function getUploadedFileType($field)
    {
        /* Get any index on the field name. */
        require_once 'Horde/Array.php';
        $index = Horde_Array::getArrayParts($field, $base, $keys);

        if ($index) {
            /* Index present, fetch the mime type var to check. */
            $keys_path = array_merge(array($base, 'type'), $keys);
            $type = Horde_Array::getElement($_FILES, $keys_path);
            $keys_path= array_merge(array($base, 'tmp_name'), $keys);
            $tmp_name = Horde_Array::getElement($_FILES, $keys_path);
        } else {
            /* No index, simple set up of vars to check. */
            $type = $_FILES[$field]['type'];
            $tmp_name = $_FILES[$field]['tmp_name'];
        }

        if (empty($type) || ($type == 'application/octet-stream')) {
            /* Type wasn't set on upload, try analising the upload. */
            require_once 'Horde/MIME/Magic.php';
            if (!($type = MIME_Magic::analyzeFile($tmp_name))) {
                if ($index) {
                    /* Get the name value. */
                    $keys_path = array_merge(array($base, 'name'), $keys);
                    $name = Horde_Array::getElement($_FILES, $keys_path);

                    /* Work out the type from the file name. */
                    $type = MIME_Magic::filenameToMIME($name);

                    /* Set the type. */
                    $keys_path = array_merge(array($base, 'type'), $keys);
                    Horde_Array::getElement($_FILES, $keys_path, $type);
                } else {
                    /* Work out the type from the file name. */
                    $type = MIME_Magic::filenameToMIME($_FILES[$field]['name']);

                    /* Set the type. */
                    $_FILES[$field]['type'] = MIME_Magic::filenameToMIME($_FILES[$field]['name']);
                }
            }
        }

        return $type;
    }

    /**
     * Loads any existing image data into the image field. Requires that the
     * array $image passed to it contains the structure:
     *   $image['load']['file'] - the filename of the image;
     *   $image['load']['data'] - the raw image data.
     *
     * @access private
     *
     * @param array $image  The image array.
     */
    function _loadImageData(&$image)
    {
        /* No existing image data to load. */
        if (!isset($image['load'])) {
            return;
        }

        /* Save the data to the temp dir. */
        $tmp_file = Horde::getTempDir() . '/' . $image['load']['file'];
        if ($fd = fopen($tmp_file, 'w')) {
            fwrite($fd, $image['load']['data']);
            fclose($fd);
        }

        $image['img'] = serialize(array('file' => $image['load']['file']));
        unset($image['load']);
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Image upload");
        return $about;
    }

}

class Horde_Form_Type_boolean extends Horde_Form_Type {

    function isValid(&$var, &$vars, $value, &$message)
    {
        return true;
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("True or false");
        return $about;
    }

}

class Horde_Form_Type_link extends Horde_Form_Type {

    function init($values)
    {
        $this->values = $values;
    }

    function isValid(&$var, &$vars, $value, &$message)
    {
        return true;
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Link");
        return $about;
    }

}

class Horde_Form_Type_email extends Horde_Form_Type {

    var $_allow_multi = false;
    var $_strip_domain = false;

    function init($allow_multi = false, $strip_domain = false)
    {
        $this->_allow_multi = $allow_multi;
        $this->_strip_domain = $strip_domain;
    }

    function isValid(&$var, &$vars, $value, &$message)
    {
        if ($var->isRequired() && empty($value)) {
            $message = _("This field is required.");
            return false;
        } elseif (!empty($value)) {
            require_once 'Mail/RFC822.php';
            $parsed_email = Mail_RFC822::parseAddressList($value, false, true);

            if ((!$this->_allow_multi) && count($parsed_email) > 1) {
                $message = _("Only one email address allowed.");
                return false;
            }
            if (empty($parsed_email[0]->mailbox)) {
                $message = _("You did not enter a valid email address.");
                return false;
            }
        }

        return true;
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Email");
        $about['params'] = array(
            'allow_multi' => array('label' => _("Allow multiple addresses"),
                                   'type'  => 'boolean'));
        return $about;
    }

}

class Horde_Form_Type_matrix extends Horde_Form_Type {

    var $_cols;
    var $_rows;
    var $_matix;
    var $_new_input;

    function init($cols, $rows = array(), $matrix = array(), $new_input = false)
    {
        $this->_cols       = $cols;
        $this->_rows       = $rows;
        $this->_matrix     = $matrix;
        $this->_new_input  = $new_input;
    }

    function isValid(&$var, &$vars, $value, &$message)
    {
        return true;
    }

    function getCols()     { return $this->_cols; }
    function getRows()     { return $this->_rows; }
    function getMatrix()   { return $this->_matrix; }
    function getNewInput() { return $this->_new_input; }

    function getInfo(&$vars, &$var, &$info)
    {
        $values = $vars->get($var->getVarName());
        if (!empty($values['n']['r'])) {
            $new_row = $values['n']['r'];
            $values['r'][$new_row] = $values['n']['v'];
            unset($values['n']);
        }

        $info = (isset($values['r']) ? $values['r'] : array());
    }

    function about()
    {
        $about = array();
        $about['name'] = _("Block selection");
        return $about;
    }

}

class Horde_Form_Type_emailConfirm extends Horde_Form_Type {

    function isValid(&$var, &$vars, $value, &$message)
    {
        if ($var->isRequired() && empty($value['original'])) {
            $message = _("This field is required.");
            return false;
        }

        if ($value['original'] != $value['confirm']) {
            $message = _("Email addresses must match.");
            return false;
        } else {
            require_once 'Mail/RFC822.php';
            $parsed_email = Mail_RFC822::parseAddressList($value['original'], false, true);

            if (count($parsed_email) > 1) {
                $message = _("Only one email address allowed.");
                return false;
            }
            if (empty($parsed_email[0]->mailbox)) {
                $message = _("You did not enter a valid email address.");
                return false;
            }
        }

        return true;
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Email with confirmation");
        return $about;
    }

}

class Horde_Form_Type_password extends Horde_Form_Type {

    function isValid(&$var, &$vars, $value, &$message)
    {
        $valid = true;

        if ($var->isRequired()) {
            $valid = strlen(trim($value)) > 0;

            if (!$valid) {
                $message = _("This field is required.");
            }
        }

        return $valid;
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Password");
        return $about;
    }

}

class Horde_Form_Type_passwordConfirm extends Horde_Form_Type {

    function isValid(&$var, &$vars, $value, &$message)
    {
        if ($var->isRequired() && empty($value['original'])) {
            $message = _("This field is required.");
            return false;
        }

        if ($value['original'] != $value['confirm']) {
            $message = _("Passwords must match.");
            return false;
        }

        return true;
    }

    function getInfo(&$vars, &$var, &$info)
    {
        $value = $vars->get($var->getVarName());
        $info = $value['original'];
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Password with confirmation");
        return $about;
    }

}

class Horde_Form_Type_enum extends Horde_Form_Type {

    var $_values;
    var $_prompt;

    function init($values, $prompt = null)
    {
        $this->_values = $values;

        if ($prompt === true) {
            $this->_prompt = _("-- select --");
        } else {
            $this->_prompt = $prompt;
        }
    }

    function isValid(&$var, &$vars, $value, &$message)
    {
        if ($var->isRequired() && $value == '' && !isset($this->_values[$value])) {
            $message = _("This field is required.");
            return false;
        }

        if (count($this->_values) == 0 || isset($this->_values[$value]) ||
            ($this->_prompt && empty($value))) {
            return true;
        }

        $message = _("Invalid data submitted.");
        return false;
    }

    function getValues()
    {
        return $this->_values;
    }

    function getPrompt()
    {
        return $this->_prompt;
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Drop down list");
        $about['params'] = array(
            'values' => array('label' => _("Values to select from"),
                              'type'  => 'stringlist'),
            'prompt' => array('label' => _("Prompt text"),
                              'type'  => 'text'));
        return $about;
    }

}

class Horde_Form_Type_mlenum extends Horde_Form_Type {

    var $_values;
    var $_prompts;

    function init(&$values, $prompts = null)
    {
        $this->_values = &$values;

        if ($prompts === true) {
            $this->_prompts = array(_("-- select --"), _("-- select --"));
        } elseif (!is_array($prompts)) {
            $this->_prompts = array($prompts, $prompts);
        } else {
            $this->_prompts = $prompts;
        }
    }

    function onSubmit(&$var, &$vars)
    {
        $varname = $var->getVarName();
        $value = $vars->get($varname);

        if ($value['1'] != $value['old']) {
            $var->form->setSubmitted(false);
        }
    }

    function isValid(&$var, &$vars, $value, &$message)
    {
        if ($var->isRequired() && (empty($value['1']) || empty($value['2']))) {
            $message = _("This field is required.");
            return false;
        }

        if (count($this->_values) == 0 || isset($this->_values[$value['1']]) ||
            (!empty($this->_prompts) && empty($value['1']))) {
            return true;
        }

        $message = _("Invalid data submitted.");
        return false;
    }

    function getValues()
    {
        return $this->_values;
    }

    function getPrompts()
    {
        return $this->_prompts;
    }

    function getInfo(&$vars, &$var, &$info)
    {
        $info = $vars->get($var->getVarName());
        return $info['2'];
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Multi-level drop down lists");
        $about['params'] = array(
            'values' => array('label' => _("Values to select from"),
                              'type'  => 'stringlist'),
            'prompt' => array('label' => _("Prompt text"),
                              'type'  => 'text'));
        return $about;
    }

}

class Horde_Form_Type_multienum extends Horde_Form_Type_enum {

    var $size = 5;

    function init($values, $size = null)
    {
        if (!is_null($size)) {
            $this->size = (int)$size;
        }

        parent::init($values);
    }

    function isValid(&$var, &$vars, $value, &$message)
    {
        if (is_array($value)) {
            foreach ($value as $val) {
                if (!$this->isValid($var, $vars, $val, $message)) {
                    return false;
                }
            }
            return true;
        }

        if (empty($value) && ((string)(int)$value !== $value)) {
            if ($var->isRequired()) {
                $message = _("This field is required.");
                return false;
            } else {
                return true;
            }
        }

        if (count($this->_values) == 0 || isset($this->_values[$value])) {
            return true;
        }

        $message = _("Invalid data submitted.");
        return false;
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Multiple selection");
        $about['params'] = array(
            'values' => array('label' => _("Values"),
                              'type'  => 'stringlist'),
            'size'   => array('label' => _("Size"),
                              'type'  => 'int'));
        return $about;
    }

}

class Horde_Form_Type_radio extends Horde_Form_Type_enum {

    /* Entirely implemented by Horde_Form_Type_enum; just a different
     * view. */

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Radio selection");
        $about['params'] = array(
            'values' => array('label' => _("Values"),
                              'type'  => 'stringlist'));
        return $about;
    }

}

class Horde_Form_Type_set extends Horde_Form_Type {

    var $_values;

    function init(&$values)
    {
        $this->_values = $values;
    }

    function isValid(&$var, &$vars, $value, &$message)
    {
        if (count($this->_values) == 0 || count($value) == 0) {
            return true;
        }
        foreach ($value as $item) {
            if (!isset($this->_values[$item])) {
                $error = true;
                break;
            }
        }
        if (!isset($error)) {
            return true;
        }

        $message = _("Invalid data submitted.");
        return false;
    }

    function getValues()
    {
        return $this->_values;
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Set");
        $about['params'] = array(
            'values' => array('label' => _("Values"),
                              'type'  => 'stringlist'));
        return $about;
    }

}

class Horde_Form_Type_date extends Horde_Form_Type {

    function isValid(&$var, &$vars, $value, &$message)
    {
        $valid = true;

        if ($var->isRequired()) {
            $valid = strlen(trim($value)) > 0;

            if (!$valid) {
                $message = sprintf(_("%s is required"), $var->getHumanName());
            }
        }

        return $valid;
    }

    function _getAgo($timestamp)
    {
        if (time() - $timestamp < time() - mktime(0, 0, 0)) {
            $ago = 0;
        } else {
            $timestamp = $timestamp - (time() - mktime(0, 0, 0));
            $ago = ceil((time() - $timestamp) / 86400);
        }

        if ($ago == 0) {
            return _(" (today)");
        } elseif ($ago == 1) {
            return _(" (yesterday)");
        } else {
            return sprintf(_(" (%s days ago)"), $ago);
        }
    }

    function getFormattedTime($timestamp, $format = '%a %d %B', $showago = true)
    {
        if (!empty($timestamp)) {
            return strftime($format, $timestamp) . ($showago ? Horde_Form_Type_date::_getAgo($timestamp) : '');
        } else {
            return '';
        }
    }

    function getFormattedTimeFull($timestamp, $format = '%c', $showago = true)
    {
        if (!empty($timestamp)) {
            return strftime($format, $timestamp) . ($showago ? Horde_Form_Type_date::_getAgo($timestamp) : '');
        } else {
            return '';
        }
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Date");
        return $about;
    }

}

class Horde_Form_Type_time extends Horde_Form_Type {

    function isValid(&$var, &$vars, $value, &$message)
    {
        if ($var->isRequired() && empty($value) && ((string)(double)$value !== $value)) {
            $message = _("This field is required.");
            return false;
        }

        if (empty($value) || preg_match('/^[0-2]?[0-9]:[0-5][0-9]$/', $value)) {
            return true;
        }

        $message = _("This field may only contain numbers and the colon.");
        return false;
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Time");
        return $about;
    }

}

class Horde_Form_Type_hourMinuteSecond extends Horde_Form_Type {

    var $_show_seconds;

    function init($show_seconds = false)
    {
        $this->_show_seconds = $show_seconds;
    }

    function isValid(&$var, &$vars, $value, &$message)
    {
        $time = $vars->get($var->getVarName());
        if (!$this->_show_seconds && !isset($time['second'])) {
            $time['second'] = $var->isRequired() ? '00' : '';
        }

        if (!$this->emptyTimeArray($time) && !$this->checktime($time['hour'], $time['minute'], $time['second'])) {
            $message = _("Please enter a valid time.");
            return false;
        } elseif ($this->emptyTimeArray($time) && $var->isRequired()) {
            $message = _("This field is required.");
            return false;
        }

        return true;
    }

    function checktime($hour, $minute, $second) {
        if (!isset($hour) || $hour == '' || ($hour < 0 || $hour > 23)) {
            return false;
        }
        if (!isset($minute) || $minute == '' || ($minute < 0 || $minute > 60)) {
            return false;
        }
        if (!isset($second) || $second == '' || ($second < 0 || $second > 60)) {
            return false;
        }
        return true;
    }

    /**
     * Return the time supplied as a PEAR Date object.
     *
     * @param string $time_in  Date in one of the three formats supported by
     *                         Horde_Form and PEAR's Date class (ISO format
     *                         YYYY-MM-DD HH:MM:SS, timestamp YYYYMMDDHHMMSS and
     *                         UNIX epoch).
     *
     * @return object  The time object.
     */
    function &getTimeOb($time_in)
    {
        require_once 'Date.php';

        /* Fix the time if it is the shortened ISO. */
        if (is_array($time_in)) {
            if (!$this->emptyTimeArray($time_in)) {
                $time_in = sprintf('%02d:%02d:%02d', $time_in['hour'], $time_in['minute'], $time_in['second']);
            }
        }

        /* Return the PEAR time object. */
        return $ret = &new Date($time_in);
    }

    /**
     * Return the time supplied split up into an array.
     *
     * @param string $time_in  Time in one of the three formats supported by
     *                         Horde_Form and PEAR's Date class (ISO format
     *                         YYYY-MM-DD HH:MM:SS, timestamp YYYYMMDDHHMMSS and
     *                         UNIX epoch).
     *
     * @return array  Array with three elements - hour, minute and seconds.
     */
    function getTimeParts($time_in)
    {
        if (is_array($time_in)) {
            /* This is probably a failed isValid input so just return the
             * parts as they are. */
            return $time_in;
        } elseif (empty($time_in)) {
            /* This is just an empty field so return empty parts. */
            return array('hour' => '', 'minute' => '', 'second' => '');
        }
        $time = &$this->getTimeOb($time_in);
        return array('hour' => $time->getHour(),
                     'minute' => $time->getMinute(),
                     'second' => $time->getSecond());
    }

    function emptyTimeArray($time)
    {
        if (is_array($time) && empty($time['hour']) && empty($time['minute']) && empty($time['second'])) {
            return true;
        }
        return false;
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Time selection");
        return $about;
    }

}

class Horde_Form_Type_monthYear extends Horde_Form_Type {

    var $_start_year;
    var $_end_year;
    var $_bare;

    function init($start_year = null, $end_year = null, $bare = false)
    {
        if (is_null($start_year)) {
            $start_year = date('Y');
        }
        if (is_null($end_year)) {
            $end_year = 1920;
        }

        $this->_start_year = $start_year;
        $this->_end_year = $end_year;
        $this->_bare = $bare;
    }

    function isValid(&$var, &$vars, $value, &$message)
    {
        if (!$var->isRequired()) {
            return true;
        }

        if (!$vars->get($this->getMonthVar($var)) ||
            !$vars->get($this->getYearVar($var))) {
            $message = _("Please enter a month and a year.");
            return false;
        }

        return true;
    }

    function getMonthVar($var)
    {
        if ($this->_bare) {
            return 'month';
        } else {
            return $var->getVarName() . '[month]';
        }
    }

    function getYearVar($var)
    {
        if ($this->_bare) {
            return 'year';
        } else {
            return $var->getVarName() . '[year]';
        }
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Month and year");
        $about['params'] = array(
            'start_year' => array('label' => _("Start year"),
                                  'type'  => 'stringlist'),
            'end_year'   => array('label' => _("End year"),
                                  'type'  => 'stringlist'),
            'bare'       => array('label' => _("Bare"),
                                  'type'  => 'boolean'));
        return $about;
    }

}

class Horde_Form_Type_monthDayYear extends Horde_Form_Type {

    var $_start_year;
    var $_end_year;
    var $_picker;
    var $_format_in;
    var $_format_out;

    /**
     * Return the date supplied as a PEAR Date object.
     *
     * @param optional integer $start_year  The first available year for input.
     * @param optional integer $end_year    The last available year for input.
     * @param optional boolean $picker      Do we show the DHTML calendar?
     * @param optional integer $format_in   The format to use when sending the date
     *                                      for storage. Defaults to PEAR Date's
     *                                      default - YYYY-MM-DD HH:MM:SS. Can take
     *                                      the following values:
     *                                        1 - YYYY-MM-DD HH:MM:SS
     *                                        2 - YYYYMMDDHHMMSS(ZI(+/-)HHMM)
     *                                        3 - YYYY-MM-DD HH:MM:SS(ZI(+/-)HHMM)
     *                                        4 - YYYYMMDDHHMMSS
     *                                        5 - Unix epoch
     *                                      See the PEAR Date class for more info.
     * @param optional integer $format_out  The format to use when displaying the
     *                                      date. Similar to the strftime()
     *                                      function.
     *
     */
    function init($start_year = '', $end_year = '', $picker = true, $format_in = null, $format_out = '%d %B, %Y')
    {
        if (empty($start_year)) {
            $start_year = date('Y');
        }
        if (empty($end_year)) {
            $end_year = date('Y') - 100;
        }

        $this->_start_year = $start_year;
        $this->_end_year = $end_year;
        $this->_picker = $picker;
        $this->_format_in = $format_in;
        $this->_format_out = $format_out;
    }

    function isValid(&$var, &$vars, $value, &$message)
    {
        $date = $vars->get($var->getVarName());
        $empty = $this->emptyDateArray($date);

        if ($empty == 1 && $var->isRequired()) {
            $message = _("This field is required.");
            return false;
        } elseif ($empty == 0 && !checkdate($date['month'], $date['day'], $date['year'])) {
            $message = _("Please enter a valid date, check the number of days in the month.");
            return false;
        } elseif ($empty == -1) {
            $message = _("Select all date components.");
            return false;
        }
        return true;
    }

    function emptyDateArray($date)
    {
        if (!is_array($date)) {
            return empty($date);
        }

        $empty = 0;
        /* Check each date array component. */
        foreach ($date as $key => $val) {
            if (empty($val)) {
                $empty++;
            }
        }
        /* Check state of empty. */
        if ($empty == 0) {
            /* If no empty parts return 0. */
            return 0;
        } elseif ($empty == 3) {
            /* If all empty parts return 1. */
            return 1;
        } else {
            /* If some empty parts return -1. */
            return -1;
        }
    }

    /**
     * Return the date supplied split up into an array.
     *
     * @param string $date_in  Date in one of the three formats supported by
     *                         Horde_Form and PEAR's Date class (ISO format
     *                         YYYY-MM-DD HH:MM:SS, timestamp YYYYMMDDHHMMSS and
     *                         UNIX epoch) plus the fourth YYYY-MM-DD.
     *
     * @return array  Array with three elements - year, month and day.
     */
    function getDateParts($date_in)
    {
        if (is_array($date_in)) {
            /* This is probably a failed isValid input so just return the
             * parts as they are. */
            return $date_in;
        } elseif (empty($date_in)) {
            /* This is just an empty field so return empty parts. */
            return array('year' => '', 'month' => '', 'day' => '');
        }
        $date = &$this->getDateOb($date_in);
        return array('year' => $date->getYear(),
                     'month' => $date->getMonth(),
                     'day' => $date->getDay());
    }

    /**
     * Return the date supplied as a PEAR Date object.
     *
     * @param string $date_in  Date in one of the three formats supported by
     *                         Horde_Form and PEAR's Date class (ISO format
     *                         YYYY-MM-DD HH:MM:SS, timestamp YYYYMMDDHHMMSS and
     *                         UNIX epoch) plus the fourth YYYY-MM-DD.
     *
     * @return object          The date object.
     */
    function &getDateOb($date_in)
    {
        require_once 'Date.php';

        if (is_array($date_in)) {
            /* If passed an array change it to the ISO format. */
            if ($this->emptyDateArray($date_in) == 0) {
                $date_in = sprintf('%04d-%02d-%02d 00:00:00', $date_in['year'], $date_in['month'], $date_in['day']);
            }
        } elseif (preg_match('/^\d{4}-\d{2}-\d{2}$/', $date_in)) {
            /* Fix the date if it is the shortened ISO. */
            $date_in = $date_in . ' 00:00:00';
        }

        /* Return the PEAR date object. */
        return $ret = &new Date($date_in);
    }

    /**
     * Return the date supplied as a PEAR Date object.
     *
     * @param string $date  Either an already set up PEAR Date object or a
     *                      string date in one of the three formats supported by
     *                      Horde_Form and PEAR's Date class (ISO format
     *                      YYYY-MM-DD HH:MM:SS, timestamp YYYYMMDDHHMMSS and
     *                      UNIX epoch) plus the fourth YYYY-MM-DD.
     *
     * @return string  The date formatted according to the $format_out parameter
     *                 when setting up the monthdayyear field.
     */
    function formatDate($date)
    {
        if (!is_a($date, 'Date')) {
            $date = &$this->getDateOb($date);
        }

        return $date->format($this->_format_out);
    }

    /**
     * Insert the date input through the form into $info array, in the
     * format specified by the $format_in parameter when setting up
     * monthdayyear field.
     */
    function getInfo(&$vars, &$var, &$info)
    {
        $info = $this->_validateAndFormat($var->getValue($vars), $var);
    }

    /**
     * Validate/format a date submission.
     */
    function _validateAndFormat($value, $var)
    {
        /* If any component is empty consider it a bad date
           and return the default. */
        if ($this->emptyDateArray($value) == 1) {
            return $var->getDefault();
        } else {
            $date = &$this->getDateOb($value);
            if (is_null($this->_format_in)) {
                $this->_format_in = DATE_FORMAT_ISO;
            }
            return $date->getDate($this->_format_in);
        }
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        return array('name' => _("Date selection"),
                     'params' => array(
                         'start_year' => array('label' => _("Start year"),
                                               'type'  => 'int'),
                         'end_year'   => array('label' => _("End year"),
                                               'type'  => 'int'),
                         'picker'     => array('label' => _("Show picker"),
                                               'type'  => 'boolean'),
                         'format_in'  => array('label' => _("Storage format"),
                                               'type'  => 'text'),
                         'format_out' => array('label' => _("Display format"),
                                               'type'  => 'text')));
    }

}

class Horde_Form_Type_colorPicker extends Horde_Form_Type {

    function isValid(&$var, &$vars, $value, &$message)
    {
        if ($var->isRequired() && empty($value)) {
            $message = _("This field is required.");
            return false;
        }

        if (empty($value) || preg_match('/^#([0-9a-z]){6}$/i', $value)) {
            return true;
        }

        $message = _("This field must contain a color code in the RGB Hex format, for example '#1234af'.");
        return false;
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Colour selection");
        return $about;
    }

}

class Horde_Form_Type_sorter extends Horde_Form_Type {

    var $_instance;
    var $_values;
    var $_size;
    var $_header;

    function init($values, $size = 8, $header = '')
    {
        static $horde_sorter_instance = 0;

        /* Get the next progressive instance count for the horde
           sorter so that multiple sorters can be used on one page. */
        $horde_sorter_instance++;
        $this->_instance = 'horde_sorter_' . $horde_sorter_instance;

        if (!empty($header)) {
            $values = array('' => $header) + $values;
        }
        $this->_values = $values;
        $this->_size   = $size;
        $this->_header = $header;
    }

    function isValid(&$var, &$vars, $value, &$message)
    {
        return true;
    }

    function getValues()
    {
        return $this->_values;
    }

    function getSize()
    {
        return $this->_size;
    }

    function getHeader()
    {
        if (!empty($this->_header)) {
            return $this->_header;
        }
        return '';
    }

    function getOptions()
    {
        $html = '';
        foreach ($this->_values as $sl_key => $sl_val) {
            $html .= '<option value="' . $sl_key . '">' . $sl_val . '</option>';
        }

        return $html;
    }

    function getInfo(&$vars, &$var, &$info)
    {
        $value = $vars->get($var->getVarName());
        $info = explode("\t", $value['array']);
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Sort order selection");
        $about['params'] = array(
            'values' => array('label' => _("Values"),
                              'type'  => 'stringlist'),
            'size'   => array('label' => _("Size"),
                              'type'  => 'int'),
            'header' => array('label' => _("Header"),
                              'type'  => 'text'));
        return $about;
    }

}

class Horde_Form_Type_creditcard extends Horde_Form_Type {

    function isValid(&$var, &$vars, $value, &$message)
    {
        if (empty($value) && $var->isRequired()) {
            $message = _("This field is required.");
            return false;
        }

        if (!empty($value)) {
            /* getCardType() will also verify the checksum. */
            $type = $this->getCardType($value);
            if ($type === false || $type == 'unknown') {
                $message = _("This does not seem to be a valid card number.");
                return false;
            }
        }

        return true;
    }

    function getChecksum($ccnum)
    {
        $len = strlen($ccnum);
        if (!is_long($len / 2)) {
            $weight = 2;
            $digit = $ccnum[0];
        } elseif (is_long($len / 2)) {
            $weight = 1;
            $digit = $ccnum[0] * 2;
        }
        if ($digit > 9) {
            $digit = $digit - 9;
        }
        $i = 1;
        $checksum = $digit;
        while ($i < $len) {
            if ($ccnum[$i] != ' ') {
                $digit = $ccnum[$i] * $weight;
                $weight = ($weight == 1) ? 2 : 1;
                if ($digit > 9) {
                    $digit = $digit - 9;
                }
                $checksum += $digit;
            }
            $i++;
        }

        return $checksum;
    }

    function getCardType($ccnum)
    {
        $sum = $this->getChecksum($ccnum);
        $l = strlen($ccnum);

        // Screen checksum.
        if (($sum % 10) != 0) {
            return false;
        }

        // Check for Visa.
        if ((($l == 16) || ($l == 13)) &&
            ($ccnum[0] == 4)) {
            return 'visa';
        }

        // Check for MasterCard.
        if (($l == 16) &&
            ($ccnum[0] == 5) &&
            ($ccnum[1] >= 1) &&
            ($ccnum[1] <= 5)) {
            return 'mastercard';
        }

        // Check for Amex.
        if (($l == 15) &&
            ($ccnum[0] == 3) &&
            (($ccnum[1] == 4) || ($ccnum[1] == 7))) {
            return 'amex';
        }

        // Check for Discover (Novus).
        if (strlen($ccnum) == 16 &&
            substr($ccnum, 0, 4) == '6011') {
            return 'discover';
        }

        // If we got this far, then no card matched.
        return 'unknown';
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        $about = array();
        $about['name'] = _("Credit card number");
        return $about;
    }

}

class Horde_Form_Type_invalid extends Horde_Form_Type {

    var $message;

    function init($message)
    {
        $this->message = $message;
    }

    function isValid(&$var, &$vars, $value, &$message)
    {
        return false;
    }

    function getInfo()
    {
        return _("Integer");
    }

}

/**
 * Horde_Form_Variable Class
 *
 * @author  Robert E. Coyle <robertecoyle@hotmail.com>
 * @package Horde_Form
 */
class Horde_Form_Variable {

    var $form;
    var $humanName;
    var $varName;
    var $type;
    var $required;
    var $readonly;
    var $description;
    var $help;
    var $_arrayVal;
    var $_defValue = null;
    var $_action;
    var $_disabled = false;
    var $_autofilled = false;
    var $_options = array();

    function Horde_Form_Variable($humanName, $varName, &$type, $required,
                                 $readonly = false, $description = null)
    {
        $this->humanName   = $humanName;
        $this->varName     = $varName;
        $this->type        = $type;
        $this->required    = $required;
        $this->readonly    = $readonly;
        $this->description = $description;
        $this->_arrayVal   = strstr($varName, '[]');
    }

    function setFormOb(&$form)  { $this->form = &$form; }
    function setDefault($value) { $this->_defValue = $value; }
    function setAction($action) { $this->_action = $action; }
    function disable()          { $this->_disabled = true; }

    /* Help functions. */
    function setHelp($help) { $this->form->_help = true; $this->help = $help; }
    function hasHelp()      { return !empty($this->help); }
    function getHelp()      { return $this->help; }

    function  getHumanName()   { return $this->humanName; }
    function  getVarName()     { return $this->varName; }
    function &getType()        { return $this->type; }
    function  getTypeName()    { return $this->type->getTypeName(); }
    function  getDefault()     { return $this->_defValue; }
    function  isRequired()     { return $this->required; }
    function  isReadonly()     { return $this->readonly; }
    function  isDisabled()     { return $this->_disabled; }
    function  getValues()      { return $this->type->getValues(); }
    function  hasDescription() { return !empty($this->description); }
    function  getDescription() { return $this->description; }
    function  isArrayVal()     { return $this->_arrayVal; }
    function  hasAction()      { return !is_null($this->_action); }
    function  isUpload()       { return ($this->type->getTypeName() == 'file'); }

    /**
     * Set a variable option.
     *
     * @param string $option  The option name.
     * @param mixed  $val     The option's value.
     */
    function setOption($option, $val)
    {
        $this->_options[$option] = $val;
    }

    /**
     * Get a variable option's value.
     *
     * @param string $option  The option name.
     *
     * @return mixed          The option's value.
     */
    function getOption($option)
    {
        return isset($this->_options[$option]) ? $this->_options[$option] : null;
    }

    function getInfo(&$vars, &$info)
    {
        return $this->type->getInfo($vars, $this, $info);
    }

    function validate(&$vars, &$message)
    {
        if ($this->_arrayVal) {
            $vals = $this->getValue($vars);
            if (!is_array($vals)) {
                if ($this->required) {
                    $message = _("This field is required.");
                    return false;
                } else {
                    return true;
                }
            }
            foreach ($vals as $i => $value) {
                if ($value === null && $this->required) {
                    $message = _("This field is required.");
                    return false;
                } else {
                    if (!$this->type->isValid($this, $vars, $value, $message)) {
                        return false;
                    }
                }
            }
        } else {
            $value = $this->getValue($vars);
            return $this->type->isValid($this, $vars, $value, $message);
        }

        return true;
    }

    function getValue(&$vars, $index = null)
    {
        if ($this->_arrayVal) {
            $name = str_replace('[]', '', $this->varName);
        } else {
            $name = $this->varName;
        }
        $value = $vars->getExists($name, $wasset);

        if (!$wasset) {
            $value = $this->getDefault();
        }

        if ($this->_arrayVal && !is_null($index)) {
            if (!$wasset && !is_array($value)) {
                $return = $value;
            } else {
                $return = isset($value[$index]) ? $value[$index] : null;
            }
        } else {
            $return = $value;
        }

        if ($this->hasAction()) {
            $this->_action->setValues($vars, $return, $this->_arrayVal);
        }
        return $return;
    }

}
