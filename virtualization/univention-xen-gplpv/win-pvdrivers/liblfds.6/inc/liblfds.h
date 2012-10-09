#ifndef __LIBLFDS_H

  /***** library header *****/
  #define LIBLFDS_RELEASE_NUMBER 6




  /***** abstraction *****/

  /***** defines *****/
  #if (defined _WIN64 && defined _MSC_VER && !defined WIN_KERNEL_BUILD)
    // TRD : 64-bit Windows user-mode with the Microsoft C compiler, any CPU
    #include <assert.h>
    #include <stdio.h>
    #include <stdlib.h>
    #include <windows.h>
    #include <intrin.h>
    typedef unsigned __int64      atom_t;
    #define INLINE                extern __forceinline
    #define ALIGN(alignment)      __declspec( align(alignment) )
    #define ALIGN_SINGLE_POINTER  8
    #define ALIGN_DOUBLE_POINTER  16
  #endif

  #if (!defined _WIN64 && defined _WIN32 && defined _MSC_VER && !defined WIN_KERNEL_BUILD)
    // TRD : 32-bit Windows user-mode with the Microsoft C compiler, any CPU
    #include <assert.h>
    #include <stdio.h>
    #include <stdlib.h>
    #include <windows.h>
    #include <intrin.h>
    typedef unsigned long int     atom_t;
    #define INLINE                extern __forceinline
    #define ALIGN(alignment)      __declspec( align(alignment) )
    #define ALIGN_SINGLE_POINTER  4
    #define ALIGN_DOUBLE_POINTER  8

    // TRD : this define is documented but missing in Microsoft Platform SDK v7.0
    #define _InterlockedCompareExchangePointer(destination, exchange, compare) _InterlockedCompareExchange((volatile long *) destination, (long) exchange, (long) compare)
  #endif

  #if (defined _WIN64 && defined _MSC_VER && defined WIN_KERNEL_BUILD)
    // TRD : 64-bit Windows kernel with the Microsoft C compiler, any CPU
    #include <assert.h>
    #include <stdio.h>
    #include <stdlib.h>
    #include <wdm.h>
    typedef unsigned __int64      atom_t;
    #define INLINE                extern __forceinline
    #define ALIGN(alignment)      __declspec( align(alignment) )
    #define ALIGN_SINGLE_POINTER  8
    #define ALIGN_DOUBLE_POINTER  16
  #endif

  #if (!defined _WIN64 && defined _WIN32 && defined _MSC_VER && defined WIN_KERNEL_BUILD)
    // TRD : 32-bit Windows kernel with the Microsoft C compiler, any CPU
    #include <assert.h>
    #include <stdio.h>
    #include <stdlib.h>
    #include <wdm.h>
    typedef unsigned long int     atom_t;
    #define INLINE                extern __forceinline
    #define ALIGN(alignment)      __declspec( align(alignment) )
    #define ALIGN_SINGLE_POINTER  4
    #define ALIGN_DOUBLE_POINTER  8

    // TRD : this define is documented but missing in Microsoft Platform SDK v7.0
    #define _InterlockedCompareExchangePointer(destination, exchange, compare) _InterlockedCompareExchange((volatile long *) destination, (long) exchange, (long) compare)
  #endif

  #if (defined __unix__ && defined __x86_64__ && __GNUC__)
    // TRD : any UNIX with GCC on x64
    #define _XOPEN_SOURCE 600
    #include <assert.h>
    #include <stdio.h>
    #include <stdlib.h>
    typedef unsigned long long int  atom_t;
    #define INLINE                  inline
    #define ALIGN(alignment)        __attribute__( (aligned(alignment)) )
    #define ALIGN_SINGLE_POINTER    8
    #define ALIGN_DOUBLE_POINTER    16
  #endif

  #if (defined __unix__ && defined __i686__ && __GNUC__)
    // TRD : any UNIX with GCC on x86
    #define _XOPEN_SOURCE 600
    #include <assert.h>
    #include <stdio.h>
    #include <stdlib.h>
    typedef unsigned long int     atom_t;
    #define INLINE                inline
    #define ALIGN(alignment)      __attribute__( (aligned(alignment)) )
    #define ALIGN_SINGLE_POINTER  4
    #define ALIGN_DOUBLE_POINTER  8
  #endif

  #if (defined __unix__ && defined __arm__ && __GNUC__)
    // TRD : any UNIX with GCC on ARM
    #define _XOPEN_SOURCE 600
    #include <assert.h>
    #include <stdio.h>
    #include <stdlib.h>
    typedef unsigned long int     atom_t;
    #define INLINE                inline
    #define ALIGN(alignment)      __attribute__( (aligned(alignment)) )
    #define ALIGN_SINGLE_POINTER  4
    #define ALIGN_DOUBLE_POINTER  8
  #endif

  /***** enums *****/
  enum data_structure_validity
  {
    VALIDITY_VALID,
    VALIDITY_INVALID_LOOP,
    VALIDITY_INVALID_MISSING_ELEMENTS,
    VALIDITY_INVALID_ADDITIONAL_ELEMENTS,
    VALIDITY_INVALID_TEST_DATA
  };

  /***** structs *****/
  struct validation_info
  {
    atom_t
      min_elements,
      max_elements;
  };

  /***** public prototypes *****/
  void abstraction_aligned_free( void *memory );
  void *abstraction_aligned_malloc( size_t size, size_t align_in_bytes );
  atom_t abstraction_cas( volatile atom_t *destination, atom_t exchange, atom_t compare );
  unsigned char abstraction_dcas( volatile atom_t *destination, atom_t *exchange, atom_t *compare );
  atom_t abstraction_increment( atom_t *value );





  /***** freelist *****/

  /***** enums *****/
  enum freelist_query_type
  {
    FREELIST_QUERY_ELEMENT_COUNT,
    FREELIST_QUERY_VALIDATE
  };

  /***** incomplete types *****/
  struct freelist_state;
  struct freelist_element;

  /***** public prototypes *****/
  int freelist_new( struct freelist_state **fs, atom_t number_elements, int (*user_data_init_function)(void **user_data, void *user_state), void *user_state );
  void freelist_delete( struct freelist_state *fs, void (*user_data_delete_function)(void *user_data, void *user_state), void *user_state );

  atom_t freelist_new_elements( struct freelist_state *fs, atom_t number_elements );

  struct freelist_element *freelist_pop( struct freelist_state *fs, struct freelist_element **fe );
  struct freelist_element *freelist_guaranteed_pop( struct freelist_state *fs, struct freelist_element **fe );
  void freelist_push( struct freelist_state *fs, struct freelist_element *fe );

  void *freelist_get_user_data_from_element( struct freelist_element *fe, void **user_data );
  void freelist_set_user_data_in_element( struct freelist_element *fe, void *user_data );

  void freelist_query( struct freelist_state *fs, enum freelist_query_type query_type, void *query_input, void *query_output );





  /***** queue *****/

  /***** enums *****/
  enum queue_query_type
  {
    QUEUE_QUERY_ELEMENT_COUNT,
    QUEUE_QUERY_VALIDATE
  };

  /***** incomplete types *****/
  struct queue_state;

  /***** public prototypes *****/
  int queue_new( struct queue_state **sq, atom_t number_elements );
  void queue_delete( struct queue_state *qs, void (*user_data_delete_function)(void *user_data, void *user_state), void *user_state );

  int queue_enqueue( struct queue_state *qs, void *user_data );
  int queue_guaranteed_enqueue( struct queue_state *qs, void *user_data );
  int queue_dequeue( struct queue_state *qs, void **user_data );

  void queue_query( struct queue_state *qs, enum queue_query_type query_type, void *query_input, void *query_output );





  /***** ringbuffer *****/

  /***** enums *****/
  enum ringbuffer_query_type
  {
    RINGBUFFER_QUERY_VALIDATE
  };

  /***** incomplete types *****/
  struct ringbuffer_state;

  /***** public prototypes *****/
  int ringbuffer_new( struct ringbuffer_state **rs, atom_t number_elements, int (*user_data_init_function)(void **user_data, void *user_state), void *user_state );
  void ringbuffer_delete( struct ringbuffer_state *rs, void (*user_data_delete_function)(void *user_data, void *user_state), void *user_state );

  struct freelist_element *ringbuffer_get_read_element( struct ringbuffer_state *rs, struct freelist_element **fe );
  struct freelist_element *ringbuffer_get_write_element( struct ringbuffer_state *rs, struct freelist_element **fe, int *overwrite_flag );

  void ringbuffer_put_read_element( struct ringbuffer_state *rs, struct freelist_element *fe );
  void ringbuffer_put_write_element( struct ringbuffer_state *rs, struct freelist_element *fe );

  void ringbuffer_query( struct ringbuffer_state *rs, enum ringbuffer_query_type query_type, void *query_input, void *query_output );





  /***** slist *****/

  /***** incomplete types *****/
  struct slist_state;
  struct slist_element;

  /***** public prototypes *****/
  int slist_new( struct slist_state **ss, void (*user_data_delete_function)(void *user_data, void *user_state), void *user_state );
  void slist_delete( struct slist_state *ss );

  struct slist_element *slist_new_head( struct slist_state *ss, void *user_data );
  struct slist_element *slist_new_next( struct slist_element *se, void *user_data );

  void slist_delete_element( struct slist_state *ss, struct slist_element *se );
  void slist_delete_all_elements( struct slist_state *ss );

  int slist_get_user_data_from_element( struct slist_element *se, void **user_data );
  int slist_set_user_data_in_element( struct slist_element *se, void *user_data );

  struct slist_element *slist_get_head( struct slist_state *ss, struct slist_element **se );
  struct slist_element *slist_get_next( struct slist_element *se, struct slist_element **next_se );
  struct slist_element *slist_get_head_and_then_next( struct slist_state *ss, struct slist_element **se );





  /***** stack *****/

  /***** enums *****/
  enum stack_query_type
  {
    STACK_QUERY_ELEMENT_COUNT
  };

  /***** incomplete types *****/
  struct stack_state;

  /***** public prototypes *****/
  int stack_new( struct stack_state **ss, atom_t number_elements );
  void stack_delete( struct stack_state *ss, void (*user_data_delete_function)(void *user_data, void *user_state), void *user_state );

  void stack_clear( struct stack_state *ss, void (*user_data_clear_function)(void *user_data, void *user_state), void *user_state );

  int stack_push( struct stack_state *ss, void *user_data );
  int stack_guaranteed_push( struct stack_state *ss, void *user_data );
  int stack_pop( struct stack_state *ss, void **user_data );

  void stack_query( struct stack_state *ss, enum stack_query_type query_type, void *query_input, void *query_output );





  #define __LIBLFDS_H

#endif

