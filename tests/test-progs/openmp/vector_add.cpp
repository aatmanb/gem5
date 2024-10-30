#include<iostream>
#include<omp.h>
#include<unistd.h>

#include<gem5/m5ops.h>

#define NUM_ELEMENTS 4
#define NUM_THREADS 1
#define NUM_ELEMENTS_PER_THREAD (NUM_ELEMENTS/NUM_THREADS)
#define STEP_SIZE 1

int* myMalloc(int num_elements, bool pageAlign) {
    int * h_counters0 = NULL, * h_counters0_temp = NULL;  
    h_counters0_temp = (int *)malloc((num_elements*sizeof(int)) + 0x1000);
    if (pageAlign) {                                                                                                                                                                                         
        h_counters0 = (int *)(((((unsigned long long)h_counters0_temp) >> 12) << 12)); // + 0x1000);
    } else {                                                                                                                                                                                                 
        h_counters0 = h_counters0_temp;
    }

    return h_counters0;
}


int main (int argc, char **argv) {

    long int pagesize = sysconf(_SC_PAGE_SIZE);
    printf("benchmark: pagesize: %ld\n", pagesize);

    //// Allocate total required memory
    //int *total = myMalloc(NUM_ELEMENTS * 3, true);

    //int *a = total;
    //int *b = (total + NUM_ELEMENTS);
    //int *ab = (total + (2*NUM_ELEMENTS));

    //int *a = myMalloc(NUM_ELEMENTS, true); 
    //int *b = myMalloc(NUM_ELEMENTS, true); 
    //int *ab = myMalloc(NUM_ELEMENTS, true);

    int a[NUM_ELEMENTS];
    int b[NUM_ELEMENTS];
    int ab[NUM_ELEMENTS];
    
    printf("benchmark: a=%p, b=%p, ab=%p\n", a, b, ab);

    // initialize 
    for (int i=0; i<NUM_ELEMENTS; i++) {
        *(a+i) = i+NUM_ELEMENTS;
        *(b+i) = (i+NUM_ELEMENTS)+NUM_ELEMENTS;
    }

    //for (int tid=0; tid<NUM_THREADS; tid++) {
    //    int idx;
    //    for (int i=0; i<NUM_ELEMENTS_PER_THREAD; i+=512) {
    //        //m5_pim_process(tid);
    //        //printf("benchmark: [tid:%d] i=%d\n", tid, i);
    //        idx = (tid*NUM_ELEMENTS_PER_THREAD) + i;
    //        printf("benchmark: [tid:%d] i=%d, idx=%d, &a[idx]=%p, &b[idx]=%p, &ab[idx]=%p\n", tid, i, idx, &a[idx], &b[idx], &ab[idx]);
    //        //m5_host_process(tid);
    //    }
    //}

    //printf("forking off NUM_ELEMENTS threads\n"); 
    omp_set_num_threads(NUM_THREADS);
    #pragma omp parallel
    {
    int tid = omp_get_thread_num();
    m5_pim_process(tid);
    int idx;
    int *a_idx, *b_idx, *ab_idx;
    for (int i=0; i<NUM_ELEMENTS_PER_THREAD; i+=STEP_SIZE) {
        //m5_pim_process(tid);
        //printf("benchmark: [tid:%d] i=%d\n", tid, i);
        idx = (tid*NUM_ELEMENTS_PER_THREAD) + i;
        a_idx = a + idx;
        b_idx = b + idx;
        ab_idx = ab + idx;
        printf("benchmark: [tid:%d] i=%d, idx=%d, a_idx=%p, b_idx=%p, ab_idx=%p\n", tid, i, idx, a_idx, b_idx, ab_idx);
        *ab_idx = *a_idx + *b_idx;
        printf("benchmark: [tid:%d] i=%d, idx=%d, *a_idx=%d, *b_idx=%d, *ab_idx=%d\n", tid, i, idx, *a_idx, *b_idx, *ab_idx);
        //printf("benchmark: [tid:%d] i=%d, idx=%d, &a[idx]=%p, &b[idx]=%p, &ab[idx]=%p\n", tid, i, idx, &a[idx], &b[idx], &ab[idx]);
        //ab[idx] = a[idx] + b[idx];
        //printf("benchmark: [tid:%d] i=%d, idx=%d, a[idx]=%d, b[idx]=%d, ab[idx]=%d\n", tid, i, idx, a[idx], b[idx], ab[idx]);
        //m5_host_process(tid);
    }
    m5_host_process(tid);
    }
    printf("complete vector add\n");
    return 0;
 }
