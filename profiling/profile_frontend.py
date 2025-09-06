#!/usr/bin/env python3
"""
Frontend Performance Analyzer
Analyzes React app bundle size, dependencies, and performance metrics.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

class FrontendProfiler:
    def __init__(self):
        self.frontend_dir = Path(__file__).parent.parent / "frontend"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "bundle_analysis": {},
            "dependencies": {},
            "lighthouse": {},
            "recommendations": []
        }
        
    def analyze_bundle_size(self) -> Dict:
        """Analyze webpack bundle size"""
        
        build_dir = self.frontend_dir / "build"
        
        if not build_dir.exists():
            return {"error": "Build directory not found. Run 'npm run build' first."}
            
        bundle_stats = {
            "static/js": {},
            "static/css": {},
            "total_size_kb": 0
        }
        
        # Analyze JS bundles
        js_dir = build_dir / "static" / "js"
        if js_dir.exists():
            for js_file in js_dir.glob("*.js"):
                size_kb = js_file.stat().st_size / 1024
                bundle_stats["static/js"][js_file.name] = {
                    "size_kb": round(size_kb, 2),
                    "gzipped_estimate_kb": round(size_kb * 0.3, 2)  # Rough estimate
                }
                bundle_stats["total_size_kb"] += size_kb
                
        # Analyze CSS bundles
        css_dir = build_dir / "static" / "css"
        if css_dir.exists():
            for css_file in css_dir.glob("*.css"):
                size_kb = css_file.stat().st_size / 1024
                bundle_stats["static/css"][css_file.name] = {
                    "size_kb": round(size_kb, 2),
                    "gzipped_estimate_kb": round(size_kb * 0.2, 2)
                }
                bundle_stats["total_size_kb"] += size_kb
                
        bundle_stats["total_size_kb"] = round(bundle_stats["total_size_kb"], 2)
        
        return bundle_stats
    
    def analyze_dependencies(self) -> Dict:
        """Analyze npm dependencies and their sizes"""
        
        package_json_path = self.frontend_dir / "package.json"
        
        if not package_json_path.exists():
            return {"error": "package.json not found"}
            
        with open(package_json_path, 'r') as f:
            package_data = json.load(f)
            
        deps = package_data.get("dependencies", {})
        dev_deps = package_data.get("devDependencies", {})
        
        # Identify large/problematic dependencies
        large_deps = []
        
        # Known large dependencies
        size_estimates = {
            "react": 42,
            "react-dom": 120,
            "@mui/material": 350,
            "@mui/icons-material": 5000,  # Can be huge if not tree-shaken
            "plotly.js": 3500,
            "react-plotly.js": 50,
            "socket.io-client": 85,
            "axios": 15,
            "marked": 35,
            "react-markdown": 45,
            "leaflet": 140,
            "react-leaflet": 60
        }
        
        for dep, version in deps.items():
            estimated_size = size_estimates.get(dep, 20)  # Default 20kb
            if estimated_size > 100:
                large_deps.append({
                    "name": dep,
                    "version": version,
                    "estimated_size_kb": estimated_size
                })
                
        return {
            "total_dependencies": len(deps),
            "total_dev_dependencies": len(dev_deps),
            "large_dependencies": sorted(large_deps, key=lambda x: x["estimated_size_kb"], reverse=True),
            "dependencies": deps
        }
    
    def run_webpack_analyzer(self) -> Dict:
        """Run webpack-bundle-analyzer if available"""
        
        try:
            # Check if webpack-bundle-analyzer is installed
            result = subprocess.run(
                ["npm", "list", "webpack-bundle-analyzer"],
                cwd=self.frontend_dir,
                capture_output=True,
                text=True
            )
            
            if "webpack-bundle-analyzer" in result.stdout:
                print("  Running webpack-bundle-analyzer...")
                
                # Create stats file
                subprocess.run(
                    ["npm", "run", "build:stats"],
                    cwd=self.frontend_dir,
                    capture_output=True
                )
                
                return {"status": "Stats generated. Run 'npm run analyze' to view."}
            else:
                return {"status": "webpack-bundle-analyzer not installed"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_code_splitting(self) -> Dict:
        """Check for code splitting opportunities"""
        
        src_dir = self.frontend_dir / "src"
        
        if not src_dir.exists():
            return {"error": "src directory not found"}
            
        opportunities = []
        
        # Check for large components that could be lazy loaded
        large_components = []
        for tsx_file in src_dir.rglob("*.tsx"):
            size_kb = tsx_file.stat().st_size / 1024
            if size_kb > 50:  # Components larger than 50KB
                large_components.append({
                    "file": str(tsx_file.relative_to(self.frontend_dir)),
                    "size_kb": round(size_kb, 2)
                })
                
        # Check for dynamic imports
        dynamic_imports = 0
        lazy_components = 0
        
        for tsx_file in src_dir.rglob("*.tsx"):
            content = tsx_file.read_text()
            if "import(" in content:
                dynamic_imports += 1
            if "React.lazy" in content:
                lazy_components += 1
                
        return {
            "large_components": sorted(large_components, key=lambda x: x["size_kb"], reverse=True)[:10],
            "dynamic_imports_count": dynamic_imports,
            "lazy_components_count": lazy_components,
            "recommendations": self._get_splitting_recommendations(large_components, lazy_components)
        }
    
    def _get_splitting_recommendations(self, large_components: List, lazy_count: int) -> List[str]:
        """Generate code splitting recommendations"""
        
        recommendations = []
        
        if len(large_components) > 5 and lazy_count < 3:
            recommendations.append(
                "Consider implementing code splitting with React.lazy() for large components"
            )
            
        if any(c["size_kb"] > 100 for c in large_components):
            recommendations.append(
                "Found components >100KB. These are prime candidates for lazy loading"
            )
            
        return recommendations
    
    def check_performance_optimizations(self) -> Dict:
        """Check for React performance optimizations"""
        
        src_dir = self.frontend_dir / "src"
        optimizations = {
            "memo_usage": 0,
            "useMemo_usage": 0,
            "useCallback_usage": 0,
            "pureComponent_usage": 0,
            "virtual_scrolling": False,
            "recommendations": []
        }
        
        for tsx_file in src_dir.rglob("*.tsx"):
            content = tsx_file.read_text()
            
            if "React.memo" in content or "memo(" in content:
                optimizations["memo_usage"] += 1
            if "useMemo" in content:
                optimizations["useMemo_usage"] += 1
            if "useCallback" in content:
                optimizations["useCallback_usage"] += 1
            if "PureComponent" in content:
                optimizations["pureComponent_usage"] += 1
            if "react-window" in content or "react-virtualized" in content:
                optimizations["virtual_scrolling"] = True
                
        # Generate recommendations
        total_components = len(list(src_dir.rglob("*.tsx")))
        
        if optimizations["memo_usage"] < total_components * 0.1:
            optimizations["recommendations"].append(
                "Low React.memo usage. Consider memoizing expensive components"
            )
            
        if not optimizations["virtual_scrolling"]:
            optimizations["recommendations"].append(
                "Consider virtual scrolling for large lists (react-window)"
            )
            
        return optimizations
    
    def generate_optimization_script(self):
        """Generate optimization recommendations script"""
        
        script_content = """#!/bin/bash
# Frontend Optimization Script
# Generated by profiler

echo "🚀 Frontend Optimization Steps"
echo "=============================="

# 1. Install bundle analyzer
echo "📦 Installing bundle analyzer..."
npm install --save-dev webpack-bundle-analyzer

# 2. Add analyze script to package.json
echo "📝 Add to package.json scripts:"
echo '  "analyze": "source-map-explorer build/static/js/*.js"'

# 3. Install compression
echo "🗜️ Installing compression..."
npm install --save compression

# 4. Tree-shaking for Material-UI icons
echo "🌳 Optimize Material-UI imports:"
echo "  Change: import { Icon } from '@mui/icons-material'"
echo "  To: import Icon from '@mui/icons-material/Icon'"

# 5. Lazy load routes
echo "💤 Implement lazy loading:"
cat << 'EOF'
// Before
import Dashboard from './pages/Dashboard';

// After
const Dashboard = React.lazy(() => import('./pages/Dashboard'));

// Wrap with Suspense
<Suspense fallback={<Loading />}>
  <Dashboard />
</Suspense>
EOF

# 6. Optimize images
echo "🖼️ Optimize images:"
echo "  - Use WebP format"
echo "  - Implement lazy loading with Intersection Observer"
echo "  - Use responsive images with srcSet"

# 7. Enable production build optimizations
echo "⚡ Production optimizations:"
echo "  npm run build -- --profile"
echo "  Analyze with: npx source-map-explorer 'build/static/js/*.js'"

echo ""
echo "✅ Run 'npm run build' after implementing optimizations"
"""
        
        script_path = Path(__file__).parent / "optimize_frontend.sh"
        with open(script_path, 'w') as f:
            f.write(script_content)
            
        os.chmod(script_path, 0o755)
        
        return str(script_path)
    
    def run_full_profile(self):
        """Run complete frontend profiling"""
        
        print("🔍 Starting Frontend Performance Profiling...")
        
        # Analyze bundle size
        print("\n📦 Analyzing Bundle Size...")
        self.results["bundle_analysis"] = self.analyze_bundle_size()
        
        # Analyze dependencies
        print("📚 Analyzing Dependencies...")
        self.results["dependencies"] = self.analyze_dependencies()
        
        # Check code splitting
        print("✂️ Analyzing Code Splitting...")
        self.results["code_splitting"] = self.analyze_code_splitting()
        
        # Check optimizations
        print("⚡ Checking Performance Optimizations...")
        self.results["optimizations"] = self.check_performance_optimizations()
        
        # Generate optimization script
        script_path = self.generate_optimization_script()
        
        # Save report
        self._generate_report()
        
        print(f"\n🔧 Optimization script created: {script_path}")
        
    def _generate_report(self):
        """Generate and save profiling report"""
        
        report_path = Path(__file__).parent / f"frontend_profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
            
        print(f"\n✅ Profile report saved to: {report_path}")
        
        # Print summary
        print("\n" + "="*60)
        print("FRONTEND PERFORMANCE SUMMARY")
        print("="*60)
        
        # Bundle size
        if "bundle_analysis" in self.results and "total_size_kb" in self.results["bundle_analysis"]:
            print(f"\n📦 Bundle Size: {self.results['bundle_analysis']['total_size_kb']} KB")
            
            if self.results["bundle_analysis"]["total_size_kb"] > 500:
                print("  ⚠️ Bundle size is large (>500KB). Consider code splitting.")
                
        # Dependencies
        if "dependencies" in self.results:
            deps = self.results["dependencies"]
            print(f"\n📚 Dependencies: {deps.get('total_dependencies', 0)}")
            
            if "large_dependencies" in deps and deps["large_dependencies"]:
                print("  Large dependencies:")
                for dep in deps["large_dependencies"][:5]:
                    print(f"    - {dep['name']}: ~{dep['estimated_size_kb']}KB")
                    
        # Code splitting
        if "code_splitting" in self.results:
            cs = self.results["code_splitting"]
            print(f"\n✂️ Code Splitting:")
            print(f"  - Lazy components: {cs.get('lazy_components_count', 0)}")
            print(f"  - Dynamic imports: {cs.get('dynamic_imports_count', 0)}")
            
            if cs.get("recommendations"):
                for rec in cs["recommendations"]:
                    print(f"  💡 {rec}")
                    
        # Optimizations
        if "optimizations" in self.results:
            opt = self.results["optimizations"]
            print(f"\n⚡ Performance Optimizations:")
            print(f"  - React.memo usage: {opt.get('memo_usage', 0)} components")
            print(f"  - useMemo hooks: {opt.get('useMemo_usage', 0)}")
            print(f"  - useCallback hooks: {opt.get('useCallback_usage', 0)}")
            
            if opt.get("recommendations"):
                for rec in opt["recommendations"]:
                    print(f"  💡 {rec}")

if __name__ == "__main__":
    print("="*60)
    print("FRONTEND PERFORMANCE PROFILER")
    print("="*60)
    
    profiler = FrontendProfiler()
    profiler.run_full_profile()