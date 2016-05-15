
#include <stdlib.h>
#include <string.h>
#include "bloom.h"
#include "dynamic_array.h"

#define DIVSHIFT 6  // log (64) for 64-bit ints
#define INTLEN 64 // length of integers in filter (in bits)

/* we choose some simple hash algorithms for investigative purposes
   we can improve on this by choosing "stronger" hash algorithms
   depending on application
   References:
   https://www.cs.hmc.edu/~geoff/classes/
      hmc.cs070.200101/homework10/hashfuncs.html
   http://stackoverflow.com/questions/664014/
      what-integer-hash-function-are-good-that-accepts-an-integer-hash-key
   https://gist.github.com/badboy/6267743 */

void bloom_init(bloom_filter_t* B, index_t size_in_bits){
    /* create a filter */
    int numints = (size_in_bits >> DIVSHIFT) + 1;  // How many ints are needed
    /*printf("Size %d\n", numints);*/
    B->table = (index_t *) malloc(numints*sizeof(int));

    for (int i = 0; i < numints; i++){
        B->table[i] = 0;  // initialize array
        /*
        printf("%llu\n", B->table[i]);*/
    }

    B->size = size_in_bits;
    B->count = 0;
}

void bloom_destroy(bloom_filter_t* B){
    /* free memory for filter */
    free(B->table);
}

void set_bit(bloom_filter_t* B, index_t i){
    /* set the bit at position i in filter */
    if (i > B->size){
        printf("beyond size of array, max: %llu\n", B->size);
        return;
    }

    /*printf("target bit %llu\n", i);*/
    index_t rightint = B->table[i >> DIVSHIFT];  // find integer
    /*printf("before %llu\n", B->table[i>>6]);*/
    index_t rightbit = i % INTLEN;  // find bit position
    index_t checkbit = 1;
    index_t setbit = checkbit << (rightbit - 1);  // move 1 into position
    /*printf("setbitasnum %llu\n", setbit);*/
    B->table[i>>6] = rightint | setbit;  // only set bit, keep everything else

    /*
    printf("changed int %llu\n", rightint);
    printf("changed bit as number %llu\n", setbit);
    printf("after %llu\n", B->table[i>>6]);*/
}

index_t get_bit(bloom_filter_t* B, index_t i){
    /* get the value of the bit at position i in filter */
    if (i >= B->size){
        printf("beyond size of array, max: %llu\n", B->size);
        return -1;
    }
    index_t rightint = B->table[i >> DIVSHIFT];  // find integer
    index_t rightbit = i % INTLEN;  // find bit position
    index_t checkbit = 1;
    index_t rightbitasnum = checkbit << (rightbit-1);  // move 1 into position

    /*printf("rightint %llu\n", B->table[i>>6]);
    printf("rightbitasnum %llu\n", rightbitasnum);
    printf("bitcomp %llu\n", rightint & rightbitasnum);*/

    return (rightint & rightbitasnum)>>(rightbit-1);  // AND, and shift to LSB
}

index_t hash1(bloom_filter_t* B, key_t k){
    /* Knuth's Multiplicative method */
    key_t hashit;
    hashit = 2654435761*k;
    return hashit;
}

index_t hash2(bloom_filter_t* B, key_t k){
    /* Robert Jenkin's 32-bit integer hash function */
    key_t hashit;
    k = (k+0x7ed55d16) + (k<<12);
    k = (k^0xc761c23c) ^ (k>>19);
    k = (k+0x165667b1) + (k<<5);
    k = (k+0xd3a2646c) ^ (k<<9);
    k = (k+0xfd7046c5) + (k<<3);
    k = (k^0xb55a4f09) ^ (k>>16);
    hashit = k;
    return hashit;
}

int bloom_check(bloom_filter_t* B, key_t k){
    /* return -1 if key not found (i.e. corresponding bits are not all 1)
       else return 1 */
    index_t bitindex;
    for (int i = 0; i < N_HASHES; i++){
        bitindex = (hash1(B, k) + i * hash2(B, k)) % (B->size);
        /*printf("Checking for %llu\n", k);
        printf("accessing %llu\n", bitindex);
        printf("%llu\n", bitindex);*/
        if (get_bit(B, bitindex)==0){
            printf("key not found %llu\n", k);
            return -1;
        }
    }
    return 1;  /* all bits are 1 */
}

void bloom_add(bloom_filter_t* B, key_t k){
    /* add a k to the filter by applying hash functions */
    index_t bitindex;
    for (int i = 0; i < N_HASHES; i++){
        bitindex = (hash1(B, k) + i * hash2(B, k)) % (B->size);
        /*printf("Checking for %llu\n", k);*/
        /*printf("setting %llu\n", bitindex);*/
        set_bit(B, bitindex);
    }
    B->count = B->count + 1;  // add key
    /*printf("total keys in filter %llu\n", B->count);*/
}

int64_t countbits(bloom_filter_t* B){
    /* count the number of bits set in the filter */
    int count = 0;
    for (int i = 0; i < B->size; i++){
        if (get_bit(B, i)==1){
            count++;
        }
    }
    return count;
}

int64_t bigrands(int64_t arr[], int64_t n, int64_t min, int64_t max){
    /* generates an array of n random numbers from min to mx */
    if (max < RAND_MAX){
        for (int i = 0; i < n; i++) {
            /*printf("%d\n", i);*/
            arr[i] = (min + rand()) % max;
        }
    } else {
        // number is bigger than generator's max
        //   use formula to generate over range
        //   source: http://cboard.cprogramming.com/
        //       cplusplus-programming/95024-max_rand.html
       for (int i = 0; i < n; i++) {
           arr[i] = (min + (rand() * RAND_MAX + rand())) % max;
       }
    }
    return 1;
}

void experiment(bloom_filter_t* B, index_t P, int64_t arr1[], int64_t arr2[],
                   int64_t n){
    /* assume both input arrays are of size n */

    bloom_init(B, P);   // create filter

    for (int i = 0; i < n; i++){
        bloom_add(B, arr1[i]);  // add elements of first array to filter
    }

    int64_t count = countbits(B);  // count number of set bits in filter
    printf("Number of Unique Bits: %llu\n", count);

    int64_t checkcount = 0;
    for (int i = 0; i < n; i++){
        if (bloom_check(B, arr2[i]) == 1){
            checkcount++;
        } // check if elements of second array in
    }
    printf("Number of Keys in Array 2 found: %llu\n", checkcount);

}


int main() {
    bloom_filter_t test;
    index_t P = 1000;

    /* bloom_init(&test, P); */

    /*
    printf("%llu\n", hash1(&test, 0));
    printf("%llu\n", hash1(&test, 1));
    printf("%llu\n", hash1(&test, 2));
    printf("%llu\n", hash1(&test, 3));
    printf("%llu\n", hash1(&test, 13));
    printf("%llu\n", hash1(&test, 97));

    printf("%llu\n", hash2(&test, 0));
    printf("%llu\n", hash2(&test, 1));
    printf("%llu\n", hash2(&test, 2));
    printf("%llu\n", hash2(&test, 3));
    printf("%llu\n", hash2(&test, 13));
    printf("%llu\n", hash2(&test, 97)); */

    /*
    set_bit(&test, 3);
    set_bit(&test, 6);
    printf("%llu\n", get_bit(&test, 2));
    printf("%llu\n", get_bit(&test, 3));
    printf("%llu\n", get_bit(&test, 4)); */

    /*
    bloom_add(&test, 75);
    bloom_add(&test, 39);
    bloom_add(&test, 124);
    bloom_add(&test, 25);
    printf("%d\n", bloom_check(&test, 25));
    printf("%d\n", bloom_check(&test, 39));
    printf("%d\n", bloom_check(&test, 55)); */

    /*
    for (int i = 1; i <= 70; i++){
        bloom_add(test, i);
    }

    printf("Number of bits set: %d\n", countbits(&test)); */

    int64_t arrsize = 100;
    int64_t minrange = 1;
    int64_t maxrange = 1000000;
    srand(0);  // seed for RNG

    int64_t arr1[arrsize];
    int64_t flag = bigrands(arr1, arrsize, minrange, maxrange);
    printf("array 1 successfully created (1-yes): %lld\n", flag);

    int64_t arr2[arrsize];
    flag = bigrands(arr2, arrsize, minrange, maxrange);
    printf("array 2 successfully created (1-yes): %lld\n", flag);

    experiment(&test, P, arr1, arr2, arrsize);

    /* int64_t a = bigrands(arr, arrsize, minrange, maxrange);
    printf("success: %lld\n", a); */

    /*
    for (int i = 0; i < arrsize; i++){
        printf("array 1: %lld\n", arr1[i]);
    }

    for (int i = 0; i < arrsize; i++){
        printf("array 2: %lld\n", arr2[i]);
    } */

    bloom_destroy(&test);
    printf("done\n");
}
