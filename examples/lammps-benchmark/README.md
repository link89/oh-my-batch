# LAMMPS Benchmark
Test different MPI and OpenMP setup for LAMMPS.

## Usage

```bash
./run.sh
sbatch out/batch-0.slurm
```

## Results

The result shows that the following setup is the best:

```bash
# Here we have to limit the threads of openblas to 1 to avoid resource limit
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
mpirun -np 64 lmp ...
```

with the following performance:

```
Performance: 113.850 ns/day, 0.211 hours/ns, 1317.708 timesteps/s, 3.076 Matom-step/s
99.3% CPU use with 64 MPI tasks x 1 OpenMP threads
```