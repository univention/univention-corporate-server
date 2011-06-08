'*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+
' Generator   : PPWIZARD version 08.307
'             : FREE tool for Windows, OS/2, DOS and UNIX by Dennis Bareis (dbareis@gmail.com)
'             : http://dennisbareis.com/ppwizard.htm
' Time        : Tuesday, 28 Sep 2010 2:57:01pm
' Input File  : Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector\installscript.mm
' Output File : Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector\out\installscript.mm\Log\Pass1+2.vbs
'*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+*+


option explicit         'All variables must be defined
if Wscript.Arguments.Count = 1 then if Wscript.Arguments(0) = "!CheckSyntax!" then wscript.quit(21924)
if ucase(mid(wscript.FullName, len(wscript.Path) + 2, 1)) = "W" Then
wscript.echo "You can't use WSCRIPT on this VB script, use CSCRIPT instead!"
wscript.quit 987
end if
public StartTime : StartTime = timer()
public MmLL : MmLL = "Start"
public MmLT : MmLT = "Initializing..."
public MmID : MmID = ""
public Pass
if  wscript.arguments.count = 0 then
Pass = "1"
else
Pass = "2"
if  wscript.arguments.count > 1 then
error "Too many arguments found, expected at most one, got " & wscript.arguments.count
end if
end if
on error resume next
SimpleTestToDetectInCompleteVbscriptForPass1()       'Will only fail if the subroutine for pass #1 is missing!
if err.number <> 0 then
wscript.echo ""
wscript.echo "The generated VBSCRIPT for pass 1 appears incomplete:"
wscript.echo ""
wscript.echo "   * " & wscript.ScriptFullName
wscript.echo ""
wscript.echo "This can happen if you don't have correct nesting of some macros,"
wscript.echo "for example, if a ""<" & "$VbsCa...>"" command doesn't have a"
wscript.echo "matching ""<" & "$/VbsCa>"" command."
wscript.echo ""
wscript.echo "If you look at the end of the vbscript you should be able to"
wscript.echo "easily identify the problem area."
wscript.quit 876
end if
on error goto 0
dim MsgWsh : MsgWsh     = "It is possible that you have an anti-virus or anti-spyware program that is" & vbCRLF & "causing this but its more likely that your computer's Windows Scripting" & vbCRLF & "Host (WSH) installation has been corrupted." & vbCRLF & vbCRLF & "Try downloading and reinstalling from Microsoft's site:" & vbCRLF & "    http://www.microsoft.com/downloads/"
dim oShell : set oShell = MkObjectWithHelp("Wscript.Shell",              MsgWsh)
dim oFs    : set oFs    = MkObjectWithHelp("Scripting.FileSystemObject", MsgWsh)


const ForReading   = 1
const ForWriting   = 2
const ForAppending = 8
const TemporaryFolder = 2
const AttributeReadOnly = 1
const RegNtfs83NamesTurnedOff = "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem\NtfsDisable8dot3NameCreation"
dim TmpDir : TmpDir = "C:\DOKUME~1\stegoh\LOKALE~1\Temp\MAKEMSI.TMP"        'oFS.GetSpecialFolder(TemporaryFolder)


const msiOpenDatabaseModeReadOnly     = 0
const msiOpenDatabaseModeTransact     = 1
const msiOpenDatabaseModeDirect       = 2
const msiOpenDatabaseModeCreate       = 3
const msiOpenDatabaseModeCreateDirect = 4


const msidbControlAttributesVisible      = &H00000001
const msidbControlAttributesEnabled      = &H00000002
const msidbControlAttributesSunken       = &H00000004
const msidbControlAttributesInteger      = &H00000010
const msidbControlAttributesRightAligned = &H00000040
const msidbControlAttributesTransparent  = &H00010000
const msidbControlAttributesSorted       = &H00010000
const msidbControlAttributesNoPrefix     = &H00020000
const msidbControlAttributesComboList    = &H00020000
const msidbControlAttributesNoWrap       = &H00040000
const msidbControlAttributesFixedSize    = &H00100000
const msidbControlAttributesPasswordInput= &H00200000


const CATYPE_MSI_IN_STORAGES_TABLE             = 7
const CATYPE_MSI_IN_MSI_SOURCE_TREE            = 23


const msidbCustomActionTypeContinue      = &H0040
const msidbCustomActionTypeAsync         = &H0080
const msidbCustomActionTypeRollback      = &H0100
const msidbCustomActionTypeCommit        = &H0200
const msidbCustomActionTypeInScript      = &H0400
const msidbCustomActionTypeNoImpersonate = &H0800



dim oDir1ParentShort  : set oDir1ParentShort = MkObject("Scripting.Dictionary")
dim Need83BaseDir, oNeed83BaseDir
Need83NameStart()
dim SeqNo, SeqCad, SeqProp
public oTableFlds      : set oTableFlds      = MkObject("Scripting.Dictionary")
public oTableCreateSql : set oTableCreateSql = MkObject("Scripting.Dictionary")
InitTableInfo()
const HKEY_CURRENT_USER_OR_LOCAL_MACHINE = -1
const HKEY_CLASSES_ROOT                  =  0
const HKEY_CURRENT_USER                  =  1
const HKEY_LOCAL_MACHINE                 =  2
const HKEY_USERS                         =  3
const msidbLocatorTypeRawValue = 2     '0x02
const msidbLocatorType64bit    = 16    '0x10
dim InLineScript


const PID_CODEPAGE     = 1
const PID_TITLE        = 2
const PID_SUBJECT      = 3
const PID_AUTHOR       = 4
const PID_KEYWORDS     = 5
const PID_COMMENTS     = 6
const PID_TEMPLATE     = 7
const PID_LASTAUTHOR   = 8
const PID_REVNUMBER    = 9
const PID_PACKAGECODE  = 9
const PID_EDITTIME     = 10
const PID_LASTPRINTED  = 11
const PID_CREATE_DTM   = 12
const PID_LASTSAVE_DTM = 13
const PID_PAGECOUNT    = 14
const PID_MsiSchema    = 14
const PID_WORDCOUNT    = 15
const PID_SourceType   = 15
const PID_CHARCOUNT    = 16
const PID_APPNAME      = 18
const PID_SECURITY     = 19


const msidbSumInfoSourceTypeSFN        = &H01
const msidbSumInfoSourceTypeCompressed = &H02
const msidbSumInfoSourceTypeAdminImage = &H04
const msidbSumInfoSourceTypeLUAPackage = &H08


const PidSecurityNoRestriction       = 0
const PidSecurityReadOnlyRecommended = 2
const PidSecurityReadOnlyEnforced    = 4
const msidbFeatureAttributesFavorLocal             = &H0000
const msidbFeatureAttributesFavorSource            = &H0001
const msidbFeatureAttributesFollowParent           = &H0002
const msidbFeatureAttributesFavorAdvertise         = &H0004
const msidbFeatureAttributesDisallowAdvertise      = &H0008
const msidbFeatureAttributesUIDisallowAbsent       = &H0010
const msidbFeatureAttributesNoUnsupportedAdvertise = &H0020
const msidbComponentAttributesLocalOnly                 = &H0000
const msidbComponentAttributesSourceOnly                = &H0001
const msidbComponentAttributesOptional                  = &H0002
const msidbComponentAttributesRegistryKeyPath           = &H0004
const msidbComponentAttributesSharedDllRefCount         = &H0008
const msidbComponentAttributesPermanent                 = &H0010
const msidbComponentAttributesODBCDataSource            = &H0020
const msidbComponentAttributesTransitive                = &H0040
const msidbComponentAttributesNeverOverwrite            = &H0080
const msidbComponentAttributes64bit                     = &H0100
const msidbComponentAttributesDisableRegistryReflection = &H0200
const msidbComponentAttributesUninstallOnSupersedence   = &H0400
const msidbComponentAttributesShared                    = &H0800
public CompGuid : CompGuid = ""
dim ob_FileLastSeqNumber          : ob_FileLastSeqNumber          = 0
dim ob_RecordedFirstFileSeqNumber : ob_RecordedFirstFileSeqNumber = false
const msidbFileAttributesReadOnly            = &H000001
const msidbFileAttributesHidden              = &H000002
const msidbFileAttributesSystem              = &H000004
const msidbFileAttributesVital               = &H000200
const msidbFileAttributesChecksum            = &H000400
const msidbFileAttributesPatchAdded          = &H001000
const msidbFileAttributesNoncompressed       = &H002000
const msidbFileAttributesCompressed          = &H004000
public CurrentFileKey, CurrentFileVersion,  CurrentFile, CurrentFileNameSL
dim    SelfRegNeeded
const SW_SHOWNORMAL      = 1
const SW_SHOWMAXIMIZED   = 3
const SW_SHOWMINNOACTIVE = 7
const msidbRemoveFileInstallModeOnInstall = 1
const msidbRemoveFileInstallModeOnRemove  = 2
const msidbRemoveFileInstallModeOnBoth    = 3
dim MergeModuleFullName
dim MergeModuleLog
dim MergeObjectName, oMerge
dim oMergeProperty, MergePropertyCnt
dim oDepend, oError, Item, TypeString, HelpString
dim MergeErrors, MergeErrorsFatal, MergeErrorsIgnoreParm, MergeErrorsTables, MergeDependErrors, DepKey, ErrCmt
dim nc_ErrKey
dim MmIgnore, MmCnt, MmKey
dim MmDbKey,  MmDbTable
dim MmModKey, MmModTable
dim MmErrKey, MmErrTable, MmErrIn
dim MergedFileKey
dim MmModuleTableText
dim MmConfigurableItems
dim MmDiskPrompt, MmVolumeLabel
dim nc_AlreadyMerged : nc_AlreadyMerged = false
dim oMmErrorType : set oMmErrorType = MkObject("Scripting.Dictionary")
dim oMmErrorHelp : set oMmErrorHelp = MkObject("Scripting.Dictionary")
oMmErrorType.add "1", "msmErrorLanguageUnsupported"
oMmErrorType.add "2", "msmErrorLanguageFailed"
oMmErrorType.add "3", "msmErrorExclusion"
oMmErrorType.add "4", "msmErrorTableMerge"
oMmErrorType.add "5", "msmErrorResequenceMerge"
oMmErrorHelp.add "5", "Bug in merge module - invalid 'BaseAction'"
oMmErrorType.add "6", "msmErrorFileCreate"
oMmErrorType.add "7", "msmErrorDirCreate"
oMmErrorType.add "8", "msmErrorFeatureRequired"
oMmErrorType.add "9", "msmErrorBadNullSubstitution"
oMmErrorType.add "10", "msmErrorBadSubstitutionType"
oMmErrorType.add "11", "msmErrorMissingConfigItem"
oMmErrorType.add "12", "msmErrorBadNullResponse"
oMmErrorType.add "13", "msmErrorDataRequestFailed"
oMmErrorType.add "14", "msmErrorPlatformMismatch"
dim oMmIgnoreTheseErrors : set oMmIgnoreTheseErrors = MkObject("Scripting.Dictionary")
const msiUILevelNone             = 2
const msiRunModeSourceShortNames = 9


const msidbServiceControlEventStart           = &H001
const msidbServiceControlEventStop            = &H002
const msidbServiceControlEventDelete          = &H008
const msidbServiceControlEventUninstallStart  = &H010
const msidbServiceControlEventUninstallStop   = &H020
const msidbServiceControlEventUninstallDelete = &H080
const SERVICE_WIN32_OWN_PROCESS   = &H010
const SERVICE_WIN32_SHARE_PROCESS = &H020
const SERVICE_INTERACTIVE_PROCESS = &H100
const SERVICE_AUTO_START    = &H02
const SERVICE_DEMAND_START  = &H03
const SERVICE_DISABLED      = &H04
const SERVICE_BOOT_START    = &H00
const SERVICE_SYSTEM_START  = &H01
const SERVICE_ERROR_IGNORE                 = &H00
const SERVICE_ERROR_NORMAL                 = &H01
const SERVICE_ERROR_CRITICAL               = &H03
const msidbServiceInstallErrorControlVital = 32768    '&H08000 (stupid VB does 16 bit 2's comp!)


const msidbIniFileActionAddLine    = 0
const msidbIniFileActionCreateLine = 1
const msidbIniFileActionAddTag     = 3


dim TransformingFile : TransformingFile = ""     'MSI being updated by user (not updated by time transform is created!)
dim WantedMstFile    : WantedMstFile    = ""     'If non-blank then user wants an MST created
const msiTransformErrorNone                   = 0    'None of the following conditions.
const msiTransformErrorAddExistingRow         = 1    'Adding a row that already exists.
const msiTransformErrorDeleteNonExistingRow   = 2    'Deleting a row that doesn't exist.
const msiTransformErrorAddExistingTable       = 4    'Adding a table that already exists.
const msiTransformErrorDeleteNonExistingTable = 8    'Deleting a table that doesn't exist.
const msiTransformErrorUpdateNonExistingRow   = 16   'Updating a row that doesn't exist.
const msiTransformErrorChangeCodepage         = 32   'Transform and database code pages do not match and neither code page is neutral.
const msiTransformValidationNone           =    0  'No validation done.
const msiTransformValidationLanguage       =    1  'Default language must match base database.
const msiTransformValidationProduct        =    2  'Product must match base database.
const msiTransformValidationMajorVer       =    8  'Check major version only.
const msiTransformValidationMinorVer       =   16  'Check major and minor version only.
const msiTransformValidationUpdateVer      =   32  'Check major, minor, and update versions.
const msiTransformValidationLess           =   64  'Applied version < base version
const msiTransformValidationLessOrEqual    =  128  'Applied version <= base version
const msiTransformValidationEqual          =  256  'Applied version = base version
const msiTransformValidationGreaterOrEqual =  512  'Applied version >= base version
const msiTransformValidationGreater        = 1024  'Applied version > base version
const msiTransformValidationUpgradeCode    = 2048  'Validates that the transform is the appropriate UpgradeCode.


dim cb_PlCntr
dim cb_PropValue


dim FileFindSL



'--- "Upgrade" table attributes ---
const msidbUpgradeAttributesMigrateFeatures     = &H001      'Migrate feature states by enabling the logic in the MigrateFeatureStates action.
const msidbUpgradeAttributesOnlyDetect          = &H002      'Detect products and applications but do not install.
const msidbUpgradeAttributesIgnoreRemoveFailure = &H004      'Continue installation upon failure to remove a product or application.
const msidbUpgradeAttributesVersionMinInclusive = &H100      'The range of versions detected includes the value in VersionMin.
const msidbUpgradeAttributesVersionMaxInclusive = &H200      'The range of versions detected includes the value in VersionMax.
const msidbUpgradeAttributesLanguagesExclusive  = &H400      'Detect all languages, excluding the languages listed in the Language column.



const MsiViewModifyInsert        = 1
const MsiViewModifyUpdate        = 2
const MsiViewModifyAssign        = 3
const MsiViewModifyReplace       = 4
const MsiViewModifyValidate      = 8
const MsiViewModifyValidateNew   = 9
const MsiViewModifyValidateField = 10
const msiColumnInfoTypes         = 1
const msiDatabaseNullInteger = &h80000000
dim RowValidationExclusions()
dim RowValidationExclusions4Human()
if  Pass = "1" then
SetupRowValidationExclusionList_1()
else
SetupRowValidationExclusionList_2()
end if


dim oValidateErrTxt : set oValidateErrTxt = MkObject("Scripting.Dictionary")
oValidateErrTxt.add "-3", "(INVALIDARG) An argument was invalid."
oValidateErrTxt.add "-2", "(MOREDATA) The buffer was too small to receive data."
oValidateErrTxt.add "-1", "(FUNCTIONERROR) The function failed."
oValidateErrTxt.add "01", "(DUPLICATEKEY) The new record duplicates primary keys of the existing record in a table."
oValidateErrTxt.add "02", "(REQUIRED) There are no NULL values allowed, or the column is about to be deleted but is referenced by another row."
oValidateErrTxt.add "03", "(BADLINK) The corresponding record in a foreign table was not found."
oValidateErrTxt.add "04", "(OVERFLOW) The data is greater than the maximum value allowed."
oValidateErrTxt.add "05", "(UNDERFLOW) The data is less than the minimum value allowed."
oValidateErrTxt.add "06", "(NOTINSET) The data is not a member of the values permitted in the set (see _Validation table)."
oValidateErrTxt.add "07", "(BADVERSION) An invalid version string was supplied."
oValidateErrTxt.add "08", "(BADCASE) Mixed case is not allowed (must be all upper or lower)."
oValidateErrTxt.add "09", "(BADGUID) An invalid GUID was supplied. Note that any letters must be UPPER case."
oValidateErrTxt.add "10", "(BADWILDCARD) An invalid wildcard file name was supplied, or the use of wildcards was invalid. The name is assumed to be in '8.3' format unless both both 8.3 and long versions supplied (example 'ABCDEF~1.TXT|abcdefgh ij.txt')."
oValidateErrTxt.add "11", "(BADIDENTIFIER) An invalid identifier was supplied. An identifier must begin with either a letter or an underscore which is followed by zero or more letters, digits, underscores ('_'), or periods ('.')"
oValidateErrTxt.add "12", "(BADLANGUAGE) Invalid language IDs were supplied."
oValidateErrTxt.add "13", "(BADFILENAME) An invalid file name was supplied. The name is assumed to be in '8.3' format unless both both 8.3 and long versions supplied (example 'ABCDEF~1.TXT|abcdefgh ij.txt')."
oValidateErrTxt.add "14", "(BADPATH) An invalid path was supplied."
oValidateErrTxt.add "15", "(BADCONDITION) An invalid conditional statement was supplied."
oValidateErrTxt.add "16", "(BADFORMATTED) An invalid formatted string was supplied. You probably need to ""escape"" characters such as curley or square brackets (encode ""["" as ""[\[]"" etc)."
oValidateErrTxt.add "17", "(BADTEMPLATE) An invalid template string was supplied."
oValidateErrTxt.add "18", "(BADDEFAULTDIR) An invalid string was supplied in the DefaultDir column of the Directory table."
oValidateErrTxt.add "19", "(BADREGPATH) An invalid registry path string was supplied."
oValidateErrTxt.add "20", "(BADCUSTOMSOURCE) An invalid string was supplied in the CustomSource column of the CustomAction table."
oValidateErrTxt.add "21", "(BADPROPERTY) An invalid property string was supplied."
oValidateErrTxt.add "22", "(MISSINGDATA) This column is not mentioned in the _Validation table. Either add the validation data or use the ""@validate"" parameter on the ""row"" command (or alter its default)."
oValidateErrTxt.add "23", "(BADCATEGORY) The category column of the _Validation table for the column is invalid."
oValidateErrTxt.add "24", "(BADKEYTABLE) The table in the Keytable column of the _Validation table was not found or loaded."
oValidateErrTxt.add "25", "(BADMAXMINVALUES) The value in the MaxValue column of the _Validation table is less than the value in the MinValue column."
oValidateErrTxt.add "26", "(BADCABINET) An invalid cabinet name was supplied."
oValidateErrTxt.add "27", "(BADSHORTCUT) An invalid shortcut target name was supplied."
oValidateErrTxt.add "28", "(STRINGOVERFLOW) The string is too long for the length specified by the column definition."
oValidateErrTxt.add "29", "(BADLOCALIZEATTRIB) An invalid localization attribute was supplied (Primary keys cannot be localized)."


dim oPreview : set oPreview = Nothing
dim DlgFind, DlgPrev, DlgNext, DlgArgument
dim SrComponent, SrDirectory     'Used by "SELFREG.MMH"
dim pc_COMPILE_CABDDF_Compress : pc_COMPILE_CABDDF_Compress = "?"
dim pc_COMPILE_CABDDF_CompressionType : pc_COMPILE_CABDDF_CompressionType = "?"
dim pc_COMPILE_CABDDF_CompressionLevel : pc_COMPILE_CABDDF_CompressionLevel = "?"
dim pc_COMPILE_CABDDF_CompressionMemory : pc_COMPILE_CABDDF_CompressionMemory = "?"
dim pc_COMPILE_CABDDF_ClusterSize : pc_COMPILE_CABDDF_ClusterSize = "?"
dim pc_COMPILE_CAB_FILE_NAME : pc_COMPILE_CAB_FILE_NAME = "?"


public CurrentTable       : CurrentTable       = ""
public CurrentTableFields : CurrentTableFields = ""
public oView : set oView = Nothing
public oRec  : set oRec  = Nothing
public RecCnt: RecCnt= 0
dim MsiErrorIgnore : MsiErrorIgnore = false
dim Dying     : Dying     = false
on error goto 0
public MsiFileName    : MsiFileName   = ""
public CommitOnError  : CommitOnError = false
public oMsi           : set oMsi      = Nothing
public oInstaller     : set oInstaller = MkObject("WindowsInstaller.Installer")
public oSummary : set oSummary = Nothing
if  Pass = "1" then
public oRetStream
set oRetStream = oFS.CreateTextFile("Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector\out\installscript.mm\Log\FromPass1.TXT", true)
oRetStream.WriteLine ";==="
oRetStream.WriteLine ";=== Generated by PASS1 of : Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector\out\installscript.mm\Log\Pass1+2.vbs"
oRetStream.WriteLine ";==="
oRetStream.WriteLine ""
end if
say ""
say Title(GetAmPmTime() & ": MAKEMSI version 10.169 - PASS " & Pass)
OutputEnvironmentalVersionInformation()



if  Pass = "2" then
MmLL = "Pass 2 (Merge Modules & Compile)"
MmLT = "Initializing..."
on error resume next
SimpleTestToDetectInCompleteVbscriptForPass2()       'Will only fail if the subroutine for pass #2 is missing!
if err.number <> 0 then
wscript.echo ""
wscript.echo "The generated VBSCRIPT for pass 2 appears incomplete:"
wscript.echo ""
wscript.echo "   * " & wscript.ScriptFullName
wscript.echo ""
wscript.echo "This can happen if you don't have correct nesting of some macros,"
wscript.echo "for example, if a ""<" & "$VbsCa...>"" command doesn't have a"
wscript.echo "matching ""<" & "$/VbsCa>"" command."
wscript.echo ""
wscript.echo "If you look at the end of the vbscript you should be able to"
wscript.echo "easily identify the problem area."
wscript.quit 876
end if
on error goto 0
SecondPassProcessing()           'Won't exist unless we plan on doing Pass 2 (and won't exist until after pass 1 executed!)
VbsQuit 0
end if
CompileInitializationAtStartOfPass1()






'######################################################################
MmLL = "COMPANY.MMH(182)"
MmLT = "<$COMPANY_GET_TEMPLATE_AND_OPEN_MSI>"
'######################################################################


MmID = "@VBS0001"

CreateDir( oFS.GetParentFolderName("Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector\out\installscript.mm\MSI\setup.msi") )
dim oMsiFile
say "Creating a new MSI (template based)"
say "Creating ""Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector\out\installscript.mm\MSI\setup.msi"""
say "From ""C:\Programme\MakeMsi\UISAMPLE.msi"""
TransformingFile = "C:\Programme\MakeMsi\UISAMPLE.msi"
if  not oFS.FileExists("C:\Programme\MakeMsi\UISAMPLE.msi") then
Error("The template MSI ""C:\Programme\MakeMsi\UISAMPLE.msi"" does not exist!")
end if
on error resume next
oFS.CopyFile "C:\Programme\MakeMsi\UISAMPLE.msi", "Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector\out\installscript.mm\MSI\setup.msi", true
VbsCheck "Copying the template MSI file"
set oMsiFile = oFS.GetFile("Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector\out\installscript.mm\MSI\setup.msi")
if oMsiFile.Attributes and AttributeReadOnly then
oMsiFile.Attributes = oMsiFile.Attributes - AttributeReadOnly
end if
on error goto 0
set oMsiFile = Nothing
if  not oFS.FileExists("Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector\out\installscript.mm\MSI\setup.msi") then
Error("The MSI file ""Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector\out\installscript.mm\MSI\setup.msi"" does not exist!")
end if
MsiOpen "Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector\out\installscript.mm\MSI\setup.msi", msiOpenDatabaseModeDirect, true

MmID = "@VBS0002"
TableNowMk "LaunchCondition"
 

MmID = "@VBS0003"
RowPrepare 2

MmID = "@VBS0004"
oRec.StringData(1) = "NoSuchProperty.so.always.false"
oRec.StringData(2) = "This MSI can't be installed as a MAKEMSI build or update did not successfully complete. " & vbCRLF & "" & vbCRLF & "The failing script ""installscript.mm"" was executed at Tue Sep 28 2010 at 2:57:01pm."
ValidateNEW(0)
RowUpdate()
 

MmID = "@VBS0005"
TableNow ""


MmID = "@VBS0006"
SummaryItem PID_AUTHOR, "Dennis Bareis"

MmID = "@VBS0007"
SummaryItem PID_COMMENTS, "MSI generated by MakeMsi version 10.169, a free tool by Dennis Bareis (http://dennisbareis.com/makemsi.htm)"

MmID = "@VBS0008"
SummaryItem PID_AppName, "MakeMsi version 10.169, a free tool by Dennis Bareis (http://dennisbareis.com/makemsi.htm)"

MmID = "@VBS0009"
SummaryItem PID_LASTSAVE_DTM, now()

if  TableExists("Property") then

MmID = "@VBS0010"
cb_PropValue = "MSI generated by MakeMsi version 10.169, a free tool by Dennis Bareis (http://dennisbareis.com/makemsi.htm)"

MmID = "@VBS0011"
TableNowMk "Property"
   if cb_PropValue = "" then

MmID = "@VBS0012"
DeleteTableRows("`Property` = 'ARPCOMMENTS'")
   else

MmID = "@VBS0013"
RowPrepare 2

MmID = "@VBS0014"
oRec.StringData(1) = "ARPCOMMENTS"
oRec.StringData(2) = cb_PropValue
ValidateFIELD(1)
RowUpdate()
   end if

MmID = "@VBS0015"
TableNow ""

end if




'######################################################################
MmLL = "COMPANY.MMH(225)"
MmLT = "<$Summary ""Security"" *Value=^<$COMPANY_SECURITY_VALUE_VBEXP>^>"
'######################################################################


MmID = "@VBS0016"
SummaryItem PID_Security, PidSecurityNoRestriction



'######################################################################
MmLL = "COMPANY.MMH(256)"
MmLT = "<$Table ""Error"">"
'######################################################################


MmID = "@VBS0017"
TableNowMk "Error"



'######################################################################
MmLL = "COMPANY.MMH(258)"
MmLT = "<$@@ErrorMsg ""1335"">"
'######################################################################


MmID = "@VBS0018"
RowPrepare 2

MmID = "@VBS0019"
oRec.IntegerData(1) = 1335
oRec.StringData(2) = "The required cabinet file '[2]' may be corrupt or we could not create a file during extraction. This could indicate a network error, an error reading from the CD-ROM, a problem with this package, or perhaps a problem extracting a file (destination path too long?)."
ValidateFIELD(1)
RowUpdate()



'######################################################################
MmLL = "COMPANY.MMH(261)"
MmLT = "<$@@ErrorMsg ""1720"">"
'######################################################################


MmID = "@VBS0020"
RowPrepare 2

MmID = "@VBS0021"
oRec.IntegerData(1) = 1720
oRec.StringData(2) = "CUSTOM ACTION SCRIPT ""[2]"" COULDN'T START (OR TRAPPED DURING INITIALIZATION*). ERROR [3], [4]: [5] LINE [6], COLUMN [7], [8]"
ValidateFIELD(1)
RowUpdate()



'######################################################################
MmLL = "COMPANY.MMH(262)"
MmLT = "<$@@ErrorMsg ""2740"">"
'######################################################################


MmID = "@VBS0022"
RowPrepare 2

MmID = "@VBS0023"
oRec.IntegerData(1) = 2740
oRec.StringData(2) = "CUSTOM ACTION SCRIPT ""[2]"" STARTED BUT FAILED. ERROR [3], [4]: [5] LINE [6], COLUMN [7], [8]"
ValidateFIELD(1)
RowUpdate()



'######################################################################
MmLL = "COMPANY.MMH(265)"
MmLT = "<$@@ErrorMsg ""2705""> ;;ICE03 error at validation time, but if not validating..."
'######################################################################


MmID = "@VBS0024"
RowPrepare 2

MmID = "@VBS0025"
oRec.IntegerData(1) = 2705
oRec.StringData(2) = "Invalid table: ""[2]"" - Could not be linked as tree (this can occur if a directory tables ""parent"" directory is missing)."
ValidateFIELD(1)
RowUpdate()



'######################################################################
MmLL = "COMPANY.MMH(268)"
MmLT = "<$@@ErrorMsg ""1721"">"
'######################################################################


MmID = "@VBS0026"
RowPrepare 2

MmID = "@VBS0027"
oRec.IntegerData(1) = 1721
oRec.StringData(2) = "CUSTOM ACTION ""[2]"" FAILED (could not start it). LOCATION: [3], COMMAND: [4]"
ValidateFIELD(1)
RowUpdate()



'######################################################################
MmLL = "COMPANY.MMH(269)"
MmLT = "<$@@ErrorMsg ""1722"">"
'######################################################################


MmID = "@VBS0028"
RowPrepare 2

MmID = "@VBS0029"
oRec.IntegerData(1) = 1722
oRec.StringData(2) = "CUSTOM ACTION ""[2]"" FAILED (unexpected return code). LOCATION: [3], COMMAND: [4]"
ValidateFIELD(1)
RowUpdate()



'######################################################################
MmLL = "COMPANY.MMH(272)"
MmLT = "<$@@ErrorMsg ""2103"">"
'######################################################################


MmID = "@VBS0030"
RowPrepare 2

MmID = "@VBS0031"
oRec.IntegerData(1) = 2103
oRec.StringData(2) = "Could not resolve path for the shell folder ""[2]"". If the MSI is being executed under the SYSTEM account then remember that you must have ALLUSERS=1."
ValidateFIELD(1)
RowUpdate()



'######################################################################
MmLL = "COMPANY.MMH(273)"
MmLT = "<$@@ErrorMsg ""2755"">"
'######################################################################


MmID = "@VBS0032"
RowPrepare 2

MmID = "@VBS0033"
oRec.IntegerData(1) = 2755
oRec.StringData(2) = "The server process failed processing the package ""[3]"" (RC = [2]). A return code of 3 probably indicates a problem accessing the drive or directory (substituted drives and network drives can be problematic). A return code of 110 probably indicates an error opening the MSI file (this can occur if the MSI is encrypted). Try moving the MSI to C:\ (make sure its not compressed or encrypted)."
ValidateFIELD(1)
RowUpdate()



'######################################################################
MmLL = "COMPANY.MMH(276)"
MmLT = "<$@@ErrorMsg ""1909"">"
'######################################################################


MmID = "@VBS0034"
RowPrepare 2

MmID = "@VBS0035"
oRec.IntegerData(1) = 1909
oRec.StringData(2) = "Could not create Shortcut [2]. Verify that the destination folder exists and that you can access it. This can also happen if the ""Target"" of a shortcut doesn't exist (or not fully qualified) in the MSI."
ValidateFIELD(1)
RowUpdate()



'######################################################################
MmLL = "COMPANY.MMH(277)"
MmLT = "<$/Table>"
'######################################################################


MmID = "@VBS0036"
TableNow ""



'######################################################################
MmLL = "COMPANY.MMH(314)"
MmLT = "<$Table ""Billboard"">"
'######################################################################


MmID = "@VBS0037"
TableNowMk "Billboard"



'######################################################################
MmLL = "COMPANY.MMH(315)"
MmLT = "<$TableDelete>"
'######################################################################


MmID = "@VBS0038"
TableDelete("")



'######################################################################
MmLL = "COMPANY.MMH(316)"
MmLT = "<$/Table>"
'######################################################################


MmID = "@VBS0039"
TableNow ""



'######################################################################
MmLL = "COMPANY.MMH(321)"
MmLT = "<$Table ""_Validation"">"
'######################################################################


MmID = "@VBS0040"
TableNowMk "_Validation"



'######################################################################
MmLL = "COMPANY.MMH(328)"
MmLT = "<$Row @Where=""`Table` = 'ListView' AND `Column` = 'Value'"" @OK='=1' Category=""Formatted"" >"
'######################################################################


MmID = "@VBS0041"
RowsPrepare "`Table` = 'ListView' AND `Column` = 'Value'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0042"
oRec.StringData(8) = "Formatted"
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "`Table` = 'ListView' AND `Column` = 'Value'")



'######################################################################
MmLL = "COMPANY.MMH(329)"
MmLT = "<$/Table>"
'######################################################################


MmID = "@VBS0043"
TableNow ""



'######################################################################
MmLL = "COMPANY.MMH(335)"
MmLT = "<$TableCreate ""FeatureComponents"" DropExisting=""N""> ;;Windows Installer will PV in MSI.DLL (in UI sequence) if missing"
'######################################################################


MmID = "@VBS0044"

MmID = "@VBS0045"
TableNow "FeatureComponents"
TableCreate()

MmID = "@VBS0046"
TableNow ""



'######################################################################
MmLL = "COMPANY.MMH(336)"
MmLT = "<$TableCreate ""File"" DropExisting=""N""> ;;Windows Installer needs table (even if empty)"
'######################################################################


MmID = "@VBS0047"

MmID = "@VBS0048"
TableNow "File"
TableCreate()

MmID = "@VBS0049"
TableNow ""



'######################################################################
MmLL = "COMPANY.MMH(337)"
MmLT = "<$TableCreate ""Media"" DropExisting=""N""> ;;Windows Installer needs table (even if empty)"
'######################################################################


MmID = "@VBS0050"

MmID = "@VBS0051"
TableNow "Media"
TableCreate()

MmID = "@VBS0052"
TableNow ""



'######################################################################
MmLL = "COMPANY.MMH(342)"
MmLT = "<$TableCreate ""<$MAKEMSI_TABLENAME_FILESOURCE>"">"
'######################################################################


MmID = "@VBS0053"

MmID = "@VBS0054"
TableNow "_MAKEMSI_FileSource"

MmID = "@VBS0055"
TableDelete("")
TableCreate()

MmID = "@VBS0056"
TableNow ""



'######################################################################
MmLL = "COMPANY.MMH(388)"
MmLT = "<$TableCreate ""MsiFileHash"">"
'######################################################################


MmID = "@VBS0057"

MmID = "@VBS0058"
TableNow "MsiFileHash"

MmID = "@VBS0059"
TableDelete("")
TableCreate()

MmID = "@VBS0060"
TableNow ""



'######################################################################
MmLL = "COMPANY.MMH(389)"
MmLT = "<$Table ""_Validation"">"
'######################################################################


MmID = "@VBS0061"
TableNowMk "_Validation"



'######################################################################
MmLL = "COMPANY.MMH(400)"
MmLT = "<$Row Table=""MsiFileHash"" Column=""File_"" Nullable=""N"" KeyTable=""File"" KeyColumn=""1"" Category=""Identifier"" Description=""Foreign key into the File table."" >"
'######################################################################


MmID = "@VBS0062"
RowPrepare 10

MmID = "@VBS0063"
oRec.StringData(1) = "MsiFileHash"
oRec.StringData(2) = "File_"
oRec.StringData(3) = "N"
oRec.StringData(6) = "File"
oRec.IntegerData(7) = 1
oRec.StringData(8) = "Identifier"
oRec.StringData(10) = "Foreign key into the File table."
ValidateFIELD(1)
RowUpdate()



'######################################################################
MmLL = "COMPANY.MMH(411)"
MmLT = "<$Row Table=""MsiFileHash"" Column=""Options"" Nullable=""N"" Category=""Integer"" MinValue=""0"" MaxValue=""0"" Description=""Reserved option (must be 0)."" >"
'######################################################################


MmID = "@VBS0064"
RowPrepare 10

MmID = "@VBS0065"
oRec.StringData(1) = "MsiFileHash"
oRec.StringData(2) = "Options"
oRec.StringData(3) = "N"
oRec.StringData(8) = "Integer"
oRec.IntegerData(4) = 0
oRec.IntegerData(5) = 0
oRec.StringData(10) = "Reserved option (must be 0)."
ValidateFIELD(1)
RowUpdate()



'######################################################################
MmLL = "COMPANY.MMH(422)"
MmLT = "<$HashRow ""1"">"
'######################################################################


MmID = "@VBS0066"
RowPrepare 10

MmID = "@VBS0067"
oRec.StringData(1) = "MsiFileHash"
oRec.StringData(2) = "HashPart1"
oRec.StringData(3) = "N"
oRec.StringData(8) = "DoubleInteger"
oRec.StringData(10) = "MD5 part 1/4."
ValidateFIELD(1)
RowUpdate()



'######################################################################
MmLL = "COMPANY.MMH(423)"
MmLT = "<$HashRow ""2"">"
'######################################################################


MmID = "@VBS0068"
RowPrepare 10

MmID = "@VBS0069"
oRec.StringData(1) = "MsiFileHash"
oRec.StringData(2) = "HashPart2"
oRec.StringData(3) = "N"
oRec.StringData(8) = "DoubleInteger"
oRec.StringData(10) = "MD5 part 2/4."
ValidateFIELD(1)
RowUpdate()



'######################################################################
MmLL = "COMPANY.MMH(424)"
MmLT = "<$HashRow ""3"">"
'######################################################################


MmID = "@VBS0070"
RowPrepare 10

MmID = "@VBS0071"
oRec.StringData(1) = "MsiFileHash"
oRec.StringData(2) = "HashPart3"
oRec.StringData(3) = "N"
oRec.StringData(8) = "DoubleInteger"
oRec.StringData(10) = "MD5 part 3/4."
ValidateFIELD(1)
RowUpdate()



'######################################################################
MmLL = "COMPANY.MMH(425)"
MmLT = "<$HashRow ""4"">"
'######################################################################


MmID = "@VBS0072"
RowPrepare 10

MmID = "@VBS0073"
oRec.StringData(1) = "MsiFileHash"
oRec.StringData(2) = "HashPart4"
oRec.StringData(3) = "N"
oRec.StringData(8) = "DoubleInteger"
oRec.StringData(10) = "MD5 part 4/4."
ValidateFIELD(1)
RowUpdate()



'######################################################################
MmLL = "COMPANY.MMH(426)"
MmLT = "<$/Table>"
'######################################################################


MmID = "@VBS0074"
TableNow ""



'######################################################################
MmLL = "COMPANY.MMH(476)"
MmLT = "<$Feature ""<$COMPANY_COMPLETE_FEATURE>"" Directory_=""<$COMPANY_COMPLETE_FEATURE_DIRECTORY>"" Title=""<$COMPANY_COMPLETE_FEATURE_TITLE>"" Description=""<$COMPANY_COMPLETE_FEATURE_DESCRIPTION>"" Attributes=""<$COMPANY_COMPLETE_FEATURE_ATTRIBUTES>"" Display=""<$COMPANY_COMPLETE_FEATURE_DISPLAY>"" >"
'######################################################################


MmID = "@VBS0075"

MmID = "@VBS0076"
TableNowMk "Feature"

MmID = "@VBS0077"
RowPrepare 8

MmID = "@VBS0078"
oRec.StringData(1) = "ALL.1.0.0.UCS_AD_Connector"
oRec.StringData(2) = ""
oRec.StringData(3) = "Complete"
oRec.StringData(4) = "The Complete feature"
oRec.IntegerData(5) = 1
oRec.IntegerData(6) = 3
oRec.StringData(7) = ""
oRec.IntegerData(8) = msidbFeatureAttributesUIDisallowAbsent
ValidateFIELD(1)
RowUpdate()

MmID = "@VBS0079"
TableNow ""


dim UpgradeCode



'######################################################################
MmLL = "COMPANY.MMH(583)"
MmLT = "<$COMPANY_SET_PROPERTY_UPGRADECODE> ;;User can override above macros to change behaviour..."
'######################################################################


MmID = "@VBS0080"
UpgradeCode = "{6EFB7F3C-98B6-4147-878F-21D5EED29EAF}"
VbsReturnGuid "UpgradeCode", UpgradeCode

MmID = "@VBS0081"
cb_PropValue = UpgradeCode

MmID = "@VBS0082"
TableNowMk "Property"
   if cb_PropValue = "" then

MmID = "@VBS0083"
DeleteTableRows("`Property` = 'UpgradeCode'")
   else

MmID = "@VBS0084"
RowPrepare 2

MmID = "@VBS0085"
oRec.StringData(1) = "UpgradeCode"
oRec.StringData(2) = cb_PropValue
ValidateFIELD(1)
RowUpdate()
   end if

MmID = "@VBS0086"
TableNow ""




'######################################################################
MmLL = "COMPANY.MMH(584)"
MmLT = "<$COMPANY_SET_PROPERTY_PRODUCTCODE>"
'######################################################################


MmID = "@VBS0087"
cb_PropValue = GuidMake("ProductCode")

MmID = "@VBS0088"
TableNowMk "Property"
   if cb_PropValue = "" then

MmID = "@VBS0089"
DeleteTableRows("`Property` = 'ProductCode'")
   else

MmID = "@VBS0090"
RowPrepare 2

MmID = "@VBS0091"
oRec.StringData(1) = "ProductCode"
oRec.StringData(2) = cb_PropValue
ValidateFIELD(1)
RowUpdate()
   end if

MmID = "@VBS0092"
TableNow ""



'######################################################################
MmLL = "COMPANY.MMH(585)"
MmLT = "<$COMPANY_SET_PROPERTY_PACKAGECODE>"
'######################################################################


MmID = "@VBS0093"
SummaryItem PID_PackageCode, GuidMake("PackageCode")



'######################################################################
MmLL = "COMPANY.MMH(595)"
MmLT = "<$Property ""ALLUSERS"" Value=""<$COMPANY_ALLUSERS_PROPERTY>"">"
'######################################################################


MmID = "@VBS0094"
cb_PropValue = "1"

MmID = "@VBS0095"
TableNowMk "Property"
   if cb_PropValue = "" then

MmID = "@VBS0096"
DeleteTableRows("`Property` = 'ALLUSERS'")
   else

MmID = "@VBS0097"
RowPrepare 2

MmID = "@VBS0098"
oRec.StringData(1) = "ALLUSERS"
oRec.StringData(2) = cb_PropValue
ValidateFIELD(1)
RowUpdate()
   end if

MmID = "@VBS0099"
TableNow ""



'######################################################################
MmLL = "COMPANY.MMH(607)"
MmLT = "<$Property ""REINSTALLMODE"" Value=^<$COMPANY_REINSTALLMODE>^>"
'######################################################################


MmID = "@VBS0100"
cb_PropValue = "amus"

MmID = "@VBS0101"
TableNowMk "Property"
   if cb_PropValue = "" then

MmID = "@VBS0102"
DeleteTableRows("`Property` = 'REINSTALLMODE'")
   else

MmID = "@VBS0103"
RowPrepare 2

MmID = "@VBS0104"
oRec.StringData(1) = "REINSTALLMODE"
oRec.StringData(2) = cb_PropValue
ValidateFIELD(1)
RowUpdate()
   end if

MmID = "@VBS0105"
TableNow ""



'######################################################################
MmLL = "COMPANY.MMH(619)"
MmLT = "<$Property ""ProductName"" Value=""<$COMPANY_PROPERTY_PRODUCTNAME>"">"
'######################################################################


MmID = "@VBS0106"
cb_PropValue = "UCS AD Connector"

MmID = "@VBS0107"
TableNowMk "Property"
   if cb_PropValue = "" then

MmID = "@VBS0108"
DeleteTableRows("`Property` = 'ProductName'")
   else

MmID = "@VBS0109"
RowPrepare 2

MmID = "@VBS0110"
oRec.StringData(1) = "ProductName"
oRec.StringData(2) = cb_PropValue
ValidateFIELD(1)
RowUpdate()
   end if

MmID = "@VBS0111"
TableNow ""



'######################################################################
MmLL = "COMPANY.MMH(637)"
MmLT = "<$Summary ""TEMPLATE"" Value=""<$COMPANY_SUMMARY_TEMPLATE>"">"
'######################################################################


MmID = "@VBS0112"
SummaryItem PID_TEMPLATE, "Intel;1033"



'######################################################################
MmLL = "COMPANY.MMH(641)"
MmLT = "<$Summary ""MsiSchema"" Value=""<$COMPANY_SUMMARY_SCHEMA>"">"
'######################################################################


MmID = "@VBS0113"
SummaryItem PID_MsiSchema, 110



'######################################################################
MmLL = "COMPANY.MMH(643)"
MmLT = "<$Summary ""TITLE"" VALUE=""<$COMPANY_SUMMARY_TITLE>"">"
'######################################################################


MmID = "@VBS0114"
SummaryItem PID_TITLE, "UCS AD Connector"



'######################################################################
MmLL = "COMPANY.MMH(644)"
MmLT = "<$Summary ""Subject"" VALUE=""<$COMPANY_SUMMARY_SUBJECT>"">"
'######################################################################


MmID = "@VBS0115"
SummaryItem PID_Subject, "1.0.0 (created Tue Sep 28 2010 at 2:57:01pm)"



'######################################################################
MmLL = "COMPANY.MMH(645)"
MmLT = "<$Summary ""SourceType"" Value=""<$COMPANY_SUMMARY_SourceType>"">"
'######################################################################


MmID = "@VBS0116"
SummaryItem PID_SourceType, msidbSumInfoSourceTypeCompressed



'######################################################################
MmLL = "COMPANY.MMH(646)"
MmLT = "<$Summary ""CREATE_DTM"" VALUE=""now()"">"
'######################################################################


MmID = "@VBS0117"
SummaryItem PID_CREATE_DTM, now()



'######################################################################
MmLL = "COMPANY.MMH(647)"
MmLT = "<$Summary ""EDITTIME"" VALUE=""now()"">"
'######################################################################


MmID = "@VBS0118"
SummaryItem PID_EDITTIME, now()



'######################################################################
MmLL = "COMPANY.MMH(648)"
MmLT = "<$Summary ""LASTSAVE_DTM"" *VALUE=""Empty""> ;;Don't want"
'######################################################################


MmID = "@VBS0119"
SummaryItem PID_LASTSAVE_DTM, Empty



'######################################################################
MmLL = "COMPANY.MMH(649)"
MmLT = "<$Summary ""LASTPRINTED"" *VALUE=^Empty^> ;;Don't want"
'######################################################################


MmID = "@VBS0120"
SummaryItem PID_LASTPRINTED, Empty



'######################################################################
MmLL = "COMPANY.MMH(653)"
MmLT = "<$Html2Text VBVAR=""VB_COMMENTS"" HTML=^<$COMPANY_SUMMARY_COMMENTS>^>"
'######################################################################


MmID = "@VBS0121"
on error resume next



dim VB_COMMENTS : VB_COMMENTS = Html2Text("Testinstall")
err.clear()         'Ignore any error in called routine...



MmID = "@VBS0122"
VbsCheck "/VBS Command detected failure!" & vbCRLF & vbCRLF & "VBS command: COMPANY.MMH(653) - HTML TO TEXT Conversion"
on error goto 0

MmID = "@VBS0123"




'######################################################################
MmLL = "COMPANY.MMH(654)"
MmLT = "<$Summary ""COMMENTS"" *VALUE=""VB_COMMENTS"">"
'######################################################################


MmID = "@VBS0124"
SummaryItem PID_COMMENTS, VB_COMMENTS



'######################################################################
MmLL = "COMPANY.MMH(665)"
MmLT = "<$Property ""Manufacturer"" Value=""<$COMPANY_PROPERTY_MANUFACTURER>"">"
'######################################################################


MmID = "@VBS0125"
cb_PropValue = "My Name"

MmID = "@VBS0126"
TableNowMk "Property"
   if cb_PropValue = "" then

MmID = "@VBS0127"
DeleteTableRows("`Property` = 'Manufacturer'")
   else

MmID = "@VBS0128"
RowPrepare 2

MmID = "@VBS0129"
oRec.StringData(1) = "Manufacturer"
oRec.StringData(2) = cb_PropValue
ValidateFIELD(1)
RowUpdate()
   end if

MmID = "@VBS0130"
TableNow ""



'######################################################################
MmLL = "COMPANY.MMH(666)"
MmLT = "<$Summary ""AUTHOR"" VALUE=""<$COMPANY_SUMMARY_AUTHOR>"">"
'######################################################################


MmID = "@VBS0131"
SummaryItem PID_AUTHOR, "My Name - using MAKEMSI"



'######################################################################
MmLL = "COMPANY.MMH(667)"
MmLT = "<$Summary ""LastAuthor"" VALUE=""<$COMPANY_SUMMARY_LASTAUTHOR>"">"
'######################################################################


MmID = "@VBS0132"
SummaryItem PID_LastAuthor, "My Name"



'######################################################################
MmLL = "COMPANY.MMH(676)"
MmLT = "<$Property ""ARPCONTACT"" VALUE=^<$COMPANY_CONTACT_NAME>^>"
'######################################################################


MmID = "@VBS0133"
cb_PropValue = "My Name"

MmID = "@VBS0134"
TableNowMk "Property"
   if cb_PropValue = "" then

MmID = "@VBS0135"
DeleteTableRows("`Property` = 'ARPCONTACT'")
   else

MmID = "@VBS0136"
RowPrepare 2

MmID = "@VBS0137"
oRec.StringData(1) = "ARPCONTACT"
oRec.StringData(2) = cb_PropValue
ValidateFIELD(1)
RowUpdate()
   end if

MmID = "@VBS0138"
TableNow ""



'######################################################################
MmLL = "COMPANY.MMH(691)"
MmLT = "<$Property ""ARPURLINFOABOUT"" Value=""<$COMPANY_ARP_URL_PUBLISHER>"">"
'######################################################################


MmID = "@VBS0139"
cb_PropValue = "http://www.MyUrl.com/See/ME.MMH/"

MmID = "@VBS0140"
TableNowMk "Property"
   if cb_PropValue = "" then

MmID = "@VBS0141"
DeleteTableRows("`Property` = 'ARPURLINFOABOUT'")
   else

MmID = "@VBS0142"
RowPrepare 2

MmID = "@VBS0143"
oRec.StringData(1) = "ARPURLINFOABOUT"
oRec.StringData(2) = cb_PropValue
ValidateFIELD(1)
RowUpdate()
   end if

MmID = "@VBS0144"
TableNow ""



'######################################################################
MmLL = "COMPANY.MMH(695)"
MmLT = "<$Property ""ARPHELPLINK"" Value=""<$COMPANY_ARP_URL_TECHNICAL_SUPPORT>"">"
'######################################################################


MmID = "@VBS0145"
cb_PropValue = "http://www.MyUrl.com/See/ME.MMH/Support"

MmID = "@VBS0146"
TableNowMk "Property"
   if cb_PropValue = "" then

MmID = "@VBS0147"
DeleteTableRows("`Property` = 'ARPHELPLINK'")
   else

MmID = "@VBS0148"
RowPrepare 2

MmID = "@VBS0149"
oRec.StringData(1) = "ARPHELPLINK"
oRec.StringData(2) = cb_PropValue
ValidateFIELD(1)
RowUpdate()
   end if

MmID = "@VBS0150"
TableNow ""



'######################################################################
MmLL = "COMPANY.MMH(707)"
MmLT = "<$Property ""ProductVersion"" Value=""<$ProductVersion>"">"
'######################################################################


MmID = "@VBS0151"
cb_PropValue = "1.0.0"

MmID = "@VBS0152"
TableNowMk "Property"
   if cb_PropValue = "" then

MmID = "@VBS0153"
DeleteTableRows("`Property` = 'ProductVersion'")
   else

MmID = "@VBS0154"
RowPrepare 2

MmID = "@VBS0155"
oRec.StringData(1) = "ProductVersion"
oRec.StringData(2) = cb_PropValue
ValidateFIELD(1)
RowUpdate()
   end if

MmID = "@VBS0156"
TableNow ""



'######################################################################
MmLL = "COMPANY.MMH(711)"
MmLT = "<$Html2Text VBVAR=""VB_ARPCOMMENTS"" HTML=^<$COMPANY_PROPERTY_ARPCOMMENTS>^>"
'######################################################################


MmID = "@VBS0157"
on error resume next



dim VB_ARPCOMMENTS : VB_ARPCOMMENTS = Html2Text("UCS AD Connector (1.0.0)" & vbCRLF & "was created Tue Sep 28 2010 at 2:57:01pm." & vbCRLF & "" & vbCRLF & "Testinstall" & vbCRLF & "Packaged by My Name (My Address (see ""ME.MMH""))." & vbCRLF & "" & vbCRLF & "SUPPORTED on On any Windows Computer.")
err.clear()         'Ignore any error in called routine...



MmID = "@VBS0158"
VbsCheck "/VBS Command detected failure!" & vbCRLF & vbCRLF & "VBS command: COMPANY.MMH(711) - HTML TO TEXT Conversion"
on error goto 0

MmID = "@VBS0159"

VB_ARPCOMMENTS = replace(VB_ARPCOMMENTS, ". ",                      "."   & vbCRLF)
VB_ARPCOMMENTS = replace(VB_ARPCOMMENTS, vbCRLF & vbCRLF & vbCRLF, vbCRLF & vbCRLF)



'######################################################################
MmLL = "COMPANY.MMH(722)"
MmLT = "<$Property ""ARPCOMMENTS"" *VALUE=""VB_ARPCOMMENTS"">"
'######################################################################


MmID = "@VBS0160"
cb_PropValue = VB_ARPCOMMENTS

MmID = "@VBS0161"
TableNowMk "Property"
   if cb_PropValue = "" then

MmID = "@VBS0162"
DeleteTableRows("`Property` = 'ARPCOMMENTS'")
   else

MmID = "@VBS0163"
RowPrepare 2

MmID = "@VBS0164"
oRec.StringData(1) = "ARPCOMMENTS"
oRec.StringData(2) = cb_PropValue
ValidateFIELD(1)
RowUpdate()
   end if

MmID = "@VBS0165"
TableNow ""



'######################################################################
MmLL = "COMPANY.MMH(735)"
MmLT = "<$UpgradeTable ""=UpgradeCode""> ;;Use value in VB variable"
'######################################################################


MmID = "@VBS0166"
TableNowMk "Upgrade"

MmID = "@VBS0167"
RowPrepare 7

MmID = "@VBS0168"
oRec.StringData(1) = UpgradeCode
oRec.IntegerData(5) = (msidbUpgradeAttributesVersionMinInclusive or msidbUpgradeAttributesVersionMaxInclusive or msidbUpgradeAttributesLanguagesExclusive)
oRec.StringData(6) = "ALL"
oRec.StringData(7) = "UNINSTALLTHIS"
oRec.StringData(2) = ""
oRec.StringData(3) = ""
oRec.StringData(4) = ""
ValidateNEW(1)
RowUpdate()

MmID = "@VBS0169"
TableNow ""

MmID = "@VBS0170"
TableNowMk "Property"

cb_PlCntr = 0

MmID = "@VBS0171"
RowsPrepare "`Property` = 'SecureCustomProperties'"
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO

'--- START of USER Code ---

MmID = "@VBS0172"
on error resume next



cb_PlCntr = cb_PlCntr + 1

MmID = "@VBS0173"



MmID = "@VBS0174"
VbsCheck "/VBS Command detected failure!" & vbCRLF & vbCRLF & "VBS command: COMPANY.MMH(735) - Processing ROW command's query results"
on error goto 0

MmID = "@VBS0175"

oRec.StringData(2) = oRec.StringData(2) & ";UNINSTALLTHIS"
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()

if   cb_PlCntr = 0 then

MmID = "@VBS0176"
cb_PropValue = "UNINSTALLTHIS"

MmID = "@VBS0177"
TableNowMk "Property"
   if cb_PropValue = "" then

MmID = "@VBS0178"
DeleteTableRows("`Property` = 'SecureCustomProperties'")
   else

MmID = "@VBS0179"
RowPrepare 2

MmID = "@VBS0180"
oRec.StringData(1) = "SecureCustomProperties"
oRec.StringData(2) = cb_PropValue
ValidateFIELD(1)
RowUpdate()
   end if

MmID = "@VBS0181"
TableNow "Property"

end if

MmID = "@VBS0182"
TableNow ""





'######################################################################
MmLL = "COMPANY.MMH(756)"
MmLT = "<$COMPANY_MOVE_RemoveExistingProducts>"
'######################################################################


MmID = "@VBS0183"
TableNowMk "InstallExecuteSequence"
 dim RepSeq : RepSeq = GetSeqNumber("InstallExecuteSequence", "InstallValidate-InstallInitialize", 1) 

MmID = "@VBS0184"
RowPrepare 3

MmID = "@VBS0185"
oRec.StringData(1) = "RemoveExistingProducts"
oRec.IntegerData(3) = RepSeq
ValidateFIELD(1)
RowUpdate()
 

MmID = "@VBS0186"
TableNow ""




'######################################################################
MmLL = "COMPANY.MMH(911)"
MmLT = "<$Icon '<$COMPANY_PRODUCT_ICON>' Product=""Y"">"
'######################################################################


MmID = "@VBS0187"

MmID = "@VBS0188"
TableNowMk "Icon"

MmID = "@VBS0189"
RowPrepare 2

MmID = "@VBS0190"
oRec.SetStream 2, "C:\Programme\MakeMsi\MmDefaultProductIcon.ico"
oRec.StringData(1) = "MmDefaultProductIcon.1.0.0.ico.exe"

ValidateStreamKeyLength array(1)
ValidateFIELD(1)
RowUpdate()

MmID = "@VBS0191"
TableNow ""

MmID = "@VBS0192"
cb_PropValue = "MmDefaultProductIcon.1.0.0.ico.exe"

MmID = "@VBS0193"
TableNowMk "Property"
   if cb_PropValue = "" then

MmID = "@VBS0194"
DeleteTableRows("`Property` = 'ARPPRODUCTICON'")
   else

MmID = "@VBS0195"
RowPrepare 2

MmID = "@VBS0196"
oRec.StringData(1) = "ARPPRODUCTICON"
oRec.StringData(2) = cb_PropValue
ValidateFIELD(1)
RowUpdate()
   end if

MmID = "@VBS0197"
TableNow ""
BinaryMd5ForReport "0", "C:\Programme\MakeMsi\MmDefaultProductIcon.ico"
  



'######################################################################
MmLL = "COMPANY.MMH(939)"
MmLT = "<$CompanyAddStampWithProperty ""MakemsiVersion"" VALUE=^<$MAKEMSI_VERSION>^>"
'######################################################################


MmID = "@VBS0198"
cb_PropValue = "10.169"

MmID = "@VBS0199"
TableNowMk "Property"
   if cb_PropValue = "" then

MmID = "@VBS0200"
DeleteTableRows("`Property` = '_MAKEMSI_MakemsiVersion'")
   else

MmID = "@VBS0201"
RowPrepare 2

MmID = "@VBS0202"
oRec.StringData(1) = "_MAKEMSI_MakemsiVersion"
oRec.StringData(2) = cb_PropValue
ValidateFIELD(1)
RowUpdate()
   end if

MmID = "@VBS0203"
TableNow ""



'######################################################################
MmLL = "COMPANY.MMH(940)"
MmLT = "<$CompanyAddStampWithProperty ""BuildComputer"" VALUE=^<$MAKEMSI_COMPUTERNAME>^>"
'######################################################################


MmID = "@VBS0204"
cb_PropValue = "DIANE"

MmID = "@VBS0205"
TableNowMk "Property"
   if cb_PropValue = "" then

MmID = "@VBS0206"
DeleteTableRows("`Property` = '_MAKEMSI_BuildComputer'")
   else

MmID = "@VBS0207"
RowPrepare 2

MmID = "@VBS0208"
oRec.StringData(1) = "_MAKEMSI_BuildComputer"
oRec.StringData(2) = cb_PropValue
ValidateFIELD(1)
RowUpdate()
   end if

MmID = "@VBS0209"
TableNow ""



'######################################################################
MmLL = "COMPANY.MMH(941)"
MmLT = "<$CompanyAddStampWithProperty ""BuildUser"" VALUE=^<$MAKEMSI_USERNAME> in <$MAKEMSI_USERDOMAIN>^>"
'######################################################################


MmID = "@VBS0210"
cb_PropValue = "stegoh in DIANE"

MmID = "@VBS0211"
TableNowMk "Property"
   if cb_PropValue = "" then

MmID = "@VBS0212"
DeleteTableRows("`Property` = '_MAKEMSI_BuildUser'")
   else

MmID = "@VBS0213"
RowPrepare 2

MmID = "@VBS0214"
oRec.StringData(1) = "_MAKEMSI_BuildUser"
oRec.StringData(2) = cb_PropValue
ValidateFIELD(1)
RowUpdate()
   end if

MmID = "@VBS0215"
TableNow ""



'######################################################################
MmLL = "COMPANY.MMH(942)"
MmLT = "<$CompanyAddStampWithProperty ""BuildTime"" VALUE=^<?CompileTime>^>"
'######################################################################


MmID = "@VBS0216"
cb_PropValue = "Tue Sep 28 2010 at 2:57:01pm"

MmID = "@VBS0217"
TableNowMk "Property"
   if cb_PropValue = "" then

MmID = "@VBS0218"
DeleteTableRows("`Property` = '_MAKEMSI_BuildTime'")
   else

MmID = "@VBS0219"
RowPrepare 2

MmID = "@VBS0220"
oRec.StringData(1) = "_MAKEMSI_BuildTime"
oRec.StringData(2) = cb_PropValue
ValidateFIELD(1)
RowUpdate()
   end if

MmID = "@VBS0221"
TableNow ""



'######################################################################
MmLL = "COMPANY.MMH(943)"
MmLT = "<$CompanyAddStampWithProperty ""ProcessingMode"" VALUE=^<$MMMODE_DESCRIPTION>^>"
'######################################################################


MmID = "@VBS0222"
cb_PropValue = "Production"

MmID = "@VBS0223"
TableNowMk "Property"
   if cb_PropValue = "" then

MmID = "@VBS0224"
DeleteTableRows("`Property` = '_MAKEMSI_ProcessingMode'")
   else

MmID = "@VBS0225"
RowPrepare 2

MmID = "@VBS0226"
oRec.StringData(1) = "_MAKEMSI_ProcessingMode"
oRec.StringData(2) = cb_PropValue
ValidateFIELD(1)
RowUpdate()
   end if

MmID = "@VBS0227"
TableNow ""



'######################################################################
MmLL = "COMPANY.MMH(944)"
MmLT = "<$CompanyAddStampWithProperty ""SupportedPlatforms"" VALUE=^<$PLATFORM_MsiSupportedWhere>^>"
'######################################################################


MmID = "@VBS0228"
cb_PropValue = "SUPPORTED on On any Windows Computer."

MmID = "@VBS0229"
TableNowMk "Property"
   if cb_PropValue = "" then

MmID = "@VBS0230"
DeleteTableRows("`Property` = '_MAKEMSI_SupportedPlatforms'")
   else

MmID = "@VBS0231"
RowPrepare 2

MmID = "@VBS0232"
oRec.StringData(1) = "_MAKEMSI_SupportedPlatforms"
oRec.StringData(2) = cb_PropValue
ValidateFIELD(1)
RowUpdate()
   end if

MmID = "@VBS0233"
TableNow ""



'######################################################################
MmLL = "COMPANY.MMH(951)"
MmLT = "<$Table ""Property"">"
'######################################################################


MmID = "@VBS0234"
TableNowMk "Property"



'######################################################################
MmLL = "COMPANY.MMH(952)"
MmLT = "<$RowsDelete WHERE=""Property = 'ShowUserRegistrationDlg'"">"
'######################################################################


MmID = "@VBS0235"
DeleteTableRows("Property = 'ShowUserRegistrationDlg'")



'######################################################################
MmLL = "COMPANY.MMH(953)"
MmLT = "<$/Table>"
'######################################################################


MmID = "@VBS0236"
TableNow ""



'######################################################################
MmLL = "COMPANY.MMH(954)"
MmLT = "<$Table ""ControlEvent"">"
'######################################################################


MmID = "@VBS0237"
TableNowMk "ControlEvent"



'######################################################################
MmLL = "COMPANY.MMH(955)"
MmLT = "<$RowsDelete WHERE=^Dialog_ = 'LicenseAgreementDlg' AND Control_ = 'Next' AND Event = 'NewDialog' AND Argument = 'SetupTypeDlg' AND Condition = 'IAgree = ""Yes"" AND ShowUserRegistrationDlg <> 1'^>"
'######################################################################


MmID = "@VBS0238"
DeleteTableRows("Dialog_ = 'LicenseAgreementDlg' AND Control_ = 'Next' AND Event = 'NewDialog' AND Argument = 'SetupTypeDlg' AND Condition = 'IAgree = ""Yes"" AND ShowUserRegistrationDlg <> 1'")



'######################################################################
MmLL = "COMPANY.MMH(956)"
MmLT = "<$RowsDelete WHERE=^Dialog_ = 'LicenseAgreementDlg' AND Control_ = 'Next' AND Event = 'NewDialog' AND Argument = 'UserRegistrationDlg' AND Condition = 'IAgree = ""Yes"" AND ShowUserRegistrationDlg = 1'^>"
'######################################################################


MmID = "@VBS0239"
DeleteTableRows("Dialog_ = 'LicenseAgreementDlg' AND Control_ = 'Next' AND Event = 'NewDialog' AND Argument = 'UserRegistrationDlg' AND Condition = 'IAgree = ""Yes"" AND ShowUserRegistrationDlg = 1'")



'######################################################################
MmLL = "COMPANY.MMH(957)"
MmLT = "<$RowsDelete WHERE=""Dialog_ = 'SetupTypeDlg' AND Control_ = 'Back' AND Event = 'NewDialog' AND Argument = 'LicenseAgreementDlg' AND Condition = 'ShowUserRegistrationDlg <> 1'"">"
'######################################################################


MmID = "@VBS0240"
DeleteTableRows("Dialog_ = 'SetupTypeDlg' AND Control_ = 'Back' AND Event = 'NewDialog' AND Argument = 'LicenseAgreementDlg' AND Condition = 'ShowUserRegistrationDlg <> 1'")



'######################################################################
MmLL = "COMPANY.MMH(958)"
MmLT = "<$RowsDelete WHERE=""Dialog_ = 'SetupTypeDlg' AND Control_ = 'Back' AND Event = 'NewDialog' AND Argument = 'UserRegistrationDlg' AND Condition = 'ShowUserRegistrationDlg = 1'"">"
'######################################################################


MmID = "@VBS0241"
DeleteTableRows("Dialog_ = 'SetupTypeDlg' AND Control_ = 'Back' AND Event = 'NewDialog' AND Argument = 'UserRegistrationDlg' AND Condition = 'ShowUserRegistrationDlg = 1'")



'######################################################################
MmLL = "COMPANY.MMH(968)"
MmLT = "<$Row Dialog_=""LicenseAgreementDlg"" Control_=""Next"" Event=""NewDialog"" Argument=""UserRegistrationDlg"" Condition='IAgree = ""Yes""' Ordering=""1"" >"
'######################################################################


MmID = "@VBS0242"
RowPrepare 6

MmID = "@VBS0243"
oRec.StringData(1) = "LicenseAgreementDlg"
oRec.StringData(2) = "Next"
oRec.StringData(3) = "NewDialog"
oRec.StringData(4) = "UserRegistrationDlg"
oRec.StringData(5) = "IAgree = ""Yes"""
oRec.IntegerData(6) = 1
ValidateFIELD(1)
RowUpdate()



'######################################################################
MmLL = "COMPANY.MMH(979)"
MmLT = "<$Row Dialog_=""SetupTypeDlg"" Control_=""Back"" Event=""NewDialog"" Argument=""UserRegistrationDlg"" Condition=""1"" Ordering="""" >"
'######################################################################


MmID = "@VBS0244"
RowPrepare 6

MmID = "@VBS0245"
oRec.StringData(1) = "SetupTypeDlg"
oRec.StringData(2) = "Back"
oRec.StringData(3) = "NewDialog"
oRec.StringData(4) = "UserRegistrationDlg"
oRec.StringData(5) = "1"
oRec.IntegerData(6) = msiDatabaseNullInteger
ValidateFIELD(1)
RowUpdate()



'######################################################################
MmLL = "COMPANY.MMH(980)"
MmLT = "<$/Table>"
'######################################################################


MmID = "@VBS0246"
TableNow ""



'######################################################################
MmLL = "COMPANY.MMH(1050)"
MmLT = "<$Table ""Control"">"
'######################################################################


MmID = "@VBS0247"
TableNowMk "Control"



'######################################################################
MmLL = "COMPANY.MMH(1055)"
MmLT = "<$Row @Where=""Dialog_='LicenseAgreementDlg' and Control='AgreementText'"" @OK=""? = 1"" *Text=~""<??b_Text>""~ >"
'######################################################################


MmID = "@VBS0248"
RowsPrepare "Dialog_='LicenseAgreementDlg' and Control='AgreementText'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0249"
oRec.StringData(10) = "{\rtf1\ansi\deff1\adeflang1025" & vbCR & "" & vbLF & "{\fonttbl{\f0\froman\fprq2\fcharset128 Liberation Serif{\*\falt Times New Roman};}{\f1\froman\fprq2\fcharset0 Times New Roman;}{\f2\fswiss\fprq2\fcharset128 Liberation Sans{\*\falt Arial};}{\f3\fswiss\fprq2\fcharset0 Calibri;}{\f4\froman\fprq2\fcharset0 Cambria;}{\f5\froman\fprq2\fcharset0 Times New Roman;}{\f6\fnil\fprq2\fcharset128 DejaVu Sans;}}" & vbCR & "" & vbLF & "{\colortbl;\red0\green0\blue0;\red79\green129\blue189;\red128\green128\blue128;}" & vbCR & "" & vbLF & "{\stylesheet{\s1\sa200\cf0\sl276\slmult1{\*\hyphen2\hyphlead2\hyphtrail2\hyphmax0}\aspalpha\rtlch\af3\afs22\lang1025\ltrch\dbch\langfe3079\hich\f3\fs22\lang3079\loch\f3\fs22\lang3079\snext1 Normal;}" & vbCR & "" & vbLF & "{\s2\sb240\sa120\keepn\cf0\sl276\slmult1{\*\hyphen2\hyphlead2\hyphtrail2\hyphmax0}\aspalpha\rtlch\af6\afs28\lang1025\ltrch\dbch\af6\langfe3079\hich\f2\fs28\lang3079\loch\f2\fs28\lang3079\sbasedon1\snext3 Heading;}" & vbCR & "" & vbLF & "{\s3\sa120\cf0\sl276\slmult1{\*\hyphen2\hyphlead2\hyphtrail2\hyphmax0}\aspalpha\rtlch\af3\afs22\lang1025\ltrch\dbch\langfe3079\hich\f3\fs22\lang3079\loch\f3\fs22\lang3079\sbasedon1\snext3 Body Text;}" & vbCR & "" & vbLF & "{\s4\sa120\cf0\sl276\slmult1{\*\hyphen2\hyphlead2\hyphtrail2\hyphmax0}\aspalpha\rtlch\af3\afs22\lang1025\ltrch\dbch\langfe3079\hich\f3\fs22\lang3079\loch\f3\fs22\lang3079\sbasedon3\snext4 List;}" & vbCR & "" & vbLF & "{\s5\sb120\sa120\cf0\sl276\slmult1{\*\hyphen2\hyphlead2\hyphtrail2\hyphmax0}\aspalpha\rtlch\af3\afs24\lang1025\ai\ltrch\dbch\langfe3079\hich\f3\fs24\lang3079\i\loch\f3\fs24\lang3079\i\sbasedon1\snext5 caption;}" & vbCR & "" & vbLF & "{\s6\sa200\cf0\sl276\slmult1{\*\hyphen2\hyphlead2\hyphtrail2\hyphmax0}\aspalpha\rtlch\af3\afs22\lang1025\ltrch\dbch\langfe3079\hich\f3\fs22\lang3079\loch\f3\fs22\lang3079\sbasedon1\snext6 Index;}" & vbCR & "" & vbLF & "{\s7\sb200\keepn\cf2\sl276\slmult1\keep{\*\hyphen2\hyphlead2\hyphtrail2\hyphmax0}\aspalpha\rtlch\af4\afs26\lang1025\ab\ltrch\dbch\langfe3079\hich\f4\fs26\lang3079\b\loch\f4\fs26\lang3079\b\sbasedon1\snext1{\*\soutlvl1} heading 2;}" & vbCR & "" & vbLF & "{\*\cs9\cf0\rtlch\af1\afs24\lang3079\ltrch\dbch\af1\langfe3079\hich\f1\fs24\lang3079\loch\f1\fs24\lang3079 Default Paragraph Font;}" & vbCR & "" & vbLF & "{\*\cs10\cf2\rtlch\af4\afs26\lang3079\ab\ltrch\dbch\langfe3079\hich\f4\fs26\lang3079\b\loch\f4\fs26\lang3079\b\sbasedon9 \'dcberschrift 2 Zchn;}" & vbCR & "" & vbLF & "}" & vbCR & "" & vbLF & "{\info{\author x}{\creatim\yr2010\mo6\dy16\hr19\min59}{\author x}{\revtim\yr2010\mo6\dy17\hr14\min37}{\printim\yr0\mo0\dy0\hr0\min0}{\comment StarWriter}{\vern3200}}\deftab708" & vbCR & "" & vbLF & "{\*\pgdsctbl" & vbCR & "" & vbLF & "{\pgdsc0\pgdscuse195\pgwsxn11906\pghsxn16838\marglsxn1417\margrsxn1417\margtsxn1417\margbsxn1134\pgdscnxt0 Standard;}}" & vbCR & "" & vbLF & "{\*\pgdscno0}\paperh16838\paperw11906\margl1417\margr1417\margt1417\margb1134\sectd\sbknone\pgwsxn11906\pghsxn16838\marglsxn1417\margrsxn1417\margtsxn1417\margbsxn1134\ftnbj\ftnstart1\ftnrstcont\ftnnar\aenddoc\aftnrstcont\aftnstart1\aftnnrlc" & vbCR & "" & vbLF & "\pard\plain \ltrpar\s7\cf2\sl276\slmult1\keep{\*\hyphen2\hyphlead2\hyphtrail2\hyphmax0}\aspalpha\sb200\keepn\ql\rtlch\af4\afs26\lang1025\ab\ltrch\dbch\langfe3079\hich\f4\fs26\lang1031\b\loch\f4\fs26\lang1031\b{\rtlch \ltrch\loch\f4\fs26\lang1031\i0\b\rtlch UCS AD Connector}" & vbCR & "" & vbLF & "\par \pard\plain \ltrpar\s7\cf2\sl276\slmult1\keep{\*\hyphen2\hyphlead2\hyphtrail2\hyphmax0}\aspalpha\sb200\keepn\ql\rtlch\af4\afs26\lang1025\ab\ltrch\dbch\langfe3079\hich\f4\fs26\lang1031\b\loch\f4\fs26\lang1031\b {\rtlch \ltrch\loch\f4\fs26\lang1031\i0\b Password synchronisation between UCS and Active Directory}" & vbCR & "" & vbLF & "\par }" & vbCR & "" & vbLF & ""
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt = 1 then Error("Found " & RecCnt & " record(s), we expected ""? = 1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Dialog_='LicenseAgreementDlg' and Control='AgreementText'")



'######################################################################
MmLL = "COMPANY.MMH(1056)"
MmLT = "<$/Table>"
'######################################################################


MmID = "@VBS0250"
TableNow ""





'######################################################################
MmLL = "COMPANY.MMH(1066)"
MmLT = "<$DialogRemove ""UserRegistrationDlg"">"
'######################################################################


MmID = "@VBS0251"

DlgFind = "UserRegistrationDlg"
DlgPrev = ""
DlgNext = ""

MmID = "@VBS0252"
TableNowMk "ControlEvent"


MmID = "@VBS0253"
RowsPrepare ""
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

'--- START of USER Code ---

MmID = "@VBS0254"
on error resume next



if  oRec.StringData(3) = "NewDialog" then
if  oRec.StringData(4) = DlgFind then
if  oRec.StringData(2) = "Back" then
DlgNext = oRec.StringData(1)
else
DlgPrev = oRec.StringData(1)
end if
end if
end if

MmID = "@VBS0255"



MmID = "@VBS0256"
VbsCheck "/VBS Command detected failure!" & vbCRLF & vbCRLF & "VBS command: COMPANY.MMH(1066) - Processing ROW command's query results"
on error goto 0

MmID = "@VBS0257"

ValidateFETCH(1)
loop
SqlViewClose()
if not RecCnt > 0 then Error("Found " & RecCnt & " record(s), we expected ""? > 0"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "")


MmID = "@VBS0258"
TableNow ""

if   DlgPrev = "" and DlgNext = "" then
error "No references to the dialog """ & DlgFind & """ were found in the ""ControlEvent"" table (dialog name spelt wrong? Wrong case?)."
end if
if   DlgPrev = "" then
error "The dialog after """ & DlgFind & """ is """ & DlgNext & """ however the previous dialog was not mentioned in the ""ControlEvent"" table."
end if
if   DlgNext = "" then
error "The dialog before """ & DlgFind & """ is """ & DlgPrev & """ however the next dialog was not mentioned in the ""ControlEvent"" table."
end if

MmID = "@VBS0259"
TableNowMk "ControlEvent"


MmID = "@VBS0260"
RowsPrepare ""
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

'--- START of USER Code ---

MmID = "@VBS0261"
on error resume next



DlgArgument = oRec.StringData(4)
if  oRec.StringData(3) = "NewDialog" then
if  DlgArgument = DlgFind then
if  oRec.StringData(2) = "Back" then DlgArgument = DlgPrev
if  oRec.StringData(2) = "Next" then DlgArgument = DlgNext
end if
end if

MmID = "@VBS0262"



MmID = "@VBS0263"
VbsCheck "/VBS Command detected failure!" & vbCRLF & vbCRLF & "VBS command: COMPANY.MMH(1066) - Processing ROW command's query results"
on error goto 0

MmID = "@VBS0264"

oRec.StringData(4) = DlgArgument
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt > 0 then Error("Found " & RecCnt & " record(s), we expected ""? > 0"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "")


MmID = "@VBS0265"
TableNow ""


MmID = "@VBS0266"
TableNowMk "ControlEvent"


MmID = "@VBS0267"
DeleteTableRows("Dialog_ = 'UserRegistrationDlg'")


MmID = "@VBS0268"
TableNow ""


MmID = "@VBS0269"
TableNowMk "Dialog"


MmID = "@VBS0270"
DeleteTableRows("Dialog = 'UserRegistrationDlg'")


MmID = "@VBS0271"
TableNow ""


MmID = "@VBS0272"
TableNowMk "Control"


MmID = "@VBS0273"
DeleteTableRows("Dialog_ = 'UserRegistrationDlg'")


MmID = "@VBS0274"
TableNow ""


MmID = "@VBS0275"
TableNowMk "ControlCondition"


MmID = "@VBS0276"
DeleteTableRows("Dialog_ = 'UserRegistrationDlg'")


MmID = "@VBS0277"
TableNow ""
  





'######################################################################
MmLL = "installscript.mm(15)"
MmLT = "<$DialogRemove ""SetupTypeDlg""> ;; do not ask for Typical Custom complete"
'######################################################################


MmID = "@VBS0278"

DlgFind = "SetupTypeDlg"
DlgPrev = ""
DlgNext = ""

MmID = "@VBS0279"
TableNowMk "ControlEvent"


MmID = "@VBS0280"
RowsPrepare ""
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

'--- START of USER Code ---

MmID = "@VBS0281"
on error resume next



if  oRec.StringData(3) = "NewDialog" then
if  oRec.StringData(4) = DlgFind then
if  oRec.StringData(2) = "Back" then
DlgNext = oRec.StringData(1)
else
DlgPrev = oRec.StringData(1)
end if
end if
end if

MmID = "@VBS0282"



MmID = "@VBS0283"
VbsCheck "/VBS Command detected failure!" & vbCRLF & vbCRLF & "VBS command: installscript.mm(15) - Processing ROW command's query results"
on error goto 0

MmID = "@VBS0284"

ValidateFETCH(1)
loop
SqlViewClose()
if not RecCnt > 0 then Error("Found " & RecCnt & " record(s), we expected ""? > 0"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "")


MmID = "@VBS0285"
TableNow ""

if   DlgPrev = "" and DlgNext = "" then
error "No references to the dialog """ & DlgFind & """ were found in the ""ControlEvent"" table (dialog name spelt wrong? Wrong case?)."
end if
if   DlgPrev = "" then
error "The dialog after """ & DlgFind & """ is """ & DlgNext & """ however the previous dialog was not mentioned in the ""ControlEvent"" table."
end if
if   DlgNext = "" then
error "The dialog before """ & DlgFind & """ is """ & DlgPrev & """ however the next dialog was not mentioned in the ""ControlEvent"" table."
end if

MmID = "@VBS0286"
TableNowMk "ControlEvent"


MmID = "@VBS0287"
RowsPrepare ""
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

'--- START of USER Code ---

MmID = "@VBS0288"
on error resume next



DlgArgument = oRec.StringData(4)
if  oRec.StringData(3) = "NewDialog" then
if  DlgArgument = DlgFind then
if  oRec.StringData(2) = "Back" then DlgArgument = DlgPrev
if  oRec.StringData(2) = "Next" then DlgArgument = DlgNext
end if
end if

MmID = "@VBS0289"



MmID = "@VBS0290"
VbsCheck "/VBS Command detected failure!" & vbCRLF & vbCRLF & "VBS command: installscript.mm(15) - Processing ROW command's query results"
on error goto 0

MmID = "@VBS0291"

oRec.StringData(4) = DlgArgument
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt > 0 then Error("Found " & RecCnt & " record(s), we expected ""? > 0"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "")


MmID = "@VBS0292"
TableNow ""


MmID = "@VBS0293"
TableNowMk "ControlEvent"


MmID = "@VBS0294"
DeleteTableRows("Dialog_ = 'SetupTypeDlg'")


MmID = "@VBS0295"
TableNow ""


MmID = "@VBS0296"
TableNowMk "Dialog"


MmID = "@VBS0297"
DeleteTableRows("Dialog = 'SetupTypeDlg'")


MmID = "@VBS0298"
TableNow ""


MmID = "@VBS0299"
TableNowMk "Control"


MmID = "@VBS0300"
DeleteTableRows("Dialog_ = 'SetupTypeDlg'")


MmID = "@VBS0301"
TableNow ""


MmID = "@VBS0302"
TableNowMk "ControlCondition"


MmID = "@VBS0303"
DeleteTableRows("Dialog_ = 'SetupTypeDlg'")


MmID = "@VBS0304"
TableNow ""





'######################################################################
MmLL = "installscript.mm(16)"
MmLT = "<$DialogRemove ""LicenseAgreementDlg""> ;;ignore lizenz.rtf File"
'######################################################################


MmID = "@VBS0305"

DlgFind = "LicenseAgreementDlg"
DlgPrev = ""
DlgNext = ""

MmID = "@VBS0306"
TableNowMk "ControlEvent"


MmID = "@VBS0307"
RowsPrepare ""
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

'--- START of USER Code ---

MmID = "@VBS0308"
on error resume next



if  oRec.StringData(3) = "NewDialog" then
if  oRec.StringData(4) = DlgFind then
if  oRec.StringData(2) = "Back" then
DlgNext = oRec.StringData(1)
else
DlgPrev = oRec.StringData(1)
end if
end if
end if

MmID = "@VBS0309"



MmID = "@VBS0310"
VbsCheck "/VBS Command detected failure!" & vbCRLF & vbCRLF & "VBS command: installscript.mm(16) - Processing ROW command's query results"
on error goto 0

MmID = "@VBS0311"

ValidateFETCH(1)
loop
SqlViewClose()
if not RecCnt > 0 then Error("Found " & RecCnt & " record(s), we expected ""? > 0"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "")


MmID = "@VBS0312"
TableNow ""

if   DlgPrev = "" and DlgNext = "" then
error "No references to the dialog """ & DlgFind & """ were found in the ""ControlEvent"" table (dialog name spelt wrong? Wrong case?)."
end if
if   DlgPrev = "" then
error "The dialog after """ & DlgFind & """ is """ & DlgNext & """ however the previous dialog was not mentioned in the ""ControlEvent"" table."
end if
if   DlgNext = "" then
error "The dialog before """ & DlgFind & """ is """ & DlgPrev & """ however the next dialog was not mentioned in the ""ControlEvent"" table."
end if

MmID = "@VBS0313"
TableNowMk "ControlEvent"


MmID = "@VBS0314"
RowsPrepare ""
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

'--- START of USER Code ---

MmID = "@VBS0315"
on error resume next



DlgArgument = oRec.StringData(4)
if  oRec.StringData(3) = "NewDialog" then
if  DlgArgument = DlgFind then
if  oRec.StringData(2) = "Back" then DlgArgument = DlgPrev
if  oRec.StringData(2) = "Next" then DlgArgument = DlgNext
end if
end if

MmID = "@VBS0316"



MmID = "@VBS0317"
VbsCheck "/VBS Command detected failure!" & vbCRLF & vbCRLF & "VBS command: installscript.mm(16) - Processing ROW command's query results"
on error goto 0

MmID = "@VBS0318"

oRec.StringData(4) = DlgArgument
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt > 0 then Error("Found " & RecCnt & " record(s), we expected ""? > 0"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "")


MmID = "@VBS0319"
TableNow ""


MmID = "@VBS0320"
TableNowMk "ControlEvent"


MmID = "@VBS0321"
DeleteTableRows("Dialog_ = 'LicenseAgreementDlg'")


MmID = "@VBS0322"
TableNow ""


MmID = "@VBS0323"
TableNowMk "Dialog"


MmID = "@VBS0324"
DeleteTableRows("Dialog = 'LicenseAgreementDlg'")


MmID = "@VBS0325"
TableNow ""


MmID = "@VBS0326"
TableNowMk "Control"


MmID = "@VBS0327"
DeleteTableRows("Dialog_ = 'LicenseAgreementDlg'")


MmID = "@VBS0328"
TableNow ""


MmID = "@VBS0329"
TableNowMk "ControlCondition"


MmID = "@VBS0330"
DeleteTableRows("Dialog_ = 'LicenseAgreementDlg'")


MmID = "@VBS0331"
TableNow ""



'######################################################################
MmLL = "installscript.mm(25)"
MmLT = "<$DirectoryTree Key=""INSTALLDIR"" Dir=""c:\Windows\UCS-AD-Connector"" CHANGE=""\"" PrimaryFolder=""Y"">"
'######################################################################


MmID = "@VBS0332"

MmID = "@VBS0333"
 

MmID = "@VBS0334"
 

MmID = "@VBS0335"

MmID = "@VBS0336"
TableNowMk "Directory"

MmID = "@VBS0337"
RowPrepare 3

MmID = "@VBS0338"
oRec.StringData(1) = "TARGETDIR"
oRec.StringData(2) = ""
oRec.StringData(3) = "SourceDir"
ValidateFIELD(1)
RowUpdate()

MmID = "@VBS0339"
TableNow ""

MmID = "@VBS0340"
TableNowMk "Directory"

MmID = "@VBS0341"
RowPrepare 3

MmID = "@VBS0342"
oRec.StringData(1) = "WindowsFolder"
oRec.StringData(2) = "TARGETDIR"
oRec.StringData(3) = ".:Windows"
ValidateFIELD(1)
RowUpdate()

MmID = "@VBS0343"
TableNow ""

MmID = "@VBS0344"
TableNowMk "Directory"
 

MmID = "@VBS0345"
RowPrepare 3

MmID = "@VBS0346"
oRec.StringData(1) = "INSTALLDIR"
oRec.StringData(2) = "WindowsFolder"
oRec.StringData(3) = MakeSfnLfn("WindowsFolder", "UCS-AD-Connector")
ValidateFIELD(1)
RowUpdate()

MmID = "@VBS0347"
TableNow ""

MmID = "@VBS0348"
TableNowMk "Feature"

MmID = "@VBS0349"
RowsPrepare "`Feature` = 'ALL.1.0.0.UCS_AD_Connector'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0350"
oRec.StringData(7) = "INSTALLDIR"
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "`Feature` = 'ALL.1.0.0.UCS_AD_Connector'")

MmID = "@VBS0351"
TableNow ""

MmID = "@VBS0352"

MmID = "@VBS0353"
TableNowMk "CustomAction"
 

MmID = "@VBS0354"
RowPrepare 5

MmID = "@VBS0355"
oRec.StringData(4) = "[INSTALLDIR]"
oRec.IntegerData(2) = &H0033
oRec.StringData(1) = "PropertyCa01_ARPINSTALLLOCATION"
oRec.StringData(3) = "ARPINSTALLLOCATION"
ValidateFIELD(1)
RowUpdate()

MmID = "@VBS0356"
TableNow ""
SeqNo = GetSeqNumber("InstallExecuteSequence", "CostFinalize-", 1)

MmID = "@VBS0357"
TableNowMk "InstallExecuteSequence"

MmID = "@VBS0358"
RowPrepare 3

MmID = "@VBS0359"
oRec.StringData(1) = "PropertyCa01_ARPINSTALLLOCATION"
oRec.StringData(2) = ""
oRec.IntegerData(3) = SeqNo
ValidateFIELD(1)
RowUpdate()

MmID = "@VBS0360"
TableNow ""
 

MmID = "@VBS0361"

MmID = "@VBS0362"
TableNowMk "CustomAction"
 

MmID = "@VBS0363"
RowPrepare 5

MmID = "@VBS0364"
oRec.StringData(4) = "[INSTALLDIR]"
oRec.IntegerData(2) = &H0033
oRec.StringData(1) = "PropertyCa02_PRIMARYFOLDER"
oRec.StringData(3) = "PRIMARYFOLDER"
ValidateFIELD(1)
RowUpdate()

MmID = "@VBS0365"
TableNow ""
SeqNo = GetSeqNumber("InstallExecuteSequence", "CostFinalize-", 1)

MmID = "@VBS0366"
TableNowMk "InstallExecuteSequence"

MmID = "@VBS0367"
RowPrepare 3

MmID = "@VBS0368"
oRec.StringData(1) = "PropertyCa02_PRIMARYFOLDER"
oRec.StringData(2) = ""
oRec.IntegerData(3) = SeqNo
ValidateFIELD(1)
RowUpdate()

MmID = "@VBS0369"
TableNow ""



'######################################################################
MmLL = "installscript.mm(35)"
MmLT = "<$Files ""files\Programme\UCS-AD-Connector\*.*"" DestDir=""INSTALLDIR"">"
'######################################################################


MmID = "@VBS0370"

MmID = "@VBS0371"

MmID = "@VBS0372"

MmID = "@VBS0373"
TableNowMk "Component"

MmID = "@VBS0374"
RowPrepare 6

MmID = "@VBS0375"
oRec.StringData(1) = "c1.ALL.1.0.0.UCS_A.INSTALLDIR_1_copypwd.dll"
oRec.StringData(2) = GuidMake("")
oRec.StringData(3) = "INSTALLDIR"
oRec.IntegerData(4) = msidbComponentAttributesLocalOnly
oRec.StringData(5) = ""
oRec.StringData(6) = ""
ValidateFIELD(1)
RowUpdate()

MmID = "@VBS0376"


MmID = "@VBS0377"
TableNowMk "FeatureComponents"

MmID = "@VBS0378"
RowPrepare 2

MmID = "@VBS0379"
oRec.StringData(1) = "ALL.1.0.0.UCS_AD_Connector"
oRec.StringData(2) = "c1.ALL.1.0.0.UCS_A.INSTALLDIR_1_copypwd.dll"
ValidateNEW(0)
RowUpdate()

MmID = "@VBS0380"
TableNow ""

CurrentFile="Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector\files\Programme\UCS-AD-Connector\copypwd.dll"
CurrentFileKey="copypwd.dll"
CurrentFileNameSL=Get83PlusLongName("copypwd.dll")
ob_FileVersion("")

MmID = "@VBS0381"
TableNowMk "File"

MmID = "@VBS0382"
RowPrepare 8

MmID = "@VBS0383"
oRec.StringData(1) = CurrentFileKey
oRec.StringData(2) = "c1.ALL.1.0.0.UCS_A.INSTALLDIR_1_copypwd.dll"
oRec.StringData(3) = CurrentFileNameSL
oRec.IntegerData(4) = 49152
oRec.StringData(5) = CurrentFileVersion
oRec.IntegerData(7) = FileAttribs(msidbFileAttributesVital, 0)
oRec.StringData(6) = FileLanguage()
oRec.IntegerData(8) = 0
ValidateNEW(2)
RowUpdate()

MmID = "@VBS0384"
TableNow ""

MmID = "@VBS0385"
TableNowMk "_MAKEMSI_FileSource"

MmID = "@VBS0386"
RowPrepare 4

MmID = "@VBS0387"
oRec.StringData(1) = CurrentFileKey
oRec.StringData(2) = CurrentFile
oRec.StringData(3) = "2010-09-28"
oRec.StringData(4) = "13:54:38"
ValidateNEW(0)
RowUpdate()

MmID = "@VBS0388"
TableNow ""
ob_FileHash("Y")

MmID = "@VBS0389"
TableNowMk "Component"

MmID = "@VBS0390"
RowsPrepare "`Component` = 'c1.ALL.1.0.0.UCS_A.INSTALLDIR_1_copypwd.dll'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0391"
oRec.IntegerData(4) = (oRec.IntegerData(4) AND NOT msidbComponentAttributesRegistryKeyPath)
oRec.StringData(6) = "copypwd.dll"
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "`Component` = 'c1.ALL.1.0.0.UCS_A.INSTALLDIR_1_copypwd.dll'")

MmID = "@VBS0392"
TableNow ""


MmID = "@VBS0393"

MmID = "@VBS0394"

MmID = "@VBS0395"
TableNowMk "Component"

MmID = "@VBS0396"
RowPrepare 6

MmID = "@VBS0397"
oRec.StringData(1) = "c2.ALL.1.0.0.UCS_A.INSTALLDIR_1_copypwd.exe"
oRec.StringData(2) = GuidMake("")
oRec.StringData(3) = "INSTALLDIR"
oRec.IntegerData(4) = msidbComponentAttributesLocalOnly
oRec.StringData(5) = ""
oRec.StringData(6) = ""
ValidateFIELD(1)
RowUpdate()

MmID = "@VBS0398"


MmID = "@VBS0399"
TableNowMk "FeatureComponents"

MmID = "@VBS0400"
RowPrepare 2

MmID = "@VBS0401"
oRec.StringData(1) = "ALL.1.0.0.UCS_AD_Connector"
oRec.StringData(2) = "c2.ALL.1.0.0.UCS_A.INSTALLDIR_1_copypwd.exe"
ValidateNEW(0)
RowUpdate()

MmID = "@VBS0402"
TableNow ""

CurrentFile="Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector\files\Programme\UCS-AD-Connector\copypwd.exe"
CurrentFileKey="copypwd.exe"
CurrentFileNameSL=Get83PlusLongName("copypwd.exe")
ob_FileVersion("")

MmID = "@VBS0403"
TableNowMk "File"

MmID = "@VBS0404"
RowPrepare 8

MmID = "@VBS0405"
oRec.StringData(1) = CurrentFileKey
oRec.StringData(2) = "c2.ALL.1.0.0.UCS_A.INSTALLDIR_1_copypwd.exe"
oRec.StringData(3) = CurrentFileNameSL
oRec.IntegerData(4) = 32768
oRec.StringData(5) = CurrentFileVersion
oRec.IntegerData(7) = FileAttribs(msidbFileAttributesVital, 0)
oRec.StringData(6) = FileLanguage()
oRec.IntegerData(8) = 0
ValidateNEW(2)
RowUpdate()

MmID = "@VBS0406"
TableNow ""

MmID = "@VBS0407"
TableNowMk "_MAKEMSI_FileSource"

MmID = "@VBS0408"
RowPrepare 4

MmID = "@VBS0409"
oRec.StringData(1) = CurrentFileKey
oRec.StringData(2) = CurrentFile
oRec.StringData(3) = "2010-09-28"
oRec.StringData(4) = "13:54:38"
ValidateNEW(0)
RowUpdate()

MmID = "@VBS0410"
TableNow ""
ob_FileHash("Y")

MmID = "@VBS0411"
TableNowMk "Component"

MmID = "@VBS0412"
RowsPrepare "`Component` = 'c2.ALL.1.0.0.UCS_A.INSTALLDIR_1_copypwd.exe'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0413"
oRec.IntegerData(4) = (oRec.IntegerData(4) AND NOT msidbComponentAttributesRegistryKeyPath)
oRec.StringData(6) = "copypwd.exe"
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "`Component` = 'c2.ALL.1.0.0.UCS_A.INSTALLDIR_1_copypwd.exe'")

MmID = "@VBS0414"
TableNow ""


MmID = "@VBS0415"

MmID = "@VBS0416"

MmID = "@VBS0417"
TableNowMk "Component"

MmID = "@VBS0418"
RowPrepare 6

MmID = "@VBS0419"
oRec.StringData(1) = "c3.ALL.1.0.0.UCS_A.INSTALLDIR_1_libeay32.dll"
oRec.StringData(2) = GuidMake("")
oRec.StringData(3) = "INSTALLDIR"
oRec.IntegerData(4) = msidbComponentAttributesLocalOnly
oRec.StringData(5) = ""
oRec.StringData(6) = ""
ValidateFIELD(1)
RowUpdate()

MmID = "@VBS0420"


MmID = "@VBS0421"
TableNowMk "FeatureComponents"

MmID = "@VBS0422"
RowPrepare 2

MmID = "@VBS0423"
oRec.StringData(1) = "ALL.1.0.0.UCS_AD_Connector"
oRec.StringData(2) = "c3.ALL.1.0.0.UCS_A.INSTALLDIR_1_libeay32.dll"
ValidateNEW(0)
RowUpdate()

MmID = "@VBS0424"
TableNow ""

CurrentFile="Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector\files\Programme\UCS-AD-Connector\libeay32.dll"
CurrentFileKey="libeay32.dll"
CurrentFileNameSL=Get83PlusLongName("libeay32.dll")
ob_FileVersion("")

MmID = "@VBS0425"
TableNowMk "File"

MmID = "@VBS0426"
RowPrepare 8

MmID = "@VBS0427"
oRec.StringData(1) = CurrentFileKey
oRec.StringData(2) = "c3.ALL.1.0.0.UCS_A.INSTALLDIR_1_libeay32.dll"
oRec.StringData(3) = CurrentFileNameSL
oRec.IntegerData(4) = 843776
oRec.StringData(5) = CurrentFileVersion
oRec.IntegerData(7) = FileAttribs(msidbFileAttributesVital, 0)
oRec.StringData(6) = FileLanguage()
oRec.IntegerData(8) = 0
ValidateNEW(2)
RowUpdate()

MmID = "@VBS0428"
TableNow ""

MmID = "@VBS0429"
TableNowMk "_MAKEMSI_FileSource"

MmID = "@VBS0430"
RowPrepare 4

MmID = "@VBS0431"
oRec.StringData(1) = CurrentFileKey
oRec.StringData(2) = CurrentFile
oRec.StringData(3) = "2010-09-28"
oRec.StringData(4) = "13:54:38"
ValidateNEW(0)
RowUpdate()

MmID = "@VBS0432"
TableNow ""
ob_FileHash("Y")

MmID = "@VBS0433"
TableNowMk "Component"

MmID = "@VBS0434"
RowsPrepare "`Component` = 'c3.ALL.1.0.0.UCS_A.INSTALLDIR_1_libeay32.dll'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0435"
oRec.IntegerData(4) = (oRec.IntegerData(4) AND NOT msidbComponentAttributesRegistryKeyPath)
oRec.StringData(6) = "libeay32.dll"
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "`Component` = 'c3.ALL.1.0.0.UCS_A.INSTALLDIR_1_libeay32.dll'")

MmID = "@VBS0436"
TableNow ""


MmID = "@VBS0437"

MmID = "@VBS0438"

MmID = "@VBS0439"
TableNowMk "Component"

MmID = "@VBS0440"
RowPrepare 6

MmID = "@VBS0441"
oRec.StringData(1) = "c4.ALL.1.0.0.UCS_A.INSTALLDIR_1_libssl32.dll"
oRec.StringData(2) = GuidMake("")
oRec.StringData(3) = "INSTALLDIR"
oRec.IntegerData(4) = msidbComponentAttributesLocalOnly
oRec.StringData(5) = ""
oRec.StringData(6) = ""
ValidateFIELD(1)
RowUpdate()

MmID = "@VBS0442"


MmID = "@VBS0443"
TableNowMk "FeatureComponents"

MmID = "@VBS0444"
RowPrepare 2

MmID = "@VBS0445"
oRec.StringData(1) = "ALL.1.0.0.UCS_AD_Connector"
oRec.StringData(2) = "c4.ALL.1.0.0.UCS_A.INSTALLDIR_1_libssl32.dll"
ValidateNEW(0)
RowUpdate()

MmID = "@VBS0446"
TableNow ""

CurrentFile="Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector\files\Programme\UCS-AD-Connector\libssl32.dll"
CurrentFileKey="libssl32.dll"
CurrentFileNameSL=Get83PlusLongName("libssl32.dll")
ob_FileVersion("")

MmID = "@VBS0447"
TableNowMk "File"

MmID = "@VBS0448"
RowPrepare 8

MmID = "@VBS0449"
oRec.StringData(1) = CurrentFileKey
oRec.StringData(2) = "c4.ALL.1.0.0.UCS_A.INSTALLDIR_1_libssl32.dll"
oRec.StringData(3) = CurrentFileNameSL
oRec.IntegerData(4) = 159744
oRec.StringData(5) = CurrentFileVersion
oRec.IntegerData(7) = FileAttribs(msidbFileAttributesVital, 0)
oRec.StringData(6) = FileLanguage()
oRec.IntegerData(8) = 0
ValidateNEW(2)
RowUpdate()

MmID = "@VBS0450"
TableNow ""

MmID = "@VBS0451"
TableNowMk "_MAKEMSI_FileSource"

MmID = "@VBS0452"
RowPrepare 4

MmID = "@VBS0453"
oRec.StringData(1) = CurrentFileKey
oRec.StringData(2) = CurrentFile
oRec.StringData(3) = "2010-09-28"
oRec.StringData(4) = "13:54:38"
ValidateNEW(0)
RowUpdate()

MmID = "@VBS0454"
TableNow ""
ob_FileHash("Y")

MmID = "@VBS0455"
TableNowMk "Component"

MmID = "@VBS0456"
RowsPrepare "`Component` = 'c4.ALL.1.0.0.UCS_A.INSTALLDIR_1_libssl32.dll'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0457"
oRec.IntegerData(4) = (oRec.IntegerData(4) AND NOT msidbComponentAttributesRegistryKeyPath)
oRec.StringData(6) = "libssl32.dll"
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "`Component` = 'c4.ALL.1.0.0.UCS_A.INSTALLDIR_1_libssl32.dll'")

MmID = "@VBS0458"
TableNow ""


MmID = "@VBS0459"

MmID = "@VBS0460"

MmID = "@VBS0461"
TableNowMk "Component"

MmID = "@VBS0462"
RowPrepare 6

MmID = "@VBS0463"
oRec.StringData(1) = "c5.ALL.1.0.0.UCS_A.INSTALLDIR_1_ssleay32.dll"
oRec.StringData(2) = GuidMake("")
oRec.StringData(3) = "INSTALLDIR"
oRec.IntegerData(4) = msidbComponentAttributesLocalOnly
oRec.StringData(5) = ""
oRec.StringData(6) = ""
ValidateFIELD(1)
RowUpdate()

MmID = "@VBS0464"


MmID = "@VBS0465"
TableNowMk "FeatureComponents"

MmID = "@VBS0466"
RowPrepare 2

MmID = "@VBS0467"
oRec.StringData(1) = "ALL.1.0.0.UCS_AD_Connector"
oRec.StringData(2) = "c5.ALL.1.0.0.UCS_A.INSTALLDIR_1_ssleay32.dll"
ValidateNEW(0)
RowUpdate()

MmID = "@VBS0468"
TableNow ""

CurrentFile="Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector\files\Programme\UCS-AD-Connector\ssleay32.dll"
CurrentFileKey="ssleay32.dll"
CurrentFileNameSL=Get83PlusLongName("ssleay32.dll")
ob_FileVersion("")

MmID = "@VBS0469"
TableNowMk "File"

MmID = "@VBS0470"
RowPrepare 8

MmID = "@VBS0471"
oRec.StringData(1) = CurrentFileKey
oRec.StringData(2) = "c5.ALL.1.0.0.UCS_A.INSTALLDIR_1_ssleay32.dll"
oRec.StringData(3) = CurrentFileNameSL
oRec.IntegerData(4) = 159744
oRec.StringData(5) = CurrentFileVersion
oRec.IntegerData(7) = FileAttribs(msidbFileAttributesVital, 0)
oRec.StringData(6) = FileLanguage()
oRec.IntegerData(8) = 0
ValidateNEW(2)
RowUpdate()

MmID = "@VBS0472"
TableNow ""

MmID = "@VBS0473"
TableNowMk "_MAKEMSI_FileSource"

MmID = "@VBS0474"
RowPrepare 4

MmID = "@VBS0475"
oRec.StringData(1) = CurrentFileKey
oRec.StringData(2) = CurrentFile
oRec.StringData(3) = "2010-09-28"
oRec.StringData(4) = "13:54:38"
ValidateNEW(0)
RowUpdate()

MmID = "@VBS0476"
TableNow ""
ob_FileHash("Y")

MmID = "@VBS0477"
TableNowMk "Component"

MmID = "@VBS0478"
RowsPrepare "`Component` = 'c5.ALL.1.0.0.UCS_A.INSTALLDIR_1_ssleay32.dll'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0479"
oRec.IntegerData(4) = (oRec.IntegerData(4) AND NOT msidbComponentAttributesRegistryKeyPath)
oRec.StringData(6) = "ssleay32.dll"
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "`Component` = 'c5.ALL.1.0.0.UCS_A.INSTALLDIR_1_ssleay32.dll'")

MmID = "@VBS0480"
TableNow ""


MmID = "@VBS0481"

MmID = "@VBS0482"

MmID = "@VBS0483"
TableNowMk "Component"

MmID = "@VBS0484"
RowPrepare 6

MmID = "@VBS0485"
oRec.StringData(1) = "c6.ALL.1.0.0.UCS_A.INSTALLDIR_1_ucs_ad_connector.exe"
oRec.StringData(2) = GuidMake("")
oRec.StringData(3) = "INSTALLDIR"
oRec.IntegerData(4) = msidbComponentAttributesLocalOnly
oRec.StringData(5) = ""
oRec.StringData(6) = ""
ValidateFIELD(1)
RowUpdate()

MmID = "@VBS0486"


MmID = "@VBS0487"
TableNowMk "FeatureComponents"

MmID = "@VBS0488"
RowPrepare 2

MmID = "@VBS0489"
oRec.StringData(1) = "ALL.1.0.0.UCS_AD_Connector"
oRec.StringData(2) = "c6.ALL.1.0.0.UCS_A.INSTALLDIR_1_ucs_ad_connector.exe"
ValidateNEW(0)
RowUpdate()

MmID = "@VBS0490"
TableNow ""

CurrentFile="Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector\files\Programme\UCS-AD-Connector\ucs-ad-connector.exe"
CurrentFileKey="ucs_ad_connector.exe"
CurrentFileNameSL=Get83PlusLongName("ucs-ad-connector.exe")
ob_FileVersion("")

MmID = "@VBS0491"
TableNowMk "File"

MmID = "@VBS0492"
RowPrepare 8

MmID = "@VBS0493"
oRec.StringData(1) = CurrentFileKey
oRec.StringData(2) = "c6.ALL.1.0.0.UCS_A.INSTALLDIR_1_ucs_ad_connector.exe"
oRec.StringData(3) = CurrentFileNameSL
oRec.IntegerData(4) = 53248
oRec.StringData(5) = CurrentFileVersion
oRec.IntegerData(7) = FileAttribs(msidbFileAttributesVital, 0)
oRec.StringData(6) = FileLanguage()
oRec.IntegerData(8) = 0
ValidateNEW(2)
RowUpdate()

MmID = "@VBS0494"
TableNow ""

MmID = "@VBS0495"
TableNowMk "_MAKEMSI_FileSource"

MmID = "@VBS0496"
RowPrepare 4

MmID = "@VBS0497"
oRec.StringData(1) = CurrentFileKey
oRec.StringData(2) = CurrentFile
oRec.StringData(3) = "2010-09-28"
oRec.StringData(4) = "13:54:38"
ValidateNEW(0)
RowUpdate()

MmID = "@VBS0498"
TableNow ""
ob_FileHash("Y")

MmID = "@VBS0499"
TableNowMk "Component"

MmID = "@VBS0500"
RowsPrepare "`Component` = 'c6.ALL.1.0.0.UCS_A.INSTALLDIR_1_ucs_ad_connector.exe'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0501"
oRec.IntegerData(4) = (oRec.IntegerData(4) AND NOT msidbComponentAttributesRegistryKeyPath)
oRec.StringData(6) = "ucs_ad_connector.exe"
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "`Component` = 'c6.ALL.1.0.0.UCS_A.INSTALLDIR_1_ucs_ad_connector.exe'")

MmID = "@VBS0502"
TableNow ""




'######################################################################
MmLL = "installscript.mm(36)"
MmLT = "<$Files ""files\temp\*.*"" DestDir=""[TempFolder]"">"
'######################################################################


MmID = "@VBS0503"

MmID = "@VBS0504"

MmID = "@VBS0505"

MmID = "@VBS0506"
TableNowMk "Directory"

MmID = "@VBS0507"
RowPrepare 3

MmID = "@VBS0508"
oRec.StringData(1) = "TempFolder"
oRec.StringData(2) = "WindowsFolder"
oRec.StringData(3) = ".:Temp"
ValidateFIELD(1)
RowUpdate()

MmID = "@VBS0509"
TableNow ""

MmID = "@VBS0510"

MmID = "@VBS0511"
TableNowMk "Component"

MmID = "@VBS0512"
RowPrepare 6

MmID = "@VBS0513"
oRec.StringData(1) = "c7.ALL.1.0.0.UCS_A.TempFolder_x"
oRec.StringData(2) = GuidMake("")
oRec.StringData(3) = "TempFolder"
oRec.IntegerData(4) = msidbComponentAttributesLocalOnly
oRec.StringData(5) = ""
oRec.StringData(6) = ""
ValidateFIELD(1)
RowUpdate()

MmID = "@VBS0514"


MmID = "@VBS0515"
TableNowMk "FeatureComponents"

MmID = "@VBS0516"
RowPrepare 2

MmID = "@VBS0517"
oRec.StringData(1) = "ALL.1.0.0.UCS_AD_Connector"
oRec.StringData(2) = "c7.ALL.1.0.0.UCS_A.TempFolder_x"
ValidateNEW(0)
RowUpdate()

MmID = "@VBS0518"
TableNow ""

CurrentFile="Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector\files\temp\ucs-ad-connector-service.cmd"
CurrentFileKey="ucs_ad_connector_service.cmd"
CurrentFileNameSL=Get83PlusLongName("ucs-ad-connector-service.cmd")
ob_FileVersion("")

MmID = "@VBS0519"
TableNowMk "File"

MmID = "@VBS0520"
RowPrepare 8

MmID = "@VBS0521"
oRec.StringData(1) = CurrentFileKey
oRec.StringData(2) = "c7.ALL.1.0.0.UCS_A.TempFolder_x"
oRec.StringData(3) = CurrentFileNameSL
oRec.IntegerData(4) = 148
oRec.StringData(5) = CurrentFileVersion
oRec.IntegerData(7) = FileAttribs(msidbFileAttributesVital, 0)
oRec.StringData(6) = FileLanguage()
oRec.IntegerData(8) = 0
ValidateNEW(2)
RowUpdate()

MmID = "@VBS0522"
TableNow ""

MmID = "@VBS0523"
TableNowMk "_MAKEMSI_FileSource"

MmID = "@VBS0524"
RowPrepare 4

MmID = "@VBS0525"
oRec.StringData(1) = CurrentFileKey
oRec.StringData(2) = CurrentFile
oRec.StringData(3) = "2010-09-28"
oRec.StringData(4) = "13:54:38"
ValidateNEW(0)
RowUpdate()

MmID = "@VBS0526"
TableNow ""
ob_FileHash("Y")

MmID = "@VBS0527"
TableNowMk "Component"

MmID = "@VBS0528"
RowsPrepare "`Component` = 'c7.ALL.1.0.0.UCS_A.TempFolder_x'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0529"
oRec.IntegerData(4) = (oRec.IntegerData(4) AND NOT msidbComponentAttributesRegistryKeyPath)
oRec.StringData(6) = "ucs_ad_connector_service.cmd"
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "`Component` = 'c7.ALL.1.0.0.UCS_A.TempFolder_x'")

MmID = "@VBS0530"
TableNow ""




'######################################################################
MmLL = "installscript.mm(54)"
MmLT = "<$ExeCa EXE='[TempFolder]ucs-ad-connector-service.cmd' Args=^""MsgBox Title"" ""MsgBox text...""^ WorkDir=""TempFolder"" SEQ=""InstallFinalize-"" Type=""immediate ASync AnyRc"" Condition=""<$CONDITION_INSTALL_ONLY>"" >"
'######################################################################


MmID = "@VBS0531"




MmID = "@VBS0532"
TableNowMk "CustomAction"


MmID = "@VBS0533"
RowPrepare 5

MmID = "@VBS0534"
oRec.StringData(1) = "ExeCaKeyF01"
oRec.StringData(3) = "TempFolder"
oRec.IntegerData(2) = &H00E2
oRec.StringData(4) = """[TempFolder]ucs-ad-connector-service.cmd"" ""MsgBox Title"" ""MsgBox text..."""
ValidateFIELD(1)
RowUpdate()


MmID = "@VBS0535"
TableNow ""

SeqNo = GetSeqNumber("InstallExecuteSequence", "InstallFinalize-", 1)

MmID = "@VBS0536"
TableNowMk "InstallExecuteSequence"


MmID = "@VBS0537"
RowPrepare 3

MmID = "@VBS0538"
oRec.StringData(1) = "ExeCaKeyF01"
oRec.StringData(2) = "not Installed"
oRec.IntegerData(3) = SeqNo
ValidateFIELD(1)
RowUpdate()


MmID = "@VBS0539"
TableNow ""


MmID = "@VBS0540"
TableNowMk "ActionText"


MmID = "@VBS0541"
RowPrepare 3

MmID = "@VBS0542"
oRec.StringData(1) = "ExeCaKeyF01"
oRec.StringData(2) = "EXE Custom Action : ExeCaKeyF01"
ValidateFIELD(1)
RowUpdate()


MmID = "@VBS0543"
TableNow ""




'######################################################################
MmLL = "UiSample.MMH(152)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0544"
TableNowMk "Control"



'######################################################################
MmLL = "UiSample.MMH(169)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0545"
RowPrepare 12

MmID = "@VBS0546"
oRec.StringData(1) = "ProgressDlg"
oRec.StringData(2) = "ActionData"
oRec.StringData(3) = "Text"
oRec.StringData(9) = ""
oRec.IntegerData(4) = 35
oRec.IntegerData(5) = 130
oRec.IntegerData(6) = 300
oRec.IntegerData(7) = 90
oRec.IntegerData(8) = msidbControlAttributesNoPrefix or msidbControlAttributesVisible or msidbControlAttributesEnabled
oRec.StringData(10) = ""
oRec.StringData(11) = ""
oRec.StringData(12) = ""
ValidateFIELD(1)
RowUpdate()



'######################################################################
MmLL = "UiSample.MMH(170)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0547"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(171)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0548"
TableNowMk "EventMapping"



'######################################################################
MmLL = "UiSample.MMH(180)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0549"
RowPrepare 4

MmID = "@VBS0550"
oRec.StringData(1) = "ProgressDlg"
oRec.StringData(2) = "ActionData"
oRec.StringData(3) = "ActionData"
oRec.StringData(4) = "Text"
ValidateFIELD(1)
RowUpdate()



'######################################################################
MmLL = "UiSample.MMH(181)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0551"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(191)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0552"
TableNowMk "Control"



'######################################################################
MmLL = "UiSample.MMH(199)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0553"
RowsPrepare "`Dialog_` = 'ProgressDlg' AND `Control` = 'ActionText'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0554"
oRec.IntegerData(8) = oRec.IntegerData(8) or msidbControlAttributesNoPrefix
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "`Dialog_` = 'ProgressDlg' AND `Control` = 'ActionText'")



'######################################################################
MmLL = "UiSample.MMH(200)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0555"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(210)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0556"
TableNowMk "Control"



'######################################################################
MmLL = "UiSample.MMH(218)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0557"
RowsPrepare "Dialog_ = 'ProgressDlg' AND Control = 'Title'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0558"
oRec.IntegerData(6) = 300
oRec.IntegerData(7) = 30
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Dialog_ = 'ProgressDlg' AND Control = 'Title'")



'######################################################################
MmLL = "UiSample.MMH(219)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0559"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(228)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0560"
TableNowMk "Control"



'######################################################################
MmLL = "UiSample.MMH(235)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0561"
RowsPrepare "Dialog_ = 'ProgressDlg' AND Control = 'ProgressBar'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0562"
oRec.IntegerData(8) = 1
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Dialog_ = 'ProgressDlg' AND Control = 'ProgressBar'")



'######################################################################
MmLL = "UiSample.MMH(236)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0563"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(245)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0564"
TableNowMk "Control"



'######################################################################
MmLL = "UiSample.MMH(253)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0565"
RowsPrepare "`Dialog_` = 'ProgressDlg' AND `Control` = 'StatusLabel'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0566"
oRec.IntegerData(6) = 30
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "`Dialog_` = 'ProgressDlg' AND `Control` = 'StatusLabel'")



'######################################################################
MmLL = "UiSample.MMH(262)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0567"
RowsPrepare "`Dialog_` = 'ProgressDlg' AND `Control` = 'ActionText'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0568"
oRec.IntegerData(4) = 65
oRec.IntegerData(6) = 300
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "`Dialog_` = 'ProgressDlg' AND `Control` = 'ActionText'")



'######################################################################
MmLL = "UiSample.MMH(263)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0569"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(275)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0570"
TableNowMk "Dialog"



'######################################################################
MmLL = "UiSample.MMH(283)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0571"
RowsPrepare "`Title` = '[ProductName] [Setup]'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0572"
oRec.StringData(7) = "[ProductName] ([ProductVersion]) [Setup]"
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt > 0 then Error("Found " & RecCnt & " record(s), we expected ""? > 0"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "`Title` = '[ProductName] [Setup]'")



'######################################################################
MmLL = "UiSample.MMH(294)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0573"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(317)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0574"
TableNowMk "RadioButton"



'######################################################################
MmLL = "UiSample.MMH(325)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0575"
RowsPrepare ""
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO

MmID = "@VBS0576"
oRec.StringData(8) = replace(oRec.StringData(8), "icense", "icence")
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()



'######################################################################
MmLL = "UiSample.MMH(326)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0577"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(336)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0578"
TableNowMk "Dialog"



'######################################################################
MmLL = "UiSample.MMH(344)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0579"
RowsPrepare "`Title` = 'Installer Information'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0580"
oRec.StringData(7) = "[ProductName] ([ProductVersion]) - Installer Information"
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt > 0 then Error("Found " & RecCnt & " record(s), we expected ""? > 0"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "`Title` = 'Installer Information'")



'######################################################################
MmLL = "UiSample.MMH(345)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0581"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(353)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0582"
TableNowMk "Control"



'######################################################################
MmLL = "UiSample.MMH(360)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0583"
RowsPrepare "`Dialog_` = 'VerifyRepairDlg' and `Control` = 'Title'"
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO

MmID = "@VBS0584"
oRec.StringData(10) = oRec.StringData(10) & " "
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()



'######################################################################
MmLL = "UiSample.MMH(367)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0585"
RowsPrepare "`Dialog_` = 'VerifyRemoveDlg' and `Control` = 'Title'"
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO

MmID = "@VBS0586"
oRec.StringData(10) = oRec.StringData(10) & " "
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()



'######################################################################
MmLL = "UiSample.MMH(368)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0587"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(391)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0588"
TableNowMk "Dialog"



'######################################################################
MmLL = "UiSample.MMH(401)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0589"
RowsPrepare "`Dialog` = 'ErrorDlg'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0590"
oRec.IntegerData(4) = oRec.IntegerData(4) + 150
oRec.IntegerData(5) = oRec.IntegerData(5) + 80
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt = 1 then Error("Found " & RecCnt & " record(s), we expected ""? = 1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "`Dialog` = 'ErrorDlg'")



'######################################################################
MmLL = "UiSample.MMH(402)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0591"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(403)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0592"
TableNowMk "Control"



'######################################################################
MmLL = "UiSample.MMH(413)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0593"
RowsPrepare "`Dialog_` = 'ErrorDlg' and `Type`='PushButton'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0594"
oRec.IntegerData(4) = oRec.IntegerData(4) + 75
oRec.IntegerData(5) = oRec.IntegerData(5) + 80
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt > 0 then Error("Found " & RecCnt & " record(s), we expected ""? > 0"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "`Dialog_` = 'ErrorDlg' and `Type`='PushButton'")
dim ErrorTextControlAttr
 ErrorTextControlAttr = msidbControlAttributesNoPrefix 
 



'######################################################################
MmLL = "UiSample.MMH(432)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0595"
RowsPrepare "`Dialog_` = 'ErrorDlg' and `Control`='ErrorText'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0596"
oRec.StringData(3) = "Text"
oRec.IntegerData(8) = oRec.IntegerData(8) or ErrorTextControlAttr
oRec.IntegerData(6) = oRec.IntegerData(6) + 150
oRec.IntegerData(7) = oRec.IntegerData(7) + 80
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt = 1 then Error("Found " & RecCnt & " record(s), we expected ""? = 1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "`Dialog_` = 'ErrorDlg' and `Control`='ErrorText'")



'######################################################################
MmLL = "UiSample.MMH(433)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0597"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(455)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0598"
TableNowMk "Control"



'######################################################################
MmLL = "UiSample.MMH(463)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0599"
RowsPrepare "`Dialog_` = 'WelcomeDlg' and `Control`='Description'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0600"
oRec.IntegerData(7) = 165
oRec.StringData(10) = "This will install ""[ProductName]"" (version [ProductVersion], dated  [_MAKEMSI_BuildTime]) onto your computer."& vbCRLF & vbCRLF & "Click ""Next"" to continue."
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt = 1 then Error("Found " & RecCnt & " record(s), we expected ""? = 1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "`Dialog_` = 'WelcomeDlg' and `Control`='Description'")



'######################################################################
MmLL = "UiSample.MMH(464)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0601"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(473)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0602"
TableNowMk "InstallUISequence"



'######################################################################
MmLL = "UiSample.MMH(481)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0603"
RowsPrepare "`Action` = 'MaintenanceWelcomeDlg'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0604"
oRec.StringData(1) = "MaintenanceTypeDlg"
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt = 1 then Error("Found " & RecCnt & " record(s), we expected ""? = 1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "`Action` = 'MaintenanceWelcomeDlg'")



'######################################################################
MmLL = "UiSample.MMH(482)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0605"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(485)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0606"
TableNowMk "Control"



'######################################################################
MmLL = "UiSample.MMH(493)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0607"
RowsPrepare "`Dialog_` = 'MaintenanceTypeDlg' and `Control`='Back'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0608"
oRec.IntegerData(8) = oRec.IntegerData(8) and not (msidbControlAttributesVisible or msidbControlAttributesEnabled)
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt = 1 then Error("Found " & RecCnt & " record(s), we expected ""? = 1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "`Dialog_` = 'MaintenanceTypeDlg' and `Control`='Back'")



'######################################################################
MmLL = "UiSample.MMH(494)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0609"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(505)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0610"
TableNowMk "Control"



'######################################################################
MmLL = "UiSample.MMH(521)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0611"
DeleteTableRows("Dialog_ = 'AdminRegistrationDlg' AND Control = 'CDKeyLabel'")
 

MmID = "@VBS0612"
DeleteTableRows("Dialog_ = 'AdminRegistrationDlg' AND Control = 'CDKeyEdit'")
 

MmID = "@VBS0613"
RowsPrepare "Dialog_ = 'AdminRegistrationDlg' AND Control = 'OrganizationEdit'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0614"
oRec.StringData(11) = "Back"
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Dialog_ = 'AdminRegistrationDlg' AND Control = 'OrganizationEdit'")



'######################################################################
MmLL = "UiSample.MMH(522)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0615"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(532)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0616"
TableNowMk "ControlEvent"



'######################################################################
MmLL = "UiSample.MMH(540)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0617"
RowsPrepare "Dialog_ = 'AdminWelcomeDlg' AND Control_ = 'Next' AND Event = 'NewDialog' AND Argument = 'AdminRegistrationDlg' AND Condition = '1'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0618"
oRec.StringData(4) = "AdminInstallPointDlg"
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Dialog_ = 'AdminWelcomeDlg' AND Control_ = 'Next' AND Event = 'NewDialog' AND Argument = 'AdminRegistrationDlg' AND Condition = '1'")



'######################################################################
MmLL = "UiSample.MMH(549)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0619"
RowsPrepare "Dialog_ = 'AdminInstallPointDlg' AND Control_ = 'Back' AND Event = 'NewDialog' AND Argument = 'AdminRegistrationDlg' AND Condition = '1'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0620"
oRec.StringData(4) = "AdminWelcomeDlg"
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Dialog_ = 'AdminInstallPointDlg' AND Control_ = 'Back' AND Event = 'NewDialog' AND Argument = 'AdminRegistrationDlg' AND Condition = '1'")



'######################################################################
MmLL = "UiSample.MMH(550)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0621"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(590)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0622"
TableNowMk "Control"



'######################################################################
MmLL = "UiSample.MMH(600)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0623"
RowsPrepare "`Control`='BottomLine' and `Type`='Line' and (`Dialog_` <> 'AdminWelcomeDlg') and (`Dialog_` <> 'ExitDialog') and (`Dialog_` <> 'FatalError') and (`Dialog_` <> 'MaintenanceWelcomeDlg') and (`Dialog_` <> 'PrepareDlg') and (`Dialog_` <> 'ResumeDlg') and (`Dialog_` <> 'UserExit') and (`Dialog_` <> 'WelcomeDlg')"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0624"
oRec.IntegerData(4) = oRec.IntegerData(4) + 95 + 2
oRec.IntegerData(6) = oRec.IntegerData(6) - 95 - 2
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt >= 1 then Error("Found " & RecCnt & " record(s), we expected ""? >= 1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "`Control`='BottomLine' and `Type`='Line' and (`Dialog_` <> 'AdminWelcomeDlg') and (`Dialog_` <> 'ExitDialog') and (`Dialog_` <> 'FatalError') and (`Dialog_` <> 'MaintenanceWelcomeDlg') and (`Dialog_` <> 'PrepareDlg') and (`Dialog_` <> 'ResumeDlg') and (`Dialog_` <> 'UserExit') and (`Dialog_` <> 'WelcomeDlg')")



'######################################################################
MmLL = "UiSample.MMH(601)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0625"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(640)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0626"
TableNowMk "TextStyle"



'######################################################################
MmLL = "UiSample.MMH(650)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0627"
RowPrepare 5

MmID = "@VBS0628"
oRec.StringData(1) = "BrandingLR"
oRec.StringData(2) = "Tahoma"
oRec.IntegerData(3) = 8
oRec.IntegerData(4) = &HFFFFFF
oRec.IntegerData(5) = 0
ValidateFIELD(1)
RowUpdate()



'######################################################################
MmLL = "UiSample.MMH(660)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0629"
RowPrepare 5

MmID = "@VBS0630"
oRec.StringData(1) = "BrandingUL"
oRec.StringData(2) = "Tahoma"
oRec.IntegerData(3) = 8
oRec.IntegerData(4) = msiDatabaseNullInteger
oRec.IntegerData(5) = 0
ValidateFIELD(1)
RowUpdate()



'######################################################################
MmLL = "UiSample.MMH(661)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0631"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(662)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0632"
TableNowMk "Control"



'######################################################################
MmLL = "UiSample.MMH(681)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0633"
RowsPrepare "`Control`='BottomLine' and `Type`='Line' and (`Dialog_` <> 'AdminWelcomeDlg') and (`Dialog_` <> 'ExitDialog') and (`Dialog_` <> 'FatalError') and (`Dialog_` <> 'MaintenanceWelcomeDlg') and (`Dialog_` <> 'PrepareDlg') and (`Dialog_` <> 'ResumeDlg') and (`Dialog_` <> 'UserExit') and (`Dialog_` <> 'WelcomeDlg')"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0634"
oRec.StringData(2) = "BrandingLR"
oRec.StringData(3) = "Text"
oRec.IntegerData(4) = 2 + 1
oRec.IntegerData(5) = oRec.IntegerData(5) - (10\2)+1
oRec.IntegerData(7) = 10
oRec.IntegerData(6) = 95
oRec.IntegerData(8) = msidbControlAttributesVisible or msidbControlAttributesNoPrefix
oRec.StringData(10) = "{&BrandingLR}MakeMsi by Dennis Bareis"
oRec.StringData(11) = ""
oRec.StringData(12) = ""
ValidateFETCH(1)
RowsINSERT()
loop
SqlViewClose()
if not RecCnt >= 1 then Error("Found " & RecCnt & " record(s), we expected ""? >= 1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "`Control`='BottomLine' and `Type`='Line' and (`Dialog_` <> 'AdminWelcomeDlg') and (`Dialog_` <> 'ExitDialog') and (`Dialog_` <> 'FatalError') and (`Dialog_` <> 'MaintenanceWelcomeDlg') and (`Dialog_` <> 'PrepareDlg') and (`Dialog_` <> 'ResumeDlg') and (`Dialog_` <> 'UserExit') and (`Dialog_` <> 'WelcomeDlg')")



'######################################################################
MmLL = "UiSample.MMH(701)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0635"
RowsPrepare "`Control`='BottomLine' and `Type`='Line' and (`Dialog_` <> 'AdminWelcomeDlg') and (`Dialog_` <> 'ExitDialog') and (`Dialog_` <> 'FatalError') and (`Dialog_` <> 'MaintenanceWelcomeDlg') and (`Dialog_` <> 'PrepareDlg') and (`Dialog_` <> 'ResumeDlg') and (`Dialog_` <> 'UserExit') and (`Dialog_` <> 'WelcomeDlg')"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0636"
oRec.StringData(2) = "BrandingUL"
oRec.StringData(3) = "Text"
oRec.StringData(9) = ""
oRec.IntegerData(4) = 2
oRec.IntegerData(5) = oRec.IntegerData(5) - (10\2)
oRec.IntegerData(7) = 10
oRec.IntegerData(6) = 95
oRec.IntegerData(8) = msidbControlAttributesVisible or msidbControlAttributesTransparent or msidbControlAttributesNoPrefix
oRec.StringData(10) = "{&BrandingUL}MakeMsi by Dennis Bareis"
oRec.StringData(11) = ""
oRec.StringData(12) = ""
ValidateFETCH(1)
RowsINSERT()
loop
SqlViewClose()
if not RecCnt >= 1 then Error("Found " & RecCnt & " record(s), we expected ""? >= 1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "`Control`='BottomLine' and `Type`='Line' and (`Dialog_` <> 'AdminWelcomeDlg') and (`Dialog_` <> 'ExitDialog') and (`Dialog_` <> 'FatalError') and (`Dialog_` <> 'MaintenanceWelcomeDlg') and (`Dialog_` <> 'PrepareDlg') and (`Dialog_` <> 'ResumeDlg') and (`Dialog_` <> 'UserExit') and (`Dialog_` <> 'WelcomeDlg')")



'######################################################################
MmLL = "UiSample.MMH(702)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0637"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(713)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0638"
TableNowMk "Control"



'######################################################################
MmLL = "UiSample.MMH(722)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0639"
RowsPrepare "Dialog_ = 'CustomizeDlg' AND Control = 'Description'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0640"
oRec.IntegerData(4) = 15
oRec.IntegerData(6) = 290
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Dialog_ = 'CustomizeDlg' AND Control = 'Description'")



'######################################################################
MmLL = "UiSample.MMH(730)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0641"
RowsPrepare "Dialog_ = 'CustomizeDlg' AND Control = 'Text'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0642"
oRec.IntegerData(4) = 15
oRec.IntegerData(6) = 330
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Dialog_ = 'CustomizeDlg' AND Control = 'Text'")



'######################################################################
MmLL = "UiSample.MMH(740)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0643"
RowsPrepare "Dialog_ = 'CustomizeDlg' AND Control = 'Tree'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0644"
oRec.IntegerData(4) = 10
oRec.IntegerData(5) = 77
oRec.IntegerData(6) = 189
oRec.IntegerData(7) = 123
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Dialog_ = 'CustomizeDlg' AND Control = 'Tree'")



'######################################################################
MmLL = "UiSample.MMH(750)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0645"
RowsPrepare "Dialog_ = 'CustomizeDlg' AND Control = 'Box'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0646"
oRec.IntegerData(4) = 207
oRec.IntegerData(5) = 73
oRec.IntegerData(6) = 153
oRec.IntegerData(7) = 127
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Dialog_ = 'CustomizeDlg' AND Control = 'Box'")



'######################################################################
MmLL = "UiSample.MMH(760)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0647"
RowsPrepare "Dialog_ = 'CustomizeDlg' AND Control = 'LocationLabel'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0648"
oRec.IntegerData(4) = 15
oRec.IntegerData(5) = 203
oRec.IntegerData(6) = 37
oRec.IntegerData(7) = 11
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Dialog_ = 'CustomizeDlg' AND Control = 'LocationLabel'")



'######################################################################
MmLL = "UiSample.MMH(771)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0649"
RowsPrepare "Dialog_ = 'CustomizeDlg' AND Control = 'Location'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0650"
oRec.IntegerData(4) = 55
oRec.IntegerData(5) = 203
oRec.IntegerData(6) = 243
oRec.IntegerData(7) = 31
oRec.StringData(10) = "{&FeatureDirFont}<The feature's path>"
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Dialog_ = 'CustomizeDlg' AND Control = 'Location'")



'######################################################################
MmLL = "UiSample.MMH(778)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0651"
RowsPrepare "Dialog_ = 'CustomizeDlg' AND Control = 'Browse'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0652"
oRec.IntegerData(5) = 208
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Dialog_ = 'CustomizeDlg' AND Control = 'Browse'")



'######################################################################
MmLL = "UiSample.MMH(788)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0653"
RowsPrepare "Dialog_ = 'CustomizeDlg' AND Control = 'ItemDescription'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0654"
oRec.IntegerData(4) = 212
oRec.IntegerData(5) = 79
oRec.IntegerData(6) = 144
oRec.IntegerData(7) = 65
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Dialog_ = 'CustomizeDlg' AND Control = 'ItemDescription'")



'######################################################################
MmLL = "UiSample.MMH(798)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0655"
RowsPrepare "Dialog_ = 'CustomizeDlg' AND Control = 'ItemSize'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0656"
oRec.IntegerData(4) = 212
oRec.IntegerData(5) = 147
oRec.IntegerData(6) = 144
oRec.IntegerData(7) = 51
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Dialog_ = 'CustomizeDlg' AND Control = 'ItemSize'")



'######################################################################
MmLL = "UiSample.MMH(800)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0657"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(803)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0658"
TableNowMk "TextStyle"



'######################################################################
MmLL = "UiSample.MMH(811)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0659"
RowPrepare 5

MmID = "@VBS0660"
oRec.StringData(1) = "FeatureDirFont"
oRec.StringData(2) = "Tahoma"
oRec.IntegerData(3) = 8
oRec.IntegerData(4) = 16711680
ValidateFIELD(1)
RowUpdate()



'######################################################################
MmLL = "UiSample.MMH(812)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0661"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(823)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0662"

MmID = "@VBS0663"
TableNowMk "Binary"

MmID = "@VBS0664"
RowPrepare 2

MmID = "@VBS0665"
oRec.SetStream 2, "C:\Programme\MakeMsi\MmCustomSetup.ico"
oRec.StringData(1) = "custicon"

ValidateStreamKeyLength array(1)
ValidateFIELD(1)
RowUpdate()

MmID = "@VBS0666"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(836)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0667"

MmID = "@VBS0668"
TableNowMk "Binary"

MmID = "@VBS0669"
RowPrepare 2

MmID = "@VBS0670"
oRec.SetStream 2, "C:\Programme\MakeMsi\white.bmp"
oRec.StringData(1) = "bannrbmp"

ValidateStreamKeyLength array(1)
ValidateFIELD(1)
RowUpdate()

MmID = "@VBS0671"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(872)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0672"

MmID = "@VBS0673"
TableNowMk "Binary"

MmID = "@VBS0674"
RowPrepare 2

MmID = "@VBS0675"
oRec.SetStream 2, "C:\Programme\MakeMsi\LeftSide.bmp"
oRec.StringData(1) = "dlgbmp"

ValidateStreamKeyLength array(1)
ValidateFIELD(1)
RowUpdate()

MmID = "@VBS0676"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(933)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0677"
TableNowMk "Control"



'######################################################################
MmLL = "UiSample.MMH(940)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0678"
RowsPrepare "Dialog_ = 'AdminWelcomeDlg' AND Control = 'Description'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0679"
oRec.IntegerData(5) = 85
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Dialog_ = 'AdminWelcomeDlg' AND Control = 'Description'")



'######################################################################
MmLL = "UiSample.MMH(947)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0680"
RowsPrepare "Dialog_ = 'ExitDialog' AND Control = 'Description'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0681"
oRec.IntegerData(5) = 85
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Dialog_ = 'ExitDialog' AND Control = 'Description'")



'######################################################################
MmLL = "UiSample.MMH(954)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0682"
RowsPrepare "Dialog_ = 'FatalError' AND Control = 'Description1'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0683"
oRec.IntegerData(5) = 85
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Dialog_ = 'FatalError' AND Control = 'Description1'")



'######################################################################
MmLL = "UiSample.MMH(961)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0684"
RowsPrepare "Dialog_ = 'FatalError' AND Control = 'Description2'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0685"
oRec.IntegerData(5) = 130
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Dialog_ = 'FatalError' AND Control = 'Description2'")



'######################################################################
MmLL = "UiSample.MMH(968)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0686"
RowsPrepare "Dialog_ = 'PrepareDlg' AND Control = 'Description'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0687"
oRec.IntegerData(5) = 85
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Dialog_ = 'PrepareDlg' AND Control = 'Description'")



'######################################################################
MmLL = "UiSample.MMH(976)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0688"
RowsPrepare "Dialog_ = 'PrepareDlg' AND Control = 'ActionText'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0689"
oRec.IntegerData(5) = 130
oRec.StringData(10) = "Initialising... Please wait..."
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Dialog_ = 'PrepareDlg' AND Control = 'ActionText'")



'######################################################################
MmLL = "UiSample.MMH(983)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0690"
RowsPrepare "Dialog_ = 'PrepareDlg' AND Control = 'ActionData'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0691"
oRec.IntegerData(5) = 155
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Dialog_ = 'PrepareDlg' AND Control = 'ActionData'")



'######################################################################
MmLL = "UiSample.MMH(990)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0692"
RowsPrepare "Dialog_ = 'UserExit' AND Control = 'Description1'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0693"
oRec.IntegerData(5) = 85
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Dialog_ = 'UserExit' AND Control = 'Description1'")



'######################################################################
MmLL = "UiSample.MMH(997)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0694"
RowsPrepare "Dialog_ = 'UserExit' AND Control = 'Description2'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0695"
oRec.IntegerData(5) = 130
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Dialog_ = 'UserExit' AND Control = 'Description2'")



'######################################################################
MmLL = "UiSample.MMH(1004)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0696"
RowsPrepare "Dialog_ = 'MaintenanceWelcomeDlg' AND Control = 'Description'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0697"
oRec.IntegerData(5) = 85
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Dialog_ = 'MaintenanceWelcomeDlg' AND Control = 'Description'")



'######################################################################
MmLL = "UiSample.MMH(1011)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0698"
RowsPrepare "Dialog_ = 'ResumeDlg' AND Control = 'Description'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0699"
oRec.IntegerData(5) = 85
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Dialog_ = 'ResumeDlg' AND Control = 'Description'")



'######################################################################
MmLL = "UiSample.MMH(1018)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0700"
RowsPrepare "Dialog_ = 'WelcomeDlg' AND Control = 'Description'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0701"
oRec.IntegerData(5) = 85
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Dialog_ = 'WelcomeDlg' AND Control = 'Description'")



'######################################################################
MmLL = "UiSample.MMH(1019)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0702"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(1083)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0703"
TableNowMk "Dialog"
 

MmID = "@VBS0704"
RowsPrepare "`Dialog` = 'CancelDlg'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0705"
oRec.IntegerData(2) = 60
oRec.IntegerData(3) = 75
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt = 1 then Error("Found " & RecCnt & " record(s), we expected ""? = 1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "`Dialog` = 'CancelDlg'")
 

MmID = "@VBS0706"
TableNow ""

MmID = "@VBS0707"
TableNowMk "Dialog"
 

MmID = "@VBS0708"
RowsPrepare "`Dialog` = 'ErrorDlg'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0709"
oRec.IntegerData(2) = 60
oRec.IntegerData(3) = 75
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt = 1 then Error("Found " & RecCnt & " record(s), we expected ""? = 1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "`Dialog` = 'ErrorDlg'")
 

MmID = "@VBS0710"
TableNow ""

MmID = "@VBS0711"
TableNowMk "Dialog"
 

MmID = "@VBS0712"
RowsPrepare "`Dialog` = 'WaitForCostingDlg'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0713"
oRec.IntegerData(2) = 60
oRec.IntegerData(3) = 75
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt = 1 then Error("Found " & RecCnt & " record(s), we expected ""? = 1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "`Dialog` = 'WaitForCostingDlg'")
 

MmID = "@VBS0714"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(1091)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0715"
cb_PropValue = "0"

MmID = "@VBS0716"
TableNowMk "Property"
   if cb_PropValue = "" then

MmID = "@VBS0717"
DeleteTableRows("`Property` = 'MM_REDUCED_UI'")
   else

MmID = "@VBS0718"
RowPrepare 2

MmID = "@VBS0719"
oRec.StringData(1) = "MM_REDUCED_UI"
oRec.StringData(2) = cb_PropValue
ValidateFIELD(1)
RowUpdate()
   end if

MmID = "@VBS0720"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(1094)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0721"
TableNowMk "InstallUISequence"



'######################################################################
MmLL = "UiSample.MMH(1102)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0722"
RowsPrepare "Action = 'ExitDialog'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0723"
oRec.StringData(2) = "Installed or (MM_REDUCED_UI = 0)"
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Action = 'ExitDialog'")



'######################################################################
MmLL = "UiSample.MMH(1110)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0724"
RowsPrepare "Action = 'WelcomeDlg'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0725"
oRec.StringData(2) = "NOT Installed and (MM_REDUCED_UI = 0)"
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Action = 'WelcomeDlg'")



'######################################################################
MmLL = "UiSample.MMH(1111)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0726"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(1170)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0727"
TableNowMk "Property"



'######################################################################
MmLL = "UiSample.MMH(1171)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0728"
DeleteTableRows("`Property` = 'ComponentDownload'")



'######################################################################
MmLL = "UiSample.MMH(1172)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0729"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(1186)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0730"
TableNowMk "ControlEvent"



'######################################################################
MmLL = "UiSample.MMH(1194)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0731"
RowsPrepare "Dialog_ = 'CancelDlg' AND Control_ = 'Yes' AND Event = 'EndDialog' AND Argument = 'Exit' AND Condition = '1'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0732"
oRec.IntegerData(6) = 2
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Dialog_ = 'CancelDlg' AND Control_ = 'Yes' AND Event = 'EndDialog' AND Argument = 'Exit' AND Condition = '1'")



'######################################################################
MmLL = "UiSample.MMH(1206)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0733"
RowPrepare 6

MmID = "@VBS0734"
oRec.StringData(1) = "CancelDlg"
oRec.StringData(2) = "Yes"
oRec.StringData(3) = "[UserPressedYesOnCancelDlg]"
oRec.StringData(4) = "YES"
oRec.StringData(5) = "1"
oRec.IntegerData(6) = 1
ValidateFIELD(1)
RowUpdate()



'######################################################################
MmLL = "UiSample.MMH(1208)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0735"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(1209)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0736"
TableNowMk "InstallUISequence"



'######################################################################
MmLL = "UiSample.MMH(1217)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0737"
RowsPrepare "Action = 'UserExit'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0738"
oRec.StringData(2) = "not UserPressedYesOnCancelDlg"
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Action = 'UserExit'")



'######################################################################
MmLL = "UiSample.MMH(1218)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0739"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(1317)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0740"
TableNowMk "Control"



'######################################################################
MmLL = "UiSample.MMH(1324)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0741"
RowsPrepare "`Dialog_` = 'FatalError' AND `Control` = 'Title'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0742"
oRec.StringData(10) = "{\VerdanaBold13Red}[ProductName] [Wizard] ended prematurely"
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "`Dialog_` = 'FatalError' AND `Control` = 'Title'")



'######################################################################
MmLL = "UiSample.MMH(1325)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0743"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(1326)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0744"
TableNowMk "TextStyle"



'######################################################################
MmLL = "UiSample.MMH(1335)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0745"
RowPrepare 5

MmID = "@VBS0746"
oRec.StringData(1) = "VerdanaBold13Red"
oRec.StringData(2) = "Verdana"
oRec.IntegerData(3) = 13
oRec.IntegerData(4) = 255
oRec.IntegerData(5) = 1
ValidateFIELD(1)
RowUpdate()



'######################################################################
MmLL = "UiSample.MMH(1336)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0747"
TableNow ""



'######################################################################
MmLL = "UiSample.MMH(1347)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0748"
TableNowMk "Control"



'######################################################################
MmLL = "UiSample.MMH(1354)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0749"
RowsPrepare "Dialog_ = 'VerifyReadyDlg' AND Control = 'Text'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0750"
oRec.IntegerData(7) = 160
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "Dialog_ = 'VerifyReadyDlg' AND Control = 'Text'")



'######################################################################
MmLL = "UiSample.MMH(1355)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0751"
TableNow ""

 



'######################################################################
MmLL = "installscript.mm(54)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0752"


MmID = "@VBS0753"
cb_PropValue = "C:\Programme\MakeMsi\MakeMsi.MMH (v10.169, 21,924 bytes, dated Tue Nov 24 2009 at 5:41:56pm)"

MmID = "@VBS0754"
TableNowMk "Property"
   if cb_PropValue = "" then

MmID = "@VBS0755"
DeleteTableRows("`Property` = '_MAKEMSI_Header_MAKEMSI.MMH'")
   else

MmID = "@VBS0756"
RowPrepare 2

MmID = "@VBS0757"
oRec.StringData(1) = "_MAKEMSI_Header_MAKEMSI.MMH"
oRec.StringData(2) = cb_PropValue
ValidateFIELD(1)
RowUpdate()
   end if

MmID = "@VBS0758"
TableNow ""


MmID = "@VBS0759"
cb_PropValue = "Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector\installscript.mm (2,601 bytes, dated Tue Sep 28 2010 at 1:54:38pm)"

MmID = "@VBS0760"
TableNowMk "Property"
   if cb_PropValue = "" then

MmID = "@VBS0761"
DeleteTableRows("`Property` = '_MAKEMSI_Source_INSTALLSCRIPT.MM'")
   else

MmID = "@VBS0762"
RowPrepare 2

MmID = "@VBS0763"
oRec.StringData(1) = "_MAKEMSI_Source_INSTALLSCRIPT.MM"
oRec.StringData(2) = cb_PropValue
ValidateFIELD(1)
RowUpdate()
   end if

MmID = "@VBS0764"
TableNow ""


MmID = "@VBS0765"
cb_PropValue = "C:\Programme\MakeMsi\COMPANY.MMH (v08.202, 53,874 bytes, dated Sun Mar 28 2010 at 5:21:00pm)"

MmID = "@VBS0766"
TableNowMk "Property"
   if cb_PropValue = "" then

MmID = "@VBS0767"
DeleteTableRows("`Property` = '_MAKEMSI_Header_COMPANY.MMH'")
   else

MmID = "@VBS0768"
RowPrepare 2

MmID = "@VBS0769"
oRec.StringData(1) = "_MAKEMSI_Header_COMPANY.MMH"
oRec.StringData(2) = cb_PropValue
ValidateFIELD(1)
RowUpdate()
   end if

MmID = "@VBS0770"
TableNow ""


MmID = "@VBS0771"
cb_PropValue = "C:\Programme\MakeMsi\DEPT.MMH (v03.171, 4,275 bytes, dated Sat May 7 2005 at 9:10:04am)"

MmID = "@VBS0772"
TableNowMk "Property"
   if cb_PropValue = "" then

MmID = "@VBS0773"
DeleteTableRows("`Property` = '_MAKEMSI_Header_DEPT.MMH'")
   else

MmID = "@VBS0774"
RowPrepare 2

MmID = "@VBS0775"
oRec.StringData(1) = "_MAKEMSI_Header_DEPT.MMH"
oRec.StringData(2) = cb_PropValue
ValidateFIELD(1)
RowUpdate()
   end if

MmID = "@VBS0776"
TableNow ""







MmID = "@VBS0777"
TableNowMk "Component"


MmID = "@VBS0778"
RowsPrepare ""
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO

'--- START of USER Code ---

MmID = "@VBS0779"
on error resume next



dim CName : CName = oRec.StringData(1)
dim CGuid : CGuid = oRec.StringData(2)
VbsReturnMacro "CompGuid." & CName, CGuid

MmID = "@VBS0780"



MmID = "@VBS0781"
VbsCheck "/VBS Command detected failure!" & vbCRLF & vbCRLF & "VBS command: installscript.mm(54) - Processing ROW command's query results"
on error goto 0

MmID = "@VBS0782"

loop
SqlViewClose()


MmID = "@VBS0783"
TableNow ""


MmID = "@VBS0784"




pc_COMPILE_CABDDF_Compress          = "ON"
pc_COMPILE_CABDDF_CompressionType   = "LZX"
pc_COMPILE_CABDDF_CompressionLevel  = "7"
pc_COMPILE_CABDDF_CompressionMemory = "21"
pc_COMPILE_CABDDF_ClusterSize       = "4096"
pc_COMPILE_CAB_FILE_NAME            = "MM*"
pc_CompileMsi "This is the ""end of pass 1 compile""", ""





if   TransformingFile <> ""  and WantedMstFile <> "" then
on error resume next
'oMSI.commit
say ""
say "Creating Transform: " & WantedMstFile
dim oMsiBefore : set oMsiBefore = oInstaller.OpenDatabase(TransformingFile, msiOpenDatabaseModeReadOnly)
VbsCheck "Opening original MSI: " & TransformingFile
dim MstChanges : MstChanges = oMsi.GenerateTransform(oMsiBefore, WantedMstFile)
VbsCheck "Creating Transform: " & WantedMstFile
if  MstChanges then
say "    * Changes Detected"
else
say "    * No changes found!"
end if
say "    * Adding Summary Information (ignore=" & msiTransformErrorNone & ", validate=" & msiTransformValidationNone & ")"
dim UndocumentedRc : UndocumentedRc = oMsi.CreateTransformSummaryInfo(oMsiBefore, WantedMstFile, msiTransformErrorNone, msiTransformValidationNone)
VbsCheck "Creating transform summary information"
say "    * Transform Completed."
set oMsiBefore = Nothing
on error goto 0
end if
dim LastSeqNumber : LastSeqNumber = GetNextFileSequence() - 1
dim Closing : Closing = MsiFileName
MsiClose(false)
say "Closing the Windows Installer Database (updates completed)."

MergeModMergeModulesNow false, LastSeqNumber
VbsReturnMacro "FINISHED", "YES"
say "Successfully processed """ & Closing & """."
say GetAmPmTime() & ": Took " & Elapsed() & " seconds."
say ""



oRetStream.close()
set oRetStream = Nothing
set oInstaller = Nothing
VbsQuit 0







'=========================================================================
function ComponentDir(ByVal Component)
'=========================================================================
on error resume next
dim SQL, oRecord
SQL = "SELECT * FROM `Component` WHERE Component = '" & Component & "'"
SqlOpenExec(Sql)
set oRecord = SqlViewFetch()
if  oRecord is Nothing then
error "The component """ & Component & """ does not exist (so directory can't be determined)!"
else
ComponentDir = oRecord.StringData(3)
if   ComponentDir = "" then
error "The component """ & Component & """ has a null ""Directory_"" column (so directory can't be determined)!"
end if
end if
set oRecord = Nothing
SqlViewClose()
end function


'=========================================================================
sub DumpComponentTable4HtmlReport()
'=========================================================================
on error resume next
dim CompCnt : CompCnt = 0
SqlOpenExec("SELECT `Component`, `ComponentId`, `Directory_`, `Attributes`, `Condition`, `KeyPath` FROM `Component`")
do
dim oRecord : set oRecord = SqlViewFetch()
if  oRecord is Nothing then exit do
dim CompName  : CompName  = oRecord.StringData(1)
dim CompGuid2  : CompGuid2  = oRecord.StringData(2)
CompCnt = CompCnt + 1
VbsReturnMacro "$Component#" & CompCnt, oRecord.StringData(1) & chr(1) & oRecord.StringData(2) & chr(1) & oRecord.StringData(3) & chr(1) & oRecord.IntegerData(4) & chr(1) & oRecord.StringData(5) & chr(1) & oRecord.StringData(6)
loop
SqlViewClose()
VbsReturnMacro "$Component#Count", CompCnt
end sub


'=========================================================================
function MakeSfnLfn(ByVal ParentDirKey, ByVal PassedSpec)
'=========================================================================
if  instr(1, PassedSpec, "|", 1) <> 0 then
MakeSfnLfn = PassedSpec
else
dim EightThree : EightThree = Need83Name(ParentDirKey, PassedSpec)
if   EightThree = PassedSpec then
MakeSfnLfn = EightThree
else
MakeSfnLfn = EightThree & "|" & PassedSpec
end if
end if
end function


'=========================================================================
sub Need83NameStart()
'=========================================================================
Need83BaseDir = TmpDir & "\MM83-53851"
if  not ofs.FolderExists(Need83BaseDir) Then
set oNeed83BaseDir = oFS.CreateFolder(Need83BaseDir)
end if
end sub


'=========================================================================
sub Need83NameEnd()
'=========================================================================
on error resume next
oNeed83BaseDir.Delete()
set oNeed83BaseDir = Nothing
end sub


'=========================================================================
function Need83Name(ByVal ParentDirKey, ByVal LongName)
'=========================================================================
dim ErrPrefix : ErrPrefix = "We were asked to generate a 8.3 formatted name for """ & LongName & """." & vbCRLF & vbCRLF
if  instr(LongName, "\") <> 0 or instr(LongName, ":") <> 0 then
Error ErrPrefix & "Drive letters or paths are not supported (a "":"" or ""\"" was detected)."
end if
on error resume next
dim EN, ET
dim ParentDir : ParentDir = Need83BaseDir & "\" & ParentDirKey
if  not oFS.FolderExists(ParentDir) then
oFS.CreateFolder ParentDir
if  err.number <> 0 then
Error ErrPrefix & "We failed creating the parent directory of """ & ParentDirKey & """, reason 0x" & hex(err.number) & " - " & err.description
end if
end if
dim LongFolder : LongFolder    = ParentDir & "\" & LongName
dim o83Folder
if  oFS.FolderExists(LongFolder) then
set o83Folder = oFS.GetFolder(LongFolder)
if   err.number <> 0 then
Error ErrPrefix & "GetFolder() failed on an existing folder of """ & LongFolder & """. Reason 0x" & hex(err.number) & " - " & err.description
end if
else
set o83Folder = oFS.CreateFolder(LongFolder)
if   err.number <> 0 then
Error ErrPrefix & "The name probably contains invalid characters. Reason 0x" & hex(err.number) & " - " & err.description
end if
end if
on error goto 0
Need83Name = ShortName(o83Folder, true)
set o83Folder  = Nothing
end function


'=========================================================================
function HasDllRegisterServer(FileName)
'=========================================================================
on error resume next
dim oTools
Set oTools = MkObject("MAKEMSI.Tools")
dim Answer : Answer = oTools.HasDllRegisterServer(FileName)
if  err.number = 0 then
if  Answer <> 0 then
HasDllRegisterServer = ""
else
HasDllRegisterServer = "<span title='We successfully determined that this file does not have self registration entry points!'>No</span>"
end if
else
dim ED : ED = err.description
if  ED = "" then
ED = "ERROR 0x" & hex(err.number)
end if
dim WeText : WeText = "We could not determine if the file """ & FileName & """ needs self registration or not. The reason being -> " & ED
Say("")
Say("WARNING: " & WeText)
Say("")
dim H
ED = replace(ED, """", "&quot;")
HasDllRegisterServer = "<span title=""" & ED & """>No<font color=red>?</font></span>"
end if
Set oTools = Nothing
end function


'=========================================================================
sub ob_FileVersion(ByVal VersionForUnversionedFile)
'=========================================================================
on error resume next
dim Real : Real = ""
CurrentFileVersion = oInstaller.FileVersion(CurrentFile)
if  err.number <> 0 then
CurrentFileVersion = ""
end if
if   CurrentFileVersion = "" then
CurrentFileVersion = VersionForUnversionedFile
Real               = "*"
end if
if  CurrentFileVersion <> "" then
VbsReturnMacro "FileVersion." & CurrentFileKey, CurrentFileVersion & Real
end if
end sub


'=========================================================================
function FileLanguage()
'=========================================================================
on error resume next
FileLanguage = oInstaller.FileLanguage(CurrentFile)
if  err.number <> 0 then
FileLanguage = "1033"
end if
if  FileLanguage <> "" then
VbsReturnMacro "FileLanguage." & CurrentFileKey, FileLanguage
end if
end function


'=========================================================================
function Get83PlusLongName(DestLongName)
'
' Called for entries being placed into the "File" table. If the 8.3 name
' differs from the long name then it is prepended to produce the required
' format:
'       8.3 Name|Long Name
'
' The "DestLongName" parameter has no path but is the "long" (non-8.3)
' name of the file.
'=========================================================================
on error resume next
dim SrcLongName : SrcLongName = oFS.GetFileName(CurrentFile)
dim File83
if   DestLongName = SrcLongName then
dim oFile : set oFile   = oFS.GetFile(CurrentFile)
VbsCheck "Could not find the file """ & CurrentFile & """"
File83 = ShortName(oFile, false)
if  File83 = "" then
File83 = Need83Name("$FILE$", DestLongName)
end if
else
File83 = Need83Name("$FILE$", DestLongName)
end if
if  File83 = DestLongName then
Get83PlusLongName = DestLongName
else
Get83PlusLongName = File83 & "|" & DestLongName
end if
VbsCheck "Get83PlusLongName() failed for the file """ & CurrentFile & """"
set oFile = Nothing
end function


'=========================================================================
function FileAttribs(BaseAttribs, CopyTheseAttribs)
'=========================================================================
on error resume next
FileAttribs = BaseAttribs
if  CopyTheseAttribs <> "" & CopyTheseAttribs <> 0 then
dim FromFileAttribs : FromFileAttribs = oInstaller.FileAttributes(CurrentFile)
VbsCheck "Could not get file attributes for """ & CurrentFile & """"
FromFileAttribs = FromFileAttribs and CopyTheseAttribs
FileAttribs = FileAttribs or FromFileAttribs
end if
if  (FileAttribs and 7) <> 0 then
VbsReturnMacro "FileHRS." & CurrentFileKey, FileAttribs and 7
end if
end function


'=========================================================================
sub ob_FileHash(AddtoHashTableYn)
'=========================================================================
on error resume next
dim oHash : set oHash = FileHash(CurrentFile)
if  err.number = 0 then
on error goto 0
if   AddtoHashTableYn = "Y" then
if   CurrentFileVersion = "" then

MmID = "@VBS0785"
TableNowMk "MsiFileHash"


MmID = "@VBS0786"
RowPrepare 6

MmID = "@VBS0787"
oRec.StringData(1) = CurrentFileKey
oRec.IntegerData(2) = 0
oRec.IntegerData(3) = oHash.IntegerData(1)
oRec.IntegerData(4) = oHash.IntegerData(2)
oRec.IntegerData(5) = oHash.IntegerData(3)
oRec.IntegerData(6) = oHash.IntegerData(4)
ValidateFIELD(1)
RowUpdate()


MmID = "@VBS0788"
TableNow ""

end if
end if
VbsReturnMacro "FileHash." & CurrentFileKey, PrettyHash(oHash)
set oHash = Nothing
end if
end sub


'=========================================================================
function FileHash(ByVal FileName)
'=========================================================================
on error resume next
set FileHash = oInstaller.FileHash(FileName, 0)
VbsCheck "Could not create a MD5 hash for """ & FileName & """" & VbCRLF & VbCRLF & "Note that Windows Installer 2.0+ is required to calculate MD5 codes."
end function


'=========================================================================
function BinaryMd5ForReport(BinId, BinaryFile)
'=========================================================================
on error resume next
dim oHash : set oHash = FileHash(BinaryFile)
if  err.number = 0 then
VbsReturnMacro "Binary." & BinId & ".MD5", PrettyHash(oHash)
end if
end function


'=========================================================================
function ForceDataBaseCodePage(ByVal CodePage)
'=========================================================================
on error resume next
dim TmpIdtFile : TmpIdtFile = "Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector\out\installscript.mm\Log\_ForceCodePage.IDT"
dim Stream     : set Stream  = oFS.CreateTextFile(TmpIdtFile, True)
VbsCheck "Could not create the database code page IDT file """ & TmpIdtFile & """"
Stream.WriteLine ""
Stream.WriteLine ""
Stream.WriteLine CodePage & vbTAB & "_ForceCodepage"
Stream.close
VbsCheck "Failind writing to the database code page IDT file """ & TmpIdtFile & """"
IdtImport(TmpIdtFile)
end function


'=========================================================================
function GuidMake(GuidName)
'=========================================================================
on error resume next
dim oGuidGen
err.clear()
set oGuidGen = MkObject("Scriptlet.Typelib")
GuidMake = oGuidGen.Guid
set oGuidGen = Nothing
VbsCheck "Generating a GUID"
GuidMake = ucase(left(GuidMake, 38))
if  GuidName <> "" then
VbsReturnGuid GuidName, GuidMake
end if
end function


'=========================================================================
function GuidGet(ByVal GuidName)
'=========================================================================
dim GuidFile : GuidFile = "Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector\installscript.GUIDS"
dim FileExists, Stream, Fileline, Bits, FoundIt, Left1
dim Name, LongestName
LongestName = len(GuidName)
on error resume next
FoundIt = false
FileExists = oFS.FileExists(GuidFile)
if  FileExists then
set Stream  = oFS.OpenTextFile(GuidFile, ForReading)
do  while Stream.AtEndOfStream <> true
Fileline = trim(Stream.ReadLine)
Left1 = Left(FileLine, 1)
if  Fileline = "" or Left1 = ";" then
nop
else
Bits  = split(FileLine, "=")
Name  = ucase(trim(Bits(0)))
if  len(Name) > LongestName then
LongestName = len(Name)
end if
if  ucase(GuidName) = Name then
GuidGet = trim(Bits(1))
FoundIt = True
exit do
end if
end if
loop
Stream.close
end if
if  not FoundIt then
GuidGet = GuidMake("")
err.clear()
set Stream  = oFS.OpenTextFile(GuidFile, ForAppending, True)
if  not FileExists then
Stream.WriteLine ";" & string(78, "+")
Stream.WriteLine "; AUTOMATICALLY GENERATED FILE - DO NOT EDIT"
Stream.WriteLine ";"
Stream.WriteLine "; Holds generated GUIDs, the values of which we MUST maintain."
Stream.WriteLine ";" & string(78, "+")
Stream.WriteLine ""
Stream.WriteLine ""
end if
Stream.WriteLine left(GuidName & string(LongestName, " "), LongestName) & " = " & GuidGet
Stream.close
VbsCheck("Updating the GUID file """ & GuidFile & """")
end if
VbsReturnGuid GuidName, GuidGet
end function


'=========================================================================
sub VbsReturnGuid(ByVal Name, ByVal Value)
'=========================================================================
VbsReturnMacro "GUID."         & Name, Value
VbsReturnMacro "GUID-Mangled." & Name, GuidMangle(Value)
end sub


'============================================================================
function ub_ReverseBits(ByVal GuidStr)
' This function mangles an MSI formatted GUID as performed by Windows
' Installer which uses this process in an attempt to hide the information.
'============================================================================
dim Lengths, i, Length, Fragment
ub_ReverseBits = ""
Lengths       = split("8,4,4,2,2,2,2,2,2,2,2", ",")
for i = 0 to ubound(Lengths)
Length = Lengths(i)
Fragment = left(GuidStr, Length)
GuidStr  = mid(GuidStr,  Length+1)
ub_ReverseBits = ub_ReverseBits & StrReverse(Fragment)
next
end function


'============================================================================
function GuidMangle(ByVal MsiGuid)
' This function mangles an MSI formatted GUID as performed by Windows
' Installer which uses this process in an attempt to hide the information.
'============================================================================
dim Tmp
Tmp = replace(MsiGuid, "{", "")
Tmp = replace(Tmp,     "}", "")
Tmp = replace(Tmp,     "-", "")
GuidMangle = ub_ReverseBits(Tmp)
end function


'============================================================================
function GuidMangleReverse(ByVal MangledGuid)
'============================================================================
dim Tmp : Tmp = ub_ReverseBits(MangledGuid)
dim Lengths, i, Length, Fragment
GuidMangleReverse = ""
Lengths           = split("8,4,4,4,12", ",")
for i = 0 to ubound(Lengths)
Length = Lengths(i)
Fragment = left(Tmp, Length)
Tmp      = mid(Tmp,  Length+1)
if   i <> 0 then
GuidMangleReverse = GuidMangleReverse & "-"
end if
GuidMangleReverse = GuidMangleReverse & Fragment
next
GuidMangleReverse = "{" & GuidMangleReverse & "}"
end function


'=========================================================================
sub DialogPreview(ByVal ReMatch)
'=========================================================================
on error resume next
'      dim oPreview : set oPreview = oMsi.EnableUIpreview()
if  oPreview is Nothing then                'Work around to Windows Installer bug
set oPreview = oMsi.EnableUIpreview()
end if
VbsCheck "Enabling Preview mode"
Dim oRec, oView : Set oView = oMSI.OpenView("SELECT `Property`,`Value` FROM `Property`")
VbsCheck "Opening property view for updating the preview objects properties"
oView.Execute
VbsCheck "Executing property view for updating the preview objects properties"
do
set oRec = oView.Fetch
VbsCheck "Fetching properties for the preview object"
if oRec is Nothing then exit do
oPreview.Property(oRec.StringData(1)) = oRec.StringData(2)
VbsCheck "Updating the preview objects properties"
loop
oView.close
VbsCheck "Closing a property view"
set oView = Nothing
if  ReMatch = "" then
ReMatch = ".*"
end if
dim oRE : set oRE = CreateRE(ReMatch)
set oView = oMSI.OpenView("SELECT `Dialog` FROM `Dialog`")
VbsCheck "Opening ""Dialog"" view for updating the preview objects properties"
oView.Execute
VbsCheck "Executing ""Dialog"" view for updating the preview objects properties"
dim DialogCnt    : DialogCnt    = 0
dim DialogTotCnt : DialogTotCnt = 0
dim ThisDlg
do
set oRec = oView.Fetch
VbsCheck "Fetching dialogs to preview"
if oRec is Nothing then exit do
ThisDlg      = oRec.StringData(1)
DialogTotCnt = DialogTotCnt + 1
dim Matches : Matches = TestRe(oRE, ThisDlg)
if  Matches then
DialogCnt = DialogCnt + 1
oPreview.ViewDialog(ThisDlg)
VbsCheck "Failed to view the dialog """ & ThisDlg & """"
dim Title, Text, MsgRc
Title = "Preview """ & ThisDlg & """ dialog."
Text  = Title & vbCRLF & vbCRLF
Text  = Text  & "Match #" & DialogCnt & " for the regular expression """ & oRE.Pattern & """" & vbCRLF
Text  = Text  & "At or after " & MmLL & vbCRLF & vbCRLF
Text  = Text  & "Please move the underlying dialog out of the way."
MsgRc = MsgBox(Text, vbInformation+vbOKCancel, Title)
if  MsgRc = vbCancel then
exit do
end if
end if
loop
oView.close
VbsCheck "Closing a Dialog view"
if  DialogCnt = 0 then
MsgBox "No dialogs (out of " & DialogTotCnt & ") found matching the regular expression """ & oRE.Pattern & """.", vbExclamation, "No such dialogs!"
end if
set oRE      = Nothing
set oRec     = Nothing
set oView    = Nothing
oPreview.ViewDialog ""
'set oPreview = Nothing
end sub


'=========================================================================
sub IdtExport1(ByVal TableName, ByVal Path)
'=========================================================================
on error resume next
if  Path = "" then Path = "Exported IDT"
CreateDir(Path)
dim FullPath
FullPath = oFS.GetAbsolutePathName(Path)
say "EXPORTING: " & TableName
err.clear()
oMSI.Export TableName, FullPath, TableName & ".IDT"
VbsCheck "Exporting MSI table """ & TableName & """"
end sub


'=========================================================================
function CreateRE(ByRef Filter)
'=========================================================================
on error resume next
set CreateRE = new RegExp
if err.number <> 0 then
error("Could not create a regular expression (""new RegExp""), windows clagged?" & vbCRLF & "The ""VBSCRIPT.DLL"" file probably needs registering... " & vbCRLF & "Reason: " & err.description)
end if
Filter = "^" & Filter & "$"
CreateRE.Pattern = Filter
if err.number <> 0 then
error("Could not set regular expression pattern """ & Filter & """ (probably invalid syntax). Reason: " & err.description)
end if
CreateRE.IgnoreCase = false
if err.number <> 0 then
error("Could not set regular expression to ignore case. Reason: " & err.description)
end if
end function


'=========================================================================
function TestRe(ByRef oRE, String2Test)      'Performs safe "oRE.test()"
'=========================================================================
on error resume next
TestRe = false                          'Not really required unless I stuff up...
TestRe = oRE.test(String2Test)          'This can fail (thanks MS, it knew this is "CreateRe"....)
if err.number <> 0 then
error("Could not test the regular expression pattern """ & oRE.pattern & """ (its syntax is probably invalid). Reason: " & err.description)
end if
end function


'=========================================================================
sub IdtExport(ByVal TableMask, ByVal Path)
'=========================================================================
on error resume next
dim oRE
if  TableMask = "" then TableMask = ".*"
say "EXPORTING TABLES MATCHING: " & TableMask
set oRE = CreateRE(TableMask)
dim oRecord
SqlOpenExec("SELECT `Name` FROM `_Tables`")
dim TableCnt : TableCnt = 0
dim TableName
do
set oRecord = SqlViewFetch()
if  oRecord is Nothing then exit do
TableName = oRecord.StringData(1)
if  TestRe(oRE, TableName) then
TableCnt  = TableCnt + 1
IdtExport1 TableName, Path
end if
loop
if  TableCnt = 0 then
Error("No tables exported for regular expression """ & TableMask & """")
end if
say "EXPORTED " & TableCnt & " table(s) matching: " &  TableMask
SqlViewClose()
set oRE = Nothing
end sub


'=========================================================================
sub IdtImport(ByVal FileName)
'=========================================================================
on error resume next
if  not oFS.FileExists(FileName) then
Error("The IDT file """ & FileName & """ does not exist!")
end if
dim FullFileName, Path, BaseName
FullFileName = oFS.GetAbsolutePathName(FileName)
Path         = oFS.GetParentFolderName(FullFileName)
BaseName     = oFS.GetFileName(FullFileName)
say "IMPORTING: " & BaseName
oMSI.Import Path, BaseName
VbsCheck "Importing the IDT file """ & Path & "\" & BaseName & """"
end sub


'=========================================================================
sub TableNow(TblName)
'=========================================================================
on error resume next
CurrentTable = TblName
if  TblName = "" then
CurrentTableFields = ""
else
if  oTableFlds.exists(TblName) then
CurrentTableFields = oTableFlds(TblName)
else
Error "Table Dictionary did not hold table information for """ & TblName & """" & vbCRLF & "Has the table been defined (with the ""TableDefinition"" command?"
end if
end if
end sub


'=========================================================================
sub TableNowMk(TblName)
'=========================================================================
on error resume next
TableNow(TblName)
if  not TableExists(TblName) then
TableCreate()
end if
end sub


'=========================================================================
sub ValidateStreamKeyLength(ByVal KeyNumberArray)
'
' From the Windows Installer manual
' ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
' Binary data is stored with an index name created by concatenating the table
' name and the values of the record's primary keys using a period delimiter.
' OLE limits stream names to 32 characters (31 + null terminator).
' Windows Installer uses a compression algorithm that can expand the limit
' to 62 characters depending upon the character.
' Note that double-byte characters count as 2.
'=========================================================================
dim Key : Key = CurrentTable
dim n
for n = 0 to ubound(KeyNumberArray)
Key = Key & "." & oRec.StringData(KeyNumberArray(n))
next
dim KeyLen   : KeyLen   = len(Key)
dim KeyLimit : KeyLimit = 62
if  KeyLen > KeyLimit then
say vbCRLF & vbCRLF & DumpRecord()
error "The underlying OLE container used to store binary data"                   & vbCRLF & _
"has has a key limit of " & KeyLimit & " characters."                      & vbCRLF & vbCRLF & _
"This was exceeded by " & KeyLen-KeyLimit & " character(s), the key was:"  & vbCRLF & _
"   " & Key
end if
end sub


'=========================================================================
sub RowsPrepare(ByVal WhereClause)
'=========================================================================
if  WhereClause <> "" then
WhereClause = " WHERE " & WhereClause
end if
on error resume next
SqlOpenExec "SELECT " & CurrentTableFields & " FROM " & CurrentTable & WhereClause
end sub


'=========================================================================
sub RowsChange_(ByVal How)
'=========================================================================
dim ModifyMode
on error resume next
select case How
case "UPDATE"
ModifyMode = MsiViewModifyUpdate
case "REPLACE"
ModifyMode = MsiViewModifyReplace
case "INSERT"
ModifyMode = MsiViewModifyInsert
end select
oView.Modify ModifyMode, oRec
VbsCheck "~ROW command - Adding record, method = " & How
set oRec  = Nothing
end sub


'=========================================================================
sub RowsInsert()
'=========================================================================
RowsChange_("INSERT")
end sub


'=========================================================================
sub RowsUpdate()
'=========================================================================
RowsChange_("UPDATE")
end sub


'=========================================================================
sub RowsReplace()
'=========================================================================
RowsChange_("REPLACE")
end sub


'=========================================================================
sub RowPrepare(ByVal NumberOfColumns)
'=========================================================================
on error resume next
SqlOpenExec "SELECT " & CurrentTableFields & " FROM " & CurrentTable
set oRec = oInstaller.CreateRecord(NumberOfColumns)
VbsCheck "ROW command - Creating a blank record with " & NumberOfColumns & " columns"
end sub


'=========================================================================
sub RowUpdate()
'=========================================================================
on error resume next
oView.Modify MsiViewModifyAssign, oRec
VbsCheck "~ROW command - Adding record"
set oRec  = Nothing
SqlViewClose()
end sub


'=========================================================================
function DumpRecord()
' Dumps record details, returns the complete text (doesn't display it)
'=========================================================================
on error resume next
dim Index, Txt, Int, FldNames, FldName
DumpRecord = Title("Contents of the Problem Record (table """ & CurrentTable & """)") & vbCRLF
Txt = oTableFlds(CurrentTable)
FldNames = split(Txt, ",")
for Index = 0 to ubound(FldNames)
FldNames(Index) = Replace(FldNames(Index), "`", "")
next
err.clear()
dim HaveColInfo, TypeName
dim MaxTypeWidth : MaxTypeWidth = 0
dim oColInfo : set oColInfo = oView.ColumnInfo(msiColumnInfoTypes)
if   err.number <> 0 then
HaveColInfo = false
'wscript.echo "CI====> " & err.description
else
HaveColInfo = true
for Index = 1 to oColInfo.FieldCount
TypeName = oColInfo.StringData(Index)
if len(TypeName) > MaxTypeWidth then
MaxTypeWidth = len(TypeName)
end if
next
end if
dim MaxFldNameWidth : MaxFldNameWidth = 0
for Index = 1 to oRec.FieldCount
FldName = FldNames(Index-1)
if len(FldName) > MaxFldNameWidth then
MaxFldNameWidth = len(FldName)
end if
next
dim ColValue
MaxTypeWidth  = MaxTypeWidth + 2          'plus brackets either side
for Index = 1 to oRec.FieldCount
dim IsNull : IsNull = false
FldName = FldNames(Index-1)
if  oRec.IsNull(Index) then
ColValue = "<<null string>>"
IsNull   = true
else
err.clear()
ColValue = oRec.StringData(Index)
if  err.number <> 0 then
ColValue = "<<Read Failed: Probably binary column>>"
else
if   (oRec.DataSize(Index) = 4) and (ColValue = "-2147483648") then
ColValue = "<<null integer>>"
IsNull   = true
end if
end if
end if
FldName = left(FldName & string(MaxFldNameWidth, " "), MaxFldNameWidth)
dim  TypeFormatted
if   not HaveColInfo then
TypeFormatted = ""
else
TypeName      = oColInfo.StringData(Index)
TypeFormatted = " " & right(string(MaxTypeWidth, " ") & "(" & TypeName & ")", MaxTypeWidth)
if  IsNull then
dim FirstLetter : FirstLetter = left(TypeName, 1)
if  FirstLetter = lcase(FirstLetter) then
ColValue = ColValue & "   (ERROR: nulls not allowed in this column)"
else
ColValue = ColValue & "   (OK: nulls allowed in this column)"
end if
end if
end if
'FldName = "COL #" & Index
DumpRecord = DumpRecord & FldName & TypeFormatted & " = " & ColValue & vbCRLF
next
end function


'=========================================================================
sub v_RowValidate(HowText, HowValue, ByVal ExclusionIndex)
'=========================================================================
on error resume next
oView.Modify HowValue, oRec
if  err.number <> 0 then
err.clear()
dim ErrCnt : ErrCnt = 0
dim ErrTxt : ErrTxt = ""
dim ColInfo, ErrNum, ErrCol, ErrReason, Want
do
ColInfo = oView.GetError()
if  ColInfo = "00" or ColInfo = "" then
exit do
end if
ErrNum = left(ColInfo,2)
ErrCol = mid(ColInfo, 3)
dim Exclusions : Exclusions = RowValidationExclusions(ExclusionIndex)
if  Exclusions = "" then
Want = true
else
dim RowSpec : RowSpec = "|"                & ErrNum & "|"
dim ColSpec : ColSpec = "|" & ErrCol & ":" & ErrNum & "|"
if      instr(Exclusions, RowSpec) <> 0 then
Want = false
elseif  instr(Exclusions, ColSpec) <> 0 then
Want = false
else
Want = true
end if
end if
if  Want then
if  oValidateErrTxt.exists(ErrNum) then
ErrReason = oValidateErrTxt(ErrNum)
else
ErrReason = "Error #" & ErrNum & " (""MSIDBERROR"" description unavailable)."
end if
ErrCnt = ErrCnt + 1
if  ErrCnt <> 1 then
ErrTxt = ErrTxt & vbCRLF
end if
ErrTxt = ErrTxt & "   * #" & ErrCnt & " """ & ErrCol & """: " & ErrReason
end if
loop
if  ErrCnt <> 0 then
ErrTxt = ErrTxt & vbCRLF & vbCRLF & DumpRecord()
if err.number <> 0 then
ErrTxt = ErrTxt & vbCRLF & vbCRLF & "MAKEMSI BUG?: Somethoing went wrong in processing errors and exclusions. Posible reason: 0x" & hex(err.number) & "- " & err.description
end if
dim HumanFriendly         : HumanFriendly         = RowValidationExclusions4Human(ExclusionIndex)
dim HowTextWithExclusions : HowTextWithExclusions = trim(HowText & " " & HumanFriendly)
Error("Windows Installer has reported that " & ErrCnt & " column(s) in a """ & CurrentTable & """ table record" & vbCRLF & "failed """ & HowTextWithExclusions & """ validation:" & vbCRLF & ErrTxt)
end if
end if
end sub


'=========================================================================
sub ValidateNew(ByVal ExclusionIndex)
'=========================================================================
v_RowValidate "NEW", MsiViewModifyValidateNew, ExclusionIndex
end sub


'=========================================================================
sub ValidateField(ByVal ExclusionIndex)
'=========================================================================
v_RowValidate "FIELD", MsiViewModifyValidateField, ExclusionIndex
end sub


'=========================================================================
sub ValidateFetch(ByVal ExclusionIndex)
'=========================================================================
v_RowValidate "FETCH", MsiViewModifyValidate, ExclusionIndex
end sub


'=========================================================================
sub TableCreate()
'=========================================================================
on error resume next
dim Sql
if  oTableCreateSql.exists(CurrentTable) then
Sql = oTableCreateSql(CurrentTable)
else
Error "Table Dictionary did not hold table information for """ & CurrentTable & """ (have you defined it?)"
end if
SqlExec(Sql)
end sub


'=========================================================================
sub TableDelete(ByVal TableName)
'=========================================================================
on error resume next
if   TableName = "" then
TableName = CurrentTable
end if
if  TableExists(TableName) then
SqlExec("DROP TABLE `" & TableName & "`")
end if
end sub


'=========================================================================
sub DeleteTableRows(ByVal Where)
'=========================================================================
on error resume next
dim SqlCmd : SqlCmd = "DELETE FROM `" & CurrentTable & "`"
if  Where  <> "" then
SqlCmd = SqlCmd & " WHERE " & where
end if
SqlExec(SqlCmd)
end sub


'=========================================================================
function LoadMergeModuleObject()
'=========================================================================
on error resume next
dim Acceptable : Acceptable = split("2.1;2", ";")
dim v
for v = 0 to ubound(Acceptable)
MergeObjectName = "Msm.Merge" & Acceptable(v)
set LoadMergeModuleObject = CreateObject(MergeObjectName)
if err.number = 0 then
exit function
end if
next
dim Msg : Msg = "We could not load ""MergeMod.dll"" (we tried versions """ & "2.1;2" & """)" & vbCRLF & vbCRLF
MergeObjectName = "Msm.Merge"
err.clear()
set LoadMergeModuleObject = CreateObject(MergeObjectName)
if err.number = 0 then
Msg = Msg & "We could load the older """ & LoadThis & """ automation object!" & vbCRLF & "There is probably an older ""MERGEMOD.DLL"" installed!" & vbCRLF & "Installing the latest version of ORCA may resolve this."
else
Msg = Msg & "Please install ""MERGEMOD.DLL"" (installing ORCA is easiest way)"  & vbCRLF & vbCRLF & "Reason 0x" & hex(err.number) & " - " & err.description
end if
error Msg
end function


'============================================================================
sub SetUpMergeModuleIgnores(ByVal IgnoreList)
'============================================================================
IgnoreList = replace(IgnoreList,  ";",  " ")
IgnoreList = replace(IgnoreList,  ",",  " ")
oMmIgnoreTheseErrors.RemoveAll()
dim lIgnoreList : lIgnoreList = split(IgnoreList, " ")
oMerge.Log ""
oMerge.Log "Configured to Ignore these Merge Errors"
oMerge.Log "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
dim nc_MmCnt, nc_MmTbl
for nc_MmCnt = lbound(lIgnoreList) to ubound(lIgnoreList)
nc_MmTbl = trim(lIgnoreList(nc_MmCnt))
if   nc_MmTbl <> "" then
oMmIgnoreTheseErrors.add nc_MmTbl, "0"
oMerge.Log nc_MmTbl
end if
next
end sub



'================================================================
sub MergeModMergeModulesNow(MergingEarly, LastFileSequenceNumber)
'================================================================
if   nc_AlreadyMerged then
exit sub
end if
nc_AlreadyMerged = true




'######################################################################
MmLL = "installscript.mm(54)"
MmLT = "Processing Merge Modules"
'######################################################################


MmID = "@VBS0789"

say ""
Say "No merge modules to be merged"
say ""

end sub


'=========================================================================
sub InitTableInfo()
'=========================================================================
TI "_MAKEMSI_FileSource", "File_,SourceFile,Date,Time", "CREATE TABLE `_MAKEMSI_FileSource` (`File_` CHARACTER(72) NOT NULL,`SourceFile` CHARACTER(255) NOT NULL,`Date` CHARACTER(10) NOT NULL,`Time` CHARACTER(8) NOT NULL PRIMARY KEY `File_`)"
TI "_MAKEMSI_Cabs", "Name,Data", "CREATE TABLE `_MAKEMSI_Cabs` (`Name` CHARACTER(48) NOT NULL,`Data` OBJECT PRIMARY KEY `Name`)"
TI "MsiFileHash", "File_,Options,HashPart1,HashPart2,HashPart3,HashPart4", "CREATE TABLE `MsiFileHash` (`File_` CHARACTER(72) NOT NULL,`Options` INTEGER NOT NULL,`HashPart1` LONG NOT NULL,`HashPart2` LONG NOT NULL,`HashPart3` LONG NOT NULL,`HashPart4` LONG NOT NULL PRIMARY KEY `File_`)"
TI "ActionText", "Action,Description,Template", "CREATE TABLE `ActionText` (`Action` CHARACTER(72) NOT NULL,`Description` LONGCHAR LOCALIZABLE,`Template` LONGCHAR LOCALIZABLE PRIMARY KEY `Action`)"
TI "AdminExecuteSequence", "Action,Condition,Sequence", "CREATE TABLE `AdminExecuteSequence` (`Action` CHARACTER(72) NOT NULL,`Condition` CHARACTER(255),`Sequence` INTEGER PRIMARY KEY `Action`)"
TI "AdminUISequence", "Action,Condition,Sequence", "CREATE TABLE `AdminUISequence` (`Action` CHARACTER(72) NOT NULL,`Condition` CHARACTER(255),`Sequence` INTEGER PRIMARY KEY `Action`)"
TI "AdvtExecuteSequence", "Action,Condition,Sequence", "CREATE TABLE `AdvtExecuteSequence` (`Action` CHARACTER(72) NOT NULL,`Condition` CHARACTER(255),`Sequence` INTEGER PRIMARY KEY `Action`)"
TI "AdvtUISequence", "Action,Condition,Sequence", "CREATE TABLE `AdvtUISequence` (`Action` CHARACTER(72) NOT NULL,`Condition` CHARACTER(255),`Sequence` INTEGER PRIMARY KEY `Action`)"
TI "AppSearch", "Property,Signature_", "CREATE TABLE `AppSearch` (`Property` CHARACTER(72) NOT NULL,`Signature_` CHARACTER(72) NOT NULL PRIMARY KEY `Property`,`Signature_`)"
TI "Binary", "Name,Data", "CREATE TABLE `Binary` (`Name` CHARACTER(72) NOT NULL,`Data` OBJECT NOT NULL PRIMARY KEY `Name`)"
TI "Component", "Component,ComponentId,Directory_,Attributes,Condition,KeyPath", "CREATE TABLE `Component` (`Component` CHARACTER(72) NOT NULL,`ComponentId` CHARACTER(38),`Directory_` CHARACTER(72) NOT NULL,`Attributes` INTEGER NOT NULL,`Condition` CHARACTER(255),`KeyPath` CHARACTER(72) PRIMARY KEY `Component`)"
TI "CreateFolder", "Directory_,Component_", "CREATE TABLE `CreateFolder` (`Directory_` CHARACTER(72) NOT NULL,`Component_` CHARACTER(72) NOT NULL PRIMARY KEY `Directory_`,`Component_`)"
TI "Directory", "Directory,Directory_Parent,DefaultDir", "CREATE TABLE `Directory` (`Directory` CHARACTER(72) NOT NULL,`Directory_Parent` CHARACTER(72),`DefaultDir` CHARACTER(255) NOT NULL LOCALIZABLE PRIMARY KEY `Directory`)"
TI "DrLocator", "Signature_,Parent,Path,Depth", "CREATE TABLE `DrLocator` (`Signature_` CHARACTER(72) NOT NULL,`Parent` CHARACTER(72),`Path` CHARACTER(255),`Depth` INTEGER PRIMARY KEY `Signature_`,`Parent`,`Path`)"
TI "Environment", "Environment,Name,Value,Component_", "CREATE TABLE `Environment` (`Environment` CHARACTER(72) NOT NULL,`Name` CHARACTER(255) NOT NULL LOCALIZABLE,`Value` CHARACTER(255) LOCALIZABLE,`Component_` CHARACTER(72) NOT NULL PRIMARY KEY `Environment`)"
TI "Error", "Error,Message", "CREATE TABLE `Error` (`Error` INTEGER NOT NULL,`Message` LONGCHAR LOCALIZABLE PRIMARY KEY `Error`)"
TI "Feature", "Feature,Feature_Parent,Title,Description,Display,Level,Directory_,Attributes", "CREATE TABLE `Feature` (`Feature` CHARACTER(38) NOT NULL,`Feature_Parent` CHARACTER(38),`Title` CHARACTER(64) LOCALIZABLE,`Description` CHARACTER(255) LOCALIZABLE,`Display` INTEGER,`Level` INTEGER NOT NULL,`Directory_` CHARACTER(72),`Attributes` INTEGER NOT NULL PRIMARY KEY `Feature`)"
TI "FeatureComponents", "Feature_,Component_", "CREATE TABLE `FeatureComponents` (`Feature_` CHARACTER(38) NOT NULL,`Component_` CHARACTER(72) NOT NULL PRIMARY KEY `Feature_`,`Component_`)"
TI "File", "File,Component_,FileName,FileSize,Version,Language,Attributes,Sequence", "CREATE TABLE `File` (`File` CHARACTER(72) NOT NULL,`Component_` CHARACTER(72) NOT NULL,`FileName` CHARACTER(255) NOT NULL LOCALIZABLE,`FileSize` LONG NOT NULL,`Version` CHARACTER(72),`Language` CHARACTER(20),`Attributes` INTEGER,`Sequence` INTEGER NOT NULL PRIMARY KEY `File`)"
TI "Icon", "Name,Data", "CREATE TABLE `Icon` (`Name` CHARACTER(72) NOT NULL,`Data` OBJECT NOT NULL PRIMARY KEY `Name`)"
TI "IniFile", "IniFile,FileName,DirProperty,Section,Key,Value,Action,Component_", "CREATE TABLE `IniFile` (`IniFile` CHARACTER(72) NOT NULL,`FileName` CHARACTER(255) NOT NULL LOCALIZABLE,`DirProperty` CHARACTER(72),`Section` CHARACTER(96) NOT NULL LOCALIZABLE,`Key` CHARACTER(128) NOT NULL LOCALIZABLE,`Value` CHARACTER(255) NOT NULL LOCALIZABLE,`Action` INTEGER NOT NULL,`Component_` CHARACTER(72) NOT NULL PRIMARY KEY `IniFile`)"
TI "InstallExecuteSequence", "Action,Condition,Sequence", "CREATE TABLE `InstallExecuteSequence` (`Action` CHARACTER(72) NOT NULL,`Condition` CHARACTER(255),`Sequence` INTEGER PRIMARY KEY `Action`)"
TI "InstallUISequence", "Action,Condition,Sequence", "CREATE TABLE `InstallUISequence` (`Action` CHARACTER(72) NOT NULL,`Condition` CHARACTER(255),`Sequence` INTEGER PRIMARY KEY `Action`)"
TI "LaunchCondition", "Condition,Description", "CREATE TABLE `LaunchCondition` (`Condition` CHARACTER(255) NOT NULL,`Description` CHARACTER(255) NOT NULL LOCALIZABLE PRIMARY KEY `Condition`)"
TI "LockPermissions", "LockObject,Table,Domain,User,Permission", "CREATE TABLE `LockPermissions` (`LockObject` CHARACTER(72) NOT NULL,`Table` CHARACTER(32) NOT NULL,`Domain` CHARACTER(255),`User` CHARACTER(255) NOT NULL,`Permission` LONG NOT NULL PRIMARY KEY `LockObject`,`Table`,`Domain`,`User`)"
TI "Media", "DiskId,LastSequence,DiskPrompt,Cabinet,VolumeLabel,Source", "CREATE TABLE `Media` (`DiskId` INTEGER NOT NULL,`LastSequence` INTEGER NOT NULL,`DiskPrompt` CHARACTER(64) LOCALIZABLE,`Cabinet` CHARACTER(255),`VolumeLabel` CHARACTER(32),`Source` CHARACTER(32) PRIMARY KEY `DiskId`)"
TI "Property", "Property,Value", "CREATE TABLE `Property` (`Property` CHARACTER(72) NOT NULL,`Value` LONGCHAR NOT NULL LOCALIZABLE PRIMARY KEY `Property`)"
TI "Registry", "Registry,Root,Key,Name,Value,Component_", "CREATE TABLE `Registry` (`Registry` CHARACTER(72) NOT NULL,`Root` INTEGER NOT NULL,`Key` CHARACTER(255) NOT NULL LOCALIZABLE,`Name` CHARACTER(255) LOCALIZABLE,`Value` LONGCHAR LOCALIZABLE,`Component_` CHARACTER(72) NOT NULL PRIMARY KEY `Registry`)"
TI "RegLocator", "Signature_,Root,Key,Name,Type", "CREATE TABLE `RegLocator` (`Signature_` CHARACTER(72) NOT NULL,`Root` INTEGER NOT NULL,`Key` CHARACTER(255) NOT NULL,`Name` CHARACTER(255),`Type` INTEGER PRIMARY KEY `Signature_`)"
TI "SelfReg", "File_,Cost", "CREATE TABLE `SelfReg` (`File_` CHARACTER(72) NOT NULL,`Cost` INTEGER PRIMARY KEY `File_`)"
TI "ServiceControl", "ServiceControl,Name,Event,Arguments,Wait,Component_", "CREATE TABLE `ServiceControl` (`ServiceControl` CHARACTER(72) NOT NULL,`Name` CHARACTER(255) NOT NULL LOCALIZABLE,`Event` INTEGER NOT NULL,`Arguments` CHARACTER(255) LOCALIZABLE,`Wait` INTEGER,`Component_` CHARACTER(72) NOT NULL PRIMARY KEY `ServiceControl`)"
TI "ServiceInstall", "ServiceInstall,Name,DisplayName,ServiceType,StartType,ErrorControl,LoadOrderGroup,Dependencies,StartName,Password,Arguments,Component_,Description", "CREATE TABLE `ServiceInstall` (`ServiceInstall` CHARACTER(72) NOT NULL,`Name` CHARACTER(255) NOT NULL,`DisplayName` CHARACTER(255) LOCALIZABLE,`ServiceType` LONG NOT NULL,`StartType` LONG NOT NULL,`ErrorControl` LONG NOT NULL,`LoadOrderGroup` CHARACTER(255),`Dependencies` CHARACTER(255),`StartName` CHARACTER(255),`Password` CHARACTER(255),`Arguments` CHARACTER(255),`Component_` CHARACTER(72) NOT NULL,`Description` CHARACTER(255) LOCALIZABLE PRIMARY KEY `ServiceInstall`)"
TI "Shortcut", "Shortcut,Directory_,Name,Component_,Target,Arguments,Description,Hotkey,Icon_,IconIndex,ShowCmd,WkDir,DisplayResourceDLL,DisplayResourceId,DescriptionResourceDLL,DescriptionResourceId", "CREATE TABLE `Shortcut` (`Shortcut` CHARACTER(72) NOT NULL,`Directory_` CHARACTER(72) NOT NULL,`Name` CHARACTER(128) NOT NULL LOCALIZABLE,`Component_` CHARACTER(72) NOT NULL,`Target` CHARACTER(72) NOT NULL,`Arguments` CHARACTER(255),`Description` CHARACTER(255) LOCALIZABLE,`Hotkey` INTEGER,`Icon_` CHARACTER(72),`IconIndex` INTEGER,`ShowCmd` INTEGER,`WkDir` CHARACTER(72),`DisplayResourceDLL` CHARACTER(100),`DisplayResourceId` LONG,`DescriptionResourceDLL` CHARACTER(100),`DescriptionResourceId` LONG PRIMARY KEY `Shortcut`)"
TI "Signature", "Signature,FileName,MinVersion,MaxVersion,MinSize,MaxSize,MinDate,MaxDate,Languages", "CREATE TABLE `Signature` (`Signature` CHARACTER(72) NOT NULL,`FileName` CHARACTER(255) NOT NULL,`MinVersion` CHARACTER(20),`MaxVersion` CHARACTER(20),`MinSize` LONG,`MaxSize` LONG,`MinDate` LONG,`MaxDate` LONG,`Languages` CHARACTER(255) PRIMARY KEY `Signature`)"
TI "Upgrade", "UpgradeCode,VersionMin,VersionMax,Language,Attributes,Remove,ActionProperty", "CREATE TABLE `Upgrade` (`UpgradeCode` CHARACTER(38) NOT NULL,`VersionMin` CHARACTER(20),`VersionMax` CHARACTER(20),`Language` CHARACTER(255),`Attributes` LONG NOT NULL,`Remove` CHARACTER(255),`ActionProperty` CHARACTER(72) NOT NULL PRIMARY KEY `UpgradeCode`,`VersionMin`,`VersionMax`,`Language`,`Attributes`)"
TI "_InstallValidate", "Action,SectionFlag,Description", "CREATE TABLE `_InstallValidate` (`Action` CHARACTER(50) NOT NULL,`SectionFlag` INTEGER NOT NULL,`Description` CHARACTER(255) PRIMARY KEY `Action`)"
TI "_Required", "Table,Value,KeyCount,Description", "CREATE TABLE `_Required` (`Table` CHARACTER(50) NOT NULL,`Value` CHARACTER(255) NOT NULL,`KeyCount` INTEGER NOT NULL,`Description` CHARACTER(255) PRIMARY KEY `Table`,`Value`)"
TI "_Sequence", "Action,Dependent,After,Optional", "CREATE TABLE `_Sequence` (`Action` CHARACTER(50) NOT NULL,`Dependent` CHARACTER(50) NOT NULL,`After` INTEGER NOT NULL,`Optional` INTEGER NOT NULL PRIMARY KEY `Action`,`Dependent`)"
TI "_Streams", "Name,Data", "CREATE TABLE `_Streams` (`Name` CHARACTER(62) NOT NULL,`Data` OBJECT PRIMARY KEY `Name`)"
TI "_Storages", "Name,Data", "CREATE TABLE `_Storages` (`Name` CHARACTER(62) NOT NULL,`Data` OBJECT PRIMARY KEY `Name`)"
TI "_Validation", "Table,Column,Nullable,MinValue,MaxValue,KeyTable,KeyColumn,Category,Set,Description", "CREATE TABLE `_Validation` (`Table` CHARACTER(32) NOT NULL,`Column` CHARACTER(32) NOT NULL,`Nullable` CHARACTER(4) NOT NULL,`MinValue` LONG,`MaxValue` LONG,`KeyTable` CHARACTER(255),`KeyColumn` INTEGER,`Category` CHARACTER(32),`Set` CHARACTER(255),`Description` CHARACTER(255) PRIMARY KEY `Table`,`Column`)"
TI "ModuleAdminExecuteSequence", "Action,Sequence,BaseAction,After,Condition", "CREATE TABLE `ModuleAdminExecuteSequence` (`Action` CHARACTER(64) NOT NULL,`Sequence` INTEGER,`BaseAction` CHARACTER(64),`After` INTEGER,`Condition` CHARACTER(255) PRIMARY KEY `Action`)"
TI "ModuleAdminUISequence", "Action,Sequence,BaseAction,After,Condition", "CREATE TABLE `ModuleAdminUISequence` (`Action` CHARACTER(64) NOT NULL,`Sequence` INTEGER,`BaseAction` CHARACTER(64),`After` INTEGER,`Condition` CHARACTER(255) PRIMARY KEY `Action`)"
TI "ModuleAdvtExecuteSequence", "Action,Sequence,BaseAction,After,Condition", "CREATE TABLE `ModuleAdvtExecuteSequence` (`Action` CHARACTER(64) NOT NULL,`Sequence` INTEGER,`BaseAction` CHARACTER(64),`After` INTEGER,`Condition` CHARACTER(255) PRIMARY KEY `Action`)"
TI "ModuleAdvtUISequence", "Action,Sequence,BaseAction,After,Condition", "CREATE TABLE `ModuleAdvtUISequence` (`Action` CHARACTER(64) NOT NULL,`Sequence` INTEGER,`BaseAction` CHARACTER(64),`After` INTEGER,`Condition` CHARACTER(255) PRIMARY KEY `Action`)"
TI "ModuleInstallExecuteSequence", "Action,Sequence,BaseAction,After,Condition", "CREATE TABLE `ModuleInstallExecuteSequence` (`Action` CHARACTER(64) NOT NULL,`Sequence` INTEGER,`BaseAction` CHARACTER(64),`After` INTEGER,`Condition` CHARACTER(255) PRIMARY KEY `Action`)"
TI "ModuleInstallUISequence", "Action,Sequence,BaseAction,After,Condition", "CREATE TABLE `ModuleInstallUISequence` (`Action` CHARACTER(64) NOT NULL,`Sequence` INTEGER,`BaseAction` CHARACTER(64),`After` INTEGER,`Condition` CHARACTER(255) PRIMARY KEY `Action`)"
TI "ModuleComponents", "Component,ModuleID,Language", "CREATE TABLE `ModuleComponents` (`Component` CHARACTER(72) NOT NULL,`ModuleID` CHARACTER(72) NOT NULL,`Language` INTEGER NOT NULL PRIMARY KEY `Component`,`ModuleID`,`Language`)"
TI "ModuleDependency", "ModuleID,ModuleLanguage,RequiredID,RequiredLanguage,RequiredVersion", "CREATE TABLE `ModuleDependency` (`ModuleID` CHARACTER(72) NOT NULL,`ModuleLanguage` INTEGER NOT NULL,`RequiredID` CHARACTER(72) NOT NULL,`RequiredLanguage` INTEGER NOT NULL,`RequiredVersion` CHARACTER(32) PRIMARY KEY `ModuleID`,`ModuleLanguage`,`RequiredID`,`RequiredLanguage`)"
TI "ModuleExclusion", "ModuleID,ModuleLanguage,ExcludedID,ExcludedLanguage,ExcludedMinVersion,ExcludedMaxVersion", "CREATE TABLE `ModuleExclusion` (`ModuleID` CHARACTER(72) NOT NULL,`ModuleLanguage` INTEGER NOT NULL,`ExcludedID` CHARACTER(72) NOT NULL,`ExcludedLanguage` INTEGER NOT NULL,`ExcludedMinVersion` CHARACTER(32),`ExcludedMaxVersion` CHARACTER(32) PRIMARY KEY `ModuleID`,`ModuleLanguage`,`ExcludedID`,`ExcludedLanguage`)"
TI "ModuleIgnoreTable", "Table", "CREATE TABLE `ModuleIgnoreTable` (`Table` CHARACTER(72) NOT NULL PRIMARY KEY `Table`)"
TI "ModuleSignature", "ModuleID,Language,Version", "CREATE TABLE `ModuleSignature` (`ModuleID` CHARACTER(72) NOT NULL,`Language` INTEGER NOT NULL,`Version` CHARACTER(32) NOT NULL PRIMARY KEY `ModuleID`,`Language`)"
TI "AppId", "AppId,RemoteServerName,LocalService,ServiceParameters,DllSurrogate,ActivateAtStorage,RunAsInteractiveUser", "CREATE TABLE `AppId` (`AppId` CHARACTER(38) NOT NULL,`RemoteServerName` CHARACTER(255),`LocalService` CHARACTER(255),`ServiceParameters` CHARACTER(255),`DllSurrogate` CHARACTER(255),`ActivateAtStorage` INTEGER,`RunAsInteractiveUser` INTEGER PRIMARY KEY `AppId`)"
TI "BBControl", "Billboard_,BBControl,Type,X,Y,Width,Height,Attributes,Text", "CREATE TABLE `BBControl` (`Billboard_` CHARACTER(50) NOT NULL,`BBControl` CHARACTER(50) NOT NULL,`Type` CHARACTER(50) NOT NULL,`X` INTEGER NOT NULL,`Y` INTEGER NOT NULL,`Width` INTEGER NOT NULL,`Height` INTEGER NOT NULL,`Attributes` LONG,`Text` CHARACTER(50) LOCALIZABLE PRIMARY KEY `Billboard_`,`BBControl`)"
TI "Billboard", "Billboard,Feature_,Action,Ordering", "CREATE TABLE `Billboard` (`Billboard` CHARACTER(50) NOT NULL,`Feature_` CHARACTER(38) NOT NULL,`Action` CHARACTER(50),`Ordering` INTEGER PRIMARY KEY `Billboard`)"
TI "BindImage", "File_,Path", "CREATE TABLE `BindImage` (`File_` CHARACTER(72) NOT NULL,`Path` CHARACTER(255) PRIMARY KEY `File_`)"
TI "CCPSearch", "Signature_", "CREATE TABLE `CCPSearch` (`Signature_` CHARACTER(72) NOT NULL PRIMARY KEY `Signature_`)"
TI "CheckBox", "Property,Value", "CREATE TABLE `CheckBox` (`Property` CHARACTER(72) NOT NULL,`Value` CHARACTER(64) PRIMARY KEY `Property`)"
TI "Class", "CLSID,Context,Component_,ProgId_Default,Description,AppId_,FileTypeMask,Icon_,IconIndex,DefInprocHandler,Argument,Feature_,Attributes", "CREATE TABLE `Class` (`CLSID` CHARACTER(38) NOT NULL,`Context` CHARACTER(32) NOT NULL,`Component_` CHARACTER(72) NOT NULL,`ProgId_Default` CHARACTER(255),`Description` CHARACTER(255) LOCALIZABLE,`AppId_` CHARACTER(38),`FileTypeMask` CHARACTER(255),`Icon_` CHARACTER(72),`IconIndex` INTEGER,`DefInprocHandler` CHARACTER(32),`Argument` CHARACTER(255),`Feature_` CHARACTER(38) NOT NULL,`Attributes` INTEGER PRIMARY KEY `CLSID`,`Context`,`Component_`)"
TI "ComboBox", "Property,Order,Value,Text", "CREATE TABLE `ComboBox` (`Property` CHARACTER(72) NOT NULL,`Order` INTEGER NOT NULL,`Value` CHARACTER(64) NOT NULL,`Text` CHARACTER(64) LOCALIZABLE PRIMARY KEY `Property`,`Order`)"
TI "CompLocator", "Signature_,ComponentId,Type", "CREATE TABLE `CompLocator` (`Signature_` CHARACTER(72) NOT NULL,`ComponentId` CHARACTER(38) NOT NULL,`Type` INTEGER PRIMARY KEY `Signature_`)"
TI "Complus", "Component_,ExpType", "CREATE TABLE `Complus` (`Component_` CHARACTER(72) NOT NULL,`ExpType` INTEGER PRIMARY KEY `Component_`)"
TI "Condition", "Feature_,Level,Condition", "CREATE TABLE `Condition` (`Feature_` CHARACTER(38) NOT NULL,`Level` INTEGER NOT NULL,`Condition` CHARACTER(255) PRIMARY KEY `Feature_`,`Level`)"
TI "Control", "Dialog_,Control,Type,X,Y,Width,Height,Attributes,Property,Text,Control_Next,Help", "CREATE TABLE `Control` (`Dialog_` CHARACTER(72) NOT NULL,`Control` CHARACTER(50) NOT NULL,`Type` CHARACTER(20) NOT NULL,`X` INTEGER NOT NULL,`Y` INTEGER NOT NULL,`Width` INTEGER NOT NULL,`Height` INTEGER NOT NULL,`Attributes` LONG,`Property` CHARACTER(50),`Text` LONGCHAR LOCALIZABLE,`Control_Next` CHARACTER(50),`Help` CHARACTER(50) LOCALIZABLE PRIMARY KEY `Dialog_`,`Control`)"
TI "ControlCondition", "Dialog_,Control_,Action,Condition", "CREATE TABLE `ControlCondition` (`Dialog_` CHARACTER(72) NOT NULL,`Control_` CHARACTER(50) NOT NULL,`Action` CHARACTER(50) NOT NULL,`Condition` CHARACTER(255) NOT NULL PRIMARY KEY `Dialog_`,`Control_`,`Action`,`Condition`)"
TI "ControlEvent", "Dialog_,Control_,Event,Argument,Condition,Ordering", "CREATE TABLE `ControlEvent` (`Dialog_` CHARACTER(72) NOT NULL,`Control_` CHARACTER(50) NOT NULL,`Event` CHARACTER(50) NOT NULL,`Argument` CHARACTER(255) NOT NULL,`Condition` CHARACTER(255),`Ordering` INTEGER PRIMARY KEY `Dialog_`,`Control_`,`Event`,`Argument`,`Condition`)"
TI "CustomAction", "Action,Type,Source,Target,ExtendedType", "CREATE TABLE `CustomAction` (`Action` CHARACTER(72) NOT NULL,`Type` INTEGER NOT NULL,`Source` CHARACTER(64),`Target` CHARACTER(255),`ExtendedType` LONG PRIMARY KEY `Action`)"
TI "Dialog", "Dialog,HCentering,VCentering,Width,Height,Attributes,Title,Control_First,Control_Default,Control_Cancel", "CREATE TABLE `Dialog` (`Dialog` CHARACTER(72) NOT NULL,`HCentering` INTEGER NOT NULL,`VCentering` INTEGER NOT NULL,`Width` INTEGER NOT NULL,`Height` INTEGER NOT NULL,`Attributes` LONG,`Title` CHARACTER(128) LOCALIZABLE,`Control_First` CHARACTER(50) NOT NULL,`Control_Default` CHARACTER(50),`Control_Cancel` CHARACTER(50) PRIMARY KEY `Dialog`)"
TI "DuplicateFile", "FileKey,Component_,File_,DestName,DestFolder", "CREATE TABLE `DuplicateFile` (`FileKey` CHARACTER(72) NOT NULL,`Component_` CHARACTER(72) NOT NULL,`File_` CHARACTER(72) NOT NULL,`DestName` CHARACTER(255) LOCALIZABLE,`DestFolder` CHARACTER(32) PRIMARY KEY `FileKey`)"
TI "EventMapping", "Dialog_,Control_,Event,Attribute", "CREATE TABLE `EventMapping` (`Dialog_` CHARACTER(72) NOT NULL,`Control_` CHARACTER(50) NOT NULL,`Event` CHARACTER(50) NOT NULL,`Attribute` CHARACTER(50) NOT NULL PRIMARY KEY `Dialog_`,`Control_`,`Event`)"
TI "Extension", "Extension,Component_,ProgId_,MIME_,Feature_", "CREATE TABLE `Extension` (`Extension` CHARACTER(255) NOT NULL,`Component_` CHARACTER(72) NOT NULL,`ProgId_` CHARACTER(255),`MIME_` CHARACTER(64),`Feature_` CHARACTER(38) NOT NULL PRIMARY KEY `Extension`,`Component_`)"
TI "FileSFPCatalog", "File_,SFPCatalog_", "CREATE TABLE `FileSFPCatalog` (`File_` CHARACTER(72) NOT NULL,`SFPCatalog_` CHARACTER(255) NOT NULL PRIMARY KEY `File_`,`SFPCatalog_`)"
TI "Font", "File_,FontTitle", "CREATE TABLE `Font` (`File_` CHARACTER(72) NOT NULL,`FontTitle` CHARACTER(128) PRIMARY KEY `File_`)"
TI "IniLocator", "Signature_,FileName,Section,Key,Field,Type", "CREATE TABLE `IniLocator` (`Signature_` CHARACTER(72) NOT NULL,`FileName` CHARACTER(255) NOT NULL,`Section` CHARACTER(96) NOT NULL,`Key` CHARACTER(128) NOT NULL,`Field` INTEGER,`Type` INTEGER PRIMARY KEY `Signature_`)"
TI "IsolatedComponent", "Component_Shared,Component_Application", "CREATE TABLE `IsolatedComponent` (`Component_Shared` CHARACTER(72) NOT NULL,`Component_Application` CHARACTER(72) NOT NULL PRIMARY KEY `Component_Shared`,`Component_Application`)"
TI "ListBox", "Property,Order,Value,Text", "CREATE TABLE `ListBox` (`Property` CHARACTER(72) NOT NULL,`Order` INTEGER NOT NULL,`Value` CHARACTER(64) NOT NULL,`Text` CHARACTER(64) LOCALIZABLE PRIMARY KEY `Property`,`Order`)"
TI "ListView", "Property,Order,Value,Text,Binary_", "CREATE TABLE `ListView` (`Property` CHARACTER(72) NOT NULL,`Order` INTEGER NOT NULL,`Value` CHARACTER(64) NOT NULL,`Text` CHARACTER(64) LOCALIZABLE,`Binary_` CHARACTER(72) PRIMARY KEY `Property`,`Order`)"
TI "MIME", "ContentType,Extension_,CLSID", "CREATE TABLE `MIME` (`ContentType` CHARACTER(64) NOT NULL,`Extension_` CHARACTER(255) NOT NULL,`CLSID` CHARACTER(38) PRIMARY KEY `ContentType`)"
TI "MoveFile", "FileKey,Component_,SourceName,DestName,SourceFolder,DestFolder,Options", "CREATE TABLE `MoveFile` (`FileKey` CHARACTER(72) NOT NULL,`Component_` CHARACTER(72) NOT NULL,`SourceName` CHARACTER(255) LOCALIZABLE,`DestName` CHARACTER(255) LOCALIZABLE,`SourceFolder` CHARACTER(72),`DestFolder` CHARACTER(72) NOT NULL,`Options` INTEGER NOT NULL PRIMARY KEY `FileKey`)"
TI "MsiAssembly", "Component_,Feature_,File_Manifest,File_Application,Attributes", "CREATE TABLE `MsiAssembly` (`Component_` CHARACTER(72) NOT NULL,`Feature_` CHARACTER(38) NOT NULL,`File_Manifest` CHARACTER(72),`File_Application` CHARACTER(72),`Attributes` INTEGER PRIMARY KEY `Component_`)"
TI "MsiAssemblyName", "Component_,Name,Value", "CREATE TABLE `MsiAssemblyName` (`Component_` CHARACTER(72) NOT NULL,`Name` CHARACTER(255) NOT NULL,`Value` CHARACTER(255) NOT NULL PRIMARY KEY `Component_`,`Name`)"
TI "MsiDigitalCertificate", "DigitalCertificate,CertData", "CREATE TABLE `MsiDigitalCertificate` (`DigitalCertificate` CHARACTER(72) NOT NULL,`CertData` OBJECT NOT NULL PRIMARY KEY `DigitalCertificate`)"
TI "MsiDigitalSignature", "Table,SignObject,DigitalCertificate_,Hash", "CREATE TABLE `MsiDigitalSignature` (`Table` CHARACTER(32) NOT NULL,`SignObject` CHARACTER(72) NOT NULL,`DigitalCertificate_` CHARACTER(72) NOT NULL,`Hash` OBJECT PRIMARY KEY `Table`,`SignObject`)"
TI "MsiPatchHeaders", "StreamRef,Header", "CREATE TABLE `MsiPatchHeaders` (`StreamRef` CHARACTER(38) NOT NULL,`Header` OBJECT NOT NULL PRIMARY KEY `StreamRef`)"
TI "ODBCAttribute", "Driver_,Attribute,Value", "CREATE TABLE `ODBCAttribute` (`Driver_` CHARACTER(72) NOT NULL,`Attribute` CHARACTER(40) NOT NULL,`Value` CHARACTER(255) LOCALIZABLE PRIMARY KEY `Driver_`,`Attribute`)"
TI "ODBCDataSource", "DataSource,Component_,Description,DriverDescription,Registration", "CREATE TABLE `ODBCDataSource` (`DataSource` CHARACTER(72) NOT NULL,`Component_` CHARACTER(72) NOT NULL,`Description` CHARACTER(255) NOT NULL,`DriverDescription` CHARACTER(255) NOT NULL,`Registration` INTEGER NOT NULL PRIMARY KEY `DataSource`)"
TI "ODBCDriver", "Driver,Component_,Description,File_,File_Setup", "CREATE TABLE `ODBCDriver` (`Driver` CHARACTER(72) NOT NULL,`Component_` CHARACTER(72) NOT NULL,`Description` CHARACTER(255) NOT NULL,`File_` CHARACTER(72) NOT NULL,`File_Setup` CHARACTER(72) PRIMARY KEY `Driver`)"
TI "ODBCSourceAttribute", "DataSource_,Attribute,Value", "CREATE TABLE `ODBCSourceAttribute` (`DataSource_` CHARACTER(72) NOT NULL,`Attribute` CHARACTER(32) NOT NULL,`Value` CHARACTER(255) LOCALIZABLE PRIMARY KEY `DataSource_`,`Attribute`)"
TI "ODBCTranslator", "Translator,Component_,Description,File_,File_Setup", "CREATE TABLE `ODBCTranslator` (`Translator` CHARACTER(72) NOT NULL,`Component_` CHARACTER(72) NOT NULL,`Description` CHARACTER(255) NOT NULL,`File_` CHARACTER(72) NOT NULL,`File_Setup` CHARACTER(72) PRIMARY KEY `Translator`)"
TI "Patch", "File_,Sequence,PatchSize,Attributes,Header,StreamRef_", "CREATE TABLE `Patch` (`File_` CHARACTER(72) NOT NULL,`Sequence` INTEGER NOT NULL,`PatchSize` LONG NOT NULL,`Attributes` INTEGER NOT NULL,`Header` OBJECT NOT NULL,`StreamRef_` CHARACTER(38) PRIMARY KEY `File_`,`Sequence`)"
TI "PatchPackage", "PatchId,Media_", "CREATE TABLE `PatchPackage` (`PatchId` CHARACTER(38) NOT NULL,`Media_` INTEGER NOT NULL PRIMARY KEY `PatchId`)"
TI "ProgId", "ProgId,ProgId_Parent,Class_,Description,Icon_,IconIndex", "CREATE TABLE `ProgId` (`ProgId` CHARACTER(255) NOT NULL,`ProgId_Parent` CHARACTER(255),`Class_` CHARACTER(38),`Description` CHARACTER(255) LOCALIZABLE,`Icon_` CHARACTER(72),`IconIndex` INTEGER PRIMARY KEY `ProgId`)"
TI "PublishComponent", "ComponentId,Qualifier,Component_,AppData,Feature_", "CREATE TABLE `PublishComponent` (`ComponentId` CHARACTER(38) NOT NULL,`Qualifier` CHARACTER(255) NOT NULL,`Component_` CHARACTER(72) NOT NULL,`AppData` CHARACTER(255) LOCALIZABLE,`Feature_` CHARACTER(38) NOT NULL PRIMARY KEY `ComponentId`,`Qualifier`,`Component_`)"
TI "RadioButton", "Property,Order,Value,X,Y,Width,Height,Text,Help", "CREATE TABLE `RadioButton` (`Property` CHARACTER(72) NOT NULL,`Order` INTEGER NOT NULL,`Value` CHARACTER(64) NOT NULL,`X` INTEGER NOT NULL,`Y` INTEGER NOT NULL,`Width` INTEGER NOT NULL,`Height` INTEGER NOT NULL,`Text` CHARACTER(64) LOCALIZABLE,`Help` CHARACTER(50) LOCALIZABLE PRIMARY KEY `Property`,`Order`)"
TI "RemoveFile", "FileKey,Component_,FileName,DirProperty,InstallMode", "CREATE TABLE `RemoveFile` (`FileKey` CHARACTER(72) NOT NULL,`Component_` CHARACTER(72) NOT NULL,`FileName` CHARACTER(255) LOCALIZABLE,`DirProperty` CHARACTER(72) NOT NULL,`InstallMode` INTEGER NOT NULL PRIMARY KEY `FileKey`)"
TI "RemoveIniFile", "RemoveIniFile,FileName,DirProperty,Section,Key,Value,Action,Component_", "CREATE TABLE `RemoveIniFile` (`RemoveIniFile` CHARACTER(72) NOT NULL,`FileName` CHARACTER(255) NOT NULL LOCALIZABLE,`DirProperty` CHARACTER(72),`Section` CHARACTER(96) NOT NULL LOCALIZABLE,`Key` CHARACTER(128) NOT NULL LOCALIZABLE,`Value` CHARACTER(255) LOCALIZABLE,`Action` INTEGER NOT NULL,`Component_` CHARACTER(72) NOT NULL PRIMARY KEY `RemoveIniFile`)"
TI "RemoveRegistry", "RemoveRegistry,Root,Key,Name,Component_", "CREATE TABLE `RemoveRegistry` (`RemoveRegistry` CHARACTER(72) NOT NULL,`Root` INTEGER NOT NULL,`Key` CHARACTER(255) NOT NULL LOCALIZABLE,`Name` CHARACTER(255) LOCALIZABLE,`Component_` CHARACTER(72) NOT NULL PRIMARY KEY `RemoveRegistry`)"
TI "ReserveCost", "ReserveKey,Component_,ReserveFolder,ReserveLocal,ReserveSource", "CREATE TABLE `ReserveCost` (`ReserveKey` CHARACTER(72) NOT NULL,`Component_` CHARACTER(72) NOT NULL,`ReserveFolder` CHARACTER(72),`ReserveLocal` LONG NOT NULL,`ReserveSource` LONG NOT NULL PRIMARY KEY `ReserveKey`)"
TI "SFPCatalog", "SFPCatalog,Catalog,Dependency", "CREATE TABLE `SFPCatalog` (`SFPCatalog` CHARACTER(255) NOT NULL,`Catalog` OBJECT NOT NULL,`Dependency` LONGCHAR PRIMARY KEY `SFPCatalog`)"
TI "TextStyle", "TextStyle,FaceName,Size,Color,StyleBits", "CREATE TABLE `TextStyle` (`TextStyle` CHARACTER(72) NOT NULL,`FaceName` CHARACTER(32) NOT NULL,`Size` INTEGER NOT NULL,`Color` LONG,`StyleBits` INTEGER PRIMARY KEY `TextStyle`)"
TI "TypeLib", "LibID,Language,Component_,Version,Description,Directory_,Feature_,Cost", "CREATE TABLE `TypeLib` (`LibID` CHARACTER(38) NOT NULL,`Language` INTEGER NOT NULL,`Component_` CHARACTER(72) NOT NULL,`Version` LONG,`Description` CHARACTER(128) LOCALIZABLE,`Directory_` CHARACTER(72),`Feature_` CHARACTER(38) NOT NULL,`Cost` LONG PRIMARY KEY `LibID`,`Language`,`Component_`)"
TI "UIText", "Key,Text", "CREATE TABLE `UIText` (`Key` CHARACTER(72) NOT NULL,`Text` CHARACTER(255) LOCALIZABLE PRIMARY KEY `Key`)"
TI "Verb", "Extension_,Verb,Sequence,Command,Argument", "CREATE TABLE `Verb` (`Extension_` CHARACTER(255) NOT NULL,`Verb` CHARACTER(32) NOT NULL,`Sequence` INTEGER,`Command` CHARACTER(255) LOCALIZABLE,`Argument` CHARACTER(255) LOCALIZABLE PRIMARY KEY `Extension_`,`Verb`)"
TI "MsiDriverPackages", "Component,Flags,Sequence", "CREATE TABLE `MsiDriverPackages` (`Component` CHARACTER(72) NOT NULL,`Flags` LONG NOT NULL,`Sequence` LONG PRIMARY KEY `Component`)"
TI "ExternalFiles", "Family,FTK,FilePath,SymbolPaths,IgnoreOffsets,IgnoreLengths,RetainOffsets,Order", "CREATE TABLE `ExternalFiles` (`Family` CHARACTER(8) NOT NULL,`FTK` CHARACTER(128) NOT NULL,`FilePath` CHARACTER(255) NOT NULL,`SymbolPaths` CHARACTER(255),`IgnoreOffsets` CHARACTER(255),`IgnoreLengths` CHARACTER(255),`RetainOffsets` CHARACTER(255),`Order` INTEGER NOT NULL PRIMARY KEY `Family`,`FTK`,`FilePath`)"
TI "FamilyFileRanges", "Family,FTK,RetainOffsets,RetainLengths", "CREATE TABLE `FamilyFileRanges` (`Family` CHARACTER(13) NOT NULL,`FTK` CHARACTER(128) NOT NULL,`RetainOffsets` CHARACTER(128) NOT NULL,`RetainLengths` CHARACTER(128) NOT NULL PRIMARY KEY `Family`,`FTK`)"
TI "ImageFamilies", "Family,MediaSrcPropName,MediaDiskId,FileSequenceStart,DiskPrompt,VolumeLabel", "CREATE TABLE `ImageFamilies` (`Family` CHARACTER(8) NOT NULL,`MediaSrcPropName` CHARACTER(72),`MediaDiskId` INTEGER,`FileSequenceStart` INTEGER,`DiskPrompt` CHARACTER(128),`VolumeLabel` CHARACTER(32) PRIMARY KEY `Family`)"
TI "Properties", "Name,Value", "CREATE TABLE `Properties` (`Name` CHARACTER(72) NOT NULL,`Value` LONGCHAR LOCALIZABLE PRIMARY KEY `Name`)"
TI "PatchSequence", "PatchFamily,Target,Sequence,Supersede", "CREATE TABLE `PatchSequence` (`PatchFamily` CHARACTER(72) NOT NULL,`Target` CHARACTER(38),`Sequence` CHARACTER(72),`Supersede` LONG PRIMARY KEY `PatchFamily`,`Target`)"
TI "TargetFiles_OptionalData", "Target,FTK,SymbolPaths,IgnoreOffsets,IgnoreLengths,RetainOffsets", "CREATE TABLE `TargetFiles_OptionalData` (`Target` CHARACTER(13) NOT NULL,`FTK` CHARACTER(255) NOT NULL,`SymbolPaths` CHARACTER(255),`IgnoreOffsets` CHARACTER(255),`IgnoreLengths` CHARACTER(255),`RetainOffsets` CHARACTER(255) PRIMARY KEY `Target`,`FTK`)"
TI "TargetImages", "Target,MsiPath,SymbolPaths,Upgraded,Order,ProductValidateFlags,IgnoreMissingSrcFiles", "CREATE TABLE `TargetImages` (`Target` CHARACTER(13) NOT NULL,`MsiPath` CHARACTER(255) NOT NULL,`SymbolPaths` CHARACTER(255),`Upgraded` CHARACTER(13) NOT NULL,`Order` INTEGER NOT NULL,`ProductValidateFlags` CHARACTER(16),`IgnoreMissingSrcFiles` INTEGER NOT NULL PRIMARY KEY `Target`)"
TI "UpgradedFiles_OptionalData", "Upgraded,FTK,SymbolPaths,AllowIgnoreOnPatchError,IncludeWholeFile", "CREATE TABLE `UpgradedFiles_OptionalData` (`Upgraded` CHARACTER(13) NOT NULL,`FTK` CHARACTER(255) NOT NULL,`SymbolPaths` CHARACTER(255),`AllowIgnoreOnPatchError` INTEGER,`IncludeWholeFile` INTEGER PRIMARY KEY `Upgraded`,`FTK`)"
TI "UpgradedFilesToIgnore", "Upgraded,FTK", "CREATE TABLE `UpgradedFilesToIgnore` (`Upgraded` CHARACTER(13) NOT NULL,`FTK` CHARACTER(255) NOT NULL PRIMARY KEY `Upgraded`,`FTK`)"
TI "UpgradedImages", "Upgraded,MsiPath,PatchMsiPath,SymbolPaths,Family", "CREATE TABLE `UpgradedImages` (`Upgraded` CHARACTER(13) NOT NULL,`MsiPath` CHARACTER(255) NOT NULL,`PatchMsiPath` CHARACTER(255),`SymbolPaths` CHARACTER(255),`Family` CHARACTER(8) NOT NULL PRIMARY KEY `Upgraded`)"
TI "PatchMetadata", "Company,Property,Value", "CREATE TABLE `PatchMetadata` (`Company` CHARACTER(72),`Property` CHARACTER(72) NOT NULL,`Value` LONGCHAR NOT NULL LOCALIZABLE PRIMARY KEY `Company`,`Property`)"
end sub


'=========================================================================
sub TI(ByVal TableName, ByVal TblFlds, ByVal CreateSQL)
'=========================================================================
on error resume next
oTableFlds.add      TableName, "`" & replace(TblFlds, ",", "`,`") & "`"
oTableCreateSql.add TableName, CreateSQL
VbsCheck("The table """ & TableName & """ was probably defined twice!")
end sub


'============================================================================
function GetSeqNumber(ByVal TableName, ByVal How, ByVal NumbSlots)
' This code will fail if a sequence table is not current when called!
'============================================================================
dim SeqFirst   : SeqFirst = 1
dim SeqLast    : SeqLast   = 32767
dim ForStep
How = trim(How)
if  left(How, 1) <> "<" then
ForStep  = 1
else
How      = mid(How, 2)
ForStep  = -1
end if
dim Bits, AfterAction, BeforeAction
Bits = split(How & " ", "-")
AfterAction = trim(Bits(0))
if  ubound(Bits) = 0 then
BeforeAction = ""
else
BeforeAction = trim(Bits(1))
end if
dim BeforeActionT : BeforeActionT = BeforeAction
dim AfterActionT  : AfterActionT  = AfterAction
if  IsNumeric(AfterAction) then
SeqFirst    = cint(AfterAction)
AfterAction = ""
end if
if  IsNumeric(BeforeAction) then
SeqLast       = cint(BeforeAction)
BeforeAction = ""
end if
dim SeqNumbers(32767), oRecord
dim AfterSeq, BeforeSeq, AfterFound, BeforeFound
AfterFound  = (AfterAction = "")
BeforeFound = (BeforeAction = "")
SqlOpenExec("SELECT * FROM `" & TableName & "`")
do
set oRecord = SqlViewFetch()
if  oRecord is Nothing then exit do
dim SeqNumber : SeqNumber = oRecord.IntegerData(3)
dim SeqAction : SeqAction = oRecord.StringData(1)
if  SeqNumber >= 0 then
SeqNumbers(SeqNumber) = SeqAction
end if
if  SeqAction = AfterAction then
SeqFirst   = SeqNumber + 1
AfterFound = true
end if
if  SeqAction = BeforeAction then
SeqLast     = SeqNumber - 1
BeforeFound = true
end if
loop
SqlViewClose()
if  not AfterFound then
error("We could not find the action """ & AfterActionT & """ in the table """ & TableName & """!")
end if
if  not BeforeFound then
error("We could not find the action """ & BeforeActionT & """ in the table """ & TableName & """!")
end if
if  (SeqLast < SeqFirst) then
error("The action """ & AfterActionT & """ needs to be before the action """ & BeforeActionT & """!")
end if
if  (SeqLast - SeqFirst)+1 < NumbSlots then
error("The sequence number range (" & SeqFirst & " - " & SeqLast & ") is too small to search for " & NumbSlots & " slots!")
end if
dim ForStart, ForEnd, i
if  ForStep = 1 then
ForStart = SeqFirst
ForEnd   = SeqLast - (NumbSlots - 1)
else
ForStart = SeqLast - (NumbSlots - 1)
ForEnd   = SeqFirst
end if
for i = ForStart to ForEnd step ForStep
if  SeqNumbers(i) = "" then
dim j, FreeSlots
FreeSlots = 0
for j = 1 to NumbSlots
if  SeqNumbers(i+j-1) = "" then
FreeSlots = FreeSlots + 1
else
exit for
end if
next
if  FreeSlots = NumbSlots then
GetSeqNumber = i
exit function
end if
end if
next
dim SlotTxt
if  NumbSlots = 1 then
SlotTxt = "a single empty ""slot"""
else
SlotTxt = NumbSlots & " consecutive empty ""slots"""
end if
error("We did not find " & SlotTxt & " between " & SeqFirst & " and " & SeqLast &  " in the table """ & TableName & """!")
end function


'=========================================================================
function GetComponentDirectoryKeys(ByVal FileKey)
'=========================================================================
on error resume next
SqlOpenExec "SELECT Component, Directory FROM File,Component,Directory WHERE File='" & FileKey & "' and Component=Component_ and Directory=Directory_"
dim oRecord
set oRecord = SqlViewFetch()
if  oRecord is Nothing then
error("To perform an ordered self registration on """ & FileKey & """ we need to know its Component and Directory information. We could not obtain this from the database.")
else
SrComponent = oRecord.StringData(1)
SrDirectory = oRecord.StringData(2)
end if
set oRecord = Nothing
SqlViewClose()
end function


'=========================================================================
function X2L(ByVal HexString)
' Works around VBSCRIPT "feature" which treats "&H8000" as an "short"
' integer no matter what (even with leading zeros).
'
' The passed string can begin with "&H" or "0x" (either case) but must
' otherwise only contain hexadecimal digits (or spaces, which are stripped).
'=========================================================================
HexString = replace(HexString, " ", "")
dim L2         : L2 = ucase(left(HexString, 2))
dim HexDigits
if  L2 = "0X" or L2 = "&H" then
HexDigits = mid(HexString, 3)
else
HexDigits = HexString
end if
on error resume next
X2L = CLng("&H" & HexDigits)
if  err.number <> 0 then
error("X2L(): The hex string """ & HexString & """ is invalid!")
end if
end function


'=========================================================================
sub pc_CompileMsi(Reason, CacheAlias)
'=========================================================================

dim NumFiles2Compile : NumFiles2Compile = NumberOfFilesNeedingCompile()
if   NumFiles2Compile = 0 then
pc_say "No files currently queued for compilation..."
if  TableExists("_MAKEMSI_FileSource") then
pc_say "@Deleting the file source information table"



'######################################################################
MmLL = "installscript.mm(54)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0790"

MmID = "@VBS0791"
TableNowMk "_MAKEMSI_FileSource"
TableDelete("")

MmID = "@VBS0792"
TableNow ""


end if
exit sub
end if

dim Cmt : Cmt = "Starting compile..."
if   CacheAlias = "" then
Cmt = Cmt & "  No cache for this compile."
else
Cmt = Cmt & "  Cache """ & CacheAlias & """"
end if
pc_Say ""
pc_Say GetAmPmTime() & ": " & Cmt
if   Reason <> "" then
pc_Say Reason
end if
dim CacheDir
if   CacheAlias = "" then
CacheDir = ""
else
CacheDir = "out\installscript.mm\Log\Cache.Cab"
if  right(CacheDir, 1) <> "\" then CacheDir = CacheDir & "\"
CacheDir = CacheDir & CacheAlias & "\"
end if
dim NextDiskId    : NextDiskId    = GetNextDiskId()
dim NextFileSeq   : NextFileSeq   = GetNextFileSequence()                           'Next file sequence number
dim CompileNumber : CompileNumber = GetCompileNumber()                              'As Text "01" etc
dim CompileLogDir : CompileLogDir = "out\installscript.mm\Log\MakeCab\#" & CompileNumber      'Dir shortname must be "#xx"
CreateDir(CompileLogDir)
pc_Say "Compile #" & CompileNumber & " for " & NumFiles2Compile & " file(s) with sequence numbers " & NextFileSeq & " to " & (NextFileSeq+NumFiles2Compile-1)
on error resume next         'Why here??????????????????????


oInstaller.UILevel = msiUILevelNone



MmID = "@VBS0793"
cb_PropValue = "UCS AD Connector version 1.0.0 - [1]"

MmID = "@VBS0794"
TableNowMk "Property"
   if cb_PropValue = "" then

MmID = "@VBS0795"
DeleteTableRows("`Property` = 'DiskPrompt'")
   else

MmID = "@VBS0796"
RowPrepare 2

MmID = "@VBS0797"
oRec.StringData(1) = "DiskPrompt"
oRec.StringData(2) = cb_PropValue
ValidateFIELD(1)
RowUpdate()
   end if

MmID = "@VBS0798"
TableNow ""

pc_Say "@Opening the ""File"" table"
SqlOpenExec "SELECT File,FileName,Directory_,Sequence,File.Attributes,SourceFile, FileSize, Component, Date,Time FROM File,Component,_MAKEMSI_FileSource WHERE Component_=Component and File=File_ ORDER BY `Component`, `Directory_`"


pc_Say "@Work out media space and requirements"
dim MaxDiskSize, AvailableBytes, ReservedBytes, MsiFileSize
'MaxDiskSize = 1998951424
'MaxDiskSize = (MaxDiskSize \ 4096) * 4096

MaxDiskSize = clng(1998950400)
VbsCheck "Working out media details"
if  MaxDiskSize = 0 then
say "Media size not specified (no limit to size of generated cab files)"
AvailableBytes = 0
else
say ""
say "Media size is " & AddComma2Long(MaxDiskSize) & " bytes."
set oFile = oFS.GetFile("Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector\out\installscript.mm\MSI\setup.msi")
VbsCheck "Could not get the size for ""Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector\out\installscript.mm\MSI\setup.msi"""
MsiFileSize    = oFile.size
ReservedBytes  = MsiFileSize + 0 + 50000
AvailableBytes = MaxDiskSize - ReservedBytes
'AvailableBytes = (AvailableBytes \ 4096) * 4096
AvailableBytes = int(AvailableBytes / 4096) * 4096
dim ReservedBytesCma : ReservedBytesCma = AddComma2Long(ReservedBytes)
dim PadLng           : PadLng           = len(ReservedBytesCma) + 1
say "Reserving " & ReservedBytesCma & " bytes on media #1 (" & AddComma2Long(AvailableBytes) & " bytes available):"
say "  = MSI      : " & Pad(AddComma2Long(MsiFileSize), PadLng, " ")
if   0 <> 0 then
say "  + Extra    : " & Pad(AddComma2Long("0"), PadLng, " ") & " (via ""MsiExtraFiles"" commands)"
end if
say "  + Reserved : " & Pad(AddComma2Long(50000), PadLng, " ") & " (see ""COMPILE_RESERVED_BYTES_ON_MEDIA1"")"
say ""
if   AvailableBytes < 10000 then
error "Too little space is available (" & AddComma2Long(AvailableBytes) & " bytes) on media 1!"
end if
end if
VbsCheck "Failed working out media info"
pc_Say "@Creating the CAB files DDF header"
dim oFileRec, FileKey, DirKey, MmSrcFile, FileDate, FileTime
dim SrcBase, CabBase, CabFile, RptFile, InfFile, CmdFile, CabDdf, CabOutput
SrcBase   = CompileLogDir & "\setup"
CabBase   = CompileLogDir & replace("\" & pc_COMPILE_CAB_FILE_NAME, "*", CompileNumber)
CabFile   = CabBase & ".cab"
CabDdf    = SrcBase & ".ddf"
RptFile   = SrcBase & ".rpt"
InfFile   = SrcBase & ".inf"
CmdFile   = SrcBase & "-MAKECAB.cmd"
CabOutput = SrcBase & ".txt"
VbsCheck "About to create the DDF file"
Dim CabStream : Set CabStream = oFS.CreateTextFile(CabDdf, true)
VbsCheck "Could not create the DDF file """ & CabDdf & """"
CabStream.WriteLine ";" & String(70, "=")
CabStream.WriteLine "; Generated at  : " &  Now()
if   Reason <> "" then
CabStream.WriteLine "; Compile Reason: " &  Reason
end if
dim CacheCmt
if   CacheAlias = "" then
CacheCmt = "No caching for this compile"
else
CacheCmt = CacheDir
end if
CabStream.WriteLine "; Caching to    : " & CacheCmt
CabStream.WriteLine ";" & String(70, "=")
CabStream.WriteLine ""
CabStream.WriteLine ".Option explicit"
CabStream.WriteLine ".Set MaxErrors=1"
CabStream.WriteLine ".Set UniqueFiles=ON"
CabStream.WriteLine ".Set MaxDiskSize="  & MaxDiskSize
if AvailableBytes <> 0 then
CabStream.WriteLine ".Set MaxDiskSize1=" & AvailableBytes
end if
CabStream.WriteLine ".Set InfHeader="
CabStream.WriteLine ".Set InfFooter="
CabStream.WriteLine ".Set DiskDirectoryTemplate=."
CabStream.WriteLine ".Set Cabinet=ON"
CabStream.WriteLine vbCRLF
CabStream.WriteLine ";---The following are for options that can vary per MAKEMSI ""Compile"" command ----"
CabStream.WriteLine ".Set Compress="          & pc_COMPILE_CABDDF_Compress
CabStream.WriteLine ".Set CompressionType="   & pc_COMPILE_CABDDF_CompressionType
CabStream.WriteLine ".Set CompressionLevel="  & pc_COMPILE_CABDDF_CompressionLevel
CabStream.WriteLine ".Set CompressionMemory=" & pc_COMPILE_CABDDF_CompressionMemory
CabStream.WriteLine ".Set ClusterSize="       & pc_COMPILE_CABDDF_ClusterSize
CabStream.WriteLine vbCRLF
CabStream.WriteLine replace("", "{NL}", vbCRLF)
CabStream.WriteLine vbCRLF
CabStream.WriteLine ".Set ReservePerCabinetSize=8"
CabStream.WriteLine ".Set   FolderSizeThreshold=1"
CabStream.WriteLine vbCRLF
CabStream.WriteLine ".Set         RptFileName=" & RptFile
CabStream.WriteLine ".Set         InfFileName=" & InfFile
CabStream.WriteLine ".Set        CabinetName1=" & CabFile
CabStream.WriteLine ".Set CabinetNameTemplate=" & CabBase & "_*.CAB"
CabStream.WriteLine vbCRLF
CabStream.WriteLine ".Set InfDiskHeader="
CabStream.WriteLine ".Set InfDiskHeader1="";=================================="""
CabStream.WriteLine ".Set InfDiskHeader2="";===          DISK List         ==="""
CabStream.WriteLine ".Set InfDiskHeader3="";=== <disk number>,<disk label> ==="""
CabStream.WriteLine ".Set InfDiskHeader4="";=================================="""
CabStream.WriteLine ".Set InfDiskHeader5=[disk list]"
CabStream.WriteLine ".Set InfDiskLineFormat=*disk#*,*label*"
CabStream.WriteLine vbCRLF
CabStream.WriteLine ".Set InfCabinetHeader="
CabStream.WriteLine ".Set InfCabinetHeader1="";==========================================================="""
CabStream.WriteLine ".Set InfCabinetHeader2="";===                   CABINET List                      ==="""
CabStream.WriteLine ".Set InfCabinetHeader3="";=== <cabinet number>,<disk number>,<cabinet file name>  ==="""
CabStream.WriteLine ".Set InfCabinetHeader4="";==========================================================="""
CabStream.WriteLine ".Set InfCabinetHeader5=[cabinet list]"
CabStream.WriteLine ".Set InfCabinetLineFormat=*cab#*,*disk#*,*cabfile*"
CabStream.WriteLine vbCRLF
CabStream.WriteLine ".Set InfFileHeader="
CabStream.WriteLine ".Set InfFileHeader1="";==============================================================="""
CabStream.WriteLine ".Set InfFileHeader2="";===                        File List                        ==="""
CabStream.WriteLine ".Set InfFileHeader3="";=== <disk number>,<cabinet number>,<file key>,<file number> ==="""
CabStream.WriteLine ".Set InfFileHeader4="";==============================================================="""
CabStream.WriteLine ".Set InfFileHeader5=[file list]"
CabStream.WriteLine ".Set InfFileLineFormat=*disk#*,*cab#*,*file*,*file#*"
CabStream.WriteLine vbCRLF
CabStream.WriteLine vbCRLF
VbsCheck "Error writing to the DDF file """ & CabDdf & """"




pc_Say "@Getting the current directory"
dim oFile, CurrentDir83, CurrentDir83Len
set oFile       = oFS.GetFolder(".")
pc_Say "@Current directory (long) = """ & oFile.Path      & """"
pc_Say "@Current directory (8.3)  = """ & oFile.ShortPath & """"
CurrentDir83    = ucase(oFile.ShortPath)
if   right(CurrentDir83, 1) <> "\" then
CurrentDir83 = CurrentDir83 & "\"
end if
pc_Say "@Current directory = """ & CurrentDir83 & """"
CurrentDir83Len = len(CurrentDir83)
set oFile = Nothing
VbsCheck "Error getting the current directory"
pc_Say "@Work through the ""File"" table"
dim InfSeqOffset        : InfSeqOffset      = NextFileSeq - 1
dim NewSequenceNumber   : NewSequenceNumber = InfSeqOffset
dim LastComponent       : LastComponent     = ""
dim UniqueCompCnt        : UniqueCompCnt     = 0
dim FileComp
do
set oFileRec = SqlViewFetch()
if  oFileRec is Nothing then exit do
FileKey   = oFileRec.StringData(1)
DirKey    = oFileRec.StringData(3)
MmSrcFile = oFileRec.StringData(6)
FileComp  = oFileRec.StringData(8)
FileDate  = oFileRec.StringData(9)
FileTime  = oFileRec.StringData(10)


dim BarPos, FilesName, MsiSrcFile
FilesName = oFileRec.StringData(2)
BarPos = InStr(FilesName, "|")
If  BarPos <> 0 then
FilesName = mid(FilesName, BarPos+1)
End If


set oFile = oFS.GetFile(MmSrcFile)
VbsCheck "Getting file object for '" & MmSrcFile & "'"
MmSrcFile = oFile.ShortPath
set oFile = Nothing
if   CurrentDir83 = ucase(left(MmSrcFile, CurrentDir83Len)) then
MmSrcFile = mid(MmSrcFile, CurrentDir83Len+1)
end if
NewSequenceNumber = NewSequenceNumber + 1
oFileRec.IntegerData(4) = NewSequenceNumber
oView.Modify msiViewModifyUpdate, oFileRec
VbsCheck "Failed updating the sequence number for '" & FileKey & "'"


if   LastComponent <> FileComp then
UniqueCompCnt = UniqueCompCnt + 1
CabStream.WriteLine ""
CabStream.WriteLine ""
CabStream.WriteLine ";---"
CabStream.WriteLine ";--- Component #" & UniqueCompCnt & " """ & FileComp & """ (starts with SEQ #" & NewSequenceNumber & ") ---"
CabStream.WriteLine ";---"
end if
LastComponent = FileComp
dim DdfFileCmt : DdfFileCmt = ""
if   CacheAlias <> "" then
err.clear()
DdfFileCmt = CacheFileStamp(MmSrcFile)
if  DdfFileCmt = "" or err.number <> 0 then
DdfFileCmt = "CacheFileStamp() failed at " & now() & " : RC = 0x" & hex(err.number) & ", Reason: " & err.description
err.clear()
end if
DdfFileCmt = ";>>> " & DdfFileCmt & " <<<"
CabStream.WriteLine DdfFileCmt
DdfFileCmt = vbCRLF
end if
dim DdfFileLine : DdfFileLine = """" & MmSrcFile & """" & " " & FileKey
if   FileDate <> "" then DdfFileLine = DdfFileLine & " /DATE=" & FileDate
if   FileTime <> "" then DdfFileLine = DdfFileLine & " /TIME=" & FileTime
CabStream.WriteLine DdfFileLine & DdfFileCmt
loop
CabStream.close()
SqlViewClose()


DeleteFile(CabOutput)
DeleteFile(RptFile)
DeleteFile(InfFile)




if   NewSequenceNumber = 0 then
pc_Say "There are no files in the MSI..."
else
dim ReadFromCache : ReadFromCache = false
if   CacheAlias <> "" then
pc_Say "Checking cache at """ & CacheDir & """"
dim CachedCabFile : CachedCabFile = CacheDir & oFS.GetFileName(CabFile)
dim CachedCabDdf  : CachedCabDdf  = CacheDir & oFS.GetFileName(CabDdf)
dim CachedRptFile : CachedRptFile = CacheDir & oFS.GetFileName(RptFile)
dim CachedInfFile : CachedInfFile = CacheDir & oFS.GetFileName(InfFile)
dim CachedCmdFile : CachedCmdFile = CacheDir & oFS.GetFileName(CmdFile)
dim HaveAll : HaveAll = oFs.FileExists(CachedCabFile) and oFs.FileExists(CachedCabDdf) and oFs.FileExists(CachedRptFile) and oFs.FileExists(CachedInfFile) and oFs.FileExists(CachedCmdFile)
if  not HaveAll then
pc_say "Cache doesn't exist or is corrupt"
else
pc_say "Cache exists.  Any file/option differences since last build?"
dim DdfTxtNew : DdfTxtNew = pc_GetDdfFileContentsForCacheCompare(CabDdf)
dim DdfTxtOld : DdfTxtOld = pc_GetDdfFileContentsForCacheCompare(CachedCabDdf)
if  DdfTxtNew = "" or DdfTxtOld = "" then
pc_Say "Oops, not sure so won't use cache..."
else
if  DdfTxtNew <> DdfTxtOld then
pc_Say "Differences found, can't use the cache..."
else
pc_Say "No differences found so we can still use the cache..."
ReadFromCache = true
end if
end if
if  ReadFromCache then
pc_say "Copying cached files now..."
ReadFromCache = false           'Play it safe
DeleteFile(CabFile)
DeleteFile(CabDdf)
DeleteFile(RptFile)
DeleteFile(InfFile)
DeleteFile(CmdFile)
oFS.CopyFile CachedCabFile, CabFile, false
oFS.CopyFile CachedCabDdf,  CabDdf,  false
oFS.CopyFile CachedRptFile, RptFile, false
oFS.CopyFile CachedInfFile, InfFile, false
oFS.CopyFile CachedCmdFile, CmdFile, false
if  err.number = 0 then
pc_say "Successfully copied all files from the cache..."
ReadFromCache = true
else
pc_say "Failed getting files from cache, will need to rebuild cabinets..."
err.clear()             'Don't fail build just because of this
end if
end if
end if
end if
if   not ReadFromCache then
pc_Say "Compressing the files into CAB file(s)"
dim MakeCabCmd : MakeCabCmd = """MakeCab.exe"" /f """ & CabDdf & """ /v1"
err.clear
dim CabCmd, CabRc
CabCmd = MakeCabCmd & " 2>&1 | Reg4mm.exe Tee4MM.4mm  '" & CabOutput & "' ""!Throughput:"""
CabCmd = "cmd.exe /c """ & CabCmd & """"          'Windows "feature"
KeepMakecabExeCommandLineForDebugging CmdFile, CabCmd, MakeCabCmd
CabRc  = oShell.Run(CabCmd, 1, True)
VbsCheck "Failed making the cab file (does ""MakeCab.exe"" exist?)"
If  CabRc <> 0 Then
if  not oFs.FileExists(CabOutput) then
Error "MAKECAB.EXE failed (no output generated - does ""MakeCab.exe"" exist?)"
else
err.clear()
dim OutStream : set OutStream = oFS.OpenTextFile(CabOutput, ForReading)
dim GenOutput : GenOutput     = OutStream.readall()
dim GenErrTxt : GenErrTxt     = ""
OutStream.Close()
if  err.number <> 0 then
GenOutput = ""
else
GenOutput = replace(GenOutput, vbCR,      "")
GenOutput = replace(GenOutput, vbLF,      vbCRLF)
GenOutput = replace(GenOutput, " ERROR:", vbCRLF & vbCRLF & "ERROR:")
say ""
say "MAKECAB FAILED - OUTPUT FOLLOWS"
say "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
say GenOutput
dim Pos : Pos = instr(GenOutput, "ERROR:")
if   Pos <> 0 then
GenErrTxt = mid(GenOutput, Pos)
end if
if  len(GenOutput) > 6000 then
GenOutput = "..." & right(GenOutput, 6000)
end if
if  len(GenErrTxt) > 6000  then
GenErrTxt = "..." & right(GenErrTxt, 6000)
end if
set OutStream = oFS.CreateTextFile(CabOutput, true)
OutStream.write GenOutput
OutStream.Close()
end if
'ViewFile CabOutput
if   GenErrTxt <> "" then
GenErrTxt = vbCRLF & vbCRLF & "CAB ERROR TEXT" & vbCRLF & "~~~~~~~~~~~~~~" & vbCRLF & GenErrTxt
end if
Error "MAKECAB.EXE (compile) step failed..." & GenErrTxt
end if
end if
end if
if   ReadFromCache then
pc_say "Files originally read from cache so we won't recache :-)"
else
if  CacheAlias = "" then
pc_say "Will not cache as this wasn't requested"
else
pc_say "Caching to """ & CacheDir & """"
CreateDir(CacheDir)
DeleteFile(CachedCabFile)
DeleteFile(CachedCabDdf)
DeleteFile(CachedRptFile)
DeleteFile(CachedInfFile)
DeleteFile(CachedCmdFile)
oFS.CopyFile CabFile, CachedCabFile, false
oFS.CopyFile CabDdf,  CachedCabDdf,  false
oFS.CopyFile RptFile, CachedRptFile, false
oFS.CopyFile InfFile, CachedInfFile, false
oFS.CopyFile CmdFile, CachedCmdFile, false
if  err.number = 0 then
pc_say "Successfully copied all files to the cache..."
else
pc_say "Failed putting files into the cache..."
err.clear()             'Don't fail build just because of this
end if
end if
end if
if  oFS.FileExists(RptFile) then
pc_Say "@Displaying: " & RptFile
say ""
dim RptStream : set RptStream = oFS.OpenTextFile(RptFile, ForReading)
do  while RptStream.AtEndOfStream <> true
say "    | " & RptStream.ReadLine
loop
RptStream.close
say ""
end if
pc_Say "@Reading the generated INF file - CAB Section"
if  not oFS.FileExists(InfFile) then
Error "We expected the file """ & InfFile & """ to have been generated by the compile."
end if
dim CabDisk(), CabName(), CabMaxSeq()
dim CabBits, InfLine
dim CabCnt       : CabCnt        = 0
dim FoundSection : FoundSection  = false
dim InfStream    : set InfStream = oFS.OpenTextFile(InfFile, ForReading)
do  while InfStream.AtEndOfStream <> true
InfLine = InfStream.ReadLine()
if  not FoundSection then
if  InfLine = "[cabinet list]" then
FoundSection = true
end if
else
if  InfLine = "" then
exit do
else
CabBits = split(InfLine, ",")
redim preserve CabDisk(CabCnt)
redim preserve CabName(CabCnt)
redim preserve CabMaxSeq(CabCnt)
CabDisk(CabCnt)   = CabBits(1)
CabName(CabCnt)   = CabBits(2)
CabMaxSeq(CabCnt) = 0
CabCnt            = CabCnt + 1
end if
end if
loop
InfStream.close
VbsCheck "Failed reading the INF for cab file information"
if   CabCnt <> 0 then
pc_say "Generated " & CabCnt & " cab file(s)."
else
Error "No cab files appear to have been generated (see """ & InfFile & """)."
end if
pc_Say "@Reading the generated INF file - FILE Section"
dim CabNumber, ThisSeq
FoundSection  = false
set InfStream = oFS.OpenTextFile(InfFile, ForReading)
do  while InfStream.AtEndOfStream <> true
InfLine = InfStream.ReadLine()
if  not FoundSection then
if  InfLine = "[file list]" then
FoundSection = true
end if
else
if  InfLine = "" then
exit do
else
CabBits = split(InfLine, ",")
CabNumber = CabBits(1)
ThisSeq   = cint(CabBits(3)) + InfSeqOffset
if  ThisSeq > CabMaxSeq(CabNumber-1) then
CabMaxSeq(CabNumber-1) = ThisSeq
end if
end if
end if
loop
InfStream.close
VbsCheck "Failed reading the INF for file sequence file information"




dim ThisCabFile, ThisDisk, MaxSeq, LastNonZeroSeq
dim CabKey, MediaCabinet
for CabNumber = 1 to CabCnt
ThisCabFile = CabName(CabNumber-1)
ThisDisk    = CabDisk(CabNumber-1)
MaxSeq      = CabMaxSeq(CabNumber-1)
pc_Say "Processing CAB #" & CabNumber & ": " & ThisCabFile
if  not oFS.FileExists(ThisCabFile) then
Error "The CAB file #" & CabNumber & " (""" & ThisCabFile & """) doesn't exist!"
end if
if   MaxSeq <> 0 then
LastNonZeroSeq = MaxSeq
else
MaxSeq = LastNonZeroSeq
if  LastNonZeroSeq = 0 then
Error "Did not find file sequence information for the CAB file #" & CabNumber & " (""" & ThisCabFile & """)!"
end if
end if
CabKey = oFS.GetFileName(ThisCabFile)
MediaCabinet = "#_MAKEMSI_Cabs." & CabKey

MmID = "@VBS0799"
TableNowMk "_MAKEMSI_Cabs"


MmID = "@VBS0800"
TableNowMk "_Validation"
 

MmID = "@VBS0801"
RowPrepare 10

MmID = "@VBS0802"
oRec.StringData(1) = "_MAKEMSI_Cabs"
oRec.StringData(2) = "Name"
oRec.StringData(3) = "N"
oRec.StringData(8) = "Identifier"
oRec.StringData(10) = "Referred to by Media Table (column ""Cabinet"")."
ValidateFIELD(1)
RowUpdate()
 

MmID = "@VBS0803"
RowPrepare 10

MmID = "@VBS0804"
oRec.StringData(1) = "_MAKEMSI_Cabs"
oRec.StringData(2) = "Data"
oRec.StringData(3) = "N"
oRec.StringData(8) = "Binary"
oRec.StringData(10) = "Hold the CAB file."
ValidateFIELD(1)
RowUpdate()
 

MmID = "@VBS0805"
TableNow "_MAKEMSI_Cabs"


MmID = "@VBS0806"
RowPrepare 2

MmID = "@VBS0807"
oRec.StringData(1) = CabKey
oRec.SetStream 2, ThisCabFile

ValidateStreamKeyLength array(1)
ValidateNEW(0)
RowUpdate()

VbsCheck "Failed imbedding the cab file """ & ThisCabFile & """ into the MSI!"

MmID = "@VBS0808"
TableNow ""

dim DiskPrompt : DiskPrompt = "Disk #{#}"
DiskPrompt = replace(DiskPrompt, "{#}", ThisDisk)
if   len(DiskPrompt) > 64 then
error "We generated a disk prompt of """ & DiskPrompt & """ which is too long, the longest valid prompt is 64 characters!{NL}Update the ""COMPILE_MEDIA_DISK_NUMBER_DESC_TEMPLATE"" macro!"
end if
dim VolumeLabel : VolumeLabel = "AppDisk #{#}"
VolumeLabel = replace(VolumeLabel, "{#}", ThisDisk)
if   len(VolumeLabel) > 32 then
error "We generated a volume label of """ & VolumeLabel & """ which is too long, the longest valid label is 32 characters!{NL}Update the ""COMPILE_MEDIA_VolumeLabel_TEMPLATE"" macro!"
end if
pc_Say "@Update the ""Media"" table"

MmID = "@VBS0809"
TableNowMk "Media"


MmID = "@VBS0810"
RowPrepare 6

MmID = "@VBS0811"
oRec.IntegerData(1) = NextDiskId
oRec.IntegerData(2) = MaxSeq
oRec.StringData(3) = DiskPrompt
oRec.StringData(5) = VolumeLabel
oRec.StringData(4) = MediaCabinet
ValidateNEW(0)
RowUpdate()
 VbsCheck "Failed updating the media table!"
NextDiskId = NextDiskId + 1

MmID = "@VBS0812"
TableNow ""

next
pc_say "@Deleting the file source information table"

MmID = "@VBS0813"

MmID = "@VBS0814"
TableNowMk "_MAKEMSI_FileSource"
TableDelete("")

MmID = "@VBS0815"
TableNow ""


pc_say "@Deleting the " & CabCnt & " temporary cab file(s)"
for CabNumber = 1 to CabCnt
DeleteFile CabName(CabNumber-1)
next
end if
Say "Marking MSI updates as complete..." 

MmID = "@VBS0816"
TableNowMk "LaunchCondition"
 

MmID = "@VBS0817"
DeleteTableRows("`Condition` = 'NoSuchProperty.so.always.false'")
 dim s_RowCnt : s_RowCnt = 0 

MmID = "@VBS0818"
RowsPrepare ""
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO

'--- START of USER Code ---

MmID = "@VBS0819"
on error resume next


 s_RowCnt = s_RowCnt + 1 

MmID = "@VBS0820"



MmID = "@VBS0821"
VbsCheck "/VBS Command detected failure!" & vbCRLF & vbCRLF & "VBS command: installscript.mm(54) - Processing ROW command's query results"
on error goto 0

MmID = "@VBS0822"

ValidateFETCH(1)
loop
SqlViewClose()
 if  s_RowCnt = 0 then 

MmID = "@VBS0823"
TableDelete("")
 end if 

MmID = "@VBS0824"
TableNow ""

pc_Say GetAmPmTime() & ": Finished compile. Took " & Elapsed() & " seconds."
pc_Say ""
end sub



'=========================================================================
function pc_GetDdfFileContentsForCacheCompare(DdfFileName)
'=========================================================================
on error resume next
dim T        : T        = ""
dim FiPrefix : FiPrefix = ";>>>"
dim FileLine
dim DdfStream : set DdfStream = oFS.OpenTextFile(DdfFileName, ForReading)
do  while DdfStream.AtEndOfStream <> true
FileLine = trim(DdfStream.ReadLine)
if left(FileLine, 1) = ";" then
if left(FileLine, len(FiPrefix)) <> FiPrefix then
FileLine = ""
end if
end if
T = T & FileLine & vbCRLF
loop
DdfStream.Close()
pc_GetDdfFileContentsForCacheCompare = T
end function



'---------------------------------------
'Available objects:
'     * oFS
'     * oInstaller
'
' By default only modification time and file size matter (you could add file version, md5 etc)
'---------------------------------------



function CacheFileStamp(ByVal FileName)      'Creates a string which should change if the file changes
CacheFileStamp = ""
dim oFile : set oFile = oFS.GetFile(FileName)
CacheFileStamp = "FileSize:"        & oFile.Size & ", LastModified: " & oFile.DateLastModified
set oFile = Nothing
end function







'=========================================================================
sub CompileInitializationAtStartOfPass1()
'=========================================================================
DeleteDir "out\installscript.mm\Log\MakeCab"
end sub


'=========================================================================
sub KeepMakecabExeCommandLineForDebugging(ByVal CmdFile, ByVal CmdLineComplete, ByVal CmdLine)
'=========================================================================
on error goto 0
pc_Say "@Creating: " & CmdFile
dim CurrentDir : CurrentDir = oFS.GetAbsolutePathName(".")
dim CmdStream  : set CmdStream = oFS.CreateTextFile(CmdFile, true)
CmdStream.WriteLine "@echo off"
CmdStream.WriteLine "@rem ***"
CmdStream.WriteLine "@rem *** This batch file makes it easier to test MAKECAB.EXE in isolation (perhaps for testing the performance impact of "".DDF"" changes)"
CmdStream.WriteLine "@rem *** It needs to be run from the "".MM"" directory!"
CmdStream.WriteLine "@rem ***"
CmdStream.WriteLine "@rem *** MAKECAB CMD  : " & CmdLine
CmdStream.WriteLine "@rem *** MAKEMSI Runs : " & CmdLineComplete
CmdStream.WriteLine "@rem *** Runs From    : " & CurrentDir
CmdStream.WriteLine "@rem ***"
CmdStream.WriteLine ""
CmdStream.WriteLine "setlocal"
CmdStream.WriteLine "cd " & CurrentDir
CmdStream.WriteLine CmdLine
CmdStream.WriteLine "pause"
CmdStream.close()
err.clear()
end sub


'=========================================================================
sub pc_Say(Text)
'=========================================================================
MmLL = "COMPILE.MMH"
if  left(Text, 1) = "@" then
MmLT = mid(Text, 2)
else
MmLT = Text
Say Text
end if
end sub



'=========================================================================
function GetCompileNumber()
'=========================================================================
dim CompileNumber : CompileNumber = 0
if  oFS.FolderExists("out\installscript.mm\Log\MakeCab") then
dim oMainDir : set oMainDir = oFS.GetFolder("out\installscript.mm\Log\MakeCab")
dim oDir
for each oDir in oMainDir.SubFolders
dim FolderName : Foldername = oDir.name
dim FolderNumb : FolderNumb = mid(FolderName, 2)
if  left(FolderName, 1) = "#" and IsNumeric(FolderNumb) then
if  cint(FolderNumb) > CompileNumber then
CompileNumber = cint(FolderNumb)
end if
end if
next
end if
set oMainDir = Nothing
set oDir     = Nothing
CompileNumber = CompileNumber + 1
GetCompileNumber = cstr(CompileNumber)
if  len(GetCompileNumber) = 1 then
GetCompileNumber = "0" & GetCompileNumber
end if
end function



'=========================================================================
function NumberOfFilesNeedingCompile()
'=========================================================================
NumberOfFilesNeedingCompile = clng(0)
if  TableExists("_MAKEMSI_FileSource") then

MmID = "@VBS0825"
TableNowMk "_MAKEMSI_FileSource"


MmID = "@VBS0826"
RowsPrepare ""
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO

'--- START of USER Code ---

MmID = "@VBS0827"
on error resume next



NumberOfFilesNeedingCompile = NumberOfFilesNeedingCompile + 1

MmID = "@VBS0828"



MmID = "@VBS0829"
VbsCheck "/VBS Command detected failure!" & vbCRLF & vbCRLF & "VBS command: installscript.mm(54) - Processing ROW command's query results"
on error goto 0

MmID = "@VBS0830"

loop
SqlViewClose()


MmID = "@VBS0831"
TableNow ""

end if
end function



'=========================================================================
function GetNextFileSequence()        'First entry is one
'=========================================================================
GetNextFileSequence = 0
if  TableExists("File") then

MmID = "@VBS0832"
TableNowMk "File"


MmID = "@VBS0833"
RowsPrepare ""
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO

'--- START of USER Code ---

MmID = "@VBS0834"
on error resume next



if   oRec.IntegerData(8) > GetNextFileSequence then
GetNextFileSequence = oRec.IntegerData(8)
end if

MmID = "@VBS0835"



MmID = "@VBS0836"
VbsCheck "/VBS Command detected failure!" & vbCRLF & vbCRLF & "VBS command: installscript.mm(54) - Processing ROW command's query results"
on error goto 0

MmID = "@VBS0837"

loop
SqlViewClose()


MmID = "@VBS0838"
TableNow ""

end if
GetNextFileSequence = GetNextFileSequence + 1
end function



'=========================================================================
function GetNextDiskId()        'First entry is one
'=========================================================================
GetNextDiskId = 0
if  TableExists("Media") then

MmID = "@VBS0839"
TableNowMk "Media"


MmID = "@VBS0840"
RowsPrepare ""
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO

'--- START of USER Code ---

MmID = "@VBS0841"
on error resume next



if   oRec.IntegerData(1) > GetNextDiskId then
GetNextDiskId = oRec.IntegerData(1)
end if

MmID = "@VBS0842"



MmID = "@VBS0843"
VbsCheck "/VBS Command detected failure!" & vbCRLF & vbCRLF & "VBS command: installscript.mm(54) - Processing ROW command's query results"
on error goto 0

MmID = "@VBS0844"

loop
SqlViewClose()


MmID = "@VBS0845"
TableNow ""

end if
GetNextDiskId = GetNextDiskId + 1
end function



'==========================================
function Html2Text(ByVal Html)
'==========================================
Html2Text = Html2TextUsingPoorMans(Html)
end function



'---- Actual IE automation code to convert HTML to Text -------------
'=========================================================================
function IeWorkedTruelyAmazing(ByVal Html, ByRef Text)
' Windows is a crock isn't it? Simply navigating to a blank page can fail
' and invalidate the IE object (which was originally successfully created).
' I have seen every single step fail on perfectly working boxes, however
' I have only seen the need for a single retry, using 20 just in case.
' I have seen evidence that IE sometimes gets confused about
' which object its refering to (scary).
'=========================================================================
on error resume next
IeWorkedTruelyAmazing = false
dim oStart : oStart  = Now()
dim IeObj  : IeObj   = "InternetExplorer.Application"
dim oIE    : set oIE = CreateObject(IeObj)
if  err.number <> 0 then
say "Html2Text(): Couldn't create IE object """ & IeObj & """, Reason 0x" & hex(err.number) & " - " & err.description
else
oIE.visible = false
oIE.Silent  = true
oIE.offline = true
oIE.Navigate("about:blank")     'Can fail
if  err.number <> 0 then
say "Html2Text(): Failed navigating IE to a blank page, Reason 0x" & hex(err.number) & " - " & err.description
else
do  while oIE.Busy
if  err.number <> 0 then
say "Html2Text(): Failed waiting for a blank page in IE, Reason 0x" & hex(err.number) & " - " & err.description
set oIE = Nothing
exit function
end if
dim Ss : Ss = DateDiff("s", oStart, Now())
if  Ss >= 2 then
say "Html2Text(): Waited too long (2 seconds) for a blank page in IE!"
set oIE = Nothing
exit function
end if
wscript.sleep(50)
loop
if  err.number <> 0 then
say "Html2Text(): IE object invalidated while waiting... Error code 0x" & hex(err.number) & " - " & err.description
err.clear()
else
dim oIeDoc : set oIeDoc = oIE.Document
if  err.number <> 0 then
say "Html2Text(): Failed getting IE object's document property... Reason 0x" & hex(err.number) & " - " & err.description
else
oIeDoc.Body.innerHtml = Html
if err.number = 0 then Text = oIeDoc.Body.innerText
if  err.number <> 0 then
say "Html2Text(): Failed in actual HTML to text conversion... Reason 0x" & hex(err.number) & " - " & err.description
else
IeWorkedTruelyAmazing = true
end if
end if
set oIeDoc = Nothing
end if
end if
oIE.Quit()
end if
set oIE = Nothing
end function



'=========================================================================
function Html2TextUsingIe(ByVal Html)
'=========================================================================
'--- MSI_HTML2TEXT_FUNCTION_VIA_IE_AUTOMATION ------------------------
on error resume next
dim Try
dim OK : OK = false
for Try = 1 to 20
if   Try <> 1 then
wscript.sleep(500)
end if
OK = IeWorkedTruelyAmazing(Html, Html2TextUsingIe)
if OK then
exit for
end if
next
if   OK then
if  Try <> 1 then
say "Html2TextUsingIe(): Recovered from the IE problem..."
end if
else
Html2TextUsingIe = Html
error("Html2Text(): Tried to use IE automation to convert HTML to text but this failed!")
end if
end function



'==========================================
function Html2TextUsingPoorMans(ByVal Html2Text)
'==========================================
'--- MSI_HTML2TEXT_FUNCTION_VIA_POOR_MANS_CHANGES -------------------
on error resume next



Html2Text = replace(Html2Text, "<p>", vbCRLF & vbCRLF)
Html2Text = replace(Html2Text, "</p>", "")
Html2Text = replace(Html2Text, "<br>", vbCRLF)
Html2Text = replace(Html2Text, "<ol>", " ")
Html2Text = replace(Html2Text, "</ol>", " ")
Html2Text = replace(Html2Text, "<ul>", " ")
Html2Text = replace(Html2Text, "</ul>", " ")
Html2Text = replace(Html2Text, "<li>", vbCRLF & " *")
Html2Text = replace(Html2Text, "</li>", "")
Html2Text = replace(Html2Text, "<b>", "")
Html2Text = replace(Html2Text, "</b>", "")
Html2Text = replace(Html2Text, "<i>", "")
Html2Text = replace(Html2Text, "</i>", "")
Html2TextUsingPoorMans = Html2Text
end function



'=========================================================================
function PrettyHash(ByVal UglyHash)
'=========================================================================
PrettyHash = Hex8(UglyHash.IntegerData(1)) & "-" & Hex8(UglyHash.IntegerData(2)) & "-" & Hex8(UglyHash.IntegerData(3)) & "-" & Hex8(UglyHash.IntegerData(4))
end function

'=========================================================================
function Hex8(Value)
'=========================================================================
Hex8 = hex(Value)
Hex8 = right(string(8, "0") & Hex8, 8)
Hex8 = mid(Hex8,7,2) & mid(Hex8,5,2) & mid(Hex8,3,2) & mid(Hex8,1,2)
end function



'=========================================================================
sub OutputEnvironmentalVersionInformation()
'=========================================================================
on error resume next
dim WinVer      : WinVer = ""
dim Base        : Base = "HKLM\Software\Microsoft\Windows NT\CurrentVersion\"
dim ProductName : ProductName = oShell.RegRead(Base & "ProductName")
if  Err.Number <> 0 then
WinVer = "WINXP"
else
dim CurrentVersion     : CurrentVersion     = oShell.RegRead(Base & "CurrentVersion")
dim CurrentBuildNumber : CurrentBuildNumber = oShell.RegRead(Base & "CurrentBuildNumber")
dim CSDVersion         : CSDVersion         = oShell.RegRead(Base & "CSDVersion")
WinVer = ProductName & " (" & CurrentVersion & "." & CurrentBuildNumber & " " & CSDVersion & ")"
end if
say "Windows   Version: " & WinVer
VbsReturnMacro "Windows.Version", WinVer
dim WshVersion : WshVersion = wscript.version
say "WSH       Version: " & WshVersion
VbsReturnMacro "WSH.Version", WshVersion
say "Installer Version: " & oInstaller.Version
VbsReturnMacro "WindowsInstaller.Version", oInstaller.Version
say ""
end sub


'=========================================================================
sub VbsReturnMacro(ByVal Name, ByVal Value)
'=========================================================================
if  Pass = "1" then
oRetStream.WriteLine "#define VBSRET." & Name & " " & Value
end if
end sub


'=========================================================================
function MsiGetOpenedFileName()
'=========================================================================
MsiGetOpenedFileName = MsiFileName
end function


'=========================================================================
sub MsiOpen(ByVal MsiName, ByVal OpenMode, ByVal Want2CommitOnError)
'=========================================================================
on error resume next
set oMsi = oInstaller.OpenDatabase(MsiName, OpenMode)
VbsCheck "Opening the MSI : " & MsiName
MsiFileName = MsiName
CommitOnError = Want2CommitOnError
end sub


'=========================================================================
sub MsiClose(ByVal Failed)
'=========================================================================
on error resume next
if  MsiFileName <> "" then
err.clear()
if   not Failed then
oMsi.commit()
VbsCheck "Commiting the MSI prior to close : " & MsiFileName
else
if  CommitOnError then
oMsi.commit()
VbsCheck "Commiting the failed MSI for debugging : " & MsiFileName
end if
end if
set oMsi = Nothing
MsiFileName = ""
end if
end sub


'=========================================================================
sub SqlOpenExec(ByVal Sql)
'=========================================================================
on error resume next
set oView = oMsi.OpenView(Sql)
VbsCheck "Opening View - " & Sql
oView.Execute
VbsCheck "Executing View - " & Sql
end sub


'=========================================================================
function SqlViewFetch()
'=========================================================================
on error resume next
set SqlViewFetch = oView.Fetch()
VbsCheck "Fetching a record"
end function


'=========================================================================
sub SqlViewClose()
'=========================================================================
on error resume next
oView.close
VbsCheck "Closing a view"
set oView = Nothing
end sub


'=========================================================================
sub SqlExec(ByVal Sql)
'=========================================================================
on error resume next
SqlOpenExec(Sql)
SqlViewClose()
end sub


'=========================================================================
function TableExists(ByVal TableName)
'=========================================================================
on error resume next
dim SQL, oRecord
SQL = "SELECT * FROM `_Tables` WHERE Name= '" & TableName & "'"
SqlOpenExec(Sql)
set oRecord = SqlViewFetch()
if  oRecord is Nothing then
TableExists = false
else
TableExists = true
end if
set oRecord = Nothing
SqlViewClose()
end function


'=========================================================================
function ErrorTemplate(ByVal ErrorNumber)
'=========================================================================
on error resume next
ErrorTemplate = ""
dim Libraries, LibNum, Library, LibStream, Line, LineBits
Libraries = split("C:\Programme\MakeMsi\ErrorTemplates.TXT", ";")
for LibNum = 0 to ubound(Libraries)
Library = trim( Libraries(LibNum) )
if  Library <> "" then
if  oFS.FileExists(Library) then
set LibStream = oFS.OpenTextFile(Library, ForReading)
do  while LibStream.AtEndOfStream <> true
Line = trim(LibStream.ReadLine())
Line = replace(Line, chr(9), " ")
LineBits = split(Line, " ", 2)
if  ubound(LineBits) = 1 then
if  LineBits(0) = ErrorNumber then
ErrorTemplate = LineBits(1)
ErrorTemplate = replace(ErrorTemplate, "\n", vbCRLF)
LibStream.close
exit function
end if
end if
loop
LibStream.close
end if
end if
next


err.clear()
dim SQL, oErrView, oErrRecord
SQL = "SELECT * FROM `Error` WHERE `Error` = " & ErrorNumber
set oErrView = oMsi.OpenView(Sql)
oErrView.Execute
if  err.number = 0 then
set oErrRecord = oErrView.Fetch()
if not (oErrRecord is Nothing) then
ErrorTemplate = oErrRecord.StringData(2)
end if
end if
oErrView.close
set oErrRecord = Nothing
set oErrView   = Nothing
end function


'=====================================================================
sub CreateDir(byVal DirName)
'=====================================================================
if  DirName = "" then exit sub
on error resume next
dim ParentDir : ParentDir = oFS.GetParentFolderName(DirName)
if  not oFS.FolderExists(ParentDir) then
CreateDir ParentDir
end if
if  not oFS.FolderExists(DirName) then
oFS.CreateFolder DirName
VbsCheck("Could not create the directory """ & DirName & """!")
end if
end sub


'=========================================================================
sub DeleteDir(ByVal DirName)
'=========================================================================
on error resume next
if  DirName = "" then exit sub
if  oFS.FolderExists(DirName) then
oFS.DeleteFolder(DirName)
VbsCheck("Could not delete the directory """ & DirName & """!")
end if
end sub


'=========================================================================
sub DeleteFile(ByVal FileName)
'=========================================================================
on error resume next
if oFs.FileExists(FileName) then
oFs.DeleteFile(FileName)
VbsCheck("Could not delete the file """ & FileName & """!")
end if
end sub


'=========================================================================
sub SummaryOpen()
'=========================================================================
on error resume next
set oSummary = oMsi.SummaryInformation(99)
VbsCheck "Opening summary information"
end sub


'=========================================================================
sub SummaryItem(ByVal SummaryNumber, ByVal SummaryValue)
'=========================================================================
on error resume next
SummaryOpen()
oSummary.Property(SummaryNumber) = SummaryValue
if   err.number <> 0 and not IsEmpty(SummaryValue) then
VbsCheck "Setting summary item #" & SummaryNumber & " = " & SummaryValue
end if
SummaryClose()
end sub


'=========================================================================
sub SummaryClose()
'=========================================================================
on error resume next
oSummary.persist()
VbsCheck "Writing summary changes"
set oSummary = Nothing
end sub


'=========================================================================
function MkObjectWithHelp(ByVal AutomationClass, ByVal Help)
'=========================================================================
on error resume next
set MkObjectWithHelp = wscript.CreateObject(AutomationClass)
dim Msg : Msg = "Loading the automation class """ & AutomationClass & """"
if   Help <> "" then
Msg = Msg & vbCRLF & vbCRLF & help
end if
VbsCheck Msg
end function


'=========================================================================
function MkObject(ByVal AutomationClass)
'=========================================================================
set MkObject = MkObjectWithHelp(AutomationClass, "")
end function


'=========================================================================
function Title(Line1)
'=========================================================================
Title = Line1 & vbCRLF & string(len(Line1), "~")
end function


'=========================================================================
function Elapsed()
'=========================================================================
Elapsed = timer() - StartTime
if  Elapsed < 0 then
Elapsed = Elapsed + (60*60*24)
end if
Elapsed = round(Elapsed, 1)
end function


'=========================================================================
sub ViewFile(TheFile)
'=========================================================================
on error resume next
oShell.Run "notepad.exe """ &  TheFile & """", 1, false
end sub


'============================================================================
function ShortName(oFileOrFolder, AbortOnError)
'============================================================================
ShortName = oFileOrFolder.ShortName
dim Bits83, WinBug
WinBug = ""
Bits83 = split(ShortName, ".")
if  ubound(Bits83) > 1 then
WinBug = "More than 1 dot"
else
if  len(Bits83(0)) > 8 then
WinBug = "Base more than 8 characters long"
else
if  ubound(Bits83) = 1 then
if  len(Bits83(1)) > 3 then
WinBug = "Extension more than 3 characters long"
end if
end if
end if
end if
if  WinBug <> "" then
if  not AbortOnError then
ShortName = ""
else
dim ExtraText : ExtraText = ""
say ""
say string(78, "=")
say "We have detected a problem with getting 8.3 formatted filenames..."
say "Checking registry to see if NTFS 8.3 names are currently turned off..."
say "Reading: " & RegNtfs83NamesTurnedOff
on error resume next
dim TurnedOff : TurnedOff = oShell.RegRead(RegNtfs83NamesTurnedOff)
if  err.number <> 0 then
say ""
Say "Can't determine whether or not NTFS 8.3 names are turned off. Reason: 0x" & hex(err.number) & " - " & err.description
else
say "  Value: " & TurnedOff
say ""
say ""
if  cint(TurnedOff) <> 0 then
ExtraText = "ERROR: NTFS shortnames ARE turned off in the Windows Registry..."
Say ExtraText
ExtraText = vbCRLF & vbCRLF & ExtraText
else
Say "NTFS shortnames are not turned off." & vbCRLF
Say "FYI: This setting only affects files created after any change was made..."
end if
end if
say string(78, "=")
say ""
error("Detected a Windows bug in the handling of the "".ShortName"" attribute" & vbCRLF & "of a file/folder object.  It doesn't contain a valid 8.3 formatted filename!" & vbCRLF & vbCRLF & "GOT 8.3  : """ & ShortName & """" & vbCRLF & "The Issue: "   & WinBug & vbCRLF & "4 File   : """ & oFileOrFolder.Path & """" & ExtraText)
end if
end if
end function


'============================================================================
function AddComma2Long(ByVal TheInteger)
'============================================================================
'AddComma2Long = FormatNumber(clng(TheInteger), 0, True, False, True)
AddComma2Long = FormatNumber(cdbl(TheInteger), 0, True, False, True)
end function


'============================================================================
function Pad(ByVal Unpadded, ByVal ItsLength, byVal PadChar)
'============================================================================
dim Lng: Lng = len(Unpadded)
if  Lng >= ItsLength then
Pad = Unpadded
else
Pad = string(ItsLength-Lng, PadChar) & Unpadded
end if
end function


'=========================================================================
sub Say(What)
'=========================================================================
wscript.echo What
end sub


'=========================================================================
sub MmDebug(What)
'=========================================================================
wscript.echo "DEBUG: " & What
end sub


'=========================================================================
function GetAmPmTime()
'=========================================================================
GetAmPmTime = FormatDateTime(Now(), vbLongTime)     'doesn't guarantee am/pm, fix later
end function


'=========================================================================
sub VbsQuit(Rc)
' 1. Return code processing under 95/98/ME completely flakely
' 2. Return code still can't be trusted under NT/2000/XP (for example if
'    VBSCRIPT traps.
' 3. Return code lost with "TEE" type programs in any case
'=========================================================================
on error resume next
Need83NameEnd()
dim oRcStream
set oRcStream = oFS.CreateTextFile("Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector\out\installscript.mm\Log\VbsRc.TXT", true)
oRcStream.WriteLine Rc
oRcStream.close
wscript.quit Rc
end sub


'=========================================================================
sub Error(What)
'=========================================================================
Dying = true
ErrorPrefix()
say ""
say Title("REASON")
say What & chr(7) & chr(7)
MsiClose(true)
VbsQuit 219
end sub


'=========================================================================
sub ErrorPrefix()
'=========================================================================
say ""
say ""
say string(78, "#")
say string(28, "#") & "[ FATAL PASS " & Pass & " ERROR ]" & string(28, "#")
say string(78, "#")
say "Built from: Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector\installscript.mm"
say ".MM Locn  : " & MmLL
say ".MM Cmd   : " & MmLT
if  MmID <> "" then
say ".MM ID    : " & MmID & "  (location in ""out\installscript.mm\Log\Pass1+2.vbs"")"
end if
if  CurrentTable <> "" then
say "In TABLE  : " & CurrentTable
end if
end sub


'=========================================================================
sub VbsCheck(ByVal Message)
'=========================================================================
if  err.number <> 0 then
if  not MsiErrorIgnore then
dim ErrNumb, ErrDesc, ErrSrc
ErrNumb = err.number
ErrDesc = err.description
ErrSrc  = err.source
dim DumpRec : DumpRec = false
if  left(Message, 1) = "~" then
DumpRec = true
Message = mid(Message, 2)
end if
if  Dying then
say "Already Dying..."
say "  -> " & Message
exit sub
end if
Dying =  true
ErrorPrefix()
say "Doing     : " & Message
say ""
say Title("VBS RETURNS")
say "Error #   : 0x" & hex(ErrNumb) & " (" & ErrNumb & ")"
if  ErrSrc = "" then
say "Error Src : No source available (VB bug?)..."
else
say "Error Src : " & ErrSrc
end if
if  ErrDesc = "" then
say "Error Desc: No description available (VB bug?)..."
else
say "Error Desc: " & ErrDesc
end if
on error resume next
dim oMsiErrRec
err.clear()
set oMsiErrRec = oInstaller.LastErrorRecord
if  err.number = 0 then
if  not oMsiErrRec is nothing then
dim MsiErrCode : MsiErrCode = oMsiErrRec.StringData(1)
say ""
say Title("MSI ERROR #" & MsiErrCode & " (see the Windows Installer documentation)")
dim TemplateText : TemplateText = ErrorTemplate(MsiErrCode)
if  TemplateText = "" then
dim Pn, T
T = "The ""Error"" table does not contain a template for this message!" & vbCRLF & "Error parameters (non-blank) are:" & vbCRLF & vbCRLF
for Pn = 1 to 20
if  oMsiErrRec.StringData(Pn) <> "" then
T = T & "  #" & Pn & " = [" & Pn & "]" & vbCRLF
end if
next
TemplateText = T
end if
oMsiErrRec.StringData(0) = TemplateText
say oMsiErrRec.FormatText()
end if
end if
dim DumpedRecord
if  DumpRec then
DumpedRecord = DumpRecord()
end if
if  CurrentTable <> "" then
if  not TableExists(CurrentTable) then
say ""
say "Note that the """ & CurrentTable & """ table does not currently exist!"
end if
end if
if  DumpRec then
say ""
say DumpedRecord         'Info captured above!
end if
MsiClose(true)
say  chr(7) & chr(7)
VbsQuit 999
end if
end if
end sub






'=========================================================================
sub SetupRowValidationExclusionList_1()
'=========================================================================
redim preserve RowValidationExclusions(2)
redim preserve  RowValidationExclusions4Human(2)
RowValidationExclusions(0) = "|22|" : RowValidationExclusions4Human(0) = "-MISSINGDATA"

RowValidationExclusions(1) = "" : RowValidationExclusions4Human(1) = ""

RowValidationExclusions(2) = "|22|Sequence:05|" : RowValidationExclusions4Human(2) = "-MISSINGDATA -Sequence:UNDERFLOW"


end sub


'=========================================================================
sub SimpleTestToDetectInCompleteVbscriptForPass1()
'=========================================================================
'--- Doesn't need to do anything -------------------------------
end sub
 




'=========================================================================
sub SecondPassProcessing()
'=========================================================================
Say "Opening the MSI ""Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector\out\installscript.mm\MSI\setup.msi"""
MsiOpen "Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector\out\installscript.mm\MSI\setup.msi", msiOpenDatabaseModeDirect, true



MmID = "@VBS0846"

MmID = "@VBS0847"
 

MmID = "@VBS0848"

MmID = "@VBS0849"
TableNowMk "Directory"

MmID = "@VBS0850"
RowPrepare 3

MmID = "@VBS0851"
oRec.StringData(1) = "ProgramFilesFolder"
oRec.StringData(2) = "TARGETDIR"
oRec.StringData(3) = ".:ProgFile|Program Files"
ValidateFIELD(1)
RowUpdate()

MmID = "@VBS0852"
TableNow ""

MmID = "@VBS0853"
TableNowMk "Directory"
 

MmID = "@VBS0854"
RowPrepare 3

MmID = "@VBS0855"
oRec.StringData(1) = "_PROGRAMFILESFOLDER_MAKEMSI_PACKAGE_DOCUMENTATION"
oRec.StringData(2) = "ProgramFilesFolder"
oRec.StringData(3) = MakeSfnLfn("ProgramFilesFolder", "MAKEMSI Package Documentation")
ValidateFIELD(1)
RowUpdate()

MmID = "@VBS0856"
TableNow ""

MmID = "@VBS0857"

MmID = "@VBS0858"
TableNowMk "Directory"
 

MmID = "@VBS0859"
RowPrepare 3

MmID = "@VBS0860"
oRec.StringData(1) = "_PROGRAMFILESFOLDER_MAKEMSI_PACKAGE_DOCUMENTATION_MY_COMPANY"
oRec.StringData(2) = "_PROGRAMFILESFOLDER_MAKEMSI_PACKAGE_DOCUMENTATION"
oRec.StringData(3) = MakeSfnLfn("_PROGRAMFILESFOLDER_MAKEMSI_PACKAGE_DOCUMENTATION", "My Company")
ValidateFIELD(1)
RowUpdate()

MmID = "@VBS0861"
TableNow ""

MmID = "@VBS0862"

MmID = "@VBS0863"
TableNowMk "Directory"
 

MmID = "@VBS0864"
RowPrepare 3

MmID = "@VBS0865"
oRec.StringData(1) = "MAKEMSI_DOCO"
oRec.StringData(2) = "_PROGRAMFILESFOLDER_MAKEMSI_PACKAGE_DOCUMENTATION_MY_COMPANY"
oRec.StringData(3) = MakeSfnLfn("_PROGRAMFILESFOLDER_MAKEMSI_PACKAGE_DOCUMENTATION_MY_COMPANY", "My Name")
ValidateFIELD(1)
RowUpdate()

MmID = "@VBS0866"
TableNow ""
 

MmID = "@VBS0867"

MmID = "@VBS0868"
TableNowMk "Component"

MmID = "@VBS0869"
RowPrepare 6

MmID = "@VBS0870"
oRec.StringData(1) = "MAKEMSI_Documentation"
oRec.StringData(2) = GuidMake("")
oRec.StringData(3) = "MAKEMSI_DOCO"
oRec.IntegerData(4) = msidbComponentAttributesLocalOnly
oRec.StringData(5) = ""
oRec.StringData(6) = ""
ValidateFIELD(1)
RowUpdate()

MmID = "@VBS0871"


MmID = "@VBS0872"
TableNowMk "FeatureComponents"

MmID = "@VBS0873"
RowPrepare 2

MmID = "@VBS0874"
oRec.StringData(1) = "ALL.1.0.0.UCS_AD_Connector"
oRec.StringData(2) = "MAKEMSI_Documentation"
ValidateNEW(0)
RowUpdate()

MmID = "@VBS0875"
TableNow ""

 

MmID = "@VBS0876"
CurrentFile="Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector\out\installscript.mm\MSI\setup.hta"
CurrentFileKey="MAKEMSI_Documentation"
CurrentFileNameSL="MSIRPT.HTA|setup.hta"
CurrentFileVersion=""

MmID = "@VBS0877"
TableNowMk "File"

MmID = "@VBS0878"
RowPrepare 8

MmID = "@VBS0879"
oRec.StringData(1) = CurrentFileKey
oRec.StringData(2) = "MAKEMSI_Documentation"
oRec.StringData(3) = CurrentFileNameSL
oRec.IntegerData(4) = 68724
oRec.StringData(5) = CurrentFileVersion
oRec.IntegerData(7) = FileAttribs(msidbFileAttributesVital, 0)
oRec.StringData(6) = "1033"
oRec.IntegerData(8) = 0
ValidateNEW(2)
RowUpdate()

MmID = "@VBS0880"
TableNow ""

MmID = "@VBS0881"
TableNowMk "_MAKEMSI_FileSource"

MmID = "@VBS0882"
RowPrepare 4

MmID = "@VBS0883"
oRec.StringData(1) = CurrentFileKey
oRec.StringData(2) = CurrentFile
oRec.StringData(3) = "2010-09-28"
oRec.StringData(4) = "14:58:06"
ValidateNEW(0)
RowUpdate()

MmID = "@VBS0884"
TableNow ""

MmID = "@VBS0885"
TableNowMk "Component"

MmID = "@VBS0886"
RowsPrepare "`Component` = 'MAKEMSI_Documentation'"
RecCnt = 0
do
set oRec = SqlViewFetch()
if oRec is Nothing then exit DO
RecCnt = RecCnt + 1

MmID = "@VBS0887"
oRec.IntegerData(4) = (oRec.IntegerData(4) AND NOT msidbComponentAttributesRegistryKeyPath)
oRec.StringData(6) = "MAKEMSI_Documentation"
ValidateFETCH(1)
RowsREPLACE()
loop
SqlViewClose()
if not RecCnt =1 then Error("Found " & RecCnt & " record(s), we expected ""=1"".  The SQL WHERE clause was:" & vbCRLF & vbCRLF & "`Component` = 'MAKEMSI_Documentation'")

MmID = "@VBS0888"
TableNow ""
  

MmID = "@VBS0889"

MmID = "@VBS0890"
TableNowMk "CustomAction"
 

MmID = "@VBS0891"
RowPrepare 5

MmID = "@VBS0892"
oRec.StringData(4) = "file:///[!MAKEMSI_Documentation]"
oRec.IntegerData(2) = &H0033
oRec.StringData(1) = "PropertyCa03_ARPREADME"
oRec.StringData(3) = "ARPREADME"
ValidateFIELD(1)
RowUpdate()

MmID = "@VBS0893"
TableNow ""
SeqNo = GetSeqNumber("InstallExecuteSequence", "CostFinalize-", 1)



'######################################################################
MmLL = "installscript.mm(54)"
MmLT = "#{ SET ""SeqTable={ }<??cb_SeqTables>"""
'######################################################################


MmID = "@VBS0894"
TableNowMk "InstallExecuteSequence"

MmID = "@VBS0895"
RowPrepare 3

MmID = "@VBS0896"
oRec.StringData(1) = "PropertyCa03_ARPREADME"
oRec.StringData(2) = ""
oRec.IntegerData(3) = SeqNo
ValidateFIELD(1)
RowUpdate()

MmID = "@VBS0897"
TableNow ""




'######################################################################
MmLL = "installscript.mm(54)"
MmLT = "#evaluate ^^ ^<$Rexx4UpdateMmLocation >^"
'######################################################################


MmID = "@VBS0898"




pc_COMPILE_CABDDF_Compress          = "ON"
pc_COMPILE_CABDDF_CompressionType   = "LZX"
pc_COMPILE_CABDDF_CompressionLevel  = "7"
pc_COMPILE_CABDDF_CompressionMemory = "21"
pc_COMPILE_CABDDF_ClusterSize       = "4096"
pc_COMPILE_CAB_FILE_NAME            = "MM*"
pc_CompileMsi "Compiling the documentation that MAKEMSI generated", ""





MsiClose(false)
say ""
end sub


'=========================================================================
sub SetupRowValidationExclusionList_2()
'=========================================================================
SetupRowValidationExclusionList_1()     'Pass 2 needs to add to those already known for pass 1...


redim preserve RowValidationExclusions(2)
redim preserve  RowValidationExclusions4Human(2)

end sub



'=========================================================================
sub SimpleTestToDetectInCompleteVbscriptForPass2()
'=========================================================================
'--- Doesn't need to do anything -------------------------------
end sub
