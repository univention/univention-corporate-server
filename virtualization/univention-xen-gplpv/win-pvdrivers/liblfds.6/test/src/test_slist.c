#include "internal.h"





/****************************************************************************/
void test_slist( void )
{
  unsigned int
    loop,
    cpu_count;

  thread_state_t
    *thread_handles;

  struct slist_thread_start_state
    stss;

  /* TRD : 1. one head writer per CPU
           2. make one element, then one after writer per CPU
           3. make a list, then one list traverser per CPU
           4. one head writer and one list traverser per CPU
           5. make one element, then one after writer and one list traverser per CPU
           6. make a list, then one 100% deleter-traverser per CPU
           7. make a list, then one 25% deleter-traverser per CPU
           8. one head writer and one 100% deleter-traverse per CPU
           9. one head writer and one 25% deleter-traverse per CPU
           10. make one element, then one after writer and one 100% deleter-traverser per CPU
           11. make one element, then one after writer and one 25% deleter-traverser per CPU
           12. one head writer, one after writer, one traverser and one 25% deleter-traverser per CPU
  */

  cpu_count = abstraction_cpu_count();

  printf( "\n"
          "SList Test\n"
          "==========\n" );

  // TRD : 1. one head writer per CPU

  printf( "\n"
          "1. one head writer per CPU\n"
          "==========================\n" );

  slist_new( &stss.ss, NULL, NULL );
  stss.iteration_modulo = 1;
  stss.se = NULL;
  stss.duration = 1;

  thread_handles = (thread_state_t *) malloc( sizeof(thread_state_t) * cpu_count * 1 );

  for( loop = 0 ; loop < cpu_count ; loop++ )
    abstraction_thread_start( &thread_handles[loop], loop, slist_internal_thread_head_writer, &stss );

  for( loop = 0 ; loop < cpu_count ; loop++ )
    abstraction_thread_wait( thread_handles[loop] );

  slist_delete( stss.ss );

  free( thread_handles );

  // TRD : 2. make one element, then one after writer per CPU

  printf( "\n"
          "2. make one element, then one after writer per CPU\n"
          "==================================================\n" );

  slist_new( &stss.ss, NULL, NULL );
  stss.iteration_modulo = 1;
  stss.se = slist_new_head( stss.ss, (void *) NULL );
  stss.duration = 1;

  thread_handles = (thread_state_t *) malloc( sizeof(thread_state_t) * cpu_count * 1 );

  for( loop = 0 ; loop < cpu_count ; loop++ )
    abstraction_thread_start( &thread_handles[loop], loop, slist_internal_thread_after_writer, &stss );

  for( loop = 0 ; loop < cpu_count ; loop++ )
    abstraction_thread_wait( thread_handles[loop] );

  slist_delete( stss.ss );

  free( thread_handles );

  // TRD : 3. make a list, then one list traverser per CPU

  printf( "\n"
          "3. make a list, then one list traverser per CPU\n"
          "===============================================\n" );

  slist_new( &stss.ss, NULL, NULL );
  stss.iteration_modulo = 1;
  stss.se = NULL;
  stss.duration = 10;

  // TRD : small list so we get collisions
  for( loop = 0 ; loop < 10 ; loop++ )
    slist_new_head( stss.ss, (void *) 0 );

  thread_handles = (thread_state_t *) malloc( sizeof(thread_state_t) * cpu_count * 1 );

  for( loop = 0 ; loop < cpu_count ; loop++ )
    abstraction_thread_start( &thread_handles[loop], loop, slist_internal_thread_traverser, &stss );

  for( loop = 0 ; loop < cpu_count ; loop++ )
    abstraction_thread_wait( thread_handles[loop] );

  slist_delete( stss.ss );

  free( thread_handles );

  // TRD : 4. one head writer and one list traverser per CPU

  printf( "\n"
          "4. one head writer and one list traverser per CPU\n"
          "=================================================\n" );

  slist_new( &stss.ss, NULL, NULL );
  stss.iteration_modulo = 1;
  stss.se = NULL;
  stss.duration = 1;

  thread_handles = (thread_state_t *) malloc( sizeof(thread_state_t) * cpu_count * 2 );

  for( loop = 0 ; loop < cpu_count ; loop++ )\
  {
    abstraction_thread_start( &thread_handles[loop], loop, slist_internal_thread_head_writer, &stss );
    abstraction_thread_start( &thread_handles[loop+cpu_count], loop, slist_internal_thread_traverser, &stss );
  }

  for( loop = 0 ; loop < cpu_count * 2 ; loop++ )
    abstraction_thread_wait( thread_handles[loop] );

  slist_delete( stss.ss );

  free( thread_handles );

  // TRD : 5. make one element, then one after writer and one list traverser per CPU

  printf( "\n"
          "5. make one element, then one after writer and one list traverser per CPU\n"
          "=========================================================================\n" );

  slist_new( &stss.ss, NULL, NULL );
  stss.iteration_modulo = 1;
  stss.se = slist_new_head( stss.ss, (void *) NULL );
  stss.duration = 1;

  thread_handles = (thread_state_t *) malloc( sizeof(thread_state_t) * cpu_count * 2 );

  for( loop = 0 ; loop < cpu_count ; loop++ )\
  {
    abstraction_thread_start( &thread_handles[loop], loop, slist_internal_thread_after_writer, &stss );
    abstraction_thread_start( &thread_handles[loop+cpu_count], loop, slist_internal_thread_traverser, &stss );
  }

  for( loop = 0 ; loop < cpu_count * 2 ; loop++ )
    abstraction_thread_wait( thread_handles[loop] );

  slist_delete( stss.ss );

  free( thread_handles );

  // TRD : 6. make a list, then one 100% deleter-traverser per CPU

  printf( "\n"
          "6. make a list, then one 100%% deleter-traverser per CPU\n"
          "=======================================================\n" );

  slist_new( &stss.ss, NULL, NULL );
  stss.iteration_modulo = 1;
  stss.se = NULL;
  stss.duration = 1;

  for( loop = 0 ; loop < 10000 ; loop++ )
    slist_new_head( stss.ss, (void *) 0 );

  thread_handles = (thread_state_t *) malloc( sizeof(thread_state_t) * cpu_count * 1 );

  for( loop = 0 ; loop < cpu_count ; loop++ )
    abstraction_thread_start( &thread_handles[loop], loop, slist_internal_thread_deleter_traverser, &stss );

  for( loop = 0 ; loop < cpu_count ; loop++ )
    abstraction_thread_wait( thread_handles[loop] );

  slist_delete( stss.ss );

  free( thread_handles );

  // TRD : 7. make a list, then one 25% deleter-traverser per CPU

  printf( "\n"
          "7. make a list, then one 25%% deleter-traverser per CPU\n"
          "======================================================\n" );

  slist_new( &stss.ss, NULL, NULL );
  stss.iteration_modulo = 4;
  stss.se = NULL;
  stss.duration = 1;

  for( loop = 0 ; loop < 10000 ; loop++ )
    slist_new_head( stss.ss, (void *) 0 );

  thread_handles = (thread_state_t *) malloc( sizeof(thread_state_t) * cpu_count * 1 );

  for( loop = 0 ; loop < cpu_count ; loop++ )
    abstraction_thread_start( &thread_handles[loop], loop, slist_internal_thread_deleter_traverser, &stss );

  for( loop = 0 ; loop < cpu_count ; loop++ )
    abstraction_thread_wait( thread_handles[loop] );

  slist_delete( stss.ss );

  free( thread_handles );

  // TRD : 8. one head writer and one 100% deleter-traverse per CPU

  printf( "\n"
          "8. one head writer and one 100%% deleter-traverse per CPU\n"
          "========================================================\n" );

  slist_new( &stss.ss, NULL, NULL );
  stss.iteration_modulo = 1;
  stss.se = NULL;
  stss.duration = 10;

  thread_handles = (thread_state_t *) malloc( sizeof(thread_state_t) * cpu_count * 2 );

  for( loop = 0 ; loop < cpu_count ; loop++ )
  {
    abstraction_thread_start( &thread_handles[loop], loop, slist_internal_thread_head_writer, &stss );
    abstraction_thread_start( &thread_handles[loop+cpu_count], loop, slist_internal_thread_deleter_traverser, &stss );
  }

  for( loop = 0 ; loop < cpu_count * 2 ; loop++ )
    abstraction_thread_wait( thread_handles[loop] );

  slist_delete( stss.ss );

  free( thread_handles );

  // TRD : 9. one head writer and one 25% deleter-traverse per CPU

  printf( "\n"
          "9. one head writer and one 25%% deleter-traverse per CPU\n"
          "=======================================================\n" );

  slist_new( &stss.ss, NULL, NULL );
  stss.iteration_modulo = 4;
  stss.se = NULL;
  stss.duration = 1;

  thread_handles = (thread_state_t *) malloc( sizeof(thread_state_t) * cpu_count * 2 );

  for( loop = 0 ; loop < cpu_count ; loop++ )
  {
    abstraction_thread_start( &thread_handles[loop], loop, slist_internal_thread_head_writer, &stss );
    abstraction_thread_start( &thread_handles[loop+cpu_count], loop, slist_internal_thread_deleter_traverser, &stss );
  }

  for( loop = 0 ; loop < cpu_count * 2 ; loop++ )
    abstraction_thread_wait( thread_handles[loop] );

  slist_delete( stss.ss );

  free( thread_handles );

  // TRD : 10. make one element, then one after writer and one 100% deleter-traverser per CPU

  printf( "\n"
          "10. make one element, then one after writer and one 100%% deleter-traverser per CPU\n"
          "==================================================================================\n" );

  slist_new( &stss.ss, NULL, NULL );
  stss.iteration_modulo = 1;
  stss.se = slist_new_head( stss.ss, (void *) NULL );
  stss.duration = 10;

  thread_handles = (thread_state_t *) malloc( sizeof(thread_state_t) * cpu_count * 2 );

  for( loop = 0 ; loop < cpu_count ; loop++ )
  {
    abstraction_thread_start( &thread_handles[loop], loop, slist_internal_thread_after_writer, &stss );
    abstraction_thread_start( &thread_handles[loop+cpu_count], loop, slist_internal_thread_deleter_traverser, &stss );
  }

  for( loop = 0 ; loop < cpu_count * 2 ; loop++ )
    abstraction_thread_wait( thread_handles[loop] );

  slist_delete( stss.ss );

  free( thread_handles );

  // TRD : 11. make one element, then one after writer and one 25% deleter-traverser per CPU

  printf( "\n"
          "11. make one element, then one after writer and one 25%% deleter-traverser per CPU\n"
          "=================================================================================\n" );

  slist_new( &stss.ss, NULL, NULL );
  stss.iteration_modulo = 4;
  stss.se = slist_new_head( stss.ss, (void *) NULL );
  stss.duration = 1;

  thread_handles = (thread_state_t *) malloc( sizeof(thread_state_t) * cpu_count * 2 );

  for( loop = 0 ; loop < cpu_count ; loop++ )
  {
    abstraction_thread_start( &thread_handles[loop], loop, slist_internal_thread_after_writer, &stss );
    abstraction_thread_start( &thread_handles[loop+cpu_count], loop, slist_internal_thread_deleter_traverser, &stss );
  }

  for( loop = 0 ; loop < cpu_count * 2 ; loop++ )
    abstraction_thread_wait( thread_handles[loop] );

  slist_delete( stss.ss );

  free( thread_handles );

  // TRD : 12. one head writer, one after writer, one traverser and one 25% deleter-traverser per CPU

  printf( "\n"
          "12. one head writer, one after writer, one traverser and one 25%% deleter-traverser per CPU\n"
          "==========================================================================================\n" );

  slist_new( &stss.ss, NULL, NULL );
  stss.iteration_modulo = 4;
  stss.se = slist_new_head( stss.ss, (void *) NULL );
  stss.duration = 1;

  thread_handles = (thread_state_t *) malloc( sizeof(thread_state_t) * cpu_count * 4 );

  for( loop = 0 ; loop < cpu_count ; loop++ )
  {
    abstraction_thread_start( &thread_handles[loop], loop, slist_internal_thread_head_writer, &stss );
    abstraction_thread_start( &thread_handles[loop+cpu_count], loop, slist_internal_thread_after_writer, &stss );
    abstraction_thread_start( &thread_handles[loop+cpu_count*2], loop, slist_internal_thread_traverser, &stss );
    abstraction_thread_start( &thread_handles[loop+cpu_count*3], loop, slist_internal_thread_deleter_traverser, &stss );
  }

  for( loop = 0 ; loop < cpu_count * 4 ; loop++ )
    abstraction_thread_wait( thread_handles[loop] );

  slist_delete( stss.ss );

  free( thread_handles );

  return;
}





/****************************************************************************/
thread_return_t CALLING_CONVENTION slist_internal_thread_head_writer( void *slist_thread_start_state )
{
  struct slist_thread_start_state
    *stss;

  time_t
    start_time;

  unsigned long int
    count = 0;

  assert( slist_thread_start_state != NULL );

  stss = (struct slist_thread_start_state *) slist_thread_start_state;

  time( &start_time );

  while( time(NULL) < start_time + stss->duration )
    if( slist_new_head(stss->ss, (void *) 0) )
      count++;

  printf( "head writer count = %lu\n", count );

  return( (thread_return_t) EXIT_SUCCESS );
}





/****************************************************************************/
thread_return_t CALLING_CONVENTION slist_internal_thread_after_writer( void *slist_thread_start_state )
{
  struct slist_thread_start_state
    *stss;

  time_t
    start_time;

  unsigned long int
    count = 0;

  assert( slist_thread_start_state != NULL );

  stss = (struct slist_thread_start_state *) slist_thread_start_state;

  time( &start_time );

  while( time(NULL) < start_time + stss->duration )
    if( slist_new_next(stss->se, (void *) 0) )
      count++;

  printf( "after writer count = %lu\n", count );

  return( (thread_return_t) EXIT_SUCCESS );
}





/****************************************************************************/
thread_return_t CALLING_CONVENTION slist_internal_thread_traverser( void *slist_thread_start_state )
{
  struct slist_thread_start_state
    *stss;

  time_t
    start_time;

  unsigned long int
    count = 0,
    iteration = 0;

  struct slist_element
    *se;

  assert( slist_thread_start_state != NULL );

  stss = (struct slist_thread_start_state *) slist_thread_start_state;

  time( &start_time );

  slist_get_head( stss->ss, &se );

  while( time(NULL) < start_time + stss->duration )
  {
    if( !(iteration % stss->iteration_modulo) )
    {
      slist_get_next( se, &se );
      count++;
    }

    if( se == NULL )
    {
      slist_get_head( stss->ss, &se );
      count++;
    }

    iteration++;
  }

  printf( "traverser count = %lu\n", count );

  return( (thread_return_t) EXIT_SUCCESS );
}





/****************************************************************************/
thread_return_t CALLING_CONVENTION slist_internal_thread_deleter_traverser( void *slist_thread_start_state )
{
  struct slist_thread_start_state
    *stss;

  time_t
    start_time;

  unsigned long int
    count = 0,
    iteration = 0;

  struct slist_element
    *se;

  assert( slist_thread_start_state != NULL );

  stss = (struct slist_thread_start_state *) slist_thread_start_state;

  time( &start_time );

  slist_get_head( stss->ss, &se );

  while( time(NULL) < start_time + stss->duration )
  {
    if( se != NULL and !(iteration % stss->iteration_modulo) )
    {
      slist_delete_element( stss->ss, se );
      count++;
    }

    if( se != NULL )
      slist_get_next( se, &se );

    if( se == NULL )
      slist_get_head( stss->ss, &se );

    iteration++;
  }

  printf( "deleter-traverser count = %lu\n", count );

  return( (thread_return_t) EXIT_SUCCESS );
}

