<?php
/**
 * Horde optimized interface to the MaxMind IP Address->Country
 * listing.
 *
 * $Horde: framework/NLS/NLS/GeoIP.php,v 1.10.10.11 2009-01-06 15:23:26 jan Exp $
 *
 * Based on PHP geoip.inc library by MaxMind LLC:
 *   http://www.maxmind.com/download/geoip/api/php/
 *
 * Originally based on php version of the geoip library written in May
 * 2002 by jim winstead <jimw@apache.org>
 *
 * Copyright 2003 MaxMind LLC
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @since   Horde 3.0
 * @package Horde_NLS
 */

/* Country list. */
$GLOBALS['GEOIP_COUNTRY_CODES'] = array(
'', 'AP', 'EU', 'AD', 'AE', 'AF', 'AG', 'AI', 'AL', 'AM', 'AN', 'AO', 'AQ',
'AR', 'AS', 'AT', 'AU', 'AW', 'AZ', 'BA', 'BB', 'BD', 'BE', 'BF', 'BG', 'BH',
'BI', 'BJ', 'BM', 'BN', 'BO', 'BR', 'BS', 'BT', 'BV', 'BW', 'BY', 'BZ', 'CA',
'CC', 'CD', 'CF', 'CG', 'CH', 'CI', 'CK', 'CL', 'CM', 'CN', 'CO', 'CR', 'CU',
'CV', 'CX', 'CY', 'CZ', 'DE', 'DJ', 'DK', 'DM', 'DO', 'DZ', 'EC', 'EE', 'EG',
'EH', 'ER', 'ES', 'ET', 'FI', 'FJ', 'FK', 'FM', 'FO', 'FR', 'FX', 'GA', 'UK',
'GD', 'GE', 'GF', 'GH', 'GI', 'GL', 'GM', 'GN', 'GP', 'GQ', 'GR', 'GS', 'GT',
'GU', 'GW', 'GY', 'HK', 'HM', 'HN', 'HR', 'HT', 'HU', 'ID', 'IE', 'IL', 'IN',
'IO', 'IQ', 'IR', 'IS', 'IT', 'JM', 'JO', 'JP', 'KE', 'KG', 'KH', 'KI', 'KM',
'KN', 'KP', 'KR', 'KW', 'KY', 'KZ', 'LA', 'LB', 'LC', 'LI', 'LK', 'LR', 'LS',
'LT', 'LU', 'LV', 'LY', 'MA', 'MC', 'MD', 'MG', 'MH', 'MK', 'ML', 'MM', 'MN',
'MO', 'MP', 'MQ', 'MR', 'MS', 'MT', 'MU', 'MV', 'MW', 'MX', 'MY', 'MZ', 'NA',
'NC', 'NE', 'NF', 'NG', 'NI', 'NL', 'NO', 'NP', 'NR', 'NU', 'NZ', 'OM', 'PA',
'PE', 'PF', 'PG', 'PH', 'PK', 'PL', 'PM', 'PN', 'PR', 'PS', 'PT', 'PW', 'PY',
'QA', 'RE', 'RO', 'RU', 'RW', 'SA', 'SB', 'SC', 'SD', 'SE', 'SG', 'SH', 'SI',
'SJ', 'SK', 'SL', 'SM', 'SN', 'SO', 'SR', 'ST', 'SV', 'SY', 'SZ', 'TC', 'TD',
'TF', 'TG', 'TH', 'TJ', 'TK', 'TM', 'TN', 'TO', 'TP', 'TR', 'TT', 'TV', 'TW',
'TZ', 'UA', 'UG', 'UM', 'US', 'UY', 'UZ', 'VA', 'VC', 'VE', 'VG', 'VI', 'VN',
'VU', 'WF', 'WS', 'YE', 'YT', 'YU', 'ZA', 'ZM', 'ZR', 'ZW', 'A1', 'A2', 'O1'
);

/* Country Names. */
$GLOBALS['GEOIP_COUNTRY_NAMES'] = array(
"", _("Asia/Pacific Region"), _("Europe"), _("Andorra"),
_("United Arab Emirates"), _("Afghanistan"), _("Antigua and Barbuda"),
_("Anguilla"), _("Albania"), _("Armenia"), _("Netherlands Antilles"),
_("Angola"), _("Antarctica"), _("Argentina"), _("American Samoa"),
_("Austria"), _("Australia"), _("Aruba"), _("Azerbaijan"),
_("Bosnia and Herzegovina"), _("Barbados"), _("Bangladesh"), _("Belgium"),
_("Burkina Faso"), _("Bulgaria"), _("Bahrain"), _("Burundi"), _("Benin"),
_("Bermuda"), _("Brunei Darussalam"), _("Bolivia"), _("Brazil"), _("Bahamas"),
_("Bhutan"), _("Bouvet Island"), _("Botswana"), _("Belarus"), _("Belize"),
_("Canada"), _("Cocos (Keeling) Islands"),
_("Congo, The Democratic Republic of the"), _("Central African Republic"),
_("Congo"), _("Switzerland"), _("Cote d'Ivoire"), _("Cook Islands"),
_("Chile"), _("Cameroon"), _("China"), _("Colombia"), _("Costa Rica"),
_("Cuba"), _("Cape Verde"), _("Christmas Island"), _("Cyprus"),
_("Czech Republic"), _("Germany"), _("Djibouti"), _("Denmark"), _("Dominica"),
_("Dominican Republic"), _("Algeria"), _("Ecuador"), _("Estonia"), _("Egypt"),
_("Western Sahara"), _("Eritrea"), _("Spain"), _("Ethiopia"), _("Finland"),
_("Fiji"), _("Falkland Islands (Malvinas)"), _("Micronesia, Federated States of"),
_("Faroe Islands"), _("France"), _("France, Metropolitan"), _("Gabon"),
_("United Kingdom"), _("Grenada"), _("Georgia"), _("French Guiana"),
_("Ghana"), _("Gibraltar"), _("Greenland"), _("Gambia"), _("Guinea"),
_("Guadeloupe"), _("Equatorial Guinea"), _("Greece"),
_("South Georgia and the South Sandwich Islands"), _("Guatemala"), _("Guam"),
_("Guinea-Bissau"), _("Guyana"), _("Hong Kong"),
_("Heard Island and McDonald Islands"), _("Honduras"), _("Croatia"),
_("Haiti"), _("Hungary"), _("Indonesia"), _("Ireland"), _("Israel"),
_("India"), _("British Indian Ocean Territory"), _("Iraq"),
_("Iran, Islamic Republic of"), _("Iceland"), _("Italy"), _("Jamaica"),
_("Jordan"), _("Japan"), _("Kenya"), _("Kyrgyzstan"), _("Cambodia"),
_("Kiribati"), _("Comoros"), _("Saint Kitts and Nevis"),
_("Korea, Democratic People's Republic of"), _("Korea, Republic of"),
_("Kuwait"), _("Cayman Islands"), _("Kazakhstan"),
_("Lao People's Democratic Republic"), _("Lebanon"), _("Saint Lucia"),
_("Liechtenstein"), _("Sri Lanka"), _("Liberia"), _("Lesotho"),
_("Lithuania"), _("Luxembourg"), _("Latvia"), _("Libyan Arab Jamahiriya"),
_("Morocco"), _("Monaco"), _("Moldova, Republic of"), _("Madagascar"),
_("Marshall Islands"), _("Macedonia, The Former Yugoslav Republic of"),
_("Mali"), _("Myanmar"), _("Mongolia"), _("Macao"),
_("Northern Mariana Islands"), _("Martinique"), _("Mauritania"),
_("Montserrat"), _("Malta"), _("Mauritius"), _("Maldives"), _("Malawi"),
_("Mexico"), _("Malaysia"), _("Mozambique"), _("Namibia"), _("New Caledonia"),
_("Niger"), _("Norfolk Island"), _("Nigeria"), _("Nicaragua"),
_("Netherlands"), _("Norway"), _("Nepal"), _("Nauru"), _("Niue"),
_("New Zealand"), _("Oman"), _("Panama"), _("Peru"), _("French Polynesia"),
_("Papua New Guinea"), _("Philippines"), _("Pakistan"), _("Poland"),
_("Saint Pierre and Miquelon"), _("Pitcairn"), _("Puerto Rico"),
_("Palestinian Territory, Occupied"), _("Portugal"), _("Palau"),
_("Paraguay"), _("Qatar"), _("Reunion"), _("Romania"),
_("Russian Federation"), _("Rwanda"), _("Saudi Arabia"), _("Solomon Islands"),
_("Seychelles"), _("Sudan"), _("Sweden"), _("Singapore"), _("Saint Helena"),
_("Slovenia"), _("Svalbard and Jan Mayen"), _("Slovakia"), _("Sierra Leone"),
_("San Marino"), _("Senegal"), _("Somalia"), _("Suriname"),
_("Sao Tome and Principe"), _("El Salvador"), _("Syrian Arab Republic"),
_("Swaziland"), _("Turks and Caicos Islands"), _("Chad"),
_("French Southern Territories"), _("Togo"), _("Thailand"), _("Tajikistan"),
_("Tokelau"), _("Turkmenistan"), _("Tunisia"), _("Tonga"), _("Timor-Leste"),
_("Turkey"), _("Trinidad and Tobago"), _("Tuvalu"), _("Taiwan"),
_("Tanzania, United Republic of"), _("Ukraine"), _("Uganda"),
_("United States Minor Outlying Islands"), _("United States"), _("Uruguay"),
_("Uzbekistan"), _("Holy See (Vatican City State)"),
_("Saint Vincent and the Grenadines"), _("Venezuela"),
_("Virgin Islands, British"), _("Virgin Islands, U.S."), _("Viet Nam"),
_("Vanuatu"), _("Wallis and Futuna"), _("Samoa"), _("Yemen"), _("Mayotte"),
_("Yugoslavia"), _("South Africa"), _("Zambia"), _("Zaire"), _("Zimbabwe"),
_("Anonymous Proxy"), _("Satellite Provider"), _("Other")
);

define('GEOIP_COUNTRY_BEGIN', 16776960);
define('STRUCTURE_INFO_MAX_SIZE', 20);
define('STANDARD_RECORD_LENGTH', 3);

class NLS_GeoIP {

    /**
     * The location of the GeoIP database.
     *
     * @var string
     */
    var $_datafile;

    /**
     * The open filehandle to the GeoIP database.
     *
     * @var resource
     */
    var $_filehandle;

    /**
     * Returns a reference to the global NLS_GeoIP object, only creating it
     * if it doesn't already exist.
     *
     * This method must be invoked as:
     *   $geoip = &GeoIP::singleton($datafile);
     *
     * @param string $datafile  The location of the GeoIP database.
     *
     * @return object NLS_GeoIP  The NLS_GeoIP instance.
     */
    function &singleton($datafile)
    {
        static $instance;

        if (!isset($instance)) {
            $instance = new NLS_GeoIP($datafile);
        }

        return $instance;
    }

    /**
     * Create a NLS_GeoIP instance (Constructor).
     *
     * @param string $datafile  The location of the GeoIP database.
     */
    function NLS_GeoIP($datafile)
    {
        $this->_datafile = $datafile;
    }

    /**
     * Open the GeoIP database.
     *
     * @access private
     *
     * @return boolean  False on error.
     */
    function _open()
    {
        /* Return if we already have an object. */
        if (!empty($this->_filehandle)) {
            return true;
        }

        /* Return if no datafile specified. */
        if (empty($this->_datafile)) {
            return false;
        }

        $this->_filehandle = fopen($this->_datafile, 'rb');
        if (!$this->_filehandle) {
            return false;
        }

        $filepos = ftell($this->_filehandle);
        fseek($this->_filehandle, -3, SEEK_END);
        for ($i = 0; $i < STRUCTURE_INFO_MAX_SIZE; $i++) {
            $delim = fread($this->_filehandle, 3);
            if ($delim == (chr(255) . chr(255) . chr(255))) {
                break;
            } else {
                fseek($this->_filehandle, -4, SEEK_CUR);
            }
        }
        fseek($this->_filehandle, $filepos, SEEK_SET);

        return true;
    }

    /**
     * Returns the country ID and Name for a given hostname.
     *
     * @since Horde 3.2
     *
     * @param string $name  The hostname.
     *
     * @return mixed  An array with 'code' as the country code and 'name' as
     *                the country name, or false if not found.
     */
    function getCountryInfo($name)
    {
        if (Util::extensionExists('geoip')) {
            $id = @geoip_country_code_by_name($name);
            $cname = @geoip_country_name_by_name($name);
            return (!empty($id) && !empty($cname)) ?
                array('code' => String::lower($id), 'name' => $cname):
                false;
        }

        $id = $this->countryIdByName($name);
        if (!empty($id)) {
            return array('code' => String::lower($GLOBALS['GEOIP_COUNTRY_CODES'][$id]), 'name' => $GLOBALS['GEOIP_COUNTRY_NAMES'][$id]);
        }
        return false;
    }

    /**
     * Returns the country ID for a hostname.
     *
     * @param string $name  The hostname.
     *
     * @return integer  The GeoIP country ID.
     */
    function countryIdByName($name)
    {
        if (!$this->_open()) {
            return false;
        }
        $addr = gethostbyname($name);
        if (!$addr || ($addr == $name)) {
            return false;
        }
        return $this->countryIdByAddr($addr);
    }

    /**
     * Returns the country abbreviation (2-letter) for a hostname.
     *
     * @param string $name  The hostname.
     *
     * @return integer  The country abbreviation.
     */
    function countryCodeByName($name)
    {
        if ($this->_open()) {
            $country_id = $this->countryIdByName($name);
            if ($country_id !== false) {
                return $GLOBALS['GEOIP_COUNTRY_CODES'][$country_id];
            }
        }
        return false;
    }

    /**
     * Returns the country name for a hostname.
     *
     * @param string $name  The hostname.
     *
     * @return integer  The country name.
     */
    function countryNameByName($name)
    {
        if ($this->_open()) {
            $country_id = $this->countryIdByName($name);
            if ($country_id !== false) {
                return $GLOBALS['GEOIP_COUNTRY_NAMES'][$country_id];
            }
        }
        return false;
    }

    /**
     * Returns the country ID for an IP Address.
     *
     * @param string $addr  The IP Address.
     *
     * @return integer  The GeoIP country ID.
     */
    function countryIdByAddr($addr)
    {
        if (!$this->_open()) {
            return false;
        }
        $ipnum = ip2long($addr);
        return ($this->_seekCountry($ipnum) - GEOIP_COUNTRY_BEGIN);
    }

    /**
     * Returns the country abbreviation (2-letter) for an IP Address.
     *
     * @param string $addr  The IP Address.
     *
     * @return integer  The country abbreviation.
     */
    function countryCodeByAddr($addr)
    {
        if ($this->_open()) {
            $country_id = $this->countryIdByAddr($addr);
            if ($country_id !== false) {
                return $GLOBALS['GEOIP_COUNTRY_CODES'][$country_id];
            }
        }
        return false;
    }

    /**
     * Returns the country name for an IP address.
     *
     * @param string $addr  The IP address.
     *
     * @return mixed  The country name.
     */
    function countryNameByAddr($addr)
    {
        if ($this->_open()) {
            $country_id = $this->countryIdByAddr($addr);
            if ($country_id !== false) {
                return $GLOBALS['GEOIP_COUNTRY_NAMES'][$country_id];
            }
        }
        return false;
    }

    /**
     * Finds a country by IP Address in the GeoIP database.
     *
     * @access private
     *
     * @param string $ipnum  The IP Address to search for.
     *
     * @return mixed  The country ID or false if not found.
     *                Returns PEAR_Error on error.
     */
    function _seekCountry($ipnum)
    {
        $offset = 0;
        for ($depth = 31; $depth >= 0; --$depth) {
            if (fseek($this->_filehandle, 2 * STANDARD_RECORD_LENGTH * $offset, SEEK_SET) != 0) {
                return PEAR::raiseError('fseek failed');
            }
            $buf = fread($this->_filehandle, 2 * STANDARD_RECORD_LENGTH);
            $x = array(0, 0);
            for ($i = 0; $i < 2; ++$i) {
                for ($j = 0; $j < STANDARD_RECORD_LENGTH; ++$j) {
                    $x[$i] += ord($buf[STANDARD_RECORD_LENGTH * $i + $j]) << ($j * 8);
                }
            }
            if ($ipnum & (1 << $depth)) {
                if ($x[1] >= GEOIP_COUNTRY_BEGIN) {
                    return $x[1];
                }
                $offset = $x[1];
            } else {
                if ($x[0] >= GEOIP_COUNTRY_BEGIN) {
                    return $x[0];
                }
                $offset = $x[0];
            }
        }

        return false;
    }

}
