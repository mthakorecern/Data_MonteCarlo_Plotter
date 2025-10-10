#!/bin/bash
MAX_JOBS=40
JOB_COUNT=0

run_job() {
    python3 norm.py "$@" &
    ((JOB_COUNT++))
    if (( JOB_COUNT >= MAX_JOBS )); then
        wait -n   # wait for one job to finish before launching next
        ((JOB_COUNT--))
    fi
}



# && (HTTvis_deltaR<1.5) && (abs(Hbb_met_phi)>1) && (HTTvis_m>20) && (softdropmassnom>=30) && (X_m>750)&&(X_m<5500))

# Define your cuts
cuts_TT="(channel==0)"
cuts_ET="(channel==1)"
cuts_MT="(channel==2)"

# Variables for LOG scale (pt, mass, MET, HTT mass, etc.)
variables_log=(
    
    #"FatJet_pt_nom[index_gFatJets[0]]"
    "FatJet_pt[index_gFatJets[0]]"
    #"PuppiMET_pt_nom"
    "PuppiMET_pt"
)
    

# Variables for NORMAL (linear) scale (eta, phi, counts, etc.)
variables_linear=(

    "PV_npvsGood"
    "PV_npvs"

    "Tau_pt[index_gTaus]"
    "Tau_eta[index_gTaus]"
    "Tau_phi[index_gTaus]"

    "boostedTau_pt[index_gboostedTaus]"
    "boostedTau_eta[index_gboostedTaus]"
    "boostedTau_phi[index_gboostedTaus]"

    #"FatJet_mass_nom[index_gFatJets[0]]"
    "FatJet_mass[index_gFatJets[0]]"
    
    #"FatJet_msoftdrop_nom[index_gFatJets[0]]"
    "FatJet_msoftdrop[index_gFatJets[0]]"
    "FatJet_particleNetLegacy_mass[index_gFatJets[0]]"
    
    "FatJet_eta[index_gFatJets[0]]"
    "FatJet_phi[index_gFatJets[0]]"

    "Electron_pt[index_gElectrons[0]]"
    "Electron_eta[index_gElectrons[0]]"
    "Electron_phi[index_gElectrons[0]]"

    "Muon_pt[index_gMuons[0]]"
    "Muon_eta[index_gMuons[0]]"
    "Muon_phi[index_gMuons[0]]"
    
    #"PuppiMET_phi_nom"
    "PuppiMET_phi"
    
    #"Jet_pt_nom[index_gJets[0]]"
    "Jet_pt[index_gJets[0]]"

    "Jet_pt[index_gJets[0]]"
    "Jet_eta[index_gJets[0]]"
    "Jet_eta[index_gJets[0]]"

    "ngood_Jets"
    "ngood_LooseJets"
    "ngood_MediumJets"
    "ngood_TightJets"

    "HTT_m"
    "HTTvis_m"
    "HTT_pt"
    "HTT_phi"
    "HTT_eta"

    "Hbb_met_phi"
    "allTaus_decayMode"

    "HTTvis_HPS_m"
    "HTTvis_HPS_eta"
    "HTTvis_HPS_phi"
    "HTTvis_boosted_m"
    "HTTvis_boosted_eta"
    "HTTvis_boosted_phi"

    "HTT_HPS_m"
    "HTT_HPS_eta"
    "HTT_HPS_phi"
    "HTT_boosted_m"
    "HTT_boosted_eta"
    "HTT_boosted_phi"

    "HTT_HPS_Ele_m"
    "HTT_HPS_Ele_eta"
    "HTT_HPS_Ele_phi"
    "HTT_HPS_Mu_m"
    "HTT_HPS_Mu_eta"
    "HTT_HPS_Mu_phi"
    "HTT_boosted_Ele_m"
    "HTT_boosted_Ele_eta"
    "HTT_boosted_Ele_phi"
    "HTT_boosted_Mu_m"
    "HTT_boosted_Mu_eta"
    "HTT_boosted_Mu_phi"
)

############################################
# --------- LOOP FOR LOG VARIABLES ---------
############################################

for var in "${variables_log[@]}"; do
    for ch in tt et mt; do
        cut_var="cuts_${ch^^}"

        run_job \
            --year 2024 \
            --variables "$var" \
            --cuts "${!cut_var}" \
            --weights xsWeight \
            --set_maximum 1e6 \
            --log_scale \
            --Channel $ch \
            --dataMC \
            &> log_${ch}_${var}_dataMC.txt &

        # run_job \
        #     --year 2024 \
        #     --variables "$var" \
        #     --cuts "${!cut_var}" \
        #     --weights xsWeight \
        #     --set_maximum 1e5 \
        #     --log_scale \
        #     --Channel $ch \
        #     --signals_only \
        #     &> log_${ch}_${var}_signals_only.txt &

        # run_job \
        #     --year 2024 \
        #     --variables "$var" \
        #     --cuts "${!cut_var}" \
        #     --weights xsWeight \
        #     --set_maximum 1e5 \
        #     --log_scale \
        #     --Channel $ch \
        #     &> log_${ch}_${var}_SignalandBackground.txt &
    done
done

############################################
# -------- LOOP FOR LINEAR VARIABLES -------
############################################

for var in "${variables_linear[@]}"; do
    for ch in tt et mt; do
        cut_var="cuts_${ch^^}"

        run_job \
            --year 2024 \
            --variables "$var" \
            --cuts "${!cut_var}" \
            --weights xsWeight \
            --Channel $ch \
            --dataMC \
            &> log_${ch}_${var}_dataMC.txt &

        # run_job \
        #     --year 2024 \
        #     --variables "$var" \
        #     --cuts "${!cut_var}" \
        #     --weights xsWeight \
        #     --Channel $ch \
        #     --signals_only \
        #     &> log_${ch}_${var}_signals_only.txt &

        # run_job \
        #     --year 2024 \
        #     --variables "$var" \
        #     --cuts "${!cut_var}" \
        #     --weights xsWeight \
        #     --Channel $ch \
        #     &> log_${ch}_${var}_SignalandBackground.txt &
    done
done



# python3 norm.py \
#     --year 2024 \
#     --variables "FatJet_pt_nom[index_gFatJets[0]]" \
#     --cuts "((channel==0) && (HTTvis_deltaR<1.5) && (abs(Hbb_met_phi)>1) && (HTTvis_m>20) && (softdropmassnom>=30) && (X_m>750)&&(X_m<5500))" \
#     --weights xsWeight \
#     --set_maximum 1e6 \
#     --log_scale \
#     --Channel tt \
#     --dataMC 