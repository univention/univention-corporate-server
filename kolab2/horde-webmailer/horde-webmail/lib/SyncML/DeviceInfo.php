<?php
/**
 * SyncML_DeviceInfo represents a device information set according to the
 * SyncML specification.
 *
 * A DeviceInfo object is created by SyncML_Command_Put from an appropriate
 * XML message. SyncML_Command_Put directly populates the members variables.
 *
 * The current implementation should handle all DevInf 1.1 DTD elements
 * except <DSMem> entries.
 *
 * $Horde: framework/SyncML/SyncML/DeviceInfo.php,v 1.2.2.13 2009-01-06 15:23:37 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Karsten Fourmont <karsten@horde.org>
 * @author  Jan Schneider <jan@horde.org>
 * @package SyncML
 */
class SyncML_DeviceInfo {

    /**
     * The major and minor version identifier of the Device Information DTD.
     *
     * @var string
     */
    var $VerDTD;

    /**
     * The name of the manufacturer of the device.
     *
     * @var string
     */
    var $Man;

    /**
     * The model name or model number of the device.
     *
     * @var string
     */
    var $Mod;

    /**
     * The OEM (Original Equipment Manufacturer) of the device.
     *
     * @var string
     */
    var $OEM;

    /**
     * The firmware version of the device.
     *
     * @var string
     */
    var $FwV;

    /**
     * The software version of the device.
     *
     * @var string
     */
    var $SwV;

    /**
     * The hardware version of the device.
     *
     * @var string
     */
    var $HwV;

    /**
     * The (globally unique) identifier of the source synchronization device.
     *
     * @var string
     */
    var $DevID;

    /**
     * The type of the source synchronization device.
     *
     * @var string
     */
    var $DevTyp;

    /**
     * Array of SyncML_DataStore objects.
     *
     * @var array
     */
    var $DataStores = array();

    /**
     * Multidimensional array that specifies the content type capabilities of
     * the device.
     *
     * Example: array('text/x-vcard' => array('FN' => SyncML_Property))
     *
     * @var array
     */
    var $CTCaps;

    /**
     * The non-standard, experimental extensions supported by the device.
     *
     * A hash with <XNam> elements as keys and arrays of <XVal> elements as
     * values.
     * Example: array('X-Foo-Bar' => array(1, 'foo'))
     *
     * @var array
     */
    var $Exts;

    /**
     * Whether the device supports UTC based time.
     *
     * @var boolean
     */
    var $UTC;

    /**
     * Whether the device supports handling of large objects.
     *
     * @var boolean
     */
    var $SupportLargeObjs;

    /**
     * Whether the device supports number of changes.
     *
     * @var boolean
     */
    var $SupportNumberOfChanges;

    /**
     * Returns a SyncML_DataStore object for a certain source URI.
     *
     * @param string $source URI  A source URI.
     *
     * @return SyncML_DataStore  A data store object or null if none found for
     *                           the source URI.
     */
    function getDataStore($sourceURI)
    {
        foreach ($this->DataStores as $dataStore) {
            if ($dataStore->SourceRef == $sourceURI) {
                return $dataStore;
            }
        }
        return null;
    }

}

/**
 * The SyncML_DataStore class describes one of the possible datastores
 * (i.e. databases) of the device.
 *
 * Most important attributes are the preferred MIME Types for sending and
 * receiving data for this datastore: $Tx_Pref and $Rx_Pref.
 *
 * @package SyncML
 */
class SyncML_DataStore {

    /**
     * The local URI of the datastore.
     *
     * @var string
     */
    var $SourceRef;

    /**
     * The display name of the datastore
     *
     * @var string
     */
    var $DisplayName;

    /**
     * The maximum size of a global unique identifier for the datastore in
     * bytes.
     *
     * @var integer
     */
    var $MaxGUIDSize;

    /**
     * The preferred types and versions of a content type received by the
     * device.
     *
     * The content types (CTType) are the keys, the versions (VerCT) are the
     * values.
     *
     * @var array
     */
    var $Rx_Pref = array();

    /**
     * The supported types and versions of a content type received by the
     * device.
     *
     * The content types (CTType) are the keys, the versions (VerCT) are the
     * values.
     *
     * @var array
     */
    var $Rx = array();

    /**
     * The preferred types and versions of a content type transmitted by the
     * device.
     *
     * The content types (CTType) are the keys, the versions (VerCT) are the
     * values.
     *
     * @var array
     */
    var $Tx_Pref = array();

    /**
     * The supported types and versions of a content type transmitted by the
     * device.
     *
     * The content types (CTType) are the keys, the versions (VerCT) are the
     * values.
     *
     * @var array
     */
    var $Tx = array();

    /**
     * The maximum memory and item identifier for the datastore.
     *
     * Not implemented yet.
     */
    var $DSMem;

    /**
     * The synchronization capabilities of the datastore.
     *
     * The synchronization types (SyncType) are stored in the keys of the
     * hash.
     *
     * @var array
     */
    var $SyncCap = array();

    /**
     * Returns the preferred content type the client wants to receive.
     *
     * @return string  The device's preferred content type or null if not
     *                 specified (which is not allowed).
     */
    function getPreferredRXContentType()
    {
        reset($this->Rx_Pref);
        return key($this->Rx_Pref);
    }

    /**
     * Returns the version of the preferred content type the client wants to
     * receive.
     *
     * @return string  The device's preferred content type version or null if
     *                 not specified (which is not allowed).
     */
    function getPreferredRXContentTypeVersion()
    {
        return reset($this->Rx_Pref);
    }

}

/**
 * The SyncML_Property class is used to define a single property of a data
 * item supported by the device.
 *
 * The allowed contents of a property can be defined by an enumeration of
 * valid values (ValEnum) or by a DataType/Size combination, or not at all.
 *
 * @package SyncML
 */
class SyncML_Property {

    /**
     * The supported enumerated values of the content type property.
     *
     * The supported values stored in the keys of the hash, e.g. 'PUBLIC' and
     * 'PRIVATE' for a text/calendar 'CLASS' property.
     *
     * @var array
     */
    var $ValEnum;

    /**
     * The datatype of the content type property, e.g. 'chr', 'int', 'bool',
     * etc.
     *
     * @var string
     */
    var $DataType;

    /**
     * The size of the content type property in bytes.
     *
     * @var integer
     */
    var $Size;

    /**
     * The display name of the content type property.
     *
     * @var string
     */
    var $DisplayName;

    /**
     * The supported parameters of the content type property.
     *
     * The parameter name (<ParamName>, e.g. 'WORK' for the text/x-vcard 'TEL'
     * property) are the keys, SyncML_PropertyParameter objects are the
     * values.
     *
     * @var array
     */
    var $Params;

}

/**
 * The SyncML_PropertyParameter class is used to define a single parameter of
 * a property of a data item supported by the device.
 *
 * The contents of a property parameter can be defined by an enumeration of
 * valid values (ValEnum) or by a DataType/Size combination, or not at all.
 *
 * @package SyncML
 */
class SyncML_PropertyParameter {

    /**
     * The supported enumerated values of the content type property.
     *
     * The supported values stored in the keys of the hash, e.g. 'PUBLIC' and
     * 'PIVATE' for a text/calendar 'CLASS' property.
     *
     * @var array
     */
    var $ValEnum;

    /**
     * The datatype of the content type property, e.g. 'chr', 'int', 'bool',
     * etc.
     *
     * @var string
     */
    var $DataType;

    /**
     * The size of the content type property in bytes.
     *
     * @var integer
     */
    var $Size;

    /**
     * The display name of the content type property.
     *
     * @var string
     */
    var $DisplayName;

}
