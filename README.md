# New Jersey Voter Data Analysis Framework

A comprehensive Python-based framework for analyzing New Jersey voter registration data from GCP storage.

## Overview

This repository contains a complete analytical framework for processing and analyzing New Jersey voter file data. The framework includes data extraction from Google Cloud Platform, comprehensive demographic and geographic analysis, and automated visualization generation.

## Features

- **GCP Integration**: Secure data download from Google Cloud Storage buckets
- **Comprehensive Analysis**: Demographic, geographic, and voting pattern analysis
- **Automated Visualizations**: Party distribution, age demographics, geographic mapping
- **Sample Data Generation**: Create realistic test datasets for development
- **Data Quality Assessment**: Missing data analysis and completeness metrics

## Files

### Core Analysis Scripts

- **`voter_data_analysis.py`** - Main analysis framework with comprehensive voter data processing
- **`setup_gcp_and_download.py`** - Production-ready GCP data download with credential management
- **`download_voter_data.py`** - Simple utility for downloading voter data from GCP bucket
- **`test_gcp_access.py`** - GCP access testing and bucket verification
- **`create_sample_voter_data.py`** - Generate realistic sample NJ voter data for testing

## Requirements

```bash
pip install pandas numpy matplotlib seaborn plotly google-cloud-storage jupyter
```

## Usage

### 1. Download Real Data (requires GCP permissions)

```bash
python setup_gcp_and_download.py
```

### 2. Generate Sample Data (for testing)

```bash
python create_sample_voter_data.py
```

### 3. Run Analysis

```bash
python voter_data_analysis.py
```

## GCP Setup

The framework expects:
- Project: `proj-roth`
- Bucket: `nj7voterfile`
- File: `export-20250729.csv`
- Service account with `storage.objects.list` permissions

## Output

The analysis generates:
- Comprehensive demographic breakdowns
- Party affiliation analysis (DEM/REP/UNA distribution)
- Geographic analysis by county and district
- Age distribution and voting history patterns
- Multiple visualization files (PNG format)

## Data Structure

Expected voter file columns:
- Voter identification (voter_id, names)
- Demographics (birth_year, gender, age)
- Political affiliation (party_affiliation)
- Geographic data (county, municipality, zip_code, districts)
- Voting history (registration_date, last_voted_date, elections_voted)
- Status information (voter_status, mail_ballot_permanent)

## Analysis Results

The framework provides insights into:
- **Party Distribution**: Democratic, Republican, and Unaffiliated voter percentages
- **Demographics**: Age ranges, gender distribution, registration patterns
- **Geography**: County-level voter distribution across all 21 NJ counties
- **Engagement**: Voting frequency and participation patterns

## Visualizations

Generated charts include:
- Dataset overview with data quality metrics
- Party affiliation bar and pie charts
- Geographic distribution by county
- Age demographics with histograms and box plots

---

*Framework developed for comprehensive New Jersey voter file analysis*
