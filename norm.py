import ROOT
ROOT.gROOT.SetBatch(True)  # To ensure that there's no GUI displayed in b/w while plotting
ROOT.TH1.AddDirectory(False)
ROOT.TH1.SetDefaultSumw2(True)

import argparse
import os
import glob
from samples import redirector_MC, Signals, Backgrounds
from observed import observed

from variable_dictionaries import variableAxisTitleDictionary, variableFileNameDictionary, variableSettingDictionary
import time
import re



def create_cut_string(weights, base_cut, additional_cuts, is_observed=False):
    if additional_cuts is None:
        additional_cuts = []

    all_cuts = []
    if base_cut:
        all_cuts.append(base_cut)
    if additional_cuts:
        all_cuts.extend(additional_cuts)
    if not all_cuts:
        all_cuts = ["1"]

    cut_expr = " && ".join(all_cuts)

    if is_observed:
        return f"({cut_expr})"
    else:
        return f"{weights} * ({cut_expr})"

def group_key_from_name(name: str) -> str:
    ## Strip any trailing _<digits> or variable suffix to make matching robust
    import re
    name_clean = re.sub(r"_[0-9]+$", "", name)      
    name_clean = re.sub(r"(_HTT_m.*)$", "", name_clean)  

    if any(s in name_clean for s in ["WW", "WZ", "ZZ"]):
        return "DiBoson"
    if any(s in name_clean for s in ["TWminus", "TbarWplus", "TbarBQ", "TBbarQ"]):
        return "STop"
    if "TTto" in name_clean:
        return "TTbar"
    if "QCD" in name_clean:
        return "QCD"
    if "Wto" in name_clean:
        return "WJets"
    if "DYto" in name_clean:
        return "Drell-Yan"
    if "GluGlutoRadion" in name_clean:
        return "Signal"
    return "Other"


import numpy as np
import math

def format_scientific(val, err=0, sig_val=3, sig_err=2):
    if val == 0 or not np.isfinite(val):
        return f"(0 ± {err:.{sig_err}g})"
    exponent = int(np.floor(np.log10(abs(val))))
    mantissa_val = val / 10 ** exponent
    mantissa_err = err / 10 ** exponent if err else 0
    if err:
        return f"({mantissa_val:.{sig_val}g} ± {mantissa_err:.{sig_err}g})×10^{exponent}"
    else:
        return f"{mantissa_val:.{sig_val}g}×10^{exponent}"

def get_integral_with_error(hist):
    import ctypes
    err = ctypes.c_double(0.0)
    val = hist.IntegralAndError(0, hist.GetNbinsX() + 1, err)
    return val, err.value

def get_full_path(base_dir, path):
    if os.path.isabs(path):
        return path
    return os.path.join(base_dir, path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate histograms from ROOT files.")
    parser.add_argument('--year',
                        nargs='?',
                        choices=['2024'],
                        help='Use the file\'s fake factor weightings when making plots for these files.',
                        required=True)
    parser.add_argument("--variables", nargs="+", required=True, help="Variables to plot.")
    parser.add_argument("--cuts", default="", help="Standard cut string.")
    parser.add_argument("--additional_cuts", nargs="+", default=[], help="Additional selection cuts.")
    parser.add_argument("--weights", default="FinalWeighting", help="Event weight expression.")
    parser.add_argument("--log_scale", action="store_true", help="Enable logarithmic Y-axis scaling.")
    parser.add_argument('--Channel',choices=["tt","et","mt","all","lt"], required=True)
    parser.add_argument("--signals_only", action="store_true", help="Plot signals only (skip backgrounds, stack, and error band).")
    parser.add_argument("--dataMC",action="store_true", help="Overlay observed data and draw Data/MC ratio")


    start = time.time()
    args = parser.parse_args()
    variable = args.variables[0]
    weights = args.weights
    base_cut = args.cuts
    additional_cuts_o = args.additional_cuts
    log_scale = args.log_scale
    
    for dirname in ["SignalandBackground", "Signal_only", "DataMC"]:
        os.makedirs(dirname, exist_ok=True)

    bins = variableSettingDictionary.get(variable, "21,0,1000")  
    bin_values = tuple(map(float, bins.split(',')))


    hists = {}
    integral_values = []
    hist_stack = ROOT.THStack("hist_stack", "")

    hists['DiBoson'] = ROOT.TH1F("DiBoson", "DiBoson",  int(bin_values[0]), bin_values[1], bin_values[2])
    hists['DiBoson'].Sumw2()
    hists['DiBoson'].SetDirectory(0)
    
    hists['STop'] = ROOT.TH1F("STop", "STop", int(bin_values[0]), bin_values[1], bin_values[2])
    hists['STop'].Sumw2()
    hists['STop'].SetDirectory(0)
    
    hists['TTbar'] = ROOT.TH1F("TTbar","TTbar", int(bin_values[0]), bin_values[1], bin_values[2])
    hists['TTbar'].Sumw2()
    hists['TTbar'].SetDirectory(0)
    
    hists['QCD'] = ROOT.TH1F("QCD", "QCD", int(bin_values[0]), bin_values[1], bin_values[2])
    hists['QCD'].Sumw2()
    hists['QCD'].SetDirectory(0)
    
    hists['WJets'] = ROOT.TH1F("WJets", "WJets", int(bin_values[0]), bin_values[1], bin_values[2])
    hists['WJets'].Sumw2()
    hists['WJets'].SetDirectory(0)

    hists['Drell-Yan'] = ROOT.TH1F("Drell-Yan","Drell-Yan",int(bin_values[0]), bin_values[1], bin_values[2])
    hists['Drell-Yan'].Sumw2()
    hists['Drell-Yan'].SetDirectory(0)

    hists['Other'] = ROOT.TH1F("Other", "Other", int(bin_values[0]), bin_values[1], bin_values[2])
    hists['Other'].Sumw2()
    hists['Other'].SetDirectory(0)

    hist_title = variableAxisTitleDictionary.get(variable, variable)
    
    cut_w  = create_cut_string(weights, base_cut, additional_cuts_o, is_observed=False)   
    cut_un = create_cut_string("",      base_cut, additional_cuts_o, is_observed=True)   
    print(f"Weighted selection:   {cut_w}")
    print(f"Unweighted selection: {cut_un}")

    ## We fill background histograms only when we are not plotting Signals Only Plots.
    if not args.signals_only:
        hists_by_proc   = {} 
        
        for category, sample_type in Backgrounds.items():
            for proc_name, proc_info in sample_type.items():                
                hists_by_proc.setdefault(proc_name, [])
                
                for path in proc_info["files"]:
                    full_path = get_full_path(redirector_MC, path)
                    print(f"Processing {full_path}")

                    root_file = ROOT.TFile.Open(full_path, 'READ')
                    if not root_file or root_file.IsZombie():
                        print(f"Could not open {full_path}")
                        continue
                    tree = root_file.Get("Events")
                    if not tree:
                        print(f"No Events tree in {full_path}")
                        root_file.Close()
                        continue
                    hist_name = f"{os.path.basename(path.replace('.root', ''))}_{variable}"
                    h = ROOT.TH1F(hist_name, hist_title, int(bin_values[0]), bin_values[1], bin_values[2])
                    h.SetDirectory(ROOT.gDirectory)
                    h.Reset()
                    tree.Draw(f"{variable} >> {hist_name}", cut_w)
                    h.SetDirectory(0)
                    hists_by_proc[proc_name].append(h)
                    root_file.Close()
                    print(f"Histogram bins and ranges are {int(bin_values[0]), bin_values[1], bin_values[2]}")
                    #print(f"{hist_name} has entries={h.GetEntries()} and integral={h.Integral(0, h.GetNbinsX()+1)} \n")

        for proc_name, hlist in hists_by_proc.items():
            for h in hlist:
                print(f"[DEBUG] {proc_name}: {h.GetName()} integral={h.Integral()}")
                key = group_key_from_name(h.GetName())
                print(f"[DEBUG] Grouped as: {key}")
                if key not in hists:
                    key = "Other"
                hists[key].Add(h)
        
        # print("\n--- Group integrals after filling ---")
        # for key, hist in hists.items():
        #     print(f"{key:12} : {hist.Integral(0, hist.GetNbinsX()+1):.6f}")

        # styling for category-sum histograms
        hists["DiBoson"].SetLineColor(ROOT.TColor.GetColor("#9d99bd"))
        hists["DiBoson"].SetFillColor(ROOT.TColor.GetColor("#9d99bd"))
        print("Diboson background Integral is:")
        print(hists["DiBoson"].Integral(0, hists["DiBoson"].GetNbinsX()+1))

        hists["STop"].SetLineColor(ROOT.TColor.GetColor("#a5e7fa"))
        hists["STop"].SetFillColor(ROOT.TColor.GetColor("#a5e7fa"))
        print("STop background Integral is:")
        print(hists["STop"].Integral(0, hists["STop"].GetNbinsX()+1))

        hists["TTbar"].SetLineColor(ROOT.TColor.GetColor("#92cfe0"))
        hists["TTbar"].SetFillColor(ROOT.TColor.GetColor("#92cfe0"))
        print("TTbar background Integral is:")
        print(hists["TTbar"].Integral(0, hists["TTbar"].GetNbinsX()+1))

        hists["QCD"].SetLineColor(ROOT.TColor.GetColor("#f29b6f"))
        hists["QCD"].SetFillColor(ROOT.TColor.GetColor("#f29b6f"))
        print("QCD background Integral is:")
        print(hists["QCD"].Integral(0, hists["QCD"].GetNbinsX()+1))

        hists["WJets"].SetLineColor(ROOT.TColor.GetColor("#fcd068"))
        hists["WJets"].SetFillColor(ROOT.TColor.GetColor("#fcd068"))
        print("WJets background Integral is:")  
        print(hists["WJets"].Integral(0, hists["WJets"].GetNbinsX()+1))

        hists["Drell-Yan"].SetLineColor(ROOT.TColor.GetColor("#d8ed79"))
        hists["Drell-Yan"].SetFillColor(ROOT.TColor.GetColor("#d8ed79"))
        print("Drell-Yan background Integral is:")  
        print(hists["Drell-Yan"].Integral(0, hists["Drell-Yan"].GetNbinsX()+1))

        hists["Other"].SetLineColor(ROOT.TColor.GetColor("#ffff00"))
        hists["Other"].SetFillColor(ROOT.TColor.GetColor("#ffff00"))
        print("Other background Integral is:")  
        print(hists["Other"].Integral(0, hists["Other"].GetNbinsX()+1))

        backgrounds_sum = (
            hists["DiBoson"].Integral(0, hists["DiBoson"].GetNbinsX()+1)
            + hists["STop"].Integral(0, hists["STop"].GetNbinsX()+1)
            + hists["TTbar"].Integral(0, hists["TTbar"].GetNbinsX()+1)
            + hists["QCD"].Integral(0, hists["QCD"].GetNbinsX()+1)
            + hists["WJets"].Integral(0, hists["WJets"].GetNbinsX()+1)
            + hists["Drell-Yan"].Integral(0, hists["Drell-Yan"].GetNbinsX()+1)
        )
        # val, err = get_integral_with_error(backgrounds_sum)
        # print(f"Total background integral = {format_scientific(val, err)}")
        #print(f"Sum of background Integrals is: {backgrounds_sum}")
        hist_stack.Add(hists["DiBoson"])
        hist_stack.Add(hists["STop"])
        hist_stack.Add(hists["TTbar"])
        hist_stack.Add(hists["QCD"])
        hist_stack.Add(hists["WJets"])
        hist_stack.Add(hists["Drell-Yan"])
        
    
    ## Signals are there in all the plots, we are adding them outside any if loops

    cut_sig = create_cut_string(weights, base_cut, additional_cuts_o, is_observed=False)

    # Signal 1
    sig_info = Signals["GluGlutoRadiontoHHto2B2Tau_M-1000"]
    sig_file = sig_info["files"][0]
    hist_name_1 = f"{os.path.basename(sig_file.replace('.root', ''))}_{variable}"
    root_file_1 = ROOT.TFile.Open(os.path.join(redirector_MC, sig_file), 'READ')
    tree_1 = root_file_1.Get("Events")
    signal_1 = ROOT.TH1F(hist_name_1, hist_title, int(bin_values[0]), bin_values[1], bin_values[2])
    
    ROOT.gDirectory.Delete(f"{hist_name_1};*")   
    signal_1.SetDirectory(ROOT.gDirectory)
    tree_1.Draw(f"{variable} >> {hist_name_1}", cut_sig)
    signal_1.SetDirectory(0)
    print(f"Integral of {hist_name_1} is {signal_1.Integral(0, signal_1.GetNbinsX()+1)}")
    print(f" - Entries: {signal_1.GetEntries()} | Mean: {signal_1.GetMean():.4f} | Std Dev: {signal_1.GetStdDev():.4f}")
    root_file_1.Close()

    # Signal 2
    sig_info = Signals["GluGlutoRadiontoHHto2B2Tau_M-2000"]
    sig_file = sig_info["files"][0]
    hist_name_2 = f"{os.path.basename(sig_file.replace('.root', ''))}_{variable}"
    root_file_2 = ROOT.TFile.Open(os.path.join(redirector_MC, sig_file), 'READ')
    tree_2 = root_file_2.Get("Events")
    signal_2 = ROOT.TH1F(hist_name_2, hist_title, int(bin_values[0]), bin_values[1], bin_values[2])
    ROOT.gDirectory.Delete(f"{hist_name_2};*")
    signal_2.SetDirectory(ROOT.gDirectory)
    tree_2.Draw(f"{variable} >> {hist_name_2}", cut_sig)
    signal_2.SetDirectory(0)
    print(f"Integral of {hist_name_2} is {signal_2.Integral(0, signal_2.GetNbinsX()+1)}")
    print(f" - Entries: {signal_2.GetEntries()} | Mean: {signal_2.GetMean():.4f} | Std Dev: {signal_2.GetStdDev():.4f}")
    root_file_2.Close()

    # Signal 3
    sig_info = Signals["GluGlutoRadiontoHHto2B2Tau_M-3000"]
    sig_file = sig_info["files"][0]
    hist_name_3 = f"{os.path.basename(sig_file.replace('.root', ''))}_{variable}"
    root_file_3 = ROOT.TFile.Open(os.path.join(redirector_MC, sig_file), 'READ')
    tree_3 = root_file_3.Get("Events")
    signal_3 = ROOT.TH1F(hist_name_3, hist_title, int(bin_values[0]), bin_values[1], bin_values[2])
    ROOT.gDirectory.Delete(f"{hist_name_3};*")
    signal_3.SetDirectory(ROOT.gDirectory)
    tree_3.Draw(f"{variable} >> {hist_name_3}", cut_sig)
    signal_3.SetDirectory(0)
    print(f"Integral of {hist_name_3} is {signal_3.Integral(0, signal_3.GetNbinsX()+1)}")
    print(f" - Entries: {signal_3.GetEntries()} | Mean: {signal_3.GetMean():.4f} | Std Dev: {signal_3.GetStdDev():.4f}")
    root_file_3.Close()

    # Signal 4
    sig_info = Signals["GluGlutoRadiontoHHto2B2Tau_M-4000"]
    sig_file = sig_info["files"][0]
    hist_name_4 = f"{os.path.basename(sig_file.replace('.root', ''))}_{variable}"
    root_file_4 = ROOT.TFile.Open(os.path.join(redirector_MC, sig_file), 'READ')
    tree_4 = root_file_4.Get("Events")
    signal_4 = ROOT.TH1F(hist_name_4, hist_title, int(bin_values[0]), bin_values[1], bin_values[2])
    ROOT.gDirectory.Delete(f"{hist_name_4};*")
    signal_4.SetDirectory(ROOT.gDirectory)
    tree_4.Draw(f"{variable} >> {hist_name_4}", cut_sig)
    signal_4.SetDirectory(0)
    print(f"Integral of {hist_name_4} is {signal_4.Integral(0, signal_4.GetNbinsX()+1)}")
    print(f" - Entries: {signal_4.GetEntries()} | Mean: {signal_4.GetMean():.4f} | Std Dev: {signal_4.GetStdDev():.4f}")
    root_file_4.Close()

    ## Signals Only Plotting

    if args.signals_only:
        canvas_sig = ROOT.TCanvas("canvas_sig", "Signal Only", 1600, 900)
        canvas_sig.SetRightMargin(0.28)
        canvas_sig.SetLeftMargin(0.1)
        canvas_sig.SetBottomMargin(0.1)

        frame = ROOT.TH1F("frame", "", int(bin_values[0]), bin_values[1], bin_values[2])
        frame.SetDirectory(0)
        frame.SetStats(0)
        frame.GetXaxis().SetTitle(hist_title)
        frame.GetYaxis().SetTitle("Events")
        
        frame.GetXaxis().SetTitleSize(0.05)      
        frame.GetYaxis().SetTitleSize(0.05)

        frame.GetYaxis().SetLabelSize(0.04)
        frame.GetXaxis().SetLabelSize(0.04)

        frame.GetXaxis().SetTitleOffset(1)     
        frame.GetYaxis().SetTitleOffset(0.8)

        if log_scale:
            canvas_sig.SetLogy()
            frame.SetMinimum(1e-1)

        frame.SetMaximum(1.2*max(signal_1.GetMaximum(), signal_2.GetMaximum(), signal_3.GetMaximum(), signal_4.GetMaximum(), 1.0))
        frame.Draw("hist")

        signal_1.SetLineColor(ROOT.kRed)
        signal_1.SetLineWidth(2)
        signal_2.SetLineColor(ROOT.kBlue+2)
        signal_2.SetLineWidth(2)
        signal_3.SetLineColor(ROOT.kViolet+3)
        signal_3.SetLineWidth(2)
        signal_4.SetLineColor(ROOT.kCyan+4)
        signal_4.SetLineWidth(2)
        
        signal_1.Draw("hist SAME")
        signal_2.Draw("hist SAME")
        signal_3.Draw("hist SAME")
        signal_4.Draw("hist SAME")

        theLegend = ROOT.TLegend(0.73, 0.20, 0.96, 0.90, "", "brNDC")
        if (args.Channel == "tt"):
            theLegend.SetHeader("#tau-#tau Channel","C")
        elif (args.Channel == "et"):
            theLegend.SetHeader("e-#tau Channel","C")
        elif (args.Channel == "mt"):
            theLegend.SetHeader("#mu-#tau Channel","C")
        elif (args.Channel == "lt"):
            theLegend.SetHeader("l-#tau Channel","C")
        elif (args.Channel == "all"):
            theLegend.SetHeader("all Channels","C")
        else:
            print ("Enter a valid channel")


        theLegend.SetNColumns(1)
        theLegend.SetLineWidth(0)
        theLegend.SetLineStyle(1)
        theLegend.SetFillStyle(1001)
        theLegend.SetFillColor(0)
        theLegend.SetMargin(0.15)
        theLegend.SetTextSize(0.035)  
        theLegend.SetBorderSize(0)
        theLegend.SetTextFont(42)

        theLegend.AddEntry(signal_1, '1TeV (1pb x 0.073 (bbtt BR))', "f")
        theLegend.AddEntry(signal_2, '2TeV (1pb x 0.073 (bbtt BR))', "f")
        theLegend.AddEntry(signal_3, '3TeV (1pb x 0.073 (bbtt BR))', "f")
        theLegend.AddEntry(signal_4, '4TeV (1pb x 0.073 (bbtt BR))', "f")
        theLegend.Draw()

        cmsLatex = ROOT.TLatex()
        cmsLatex.SetNDC(True)
        cmsLatex.SetTextFont(61)
        cmsLatex.SetTextSize(0.05)
        cmsLatex.DrawLatex(0.10, 0.91, "CMS")
        cmsLatex.SetTextFont(52)
        cmsLatex.SetTextSize(0.04)
        cmsLatex.DrawLatex(0.16, 0.91, "Preliminary")

        canvas_sig.SaveAs(os.path.join("Signal_only", f"{args.year}_{args.Channel}_{variable}_signals_only.png"))

    elif args.dataMC:

        canvas_dataMC = ROOT.TCanvas("canvas_dataMC", "Data + MC", 1600, 1000)  
        canvas_dataMC.Divide(1, 2)  

        pad1 = canvas_dataMC.cd(1)
        pad1.SetPad(0.0, 0.3, 1.0, 1.0)
        pad1.SetBottomMargin(0.01)
        pad1.SetRightMargin(0.28)
        pad1.SetLeftMargin(0.1)
        
        theLegend = ROOT.TLegend(0.73, 0, 0.97, 0.9, "", "brNDC")
        if (args.Channel == "tt"):
            theLegend.SetHeader("#tau-#tau Channel","C")
        elif (args.Channel == "et"):
            theLegend.SetHeader("e-#tau Channel","C")
        elif (args.Channel == "mt"):
            theLegend.SetHeader("#mu-#tau Channel","C")
        elif (args.Channel == "lt"):
            theLegend.SetHeader("l-#tau Channel","C")
        elif (args.Channel == "all"):
            theLegend.SetHeader("all Channels","C")

        theLegend.SetNColumns(1)
        theLegend.SetLineWidth(0)
        theLegend.SetLineStyle(1)
        theLegend.SetFillStyle(1001)
        theLegend.SetFillColor(0)
        theLegend.SetMargin(0.15)
        theLegend.SetTextSize(0.037)  
        theLegend.SetBorderSize(0)
        theLegend.SetTextFont(42)

        # Total background
        total_bkg_hist = hists["DiBoson"].Clone("total_bkg")
        total_bkg_hist.Add(hists["STop"])
        total_bkg_hist.Add(hists["TTbar"])
        total_bkg_hist.Add(hists["QCD"])
        total_bkg_hist.Add(hists["WJets"])
        total_bkg_hist.Add(hists["Drell-Yan"])
        
        # Error band
        bkg_errors = ROOT.TGraphAsymmErrors(total_bkg_hist)
        for b in range(1, total_bkg_hist.GetNbinsX() + 1):
            bin_content = total_bkg_hist.GetBinContent(b)
            bin_error = total_bkg_hist.GetBinError(b)
            bkg_errors.SetPoint(b - 1, total_bkg_hist.GetBinCenter(b), bin_content)
            bkg_errors.SetPointError(b - 1,
                                    total_bkg_hist.GetBinWidth(b)/2,
                                    total_bkg_hist.GetBinWidth(b)/2,
                                    bin_error, bin_error)
        bkg_errors.SetFillStyle(3008)
        bkg_errors.SetFillColor(ROOT.TColor.GetColor("#545252"))

        val, err = get_integral_with_error(total_bkg_hist)
        print(f"Total background integral = {format_scientific(val, err)}")

        # Signals
        signal_1.SetLineColor(ROOT.kRed)
        signal_1.SetLineWidth(2)
        signal_2.SetLineColor(ROOT.kBlue+2)
        signal_2.SetLineWidth(2)
        signal_3.SetLineColor(ROOT.kViolet+3)
        signal_3.SetLineWidth(2)
        signal_4.SetLineColor(ROOT.kCyan+4)
        signal_4.SetLineWidth(2)


        # Data
        import re

        def _sanitize(name: str) -> str:
            return re.sub(r'[^A-Za-z0-9_]', '_', name)

        cut_data = create_cut_string("", base_cut, additional_cuts_o, is_observed=True)
        print(f"cut-data string is {cut_data}")

        data = ROOT.TH1F("Observed_Data", "", int(bin_values[0]), bin_values[1], bin_values[2])
        data.Sumw2()
        data.SetDirectory(0)

        prev_adddir = ROOT.TH1.AddDirectoryStatus()   
        data_hists = []

        for category, sample_type in observed.items():
            for path in sample_type["files"]:
                f = ROOT.TFile.Open(path, "READ")
                if not f or f.IsZombie():
                    print(f"Could not open {path}")
                    continue
                tree = f.Get("Events")
                if not tree:
                    print(f"No Events tree in {path}")
                    f.Close()
                    continue

                raw_name  = f"{os.path.basename(path).replace('.root','')}_{variable}"
                safe_name = _sanitize(raw_name)

                ROOT.TH1.AddDirectory(True)
                ROOT.gROOT.cd()
                ROOT.gDirectory.Delete(f"{safe_name};*")

                expr = f"{variable} >> {safe_name}({int(bin_values[0])},{bin_values[1]},{bin_values[2]})"
                nsel = tree.Draw(expr, cut_data, "goff")

                htemp = ROOT.gDirectory.Get(safe_name)
                ROOT.TH1.AddDirectory(prev_adddir)

                if nsel < 0:
                    print(f"Draw failed for {path}. expr={expr}")
                    f.Close()
                    continue
                if not htemp:
                    print(f"Histogram {safe_name} not created for {path} (likely 0 selected). Making empty.")
                    htemp = ROOT.TH1F(safe_name, hist_title, int(bin_values[0]), bin_values[1], bin_values[2])
                    htemp.Sumw2()

                htemp.SetDirectory(0)
                data_hists.append(htemp)
                data.Add(htemp)
                f.Close()

        
        data.SetMarkerStyle(20)
        data.SetLineColor(ROOT.kBlack)
        val, err = get_integral_with_error(data)
        print(f"Total Data integral = {format_scientific(val, err)}")
        
        max_bkg = max(h.GetMaximum() for _, h in hists.items())
        max_sig = max(signal_1.GetMaximum(), signal_2.GetMaximum(),
                            signal_3.GetMaximum(), signal_4.GetMaximum())
        max_data = data.GetMaximum() if data.GetMaximum() > 0 else 0

        pad1.cd()
        hist_stack.SetMaximum(max(max_bkg, max_sig, max_data) * 1.8)
        hist_stack.Draw("hist")
        hist_stack.GetXaxis().SetTitle("")
        hist_stack.GetXaxis().SetLabelSize(0)
        hist_stack.GetYaxis().SetTitle("Events")
        hist_stack.GetYaxis().SetTitleSize(0.05)
        hist_stack.GetYaxis().SetLabelSize(0.04)
        hist_stack.GetYaxis().SetTitleOffset(0.8)
        #pad1.Update()
        hist_stack.Draw("hist same")  

        if log_scale:
            pad1.SetLogy()
            hist_stack.SetMinimum(1e-1)

        pad1.Update()

        bkg_errors.Draw("E2 SAME")
        signal_1.Draw("hist SAME")
        signal_2.Draw("hist SAME")
        signal_3.Draw("hist SAME")
        signal_4.Draw("hist SAME")
        data.Draw("ep SAME")

        pad1.RedrawAxis()

        theLegend.AddEntry(hists["DiBoson"], "DiBoson", "f")
        theLegend.AddEntry(hists["STop"], "STop", "f")
        theLegend.AddEntry(hists["TTbar"], "TTbar", "f")
        theLegend.AddEntry(hists["QCD"], "QCD", "f")
        theLegend.AddEntry(hists["WJets"], "WJets", "f")
        theLegend.AddEntry(hists["Drell-Yan"], "Drell-Yan", "f")
        theLegend.AddEntry(signal_1, '1TeV (1pb x 0.073 (bbtt BR))', "f")
        theLegend.AddEntry(signal_2, '2TeV (1pb x 0.073 (bbtt BR))', "f")
        theLegend.AddEntry(signal_3, '3TeV (1pb x 0.073 (bbtt BR))', "f")
        theLegend.AddEntry(signal_4, '4TeV (1pb x 0.073 (bbtt BR))', "f")
        theLegend.AddEntry(data, "Observed", "lep")
        theLegend.Draw()

        # CMS label
        cmsLatex = ROOT.TLatex()
        cmsLatex.SetNDC(True)
        cmsLatex.SetTextFont(61)
        cmsLatex.SetTextSize(0.05)
        cmsLatex.DrawLatex(0.10, 0.91, "CMS")
        cmsLatex.SetTextFont(52)
        cmsLatex.SetTextSize(0.04)
        cmsLatex.DrawLatex(0.15, 0.91, "Preliminary")
        if args.year == '2024':
            cmsLatex.SetTextAlign(31)
            cmsLatex.SetTextFont(42)
            cmsLatex.DrawLatex(0.72,0.91,"109.08 fb^{-1}, 13.6 TeV (2024)")

        pad2 = canvas_dataMC.cd(2)
        pad2.SetPad(0.0, 0.0, 1.0, 0.3)
        pad1.SetLeftMargin(0.1)
        pad2.SetRightMargin(0.28)
        pad2.SetTopMargin(0.04)
        pad2.SetBottomMargin(0.35)
        pad2.SetGridy()

        ratio = data.Clone("Data_MC_Ratio")
        ratio.Divide(total_bkg_hist)
        ratio.SetStats(0)
        ratio.SetMarkerStyle(20)
        ratio.SetMarkerSize(0.9)

        ratio.GetXaxis().SetTitleSize(0.14)
        ratio.GetXaxis().SetLabelSize(0.10)
        ratio.GetXaxis().SetLabelOffset(0.04)
        ratio.GetXaxis().SetTitle(hist_title)
        ratio.GetYaxis().SetTitle("Data / MC")
        ratio.GetYaxis().SetTitleSize(0.12)
        ratio.GetYaxis().SetTitleOffset(0.3)
        ratio.GetYaxis().SetLabelSize(0.10)
        ratio.GetYaxis().SetNdivisions(505)
        ratio.GetYaxis().SetRangeUser(0, 2)
        ratio.Draw("ep")

        line = ROOT.TLine(bin_values[1], 1.0, bin_values[2], 1.0)
        line.SetLineColor(ROOT.kRed)
        line.SetLineStyle(2)
        line.SetLineWidth(2)
        line.Draw("same")

        canvas_dataMC.SaveAs(os.path.join("DataMC", f"{args.year}_{args.Channel}_{variable}_DataMC.png"))

        data_val, data_err = get_integral_with_error(data)
        mc_val, mc_err     = get_integral_with_error(total_bkg_hist)

        if mc_val > 0:
            ratio_val = data_val / mc_val
            ratio_err = ratio_val * math.sqrt(
                (data_err / data_val) ** 2 + (mc_err / mc_val) ** 2
            ) if data_val > 0 else 0.0
        else:
            ratio_val, ratio_err = float("nan"), 0.0
        print("\n")
        print(f"Data Integral : {format_scientific(data_val, data_err)}")
        print(f"MC Integral   : {format_scientific(mc_val, mc_err)}")
        print(f"Data/MC Ratio : {format_scientific(ratio_val, ratio_err)}")
    
    else:  
        ## Signal & Backgrounds both

        canvas_sb = ROOT.TCanvas("canvas_sb", "Signal + Backgrounds", 1600, 800)  
        canvas_sb.SetRightMargin(0.30)

        theLegend = ROOT.TLegend(0.80, 0.20, 0.98, 0.90, "", "brNDC")

        if (args.Channel == "tt"):
            theLegend.SetHeader("#tau-#tau Channel","C")
        elif (args.Channel == "et"):
            theLegend.SetHeader("e-#tau Channel","C")
        elif (args.Channel == "mt"):
            theLegend.SetHeader("#mu-#tau Channel","C")
        elif (args.Channel == "lt"):
            theLegend.SetHeader("l-#tau Channel","C")
        elif (args.Channel == "all"):
            theLegend.SetHeader("all Channels","C")
        else:
            print ("Enter a valid channel")

        theLegend.SetTextSize(0.035)
        theLegend.SetBorderSize(0)
        theLegend.SetFillStyle(0)
        theLegend.SetTextFont(42)

        signal_1.SetLineColor(ROOT.kRed)
        signal_1.SetLineWidth(2)
        signal_2.SetLineColor(ROOT.kBlue+2)
        signal_2.SetLineWidth(2)
        signal_3.SetLineColor(ROOT.kViolet+3)
        signal_3.SetLineWidth(2)
        signal_4.SetLineColor(ROOT.kCyan+4)
        signal_4.SetLineWidth(2)
        
        total_bkg_hist = hists["DiBoson"].Clone("total_bkg")
        total_bkg_hist.Add(hists["STop"])
        total_bkg_hist.Add(hists["TTbar"])
        total_bkg_hist.Add(hists["QCD"])
        total_bkg_hist.Add(hists["WJets"])
        total_bkg_hist.Add(hists["Drell-Yan"])
        bkg_errors = ROOT.TGraphAsymmErrors(total_bkg_hist)
        for b in range(1, total_bkg_hist.GetNbinsX() + 1):
            bin_content = total_bkg_hist.GetBinContent(b)
            bin_error = total_bkg_hist.GetBinError(b)
            bkg_errors.SetPoint(b - 1, total_bkg_hist.GetBinCenter(b), bin_content)
            bkg_errors.SetPointError(b - 1, total_bkg_hist.GetBinWidth(b)/2,
                                    total_bkg_hist.GetBinWidth(b)/2,
                                    bin_error, bin_error)
        bkg_errors.SetLineColor(0)
        bkg_errors.SetFillStyle(3008)
        bkg_errors.SetFillColor(ROOT.TColor.GetColor("#545252"))
        bkg_errors.SetMarkerStyle(0)
        bkg_errors.SetLineWidth(0)
        
        pad1.cd()
        hist_stack.GetHistogram().SetMaximum(1.2 * max(max_bkg, max_sig))
        hist_stack.Draw("hist")
        pad1.Update()
        hist_stack.Draw("hist same")
        if log_scale:
            pad1.SetLogy()
            hist_stack.SetMinimum(1e-1)
        pad1.Update()

        signal_1.Draw("hist SAME")
        signal_2.Draw("hist SAME")
        signal_3.Draw("hist SAME")
        signal_4.Draw("hist SAME")
        bkg_errors.Draw("E2 SAME")

        theLegend.AddEntry(hists["DiBoson"], "DiBoson", "f")
        theLegend.AddEntry(hists["STop"], "STop", "f")
        theLegend.AddEntry(hists["TTbar"], "TTbar", "f")
        theLegend.AddEntry(hists["QCD"], "QCD", "f")
        theLegend.AddEntry(hists["WJets"], "WJets", "f")
        theLegend.AddEntry(hists["Drell-Yan"], "Drell-Yan", "f")

        theLegend.AddEntry(signal_1, '1TeV (1pb x 0.073 (bbtt BR))', "f")
        theLegend.AddEntry(signal_2, '2TeV (1pb x 0.073 (bbtt BR))', "f")
        theLegend.AddEntry(signal_3, '3TeV (1pb x 0.073 (bbtt BR))', "f")
        theLegend.AddEntry(signal_4, '4TeV (1pb x 0.073 (bbtt BR))', "f")


        cmsLatex = ROOT.TLatex()
        cmsLatex.SetNDC(True)
        cmsLatex.SetTextFont(61)
        cmsLatex.SetTextSize(0.05)
        cmsLatex.DrawLatex(0.10, 0.92, "CMS")
        cmsLatex.SetTextFont(52)
        cmsLatex.SetTextSize(0.04)
        cmsLatex.DrawLatex(0.18, 0.92, "Preliminary")

        cmsLatex.SetTextAlign(31)
        cmsLatex.SetTextFont(42)
        if args.year == '2024':
            lumiText = '109.08 fb^{-1}, 13.6 TeV (2024)'
        cmsLatex.DrawLatex(0.700,0.91,lumiText)

        theLegend.SetNColumns(1)
        theLegend.SetLineWidth(0)
        theLegend.SetLineStyle(1)
        theLegend.SetFillStyle(1001)
        theLegend.SetFillColor(0)
        theLegend.SetMargin(0.2)
        theLegend.SetTextSize(0.035)  
        theLegend.SetBorderSize(0)
        theLegend.SetTextFont(42)
        theLegend.Draw()
    
        canvas_sb.SaveAs(os.path.join("SignalandBackground", f"{args.year}_{args.Channel}_{variable}_SignalandBackground.png"))

    end = time.time()
    print(f"Execution time: {end - start:.2f} seconds")
