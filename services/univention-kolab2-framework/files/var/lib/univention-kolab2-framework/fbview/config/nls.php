<?php
/**
 * NLS (National Language Support) configuration file.
 *
 * $Horde: horde/config/nls.php.dist,v 1.57 2004/05/21 17:08:50 jan Exp $
 */

/**
 ** Defaults
 **/

/* The language to fall back on if we cannot determine one any other
   way (user choice or preferences). If empty, we will try to negotiate
   with the browser using HTTP_ACCEPT_LANGUAGE. */
$nls['defaults']['language'] = '';

/* The charset to fall back on if we cannot determine one any other
   way (chosen language, HTTP_ACCEPT_CHARSETS). */
$nls['defaults']['charset'] = 'ISO-8859-1';


/**
 ** Language
 **/

$nls['languages']['ar_OM'] = 'Arabic (Oman) (&#x0627;&#x0644;&#x0639;&#x0631;&#x0628;&#x064a;&#x0629;)';
$nls['languages']['ar_SY'] = 'Arabic (Syria) (&#x0627;&#x0644;&#x0639;&#x0631;&#x0628;&#x064a;&#x0629;)';
$nls['languages']['id_ID'] = 'Bahasa Indonesia';
$nls['languages']['bg_BG'] = 'Bulgarian (&#x0411;&#x044a;&#x043b;&#x0433;&#x0430;&#x0440;&#x0441;&#x043a;&#x0438;)';
$nls['languages']['ca_ES'] = 'Catal&agrave;';
$nls['languages']['zh_CN'] = 'Chinese (Simplified) (&#x7b80;&#x4f53;&#x4e2d;&#x6587;)';
$nls['languages']['zh_TW'] = 'Chinese (Traditional) (&#x6b63;&#x9ad4;&#x4e2d;&#x6587;)';
$nls['languages']['cs_CZ'] = 'Czech (&#x010c;esky)';
$nls['languages']['da_DK'] = 'Dansk';
$nls['languages']['de_DE'] = 'Deutsch';
$nls['languages']['en_US'] = 'English (American)';
$nls['languages']['en_GB'] = 'English (British)';
$nls['languages']['en_CA'] = 'English (Canadian)';
$nls['languages']['es_ES'] = 'Espa&ntilde;ol';
$nls['languages']['et_EE'] = 'Eesti';
$nls['languages']['fr_FR'] = 'Fran&ccedil;ais';
$nls['languages']['gl_ES'] = 'Galego';
$nls['languages']['el_GR'] = 'Greek (&#x0395;&#x03bb;&#x03bb;&#x03b7;&#x03bd;&#x03b9;&#x03ba;&#x03ac;)';
$nls['languages']['is_IS'] = '&Iacute;slenska';
$nls['languages']['it_IT'] = 'Italiano';
$nls['languages']['ja_JP'] = 'Japanese (&#x65e5;&#x672c;&#x8a9e;)';
$nls['languages']['ko_KR'] = 'Korean (&#xd55c;&#xad6d;&#xc5b4;)';
$nls['languages']['lv_LV'] = 'Latvie&#x0161;u';
$nls['languages']['lt_LT'] = 'Lietuvi&#x0173;';
$nls['languages']['mk_MK'] = 'Macedonian (&#x041c;&#x0430;&#x043a;&#x0435;&#x0434;&#x043e;&#x043d;&#x0441;&#x043a;&#x0438;)';
$nls['languages']['hu_HU'] = 'Magyar';
$nls['languages']['nl_NL'] = 'Nederlands';
$nls['languages']['nb_NO'] = 'Norsk bokm&aring;l';
$nls['languages']['nn_NO'] = 'Norsk nynorsk';
$nls['languages']['pl_PL'] = 'Polski';
$nls['languages']['pt_PT'] = 'Portugu&ecirc;s';
$nls['languages']['pt_BR'] = 'Portugu&ecirc;s Brasileiro';
$nls['languages']['ro_RO'] = 'Rom&acirc;n&auml;';
$nls['languages']['ru_RU'] = 'Russian (&#x0420;&#x0443;&#x0441;&#x0441;&#x043a;&#x0438;&#x0439;)';
$nls['languages']['sk_SK'] = 'Slovak (Sloven&#x010d;ina)';
$nls['languages']['sl_SI'] = 'Slovenian (Sloven&#x0161;&#x010d;ina)';
$nls['languages']['fi_FI'] = 'Suomi';
$nls['languages']['sv_SE'] = 'Svenska';
$nls['languages']['th_TH'] = 'Thai (&#x0e44;&#x0e17;&#x0e22;)';
$nls['languages']['tr_TR'] = 'T&uuml;rk&ccedil;e';
$nls['languages']['uk_UA'] = 'Ukrainian (&#x0423;&#x043a;&#x0440;&#x0430;&#x0457;&#x043d;&#x0441;&#x044c;&#x043a;&#x0430;)';


/**
 ** Aliases for languages with different browser and gettext codes
 **/

$nls['aliases']['ar'] = 'ar_SY';
$nls['aliases']['bg'] = 'bg_BG';
$nls['aliases']['ca'] = 'ca_ES';
$nls['aliases']['cs'] = 'cs_CZ';
$nls['aliases']['da'] = 'da_DK';
$nls['aliases']['de'] = 'de_DE';
$nls['aliases']['el'] = 'el_GR';
$nls['aliases']['en'] = 'en_US';
$nls['aliases']['es'] = 'es_ES';
$nls['aliases']['et'] = 'et_EE';
$nls['aliases']['fi'] = 'fi_FI';
$nls['aliases']['fr'] = 'fr_FR';
$nls['aliases']['gl'] = 'gl_ES';
$nls['aliases']['hu'] = 'hu_HU';
$nls['aliases']['id'] = 'id_ID';
$nls['aliases']['is'] = 'is_IS';
$nls['aliases']['it'] = 'it_IT';
$nls['aliases']['ja'] = 'ja_JP';
$nls['aliases']['ko'] = 'ko_KR';
$nls['aliases']['lt'] = 'lt_LT';
$nls['aliases']['lv'] = 'lv_LV';
$nls['aliases']['mk'] = 'mk_MK';
$nls['aliases']['nl'] = 'nl_NL';
$nls['aliases']['nn'] = 'nn_NO';
$nls['aliases']['no'] = 'nb_NO';
$nls['aliases']['pl'] = 'pl_PL';
$nls['aliases']['pt'] = 'pt_PT';
$nls['aliases']['ro'] = 'ro_RO';
$nls['aliases']['ru'] = 'ru_RU';
$nls['aliases']['sk'] = 'sk_SK';
$nls['aliases']['sl'] = 'sl_SI';
$nls['aliases']['sv'] = 'sv_SE';
$nls['aliases']['th'] = 'th_TH';
$nls['aliases']['tr'] = 'tr_TR';
$nls['aliases']['uk'] = 'uk_UA';


/**
 ** Charsets
 **/

$nls['charsets']['ar_OM'] = 'windows-1256';
$nls['charsets']['ar_SY'] = 'windows-1256';
$nls['charsets']['bg_BG'] = 'windows-1251';
$nls['charsets']['cs_CZ'] = 'ISO-8859-2';
$nls['charsets']['el_GR'] = 'ISO-8859-7';
$nls['charsets']['hu_HU'] = 'ISO-8859-2';
$nls['charsets']['ja_JP'] = 'SHIFT_JIS';
$nls['charsets']['ko_KR'] = 'EUC-KR';
$nls['charsets']['lt_LT'] = 'ISO-8859-13';
$nls['charsets']['lv_LV'] = 'windows-1257';
$nls['charsets']['mk_MK'] = 'ISO-8859-5';
$nls['charsets']['pl_PL'] = 'ISO-8859-2';
$nls['charsets']['ru_RU'] = 'windows-1251';
$nls['charsets']['ru_RU.KOI8-R'] = 'KOI8-R';
$nls['charsets']['sk_SK'] = 'ISO-8859-2';
$nls['charsets']['sl_SI'] = 'ISO-8859-2';
$nls['charsets']['th_TH'] = 'TIS-620';
$nls['charsets']['tr_TR'] = 'ISO-8859-9';
$nls['charsets']['uk_UA'] = 'KOI8-U';
$nls['charsets']['zh_CN'] = 'GB2312';
$nls['charsets']['zh_TW'] = 'BIG5';


/**
 ** Multibyte charsets
 **/

$nls['multibyte']['BIG5'] = true;
$nls['multibyte']['EUC-KR'] = true;
$nls['multibyte']['GB2312'] = true;
$nls['multibyte']['SHIFT_JIS'] = true;
$nls['multibyte']['UTF-8'] = true;


/**
 ** Right-to-left charsets
 **/

$nls['rtl']['windows-1256'] = true;


/**
 ** Preferred charsets for email traffic if not the languages' default charsets.
 **/

$nls['emails']['ja_JP'] = 'ISO-2022-JP';


/**
 ** Available charsets for outgoing email traffic.
 **/

$nls['encodings']['windows-1256'] = _("Arabic (Windows-1256)");
$nls['encodings']['ARMSCII-8'] = _("Armenian (ARMSCII-8)");
$nls['encodings']['ISO-8859-13'] = _("Baltic (ISO-8859-13)");
$nls['encodings']['ISO-8859-14'] = _("Celtic (ISO-8859-14)");
$nls['encodings']['ISO-8859-2'] = _("Central European (ISO-8859-2)");
$nls['encodings']['GB2312'] = _("Chinese Simplified (GB2312)");
$nls['encodings']['BIG5'] = _("Chinese Traditional (Big5)");
$nls['encodings']['KOI8-R'] = _("Cyrillic (KOI8-R)");
$nls['encodings']['windows-1251'] = _("Cyrillic (Windows-1251)");
$nls['encodings']['KOI8-U'] = _("Cyrillic/Ukrainian (KOI8-U)");
$nls['encodings']['ISO-8859-7'] = _("Greek (ISO-8859-7)");
$nls['encodings']['ISO-8859-8-I'] = _("Hebrew (ISO-8859-8-I)");
$nls['encodings']['ISO-2022-JP'] = _("Japanese (ISO-2022-JP)");
$nls['encodings']['EUC-KR'] = _("Korean (EUC-KR)");
$nls['encodings']['ISO-8859-10'] = _("Nordic (ISO-8859-10)");
$nls['encodings']['ISO-8859-3'] = _("South European (ISO-8859-3)");
$nls['encodings']['TIS-620'] = _("Thai (TIS-620)");
$nls['encodings']['ISO-8859-9'] = _("Turkish (ISO-8859-9)");
$nls['encodings']['UTF-8'] = _("Unicode (UTF-8)");
$nls['encodings']['VISCII'] = _("Vietnamese (VISCII)");
$nls['encodings']['ISO-8859-1'] = _("Western (ISO-8859-1)");
$nls['encodings']['ISO-8859-15'] = _("Western (ISO-8859-15)");
asort($nls['encodings']);


/**
 ** Multi-language spelling support
 **/

$nls['spelling']['cs_CZ'] = '-T latin2 -d czech';
$nls['spelling']['da_DK'] = '-d dansk';
$nls['spelling']['de_DE'] = '-T latin1 -d deutsch';
$nls['spelling']['el_GR'] = '-T latin1 -d ellinika';
$nls['spelling']['en_CA'] = '-d canadian';
$nls['spelling']['en_GB'] = '-d british';
$nls['spelling']['en_US'] = '-d american';
$nls['spelling']['es_ES'] = '-d espanol';
$nls['spelling']['fr_FR'] = '-d francais';
$nls['spelling']['it_IT'] = '-T latin1 -d italian';
$nls['spelling']['nl_NL'] = '-d nederlands';
$nls['spelling']['pl_PL'] = '-d polish';
$nls['spelling']['pt_BR'] = '-d br';
$nls['spelling']['pt_PT'] = '-T latin1 -d portuguese';
$nls['spelling']['ru_RU'] = '-d russian';
$nls['spelling']['sl_SI'] = '-d slovensko';
$nls['spelling']['sv_SE'] = '-d svenska';

$GLOBALS['nls'] = &$nls;


/**
 ** Timezones
 **/

$tz['Africa/Abidjan'] = 'Africa/Abidjan';
$tz['Africa/Accra'] = 'Africa/Accra';
$tz['Africa/Addis_Ababa'] = 'Africa/Addis Ababa';
$tz['Africa/Algiers'] = 'Africa/Algiers';
$tz['Africa/Asmera'] = 'Africa/Asmera';
$tz['Africa/Bamako'] = 'Africa/Bamako';
$tz['Africa/Bangui'] = 'Africa/Bangui';
$tz['Africa/Banjul'] = 'Africa/Banjul';
$tz['Africa/Bissau'] = 'Africa/Bissau';
$tz['Africa/Blantyre'] = 'Africa/Blantyre';
$tz['Africa/Brazzaville'] = 'Africa/Brazzaville';
$tz['Africa/Bujumbura'] = 'Africa/Bujumbura';
$tz['Africa/Cairo'] = 'Africa/Cairo';
$tz['Africa/Casablanca'] = 'Africa/Casablanca';
$tz['Africa/Ceuta'] = 'Africa/Ceuta';
$tz['Africa/Conakry'] = 'Africa/Conakry';
$tz['Africa/Dakar'] = 'Africa/Dakar';
$tz['Africa/Dar_es_Salaam'] = 'Africa/Dar es Salaam';
$tz['Africa/Djibouti'] = 'Africa/Djibouti';
$tz['Africa/Douala'] = 'Africa/Douala';
$tz['Africa/El_Aaiun'] = 'Africa/El Aaiun';
$tz['Africa/Freetown'] = 'Africa/Freetown';
$tz['Africa/Gaborone'] = 'Africa/Gaborone';
$tz['Africa/Harare'] = 'Africa/Harare';
$tz['Africa/Johannesburg'] = 'Africa/Johannesburg';
$tz['Africa/Kampala'] = 'Africa/Kampala';
$tz['Africa/Khartoum'] = 'Africa/Khartoum';
$tz['Africa/Kigali'] = 'Africa/Kigali';
$tz['Africa/Kinshasa'] = 'Africa/Kinshasa';
$tz['Africa/Lagos'] = 'Africa/Lagos';
$tz['Africa/Libreville'] = 'Africa/Libreville';
$tz['Africa/Lome'] = 'Africa/Lome';
$tz['Africa/Luanda'] = 'Africa/Luanda';
$tz['Africa/Lubumbashi'] = 'Africa/Lubumbashi';
$tz['Africa/Lusaka'] = 'Africa/Lusaka';
$tz['Africa/Malabo'] = 'Africa/Malabo';
$tz['Africa/Maputo'] = 'Africa/Maputo';
$tz['Africa/Maseru'] = 'Africa/Maseru';
$tz['Africa/Mbabane'] = 'Africa/Mbabane';
$tz['Africa/Mogadishu'] = 'Africa/Mogadishu';
$tz['Africa/Monrovia'] = 'Africa/Monrovia';
$tz['Africa/Nairobi'] = 'Africa/Nairobi';
$tz['Africa/Ndjamena'] = 'Africa/Ndjamena';
$tz['Africa/Niamey'] = 'Africa/Niamey';
$tz['Africa/Nouakchott'] = 'Africa/Nouakchott';
$tz['Africa/Ouagadougou'] = 'Africa/Ouagadougou';
$tz['Africa/Porto-Novo'] = 'Africa/Porto-Novo';
$tz['Africa/Sao_Tome'] = 'Africa/Sao Tome';
$tz['Africa/Timbuktu'] = 'Africa/Timbuktu';
$tz['Africa/Tripoli'] = 'Africa/Tripoli';
$tz['Africa/Tunis'] = 'Africa/Tunis';
$tz['Africa/Windhoek'] = 'Africa/Windhoek';
$tz['America/Adak'] = 'America/Adak';
$tz['America/Anchorage'] = 'America/Anchorage';
$tz['America/Anguilla'] = 'America/Anguilla';
$tz['America/Antigua'] = 'America/Antigua';
$tz['America/Araguaina'] = 'America/Araguaina';
$tz['America/Aruba'] = 'America/Aruba';
$tz['America/Asuncion'] = 'America/Asuncion';
$tz['America/Barbados'] = 'America/Barbados';
$tz['America/Belem'] = 'America/Belem';
$tz['America/Belize'] = 'America/Belize';
$tz['America/Boa_Vista'] = 'America/Boa Vista';
$tz['America/Bogota'] = 'America/Bogota';
$tz['America/Boise'] = 'America/Boise';
$tz['America/Buenos_Aires'] = 'America/Buenos Aires';
$tz['America/Cambridge_Bay'] = 'America/Cambridge Bay';
$tz['America/Cancun'] = 'America/Cancun';
$tz['America/Caracas'] = 'America/Caracas';
$tz['America/Catamarca'] = 'America/Catamarca';
$tz['America/Cayenne'] = 'America/Cayenne';
$tz['America/Cayman'] = 'America/Cayman';
$tz['America/Chicago'] = 'America/Chicago';
$tz['America/Chihuahua'] = 'America/Chihuahua';
$tz['America/Cordoba'] = 'America/Cordoba';
$tz['America/Costa_Rica'] = 'America/Costa Rica';
$tz['America/Cuiaba'] = 'America/Cuiaba';
$tz['America/Curacao'] = 'America/Curacao';
$tz['America/Dawson'] = 'America/Dawson';
$tz['America/Dawson_Creek'] = 'America/Dawson Creek';
$tz['America/Denver'] = 'America/Denver';
$tz['America/Detroit'] = 'America/Detroit';
$tz['America/Dominica'] = 'America/Dominica';
$tz['America/Edmonton'] = 'America/Edmonton';
$tz['America/Eirunepe'] = 'America/Eirunepe';
$tz['America/El_Salvador'] = 'America/El Salvador';
$tz['America/Fortaleza'] = 'America/Fortaleza';
$tz['America/Glace_Bay'] = 'America/Glace Bay';
$tz['America/Godthab'] = 'America/Godthab';
$tz['America/Goose_Bay'] = 'America/Goose Bay';
$tz['America/Grand_Turk'] = 'America/Grand Turk';
$tz['America/Grenada'] = 'America/Grenada';
$tz['America/Guadeloupe'] = 'America/Guadeloupe';
$tz['America/Guatemala'] = 'America/Guatemala';
$tz['America/Guayaquil'] = 'America/Guayaquil';
$tz['America/Guyana'] = 'America/Guyana';
$tz['America/Halifax'] = 'America/Halifax';
$tz['America/Havana'] = 'America/Havana';
$tz['America/Hermosillo'] = 'America/Hermosillo';
$tz['America/Indiana/Knox'] = 'America/Indiana/Knox';
$tz['America/Indiana/Marengo'] = 'America/Indiana/Marengo';
$tz['America/Indiana/Vevay'] = 'America/Indiana/Vevay';
$tz['America/Indianapolis'] = 'America/Indianapolis';
$tz['America/Inuvik'] = 'America/Inuvik';
$tz['America/Iqaluit'] = 'America/Iqaluit';
$tz['America/Jamaica'] = 'America/Jamaica';
$tz['America/Jujuy'] = 'America/Jujuy';
$tz['America/Juneau'] = 'America/Juneau';
$tz['America/Kentucky/Monticello'] = 'America/Kentucky/Monticello';
$tz['America/La_Paz'] = 'America/La Paz';
$tz['America/Lima'] = 'America/Lima';
$tz['America/Los_Angeles'] = 'America/Los Angeles';
$tz['America/Louisville'] = 'America/Louisville';
$tz['America/Maceio'] = 'America/Maceio';
$tz['America/Managua'] = 'America/Managua';
$tz['America/Manaus'] = 'America/Manaus';
$tz['America/Martinique'] = 'America/Martinique';
$tz['America/Mazatlan'] = 'America/Mazatlan';
$tz['America/Mendoz'] = 'America/Mendoz';
$tz['America/Menominee'] = 'America/Menominee';
$tz['America/Merida'] = 'America/Merida';
$tz['America/Mexico_City'] = 'America/Mexico City';
$tz['America/Miquelon'] = 'America/Miquelon';
$tz['America/Monterrey'] = 'America/Monterrey';
$tz['America/Montevideo'] = 'America/Montevideo';
$tz['America/Montreal'] = 'America/Montreal';
$tz['America/Montserrat'] = 'America/Montserrat';
$tz['America/Nassau'] = 'America/Nassau';
$tz['America/New_York'] = 'America/New York';
$tz['America/Nipigon'] = 'America/Nipigon';
$tz['America/Nome'] = 'America/Nome';
$tz['America/Noronha'] = 'America/Noronha';
$tz['America/Panama'] = 'America/Panama';
$tz['America/Pangnirtung'] = 'America/Pangnirtung';
$tz['America/Paramaribo'] = 'America/Paramaribo';
$tz['America/Phoenix'] = 'America/Phoenix';
$tz['America/Port-au-Prince'] = 'America/Port-au-Prince';
$tz['America/Porto_Velho'] = 'America/Porto Velho';
$tz['America/Port_of_Spain'] = 'America/Port of Spain';
$tz['America/Puerto_Rico'] = 'America/Puerto Rico';
$tz['America/Rainy_River'] = 'America/Rainy River';
$tz['America/Rankin_Inlet'] = 'America/Rankin Inlet';
$tz['America/Recife'] = 'America/Recife';
$tz['America/Regina'] = 'America/Regina';
$tz['America/Rio_Branco'] = 'America/Rio Branco';
$tz['America/Rosario'] = 'America/Rosario';
$tz['America/Santiago'] = 'America/Santiago';
$tz['America/Santo_Domingo'] = 'America/Santo Domingo';
$tz['America/Sao_Paulo'] = 'America/Sao Paulo';
$tz['America/Scoresbysund'] = 'America/Scoresbysund';
$tz['America/Shiprock'] = 'America/Shiprock';
$tz['America/St_Johns'] = 'America/St Johns';
$tz['America/St_Kitts'] = 'America/St Kitts';
$tz['America/St_Lucia'] = 'America/St Lucia';
$tz['America/St_Thomas'] = 'America/St Thomas';
$tz['America/St_Vincent'] = 'America/St Vincent';
$tz['America/Swift_Current'] = 'America/Swift Current';
$tz['America/Tegucigalpa'] = 'America/Tegucigalpa';
$tz['America/Thule'] = 'America/Thule';
$tz['America/Thunder_Bay'] = 'America/Thunder Bay';
$tz['America/Tijuana'] = 'America/Tijuana';
$tz['America/Tortola'] = 'America/Tortola';
$tz['America/Vancouver'] = 'America/Vancouver';
$tz['America/Whitehorse'] = 'America/Whitehorse';
$tz['America/Winnipeg'] = 'America/Winnipeg';
$tz['America/Yakutat'] = 'America/Yakutat';
$tz['America/Yellowknife'] = 'America/Yellowknife';
$tz['Antarctica/Casey'] = 'Antarctica/Casey';
$tz['Antarctica/Davis'] = 'Antarctica/Davis';
$tz['Antarctica/DumontDUrville'] = 'Antarctica/DumontDUrville';
$tz['Antarctica/Mawson'] = 'Antarctica/Mawson';
$tz['Antarctica/McMurdo'] = 'Antarctica/McMurdo';
$tz['Antarctica/Palmer'] = 'Antarctica/Palmer';
$tz['Antarctica/South_Pole'] = 'Antarctica/South Pole';
$tz['Antarctica/Syowa'] = 'Antarctica/Syowa';
$tz['Antarctica/Vostok'] = 'Antarctica/Vostok';
$tz['Arctic/Longyearbyen'] = 'Arctic/Longyearbyen';
$tz['Asia/Aden'] = 'Asia/Aden';
$tz['Asia/Almaty'] = 'Asia/Almaty';
$tz['Asia/Amman'] = 'Asia/Amman';
$tz['Asia/Anadyr'] = 'Asia/Anadyr';
$tz['Asia/Aqtau'] = 'Asia/Aqtau';
$tz['Asia/Aqtobe'] = 'Asia/Aqtobe';
$tz['Asia/Ashgabat'] = 'Asia/Ashgabat';
$tz['Asia/Baghdad'] = 'Asia/Baghdad';
$tz['Asia/Bahrain'] = 'Asia/Bahrain';
$tz['Asia/Baku'] = 'Asia/Baku';
$tz['Asia/Bangkok'] = 'Asia/Bangkok';
$tz['Asia/Beirut'] = 'Asia/Beirut';
$tz['Asia/Bishkek'] = 'Asia/Bishkek';
$tz['Asia/Brunei'] = 'Asia/Brunei';
$tz['Asia/Calcutta'] = 'Asia/Calcutta';
$tz['Asia/Chungking'] = 'Asia/Chungking';
$tz['Asia/Colombo'] = 'Asia/Colombo';
$tz['Asia/Damascus'] = 'Asia/Damascus';
$tz['Asia/Dhaka'] = 'Asia/Dhaka';
$tz['Asia/Dili'] = 'Asia/Dili';
$tz['Asia/Dubai'] = 'Asia/Dubai';
$tz['Asia/Dushanbe'] = 'Asia/Dushanbe';
$tz['Asia/Gaza'] = 'Asia/Gaza';
$tz['Asia/Harbin'] = 'Asia/Harbin';
$tz['Asia/Hong_Kong'] = 'Asia/Hong Kong';
$tz['Asia/Hovd'] = 'Asia/Hovd';
$tz['Asia/Irkutsk'] = 'Asia/Irkutsk';
$tz['Asia/Jakarta'] = 'Asia/Jakarta';
$tz['Asia/Jayapura'] = 'Asia/Jayapura';
$tz['Asia/Jerusalem'] = 'Asia/Jerusalem';
$tz['Asia/Kabul'] = 'Asia/Kabul';
$tz['Asia/Kamchatka'] = 'Asia/Kamchatka';
$tz['Asia/Karachi'] = 'Asia/Karachi';
$tz['Asia/Kashgar'] = 'Asia/Kashgar';
$tz['Asia/Katmandu'] = 'Asia/Katmandu';
$tz['Asia/Krasnoyarsk'] = 'Asia/Krasnoyarsk';
$tz['Asia/Kuala_Lumpur'] = 'Asia/Kuala Lumpur';
$tz['Asia/Kuching'] = 'Asia/Kuching';
$tz['Asia/Kuwait'] = 'Asia/Kuwait';
$tz['Asia/Macao'] = 'Asia/Macao';
$tz['Asia/Magadan'] = 'Asia/Magadan';
$tz['Asia/Manila'] = 'Asia/Manila';
$tz['Asia/Muscat'] = 'Asia/Muscat';
$tz['Asia/Nicosia'] = 'Asia/Nicosia';
$tz['Asia/Novosibirsk'] = 'Asia/Novosibirsk';
$tz['Asia/Omsk'] = 'Asia/Omsk';
$tz['Asia/Phnom_Penh'] = 'Asia/Phnom Penh';
$tz['Asia/Pyongyang'] = 'Asia/Pyongyang';
$tz['Asia/Qatar'] = 'Asia/Qatar';
$tz['Asia/Rangoon'] = 'Asia/Rangoon';
$tz['Asia/Riyadh'] = 'Asia/Riyadh';
$tz['Asia/Saigon'] = 'Asia/Saigon';
$tz['Asia/Samarkand'] = 'Asia/Samarkand';
$tz['Asia/Seoul'] = 'Asia/Seoul';
$tz['Asia/Shanghai'] = 'Asia/Shanghai';
$tz['Asia/Singapore'] = 'Asia/Singapore';
$tz['Asia/Taipei'] = 'Asia/Taipei';
$tz['Asia/Tashkent'] = 'Asia/Tashkent';
$tz['Asia/Tbilisi'] = 'Asia/Tbilisi';
$tz['Asia/Tehran'] = 'Asia/Tehran';
$tz['Asia/Thimphu'] = 'Asia/Thimphu';
$tz['Asia/Tokyo'] = 'Asia/Tokyo';
$tz['Asia/Ujung_Pandang'] = 'Asia/Ujung Pandang';
$tz['Asia/Ulaanbaatar'] = 'Asia/Ulaanbaatar';
$tz['Asia/Urumqi'] = 'Asia/Urumqi';
$tz['Asia/Vientiane'] = 'Asia/Vientiane';
$tz['Asia/Vladivostok'] = 'Asia/Vladivostok';
$tz['Asia/Yakutsk'] = 'Asia/Yakutsk';
$tz['Asia/Yekaterinburg'] = 'Asia/Yekaterinburg';
$tz['Asia/Yerevan'] = 'Asia/Yerevan';
$tz['Atlantic/Azores'] = 'Atlantic/Azores';
$tz['Atlantic/Bermuda'] = 'Atlantic/Bermuda';
$tz['Atlantic/Canary'] = 'Atlantic/Canary';
$tz['Atlantic/Cape_Verde'] = 'Atlantic/Cape Verde';
$tz['Atlantic/Faeroe'] = 'Atlantic/Faeroe';
$tz['Atlantic/Jan_Mayen'] = 'Atlantic/Jan Mayen';
$tz['Atlantic/Madeira'] = 'Atlantic/Madeira';
$tz['Atlantic/Reykjavik'] = 'Atlantic/Reykjavik';
$tz['Atlantic/South_Georgia'] = 'Atlantic/South Georgia';
$tz['Atlantic/Stanley'] = 'Atlantic/Stanley';
$tz['Atlantic/St_Helena'] = 'Atlantic/St Helena';
$tz['Australia/Adelaide'] = 'Australia/Adelaide';
$tz['Australia/Brisbane'] = 'Australia/Brisbane';
$tz['Australia/Broken_Hill'] = 'Australia/Broken Hill';
$tz['Australia/Darwin'] = 'Australia/Darwin';
$tz['Australia/Hobart'] = 'Australia/Hobart';
$tz['Australia/Lindeman'] = 'Australia/Lindeman';
$tz['Australia/Lord_Howe'] = 'Australia/Lord Howe';
$tz['Australia/Melbourne'] = 'Australia/Melbourne';
$tz['Australia/Perth'] = 'Australia/Perth';
$tz['Australia/Sydney'] = 'Australia/Sydney';
$tz['Europe/Amsterdam'] = 'Europe/Amsterdam';
$tz['Europe/Andorra'] = 'Europe/Andorra';
$tz['Europe/Athens'] = 'Europe/Athens';
$tz['Europe/Belfast'] = 'Europe/Belfast';
$tz['Europe/Belgrade'] = 'Europe/Belgrade';
$tz['Europe/Berlin'] = 'Europe/Berlin';
$tz['Europe/Bratislava'] = 'Europe/Bratislava';
$tz['Europe/Brussels'] = 'Europe/Brussels';
$tz['Europe/Bucharest'] = 'Europe/Bucharest';
$tz['Europe/Budapest'] = 'Europe/Budapest';
$tz['Europe/Chisinau'] = 'Europe/Chisinau';
$tz['Europe/Copenhagen'] = 'Europe/Copenhagen';
$tz['Europe/Dublin'] = 'Europe/Dublin';
$tz['Europe/Gibraltar'] = 'Europe/Gibraltar';
$tz['Europe/Helsinki'] = 'Europe/Helsinki';
$tz['Europe/Istanbul'] = 'Europe/Istanbul';
$tz['Europe/Kaliningrad'] = 'Europe/Kaliningrad';
$tz['Europe/Kiev'] = 'Europe/Kiev';
$tz['Europe/Lisbon'] = 'Europe/Lisbon';
$tz['Europe/Ljubljana'] = 'Europe/Ljubljana';
$tz['Europe/London'] = 'Europe/London';
$tz['Europe/Luxembourg'] = 'Europe/Luxembourg';
$tz['Europe/Madrid'] = 'Europe/Madrid';
$tz['Europe/Malta'] = 'Europe/Malta';
$tz['Europe/Minsk'] = 'Europe/Minsk';
$tz['Europe/Monaco'] = 'Europe/Monaco';
$tz['Europe/Moscow'] = 'Europe/Moscow';
$tz['Europe/Oslo'] = 'Europe/Oslo';
$tz['Europe/Paris'] = 'Europe/Paris';
$tz['Europe/Prague'] = 'Europe/Prague';
$tz['Europe/Riga'] = 'Europe/Riga';
$tz['Europe/Rome'] = 'Europe/Rome';
$tz['Europe/Samara'] = 'Europe/Samara';
$tz['Europe/San_Marino'] = 'Europe/San Marino';
$tz['Europe/Sarajevo'] = 'Europe/Sarajevo';
$tz['Europe/Simferopol'] = 'Europe/Simferopol';
$tz['Europe/Skopje'] = 'Europe/Skopje';
$tz['Europe/Sofia'] = 'Europe/Sofia';
$tz['Europe/Stockholm'] = 'Europe/Stockholm';
$tz['Europe/Tallinn'] = 'Europe/Tallinn';
$tz['Europe/Tirane'] = 'Europe/Tirane';
$tz['Europe/Uzhgorod'] = 'Europe/Uzhgorod';
$tz['Europe/Vaduz'] = 'Europe/Vaduz';
$tz['Europe/Vatican'] = 'Europe/Vatican';
$tz['Europe/Vienna'] = 'Europe/Vienna';
$tz['Europe/Vilnius'] = 'Europe/Vilnius';
$tz['Europe/Warsaw'] = 'Europe/Warsaw';
$tz['Europe/Zagreb'] = 'Europe/Zagreb';
$tz['Europe/Zaporozhye'] = 'Europe/Zaporozhye';
$tz['Europe/Zurich'] = 'Europe/Zurich';
$tz['Indian/Antananarivo'] = 'Indian/Antananarivo';
$tz['Indian/Chagos'] = 'Indian/Chagos';
$tz['Indian/Christmas'] = 'Indian/Christmas';
$tz['Indian/Cocos'] = 'Indian/Cocos';
$tz['Indian/Comoro'] = 'Indian/Comoro';
$tz['Indian/Kerguelen'] = 'Indian/Kerguelen';
$tz['Indian/Mahe'] = 'Indian/Mahe';
$tz['Indian/Maldives'] = 'Indian/Maldives';
$tz['Indian/Mauritius'] = 'Indian/Mauritius';
$tz['Indian/Mayotte'] = 'Indian/Mayotte';
$tz['Indian/Reunion'] = 'Indian/Reunion';
$tz['Pacific/Apia'] = 'Pacific/Apia';
$tz['Pacific/Auckland'] = 'Pacific/Auckland';
$tz['Pacific/Chatham'] = 'Pacific/Chatham';
$tz['Pacific/Easter'] = 'Pacific/Easter';
$tz['Pacific/Efate'] = 'Pacific/Efate';
$tz['Pacific/Enderbury'] = 'Pacific/Enderbury';
$tz['Pacific/Fakaofo'] = 'Pacific/Fakaofo';
$tz['Pacific/Fiji'] = 'Pacific/Fiji';
$tz['Pacific/Funafuti'] = 'Pacific/Funafuti';
$tz['Pacific/Galapagos'] = 'Pacific/Galapagos';
$tz['Pacific/Gambier'] = 'Pacific/Gambier';
$tz['Pacific/Guadalcanal'] = 'Pacific/Guadalcanal';
$tz['Pacific/Guam'] = 'Pacific/Guam';
$tz['Pacific/Honolulu'] = 'Pacific/Honolulu';
$tz['Pacific/Johnston'] = 'Pacific/Johnston';
$tz['Pacific/Kiritimati'] = 'Pacific/Kiritimati';
$tz['Pacific/Kosrae'] = 'Pacific/Kosrae';
$tz['Pacific/Kwajalein'] = 'Pacific/Kwajalein';
$tz['Pacific/Majuro'] = 'Pacific/Majuro';
$tz['Pacific/Marquesas'] = 'Pacific/Marquesas';
$tz['Pacific/Midway'] = 'Pacific/Midway';
$tz['Pacific/Nauru'] = 'Pacific/Nauru';
$tz['Pacific/Niue'] = 'Pacific/Niue';
$tz['Pacific/Norfolk'] = 'Pacific/Norfolk';
$tz['Pacific/Noumea'] = 'Pacific/Noumea';
$tz['Pacific/Pago_Pago'] = 'Pacific/Pago Pago';
$tz['Pacific/Palau'] = 'Pacific/Palau';
$tz['Pacific/Pitcairn'] = 'Pacific/Pitcairn';
$tz['Pacific/Ponape'] = 'Pacific/Ponape';
$tz['Pacific/Port_Moresby'] = 'Pacific/Port Moresby';
$tz['Pacific/Rarotonga'] = 'Pacific/Rarotonga';
$tz['Pacific/Saipan'] = 'Pacific/Saipan';
$tz['Pacific/Tahiti'] = 'Pacific/Tahiti';
$tz['Pacific/Tarawa'] = 'Pacific/Tarawa';
$tz['Pacific/Tongatapu'] = 'Pacific/Tongatapu';
$tz['Pacific/Truk'] = 'Pacific/Truk';
$tz['Pacific/Wake'] = 'Pacific/Wake';
$tz['Pacific/Wallis'] = 'Pacific/Wallis';
$tz['Pacific/Yap'] = 'Pacific/Yap';

$GLOBALS['tz'] = &$tz;
