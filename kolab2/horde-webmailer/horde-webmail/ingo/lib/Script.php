<?php

/**
 * Only filter unseen messages.
 */
define('INGO_SCRIPT_FILTER_UNSEEN', 1);

/**
 * Only filter seen messages.
 */
define('INGO_SCRIPT_FILTER_SEEN', 2);

/**
 * The Ingo_Script:: class provides a common abstracted interface to the
 * script-generation subclasses.
 *
 * $Horde: ingo/lib/Script.php,v 1.30.10.10 2008-09-12 17:00:57 jan Exp $
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author  Brent J. Nordquist <bjn@horde.org>
 * @package Ingo
 */
class Ingo_Script {

    /**
     * The script class' additional parameters.
     *
     * @var array
     */
    var $_params = array();

    /**
     * The list of actions allowed (implemented) for this driver.
     * This SHOULD be defined in each subclass.
     *
     * @var array
     */
    var $_actions = array();

    /**
     * The categories of filtering allowed.
     * This SHOULD be defined in each subclass.
     *
     * @var array
     */
    var $_categories = array();

    /**
     * The list of tests allowed (implemented) for this driver.
     * This SHOULD be defined in each subclass.
     *
     * @var array
     */
    var $_tests = array();

    /**
     * The types of tests allowed (implemented) for this driver.
     * This SHOULD be defined in each subclass.
     *
     * @var array
     */
    var $_types = array();

    /**
     * A list of any special types that this driver supports.
     *
     * @var array
     */
    var $_special_types = array();

    /**
     * Can tests be case sensitive?
     *
     * @var boolean
     */
    var $_casesensitive = false;

    /**
     * Does the driver support setting IMAP flags?
     *
     * @var boolean
     */
    var $_supportIMAPFlags = false;

    /**
     * Does the driver support the stop-script option?
     *
     * @var boolean
     */
    var $_supportStopScript = false;

    /**
     * Can this driver perform on demand filtering?
     *
     * @var boolean
     */
    var $_ondemand = false;

    /**
     * Does the driver require a script file to be generated?
     *
     * @var boolean
     */
    var $_scriptfile = false;

    /**
     * Attempts to return a concrete Ingo_Script instance based on $script.
     *
     * @param string $script  The type of Ingo_Script subclass to return.
     * @param array $params   Hash containing additional paramters to be passed
     *                        to the subclass' constructor.
     *
     * @return Ingo_Script  The newly created concrete Ingo_Script instance, or
     *                      false on error.
     */
    function factory($script, $params = array())
    {
        $script = basename($script);
        include_once dirname(__FILE__) . '/Script/' . $script . '.php';
        $class = 'Ingo_Script_' . $script;
        if (class_exists($class)) {
            return new $class($params);
        } else {
            return PEAR::raiseError(sprintf(_("Unable to load the definition of %s."), $class));
        }
    }

    /**
     * Constructor.
     *
     * @param array $params  A hash containing parameters needed.
     */
    function Ingo_Script($params = array())
    {
        global $registry;

        $this->_params = $params;

        /* Determine if ingo should handle the blacklist. */
        $key = array_search(INGO_STORAGE_ACTION_BLACKLIST, $this->_categories);
        if ($key !== false && ($registry->hasMethod('mail/blacklistFrom') != 'ingo')) {
            unset($this->_categories[$key]);
        }

        /* Determine if ingo should handle the whitelist. */
        $key = array_search(INGO_STORAGE_ACTION_WHITELIST, $this->_categories);
        if ($key !== false && ($registry->hasMethod('mail/whitelistFrom') != 'ingo')) {
            unset($this->_categories[$key]);
        }
    }

    /**
     * Returns a regular expression that should catch mails coming from most
     * daemons, mailing list, newsletters, and other bulk.
     *
     * This is the expression used for procmail's FROM_DAEMON, including all
     * mailinglist headers.
     *
     * @return string  A regular expression.
     */
    function excludeRegexp()
    {
        return '(^(Mailing-List:|List-(Id|Help|Unsubscribe|Subscribe|Owner|Post|Archive):|Precedence:.*(junk|bulk|list)|To: Multiple recipients of|(((Resent-)?(From|Sender)|X-Envelope-From):|>?From)([^>]*[^(.%@a-z0-9])?(Post(ma?(st(e?r)?|n)|office)|(send)?Mail(er)?|daemon|m(mdf|ajordomo)|n?uucp|LIST(SERV|proc)|NETSERV|o(wner|ps)|r(e(quest|sponse)|oot)|b(ounce|bs\.smtp)|echo|mirror|s(erv(ices?|er)|mtp(error)?|ystem)|A(dmin(istrator)?|MMGR|utoanswer))(([^).!:a-z0-9][-_a-z0-9]*)?[%@>\t ][^<)]*(\(.*\).*)?)?$([^>]|$)))';
    }

    /**
     * Returns the available actions for this driver.
     *
     * @return array  The list of available actions.
     */
    function availableActions()
    {
        return $this->_actions;
    }

    /**
     * Returns the available categories for this driver.
     *
     * @return array  The list of categories.
     */
    function availableCategories()
    {
        return $this->_categories;
    }

    /**
     * Returns the available tests for this driver.
     *
     * @return array  The list of tests actions.
     */
    function availableTests()
    {
        return $this->_tests;
    }

    /**
     * Returns the available test types for this driver.
     *
     * @return array  The list of test types.
     */
    function availableTypes()
    {
        return $this->_types;
    }

    /**
     * Returns any test types that are special for this driver.
     *
     * @return array  The list of special types
     */
    function specialTypes()
    {
        return $this->_special_types;
    }

    /**
     * Returns if this driver allows case sensitive searches.
     *
     * @return boolean  Does this driver allow case sensitive searches?
     */
    function caseSensitive()
    {
        return $this->_casesensitive;
    }

    /**
     * Returns if this driver allows IMAP flags to be set.
     *
     * @return boolean  Does this driver allow IMAP flags to be set?
     */
    function imapFlags()
    {
        return $this->_supportIMAPFlags;
    }

    /**
     * Returns if this driver supports the stop-script option.
     *
     * @return boolean  Does this driver support the stop-script option?
     */
    function stopScript()
    {
        return $this->_supportStopScript;
    }

    /**
     * Returns a script previously generated with generate().
     *
     * @abstract
     *
     * @return string  The script.
     */
    function toCode()
    {
        return '';
    }

    /**
     * Can this driver generate a script file?
     *
     * @return boolean  True if generate() is available, false if not.
     */
    function generateAvailable()
    {
        return $this->_scriptfile;
    }

    /**
     * Generates the script to do the filtering specified in
     * the rules.
     *
     * @abstract
     *
     * @return string  The script.
     */
    function generate()
    {
        return '';
    }

    /**
     * Can this driver perform on demand filtering?
     *
     * @return boolean  True if perform() is available, false if not.
     */
    function performAvailable()
    {
        return $this->_ondemand;
    }

    /**
     * Perform the filtering specified in the rules.
     *
     * @abstract
     *
     * @param array $params  The parameter array.
     *
     * @return boolean  True if filtering performed, false if not.
     */
    function perform($params = array())
    {
        return false;
    }

    /**
     * Is the apply() function available?
     *
     * @return boolean  True if apply() is available, false if not.
     */
    function canApply()
    {
        return $this->performAvailable();
    }

    /**
     * Apply the filters now.
     * This is essentially a wrapper around perform() that allows that
     * function to be called from within Ingo ensuring that all necessary
     * parameters are set.
     *
     * @abstract
     *
     * @return boolean  See perform().
     */
    function apply()
    {
        return $this->perform();
    }

    /**
     * Is this a valid rule?
     *
     * @access private
     *
     * @param integer $type  The rule type.
     *
     * @return boolean  Whether the rule is valid or not for this driver.
     */
    function _validRule($type)
    {
        return (!empty($type) && in_array($type, array_merge($this->_categories, $this->_actions)));
    }

}
