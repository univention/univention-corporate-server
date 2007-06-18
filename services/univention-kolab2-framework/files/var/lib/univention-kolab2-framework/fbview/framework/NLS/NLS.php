<?php
/**
 * The NLS:: class provides Native Language Support. This includes common
 * methods for handling language detection and selection, timezones, and
 * hostname->country lookups.
 *
 * $Horde: framework/NLS/NLS.php,v 1.72 2004/05/02 21:47:09 chuck Exp $
 *
 * Copyright 1999-2004 Jon Parise <jon@horde.org>
 * Copyright 1999-2004 Chuck Hagenbuch <chuck@horde.org>
 * Copyright 2002-2004 Jan Schneider <jan@horde.org>
 * Copyright 2003-2004 Michael Slusarz <slusarz@bigworm.colorado.edu>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jon Parise <jon@horde.org>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jan Schneider <jan@horde.org>
 * @author  Michael Slusarz <slusarz@bigworm.colorado.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_NLS
 */
class NLS {

    /**
     * Selects the most preferred language for the current client session.
     *
     * @access public
     *
     * @return string  The selected language abbreviation.
     */
    function select()
    {
        global $nls, $prefs;

        $lang = Util::getFormData('new_lang');

        /* First, check if language pref is locked and, if so, set it to its
           value */
        if (isset($prefs) && $prefs->isLocked('language')) {
            $language = $prefs->getValue('language');
        /* Check if the user selected a language from the login screen */
        } elseif (!empty($lang)) {
            $language = $lang;
        /* Check if we have a language set in a cookie */
        } elseif (isset($_SESSION['horde_language'])) {
            $language = $_SESSION['horde_language'];
        /* Use site-wide default, if one is defined */
        } elseif (!empty($nls['defaults']['language'])) {
            $language = $nls['defaults']['language'];
        /* Try browser-accepted languages. */
        } elseif (!empty($_SERVER['HTTP_ACCEPT_LANGUAGE'])) {
            /* The browser supplies a list, so return the first valid one. */
            $browser_langs = explode(',', $_SERVER['HTTP_ACCEPT_LANGUAGE']);
            foreach ($browser_langs as $lang) {
                /* Strip quality value for language */
                if (($pos = strpos($lang, ';')) !== false) {
                    $lang = substr($lang, 0, $pos);
                }
                $lang = NLS::_map(trim($lang));
                if (NLS::isValid($lang)) {
                    $language = $lang;
                    break;
                }
                /* In case no full match, save best guess based on prefix */
                if (!isset($partial_lang) &&
                    NLS::isValid(NLS::_map(substr($lang, 0, 2)))) {
                    $partial_lang = NLS::_map(substr($lang, 0, 2));
                }
            }
        }

        if (!isset($language)) {
            if (isset($partial_lang)) {
                $language = $partial_lang;
            } else {
                /* No dice auto-detecting, default to US English. */
                $language = 'en_US';
            }
        }

        return basename($language);
    }

    /**
     * Sets the language.
     *
     * @access public
     *
     * @param optional string $lang     The language abbriviation.
     */
    function setLang($lang = null)
    {
        include_once HORDE_BASE . '/config/nls.php';

        if (empty($lang) || !NLS::isValid($lang)) {
            $lang = NLS::select();
        }
        $GLOBALS['language'] = $lang;

        /* First try language with the current charset. */
        $lang_charset = $lang . '.' . NLS::getCharset();
        if ($lang_charset != setlocale(LC_ALL, $lang_charset)) {
            /* Next try language with its default charset. */
            global $nls;
            $charset = !empty($nls['charsets'][$lang]) ? $nls['charsets'][$lang] : $nls['defaults']['charset'];
            $lang_charset = $lang . '.' . $charset;
            NLS::_cachedCharset(0, $charset);
            if ($lang_charset != setlocale(LC_ALL, $lang_charset)) {
                /* At last try language solely. */
                $lang_charset = $lang;
                setlocale(LC_ALL, $lang_charset);
            }
        }
        @putenv('LANG=' . $lang_charset);
        @putenv('LANGUAGE=' . $lang_charset);
    }

    /**
     * Sets the gettext domain.
     *
     * @access public
     *
     * @param string $app        The application name.
     * @param string $directory  The directory where the application's
     *                           LC_MESSAGES directory resides.
     * @param string $charset    The charset.
     */
    function setTextdomain($app, $directory, $charset)
    {
        bindtextdomain($app, $directory);
        textdomain($app);

        /* The existence of this function depends on the platform. */
        if (function_exists('bind_textdomain_codeset')) {
           bind_textdomain_codeset($app, $charset);
        }

        if (!headers_sent()) {
            header('Content-Type: text/html; charset=' . $charset);
        }
    }

    /**
     * Determines whether the supplied language is valid.
     *
     * @access public
     *
     * @param string $language  The abbreviated name of the language.
     *
     * @return boolean  True if the language is valid, false if it's not
     *                  valid or unknown.
     */
    function isValid($language)
    {
        return !empty($GLOBALS['nls']['languages'][$language]);
    }

    /**
     * Maps languages with common two-letter codes (such as nl) to the
     * full gettext code (in this case, nl_NL). Returns the language
     * unmodified if it isn't an alias.
     *
     * @access private
     *
     * @param string $language  The language code to map.
     *
     * @return string  The mapped language code.
     */

    function _map($language)
    {
        require_once 'Horde/String.php';

        $aliases = &$GLOBALS['nls']['aliases'];

        // Translate the $language to get broader matches.
        // (eg. de-DE should match de_DE)
        $trans_lang = str_replace('-', '_', $language);
        $lang_parts = explode('_', $trans_lang);
        $trans_lang = String::lower($lang_parts[0]);
        if (isset($lang_parts[1])) {
            $trans_lang .= '_' . String::upper($lang_parts[1]);
        }

        // See if we get a match for this
        if (!empty($aliases[$trans_lang])) {
            return $aliases[$trans_lang];
        }

        // If we get that far down, the language cannot be found.
        // Return $trans_lang.
        return $trans_lang;
    }

    /**
     * Return the charset for the current language.
     *
     * @access public
     *
     * @param optional boolean $no_utf  Do not use UTF-8?
     *
     * @return string  The character set that should be used with the current
     *                 locale settings.
     */
    function getCharset($no_utf = false)
    {
        global $language, $nls;

        /* Get cached results. */
        $cacheKey = intval($no_utf);
        $charset = NLS::_cachedCharset($cacheKey);
        if (!is_null($charset)) {
            return $charset;
        }

        if (!$no_utf) {
            require_once 'Horde/Browser.php';
            $browser = &Browser::singleton();

            if ($browser->hasFeature('utf') &&
                (Util::extensionExists('iconv') ||
                 Util::extensionExists('mbstring'))) {
                NLS::_cachedCharset($cacheKey, 'UTF-8');
                return 'UTF-8';
            }
        }

        $lang_charset = setlocale(LC_ALL, 0);
        if (!strstr($lang_charset, ';') &&
            !strstr($lang_charset, '/')) {
            $lang_charset = explode('.', $lang_charset);
            if ((count($lang_charset) == 2) && !empty($lang_charset[1]) &&
                (!$no_utf || ($lang_charset[1] != 'UTF-8'))) {
                NLS::_cachedCharset($cacheKey, $lang_charset[1]);
                return $lang_charset[1];
            }
        }

        return (!empty($nls['charsets'][$language])) ? $nls['charsets'][$language] : $nls['defaults']['charset'];
    }

    function _cachedCharset($index, $charset = null)
    {
        static $cache;

        if (!isset($cache)) {
            $cache = array();
        }

        if ($charset == null) {
            return isset($cache[$index]) ? $cache[$index] : null;
        } else {
            $cache[$index] = $charset;
        }
    }

    /**
     * Returns the charset to use for outgoing emails.
     *
     * @return string  The preferred charset for outgoing mails based on
     *                 the user's preferences and the current language.
     */
    function getEmailCharset()
    {
        global $prefs, $language, $nls;

        $charset = $prefs->getValue('sending_charset');
        if (!empty($charset)) {
            return $charset;
        }
        return isset($nls['emails'][$language]) ? $nls['emails'][$language] :
               (isset($nls['charsets'][$language]) ? $nls['charsets'][$language] : $nls['defaults']['charset']);
    }

    /**
     * Check to see if character set is valid for htmlspecialchars() calls.
     *
     * @access public
     *
     * @param string $charset  The character set to check.
     *
     * @return boolean  Is charset valid for the current system?
     */
    function checkCharset($charset)
    {
        static $check;

        if (is_null($charset) || empty($charset)) {
            return false;
        }

        if (isset($check[$charset])) {
            return $check[$charset];
        } elseif (!isset($check)) {
            $check = array();
        }

        $valid = true;

        ini_set('track_errors', 1);
        @htmlspecialchars('', ENT_COMPAT, $charset);
        if (isset($php_errormsg)) {
            $valid = false;
        }
        ini_restore('track_errors');

        $check[$charset] = $valid;

        return $valid;
    }

    /**
     * Sets the current timezone, if available.
     *
     * @access public
     */
    function setTimeZone()
    {
        global $prefs;

        $tz = $prefs->getValue('timezone');
        if (!empty($tz)) {
            @putenv('TZ=' . $tz);
        }
    }

    /**
     * Get the locale info returned by localeconv(), but cache it, to
     * avoid repeated calls.
     *
     * @access public
     *
     * @return array  The results of localeconv().
     */
    function getLocaleInfo()
    {
        static $lc_info;

        if (!isset($lc_info)) {
            $lc_info = localeconv();
        }

        return $lc_info;
    }

    /**
     * Get country information from a hostname or IP address.
     *
     * @access public
     *
     * @param string $host  The hostname or IP address.
     *
     * @return mixed  On success, return an array with the following entries:
     *                'code'  =>  Country Code
     *                'name'  =>  Country Name
     *                On failure, return false.
     */
    function getCountryByHost($host)
    {
        global $conf;

        /* List of generic domains that we know is not in the country TLD
           list. See: http://www.iana.org/gtld/gtld.htm */
        $generic = array(
            'aero', 'biz', 'com', 'coop', 'edu', 'gov', 'info', 'int', 'mil',
            'museum', 'name', 'net', 'org', 'pro'
        );

        $checkHost = $host;
        if (preg_match('/^\d+\.\d+\.\d+\.\d+$/', $host)) {
            $checkHost = @gethostbyaddr($host);
        }

        /* Get the TLD of the hostname. */
        $pos = strrpos($checkHost, '.');
        if ($pos === false) {
            return false;
        }
        $domain = String::lower(substr($checkHost, $pos + 1));

        /* Try lookup via TLD first. */
        if (!in_array($domain, $generic)) {
            require 'Horde/NLS/tld.php';
            if (isset($tld[$domain])) {
                return array('code' => $domain, 'name' => $tld[$domain]);
            }
        }

        /* Try GeoIP lookup next. */
        if (!empty($conf['geoip']['datafile'])) {
            require_once 'Horde/NLS/GeoIP.php';
            $geoip = &NLS_GeoIP::singleton($conf['geoip']['datafile']);
            $id = $geoip->countryIdByName($checkHost);
            if (!empty($id)) {
                return array('code' => String::lower($GLOBALS['GEOIP_COUNTRY_CODES'][$id]), 'name' => $GLOBALS['GEOIP_COUNTRY_NAMES'][$id]);
            }
        }

        return false;
    }

    /**
     * Returns a Horde image link to the country flag.
     *
     * @access public
     *
     * @param string $host  The hostname or IP address.
     *
     * @return string  The image URL, or the empty string on error.
     */
    function generateFlagImageByHost($host)
    {
        global $registry;

        $data = NLS::getCountryByHost($host);
        if ($data !== false) {
            $img = $data['code'] . '.gif';
            if (file_exists($registry->getParam('fileroot', 'horde') . '/graphics/flags/' . $img)) {
                return Horde::img($img, $data['name'], '', $registry->getParam('graphics', 'horde') . '/flags');
            } else {
                return '[' . $data['name'] . ']';
            }
        }

        return '';
    }

    /**
     * Returns either a specific or all ISO-3166 country names.
     *
     * @access public
     *
     * @param optional string $code  The ISO 3166 country code.
     *
     * @return mixed  If a country code has been requested will return the
     *                corresponding country name. If empty will return an
     *                array of all the country codes and their names.
     */
    function &getCountryISO($code = '')
    {
        static $countries = array();
        if (empty($countries)) {
            require_once 'Horde/NLS/countries.php';
        }
        if (empty($code)) {
            return $countries;
        } elseif (isset($countries[$code])) {
            return $countries[$code];
        }
        return false;
    }

}
