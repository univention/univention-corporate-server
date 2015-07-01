Wir verwenden die von Fedora/RedHat gebauten und signierten Treiber:
<https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/>

Das ISO-Image wird angepasst, um folgende konsistente Struktur zu haben:
    /XP     Treiber für Windows XP
    /WNET   Treiber für Windows 2003
    /VISTA  Treiber für Windows Vista und Windows Server 2008 (Long Horn)
    /WIN7   Treiber für Windows 7
        */X86   Treiber für 32-Bit Version
        */AMD64 Treiber für 64-Bit Version
            */*/NETKVM*     Treiber für Netzwerk
            */*/VIOSTOR*    Treiber für Speichermedien
            */*/VIOSER*     Treiber für serielle Schnittstelle
            */*/BALLOON*    Treiber für Speicher-Balooning
            */*/BLNSVR*     Daemon für Speicher-Balooning

Treiber für Windows 8 stehen noch nicht zur Verfügung.
