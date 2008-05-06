<?php
/**
 * Turba Attributes File.
 *
 * This file contains examples of attributes that Turba understands, and their
 * types. It may be safely edited by hand. Use attributes.php.dist as a
 * reference.
 *
 * The syntax of this array is as follows:<pre>
 *      label              - The text that the user will see attached to this
 *                           field.
 *      type               - One of the following:
 *                             - spacer            - header
 *                             - description       - html
 *                             - number            - int
 *                             - intlist           - text
 *                             - longtext          - countedtext
 *                             - address           - file
 *                             - boolean           - link
 *                             - email             - emailconfirm
 *                             - password          - passwordconfirm
 *                             - enum              - multienum
 *                             - radio             - set
 *                             - date              - time
 *                             - monthyear         - monthdayyear
 *                             - colorpicker       - sorter
 *                             - creditcard        - invalid
 *                             - stringlist        - addresslink (requires Horde-3.2)
 *      required           - Boolean whether this field is mandatory.
 *      readonly           - Boolean whether this field is editable.
 *      desc               - Any help text attached to the field.
 *      time_object_label  - The text to describe the time object category.
 *                           Only valid for monthdayyear types and removing this
 *                           from a monthdayyear type will hide it from the
 *                           listTimeObjects api.
 *      params             - Any other parameters that need to be passed to the
 *                           field. For a documentation of available field
 *                           paramaters see
 *                           http://wiki.horde.org/Doc/Dev/FormTypes.
 * </pre>
 *
 * $Horde: turba/config/attributes.php.dist,v 1.36.6.6 2008/03/13 00:11:40 jan Exp $
 */

/* Personal stuff. */
$attributes['name'] = array(
    'label' => _("Name"),
    'type' => 'text',
    'required' => true,
    'params' => array('regex' => '', 'size' => 40, 'maxlength' => 255)
);
$attributes['firstname'] = array(
    'label' => _("First Name"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 40, 'maxlength' => 255)
);
$attributes['lastname'] = array(
    'label' => _("Last Name"),
    'type' => 'text',
    'required' => true,
    'params' => array('regex' => '', 'size' => 40, 'maxlength' => 255)
);
$attributes['middlenames'] = array(
    'label' => _("Middle Names"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 40, 'maxlength' => 255)
);
$attributes['namePrefix'] = array(
    'label' => _("Name Prefixes"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 32, 'maxlength' => 32)
);
$attributes['nameSuffix'] = array(
    'label' => _("Name Suffixes"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 32, 'maxlength' => 32)
);
$attributes['alias'] = array(
    'label' => _("Alias"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 40, 'maxlength' => 32)
);
$attributes['nickname'] = array(
    'label' => _("Nickname"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 32, 'maxlength' => 32)
);
$attributes['birthday'] = array(
    'label' => _("Birthday"),
    'type' => 'monthdayyear',
    'required' => false,
    'params' => array('start_year' => 1900, 'end_year' => null, 'picker' => true, 'format_in' => '%Y-%m-%d', 'format_out' => '%x'),
    'time_object_label' => _("Birthdays"),
);
$attributes['anniversary'] = array(
    'label' => _("Anniversary"),
    'type' => 'monthdayyear',
    'params' => array('start_year' => 1900, 'end_year' => null, 'picker' => true, 'format_in' => '%Y-%m-%d', 'format_out' => '%x'),
    'required' => false,
    'time_object_label' => _("Anniversaries"),
);
$attributes['spouse'] = array(
    'label' => _("Spouse"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 40, 'maxlength' => 255)
);
$attributes['children'] = array(
    'label' => _("Children"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 40, 'maxlength' => 255)
);

/* Locations, addresses. */
$attributes['homeAddress'] = array(
    'label' => _("Home Address"),
    'type' => 'address',
    'required' => false,
    'params' => array('rows' => 3, 'cols' => 40)
);
$attributes['homeStreet'] = array(
    'label' => _("Home Street Address"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 40, 'maxlength' => 255)
);
$attributes['homePOBox'] = array(
    'label' => _("Home Post Office Box"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 10, 'maxlength' => 10)
);
$attributes['homeCity'] = array(
    'label' => _("Home City"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 40, 'maxlength' => 255)
);
$attributes['homeProvince'] = array(
    'label' => _("Home State/Province"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 40, 'maxlength' => 255)
);
$attributes['homePostalCode'] = array(
    'label' => _("Home Postal Code"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 10, 'maxlength' => 10)
);
$attributes['homeCountry'] = array(
    'label' => _("Home Country"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 40, 'maxlength' => 255)
);
/* If using Horde 3.2 or higher, you can display a drop down with a country
 * list. */
// $attributes['homeCountry'] = array(
//     'label' => _("Home Country"),
//     'type' => 'country',
//     'required' => false,
//     'params' => array('prompt' => true)
// );
$attributes['workAddress'] = array(
    'label' => _("Work Address"),
    'type' => 'address',
    'required' => false,
    'params' => array('rows' => 3, 'cols' => 40)
);
$attributes['workStreet'] = array(
    'label' => _("Work Street Address"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 40, 'maxlength' => 255)
);
$attributes['workPOBox'] = array(
    'label' => _("Work Post Office Box"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 10, 'maxlength' => 10)
);
$attributes['workCity'] = array(
    'label' => _("Work City"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 40, 'maxlength' => 255)
);
$attributes['workProvince'] = array(
    'label' => _("Work State/Province"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 40, 'maxlength' => 255)
);
$attributes['workPostalCode'] = array(
    'label' => _("Work Postal Code"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 10, 'maxlength' => 10)
);
$attributes['workCountry'] = array(
    'label' => _("Work Country"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 40, 'maxlength' => 255)
);
/* If using Horde 3.2 or higher, you can display a drop down with a country
 * list. */
// $attributes['workCountry'] = array(
//     'label' => _("Work Country"),
//     'type' => 'country',
//     'required' => false,
//     'params' => array('prompt' => true)
// );
$attributes['companyAddress'] = array(
    'label' => _("Company Address"),
    'type' => 'address',
    'required' => false,
    'params' => array('rows' => 3, 'cols' => 40)
);
$attributes['timezone'] = array(
    'label' => _("Time Zone"),
    'type' => 'enum',
    'params' => array('values' => $GLOBALS['tz'], 'prompt' => true),
    'required' => false
);

/* Communication. */
$attributes['email'] = array(
    'label' => _("Email"),
    'type' => 'email',
    'required' => false,
    'params' => array('allow_multi' => false, 'strip_domain' => false, 'link_compose' => true)
);
$attributes['emails'] = array(
    'label' => _("Emails"),
    'type' => 'email',
    'required' => false,
    'params' => array('allow_multi' => true, 'strip_domain' => false, 'link_compose' => true)
);
$attributes['homePhone'] = array(
    'label' => _("Home Phone"),
    'type' => 'phone',
    'required' => false
);
$attributes['workPhone'] = array(
    'label' => _("Work Phone"),
    'type' => 'phone',
    'required' => false
);
$attributes['cellPhone'] = array(
    'label' => _("Mobile Phone"),
    'type' => 'cellphone',
    'required' => false
);
$attributes['fax'] = array(
    'label' => _("Fax"),
    'type' => 'phone',
    'required' => false
);
$attributes['pager'] = array(
    'label' => _("Pager"),
    'type' => 'phone',
    'required' => false
);

/* Job, company, organization. */
$attributes['title'] = array(
    'label' => _("Job Title"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 40, 'maxlength' => 255)
);
$attributes['role'] = array(
    'label' => _("Occupation"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 40, 'maxlength' => 255)
);
$attributes['businessCategory'] = array(
    'label' => _("Business Category"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 40, 'maxlength' => 255)
);
$attributes['company'] = array(
    'label' => _("Company"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 40, 'maxlength' => 255)
);
$attributes['department'] = array(
    'label' => _("Department"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 40, 'maxlength' => 255)
);
$attributes['office'] = array(
    'label' => _("Office"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 40, 'maxlength' => 255)
);

/* Other */
$attributes['notes'] = array(
    'label' => _("Notes"),
    'type' => 'longtext',
    'required' => false,
    'params' => array('rows' => 3, 'cols' => 40)
);
$attributes['website'] = array(
    'label' => _("Website URL"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 40, 'maxlength' => 255)
);
$attributes['freebusyUrl'] = array(
    'label' => _("Freebusy URL"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 40, 'maxlength' => 255)
);
$attributes['pgpPublicKey'] = array(
    'label' => _("PGP Public Key"),
    'type' => 'longtext',
    'required' => false,
    'params' => array('rows' => 3, 'cols' => 40)
);
$attributes['smimePublicKey'] = array(
    'label' => _("S/MIME Public Certificate"),
    'type' => 'longtext',
    'required' => false,
    'params' => array('rows' => 3, 'cols' => 40)
);
/* This attribute uses Horde's categories and is an example how to use an enum
 * field.  Don't forget to add a 'map' entry to config/sources.php if you want
 * to use this attribute. */
require_once 'Horde/Prefs/CategoryManager.php';
require_once 'Horde/Array.php';
$cManager = new Prefs_CategoryManager();
$attributes['category'] = array(
    'label' => _("Category"),
    'type' => 'enum',
    'params' => array(
        'values' => array_merge(array('' => _("Unfiled")), Horde_Array::valuesToKeys($cManager->get())),
        'prompt' => false),
    'required' => false
);

/* Additional attributes supported by Kolab */
$attributes['initials'] = array(
    'label' => _("Initials"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 40, 'maxlength' => 255)
);
$attributes['instantMessenger'] = array(
    'label' => _("Instant Messenger"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 40, 'maxlength' => 255)
);
$attributes['manager'] = array(
    'label' => _("Manager"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 40, 'maxlength' => 255)
);
$attributes['assistant'] = array(
    'label' => _("Assistant"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 40, 'maxlength' => 255)
);
$attributes['gender'] = array(
    'label' => _("Gender"),
    'type' => 'enum',
    'required' => false,
    'params' => array('values' => array(_("male"), _("female")), 'prompt' => true),
);
$attributes['language'] = array(
    'label' => _("Language"),
    'type' => 'text',
    'required' => false,
    'params' => array('regex' => '', 'size' => 40, 'maxlength' => 255)
);
$attributes['latitude'] = array(
    'label' => _("Latitude"),
    'type' => 'number',
    'required' => false,
);
$attributes['longitude'] = array(
    'label' => _("Longitude"),
    'type' => 'number',
    'required' => false,
);
