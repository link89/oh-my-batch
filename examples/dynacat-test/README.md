# dynacat test

基于 `oh-my-batch` 编写的一个测试工作流，该工作流完成：

* 使用相同的配置和数据集，使用4个不同的随机种子训练出 4个 deepmd 模型
* 使用这4个模型运行 lammps 动力学模拟

## 运行
请修改 `workflow.sh` 中的 `DP_DATASET` 指向数据集位置，然后运行

```bash
./workflow.sh
``` 
