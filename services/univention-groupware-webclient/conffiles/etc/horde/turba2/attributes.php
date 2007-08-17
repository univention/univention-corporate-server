<?php
/**
 * Turba Attributes File
 *
 * This file contains the attributes that Turba understands, and their
 * types. It may be safely edited by hand. Use attributes.php.dist as a
 * reference.
 *
 * The syntax of this array is as follows:<pre>
 *      label    - The text that the user will see attached to this field.
 *      type     - One of the following:
 *                      - spacer            - header
 *                      - description       - html
 *                      - number            - int
 *                      - intlist           - text
 *                      - longtext          - countedtext
 *                      - address           - file
 *                      - boolean           - link
 *                      - email             - emailconfirm
 *                      - password          - passwordconfirm
 *                      - enum              - multienum
 *                      - radio             - set
 *                      - date              - time
 *                      - monthyear         - monthdayyear
 *                      - colorpicker       - sorter
 *                      - creditcard        - invalid
 *                      - stringlist        - addresslink (requires Horde-3.2)
 *      required - Boolean whether this field is mandatory.
 *      readonly - Boolean whether this field is editable.
 *      desc     - Any help text attached to the field.
 *      params   - Any other parameters that need to be passed to the field.
 *                 For a documentation of available field paramaters see
 *                 http://wiki.horde.org/Doc/Dev/FormTypes.
 * </pre>
 *
 * $Horde: turba/config/attributes.php.dist,v 1.49 2007/06/14 15:54:53 chuck Exp $
 */

$attributes['name'] = array(
    'label' => _("Name"),
    'type' => 'text',
    'required' => true,
    'params' => array('', 40, 255)
);
$attributes['firstname'] = array(
    'label' => _("First Name"),
    'type' => 'text',
    'required' => false
);
$attributes['lastname'] = array(
    'label' => _("Last Name"),
    'type' => 'text',
    'required' => true
);
$attributes['name_prefix'] = array(
    'label' => _("Salutation"),
    'type' => 'enum',
    'required' => false,
    'params' => array(array('', _("Mr"), _("Ms"), _("Mrs"), _("Dr"))),
);
$attributes['email'] = array(
    'label' => _("Email"),
    'type' => 'email',
    'required' => false,
    'params' => array(false, false, true)
);
$attributes['emails'] = array(
    'label' => _("Emails"),
    'type' => 'email',
    'required' => false,
    'params' => array(true, false, true)
);
$attributes['alias'] = array(
    'label' => _("Alias"),
    'type' => 'text',
    'required' => false,
    'params' => array('', 40, 32)
);
$attributes['title'] = array(
    'label' => _("Title"),
    'type' => 'text',
    'required' => false,
    'params' => array('', 40, 255)
);
$attributes['company'] = array(
    'label' => _("Company"),
    'type' => 'text',
    'required' => false,
    'params' => array('', 40, 255)
);
$attributes['homeAddress'] = array(
    'label' => _("Home Address"),
    'type' => 'address',
    'required' => false,
    'params' => array(3, 40)
);
$attributes['homeStreet'] = array(
    'label' => _("Home Street Address"),
    'type' => 'text',
    'required' => false
);
$attributes['homeCity'] = array(
    'label' => _("Home City"),
    'type' => 'text',
    'required' => false
);
$attributes['homeProvince'] = array(
    'label' => _("Home State/Province"),
    'type' => 'text',
    'required' => false
);
$attributes['homePostalCode'] = array(
    'label' => _("Home Postal Code"),
    'type' => 'text',
    'required' => false
);
$attributes['homeCountry'] = array(
    'label' => _("Home Country"),
    'type' => 'text',
    'required' => false
);
$attributes['workAddress'] = array(
    'label' => _("Work Address"),
    'type' => 'address',
    'required' => false,
    'params' => array(3, 40)
);
$attributes['workStreet'] = array(
    'label' => _("Work Street Address"),
    'type' => 'text',
    'required' => false
);
$attributes['workCity'] = array(
    'label' => _("Work City"),
    'type' => 'text',
    'required' => false
);
$attributes['workProvince'] = array(
    'label' => _("Work State/Province"),
    'type' => 'text',
    'required' => false
);
$attributes['workPostalCode'] = array(
    'label' => _("Work Postal Code"),
    'type' => 'text',
    'required' => false
);
$attributes['workCountry'] = array(
    'label' => _("Work Country"),
    'type' => 'text',
    'required' => false
);
$attributes['companyAddress'] = array(
    'label' => _("Company Address"),
    'type' => 'address',
    'required' => false,
    'params' => array(3, 40)
);
$attributes['homePhone'] = array(
    'label' => _("Home Phone"),
    'type' => 'text',
    'required' => false,
    'params' => array('', 40, 25)
);
$attributes['workPhone'] = array(
    'label' => _("Work Phone"),
    'type' => 'text',
    'required' => false,
    'params' => array('', 40, 25)
);
$attributes['cellPhone'] = array(
    'label' => _("Mobile Phone"),
    'type' => 'cellphone',
    'required' => false
);
$attributes['fax'] = array(
    'label' => _("Fax"),
    'type' => 'text',
    'required' => false,
    'params' => array('', 40, 25)
);
$attributes['pager'] = array(
    'label' => _("Pager"),
    'type' => 'text',
    'required' => false,
    'params' => array('', 40, 25)
);
$attributes['businessCategory'] = array(
    'label' => _("Business Category"),
    'type' => 'text',
    'required' => false
);
$attributes['birthday'] = array(
    'label' => _("Birthday"),
    'type' => 'monthdayyear',
    'params' => array(1900, null, true, '%Y-%m-%d'),
    'required' => false,
);
$attributes['notes'] = array(
    'label' => _("Notes"),
    'type' => 'longtext',
    'required' => false,
    'params' => array(3, 40)
);
$attributes['pgpPublicKey'] = array(
    'label' => _("PGP Public Key"),
    'type' => 'longtext',
    'required' => false,
    'params' => array(3, 40)
);
$attributes['smimePublicKey'] = array(
    'label' => _("S/MIME Public Certificate"),
    'type' => 'longtext',
    'required' => false,
    'params' => array(3, 40)
);
$attributes['freebusyUrl'] = array(
    'label' => _("Freebusy URL"),
    'type' => 'text',
    'required' => false,
    'params' => array('', 40, 255)
);
$attributes['website'] = array(
     'label' => _("Website URL"),
     'type' => 'text',
     'required' => false,
);
$attributes['department'] = array(
    'label' => _("Department"),
    'type' => 'text',
    'required' => false,
);
$attributes['nickname'] = array(
    'label' => _("Nickname"),
    'type' => 'text',
    'required' => false,
);
$attributes['office'] = array(
    'label' => _("Office"),
    'type' => 'text',
    'required' => false
);
$attributes['initials'] = array(
    'label' => _("Initials"),
    'type' => 'text',
    'required' => false
);
$attributes['salutation'] = array(
    'label' => _("Salutation"),
    'type' => 'text',
    'required' => false
);
$attributes['anniversary'] = array(
    'label' => _("Anniversary"),
    'type' => 'monthdayyear',
    'params' => array(1900, null, true, '%Y-%m-%d'),
    'required' => false,
);
$attributes['spouse'] = array(
    'label' => _("Spouse"),
    'type' => 'text',
    'required' => false,
);
$attributes['children'] = array(
    'label' => _("Children"),
    'type' => 'text',
    'required' => false,
);

/* This attribute uses Horde's categories and is an example how to use an enum
 * field.  Don't forget to add a 'map' entry to config/sources.php if you want
 * to use this attribute. */
// require_once 'Horde/Prefs/CategoryManager.php';
// $cManager = new Prefs_CategoryManager();
// $categories = array_merge(array(_("Unfiled")), $cManager->get());
// $attributes['category'] = array(
//     'label' => _("Category"),
//     'type' => 'enum',
//     'params' => array($categories),
//     'required' => false
// );
