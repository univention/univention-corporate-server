<?php
/**
 * Abstract class to allow data exchange between the Horde
 * applications and various Palm formats.
 *
 * $Horde: framework/Data/Data/palm.php,v 1.4 2003/11/06 15:26:25 chuck Exp $
 *
 * TODO: export method
 *
 * @author  Mathieu Clabaut <mathieu.clabaut@free.fr>
 * @package Horde_Data
 */
class Data_palm extends Data {

}

/**
 * PHP-PDB -- PHP class to write PalmOS databases.
 *
 * Copyright (C) 2001 - PHP-PDB development team
 * Licensed under the GNU LGPL software license.
 * See the doc/LEGAL file for more information
 * See http://php-pdb.sourceforge.net/ for more information about the library
 *
 * As a note, storing all of the information as hexadecimal kinda
 * sucks, but it is tough to store and properly manipulate a binary
 * string in PHP. We double the size of the data but decrease the
 * difficulty level immensely.
 */

/**
 * Define constants
 */

// Sizes
define('PDB_HEADER_SIZE', 72); // Size of the database header
define('PDB_INDEX_HEADER_SIZE', 6); // Size of the record index header
define('PDB_RECORD_HEADER_SIZE', 8); // Size of the record index entry
define('PDB_RESOURCE_SIZE', 10);  // Size of the resource index entry
define('PDB_EPOCH_1904', 2082844800); // Difference between Palm's time and Unix

// Attribute Flags
define('PDB_ATTRIB_RESOURCE', 1);
define('PDB_ATTRIB_READ_ONLY', 2);
define('PDB_ATTRIB_APPINFO_DIRTY', 4);
define('PDB_ATTRIB_BACKUP', 8);
define('PDB_ATTRIB_OK_NEWER', 16);
define('PDB_ATTRIB_RESET', 32);
define('PDB_ATTRIB_OPEN', 64);
define('PDB_ATTRIB_LAUNCHABLE', 512);

// Record Flags
// The first nibble is reserved for the category number
// See PDB_CATEGORY_MASK
define('PDB_RECORD_ATTRIB_PRIVATE', 16);
define('PDB_RECORD_ATTRIB_DELETED', 32);
define('PDB_RECORD_ATTRIB_DIRTY', 64);
define('PDB_RECORD_ATTRIB_EXPUNGED', 128);

// Category support
define('PDB_CATEGORY_NUM', 16);  // Number of categories
define('PDB_CATEGORY_NAME_LENGTH', 16);  // Bytes allocated for name
define('PDB_CATEGORY_SIZE', 276); // 2 + (num * length) + num + 1 + 1
define('PDB_CATEGORY_MASK', 15);  // Bitmask -- use with attribute of record
                                  // to get the category ID


// Double conversion
define('PDB_DOUBLEMETHOD_UNTESTED', 0);
define('PDB_DOUBLEMETHOD_NORMAL', 1);
define('PDB_DOUBLEMETHOD_REVERSE', 2);
define('PDB_DOUBLEMETHOD_BROKEN', 3);

/**
 * PalmDB Class
 *
 * Contains all of the required methods and variables to write a pdb file.
 * Extend this class to provide functionality for memos, addresses, etc.
 *
 * @package Horde_Data
 */
class PalmDB {
   var $Records = array();     // All of the data from the records is here
                               // Key = record ID
   var $RecordAttrs = array(); // And their attributes are here
   var $CurrentRecord = 1;     // Which record we are currently editing
   var $Name = '';             // Name of the PDB file
   var $TypeID = '';           // The 'Type' of the file (4 chars)
   var $CreatorID = '';        // The 'Creator' of the file (4 chars)
   var $Attributes = 0;        // Attributes (bitmask)
   var $Version = 0;           // Version of the file
   var $ModNumber = 0;         // Modification number
   var $CreationTime = 0;      // Stored in unix time (Jan 1, 1970)
   var $ModificationTime = 0;  // Stored in unix time (Jan 1, 1970)
   var $BackupTime = 0;        // Stored in unix time (Jan 1, 1970)
   var $AppInfo = '';          // Basic AppInfo block
   var $SortInfo = '';         // Basic SortInfo block
   var $DoubleMethod = PDB_DOUBLEMETHOD_UNTESTED;
                               // What method to use for converting doubles


   // Creates a new database class
   function PalmDB($Type = '', $Creator = '', $Name = '') {
      $this->TypeID = $Type;
      $this->CreatorID = $Creator;
      $this->Name = $Name;
      $this->CreationTime = time();
      $this->ModificationTime = time();
   }


   /*
    * Data manipulation functions
    *
    * These convert various numbers and strings into the hexadecimal
    * format that is used internally to construct the file.  We use hex
    * encoded strings since that is a lot easier to work with than binary
    * data in strings, and we can easily tell how big the true value is.
    * B64 encoding does some odd stuff, so we just make the memory
    * consumption grow tremendously and the complexity level drops
    * considerably.
    */
       
   // Converts a byte and returns the value
   function Int8($value) {
      $value &= 0xFF;
      return sprintf("%02x", $value);
   }
   
   
   // Loads a single byte as a number from the file
   // Use if you want to make your own ReadFile function
   function LoadInt8($file) {
      if (is_resource($file))
         $string = fread($file, 1);
      else
         $string = $file;
      return ord($string[0]);
   }
   
   
   // Converts an integer (two bytes) and returns the value
   function Int16($value) {
      $value &= 0xFFFF;
      return sprintf("%02x%02x", $value / 256, $value % 256);
   }
   
   
   // Loads two bytes as a number from the file
   // Use if you want to make your own ReadFile function
   function LoadInt16($file) {
      if (is_resource($file))
         $string = fread($file, 2);
      else
         $string = $file;
      return ord($string[0]) * 256 + ord($string[1]);
   }
   
   
   // Converts an integer (three bytes) and returns the value
   function Int24($value) {
      $value &= 0xFFFFFF;
      return sprintf("%02x%02x%02x", $value / 65536, 
                     ($value / 256) % 256, $value % 256);
   }


   // Loads three bytes as a number from the file
   // Use if you want to make your own ReadFile function
   function LoadInt24($file) {
      if (is_resource($file))
         $string = fread($file, 3);
      else
     $string = $file;
      return ord($string[0]) * 65536 + ord($string[1]) * 256 +
         ord($string[2]);
   }
      
      
   // Converts an integer (four bytes) and returns the value
   // 32-bit integers have problems with PHP when they are bigger than
   // 0x80000000 (about 2 billion) and that's why I don't use pack() here
   function Int32($value) {
      $negative = false;
      if ($value < 0) {
         $negative = true;
     $value = - $value;
      }
      $big = $value / 65536;
      settype($big, 'integer');
      $little = $value - ($big * 65536);
      if ($negative) {
         // Little must contain a value
         $little = - $little;
     // Big might be zero, and should be 0xFFFF if that is the case.
     $big = 0xFFFF - $big;
      }
      $value = PalmDB::Int16($big) . PalmDB::Int16($little);
      return $value;
   }
   
   
   // Loads a four-byte string from a file into a number
   // Use if you want to make your own ReadFile function
   function LoadInt32($file) {
      if (is_resource($file))
         $string = fread($file, 4);
      else
         $string = $file;
      $value = 0;
      $i = 0;
      while ($i < 4) {
         $value *= 256;
     $value += ord($string[$i]);
     $i ++;
      }
      return $value;
   }
   
   
   // Converts the number into a double and returns the encoded value
   // Not sure if this will work on all platforms.
   // Double(10.53) should return "40250f5c28f5c28f"
   function Double($value) {
      if ($this->DoubleMethod == PDB_DOUBLEMETHOD_UNTESTED) {
         $val = bin2hex(pack('d', 10.53));
     $val = strtolower($val);
     if (substr($val, 0, 4) == '8fc2')
        $this->DoubleMethod = PDB_DOUBLEMETHOD_REVERSE;
     if (substr($val, 0, 4) == '4025')
        $this->DoubleMethod = PDB_DOUBLEMETHOD_NORMAL;
     if ($this->DoubleMethod == PDB_DOUBLEMETHOD_UNTESTED)
        $this->DoubleMethod = PDB_DOUBLEMETHOD_BROKEN;
      }
      
      if ($this->DoubleMethod == PDB_DOUBLEMETHOD_BROKEN)
         return '0000000000000000';
     
      $value = bin2hex(pack('d', $value));
      
      if ($this->DoubleMethod == PDB_DOUBLEMETHOD_REVERSE)
         $value = substr($value, 14, 2) . substr($value, 12, 2) . 
            substr($value, 10, 2) . substr($value, 8, 2) . 
        substr($value, 6, 2) . substr($value, 4, 2) . 
        substr($value, 2, 2) . substr($value, 0, 2);
        
      return $value;
   }
   
   
   // The reverse?  Not coded yet.
   // Use if you want to make your own ReadFile function
   function LoadDouble($file) {
      if (is_resource($file))
         $string = fread($file, 8);
      else
         $string = $file;
      return 0;
   }
   
   
   // Converts a string into hexadecimal.
   // If $maxLen is specified and is greater than zero, the string is 
   // trimmed and will contain up to $maxLen characters.
   // String("abcd", 2) will return "ab" hex encoded (a total of 4
   // resulting bytes, but 2 encoded characters).
   // Returned string is *not* NULL-terminated.
   function String($value, $maxLen = false) {
      $value = bin2hex($value);
      if ($maxLen !== false && $maxLen > 0)
         $value = substr($value, 0, $maxLen * 2);
      return $value;
   }
   
   
   // Pads a hex-encoded value (typically a string) to a fixed size.
   // May grow too long if $value starts too long
   // $value = hex encoded value
   // $minLen = Append nulls to $value until it reaches $minLen
   // $minLen is the desired size of the string, unencoded.
   // PadString('6162', 3) results in '616200' (remember the hex encoding)
   function PadString($value, $minLen) {
      $PadBytes = '00000000000000000000000000000000';
      $PadMe = $minLen - (strlen($value) / 2);
      while ($PadMe > 0) {
         if ($PadMe > 16)
        $value .= $PadBytes;
     else
        return $value . substr($PadBytes, 0, $PadMe * 2);
           
     $PadMe = $minLen - (strlen($value) / 2);
      }
      
      return $value;
   }
   
   
   /*
    * Record manipulation functions
    */
    
   // Sets the current record pointer to the new record number if an
   // argument is passed in.
   // Returns the old record number (just in case you want to jump back)
   // Does not do basic record initialization if we are going to a new 
   // record.
   function GoToRecord($num = false) {
      if ($num === false)
         return $this->CurrentRecord;
      if (gettype($num) == 'string' && ($num[0] == '+' || $num[0] == '-'))
         $num = $this->CurrentRecord + $num;
      $oldRecord = $this->CurrentRecord;
      $this->CurrentRecord = $num;
      return $oldRecord;
   }
   
   
   // Returns the size of the current record if no arguments.
   // Returns the size of the specified record if arguments.
   function GetRecordSize($num = false) {
      if ($num === false)
         $num = $this->CurrentRecord;
      if (! isset($this->Records[$num]))
         return 0;
      return strlen($this->Records[$num]) / 2;
   }
   
   
   // Adds to the current record.  The input data must be already
   // hex encoded.  Initializes the record if it doesn't exist.
   function AppendCurrent($value) {
      if (! isset($this->Records[$this->CurrentRecord]))
         $this->Records[$this->CurrentRecord] = '';
      $this->Records[$this->CurrentRecord] .= $value;
   }
   
   
   // Adds a byte to the current record
   function AppendInt8($value) {
      $this->AppendCurrent($this->Int8($value));
   }
   
   
   // Adds an integer (2 bytes) to the current record
   function AppendInt16($value) {
      $this->AppendCurrent($this->Int16($value));
   }
   
   
   // Adds an integer (4 bytes) to the current record
   function AppendInt32($value) {
      $this->AppendCurrent($this->Int32($value));
   }
   
   
   // Adds a double to the current record
   function AppendDouble($value) {
      $this->AppendCurrent($this->Double($value));
   }
   
   
   // Adds a string (not NULL-terminated)
   function AppendString($value, $maxLen = false) {
      $this->AppendCurrent($this->String($value, $maxLen));
   }
   
   
   // Returns true if the specified/current record exists and is set
   function RecordExists($Rec = false) {
      if ($Rec === false)
         $Rec = $this->CurrentRecord;
      if (isset($this->Records[$Rec]))
         return true;
      return false;
   }
   
   
   // Returns the hex-encoded data for the specified record or the current
   // record if not specified
   function GetRecord($Rec = false) {
      if ($Rec === false)
         $Rec = $this->CurrentRecord;
      if (isset($this->Records[$Rec]))
         return $this->Records[$Rec];
      return '';
   }
   
   
   // Returns the raw data inside the current/specified record.  Use this
   // for odd record types (like a Datebook record).  Also, use this
   // instead of just using $PDB->Records[] directly.
   function GetRecordRaw($Rec = false) {
      if ($Rec === false)
         $Rec = $this->CurrentRecord;
      if (isset($this->Records[$Rec]))
         return $this->Records[$Rec];
      return false;
   }
   
   
   // Sets the hex-encoded data (or whatever) for the current record
   // Use this instead of the Append* functions if you have an odd
   // type of record (like a Datebook record).
   // Also, use this instead of just setting $PDB->Records[]
   // directly.
   // SetRecordRaw('data');
   // SetRecordRaw(24, 'data');   (specifying the record num)
   function SetRecordRaw($A, $B = false) {
      if ($B === false) {
         $B = $A;
     $A = $this->CurrentRecord;
      }
      $this->Records[$A] = $B;
   }
   
   
   // Deletes the current record
   // You are urged to use GoToRecord() and jump to an existing record
   // after this function call so that the deleted record doesn't
   // get accidentally recreated/used -- all append functions will
   // create a new, empty record if the current record doesn't exist.
   function DeleteCurrentRecord() {
      if (isset($this->Records[$this->CurrentRecord]))
         unset($this->Records[$this->CurrentRecord]);
      if (isset($this->RecordAttrs[$this->CurrentRecord]))
         unset($this->RecordAttrs[$this->CurrentRecord]);
   }
   
   
   // Returns an array of available record IDs in the order they should
   // be written.
   // Probably should only be called within the class.
   function GetRecordIDs() {
      $keys = array_keys($this->Records);
      if (! is_array($keys) || count($keys) < 1)
         return array();
      sort($keys, SORT_NUMERIC);
      return $keys;
   }
   
   
   // Returns the number of records.  This should match the number of
   // keys returned by GetRecordIDs().
   function GetRecordCount() {
      return count($this->Records);
   }
   
   
   // Returns the size of the AppInfo block.
   // Used only for writing
   function GetAppInfoSize() {
      if (! isset($this->AppInfo))
         return 0;
      return strlen($this->AppInfo) / 2;
   }
   
   
   // Returns the AppInfo block (hex encoded)
   // Used only for writing
   function GetAppInfo() {
      if (! isset($this->AppInfo))
         return 0;
      return $this->AppInfo;
   }
   
   
   // Returns the size of the SortInfo block
   // Used only for writing
   function GetSortInfoSize() {
      if (! isset($this->SortInfo))
         return 0;
      return strlen($this->SortInfo) / 2;
   }
   
   
   // Returns the SortInfo block (hex encoded)
   // Used only for writing
   function GetSortInfo() {
      if (! isset($this->SortInfo))
         return 0;
      return $this->SortInfo;
   }
   
   
   /*
    * Category Support
    */
    
   // Creates the hex-encoded data to be stuck in the AppInfo
   // block if the database supports categories.
   //
   // Data format:
   //    $categoryArray[id#] = name
   // Or:
   //    $categoryArray[id#]['name'] = name
   //    $categoryArray[id#]['renamed'] = true / false
   //
   // Tips:
   //  * I'd suggest numbering your categories sequentially
   //  * Do not have a category 0.  It must always be 'Unfiled'.  This
   //    function will overwrite any category with the ID of 0.
   //  * There is a maximum of 16 categories, including 'Unfiled'.
   //
   // Category 0 is reserved for 'Unfiled'
   // Categories 1-127 are used for handheld ID numbers
   // Categories 128-255 are used for desktop ID numbers
   // Do not let category numbers be created larger than 255
   function CreateCategoryData($CategoryArray) {
      $CategoryArray[0] = array('Name' => 'Unfiled', 'Renamed' => false);
      $CatsWritten = 0;
      $LastIdWritten = 0;
      $RenamedFlags = 0;
      $CategoryStr = '';
      $IdStr = '';
      $keys = array_keys($CategoryArray);
      sort($keys);
      foreach ($keys as $id) {
         if ($CatsWritten < PDB_CATEGORY_NUM) {
        $CatsWritten ++;
        $LastIdWritten = $id;
        $RenamedFlags *= 2;
        if (is_array($CategoryArray[$id]) && 
            isset($CategoryArray[$id]['Renamed']) &&
        $CategoryArray[$id]['Renamed'])
           $RenamedFlags += 1;
        $name = '';
        if (is_array($CategoryArray[$id])) {
           if (isset($CategoryArray[$id]['Name']))
              $name = $CategoryArray[$id]['Name'];
        } else
           $name = $CategoryArray[$id];
        $name = $this->String($name, PDB_CATEGORY_NAME_LENGTH);
        $CategoryStr .= $this->PadString($name,
                                         PDB_CATEGORY_NAME_LENGTH);
        $IdStr .= $this->Int8($id);
     }
      }
     
      while ($CatsWritten < PDB_CATEGORY_NUM) {
         $CatsWritten ++;
     $LastIdWritten ++;
     $RenamedFlags *= 2;
     $CategoryStr .= $this->PadString('', PDB_CATEGORY_NAME_LENGTH);
     $IdStr .= $this->Int8($LastIdWritten);
      }
      
      $TrailingBytes = $this->Int8($LastIdWritten);
      $TrailingBytes .= $this->Int8(0);
     
      // Error checking
      if ($LastIdWritten >= 256)
         return $this->PadString('', PDB_CATEGORY_SIZE);
     
      return $this->Int16($RenamedFlags) . $CategoryStr . $IdStr . 
         $TrailingBytes;
   }
   
   
   // This should be called by other subclasses that use category support
   // It returns a category array.  Each element in the array is another
   // array with the key 'name' set to the name of the category and 
   // the key 'renamed' set to the renamed flag for that category.
   function LoadCategoryData($fileData) {
      $RenamedFlags = $this->LoadInt16(substr($fileData, 0, 2));
      $Offset = 2;
      $StartingFlag = 65536;
      $Categories = array();
      while ($StartingFlag > 1) {
         $StartingFlag /= 2;
     $Name = substr($fileData, $Offset, PDB_CATEGORY_NAME_LENGTH);
     $i = 0;
     while ($i < PDB_CATEGORY_NAME_LENGTH && $Name[$i] != "\0")
        $i ++;
     if ($i == 0)
        $Name = '';
     elseif ($i < PDB_CATEGORY_NAME_LENGTH)
        $Name = substr($Name, 0, $i);
     if ($RenamedFlags & $StartingFlag)
        $RenamedFlag = true;
     else
        $RenamedFlag = false;
     $Categories[] = array('Name' => $Name, 'Renamed' => $RenamedFlag);
     $Offset += PDB_CATEGORY_NAME_LENGTH;
      }
      
      $CategoriesParsed = array();
      
      foreach ($Categories as $CategoryData) {
         $UID = $this->LoadInt8(substr($fileData, $Offset, 1));
     $Offset ++;
     if ($CategoryData['Name'] != '')
        $CategoriesParsed[$UID] = $CategoryData;
      }
      
      // Ignore the last ID
      return $CategoriesParsed;
   }
   
   
   /*
    * Database Writing Functions
    */
   
   // *NEW*
   // Takes a hex-encoded string and makes sure that when decoded, the data
   // lies on a four-byte boundary.  If it doesn't, it pads the string with
   // NULLs
   /*
    * Commented out because we don't use this function currently.
    * It is part of a test to see what is needed to get files to sync
    * properly with Desktop 4.0
    *
   function PadTo4ByteBoundary($string) {
      while ((strlen($string)/2) % 4) {
         $string .= '00';
      }
      return $string;
   }
    *
    */
    
   // Returns the hex encoded header of the pdb file
   // Header = name, attributes, version, creation/modification/backup 
   //          dates, modification number, some offsets, record offsets,
   //          record attributes, appinfo block, sortinfo block
   // Shouldn't be called from outside the class
   function MakeHeader() {
      // 32 bytes = name, but only 31 available (one for null)
      $header = $this->String($this->Name, 31);
      $header = $this->PadString($header, 32);
      
      // Attributes & version fields
      $header .= $this->Int16($this->Attributes);
      $header .= $this->Int16($this->Version);
      
      // Creation, modification, and backup date
      if ($this->CreationTime != 0)
         $header .= $this->Int32($this->CreationTime + PDB_EPOCH_1904);
      else
         $header .= $this->Int32(time() + PDB_EPOCH_1904);
      if ($this->ModificationTime != 0)
         $header .= $this->Int32($this->ModificationTime + PDB_EPOCH_1904);
      else
         $header .= $this->Int32(time() + PDB_EPOCH_1904);
      if ($this->BackupTime != 0)
         $header .= $this->Int32($this->BackupTime + PDB_EPOCH_1904);
      else
         $header .= $this->Int32(0);
      
      // Calculate the initial offset
      $Offset = PDB_HEADER_SIZE + PDB_INDEX_HEADER_SIZE;
      $Offset += PDB_RECORD_HEADER_SIZE * count($this->GetRecordIDs());
      
      // Modification number, app information id, sort information id
      $header .= $this->Int32($this->ModNumber);
      
      $AppInfo_Size = $this->GetAppInfoSize();
      if ($AppInfo_Size > 0) {
         $header .= $this->Int32($Offset);
     $Offset += $AppInfo_Size;
      } else
         $header .= $this->Int32(0);
      
      $SortInfo_Size = $this->GetSortInfoSize();
      if ($SortInfo_Size > 0) {
         $header .= $this->Int32($Offset);
         $Offset += $SortInfo_Size;
      } else
         $header .= $this->Int32(0);
     
      // Type, creator
      $header .= $this->String($this->TypeID, 4);
      $header .= $this->String($this->CreatorID, 4);
      
      // Unique ID seed
      $header .= $this->Int32(0);
      
      // next record list
      $header .= $this->Int32(0);
      
      // Number of records
      $header .= $this->Int16($this->GetRecordCount());
      
      // Compensate for the extra 2 NULL characters in the $Offset
      $Offset += 2;
      
      // Dump each record
      if ($this->GetRecordCount() != 0) {
         $keys = $this->GetRecordIDs();
     sort($keys, SORT_NUMERIC);
     foreach ($keys as $index) {
        $header .= $this->Int32($Offset);
        if (isset($this->RecordAttrs[$index]))
           $header .= $this->Int8($this->RecordAttrs[$index]);
        else
           $header .= $this->Int8(0);
        
        // The unique id is just going to be the record number
        $header .= $this->Int24($index);
        
        $Offset += $this->GetRecordSize($index);
        // *new* method 3
        //$Mod4 = $Offset % 4;
        //if ($Mod4)
        //   $Offset += 4 - $Mod4;
     }
      }
      
      // These are the mysterious two NULL characters that we need
      $header .= $this->Int16(0);
      
      // AppInfo and SortInfo blocks go here
      if ($AppInfo_Size > 0)
         // *new* method 1
         $header .= $this->GetAppInfo();
         //$header .= $this->PadTo4ByteBoundary($this->GetAppInfo());
      
      if ($SortInfo_Size > 0)
         // *new* method 2
         $header .= $this->GetSortInfo();
         //$header .= $this->PadTo4ByteBoundary($this->GetSortInfo());

      return $header;
   }
   
   
   // Writes the database to the file handle specified.
   // Use this function like this:
   //   $file = fopen("output.pdb", "wb"); 
   //   // "wb" = write binary for non-Unix systems
   //   if (! $file) {
   //      echo "big problem -- can't open file";
   //      exit;
   //   }
   //   $pdb->WriteToFile($file);
   //   fclose($file);
   function WriteToFile($file) {
      $header = $this->MakeHeader();
      fwrite($file, pack('H*', $header), strlen($header) / 2);
      $keys = $this->GetRecordIDs();
      sort($keys, SORT_NUMERIC);
      foreach ($keys as $index) {
         // *new* method 3
         //$data = $this->PadTo4ByteBoundary($this->GetRecord($index));
         $data = $this->GetRecord($index);
     fwrite($file, pack('H*', $data), strlen($data) / 2);
      }
      fflush($file);
   }
   
   
   // Writes the database to the standard output (like echo).
   // Can be trapped with output buffering
   function WriteToStdout() {
      // You'd think these three lines would work.
      // If someone can figure out why they don't, please tell me.
      //
      // $fp = fopen('php://stdout', 'wb');
      // $this->WriteToFile($fp);
      // fclose($fp);
      
      $header = $this->MakeHeader();
      echo pack("H*", $header);
      $keys = $this->GetRecordIDs();
      sort($keys, SORT_NUMERIC);
      foreach ($keys as $index) {
         // *new* method 3
     $data = $this->GetRecord($index);
         //$data = $this->PadTo4ByteBoundary($this->GetRecord($index));
     echo pack("H*", $data);
      }
   }
   
   
   // Writes the database to the standard output (like echo) but also
   // writes some headers so that the browser should prompt to save the
   // file properly.
   //
   // Use this only if you didn't send any content and you only want the
   // PHP script to output the PDB file and nothing else.  An example
   // would be if you wanted to have 'download' link so the user can
   // stick the information they are currently viewing and transfer
   // it easily into their handheld.
   //
   // $filename is the desired filename to download the database as.
   // For example, DownloadPDB('memos.pdb');
   function DownloadPDB($filename)
   {
      // Alter the filename to only allow certain characters.
      // Some platforms and some browsers don't respond well if
      // there are illegal characters (such as spaces) in the name of
      // the file being downloaded.
      $filename = preg_replace('/[^-a-zA-Z0-9\\.]/', '_', $filename);
      
      if (strstr($_SERVER['HTTP_USER_AGENT'], 'compatible; MSIE ') !== false &&
          strstr($_SERVER['HTTP_USER_AGENT'], 'Opera') === false) {
     // IE doesn't properly download attachments.  This should work
     // pretty well for IE 5.5 SP 1
     header("Content-Disposition: inline; filename=$filename");
     header("Content-Type: application/download; name=\"$filename\"");
      } else {
         // Use standard headers for Netscape, Opera, etc.
     header("Content-Disposition: attachment; filename=\"$filename\"");
     header("Content-Type: application/x-pilot; name=\"$filename\"");
      }
      
      $this->WriteToStdout();
   }
   
   
   /*
    * Loading in a database
    */
       
   // Reads data from the file and tries to load it properly
   // $file is the already-opened file handle.
   // Returns false if no error
   function ReadFile($file) {
      // 32 bytes = name, but only 31 available
      $this->Name = fread($file, 32);
      
      $i = 0;
      while ($i < 32 && $this->Name[$i] != "\0")
         $i ++;
      $this->Name = substr($this->Name, 0, $i);
      
      $this->Attributes = $this->LoadInt16($file);
      $this->Version = $this->LoadInt16($file);
      
      $this->CreationTime = $this->LoadInt32($file);
      if ($this->CreationTime != 0)
         $this->CreationTime -= PDB_EPOCH_1904;
      if ($this->CreationTime < 0)
         $this->CreationTime = 0;
        
      $this->ModificationTime = $this->LoadInt32($file);
      if ($this->ModificationTime != 0)
         $this->ModificationTime -= PDB_EPOCH_1904;
      if ($this->ModificationTime < 0)
         $this->ModificationTime = 0;
        
      $this->BackupTime = $this->LoadInt32($file);
      if ($this->BackupTime != 0)
         $this->BackupTime -= PDB_EPOCH_1904;
      if ($this->BackupTime < 0)
         $this->BackupTime = 0;

      // Modification number
      $this->ModNumber = $this->LoadInt32($file);
      
      // AppInfo and SortInfo size
      $AppInfoOffset = $this->LoadInt32($file);
      $SortInfoOffset = $this->LoadInt32($file);
      
      // Type, creator
      $this->TypeID = fread($file, 4);
      $this->CreatorID = fread($file, 4);
      
      // Skip unique ID seed
      fread($file, 4);
      
      // skip next record list (hope that's ok)
      fread($file, 4);
      
      $RecCount = $this->LoadInt16($file);
      
      $RecordData = array();
      
      while ($RecCount > 0) {
         $RecCount --;
     $Offset = $this->LoadInt32($file);
     $Attrs = $this->LoadInt8($file);
     $UID = $this->LoadInt24($file);
     $RecordData[] = array('Offset' => $Offset, 'Attrs' => $Attrs,
                           'UID' => $UID);
      }
      
      // Create the offset list
      if ($AppInfoOffset != 0)
         $OffsetList[$AppInfoOffset] = 'AppInfo';
      if ($SortInfoOffset != 0)
         $OffsetList[$SortInfoOffset] = 'SortInfo';
      foreach ($RecordData as $data)
         $OffsetList[$data['Offset']] = array('Record', $data);
      fseek($file, 0, SEEK_END);
      $OffsetList[ftell($file)] = 'EOF';
      
      // Parse each chunk
      ksort($OffsetList);
      $Offsets = array_keys($OffsetList);
      while (count($Offsets) > 1) {
         // Don't use the EOF (which should be the last offset)
     $ThisOffset = $Offsets[0];
     $NextOffset = $Offsets[1];
     if ($OffsetList[$ThisOffset] == 'EOF')
        // Messed up file.  Stop here.
        return true;
     $FuncName = 'Load';
     if (is_array($OffsetList[$ThisOffset])) {
        $FuncName .= $OffsetList[$ThisOffset][0];
        $extraData = $OffsetList[$ThisOffset][1];
     } else {
        $FuncName .= $OffsetList[$ThisOffset];
        $extraData = false;
     }
     fseek($file, $ThisOffset);
     $fileData = fread($file, $NextOffset - $ThisOffset);
     if ($this->$FuncName($fileData, $extraData))
        return -2;
     array_shift($Offsets);
      }
      
      return false;
   }

  
   // Generic function to load the AppInfo block into $this->AppInfo
   // Should only be called within this class
   // Return false to signal no error
   function LoadAppInfo($fileData) {
      $this->AppInfo = bin2hex($fileData);
      return false;
   }
   
   
   // Generic function to load the SortInfo block into $this->SortInfo
   // Should only be called within this class
   // Return false to signal no error
   function LoadSortInfo($fileData) {
      $this->SortInfo = bin2hex($fileData);
      return false;
   }
   
   
   // Generic function to load a record
   // Should only be called within this class
   // Return false to signal no error
   function LoadRecord($fileData, $recordInfo) {
      $this->Records[$recordInfo['UID']] = bin2hex($fileData);
      $this->RecordAttrs[$recordInfo['UID']] = $recordInfo['Attrs'];
      return false;
   }

}
