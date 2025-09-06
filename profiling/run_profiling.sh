#!/bin/bash

# NJ Voter Chat - Complete Performance Profiling Suite
# This script runs all profiling tools and generates comprehensive reports

echo "======================================================================"
echo "NJ VOTER CHAT - PERFORMANCE PROFILING SUITE"
echo "======================================================================"
echo ""

# Create profiling results directory
RESULTS_DIR="profiling/results_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

echo "📁 Results will be saved to: $RESULTS_DIR"
echo ""

# Check Python environment
echo "🐍 Checking Python environment..."
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️  No virtual environment found. Using system Python."
fi

# Function to check if backend is running
check_backend() {
    echo "🔍 Checking if backend is running..."
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo "✅ Backend is running"
        return 0
    else
        echo "❌ Backend is not running"
        return 1
    fi
}

# Menu
echo "Select profiling options:"
echo "========================="
echo "1) Profile BigQuery Performance (standalone)"
echo "2) Profile Backend & Agent (requires running backend)"
echo "3) Profile Frontend (analyzes build)"
echo "4) Run Complete Profile Suite"
echo "5) Quick Performance Check"
echo ""
read -p "Enter choice (1-5): " choice

case $choice in
    1)
        echo ""
        echo "🗄️ Running BigQuery Performance Profiler..."
        echo "----------------------------------------"
        python profiling/profile_bigquery.py
        if [ -f profiling/bigquery_profile_*.json ]; then
            mv profiling/bigquery_profile_*.json "$RESULTS_DIR/"
            echo "✅ BigQuery profiling complete"
        fi
        ;;
        
    2)
        echo ""
        if check_backend; then
            echo "🚀 Running Backend Performance Profiler..."
            echo "----------------------------------------"
            python profiling/profile_backend.py
            if [ -f profiling/backend_profile_*.json ]; then
                mv profiling/backend_profile_*.json "$RESULTS_DIR/"
                echo "✅ Backend profiling complete"
            fi
        else
            echo "Please start the backend first:"
            echo "  python backend/main.py"
            exit 1
        fi
        ;;
        
    3)
        echo ""
        echo "📦 Running Frontend Performance Analyzer..."
        echo "----------------------------------------"
        
        # Check if build exists
        if [ ! -d "frontend/build" ]; then
            echo "⚠️  No build found. Building frontend..."
            cd frontend
            npm run build
            cd ..
        fi
        
        python profiling/profile_frontend.py
        if [ -f profiling/frontend_profile_*.json ]; then
            mv profiling/frontend_profile_*.json "$RESULTS_DIR/"
            echo "✅ Frontend profiling complete"
        fi
        
        # Run webpack analyzer if available
        if [ -f "frontend/package.json" ]; then
            echo ""
            read -p "Run webpack bundle analyzer? (y/n): " run_analyzer
            if [ "$run_analyzer" = "y" ]; then
                cd frontend
                npx webpack-bundle-analyzer build/bundle-stats.json -m static -r ../profiling/bundle-report.html
                cd ..
                mv profiling/bundle-report.html "$RESULTS_DIR/"
            fi
        fi
        ;;
        
    4)
        echo ""
        echo "🎯 Running Complete Profile Suite..."
        echo "====================================="
        
        # BigQuery
        echo ""
        echo "[1/3] BigQuery Performance..."
        python profiling/profile_bigquery.py
        
        # Backend (if running)
        echo ""
        echo "[2/3] Backend Performance..."
        if check_backend; then
            python profiling/profile_backend.py
        else
            echo "⚠️  Skipping backend profiling (not running)"
        fi
        
        # Frontend
        echo ""
        echo "[3/3] Frontend Performance..."
        python profiling/profile_frontend.py
        
        # Move all results
        mv profiling/*_profile_*.json "$RESULTS_DIR/" 2>/dev/null
        
        echo ""
        echo "✅ Complete profiling suite finished!"
        ;;
        
    5)
        echo ""
        echo "⚡ Quick Performance Check..."
        echo "============================"
        
        # Quick BigQuery check
        echo ""
        echo "BigQuery Performance:"
        python -c "
from google.cloud import bigquery
import time

client = bigquery.Client(project='proj-roth')

# Test query
query = 'SELECT COUNT(*) FROM \`proj-roth.voter_data.voters\`'
start = time.time()
result = list(client.query(query).result())
elapsed = (time.time() - start) * 1000

print(f'  - Row count query: {elapsed:.2f}ms')
print(f'  - Total voters: {result[0][0]:,}')
"
        
        # Quick backend check
        if check_backend; then
            echo ""
            echo "Backend Response Times:"
            echo "  - Health check:"
            time curl -s http://localhost:8080/health > /dev/null
            echo "  - Auth check:"
            time curl -s http://localhost:8080/api/auth/me > /dev/null
        fi
        
        # Quick frontend check
        if [ -d "frontend/build" ]; then
            echo ""
            echo "Frontend Bundle Sizes:"
            du -sh frontend/build/static/js/*.js 2>/dev/null | head -5
            echo ""
            echo "Total build size:"
            du -sh frontend/build
        fi
        ;;
        
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "======================================================================"
echo "PROFILING COMPLETE"
echo "======================================================================"
echo ""
echo "📊 Results saved to: $RESULTS_DIR"
echo ""
echo "Next steps:"
echo "-----------"
echo "1. Review JSON reports in $RESULTS_DIR"
echo "2. Check optimization recommendations in each report"
echo "3. Run 'bash profiling/optimize_frontend.sh' for frontend optimizations"
echo ""

# Generate summary report
if [ -d "$RESULTS_DIR" ]; then
    echo "📝 Generating summary report..."
    python -c "
import json
import glob
from pathlib import Path

results_dir = Path('$RESULTS_DIR')
reports = list(results_dir.glob('*.json'))

if reports:
    print('')
    print('PERFORMANCE SUMMARY')
    print('==================')
    
    for report_path in reports:
        with open(report_path) as f:
            data = json.load(f)
            
        if 'bigquery' in report_path.name:
            print(f'\\n📊 BigQuery:')
            if 'queries' in data:
                slow = [q for q in data['queries'] if q.get('total_time_ms', 0) > 500]
                if slow:
                    print(f'  ⚠️  {len(slow)} slow queries (>500ms)')
                else:
                    print(f'  ✅ All queries fast (<500ms)')
                    
        elif 'backend' in report_path.name:
            print(f'\\n🚀 Backend:')
            if 'endpoints' in data:
                slow = [e for e, d in data['endpoints'].items() if d.get('response_time_ms', 0) > 100]
                if slow:
                    print(f'  ⚠️  {len(slow)} slow endpoints: {', '.join(slow[:3])}'
                else:
                    print(f'  ✅ All endpoints fast (<100ms)')
                    
        elif 'frontend' in report_path.name:
            print(f'\\n📦 Frontend:')
            if 'bundle_analysis' in data:
                size = data['bundle_analysis'].get('total_size_kb', 0)
                if size > 500:
                    print(f'  ⚠️  Large bundle: {size}KB (recommend <500KB)')
                else:
                    print(f'  ✅ Bundle size OK: {size}KB')
"
fi

echo ""
echo "✨ Done!"