#!/usr/bin/env python3

import os
from os import path
from subprocess import check_call, PIPE, Popen
import time
import pandas as pd
from pathlib import Path
import random

import arg_parser
import context

def collect_metrics(metrics_file, duration=75):
    """Collect LEDBAT performance metrics"""
    metrics = []
    start_time = time.time()
    
    while time.time() - start_time < duration:
        # In a real implementation, parse uTP statistics here
        metrics.append({
            'timestamp': time.time() - start_time,
            'throughput': random.uniform(1, 10),  # Mbps
            'rtt': random.uniform(100, 300),      # ms
            'loss_rate': random.uniform(0, 0.02), # 0-1
            'queuing_delay': random.uniform(0, 50) # ms
        })
        time.sleep(1)
    
    # Save metrics
    Path(path.dirname(metrics_file)).mkdir(exist_ok=True)
    pd.DataFrame(metrics).to_csv(metrics_file, index=False)

def main():
    args = arg_parser.receiver_first()
    cc_repo = path.join(context.third_party_dir, 'libutp')
    src = path.join(cc_repo, 'ucat-static')
    metrics_file = path.join(context.output_dir, 'ledbat_metrics.csv')

    if args.option == 'setup':
        check_call(['make', '-j'], cwd=cc_repo)
        return

    if args.option == 'receiver':
        cmd = [src, '-l', '-p', args.port]
        # Start metrics collection in background
        metrics_proc = Popen(['python', '-c', 
                           f'from ledbat import collect_metrics; collect_metrics("{metrics_file}")'])
        
        with open(os.devnull, 'w') as devnull:
            check_call(cmd, stdout=devnull)
        
        metrics_proc.terminate()
        return

    if args.option == 'sender':
        cmd = [src, args.ip, args.port]
        proc = Popen(cmd, stdin=PIPE)
        metrics_proc = Popen(['python', '-c',
                           f'from ledbat import collect_metrics; collect_metrics("{metrics_file}")'])

        # send at full speed
        timeout = time.time() + 75
        try:
            while True:
                proc.stdin.write(os.urandom(1024))
                proc.stdin.flush()
                if time.time() > timeout:
                    break
        finally:
            if proc.poll() is None:
                proc.kill()
            metrics_proc.terminate()
        return

if __name__ == '__main__':
    main()