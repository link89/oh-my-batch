# Thinking in [Oh-My-Batch]

This document outlines the design principles and usage of [Oh-My-Batch].
[Oh-My-Batch] is a CLI- and Python-based toolkit for building batch scripts and computational workflows.
It provides standalone command-line tools and Python modules that let you assemble a workflow in shell or Python
and run it on a local machine or an HPC cluster.

When used with [ai2-kit], [Oh-My-Batch] is particularly useful for developing active-learning workflows
that combine multiple computational chemistry packages.
These workflows often follow a TESLA-style loop with four stages: train, explore, screen, and label.
This document uses TESLA as the main example to introduce the core features and working patterns of [Oh-My-Batch].

The document also covers general shell techniques that are useful in [Oh-My-Batch] workflows
and in shell scripting more broadly.


## Shell practices
Shell scripting is a practical way to build automation quickly.
A small set of good shell practices goes a long way toward making scripts more reliable and easier to maintain.

### Use `set -e` for fail-fast
Add `set -e` near the top of a script to exit immediately when a command fails.

```bash
#!/bin/bash
set -e
```

In most cases, this is the right default.
It prevents silent failures and reduces the chance that the script continues in an invalid state.
If a command is allowed to fail without stopping the script, append `|| true`:

```bash
some_command || true
```

In practice, logging the decision is usually better:

```bash
some_command || echo "ignore error of some_command"
```
This makes it clear that the failure was expected and intentionally ignored.

### Be cautious when changing the working directory

Using `cd` introduces global state into the script, which can easily affect later commands.
As a rule, avoid changing the working directory unless it is necessary.

When possible, pass explicit paths to commands instead of switching directories first.
For example, to archive files under `data`, prefer:

```bash
tar -czf archive.tar.gz data/ -C data/
```

instead of:

```bash
cd data
tar -czf ../archive.tar.gz .
```

Both forms produce the same archive, but the second one mutates the working directory.
If you forget to restore it, later commands may fail in non-obvious ways.

If a directory change is unavoidable, consider a subshell so the change does not leak into the parent shell:

```bash
(
    cd data
    tar -czf ../archive.tar.gz .
)
```

Or in one line:

```bash
(cd data && tar -czf ../archive.tar.gz .)
```

If you need to change directories in the current shell, use `pushd` and `popd` as a pair:

```bash
pushd some/directory
# Do something here
popd
```

### Auto cd to the script directory (use with caution)
If a script should always start from its own directory, add this near the top:

```bash
cd $(dirname "$0")
```

This establishes a predictable starting location and avoids failures caused by incorrect relative paths.

Do not use this pattern everywhere.
In most cases, only the top-level entry script, the one invoked directly by the user, should do this.

Helper scripts usually should not force their own working directory.
They should inherit the caller’s working directory unless there is a clear reason not to.


### Automatically skip completed tasks
In long or iterative workflows, you need a way to avoid re-running work that has already completed.
A common pattern is to create a marker file:

```bash
[ -f task-name.done ]  || {
    # Do something here

    touch task-name.done
}
```

This checks for `task-name.done`.
If the file is missing, the block runs; if the block succeeds, the marker file is created.
On the next run, the task is skipped.

It is often useful to log skipped tasks:

```bash
[ -f task-name.done ] && echo "skip <task-name>"  || {
    # Do something here

    touch task-name.done
}
```

This makes script output easier to read during debugging and maintenance.

To re-run the task, delete the corresponding `task-name.done` file.

If the task already produces a clear output artifact, you can check for that file instead of maintaining a separate marker.


### Limited retries

Some commands fail transiently and should be retried a limited number of times:

```bash
EXIT_CODE=0
for i in {1..5}; do
    some_flaky_command && break || EXIT_CODE=$?
    sleep 5
done
[ $EXIT_CODE -eq 0 ] || exit $EXIT_CODE
```

Here the script retries `some_flaky_command` up to five times, with a five-second delay between attempts.
If every attempt fails, the script exits with the last non-zero status.


## Writing complex workflows (using [TESLA] as an example)

Building a workflow does not always require a dedicated framework.
In many cases, solid scripting practices and a well-structured project layout are enough.
With Bash and [Oh-My-Batch], you can build robust workflows without introducing much additional machinery.

### Directory planning

A common approach for a Bash-based workflow project is to organize the repository around
configuration, data, scripts, and runtime directories.

The configuration directory stores software configuration, parameter files, templates,
and other small data files.
Because these files are updated frequently, they are usually tracked in Git.

The data directory stores large static assets required by the workflow, such as model weights and datasets.
These files can be managed with Git LFS, or stored externally and downloaded into a local cache when needed.

The script directory stores workflow scripts and related source code.
Like configuration files, these files should normally be version-controlled with Git.

The runtime directory stores data generated while the workflow is running.
This data is often large, so it is usually excluded from Git, cleaned up when appropriate,
or archived to platforms such as Zenodo after the run completes.

Finally, one or more entry scripts are used to orchestrate the workflow.
They start the job and provide a central place to define adjustable parameters.

In the [TESLA] example:

`00-config` is the configuration directory.
It stores software configuration templates, command templates for launching software,
HPC environment templates, and small input data such as initial structures.
Because this example does not rely on large static assets, there is no separate data directory.

`10-workflow` is the script directory.
It contains the one-time initialization script `setup.sh`,
as well as iteration scripts such as `iter-classic-dp-lammps-cp2k.sh`.

Runtime data is stored under `20-workdir`,
which is excluded through `.gitignore` and not tracked in version control.

`run.sh` is the entry script for the workflow.
It is responsible for orchestration and for defining adjustable parameters.

[Oh-My-Batch]: https://github.com/link89/oh-my-batch
[ai2-kit]: https://github.com/chenggroup/ai2-kit
[TESLA]: ../examples/tesla/
