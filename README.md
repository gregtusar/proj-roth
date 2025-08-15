# New Jersey Voter Data Analysis Framework

A comprehensive Python-based framework for analyzing New Jersey voter registration data from GCP storage.

## Overview

This repository contains a complete analytical framework for processing and analyzing New Jersey voter file data. The framework includes secure data extraction from Google Cloud Platform, comprehensive demographic and geographic analysis, and automated visualization generation.

## Features

- **Secure GCP Integration**: Safe credential handling for Google Cloud Storage access
- **Comprehensive Analysis**: Demographic, geographic, and voting pattern analysis
- **Automated Visualizations**: Party distribution, age demographics, geographic mapping
- **Data Quality Assessment**: Missing data analysis and completeness metrics
- **Real Data Processing**: Handles actual NJ voter file with 80+ data fields

## Files

### Core Analysis Scripts

- **`real_voter_analysis.py`** - Main analysis framework for real NJ voter data (622K+ records)
- **`gcp_data_downloader.py`** - Secure GCP data download utility with credential management

## Requirements

```bash
pip install pandas numpy matplotlib seaborn plotly google-cloud-storage
```

## Usage

### 1. Download Real Data

```python
from gcp_data_downloader import GCPVoterDataDownloader

# Initialize downloader
downloader = GCPVoterDataDownloader()

# Set up credentials (provide your service account JSON)
downloader.setup_credentials_from_file('/path/to/credentials.json')

# Download voter data
downloader.download_voter_data('export-20250729.csv', './voter_data.csv')
```

### 2. Run Comprehensive Analysis

```bash
python real_voter_analysis.py
```

## GCP Setup

The framework expects:
- **Project**: `proj-roth`
- **Bucket**: `nj7voterfile`
- **File**: `export-20250729.csv`
- **Service Account**: With `storage.objects.list` and `storage.objects.get` permissions

## Real Data Structure

The actual NJ voter file contains 80 columns including:
- **Demographics**: age, gender, race, party affiliation
- **Geographic**: county, city, congressional/state districts
- **Contact**: addresses, phone, email (where available)
- **Voting History**: Participation in primaries/generals 2016-2024
- **Registration**: Status and voter type information

## Analysis Results

The framework analyzes 622,304+ registered voters and provides insights into:

### Demographics
- **Party Distribution**: Republican (34.5%), Unaffiliated (33.0%), Democrat (31.4%)
- **Age**: Average 50.0 years, ranging from 17-120
- **Gender**: Female (46.4%), Male (44.0%), Unknown (9.6%)
- **Race**: White (69.0%), Latino/a (13.1%), Asian (12.3%), Black (2.8%)

### Geography
- **Counties**: Union (157K), Somerset (126K), Hunterdon (106K) lead voter counts
- **Congressional**: All voters in NJ District 07
- **State Districts**: 7 house districts represented

### Data Quality
- **Completeness**: 75.0% overall data completeness
- **Missing Data**: Primarily in optional fields (email, phone, municipal data)
- **Core Fields**: Demographics and voting history well-populated

## Generated Visualizations

- **`voter_demographics_overview.png`** - Age, gender, party, and county distributions
- **`voting_participation_trends.png`** - Participation rates over time (2016-2024)
- **`county_distribution.png`** - Geographic voter distribution

## Security

- Credentials are handled securely with temporary files
- No hardcoded secrets in the codebase
- Service account authentication recommended

---

*Real voter data analysis framework for New Jersey Congressional District 07*
