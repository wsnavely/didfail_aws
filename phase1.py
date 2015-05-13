import phase1_config
import command
import sys
import errno
import os
import os.path
import tempfile
import logging

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

def run_transformer(
        apkpath, 
        outdir, 
        logfile,
        jvm_flags=phase1_config.transform_jvm_flags,
        classpath=phase1_config.transform_classpath,
        platformpath=phase1_config.sdk_platforms,
        timeout=phase1_config.transform_timeout,
        monitor=phase1_config.transform_monitor):
    args = []
    args += jvm_flags
    args += ["-cp", classpath]
    args += ["TransformAPKs_IntentSinks"]
    args += ["-android-jars", platformpath]
    args += ["-process-dir", apkpath]
    args += ["-output-dir", outdir]
    cmd = command.Command(
                phase1_config.java_bin, 
                args, 
                monitor=monitor, 
                stdout=logfile, 
                stderr=logfile,
                statslog=logfile + ".stats")
    result = cmd.run(timeout)
    apk_name = os.path.basename(apk_path)
    success = os.path.exists(os.path.join(outdir, apk_name))
    return (success, result)

def run_dare(
        apkpath, 
        outdir, 
        logfile,
        cwd=phase1_config.dare_base,
        timeout=phase1_config.dare_timeout,
        monitor=phase1_config.dare_monitor):
    apk_name = os.path.basename(apk_path)
    outpath = os.path.join(outdir, apk_name)
    args = []
    args += ["-d", outpath]
    args += [apkpath]
    cmd = command.Command(
                phase1_config.dare_exec, 
                args, 
                monitor=monitor, 
                stdout=logfile, 
                stderr=logfile, 
                cwd=cwd,
                statslog=logfile + ".stats")
    result = cmd.run(timeout)
    success = os.path.exists(outpath)
    return (success, result)

def run_flowdroid(
        apkpath, 
        outdir, 
        logfile,
        cwd=phase1_config.fd_android_base,
        jvm_flags=phase1_config.fd_jvm_flags,
        classpath=phase1_config.fd_classpath,
        platformpath=phase1_config.sdk_platforms,
        timeout=phase1_config.fd_timeout,
        monitor=phase1_config.fd_monitor):
    apk_name = os.path.basename(apk_path)
    outfile = apk_name + ".fd.xml"
    outpath = os.path.join(outdir, outfile)
    args = []
    args += jvm_flags
    args += ["-Dfile.encoding=UTF-8"]
    args += ["-cp", classpath]
    args += ["soot.jimple.infoflow.android.TestApps.Test"]
    args += [apkpath]
    args += [platformpath]
    args += ["--nostatic"]
    args += ["--aplength", "1"]
    args += ["--aliasflowins"]
    args += ["--out", outpath]

    cmd = command.Command(
                phase1_config.java_bin, 
                args, 
                cwd=cwd, 
                monitor=monitor, 
                stdout=logfile, 
                stderr=logfile,
                statslog=logfile + ".stats")
    result = cmd.run(timeout)
    success = os.path.exists(outpath)
    return (success, result)

def run_epicc(
        apkpath, 
        outdir, 
        dare_output,
        logfile,
        jvm_flags=phase1_config.epicc_jvm_flags,
        classpath=phase1_config.epicc_classpath,
        epicc_jar=phase1_config.epicc_jar,
        platformpath=phase1_config.sdk_platforms,
        timeout=phase1_config.epicc_timeout,
        monitor=phase1_config.epicc_monitor):
    apk_name = os.path.basename(apk_path)
    pkg_name = os.path.splitext(apk_name)[0]
    outfile = apk_name + ".epicc"
    outpath = os.path.join(outdir, outfile)
    android_dir = os.path.join(dare_output, apk_name) + "/retargeted/" + pkg_name
    args = []
    args += jvm_flags
    args += ["-jar", epicc_jar]
    args += ["-apk", apkpath]
    args += ["-android-directory", android_dir]
    args += ["-cp", classpath]
    cmd = command.Command(
                phase1_config.java_bin,
                args,
                monitor=monitor,
                stderr=logfile,
                stdout=outpath,
                statslog=logfile + ".stats")
    result = cmd.run(timeout)
    success = os.path.exists(outpath)
    return (success, result)

def run_extract_manifest(
        apkpath,
        outdir,
        logfile,
        jarpath=phase1_config.manifest_jarpath):
    mfile = os.path.basename(apkpath) + ".manifest.xml"
    mpath = os.path.join(outdir, mfile)
    unzip_cmd = "unzip -p {0} AndroidManifest.xml > {1} 2>> {2}"
    xml_cmd = phase1_config.java_bin + " -cp {0} test.AXMLPrinter {1} > {2} 2>> {3}"
    with tempfile.NamedTemporaryFile() as tmp:
        unzip = unzip_cmd.format(apkpath, tmp.name, logfile)
        printxml = xml_cmd.format(jarpath, tmp.name, mpath, logfile)
        logging.debug("Extract Manifest Command: " + unzip)
        os.system(unzip)
        logging.debug("Extract Manifest Command: " + printxml)
        os.system(printxml)
    return (os.path.exists(mpath), None)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "Usage: outdir apk1 apk2 ... apkN"
        exit(-1)

    logging.basicConfig(level=phase1_config.log_level)
    outdir = os.path.abspath(os.sys.argv[1])
    log_dir = os.path.join(outdir, "log")
    transform_dir = os.path.join(outdir, "transform")
    flowdroid_dir = os.path.join(outdir, "flowdroid")
    dare_dir = os.path.join(outdir, "dare")
    epicc_dir = os.path.join(outdir, "epicc")
    mkdir_p(log_dir)
    mkdir_p(transform_dir)
    mkdir_p(flowdroid_dir)
    mkdir_p(dare_dir)
    mkdir_p(epicc_dir)

    task_status = None
   
    for apk in (x for x in sys.argv[2:]):
        if task_status != None:
            for k in sorted(task_status.keys()):
                logging.info("\t".join(["DidFailTaskStatus", k] + map(str,list(task_status[k]))))

        task_status = {}
        task_status["APKTransformer"] = (apk, "SKIPPED", 0.0)
        task_status["ExtractManifest"] = (apk, "SKIPPED", 0.0)
        task_status["FlowDroid"] = (apk, "SKIPPED", 0.0)
        task_status["Dare"] = (apk, "SKIPPED", 0.0)
        task_status["Epicc"] = (apk, "SKIPPED", 0.0)

        apk_path = os.path.abspath(apk)
        apk_name = os.path.basename(apk_path)
        apk_transform_log = os.path.join(log_dir, apk_name + "_transform")
        fd_log = os.path.join(log_dir, apk_name + "_flowdroid")
        dare_log = os.path.join(log_dir, apk_name + "_dare")
        epicc_log = os.path.join(log_dir, apk_name + "_epicc")

        logging.info("Processing APK: " + apk_path)
        logging.info("Running APK Transformer...")
        (success, stats) = run_transformer(apk_path, transform_dir, apk_transform_log)
        if not success:
            logging.info("FAILURE: APK Transformer failed")
            if stats[2]:
                task_status["APKTransformer"] = (apk, "TIMEOUT", stats[1])
            else:
                task_status["APKTransformer"] = (apk, "FAILED", stats[1])
            continue
        else:
            task_status["APKTransformer"] = (apk, "SUCCESS", stats[1])
              
        transformed_apk = os.path.join(transform_dir, apk_name)
            
        logging.info("Running Extract Manifest...")
        (success, stats) = run_extract_manifest(apk_path, transform_dir, apk_transform_log)
        if not success:
            task_status["ExtractManifest"] = (apk, "FAILED", 0.0)
            logging.info("FAILURE: Extract manifest failed")
            continue
        else:
            task_status["ExtractManifest"] = (apk, "SUCCESS", 0.0)

        logging.info("Running FlowDroid...")
        (success, stats) = run_flowdroid(transformed_apk, flowdroid_dir, fd_log)
        if not success:
            logging.info("FAILURE: Flowdroid failed")
            if stats[2]:
                task_status["FlowDroid"] = (apk, "TIMEOUT", stats[1])
            else:
                task_status["FlowDroid"] = (apk, "FAILED", stats[1])
            continue
        else:
            task_status["FlowDroid"] = (apk, "SUCCESS", stats[1])

        logging.info("Running dare...")
        (success, stats) = run_dare(transformed_apk, dare_dir, dare_log)
        if not success:
            logging.info("FAILURE: dare failed")
            if stats[2]:
                task_status["Dare"] = (apk, "TIMEOUT", stats[1])
            else:
                task_status["Dare"] = (apk, "FAILED", stats[1])
            continue
        else:
            task_status["Dare"] = (apk, "SUCCESS", stats[1])

        logging.info("Running epicc...")
        (success, stats) = run_epicc(transformed_apk, epicc_dir, dare_dir, epicc_log)
        if not success:
            logging.info("FAILURE: epicc failed")
            if stats[2]:
                task_status["Epicc"] = (apk, "TIMEOUT", stats[1])
            else:
                task_status["Epicc"] = (apk, "FAILED", stats[1])
            continue
        else: 
            task_status["Epicc"] = (apk, "SUCCESS", stats[1])

if task_status != None:
     for k in sorted(task_status.keys()):
         logging.info("\t".join(["DidFailTaskStatus", k] + map(str, list(task_status[k]))))
