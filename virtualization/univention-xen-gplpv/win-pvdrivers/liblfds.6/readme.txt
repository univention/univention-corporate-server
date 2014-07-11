introduction
============
Welcome to liblfds, a portable, license-free, lock-free data structure
library written in C.

platforms
=========
Currently liblfds out-of-the-box supports;

Operating System  CPU         Toolset
================  ==========  =======
Windows 64-bit    IA64 & x64  1. Microsoft Visual Studio 2008
                              2. Microsoft Windows SDK and GNUmake >= 3.8.1

Windows 32-bit 	  x64 & x86   1. Microsoft Visual Studio 2008
                              2. Visual C++ 2008 Express Edition
                              3. Microsoft Windows SDK and GNUmake >= 3.8.1

Windows Kernel    IA64, x64,  1. Windows Driver Kit >= 7.0.0
                  x86

Linux 64-bit      x64         1. GCC >= 4.1.0 and GNUmake >= 3.8.1

Linux 32-bit      x64, x86,   1. GCC >= 4.1.0 and GNUmake >= 3.8.1 
                  ARM

data structures
===============
Currently liblfds provides the following;

* Freelist
* Queue
* Ringbuffer
* Singly linked list (logical delete only)
* Stack

liblfds on-line
===============
On the liblfds home page, you will find the blog, a bugzilla, a forum, a
wikipedia and the current and all historical source releases.

The wikipedia contains comprehensive documentation for development,
building, testing and porting.

http://www.liblfds.org

license
=======
There is no license.  You are free to use this code in any way.

building
========
On Windows, depending on your target platform, one of the following toolchains
is required;

    * Microsoft Visual Studio 2008 (expensive)
    * Visual C++ 2008 Express Edition (free, but no 64 bit support)
    * Microsoft Windows SDK (free, no GUI, has 64 bit support) and GNUmake 3.81 

On Windows (kernel-mode), the following toolchain is required; 

    * Windows Driver Kit 7.0.0 or later

On Linux, the following toolchain is required;

    * gcc 4.1.0 or later and GNUmake 3.81 

For documentation, see the building guide in the wikipedia.

using
=====
Once built, there is a single header file, /inc/liblfds.h, which you must include
in your source code, and a single library file /bin/liblfds.*, where the suffix
depends on your platform and your build choice (static or dynamic), to which,
if statically built, you must link directly or, if dynamically built, you must
arrange your system such that the library can be found by the loader at run-time. 

testing
=======
The library comes with a command line test and benchmark program.  This
program requires threads.  As such, it is only suitable for platforms providing
thread support and which can execute a command line binary.  Currently this
means the test and benchmark program works for all platforms except the Windows
Kernel.

For documentation, see the testing and benchmarking guide in the wikipedia.

porting
=======
Both the test program and liblfds provide an abstraction layer which acts to
mask platform differences. Porting is the act of implementing on your platform
the functions which make up the abstraction layers.  You do not need to port
the test program to port liblfds, but obviously it is recommended, so you can
test your port.

To support liblfds, your platform must support either contigious double-word
compare-and-swap (e.g. x86/x64) or contigious double-word load-link/conditional-store
where normal loads cannot occur inside the LL/CS pair (e.g. ARM) or single word
load-link/conditional-store where normal loads can occur inside the LL/CS pair.

For documentation, see the porting guide in the wikipedia.

release history
===============
release 1, 25th September 2009, svn revision 1574.
  - initial release

release 2, 5th October 2009, svn revision 1599.
  - added abstraction layer for Windows kernel
  - minor code tidyups/fixes

release 3, 25th October 2009, svn revision 1652.
  - added singly linked list (logical delete only)
  - minor code tidyups/fixes

release 4, 7th December 2009, svn revision 1716.
  - added ARM support
  - added benchmarking functionality to the test program
  - fixed a profound and pervasive pointer
    decleration bug; earlier releases of liblfds
    *should not be used*

release 5, 19th December 2009, svn revision 1738.
  - fixed subtle queue bug, which also affected ringbuffer
    and caused data re-ordering under high load
  - added benchmarks for freelist, ringbuffer and stack

release 6, 29th December 2009, svn revision 1746.
  - fixed two implementation errors, which reduced performance,
    spotted by Codeplug from "http://cboard.cprogramming.com".
 
