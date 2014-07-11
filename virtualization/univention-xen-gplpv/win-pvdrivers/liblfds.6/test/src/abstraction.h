/***** defines *****/
#if (defined _WIN32 && defined _MSC_VER && !defined WIN_KERNEL_BUILD)
  /* TRD : any Windows (user-mode) on any CPU with the Microsoft C compiler

           _WIN32             indicates 64-bit or 32-bit Windows
           _MSC_VER           indicates Microsoft C compiler
           !WIN_KERNEL_BUILD  indicates Windows user-mode
  */

  #include <windows.h>
  typedef HANDLE              thread_state_t;
  typedef DWORD               thread_return_t;
  #define CALLING_CONVENTION  WINAPI
#endif

#if (defined _WIN32 && defined _MSC_VER && defined WIN_KERNEL_BUILD)
  /* TRD : any Windows (kernel-mode) on any CPU with the Microsoft C compiler

           _WIN32            indicates 64-bit or 32-bit Windows
           _MSC_VER          indicates Microsoft C compiler
           WIN_KERNEL_BUILD  indicates Windows kernel
  */

  #include <wdm.h>
  typedef HANDLE              thread_state_t;
  typedef VOID                thread_return_t;
  #define CALLING_CONVENTION  
#endif

#if (defined __unix__ && __GNUC__)
  /* TRD : any UNIX on any CPU with GCC

           __unix__   indicates Solaris, Linux, HPUX, etc
           __GNUC__   indicates GCC
  */

  #include <unistd.h>
  #include <pthread.h>
  typedef pthread_t           thread_state_t;
  typedef void *              thread_return_t;
  #define CALLING_CONVENTION  
#endif

typedef thread_return_t (CALLING_CONVENTION *thread_function_t)( void *thread_user_state );

/***** public prototypes *****/
unsigned int abstraction_cpu_count( void );
int abstraction_thread_start( thread_state_t *thread_state, unsigned int cpu, thread_function_t thread_function, void *thread_user_state );
void abstraction_thread_wait( thread_state_t thread_state );

