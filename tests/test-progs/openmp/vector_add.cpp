#include<iostream>
#include<omp.h>

#include<gem5/m5ops.h>

 int main (int argc, char **argv) {
 
    int a[1];
    int b[1];
    int ab[1];

    // initialize 
    for (int i=0; i<1; i++) {
        a[i] = i+1;
        b[i] = (i+1)+1;
    }

    printf("forking off 1 threads\n"); 
    omp_set_num_threads(1);
    #pragma omp parallel for
    for (int i=0; i<1; i++) {
        printf("i=%d, I am thread: %d\n", i, omp_get_thread_num());
        ab[i] = a[i] + b[i];
    }
    printf("complete vector add\n");
    return 0;
 }
