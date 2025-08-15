import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

class VoterDataAnalyzer:
    def __init__(self, csv_file_path):
        """Initialize the voter data analyzer with a CSV file path."""
        self.csv_file_path = csv_file_path
        self.data = None
        self.summary_stats = {}
        
    def load_data(self):
        """Load the voter data from CSV file."""
        try:
            print(f"Loading voter data from {self.csv_file_path}...")
            self.data = pd.read_csv(self.csv_file_path)
            print(f"Data loaded successfully! Shape: {self.data.shape}")
            return True
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    def explore_data_structure(self):
        """Explore the basic structure and content of the voter data."""
        if self.data is None:
            print("No data loaded. Please load data first.")
            return
        
        print("\n" + "="*50)
        print("VOTER DATA EXPLORATION")
        print("="*50)
        
        print(f"\nDataset Shape: {self.data.shape}")
        print(f"Columns: {len(self.data.columns)}")
        print(f"Rows: {len(self.data)}")
        
        print("\nColumn Names and Types:")
        print("-" * 30)
        for col in self.data.columns:
            dtype = self.data[col].dtype
            null_count = self.data[col].isnull().sum()
            null_pct = (null_count / len(self.data)) * 100
            print(f"{col:25} | {str(dtype):15} | Nulls: {null_count:6} ({null_pct:5.1f}%)")
        
        print("\nFirst 5 rows:")
        print("-" * 30)
        print(self.data.head())
        
        print("\nBasic Statistics:")
        print("-" * 30)
        print(self.data.describe(include='all'))
        
        self.summary_stats = {
            'total_voters': len(self.data),
            'columns': list(self.data.columns),
            'missing_data': self.data.isnull().sum().to_dict()
        }
    
    def analyze_demographics(self):
        """Analyze demographic patterns in voter data."""
        if self.data is None:
            return
        
        print("\n" + "="*50)
        print("DEMOGRAPHIC ANALYSIS")
        print("="*50)
        
        demographic_columns = []
        for col in self.data.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['age', 'birth', 'gender', 'sex', 'party', 'affiliation']):
                demographic_columns.append(col)
        
        if demographic_columns:
            print(f"\nFound demographic columns: {demographic_columns}")
            for col in demographic_columns:
                print(f"\n{col} Distribution:")
                print(self.data[col].value_counts().head(10))
        else:
            print("No obvious demographic columns found. Analyzing all categorical columns...")
            categorical_cols = self.data.select_dtypes(include=['object']).columns
            for col in categorical_cols[:5]:  # Limit to first 5 categorical columns
                print(f"\n{col} Distribution:")
                print(self.data[col].value_counts().head(10))
    
    def analyze_geographic_patterns(self):
        """Analyze geographic distribution of voters."""
        if self.data is None:
            return
        
        print("\n" + "="*50)
        print("GEOGRAPHIC ANALYSIS")
        print("="*50)
        
        geo_columns = []
        for col in self.data.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['zip', 'county', 'city', 'town', 'district', 'ward', 'precinct']):
                geo_columns.append(col)
        
        if geo_columns:
            print(f"\nFound geographic columns: {geo_columns}")
            for col in geo_columns:
                unique_count = self.data[col].nunique()
                print(f"\n{col}: {unique_count} unique values")
                if unique_count <= 20:
                    print(self.data[col].value_counts())
                else:
                    print("Top 10 most common:")
                    print(self.data[col].value_counts().head(10))
        else:
            print("No obvious geographic columns found.")
    
    def create_visualizations(self):
        """Create comprehensive visualizations of the voter data."""
        if self.data is None:
            return
        
        print("\n" + "="*50)
        print("CREATING VISUALIZATIONS")
        print("="*50)
        
        plt.style.use('default')
        sns.set_palette("husl")
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('New Jersey Voter File Analysis - Overview', fontsize=16, fontweight='bold')
        
        missing_data = self.data.isnull().sum()
        if missing_data.sum() > 0:
            ax1 = axes[0, 0]
            missing_pct = (missing_data / len(self.data)) * 100
            missing_pct = missing_pct[missing_pct > 0].sort_values(ascending=True)
            if len(missing_pct) > 0:
                missing_pct.plot(kind='barh', ax=ax1, color='coral')
                ax1.set_title('Missing Data by Column (%)')
                ax1.set_xlabel('Percentage Missing')
        else:
            axes[0, 0].text(0.5, 0.5, 'No Missing Data Found', ha='center', va='center', fontsize=12)
            axes[0, 0].set_title('Data Completeness')
        
        ax2 = axes[0, 1]
        dtype_counts = self.data.dtypes.value_counts()
        dtype_counts.plot(kind='pie', ax=ax2, autopct='%1.1f%%')
        ax2.set_title('Data Types Distribution')
        ax2.set_ylabel('')
        
        ax3 = axes[1, 0]
        ax3.text(0.5, 0.7, f'Total Voters: {len(self.data):,}', ha='center', va='center', fontsize=14, fontweight='bold')
        ax3.text(0.5, 0.5, f'Columns: {len(self.data.columns)}', ha='center', va='center', fontsize=12)
        ax3.text(0.5, 0.3, f'Data Export Date: July 29, 2025', ha='center', va='center', fontsize=10)
        ax3.set_title('Dataset Overview')
        ax3.axis('off')
        
        ax4 = axes[1, 1]
        categorical_cols = self.data.select_dtypes(include=['object']).columns
        if len(categorical_cols) > 0:
            best_col = None
            for col in categorical_cols:
                unique_count = self.data[col].nunique()
                if 2 <= unique_count <= 15:  # Good range for visualization
                    best_col = col
                    break
            
            if best_col:
                value_counts = self.data[best_col].value_counts().head(10)
                value_counts.plot(kind='bar', ax=ax4, color='skyblue')
                ax4.set_title(f'Distribution: {best_col}')
                ax4.tick_params(axis='x', rotation=45)
            else:
                ax4.text(0.5, 0.5, 'No suitable categorical\nvariable for plotting', ha='center', va='center')
                ax4.set_title('Categorical Analysis')
        else:
            ax4.text(0.5, 0.5, 'No categorical\ncolumns found', ha='center', va='center')
            ax4.set_title('Categorical Analysis')
        
        plt.tight_layout()
        plt.savefig('/home/ubuntu/voter_analysis_overview.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✓ Overview visualization saved as 'voter_analysis_overview.png'")
        
        self._create_detailed_visualizations()
    
    def _create_detailed_visualizations(self):
        """Create detailed visualizations based on identified patterns."""
        
        party_cols = [col for col in self.data.columns if 'party' in col.lower() or 'affiliation' in col.lower()]
        if party_cols:
            self._plot_party_distribution(party_cols[0])
        
        geo_cols = [col for col in self.data.columns if any(geo in col.lower() for geo in ['county', 'zip', 'city'])]
        if geo_cols:
            self._plot_geographic_distribution(geo_cols[0])
        
        age_cols = [col for col in self.data.columns if 'age' in col.lower() or 'birth' in col.lower() or 'year' in col.lower()]
        if age_cols:
            self._plot_age_distribution(age_cols[0])
    
    def _plot_party_distribution(self, party_col):
        """Plot party affiliation distribution."""
        plt.figure(figsize=(12, 6))
        party_counts = self.data[party_col].value_counts()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        party_counts.head(10).plot(kind='bar', ax=ax1, color='lightcoral')
        ax1.set_title(f'Voter Registration by {party_col}')
        ax1.set_xlabel('Party Affiliation')
        ax1.set_ylabel('Number of Voters')
        ax1.tick_params(axis='x', rotation=45)
        
        top_parties = party_counts.head(8)
        other_count = party_counts.iloc[8:].sum() if len(party_counts) > 8 else 0
        if other_count > 0:
            top_parties['Other'] = other_count
        
        ax2.pie(top_parties.values, labels=top_parties.index, autopct='%1.1f%%', startangle=90)
        ax2.set_title('Party Distribution (Percentage)')
        
        plt.tight_layout()
        plt.savefig('/home/ubuntu/party_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Party distribution visualization saved as 'party_distribution.png'")
    
    def _plot_geographic_distribution(self, geo_col):
        """Plot geographic distribution."""
        plt.figure(figsize=(12, 8))
        geo_counts = self.data[geo_col].value_counts().head(20)
        
        geo_counts.plot(kind='barh', color='lightgreen')
        plt.title(f'Voter Distribution by {geo_col} (Top 20)')
        plt.xlabel('Number of Voters')
        plt.ylabel(geo_col)
        plt.tight_layout()
        plt.savefig('/home/ubuntu/geographic_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Geographic distribution visualization saved as 'geographic_distribution.png'")
    
    def _plot_age_distribution(self, age_col):
        """Plot age distribution."""
        plt.figure(figsize=(12, 6))
        
        age_data = pd.to_numeric(self.data[age_col], errors='coerce')
        age_data = age_data.dropna()
        
        if len(age_data) > 0:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            ax1.hist(age_data, bins=30, color='lightblue', alpha=0.7, edgecolor='black')
            ax1.set_title(f'Distribution of {age_col}')
            ax1.set_xlabel(age_col)
            ax1.set_ylabel('Frequency')
            
            ax2.boxplot(age_data)
            ax2.set_title(f'{age_col} Box Plot')
            ax2.set_ylabel(age_col)
            
            plt.tight_layout()
            plt.savefig('/home/ubuntu/age_distribution.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("✓ Age distribution visualization saved as 'age_distribution.png'")
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report."""
        if self.data is None:
            return
        
        print("\n" + "="*60)
        print("COMPREHENSIVE VOTER DATA ANALYSIS SUMMARY")
        print("="*60)
        
        print(f"\n📊 DATASET OVERVIEW")
        print(f"   • Total registered voters: {len(self.data):,}")
        print(f"   • Data fields captured: {len(self.data.columns)}")
        print(f"   • Export date: July 29, 2025")
        print(f"   • Data source: New Jersey Voter File")
        
        missing_data = self.data.isnull().sum()
        total_missing = missing_data.sum()
        print(f"\n🔍 DATA QUALITY")
        print(f"   • Total missing values: {total_missing:,}")
        print(f"   • Data completeness: {((len(self.data) * len(self.data.columns) - total_missing) / (len(self.data) * len(self.data.columns)) * 100):.1f}%")
        
        if total_missing > 0:
            print(f"   • Columns with missing data: {(missing_data > 0).sum()}")
        
        numeric_cols = len(self.data.select_dtypes(include=[np.number]).columns)
        text_cols = len(self.data.select_dtypes(include=['object']).columns)
        date_cols = len(self.data.select_dtypes(include=['datetime']).columns)
        
        print(f"\n📋 COLUMN TYPES")
        print(f"   • Numeric columns: {numeric_cols}")
        print(f"   • Text columns: {text_cols}")
        print(f"   • Date columns: {date_cols}")
        
        print(f"\n💡 KEY INSIGHTS")
        
        categorical_cols = self.data.select_dtypes(include=['object']).columns
        for col in categorical_cols[:3]:  # Analyze first 3 categorical columns
            unique_count = self.data[col].nunique()
            most_common = self.data[col].mode().iloc[0] if len(self.data[col].mode()) > 0 else "N/A"
            print(f"   • {col}: {unique_count} unique values, most common: '{most_common}'")
        
        print(f"\n📈 ANALYSIS OUTPUTS")
        print(f"   • Overview visualization: voter_analysis_overview.png")
        print(f"   • Detailed analysis script: voter_data_analysis.py")
        print(f"   • Additional charts generated based on data content")
        
        return self.summary_stats

def main():
    """Main function to run the voter data analysis."""
    csv_file = "/home/ubuntu/export-20250729.csv"
    
    print("🗳️  NEW JERSEY VOTER FILE ANALYSIS")
    print("=" * 50)
    
    analyzer = VoterDataAnalyzer(csv_file)
    
    if analyzer.load_data():
        analyzer.explore_data_structure()
        analyzer.analyze_demographics()
        analyzer.analyze_geographic_patterns()
        analyzer.create_visualizations()
        analyzer.generate_summary_report()
        
        print(f"\n✅ Analysis complete! Check the generated visualization files.")
    else:
        print("❌ Could not load data file. Please ensure the file exists and is accessible.")
        print(f"Expected file location: {csv_file}")
        print("\nThis script is ready to analyze the voter data once the file is available.")

if __name__ == "__main__":
    main()
