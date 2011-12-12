#include "internal.h"





/****************************************************************************/
void benchmark_ringbuffer( void )
{
  unsigned int
    loop,
    thread_count,
    cpu_count;

  struct ringbuffer_state
    *rs;

  struct ringbuffer_benchmark
    *rb;

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

  /* TRD : here we benchmark the ringbuffer

           the benchmark is to have a single ringbuffer
           where a worker thread busy-works writing and then reading
  */

  cpu_count = abstraction_cpu_count();

  thread_handles = (thread_state_t *) malloc( sizeof(thread_state_t) * cpu_count );

  rb = (struct ringbuffer_benchmark *) malloc( sizeof(struct ringbuffer_benchmark) * cpu_count );

  // TRD : print the benchmark ID and CSV header
  printf( "\n"
          "Release %d Ringbuffer Benchmark #1\n"
          "CPUs,total ops,mean ops/sec per CPU,standard deviation,scalability\n", LIBLFDS_RELEASE_NUMBER );

  // TRD : we run CPU count times for scalability
  for( thread_count = 1 ; thread_count <= cpu_count ; thread_count++ )
  {
    // TRD : initialisation
    ringbuffer_new( &rs, 1000, NULL, NULL );

    for( loop = 0 ; loop < cpu_count ; loop++ )
    {
      (rb+loop)->rs = rs;
      (rb+loop)->operation_count = 0;
    }

    // TRD : main test
    for( loop = 0 ; loop < thread_count ; loop++ )
      abstraction_thread_start( &thread_handles[loop], loop, benchmark_ringbuffer_thread_write_and_read, rb+loop );

    for( loop = 0 ; loop < thread_count ; loop++ )
      abstraction_thread_wait( thread_handles[loop] );

    // TRD : post test math
    total_operations_for_full_test_for_all_cpus = 0;
    total_difference_per_second_per_cpu = 0;

    for( loop = 0 ; loop < thread_count ; loop++ )
      total_operations_for_full_test_for_all_cpus += (rb+loop)->operation_count;

    mean_operations_per_second_per_cpu = ((double) total_operations_for_full_test_for_all_cpus / (double) thread_count) / (double) 10;

    if( thread_count == 1 )
      total_operations_for_full_test_for_all_cpus_for_one_cpu = total_operations_for_full_test_for_all_cpus;

    for( loop = 0 ; loop < thread_count ; loop++ )
    {
      difference_per_second_per_cpu = ((double) (rb+loop)->operation_count / (double) 10) - mean_operations_per_second_per_cpu;
      total_difference_per_second_per_cpu += difference_per_second_per_cpu * difference_per_second_per_cpu;
    }

    std_dev_per_second_per_cpu = sqrt( (double) total_difference_per_second_per_cpu );

    scalability = (double) total_operations_for_full_test_for_all_cpus / (double) (total_operations_for_full_test_for_all_cpus_for_one_cpu * thread_count);

    printf( "%u,%u,%.0f,%.0f,%0.2f\n", thread_count, (unsigned int) total_operations_for_full_test_for_all_cpus, mean_operations_per_second_per_cpu, std_dev_per_second_per_cpu, scalability );

    // TRD : cleanup
    ringbuffer_delete( rs, NULL, NULL );
  }

  free( rb );

  free( thread_handles );

  return;
}





/****************************************************************************/
thread_return_t CALLING_CONVENTION benchmark_ringbuffer_thread_write_and_read( void *ringbuffer_benchmark )
{
  struct ringbuffer_benchmark
    *rb;

  struct freelist_element
    *fe;

  time_t
    start_time;

  assert( ringbuffer_benchmark != NULL );

  rb = (struct ringbuffer_benchmark *) ringbuffer_benchmark;

  time( &start_time );

  while( time(NULL) < start_time + 10 )
  {
    ringbuffer_get_write_element( rb->rs, &fe, NULL );
    ringbuffer_put_write_element( rb->rs, fe );

    ringbuffer_get_read_element( rb->rs, &fe );
    ringbuffer_put_read_element( rb->rs, fe );

    rb->operation_count += 2;
  }

  return( (thread_return_t) EXIT_SUCCESS );
}

