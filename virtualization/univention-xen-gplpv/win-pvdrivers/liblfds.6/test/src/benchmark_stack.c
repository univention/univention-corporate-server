#include "internal.h"





/****************************************************************************/
void benchmark_stack( void )
{
  unsigned int
    loop,
    thread_count,
    cpu_count;

  struct stack_state
    *ss;

  struct stack_benchmark
    *sb;

  thread_state_t
    *thread_handles;

  atom_t
    total_operations_for_full_test_for_all_cpus,
    total_operations_for_full_test_for_all_cpus_for_one_cpu = 0;

  double
    mean_operations_per_second_per_cpu,
    difference_per_second_per_cpu,
    total_difference_per_second_per_cpu,
    std_dev_per_second_per_cpu,
    scalability;

  /* TRD : here we benchmark the stack

           the benchmark is to have a single stack
           where a worker thread busy-works pushing then popping
  */

  cpu_count = abstraction_cpu_count();

  thread_handles = (thread_state_t *) malloc( sizeof(thread_state_t) * cpu_count );

  sb = (struct stack_benchmark *) malloc( sizeof(struct stack_benchmark) * cpu_count );

  // TRD : print the benchmark ID and CSV header
  printf( "\n"
          "Release %d Stack Benchmark #1\n"
          "CPUs,total ops,mean ops/sec per CPU,standard deviation,scalability\n", LIBLFDS_RELEASE_NUMBER );

  // TRD : we run CPU count times for scalability
  for( thread_count = 1 ; thread_count <= cpu_count ; thread_count++ )
  {
    // TRD : initialisation
    stack_new( &ss, 1000 );

    for( loop = 0 ; loop < cpu_count ; loop++ )
    {
      (sb+loop)->ss = ss;
      (sb+loop)->operation_count = 0;
    }

    // TRD : main test
    for( loop = 0 ; loop < thread_count ; loop++ )
      abstraction_thread_start( &thread_handles[loop], loop, benchmark_stack_thread_push_and_pop, sb+loop );

    for( loop = 0 ; loop < thread_count ; loop++ )
      abstraction_thread_wait( thread_handles[loop] );

    // TRD : post test math
    total_operations_for_full_test_for_all_cpus = 0;
    total_difference_per_second_per_cpu = 0;

    for( loop = 0 ; loop < thread_count ; loop++ )
      total_operations_for_full_test_for_all_cpus += (sb+loop)->operation_count;

    mean_operations_per_second_per_cpu = ((double) total_operations_for_full_test_for_all_cpus / (double) thread_count) / (double) 10;

    if( thread_count == 1 )
      total_operations_for_full_test_for_all_cpus_for_one_cpu = total_operations_for_full_test_for_all_cpus;

    for( loop = 0 ; loop < thread_count ; loop++ )
    {
      difference_per_second_per_cpu = ((double) (sb+loop)->operation_count / (double) 10) - mean_operations_per_second_per_cpu;
      total_difference_per_second_per_cpu += difference_per_second_per_cpu * difference_per_second_per_cpu;
    }

    std_dev_per_second_per_cpu = sqrt( (double) total_difference_per_second_per_cpu );

    scalability = (double) total_operations_for_full_test_for_all_cpus / (double) (total_operations_for_full_test_for_all_cpus_for_one_cpu * thread_count);

    printf( "%u,%u,%.0f,%.0f,%0.2f\n", thread_count, (unsigned int) total_operations_for_full_test_for_all_cpus, mean_operations_per_second_per_cpu, std_dev_per_second_per_cpu, scalability );

    // TRD : cleanup
    stack_delete( ss, NULL, NULL );
  }

  free( sb );

  free( thread_handles );

  return;
}





/****************************************************************************/
thread_return_t CALLING_CONVENTION benchmark_stack_thread_push_and_pop( void *stack_benchmark )
{
  struct stack_benchmark
    *sb;

  void
    *user_data = NULL;

  time_t
    start_time;

  assert( stack_benchmark != NULL );

  sb = (struct stack_benchmark *) stack_benchmark;

  time( &start_time );

  while( time(NULL) < start_time + 10 )
  {
    stack_push( sb->ss, user_data );
    stack_pop( sb->ss, &user_data );

    sb->operation_count += 2;
  }

  return( (thread_return_t) EXIT_SUCCESS );
}

