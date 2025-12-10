#!/usr/bin/env python3
import concurrent.futures
import subprocess
import os
import threading
from tqdm import tqdm

MAX_JOBS = 40

##Run2cuts

#'xsWeight*pileupcorrWeight*topptWeight*combinedWZgenPtDeborahWeight*eleidWeight*elerecoWeight*muonidWeight*muonisoWeight*hpstauidWeight*metsfWeight*(((channel==0)&&(HTTvis_deltaR<1.5)&&(abs(Hbb_met_phi)>1)&&(HTTvis_m>20)&&(softdropmassnom>=30)) && (X_m>750) && (X_m<5500))')

# cuts = {
#     "tt": "((channel==0) && (Flag_JetVetoed==0) && (Flag_FatJetVetoed==0) && boostedTau_rawBoostedDeepTauRunIIv2p0VSjet >= 0.95 && softdropmass >= 30 && PuppiMET_pt >= 200 && FatJet_pt[index_gFatJets[0]] >=200)",
#     "et": "((channel==1) && (Flag_JetVetoed==0) && (Flag_FatJetVetoed==0) && boostedTau_rawBoostedDeepTauRunIIv2p0VSjet >= 0.95  && softdropmass >= 30 && PuppiMET_pt >= 200 && FatJet_pt[index_gFatJets[0]] >=200)",
#     "mt": "((channel==2) && (Flag_JetVetoed==0) && (Flag_FatJetVetoed==0) && boostedTau_rawBoostedDeepTauRunIIv2p0VSjet >= 0.95  && softdropmass >= 30 && PuppiMET_pt >= 200 && FatJet_pt[index_gFatJets[0]] >=200)",
# }

# cuts = {
#     "tt": "((channel==0) && PuppiMET_pt > 180 && (boost==0) && (Flag_JetVetoed==0) && (Flag_FatJetVetoed==0))",
#     "et": "((channel==1) && PuppiMET_pt > 180  && (boost==0) && (Flag_JetVetoed==0) && (Flag_FatJetVetoed==0))",
#     "mt": "((channel==2) && PuppiMET_pt > 180  && (boost==0) && (Flag_JetVetoed==0) && (Flag_FatJetVetoed==0))",
# }


# cuts = {
#     "tt": "((channel==0) && (boost==0))",
#     "et": "((channel==1) && (boost==0))",
#     "mt": "((channel==2) && (boost==0))",
# }
# cuts = {
#     "tt": "((channel==0)  && (Flag_JetVetoed==0) && (Flag_FatJetVetoed==0))",
#     "et": "((channel==1)  && (Flag_JetVetoed==0) && (Flag_FatJetVetoed==0))",
#     "mt": "((channel==2)  && (Flag_JetVetoed==0) && (Flag_FatJetVetoed==0))",
# }

# cuts = {
#     "tt": "((channel==0))",
#     "et": "((channel==1))",
#     "mt": "((channel==2))",
# }

#&& (HTTvis_deltaR > 3 && HTTvis_deltaR < 3.2) && 
## && (FatJet_eta[index_gFatJets[0]] > 1.2 && FatJet_eta[index_gFatJets[0]] < 1.4)

cuts = {
    # "tt": "((channel==0) && (boost==1) && PuppiMET_pt > 180 && (Flag_JetVetoed==0) && (Flag_FatJetVetoed==0))",
    
    # "et": "((channel==1) && (boost==1) && PuppiMET_pt > 180 && (Flag_JetVetoed==0) && (Flag_FatJetVetoed==0))",
    
    "mt": "((channel==2) && (boost==1) && PuppiMET_pt > 180 && (Flag_JetVetoed==0) && (Flag_FatJetVetoed==0))",
}
#"((channel==0) && PuppiMET_pt > 180 && (boost==1) && (Flag_JetVetoed==0) && (Flag_FatJetVetoed==0))"


variables_log = [
    "FatJet_pt[index_gFatJets[0]]",
    "PuppiMET_pt",
    "Tau_rawDeepTau2018v2p5VSjet[index_gTaus]",
    "boostedTau_rawBoostedDeepTauRunIIv2p0VSjet[index_gboostedTaus]"

]

variables_linear = [

    "FatJet_mass[index_gFatJets[0]]",
    "FatJet_msoftdrop[index_gFatJets[0]]",
    "FatJet_particleNetLegacy_mass[index_gFatJets[0]]",
    
    "FatJet_eta[index_gFatJets[0]]",
    "FatJet_phi[index_gFatJets[0]]",   
    "PV_npvsGood",
    "PV_npvs",

    "Tau_pt[index_gTaus]",
    "Tau_eta[index_gTaus]",
    "Tau_phi[index_gTaus]",

    "Tau_pt[index_gTaus[0]]",
    "Tau_eta[index_gTaus[0]]",
    "Tau_phi[index_gTaus[0]]",
    
    "Tau_pt[index_gTaus[1]]",
    "Tau_eta[index_gTaus[1]]",
    "Tau_phi[index_gTaus[1]]",

    "boostedTau_pt[index_gboostedTaus]",
    "boostedTau_eta[index_gboostedTaus]",
    "boostedTau_phi[index_gboostedTaus]",

    "boostedTau_pt[index_gboostedTaus[0]]",
    "boostedTau_eta[index_gboostedTaus[0]]",
    "boostedTau_phi[index_gboostedTaus[0]]",
    
    "boostedTau_pt[index_gboostedTaus[1]]",
    "boostedTau_eta[index_gboostedTaus[1]]",
    "boostedTau_phi[index_gboostedTaus[1]]",

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

    "Hbb_lep1_deltaR",
    "Hbb_lep2_deltaR",

    "deltaR_tau_ele",
    "deltaR_tau_mu",
    "deltaPhi_tau_ele",
    "deltaPhi_tau_mu",
    "deltaPhi_tau1_tau2",
    "deltaR_tau1_tau2",
    
    "deltaR_hbb_httvis",
    "deltaR_hbb_htt",
    "deltaPhi_hbb_httvis",
    "deltaPhi_hbb_htt",
    "deltaPhi_hbb_leadingtau",
    "deltaPhi_hbb_subleadingtau",
    "deltaPhi_hbb_leadingele",
    "deltaPhi_hbb_leadingmu",
    
    "deltaPhi_met_tautau",
    "deltaPhi_met_leadingtau",
    "deltaPhi_met_subleadingtau",
    "deltaPhi_met_leadingele",
    "deltaPhi_met_leadingmu",

    "fatjet_tau21",
    "fatjet_tau32",

    "deltaR_subjets",
    "deltaPhi_subjets",


    "subjet1_tau21",
    "subjet1_tau32",
    "subjet2_tau21",
    "subjet2_tau32",

    "deltaR_subjet1_leadtau",
    "deltaPhi_subjet1_leadtau",
    "deltaR_subjet1_subtau",
    "deltaPhi_subjet1_subtau",
    "deltaR_subjet1_ele",
    "deltaPhi_subjet1_ele",
    "deltaR_subjet1_mu",
    "deltaPhi_subjet1_mu",

    "deltaR_subjet2_leadtau",
    "deltaPhi_subjet2_leadtau",
    "deltaR_subjet2_subtau",
    "deltaPhi_subjet2_subtau",
    "deltaR_subjet2_ele",
    "deltaPhi_subjet2_ele",
    "deltaR_subjet2_mu",
    "deltaPhi_subjet2_mu",

    "Tau_rawDeepTauVSjet_logit",
    "boostedTau_rawDeepTauVSjet_logit",

    "pt_balance_hbb_htt",
    "deltaR_hbb_ak4lead",
    "deltaPhi_hbb_ak4lead",

    "deltaR_ak4_leadtau",
    "deltaPhi_ak4_leadtau",
    "deltaR_ak4_subtau",
    "deltaPhi_ak4_subtau",

    "deltaR_ak4_ele",
    "deltaPhi_ak4_ele",

    "deltaR_ak4_mu",
    "deltaPhi_ak4_mu",

    "deltaPhi_met_ak4lead",

    "deltaR_httvis_ak4lead",
    "deltaPhi_httvis_ak4lead"
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
        for ch in ["mt"]:#"tt", "et", "mt"]:
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
                "--data_only",
                log_name,
            ]

    for var in variables_linear:
        for ch in ["mt"]:#["tt", "et", "mt"]:
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
                "--data_only",
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