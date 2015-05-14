# didfail_aws
These are some Python scripts for running the Didfail static analyzer over a set of APKs. At the moment, only the first phase of the analysis is automated.

## phase1.py
Phase 1 of Didfail takes as input a list of APK files, and produces a taint flow analysis for each APK.  APKs are processed in isolation in this phase.  `phase1.py` automates this phase.  The main tasks are enumerated below.

####1. APK Transformer
Marks Intent-sending methods with unique IDs, so that the output of Epicc can be correlated with the output of FlowDroid.  This is a Java program written on top of the Soot framework.  This task takes an APK file as input, and outputs an instrumented APK.
####2. Dare and Epicc
Dare retargets the transformed APK to vanilla Java bytecode (from Dalvik), so that it can be processed by Epicc, which outputs various information regarding the Intents sent/received by a given APK.
####3. FlowDroid
FlowDroid takes the transformed APK as input, and performs static taint analysis.

#### Basic Usage
The basic usage for `phase1.py` is:
```
python phase1.py <outdir> <apk1> <apk2> ... <apkN>
outdir: A directory, where the results of phase 1 should be stored
apkI: A path to an APK file.
```
The structure of the output directory is as follows:
```
outdir
|------dare
       |------Output from Dare for all APKS 
|------epicc
       |------Output from epicc for all APKS
|------flowdroid
       |------Output from flowdroid for all APKS
|------log
       |------Log files for all tools
|------transform
       |------Output from the APK transformer for all APKS
```
The output of this script can be controlled via the `log_level` variable in the configuration, described below.  Summary information about each command executed is outputted by default, in this format.
```
INFO:root:DidFailTaskStatus     APKTransformer  /home/ubuntu/apk_samples/BOOKS_AND_REFERENCE/joansoft.dailybible.apk    SUCCESS 61.2379238605
INFO:root:DidFailTaskStatus     Dare    /home/ubuntu/apk_samples/BOOKS_AND_REFERENCE/joansoft.dailybible.apk    SKIPPED 0.0
INFO:root:DidFailTaskStatus     Epicc   /home/ubuntu/apk_samples/BOOKS_AND_REFERENCE/joansoft.dailybible.apk    SKIPPED 0.0
INFO:root:DidFailTaskStatus     ExtractManifest /home/ubuntu/apk_samples/BOOKS_AND_REFERENCE/joansoft.dailybible.apk    SUCCESS 0.0
INFO:root:DidFailTaskStatus     FlowDroid       /home/ubuntu/apk_samples/BOOKS_AND_REFERENCE/joansoft.dailybible.apk    FAILED  81.4125051498
```
This information can easily be extracted to compute statistics for a given run.

#### Configuration
Very granular configuration of the phase 1 is facilitated by editing `phase1_config.py`.  This file is used by `phase1.py` to locate the various binaries required for phase 1 analysis; for example, FlowDroid, Epicc, Soot, etc.

#### Running on AWS
A virtual machine image was created for running DidFail phase 1. The id of this image is: `ami-b2b6a5da`.  After launching an instance from this image, you can run phase 1 as follows:
```
cd ~/pythonrunner/phase1/didfail_aws
~/pythonrunner/phase1/didfail_aws$ python phase1.py output ~/apk_samples/BOOKS_AND_REFERENCE/joansoft.dailybible.apk
```
Some sample APKs are included in `~/apk_samples`.  For large runs, ensure the directory you are writing to has enough space to hold the output.  The root volumes on these VMs often are too small for the task. 

## Phase 2
Phase 2 involves correlating the output from Phase 1 to construct tainted flows between applications.  This repository currently only has code for automating phase 1. 


