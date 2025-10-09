# DATA-MC Plots

## To use the code for just variable use
```
python3 norm.py \
    --year 2024 \
    --variables "FatJet_pt_nom[index_gFatJets[0]]" \
    --cuts "((channel==0) && (HTTvis_deltaR<1.5) && (abs(Hbb_met_phi)>1) && (HTTvis_m>20) && (softdropmassnom>=30) && (X_m>750)&&(X_m<5500))" \
    --weights xsWeight \
    --set_maximum 1e6 \
    --log_scale \
    --Channel tt \
    --dataMC 
```

for cuts, you can use ```channel = {0,1,2}``` for Tau-Tau, Tau-Electron and Tau-Muon respectively

    For batch mode, you can use the bash script ```signal_background.sh```


