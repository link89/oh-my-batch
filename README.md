# oh-my-batch
A simple tool to manipulate batch tasks.

## Install
```bash
pip install oh-my-batch
```

## Usage

### Use `omb combo` to generate files with different combinations of parameters

It's a very common task to generate files with different combinations of parameters. 
For example, you have 3 LAMMPS data files in `tmp` directory: `tmp/1.data`, `tmp/2.data`, `tmp/3.data`.

Now you want to generate a series of input files with different parameters,
for example, different temperatures 300K, 400K, 500K, against each data file.

In this case, you can use `combo` command to generate a series of input files for you.

```bash
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
lmp -in in.lmp
EOF

# generate input files
omb combo \
    add_files DATA_FILE tmp/*.data - \
    add_var TEMP 300 400 500 - \
    add_randint RANDOM -n 3 -a 1 -b 1000 --broadcast - \
    make_files tmp/in.lmp.tmp tmp/{i}-T-{TEMP}/in.lmp - \
    make_files tmp/run.sh.tmp tmp/{i}-T-{TEMP}/run.sh - \
    done
```

The above script will generate 9 folders in `tmp` directory
with names like `0-T-300`, `1-T-400`, `2-T-500`, `3-T-300` and so on.
Each folder will contain a `in.lmp` file and a `run.sh` file.

The 9 folders are the combinations of 3 data files and 3 temperatures,
and each input file will have a independent random number between 1 and 1000 as `RANDOM`.

You can save the above script to a file and run it yourself to see the result, 
and you can also run `omb combo --help` to see the detailed usage of `combo` command.


### Use `omb batch` to generate batch scripts
TODO