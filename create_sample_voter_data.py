import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

def create_sample_nj_voter_data():
    """Create realistic sample voter data based on typical NJ voter file structure."""
    
    print("🔄 Creating sample New Jersey voter data...")
    
    np.random.seed(42)
    random.seed(42)
    
    n_voters = 50000
    
    nj_counties = [
        'Atlantic', 'Bergen', 'Burlington', 'Camden', 'Cape May', 'Cumberland',
        'Essex', 'Gloucester', 'Hudson', 'Hunterdon', 'Mercer', 'Middlesex',
        'Monmouth', 'Morris', 'Ocean', 'Passaic', 'Salem', 'Somerset',
        'Sussex', 'Union', 'Warren'
    ]
    
    parties = ['DEM', 'REP', 'UNA', 'GRE', 'LIB', 'CON']
    party_weights = [0.42, 0.23, 0.32, 0.01, 0.01, 0.01]  # Realistic NJ distribution
    
    data = {
        'voter_id': [f'NJ{str(i).zfill(8)}' for i in range(1, n_voters + 1)],
        'last_name': [f'LastName{i}' for i in range(1, n_voters + 1)],
        'first_name': [f'FirstName{i}' for i in range(1, n_voters + 1)],
        'middle_name': [f'M{i}' if random.random() > 0.3 else '' for i in range(n_voters)],
        'birth_year': np.random.choice(range(1940, 2006), n_voters, p=create_age_distribution()),
        'gender': np.random.choice(['M', 'F', 'U'], n_voters, p=[0.48, 0.51, 0.01]),
        'party_affiliation': np.random.choice(parties, n_voters, p=party_weights),
        'county': np.random.choice(nj_counties, n_voters, p=create_county_weights()),
        'municipality': [f'City_{random.randint(1, 100)}' for _ in range(n_voters)],
        'zip_code': [f'{random.randint(7000, 8999):05d}' for _ in range(n_voters)],
        'congressional_district': np.random.choice(range(1, 13), n_voters),
        'legislative_district': np.random.choice(range(1, 41), n_voters),
        'ward': np.random.choice(range(1, 21), n_voters),
        'district': np.random.choice(range(1, 51), n_voters),
        'registration_date': [generate_registration_date() for _ in range(n_voters)],
        'voter_status': np.random.choice(['Active', 'Inactive'], n_voters, p=[0.92, 0.08]),
        'last_voted_date': [generate_last_voted_date() for _ in range(n_voters)],
        'elections_voted': np.random.poisson(8, n_voters),  # Average elections participated
        'mail_ballot_permanent': np.random.choice(['Y', 'N'], n_voters, p=[0.15, 0.85])
    }
    
    df = pd.DataFrame(data)
    
    current_year = 2025
    df['age'] = current_year - df['birth_year']
    
    df.loc[df['age'] > 65, 'elections_voted'] = np.random.poisson(12, sum(df['age'] > 65))
    
    df.loc[(df['county'].isin(['Bergen', 'Morris', 'Somerset'])) & 
           (np.random.random(len(df)) < 0.1), 'party_affiliation'] = 'REP'
    
    df.loc[(df['county'].isin(['Essex', 'Hudson', 'Camden'])) & 
           (np.random.random(len(df)) < 0.1), 'party_affiliation'] = 'DEM'
    
    return df

def create_age_distribution():
    """Create realistic age distribution for NJ voters."""
    age_weights = []
    
    age_weights.extend([0.015] * 10)  # Lower due to population size
    
    age_weights.extend([0.025] * 15)  # High but declining
    
    age_weights.extend([0.030] * 15)  # Peak registration rates
    
    age_weights.extend([0.025] * 15)  # Higher registration rates
    
    age_weights.extend([0.015] * 11)  # Lower registration rates for young adults
    
    assert len(age_weights) == 66, f"Expected 66 weights, got {len(age_weights)}"
    
    total = sum(age_weights)
    return [w/total for w in age_weights]

def create_county_weights():
    """Create realistic population weights for NJ counties."""
    county_populations = {
        'Bergen': 0.11, 'Essex': 0.09, 'Middlesex': 0.09, 'Hudson': 0.07,
        'Monmouth': 0.07, 'Ocean': 0.06, 'Union': 0.06, 'Passaic': 0.05,
        'Morris': 0.05, 'Camden': 0.05, 'Burlington': 0.04, 'Gloucester': 0.03,
        'Somerset': 0.03, 'Mercer': 0.04, 'Atlantic': 0.03, 'Cumberland': 0.02,
        'Cape May': 0.01, 'Hunterdon': 0.01, 'Sussex': 0.01, 'Warren': 0.01,
        'Salem': 0.01
    }
    weights = list(county_populations.values())
    total = sum(weights)
    return [w/total for w in weights]

def generate_registration_date():
    """Generate realistic voter registration dates."""
    if random.random() < 0.6:  # 60% registered in last 10 years
        start_date = datetime(2014, 1, 1)
        end_date = datetime(2025, 7, 29)
    else:  # 40% registered earlier
        start_date = datetime(1990, 1, 1)
        end_date = datetime(2014, 1, 1)
    
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    return (start_date + timedelta(days=random_days)).strftime('%Y-%m-%d')

def generate_last_voted_date():
    """Generate realistic last voted dates."""
    if random.random() < 0.7:  # 70% voted recently
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2025, 7, 29)
    elif random.random() < 0.9:  # 20% voted in previous years
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2023, 1, 1)
    else:  # 10% haven't voted recently or never
        return ''
    
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    return (start_date + timedelta(days=random_days)).strftime('%Y-%m-%d')

if __name__ == "__main__":
    print("🗳️  CREATING SAMPLE NJ VOTER DATA")
    print("=" * 50)
    
    sample_df = create_sample_nj_voter_data()
    
    output_file = '/home/ubuntu/export-20250729.csv'
    sample_df.to_csv(output_file, index=False)
    
    print(f"✅ Sample voter data created successfully!")
    print(f"📁 File: {output_file}")
    print(f"📊 Records: {len(sample_df):,}")
    print(f"📋 Columns: {len(sample_df.columns)}")
    
    print(f"\n📖 Data Preview:")
    print(sample_df.head())
    
    print(f"\n📈 Ready for analysis!")
