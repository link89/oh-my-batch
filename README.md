# oh-my-batch
A simple tool to manipulate batch tasks designed for scientific computing community.

## Features
* `omb combo`: generate folders/files from different combinations of parameters
* `omb batch`: generate batch scripts from multiple working directories
* `omb job`: track the state of job in job schedular

## Install
```bash
pip install oh-my-batch
```

## Use cases

### Generate files from different combinations of parameters

It's common to generate files with different combinations of parameters in scientific computing.
For example, you have 3 LAMMPS data files in `tmp` directory: `tmp/1.data`, `tmp/2.data`, `tmp/3.data`.
And you want to generate a series of input files with different parameters,
for example, different temperatures 300K, 400K, 500K, against each data file.

In this case, you can use `omb combo` command to generate a series of input files for you.

```bash
#! /bin/bash
# prepare fake data files
mkdir -p tmp/
touch tmp/1.data tmp/2.data tmp/3.data

# prepare a lammps input file template
cat > tmp/in.lmp.tmp <<EOF
read_data $DATA_FILE
velocity all create $TEMP $RANDOM
run 1000
EOF

# prepare a run script template
cat > tmp/run.sh.tmp <<EOF
cat in.lmp  # simulate running lammps
EOF

# generate input files
omb combo \
    add_files DATA_FILE tmp/*.data - \
    add_var TEMP 300 400 500 - \
    add_randint RANDOM -n 3 -a 1 -b 1000 --broadcast - \
    make_files tmp/in.lmp.tmp tmp/tasks/{i}-T-{TEMP}/in.lmp - \
    make_files tmp/run.sh.tmp tmp/tasks/{i}-T-{TEMP}/run.sh --mode 755 - \
    done
```

The above script will generate 9 folders in `tmp/tasks` directory
with names from `0-T-300`, `1-T-400`, `2-T-500`, `3-T-300` to `8-T-500`.
Each folder will contain a `in.lmp` file and a `run.sh` file.

The 9 folders are the combinations of 3 data files and 3 temperatures,
and each input file will have a independent random number between 1 and 1000 as `RANDOM`.

You can run the about script by `./examples/omb-combo.sh`,
and you can also run `omb combo --help` to see the detailed usage of `combo` command.

### Generate batch scripts from multiple working directories
It's common to submit a lot of jobs to a job scheduler. `omb batch` is designed to help you generate batch scripts from multiple working directories and package them into several batch scripts.

Let's continue the above example, now you have 9 folders in `tmp/tasks` directory.
You want to package them into 2 batch scripts to submit to a job scheduler.

You can use `omb batch` to generate batch scripts for you like this:

```bash
#! /bin/bash
cat > tmp/lammps_header.sh <<EOF
#!/bin/bash
#SBATCH -J lmp
#SBATCH -n 1
#SBATCH -t 1:00:00
EOF

omb batch \
    add_work_dir tmp/tasks/* - \
    add_header_file tmp/lammps_header.sh - \
    add_command "checkpoint lmp.done ./run.sh" - \
    make tmp/lmp-{i}.slurm --concurrency 2
```

You will find batch scripts `tmp/lmp-0.slurm` and `tmp/lmp-1.slurm` in `tmp` directory.

`omb batch` will provide some useful functions in the batch script.
For example, `checkpoint` will check if the job is done and skip the job if it's done.

You can run the above script by `./examples/omb-batch.sh`,

### Track the state of job in job schedular

Let's continue the above example, now you have submitted the batch scripts to the job scheduler.

You can use `omb job` to track the state of the jobs.

```bash

omb job slurm \
    submit tmp/*.slurm --max_tries 3 --wait --recovery lammps-jobs.json 
```

The above command will submit the batch scripts to the job scheduler,
and wait for the jobs to finish. If the job fails, it will retry for at most 3 times.

The `--recovery` option will save the job information to `lammps-jobs.json` file,
if `omb job` is interrupted, you can run the exact same command to recover the job status, 
so that you don't need to resubmit the jobs that are already submitted.
