<?php
// Warning: This file is auto-generated and might be overwritten by
//          univention-baseconfig.
//          Please edit the following file instead:
// Warnung: Diese Datei wurde automatisch generiert und kann durch
//          univention-baseconfig überschrieben werden.
//          Bitte bearbeiten Sie an Stelle dessen die folgende Datei:
//
// 	/etc/univention/templates/files/etc/horde/turba2/attributes.php
//

/**
 * Turba Attributes File
 *
 * This file contains the attributes that Turba understands, and their
 * types. It may be safely edited by hand. Use attributes.php.dist as
 * a reference.
 *
 * General configuration is in 'conf.php'.
 * Contact sources are defined in 'sources.php'.
 * Default user preferences are defined in 'prefs.php'.
 *
 * $Horde: turba/config/attributes.php.dist,v 1.36.6.3 2005/10/18 12:50:04 jan Exp $
 * The syntax of this array is as follows:
 *      label    - the text that the user will see attached to this field
 *      type     - one of the following:
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
 *                      - stringlist
 *      required - boolean, true or false whether this field is mandatory
 *      readonly - boolean, true or false whether this editable
 *      desc     - any help text attached to the field
 *      params   - any other parameters that need to be passed to the field
 *                 such as a list to be used in the enum field, the row and
 *                 column sizing for a longtext field, TODO (list more types)
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
    'required' => true
);
$attributes['lastname'] = array(
    'label' => _("Last Name"),
    'type' => 'text',
    'required' => true
);
$attributes['email'] = array(
    'label' => _("Email"),
    'type' => 'email',
    'required' => false,
    'params' => array('', 40, 255)
);
/*
$attributes['alias'] = array(
    'label' => _("Alias"),
    'type' => 'text',
    'required' => false,
    'params' => array('', 40, 32)
);
*/
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
/*
$attributes['homeAddress'] = array(
    'label' => _("Home Address"),
    'type' => 'address',
    'required' => false,
    'params' => array('3', '40')
);
*/
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
    'params' => array('3', '40')
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
    'params' => array('3', '40')
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
/*
$attributes['businessCategory'] = array(
    'label' => _("Business Category"),
    'type' => 'text',
    'required' => false
);
*/
$attributes['birthday'] = array(
    'label' => _("Birthday"),
    'type' => 'monthdayyear',
    'params' => array(1900, null, true, 1),
    'required' => false,
);
$attributes['notes'] = array(
    'label' => _("Notes"),
    'type' => 'longtext',
    'required' => false,
    'params' => array('3', '40')
);
/*
$attributes['pgpPublicKey'] = array(
    'label' => _("PGP Public Key"),
    'type' => 'longtext',
    'required' => false,
    'params' => array('3', '40')
);
$attributes['smimePublicKey'] = array(
    'label' => _("S/MIME Public Certificate"),
    'type' => 'longtext',
    'required' => false,
    'params' => array('3', '40')
);
$attributes['freebusyUrl'] = array(
    'label' => _("Freebusy URL"),
    'type' => 'text',
    'required' => false,
    'params' => array('', 40, 255)
);
*/
$attributes['website'] = array(
     'label' => _("Website URL"),
     'type' => 'text',
     'required' => false,
);
/*
$attributes['department'] = array(
    'label' => _("Department"),
    'type' => 'text',
    'required' => false,
);
*/
$attributes['nickname'] = array(
    'label' => _("Nickname"),
    'type' => 'text',
    'required' => false,
);
/*
$attributes['office'] = array(
    'label' => _("Office"),
    'type' => 'text',
    'required' => false
);
*/
/* This attribute uses Horde's categories and is an example how to use an enum
 * field.  Don't forget to add a 'map' entry to config/sources.php if you want
 * to use this attribute. */
// require_once 'Horde/Prefs/CategoryManager.php';
// $cManager = &new Prefs_CategoryManager();
// $categories = array_merge(array(_("Unfiled")), $cManager->get());
// $attributes['category'] = array(
//     'label' => _("Category"),
//     'type' => 'enum',
//     'params' => array($categories),
//     'required' => false
// );
