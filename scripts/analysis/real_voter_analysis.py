import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

class RealVoterDataAnalyzer:
    """Comprehensive analysis framework for real New Jersey voter data."""
    
    def __init__(self, csv_file_path):
        """Initialize the analyzer with the voter data file."""
        self.csv_file_path = csv_file_path
        self.df = None
        self.analysis_results = {}
        
    def load_data(self):
        """Load the voter data from CSV file."""
        print(f"Loading voter data from {self.csv_file_path}...")
        try:
            self.df = pd.read_csv(self.csv_file_path)
            print(f"Data loaded successfully! Shape: {self.df.shape}")
            return True
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    def explore_data_structure(self):
        """Explore the structure and content of the voter data."""
        if self.df is None:
            print("No data loaded. Please run load_data() first.")
            return
        
        print("\n" + "="*50)
        print("VOTER DATA EXPLORATION")
        print("="*50)
        
        print(f"\nDataset Shape: {self.df.shape}")
        print(f"Columns: {self.df.shape[1]}")
        print(f"Rows: {self.df.shape[0]}")
        
        print(f"\nColumn Names and Types:")
        print("-" * 30)
        for col in self.df.columns:
            dtype = str(self.df[col].dtype)
            null_count = self.df[col].isnull().sum()
            null_pct = (null_count / len(self.df)) * 100
            print(f"{col:<30} | {dtype:<15} | Nulls: {null_count:6} ({null_pct:5.1f}%)")
        
        print(f"\nFirst 5 rows:")
        print("-" * 30)
        print(self.df.head())
        
        print(f"\nBasic Statistics:")
        print("-" * 30)
        print(self.df.describe(include='all'))
        
        self.analysis_results['data_structure'] = {
            'shape': self.df.shape,
            'columns': list(self.df.columns),
            'dtypes': dict(self.df.dtypes),
            'null_counts': dict(self.df.isnull().sum())
        }
    
    def analyze_demographics(self):
        """Analyze demographic patterns in the voter data."""
        if self.df is None:
            return
        
        print("\n" + "="*50)
        print("DEMOGRAPHIC ANALYSIS")
        print("="*50)
        
        if 'demo_age' in self.df.columns:
            print(f"\nAge Distribution:")
            age_stats = self.df['demo_age'].describe()
            print(age_stats)
            
            self.df['age_group'] = pd.cut(self.df['demo_age'], 
                                        bins=[0, 25, 35, 50, 65, 100], 
                                        labels=['18-25', '26-35', '36-50', '51-65', '65+'])
            age_group_dist = self.df['age_group'].value_counts()
            print(f"\nAge Group Distribution:")
            print(age_group_dist)
        
        if 'demo_gender' in self.df.columns:
            print(f"\nGender Distribution:")
            gender_dist = self.df['demo_gender'].value_counts()
            print(gender_dist)
        
        if 'demo_race' in self.df.columns:
            print(f"\nRace Distribution:")
            race_dist = self.df['demo_race'].value_counts()
            print(race_dist)
        
        if 'demo_party' in self.df.columns:
            print(f"\nParty Affiliation Distribution:")
            party_dist = self.df['demo_party'].value_counts()
            print(party_dist)
        
        self.analysis_results['demographics'] = {
            'age_stats': age_stats.to_dict() if 'demo_age' in self.df.columns else None,
            'gender_dist': gender_dist.to_dict() if 'demo_gender' in self.df.columns else None,
            'race_dist': race_dist.to_dict() if 'demo_race' in self.df.columns else None,
            'party_dist': party_dist.to_dict() if 'demo_party' in self.df.columns else None
        }
    
    def analyze_geographic_patterns(self):
        """Analyze geographic distribution of voters."""
        if self.df is None:
            return
        
        print("\n" + "="*50)
        print("GEOGRAPHIC ANALYSIS")
        print("="*50)
        
        if 'county_name' in self.df.columns:
            print(f"\nCounty Distribution:")
            county_dist = self.df['county_name'].value_counts()
            print(f"Top 10 counties by voter count:")
            print(county_dist.head(10))
        
        if 'addr_residential_city' in self.df.columns:
            print(f"\nCity Distribution:")
            city_dist = self.df['addr_residential_city'].value_counts()
            print(f"Top 10 cities by voter count:")
            print(city_dist.head(10))
        
        if 'congressional_name' in self.df.columns:
            print(f"\nCongressional District Distribution:")
            congress_dist = self.df['congressional_name'].value_counts()
            print(congress_dist)
        
        if 'state_house_name' in self.df.columns:
            print(f"\nState House District Distribution:")
            house_dist = self.df['state_house_name'].value_counts()
            print(f"Number of unique districts: {len(house_dist)}")
            print(house_dist.head(10))
        
        self.analysis_results['geography'] = {
            'county_dist': county_dist.to_dict() if 'county_name' in self.df.columns else None,
            'city_dist': city_dist.head(20).to_dict() if 'addr_residential_city' in self.df.columns else None,
            'congress_dist': congress_dist.to_dict() if 'congressional_name' in self.df.columns else None
        }
    
    def analyze_voting_patterns(self):
        """Analyze voting participation patterns."""
        if self.df is None:
            return
        
        print("\n" + "="*50)
        print("VOTING PATTERN ANALYSIS")
        print("="*50)
        
        participation_cols = [col for col in self.df.columns if 'participation_' in col]
        primary_cols = [col for col in participation_cols if 'primary' in col]
        general_cols = [col for col in participation_cols if 'general' in col]
        
        print(f"Found {len(participation_cols)} participation columns")
        print(f"Primary elections: {len(primary_cols)}")
        print(f"General elections: {len(general_cols)}")
        
        if participation_cols:
            participation_rates = {}
            for col in participation_cols:
                total_eligible = self.df[col].notna().sum()
                participated = (self.df[col] == 'Y').sum()
                if total_eligible > 0:
                    rate = (participated / total_eligible) * 100
                    participation_rates[col] = rate
                    print(f"{col}: {participated:,} / {total_eligible:,} ({rate:.1f}%)")
            
            self.df['total_elections_participated'] = 0
            for col in participation_cols:
                self.df['total_elections_participated'] += (self.df[col] == 'Y').astype(int)
            
            print(f"\nTotal Elections Participated Distribution:")
            participation_dist = self.df['total_elections_participated'].value_counts().sort_index()
            print(participation_dist)
        
        if 'registration_status_civitech' in self.df.columns:
            print(f"\nRegistration Status Distribution:")
            reg_status = self.df['registration_status_civitech'].value_counts()
            print(reg_status)
        
        self.analysis_results['voting_patterns'] = {
            'participation_rates': participation_rates if participation_cols else None,
            'registration_status': reg_status.to_dict() if 'registration_status_civitech' in self.df.columns else None
        }
    
    def create_visualizations(self):
        """Create comprehensive visualizations of the voter data."""
        if self.df is None:
            return
        
        print("\n" + "="*50)
        print("CREATING VISUALIZATIONS")
        print("="*50)
        
        plt.style.use('default')
        sns.set_palette("husl")
        
        if any(col in self.df.columns for col in ['demo_age', 'demo_gender', 'demo_party']):
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('New Jersey Voter Demographics Overview', fontsize=16, fontweight='bold')
            
            if 'demo_age' in self.df.columns:
                self.df['demo_age'].hist(bins=30, ax=axes[0,0], alpha=0.7, color='skyblue')
                axes[0,0].set_title('Age Distribution')
                axes[0,0].set_xlabel('Age')
                axes[0,0].set_ylabel('Count')
            
            if 'demo_gender' in self.df.columns:
                gender_counts = self.df['demo_gender'].value_counts()
                axes[0,1].pie(gender_counts.values, labels=gender_counts.index, autopct='%1.1f%%')
                axes[0,1].set_title('Gender Distribution')
            
            if 'demo_party' in self.df.columns:
                party_counts = self.df['demo_party'].value_counts().head(10)
                party_counts.plot(kind='bar', ax=axes[1,0], color='lightcoral')
                axes[1,0].set_title('Party Affiliation (Top 10)')
                axes[1,0].tick_params(axis='x', rotation=45)
            
            if 'county_name' in self.df.columns:
                county_counts = self.df['county_name'].value_counts().head(10)
                county_counts.plot(kind='bar', ax=axes[1,1], color='lightgreen')
                axes[1,1].set_title('Top 10 Counties by Voter Count')
                axes[1,1].tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            plt.savefig('voter_demographics_overview.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("✓ Demographics overview saved as 'voter_demographics_overview.png'")
        
        participation_cols = [col for col in self.df.columns if 'participation_' in col]
        if participation_cols:
            years = []
            primary_rates = []
            general_rates = []
            
            for year in range(2016, 2025):
                primary_col = f'participation_primary_{year}'
                general_col = f'participation_general_{year}'
                
                if primary_col in self.df.columns:
                    total = self.df[primary_col].notna().sum()
                    participated = (self.df[primary_col] == 'Y').sum()
                    rate = (participated / total * 100) if total > 0 else 0
                    years.append(year)
                    primary_rates.append(rate)
                
                if general_col in self.df.columns:
                    total = self.df[general_col].notna().sum()
                    participated = (self.df[general_col] == 'Y').sum()
                    rate = (participated / total * 100) if total > 0 else 0
                    if year not in years:
                        years.append(year)
                    general_rates.append(rate)
            
            if years and (primary_rates or general_rates):
                plt.figure(figsize=(12, 6))
                if primary_rates:
                    plt.plot(years[:len(primary_rates)], primary_rates, marker='o', label='Primary Elections', linewidth=2)
                if general_rates:
                    plt.plot(years[:len(general_rates)], general_rates, marker='s', label='General Elections', linewidth=2)
                
                plt.title('Voter Participation Rates Over Time', fontsize=14, fontweight='bold')
                plt.xlabel('Year')
                plt.ylabel('Participation Rate (%)')
                plt.legend()
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                plt.savefig('voting_participation_trends.png', dpi=300, bbox_inches='tight')
                plt.close()
                print("✓ Voting participation trends saved as 'voting_participation_trends.png'")
        
        if 'county_name' in self.df.columns:
            plt.figure(figsize=(12, 8))
            county_counts = self.df['county_name'].value_counts()
            
            plt.barh(range(len(county_counts)), county_counts.values, color='steelblue')
            plt.yticks(range(len(county_counts)), county_counts.index)
            plt.xlabel('Number of Voters')
            plt.title('Voter Distribution by County', fontsize=14, fontweight='bold')
            plt.gca().invert_yaxis()
            
            for i, v in enumerate(county_counts.values):
                plt.text(v + max(county_counts.values) * 0.01, i, f'{v:,}', 
                        va='center', fontsize=9)
            
            plt.tight_layout()
            plt.savefig('county_distribution.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("✓ County distribution saved as 'county_distribution.png'")
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report."""
        if self.df is None:
            return
        
        print("\n" + "="*60)
        print("COMPREHENSIVE VOTER DATA ANALYSIS SUMMARY")
        print("="*60)
        
        print(f"\n📊 DATASET OVERVIEW")
        print(f"   • Total registered voters: {len(self.df):,}")
        print(f"   • Data fields captured: {len(self.df.columns)}")
        print(f"   • Export date: July 29, 2025")
        print(f"   • Data source: New Jersey Voter File")
        
        total_cells = self.df.shape[0] * self.df.shape[1]
        missing_cells = self.df.isnull().sum().sum()
        completeness = ((total_cells - missing_cells) / total_cells) * 100
        
        print(f"\n🔍 DATA QUALITY")
        print(f"   • Total missing values: {missing_cells:,}")
        print(f"   • Data completeness: {completeness:.1f}%")
        print(f"   • Columns with missing data: {(self.df.isnull().sum() > 0).sum()}")
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        text_cols = self.df.select_dtypes(include=['object']).columns
        
        print(f"\n📋 COLUMN TYPES")
        print(f"   • Numeric columns: {len(numeric_cols)}")
        print(f"   • Text columns: {len(text_cols)}")
        
        print(f"\n💡 KEY INSIGHTS")
        
        if 'demo_party' in self.df.columns:
            party_dist = self.df['demo_party'].value_counts()
            top_party = party_dist.index[0] if len(party_dist) > 0 else "Unknown"
            top_party_pct = (party_dist.iloc[0] / len(self.df) * 100) if len(party_dist) > 0 else 0
            print(f"   • Most common party affiliation: {top_party} ({top_party_pct:.1f}%)")
        
        if 'county_name' in self.df.columns:
            county_dist = self.df['county_name'].value_counts()
            top_county = county_dist.index[0] if len(county_dist) > 0 else "Unknown"
            top_county_count = county_dist.iloc[0] if len(county_dist) > 0 else 0
            print(f"   • Largest county by voter count: {top_county} ({top_county_count:,} voters)")
        
        if 'demo_age' in self.df.columns:
            avg_age = self.df['demo_age'].mean()
            print(f"   • Average voter age: {avg_age:.1f} years")
        
        participation_cols = [col for col in self.df.columns if 'participation_' in col]
        if participation_cols and 'total_elections_participated' in self.df.columns:
            avg_participation = self.df['total_elections_participated'].mean()
            print(f"   • Average elections participated: {avg_participation:.1f}")
        
        print(f"\n📈 ANALYSIS OUTPUTS")
        print(f"   • Demographics visualization: voter_demographics_overview.png")
        print(f"   • Participation trends: voting_participation_trends.png")
        print(f"   • Geographic distribution: county_distribution.png")
        print(f"   • Detailed analysis script: real_voter_analysis.py")
        
        print(f"\n✅ Analysis complete! Check the generated visualization files.")

def main():
    """Main execution function."""
    csv_file_path = '/home/ubuntu/export-20250729.csv'
    
    print("🗳️  NEW JERSEY REAL VOTER FILE ANALYSIS")
    print("="*50)
    
    analyzer = RealVoterDataAnalyzer(csv_file_path)
    
    if analyzer.load_data():
        analyzer.explore_data_structure()
        analyzer.analyze_demographics()
        analyzer.analyze_geographic_patterns()
        analyzer.analyze_voting_patterns()
        analyzer.create_visualizations()
        analyzer.generate_summary_report()
    else:
        print("Failed to load voter data. Please check the file path and try again.")

if __name__ == "__main__":
    main()
