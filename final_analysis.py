import os
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import shutil
import glob

# Define congestion control algorithms
CC_ALGOS = ["cubic", "fillp_sheep", "vegas"]

# Define color scheme for each algorithm
COLOR_MAP = {
    "cubic": "#7f7f7f",  # Grey
    "fillp_sheep": "#9467bd",  # purple
    "vegas": "#ff7f0e"  # Orange
}

# Define line styles for different profiles
LINE_STYLES = {
    "1": "-",  # Solid line for profile 1
    "2": "--"  # Dashed line for profile 2
}

NET_PROFILES = {
    "1": {
        "name": "LTE (Low Latency)",
        "latency": 5,
        "dl_trace": "mahimahi/traces/TMobile-LTE-driving.down",
        "ul_trace": "mahimahi/traces/TMobile-LTE-driving.up"
    },
    "2": {
        "name": "LTE (High Latency)",
        "latency": 200,
        "dl_trace": "mahimahi/traces/TMobile-LTE-short.down",
        "ul_trace": "mahimahi/traces/TMobile-LTE-short.up"
    }
}

def execute_tests():
    """Execute network tests for all profiles and algorithms"""
    for prof_id, prof_config in NET_PROFILES.items():
        print(f"\n--- Running tests for Network Profile {prof_id}: {prof_config['name']} "
              f"(latency = {prof_config['latency']} ms) ---")
        
        for algo in CC_ALGOS:
            print(f"[INFO] Testing congestion control algorithm: {algo.upper()}")
            result_path = f"results/profile_{prof_id}/{algo}"
            os.makedirs(result_path, exist_ok=True)

            test_command = (
                f"mm-delay {prof_config['latency']} "
                f"mm-link {prof_config['dl_trace']} {prof_config['ul_trace']} -- "
                f"bash -c 'python3 tests/test_schemes.py --schemes \"{algo}\" > {result_path}/log.txt 2>&1'"
            )

            try:
                subprocess.run(test_command, shell=True, check=True)
                print(f"[SUCCESS] {algo.upper()} test completed for Profile {prof_id}")
            except subprocess.CalledProcessError as err:
                print(f"[ERROR] Test failed for {algo.upper()} (Profile {prof_id}): {err}")
                continue

            # Copy the latest metrics file
            metric_logs = sorted(glob.glob(f"logs/metrics_{algo}_*.csv"), 
                         key=os.path.getmtime, reverse=True)
            if metric_logs:
                newest_log = metric_logs[0]
                shutil.copy(newest_log, os.path.join(result_path, f"{algo}_cc_log.csv"))
                print(f"[INFO] Metrics file saved for {algo.upper()} (Profile {prof_id})")
            else:
                print(f"[WARNING] No metrics file found for {algo.upper()} (Profile {prof_id})")

def collect_dataframes():
    """Collect all test results into a single DataFrame with additional metadata"""
    frames = []
    for prof_id, prof_config in NET_PROFILES.items():
        for algo in CC_ALGOS:
            log_file = f'results/profile_{prof_id}/{algo}/{algo}_cc_log.csv'
            if os.path.isfile(log_file):
                try:
                    df = pd.read_csv(log_file)
                    df["scheme"] = algo
                    df["profile"] = prof_id
                    df["profile_name"] = prof_config["name"]
                    df["latency"] = prof_config["latency"]
                    df["timestamp"] = list(range(len(df)))
                    frames.append(df)
                except Exception as e:
                    print(f"[ERROR] Failed to process {log_file}: {str(e)}")
            else:
                print(f"[WARNING] Missing CSV file for {algo.upper()} (Profile {prof_id})")
    
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

def draw_throughput_plot(data):
    """Create throughput plots with improved styling"""
    for prof_id in data['profile'].unique():
        prof_name = data[data['profile'] == prof_id]['profile_name'].iloc[0]
        print(f"[INFO] Generating throughput plot for {prof_name}")
        
        plt.figure(figsize=(12, 6))
        
        for algo in data['scheme'].unique():
            subdata = data[(data['scheme'] == algo) & (data['profile'] == prof_id)]
            if len(subdata) > 0:
                plt.plot(subdata['timestamp'], subdata['throughput'], 
                         label=f"{algo.upper()}",
                         color=COLOR_MAP[algo],
                         linewidth=2,
                         linestyle=LINE_STYLES[prof_id])
        
        plt.title(f'Throughput Over Time - {prof_name}\n(Latency: {NET_PROFILES[prof_id]["latency"]}ms)', 
                 fontsize=14, pad=20)
        plt.xlabel('Time (s)', fontsize=12)
        plt.ylabel('Throughput (Mbps)', fontsize=12)
        plt.legend(fontsize=10, framealpha=1)
        plt.grid(True, linestyle=':', alpha=0.7)
        plt.tight_layout()
        plt.savefig(f'graphs/throughput_profile_{prof_id}.png', dpi=300, bbox_inches='tight')
        plt.close()

def draw_loss_plot(data):
    """Create loss rate plots with improved styling"""
    for prof_id in data['profile'].unique():
        prof_name = data[data['profile'] == prof_id]['profile_name'].iloc[0]
        print(f"[INFO] Generating loss rate plot for {prof_name}")
        
        plt.figure(figsize=(12, 6))
        
        for algo in data['scheme'].unique():
            subdata = data[(data['scheme'] == algo) & (data['profile'] == prof_id)]
            if 'loss_rate' in subdata.columns and len(subdata) > 0:
                plt.plot(subdata['timestamp'], subdata['loss_rate']*100,  # Convert to percentage
                         label=f"{algo.upper()}",
                         color=COLOR_MAP[algo],
                         linewidth=2,
                         linestyle=LINE_STYLES[prof_id])
        
        plt.title(f'Packet Loss Rate Over Time - {prof_name}\n(Latency: {NET_PROFILES[prof_id]["latency"]}ms)', 
                 fontsize=14, pad=20)
        plt.xlabel('Time (s)', fontsize=12)
        plt.ylabel('Loss Rate (%)', fontsize=12)
        plt.legend(fontsize=10, framealpha=1)
        plt.grid(True, linestyle=':', alpha=0.7)
        plt.tight_layout()
        plt.savefig(f'graphs/loss_profile_{prof_id}.png', dpi=300, bbox_inches='tight')
        plt.close()

def draw_throughput_cdf(data):
    """Create CDF plots of throughput distribution"""
    for prof_id in data['profile'].unique():
        prof_name = data[data['profile'] == prof_id]['profile_name'].iloc[0]
        print(f"[INFO] Generating throughput CDF plot for {prof_name}")
        
        plt.figure(figsize=(10, 6))
        
        for algo in data['scheme'].unique():
            subdata = data[(data['scheme'] == algo) & (data['profile'] == prof_id)]
            if len(subdata) > 0:
                sorted_data = np.sort(subdata['throughput'])
                cdf = np.arange(1, len(sorted_data)+1) / len(sorted_data)
                plt.plot(sorted_data, cdf,
                         label=f"{algo.upper()}",
                         color=COLOR_MAP[algo],
                         linewidth=2)
        
        plt.title(f'Throughput CDF - {prof_name}', fontsize=14)
        plt.xlabel('Throughput (Mbps)', fontsize=12)
        plt.ylabel('Cumulative Probability', fontsize=12)
        plt.legend(fontsize=10, framealpha=1)
        plt.grid(True, linestyle=':', alpha=0.7)
        plt.tight_layout()
        plt.savefig(f'graphs/throughput_cdf_profile_{prof_id}.png', dpi=300, bbox_inches='tight')
        plt.close()

def summarize_rtt(data):
    """Calculate and display comprehensive RTT statistics"""
    print("\n[INFO] Summarizing RTT statistics")
    rtt_records = []
    
    for prof_id in data['profile'].unique():
        prof_name = data[data['profile'] == prof_id]['profile_name'].iloc[0]
        for algo in data['scheme'].unique():
            subdata = data[(data['scheme'] == algo) & (data['profile'] == prof_id)]
            if not subdata.empty and 'rtt' in subdata.columns:
                rtt_stats = {
                    "Algorithm": algo.upper(),
                    "Profile": prof_name,
                    "Latency (ms)": NET_PROFILES[prof_id]["latency"],
                    "Avg RTT (ms)": subdata['rtt'].mean(),
                    "Min RTT (ms)": subdata['rtt'].min(),
                    "Max RTT (ms)": subdata['rtt'].max(),
                    "Median RTT (ms)": subdata['rtt'].median(),
                    "Std Dev (ms)": subdata['rtt'].std(),
                    "95th %ile (ms)": subdata['rtt'].quantile(0.95),
                    "Jitter (ms)": (subdata['rtt'].diff().abs().mean())
                }
                rtt_records.append(rtt_stats)
    
    if rtt_records:
        summary_df = pd.DataFrame(rtt_records)
        summary_df.to_csv("graphs/rtt_summary.csv", index=False)
        
        # Format for nice console output
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        pd.set_option('display.float_format', '{:.2f}'.format)
        print("\nRTT Statistics Summary:")
        print(summary_df.to_string(index=False))
    else:
        print("[WARNING] No RTT data available for summary")

def scatter_rtt_vs_throughput(data):
    """Create enhanced scatter plot of RTT vs Throughput"""
    print("[INFO] Creating enhanced RTT vs Throughput scatter plot")
    
    plt.figure(figsize=(12, 8))
    
    markers = ['o', 's', 'D']  # Different markers for different algorithms
    marker_sizes = [100, 150, 200]  # Different sizes for different profiles
    
    for prof_id in data['profile'].unique():
        for algo_idx, algo in enumerate(data['scheme'].unique()):
            subdata = data[(data['scheme'] == algo) & (data['profile'] == prof_id)]
            if not subdata.empty:
                rtt_avg = subdata['rtt'].mean()
                tp_avg = subdata['throughput'].mean()
                tp_std = subdata['throughput'].std()
                
                plt.scatter(rtt_avg, tp_avg,
                            label=f'{algo.upper()} (Profile {prof_id})',
                            color=COLOR_MAP[algo],
                            s=marker_sizes[int(prof_id)-1],
                            marker=markers[algo_idx % len(markers)],
                            edgecolors='black',
                            alpha=0.8)
                
                # Add error bars for throughput variability
                plt.errorbar(rtt_avg, tp_avg, yerr=tp_std,
                             fmt='none', ecolor=COLOR_MAP[algo], alpha=0.5)
    
    plt.title("Average Throughput vs Average RTT\n(with throughput variability)", fontsize=14)
    plt.xlabel("Average RTT (ms)", fontsize=12)
    plt.ylabel("Average Throughput ± Std Dev (Mbps)", fontsize=12)
    plt.grid(True, linestyle=':', alpha=0.5)
    plt.legend(fontsize=10, bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig("graphs/rtt_vs_throughput.png", dpi=300, bbox_inches='tight')
    plt.close()

def generate_comparison_table(data):
    """Generate a comparison table of key metrics"""
    print("\n[INFO] Generating algorithm comparison table")
    
    comparison_records = []
    
    for prof_id in data['profile'].unique():
        for algo in data['scheme'].unique():
            subdata = data[(data['scheme'] == algo) & (data['profile'] == prof_id)]
            if not subdata.empty:
                record = {
                    "Profile": NET_PROFILES[prof_id]["name"],
                    "Algorithm": algo.upper(),
                    "Avg Throughput (Mbps)": subdata['throughput'].mean(),
                    "Throughput Std Dev": subdata['throughput'].std(),
                    "Avg RTT (ms)": subdata['rtt'].mean(),
                    "Avg Loss Rate (%)": subdata['loss_rate'].mean()*100 if 'loss_rate' in subdata.columns else 0,
                    "90% Throughput (Mbps)": subdata['throughput'].quantile(0.9)
                }
                comparison_records.append(record)
    
    if comparison_records:
        comparison_df = pd.DataFrame(comparison_records)
        comparison_df.to_csv("graphs/algorithm_comparison.csv", index=False)
        
        # Format for nice console output
        pd.set_option('display.float_format', '{:.2f}'.format)
        print("\nAlgorithm Comparison:")
        print(comparison_df.to_string(index=False))
    else:
        print("[WARNING] No data available for comparison table")

def orchestrate():
    """Main function to coordinate the testing and analysis"""
    print("[SETUP] Creating required directories")
    os.makedirs("graphs", exist_ok=True)
    os.makedirs("results", exist_ok=True)
    
    execute_tests()

    print("\n[PROCESS] Collecting and processing test results")
    full_df = collect_dataframes()
    if full_df.empty:
        print("[ERROR] No data collected. Please check logs or metrics output.")
        return

    print("\n[ANALYSIS] Generating plots and summaries")
    draw_throughput_plot(full_df)
    draw_loss_plot(full_df)
    draw_throughput_cdf(full_df)  # New CDF plot
    summarize_rtt(full_df)
    scatter_rtt_vs_throughput(full_df)
    generate_comparison_table(full_df)  # New comparison table

    print("\n[COMPLETE] All tests finished and results saved in the 'graphs/' directory")

if __name__ == "__main__":
    try:
        orchestrate()
    except Exception as e:
        print(f"[CRITICAL ERROR] Script failed: {str(e)}")
        raise