# Change Log

## v0.5.2
* `omb combo make_files` support ignore_error 

## v0.5.1
* `omb combo make_files` support extra_vars_from_file

## v0.5.0
* `omb batch` add_work_dirs support --abs

## v0.4.9
* `omb batch` support full concurrency

## v0.4.8
* implement `omb job slurm wait` command

## v0.4.7
* `omb job slurm submit` raise error on fail job 

## v0.4.6
* don't inject script to `omb batch`

## v0.4.5
* chore: fix fire version

## v0.4.4
* feat: `omb combo add_randint` support `--uniq` option

## v0.4.3
* feat: implement `omb combo show_combos`

## v0.4.2
* breaking: rename `add_files_as_one` to `add_file_set`

## v0.4.1
* feat: implement `omb combo run_cmd`

## v0.4.0
* breaking: use `set_broadcast` to replace `--broadcast` in `omb combo` command

## v0.3.2
* feat: tempate file path should support variables

## v0.3.1
* fix: ensure_dir

## v0.3.0
* breaking: change `omb combo make_files` API

## v0.2.5
* fix: change normpath method

## v0.2.4
* fix: util: ensure_dir 

## v0.2.3
* feat: implement `omb combo print` command

## v0.2.2
* refactor: change default template delimiter from `$` to `@`
* feat: `omb combo add_files_as_one` support `json-list` and `json-item` format

## v0.2.1
* feat: implement `omb misc export-shell-func`

## v0.2.0
* breaking: change `omb batch` api, check with `omb batch`

## v0.1.1
* fix: use absolute path as cache key in `omb job`

## v0.1.0
* feat: implement `omb combo`, `omb batch`, `omb job` commands
