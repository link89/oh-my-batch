# Thinking in [Oh-My-Batch]

本文档用于介绍 [Oh-My-Batch] 的设计理念和使用方法。
[Oh-My-Batch] 是一个基于命令行和 Python 的批处理脚本和工作流构建模块，
它通过提供一系列可独立使用的命令工具和 Python 模块，
帮助开发者快速通过编写一个 Shell 脚本或者 Python 脚本实现一个计算工作流，
并在本地电脑或者 HPC 集群上完成计算。

特别地，如果结合 [ai2-kit] 使用，[Oh-My-Batch] 可以用于快速开发一个组合不同计算化学软件的势函数主动学习工作流。这类工作流通常使用一个名为 TESLA 的主动学习（active learning）结构，包含 train, explore, screen, label 四个基本步骤构成的 active learning 循环。 本文档将以 TESLA 工作流的开发为例，介绍 [Oh-My-Batch] 的基本功能和使用技巧，帮助开发者快速上手。

除此之外，本文档还会介绍一些通用 Shell 技巧，这些技巧不仅可以用于 [Oh-My-Batch] 工作流，同时也可以用于其他 Shell 脚本的编写，希望对读者有所帮助。

本文档使用的相关示例代码位于 [./examples/tesla](../examples/tesla/) 目录下。


## Shell 脚本技巧
Shell 脚本是快速构建自动化工作流的常用方法，掌握一些常用的 Shell 技巧会有助于构建高效可靠的自动化脚本。这些技巧在 [TESLA] 脚本中会被大量使用，因此提前了解将有助于大家更好地阅读脚本。

### 必须遵守的脚本纪律
所谓“脚本纪律”，是指编写脚本默认所应该采用的一些规范和习惯。遵守这些纪律可以使脚本更易读、更易维护。具体包括：

#### 设置 `set -e` 快速失败
在脚本开头添加 `set -e` 可以使脚本在遇到错误时立即退出，而不是继续执行后续命令。

```bash
#!/bin/bash
set -e 
```

### 自动进入脚本所在目录
如果你希望执行脚本时自动进入脚本所在目录，可以在脚本开头添加以下代码：

```bash
cd $(dirname "$0")
```

这样一来，在后续使用相对路径时，就可以以相对脚本所在目录的方式来引用文件和目录。

### 忽略错误
如果希望一个命令在失败仍可以继续执行脚本，可以在该命令后加 `|| true` 来抑制错误。例如：

```bash
some_command || true
```
一个改进的版本是使用 `echo` 输出日志，例如：
```bash
some_command || echo "ignore error of some_command"
```
这样可以在脚本执行时输出一条日志，提示用户该命令的错误被忽略了。

### 自动跳过已完成的任务
如果一个脚本十分复杂，那么你就必需考虑如果脚本失败，或者需要修改脚本时，如何避免重复执行已经完成的任务。一个常用的技巧是使用一个标志文件来记录任务是否已经完成。它的典型结构如下：

```bash


[ -f task-name.done ]  || {
    # Do something here

    touch task-name.done
}

```
上述代码的意思是，检查 `task-name.done` 文件是否存在，如果不存在，则执行后面的代码块。如果代码块执行成功，则会创建一个名为 `task-name.done` 的文件，表示该任务已经完成。下次执行脚本时，如果该文件存在，则会跳过这个任务。

一个改进的版本如下：

```bash
[ -f task-name.done ] && echo "skip <task-name>"  || {
    # Do something here

    touch task-name.done
}
```

这个版本会在跳过任务时输出一条日志，提示用户该任务已被跳过。这有助于调试和维护脚本。

如果要重新执行一个已经完成的任务，可以删除对应的 `task-name.done` 文件。这样下次执行脚本时，就会重新执行该任务。


## 开发 [TESLA] 工作流 
### 介绍
TODO

### 约定
#### 目录结构
TODO

#### 迭代脚本`iter-` 命名规范
以 `iter-` 开头命名的脚本是 [TESLA] 工作流在每次迭代中所使用的脚本。我们建议使用以下命名格式以确保脚本的可读性：

`iter-<feature>-<software-...>-<version>.sh`

其中，
* feature 用于描述这个替代的特征，比如 `classic` 代表经典模式，`redox` 代表用于 `redox potential` 等，开发者可以根据相应的特征选取合适的名字方便记忆。
* software 用于指代使用到的软件，如 `dp`, `lammps`, `cp2k` ,`vasp`等。
* version 用于指代软件的版本号。如果在后续迭代中需要对脚本进行修改，开发者应该复制一份脚本并修改版本号，而不是直接修改原来的版本，这时就可以在原始版本上添加 version 编号进行区分。

例如，
* `iter-classic-dp-lammps-cp2k.sh` 代表使用经典模式的 `DeepMD`, `LAMMPS`, `CP2K` 的初始版本。
* `iter-classic-dp-lammps-cp2k-v1.sh` 代表使用经典模式的 `DeepMD`, `LAMMPS`, `CP2K` 的第一个改版。
* `iter-classic-dp-lammps-vasp.sh` 代表使用经典模式的 `DeepMD`, `LAMMPS`, `VASP` 的初始版本。

以此类推。

[Oh-My-Batch]: https://github.com/link89/oh-my-batch
[ai2-kit]: https://github.com/chenggroup/ai2-kit
[TESLA]: ../examples/tesla/
