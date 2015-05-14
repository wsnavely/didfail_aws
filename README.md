# didfail_aws
These are some Python scripts for running the Didfail static analyzer over a set of APKs. At the moment, only the first phase of the analysis is automated.

## Phase 1
Phase 1 of Didfail takes as input a list of APK files, and produces a taint flow analysis for each APK.  APKs are processed in isolation in this phase.  `phase1.py` automates this phase.  The main tasks are enumarated below.

####APK Transformer
Marks Intent-sending methods with unique IDs, so that the output of Epicc can be correlated with the output of FlowDroid.  This is a Java program written on top of the Soot framework.  This task takes an APK file as input, and outputs an instrumented APK.
####2. Dare and Epicc
Dare retargets the transformed APK to vanilla Java bytecode (from Dalvik), so that it can be processed by Epicc, which outputs various information regarding the Intents sent/received by a given APK.
####3. FlowDroid
FlowDroid takes the transformed APK as input, and performs static taint analysis.

## Phase 2
Phase 2 involves correlating the output from Phase 1 to construct tainted flows between applications.  This repository currently only has code for automating phase 1. 


