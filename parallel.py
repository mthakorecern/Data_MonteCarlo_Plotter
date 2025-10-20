#!/usr/bin/env python3
import concurrent.futures
import subprocess
import os
import threading
from tqdm import tqdm

MAX_JOBS = 40

cuts = {
    "tt": "((channel==0) && (Flag_JetVetoed==0) && (Flag_FatJetVetoed==0))",
    "et": "((channel==1) && (Flag_JetVetoed==0) && (Flag_FatJetVetoed==0))",
    "mt": "((channel==2) && (Flag_JetVetoed==0) && (Flag_FatJetVetoed==0))",
}

variables_log = [
    "FatJet_pt[index_gFatJets[0]]",
    "PuppiMET_pt",
]

variables_linear = [
    "PV_npvsGood",
    "PV_npvs",

    "Tau_pt[index_gTaus]",
    "Tau_eta[index_gTaus]",
    "Tau_phi[index_gTaus]",

    "boostedTau_pt[index_gboostedTaus]",
    "boostedTau_eta[index_gboostedTaus]",
    "boostedTau_phi[index_gboostedTaus]",

    "FatJet_mass[index_gFatJets[0]]",
    "FatJet_msoftdrop[index_gFatJets[0]]",
    "FatJet_particleNetLegacy_mass[index_gFatJets[0]]",
    "FatJet_eta[index_gFatJets[0]]",
    "FatJet_phi[index_gFatJets[0]]",

    "Electron_pt[index_gElectrons[0]]",
    "Electron_eta[index_gElectrons[0]]",
    "Electron_phi[index_gElectrons[0]]",

    "Muon_pt[index_gMuons[0]]",
    "Muon_eta[index_gMuons[0]]",
    "Muon_phi[index_gMuons[0]]",

    "PuppiMET_phi",

    "Jet_pt[index_gJets[0]]",
    "Jet_eta[index_gJets[0]]",
    "Jet_phi[index_gJets[0]]",

    "HTTvis_deltaR",

    "ngood_Jets",
    "ngood_LooseJets",
    "ngood_MediumJets",
    "ngood_TightJets",

    "HTT_m",
    "HTTvis_m",
    "HTT_pt",
    "HTT_phi",
    "HTT_eta",

    "Hbb_met_phi",

    "allTaus_decayMode",

    "HTTvis_HPS_m",
    "HTTvis_HPS_eta",
    "HTTvis_HPS_phi",
    "HTTvis_boosted_m",
    "HTTvis_boosted_eta",
    "HTTvis_boosted_phi",

    "HTT_HPS_m",
    "HTT_HPS_eta",
    "HTT_HPS_phi",

    "HTT_boosted_m",
    "HTT_boosted_eta",
    "HTT_boosted_phi",

    "HTT_HPS_Ele_m",
    "HTT_HPS_Ele_eta",
    "HTT_HPS_Ele_phi",

    "HTT_HPS_Mu_m",
    "HTT_HPS_Mu_eta",
    "HTT_HPS_Mu_phi",
    
    "HTT_boosted_Ele_m",
    "HTT_boosted_Ele_eta",
    "HTT_boosted_Ele_phi",
    
    "HTT_boosted_Mu_m",
    "HTT_boosted_Mu_eta",
    "HTT_boosted_Mu_phi",
]

print_lock = threading.Lock()
progress_bar = None

def safe_print(*args, **kwargs):
    with print_lock:
        print(*args, **kwargs)

def run_job(args):
    global progress_bar
    cmd = ["python3", "norm.py"] + args[:-1]
    log_file = args[-1]

    with open(log_file, "w") as f:
        result = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)

    with print_lock:
        if progress_bar:
            progress_bar.update(1)
            if result.returncode != 0:
                progress_bar.write(f"Failed: {log_file}")
    return result.returncode

def generate_commands():
    for var in variables_log:
        for ch in ["tt", "et", "mt"]:
            cut_expr = cuts[ch]
            safe_var = (
                var.replace("[", "")
                .replace("]", "")
                .replace("(", "")
                .replace(")", "")
                .replace("/", "_")
            )
            log_name = f"logs/log_{ch}_{safe_var}_dataMC.txt"
            yield [
                "--year", "2024",
                "--variables", var,
                "--cuts", cut_expr,
                "--weights", "xsWeight",
                "--log_scale",
                "--Channel", ch,
                "--dataMC",
                log_name,
            ]

    for var in variables_linear:
        for ch in ["tt", "et", "mt"]:
            cut_expr = cuts[ch]
            safe_var = (
                var.replace("[", "")
                .replace("]", "")
                .replace("(", "")
                .replace(")", "")
                .replace("/", "_")
            )
            log_name = f"logs/log_{ch}_{safe_var}_dataMC.txt"
            yield [
                "--year", "2024",
                "--variables", var,
                "--cuts", cut_expr,
                "--weights", "xsWeight",
                "--Channel", ch,
                "--dataMC",
                log_name,
            ]


if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    commands = list(generate_commands())
    total_jobs = len(commands)

    print(f"Launching {total_jobs} jobs with up to {MAX_JOBS} concurrent processes...\n")

    # Initialize tqdm progress bar
    progress_bar = tqdm(total=total_jobs, ncols=90, desc="Processing", unit="job")

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_JOBS) as executor:
        futures = [executor.submit(run_job, cmd) for cmd in commands]
        for _ in concurrent.futures.as_completed(futures):
            pass  # tqdm updated in run_job()

    progress_bar.close()
    print("\n All jobs finished!")
