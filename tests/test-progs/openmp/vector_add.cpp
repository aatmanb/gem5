#include<iostream>
#include<omp.h>

#include<gem5/m5ops.h>

 int main (int argc, char **argv) {
 
    int a[2];
    int b[2];
    int ab[2];

    // initialize 
    for (int i=0; i<2; i++) {
        a[i] = i+2;
        b[i] = (i+2)+2;
    }

    printf("forking off 2 threads\n"); 
    omp_set_num_threads(2);
    #pragma omp parallel for
    for (int i=0; i<2; i++) {
        m5_pim_process(omp_get_thread_num());
        printf("i=%d, I am thread: %d\n", i, omp_get_thread_num());
        ab[i] = a[i] + b[i];
    }
    printf("complete vector add\n");
    return 0;
 }
