# dynacat test

A workflow written based on `oh-my-batch`, includes:

* Training 4 deepmd models using 4 different random seeds with the same configuration and dataset.
* Running LAMMPS dynamics simulations using these 4 models.
* Execution

Please modify the `DP_DATASET` in `workflow.sh` to point to your dataset location, then execute the script


```bash
./workflow.sh
``` 
