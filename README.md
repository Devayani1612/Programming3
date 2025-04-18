Pantheon Congestion Control Analysis

Introduction

Welcome to the Pantheon Congestion Control Analysis toolkit! This repository is packed with scripts and utilities built to assess and benchmark various congestion control algorithms using the Pantheon framework alongside the MahiMahi network emulator. The aim here is to observe and compare how algorithms like TCP Cubic, Vegas, and Fillp_sheep perform when exposed to diverse network conditions.

Pantheon serves as a unified testing platform that brings together multiple congestion control methods. This project taps into its standardized environment to ensure fair and reliable performance comparisons across different setups.



Prerequisites

Before you get started, make sure you’ve got the following:

1. Ubuntu 20.04 or higher

2. Python 3 or above

3. Git

4. MahiMahi network emulator



Installation

1. Clone the Repository
	git clone https://github.com/Devayani1612/Programming3.git

2. Move into the Project Folder
	cd pantheon/

3. Install Dependencies
	Install all required packages and tools to work with Pantheon and Mahimahi environments.

4. Run the Full Set of Experiments
	sudo sysctl -w net.ipv4.ip_forward=1
	python3 final_analysis.py

5. Generated Output
	After execution, you’ll find the following artifacts:

	logs: pantheon/logs/ — Contains raw logs from each test iteration

	graphs: pantheon/graphs/ — Visual plots showcasing throughput, latency, and packet loss

	CSV Results:

		pantheon/results/profile_1/ — Data from experiments under Profile 1

		pantheon/results/profile_2/ — Data from experiments under Profile 2