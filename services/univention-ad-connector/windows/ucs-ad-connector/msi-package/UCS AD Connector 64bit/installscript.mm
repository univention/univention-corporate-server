;----------------------------------------------------------------------------
;--- Global Definitions						        -----
;----------------------------------------------------------------------------
#define VALID_MSIVAL2_DIR C:\Programme\MsiVal2  ;;Used before loading MSI header
;--- Include MAKEMSI support (with my customisations and MSI branding) ------
#define VER_FILENAME.VER  version.Ver      ;;I only want one VER file for all samples! (this line not actually required in "tryme.mm")
#include "ME.MMH"
;;;; Disabling Dialog??
;--- Prevent "UISAMPLE" trying to manipulate the dialog deleted below -------
#define UISAMPLE_DISABLE_TYPICAL_SETUP N
#define REMOVED_LicenseAgreementDlg N
#define "ME.MMH"

;--- Remove the dialog ------------------------------------------------------
<$DialogRemove "SetupTypeDlg"> ;; do not ask for Typical Custom complete
<$DialogRemove "LicenseAgreementDlg"> ;;ignore lizenz.rtf File
;----------------------------------------------------------------------------

;--- Want to debug (not common) ---------------------------------------------
;#debug on
;#Option DebugLevel=^NONE, +OpSys^
;--- Define default location where file should install and add files --------

;Installdir:
<$DirectoryTree Key="INSTALLDIR" Dir="c:\Windows\UCS-AD-Connector" CHANGE="\" PrimaryFolder="Y">




;----------------------------------------------------------------------------
;--- what should the installation do?					-----
;----------------------------------------------------------------------------

;Example for Filecopy:
<$Files "files\Programme\UCS-AD-Connector\*.*" DestDir="INSTALLDIR">
<$Files "files\temp\*.*" DestDir="[TempFolder]">

;----------------------------------------------------------------------------
;--- Add a registry entry (let it create a component - GUID not fixed!) -----
;----------------------------------------------------------------------------
; <$Registry HKEY="LOCAL_MACHINE" Key="SOFTWARE\testkey" Value="testkey_script_example.com">

;----------------------------------------------------------------------------
;--- start a batch script				                -----
;----------------------------------------------------------------------------
#(
    ;--- Run after install, ignore return code and don't wait for completion ---
   <$ExeCa
             EXE='[TempFolder]ucs-ad-connector-service.cmd' Args=^"MsgBox Title" "MsgBox text..."^
         WorkDir="TempFolder"
             SEQ="InstallFinalize-"   Type="immediate ASync AnyRc"
      Condition="<$CONDITION_INSTALL_ONLY>"
   >
  #)
