TARGET_ISA=x86

GEM5_HOME=$(PWD)
$(info   GEM5_HOME is $(GEM5_HOME))

CXX=g++

CFLAGS=-I$(GEM5_HOME)/include

LDFLAGS=-L$(GEM5_HOME)/util/m5/build/$(TARGET_ISA)/out -lm5

BENCHMARK_ROOT=$(GEM5_HOME)/tests/test-progs/openmp

OBJECTS= vector_add.exe

all: vector_add

vector_add:
	$(CXX) -o $(BENCHMARK_ROOT)/$(OBJECTS) $(BENCHMARK_ROOT)/vector_add.cpp $(CFLAGS) $(LDFLAGS) -fopenmp -O0 -g

clean:
	rm -f $(OBJECTS)
