# Thinking in [Oh-My-Batch]

This document introduces the design philosophy and usage of [Oh-My-Batch].
[Oh-My-Batch] is a CLI- and Python-based toolkit for building batch scripts and workflows.
It provides a set of standalone command-line tools and Python modules
that help you quickly implement a computational workflow by writing a shell or Python script,
then run it on a local machine or an HPC cluster.

Specifically, when used together with [ai2-kit], [Oh-My-Batch] can help quickly develop an active-learning workflow
that combines different computational chemistry software.
Such workflows typically follow an active learning structure we call TESLA,
composed of four basic steps: train, explore, screen, and label.
This document uses a TESLA workflow as the running example to demonstrate the basic features and tips of [Oh-My-Batch]
so that you can get productive fast.

In addition, we also cover some general-purpose shell tips.
These tips are useful not only for [Oh-My-Batch] workflows, but also when writing other shell scripts.


## Common shell tips
Shell scripting is a convenient way to quickly build automated workflows. Mastering a few common patterns
will help you write efficient and reliable automation. These techniques are used throughout the [TESLA] scripts,
so learning them in advance will make the scripts easier to read.

### Use `set -e` for fail-fast
Add `set -e` at the beginning of a script to make it exit immediately when a command fails instead of continuing.

```bash
#!/bin/bash
set -e
```

In most cases, it’s recommended to add `set -e` up top to improve robustness.
This prevents errors from being ignored and the script from proceeding into an unexpected state.
For commands whose failures you intentionally want to ignore, see the next section.


### Ignore errors selectively
If you want a command’s failure not to stop the script, you can append `|| true` to suppress the error, e.g.:

```bash
some_command || true
```

An improved version is to log it with `echo`, for example:

```bash
some_command || echo "ignore error of some_command"
```
This prints a log line to signal that the error of this command was intentionally ignored.

### Be cautious when changing the working directory

Using `cd` is a side effect that may impact subsequent commands, so be extra careful.
In general, try to avoid frequent directory changes, especially in complex scripts.

Instead of changing the directory and then running a command, prefer specifying input and output paths explicitly
within the command when possible. For example, to archive files under `data`, you can run:

```bash
tar -czf archive.tar.gz data/ -C data/
```

rather than:

```bash
cd data
tar -czf ../archive.tar.gz .
```

Both yield the same result, but the latter changes the working directory and may cause later commands to fail
if you forget to restore it.

If you must change directories, use a paired `pushd` and `popd` to manage the directory stack.
This ensures you always return to the original directory, for example:

```bash
pushd some/directory
# Do something here
popd
```

### Auto cd to the script directory (use with caution)
If you want the script to automatically switch to its own directory at start, add this to the top:

```bash
cd $(dirname "$0")
```

This helps ensure the script begins from a deterministic path, avoiding errors caused by a wrong working directory
(e.g., relative paths not being found).

However, not all scripts should do this. Usually only the outermost script (the one users invoke directly)
needs it. For helper scripts that are invoked by others, decide based on actual needs.


### Automatically skip completed tasks
For complex scripts, you need a way to avoid re-running completed tasks when the script fails partway or
when you revise it. A common technique is to use a “done file” flag to mark completion. The typical pattern is:

```bash
[ -f task-name.done ]  || {
    # Do something here

    touch task-name.done
}
```

This checks whether `task-name.done` exists. If not, it runs the block. If the block succeeds, it creates the file to
indicate the task is complete. The next time the script runs, it will skip the task if the file exists.

An improved version:

```bash
[ -f task-name.done ] && echo "skip <task-name>"  || {
    # Do something here

    touch task-name.done
}
```

This logs a message when the task is skipped, which helps debugging and maintenance.

To re-run a completed task, simply delete the corresponding `task-name.done` file, and the next run will execute it again.

Of course, if the task produces signature output files, you can also check for those directly to decide whether to skip.


### Limited retries

For tasks that may fail transiently but are worth retrying, use a loop to implement limited retries:

```bash
EXIT_CODE=0
for i in {1..5}; do
    some_flaky_command && break || EXIT_CODE=$?
    sleep 5

done
[ $EXIT_CODE -eq 0 ] || exit $EXIT_CODE
```

In this example, `some_flaky_command` is a command that may fail. The script tries up to 5 times.
If it succeeds (returns 0), the loop breaks. If it fails, it waits 5 seconds and retries.
If all attempts fail, the script exits with the last command’s exit code.


## Writing complex workflows (using [TESLA] as an example)
### Introduction
TODO

### Conventions
#### Directory layout
TODO

#### Naming convention for iteration scripts `iter-`
Scripts starting with `iter-` are the ones executed in each iteration of the [TESLA] workflow. We recommend the following
format to keep names clear and readable:

`iter-<feature>-<software-...>-<version>.sh`

Where:
* feature describes a variant, e.g. `classic` for the classic mode, `redox` for redox-potential workflows, etc. Pick a name that’s easy to remember.
* software lists the software being used, e.g. `dp`, `lammps`, `cp2k`, `vasp`, etc.
* version is the software/script version tag. If you need to modify the script in later iterations, you should copy it and
  bump the version instead of editing the original. Use the version suffix to distinguish variants.

For example,
* `iter-classic-dp-lammps-cp2k.sh` means the initial version using `DeepMD`, `LAMMPS`, and `CP2K` in classic mode.
* `iter-classic-dp-lammps-cp2k-v1.sh` means the first revision using `DeepMD`, `LAMMPS`, and `CP2K` in classic mode.
* `iter-classic-dp-lammps-vasp.sh` means the initial version using `DeepMD`, `LAMMPS`, and `VASP` in classic mode.

And so on.

[Oh-My-Batch]: https://github.com/link89/oh-my-batch
[ai2-kit]: https://github.com/chenggroup/ai2-kit
[TESLA]: ../examples/tesla/
