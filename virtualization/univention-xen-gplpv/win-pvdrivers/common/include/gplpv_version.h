#ifndef GPLPV_VERSION_H
#define GPLPV_VERSION_H

#define EXPAND(x) STRINGIFY(x)
#define STRINGIFY(x) #x

#ifdef BUILD_NUMBER
  #define VER_FILEVERSION             0,10,0,BUILD_NUMBER
  #define VER_FILEVERSION_STR         "GPLPV 0.10.0." EXPAND(BUILD_NUMBER)
#else
  #define VER_FILEVERSION             0,0,0,0
  #define VER_FILEVERSION_STR         "GPLPV Unversioned"
#endif

#endif
