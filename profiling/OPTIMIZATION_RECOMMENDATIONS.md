# Performance Optimization Recommendations

Based on profiling analysis performed on 2025-09-05

## 🚨 Critical Issues

### 1. Frontend Bundle Size (2.4MB)
**Impact**: Slow initial page load, especially on mobile
**Current**: 2366KB uncompressed
**Target**: <500KB

**Actions**:
```bash
# 1. Replace full Material-UI icons import
# BAD:
import { Home, Search, Person } from '@mui/icons-material';

# GOOD:
import Home from '@mui/icons-material/Home';
import Search from '@mui/icons-material/Search';
import Person from '@mui/icons-material/Person';

# 2. Implement code splitting for routes
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const VoterSearch = React.lazy(() => import('./pages/VoterSearch'));
const Maps = React.lazy(() => import('./pages/Maps'));

# 3. Tree-shake unused dependencies
npm prune --production
```

### 2. BigQuery Query Performance
**Impact**: Slow query responses (>1 second for some queries)
**Issues**: No clustering optimization, low cache hit rate

**Actions**:
```sql
-- Add clustering to voters table
ALTER TABLE `proj-roth.voter_data.voters`
CLUSTER BY city, demo_party, county_name;

-- Create materialized view for common aggregations
CREATE MATERIALIZED VIEW `proj-roth.voter_data.city_party_summary` AS
SELECT 
  city,
  demo_party,
  COUNT(*) as voter_count,
  AVG(CAST(SUBSTR(demo_age, 1, 3) AS INT64)) as avg_age
FROM `proj-roth.voter_data.voters`
GROUP BY city, demo_party;
```

## 🎯 High Priority Optimizations

### 1. Implement React Performance Optimizations
```typescript
// Use React.memo for expensive components
export default React.memo(VoterTable, (prevProps, nextProps) => {
  return prevProps.data === nextProps.data;
});

// Use useMemo for expensive calculations
const sortedVoters = useMemo(() => {
  return voters.sort((a, b) => a.name.localeCompare(b.name));
}, [voters]);

// Use useCallback for event handlers
const handleSearch = useCallback((query) => {
  // search logic
}, [dependencies]);
```

### 2. Implement Virtual Scrolling for Large Lists
```bash
npm install react-window

# Then in your component:
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={voters.length}
  itemSize={50}
  width={'100%'}
>
  {Row}
</FixedSizeList>
```

### 3. Optimize WebSocket Connection
- Implement connection pooling
- Add exponential backoff for reconnection
- Batch multiple messages

### 4. Add Response Caching
```python
# Backend caching for common queries
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def cached_bigquery_query(query_hash):
    # Execute query
    return results

def execute_query(sql):
    query_hash = hashlib.md5(sql.encode()).hexdigest()
    return cached_bigquery_query(query_hash)
```

## 📊 Performance Metrics Targets

| Metric | Current | Target | Priority |
|--------|---------|--------|----------|
| Frontend Bundle Size | 2.4MB | <500KB | Critical |
| Initial Page Load | ~3s | <1s | High |
| BigQuery Simple Count | 909ms | <200ms | Medium |
| BigQuery Complex Join | 1352ms | <500ms | High |
| WebSocket Latency | Variable | <50ms | Medium |
| Memory Usage (Backend) | Not measured | <500MB | Low |

## 🔧 Quick Wins (Can implement immediately)

1. **Enable BigQuery Query Caching**
   ```python
   job_config = bigquery.QueryJobConfig(use_query_cache=True)
   ```

2. **Add Frontend Compression**
   ```javascript
   // In webpack.config.js
   const CompressionPlugin = require('compression-webpack-plugin');
   
   plugins: [
     new CompressionPlugin({
       algorithm: 'gzip',
       test: /\.(js|css|html|svg)$/,
       threshold: 8192,
       minRatio: 0.8
     })
   ]
   ```

3. **Implement Browser Caching Headers**
   ```python
   # In FastAPI backend
   from fastapi.staticfiles import StaticFiles
   
   app.mount("/static", StaticFiles(
       directory="frontend/build/static",
       html=True,
       headers={"Cache-Control": "public, max-age=31536000"}
   ))
   ```

4. **Optimize Images**
   - Convert PNG to WebP format
   - Implement lazy loading
   - Use responsive images with srcSet

## 📈 Monitoring Setup

Create monitoring dashboard to track:
- Page load times (use Google Lighthouse CI)
- BigQuery query performance (use Cloud Monitoring)
- WebSocket connection stability
- Bundle size over time (webpack-bundle-analyzer)
- Error rates and response times

## 🚀 Implementation Priority

### Phase 1 (Week 1)
- [ ] Fix Material-UI icons imports
- [ ] Implement code splitting
- [ ] Enable query caching
- [ ] Add compression

### Phase 2 (Week 2)
- [ ] Add React.memo to components
- [ ] Implement virtual scrolling
- [ ] Create BigQuery materialized views
- [ ] Optimize images

### Phase 3 (Week 3)
- [ ] Add comprehensive caching layer
- [ ] Implement WebSocket optimizations
- [ ] Set up performance monitoring
- [ ] Optimize database indexes

## 📝 Testing Strategy

Before deploying optimizations:
1. Run performance profiling suite
2. Compare metrics against baseline
3. Test on slow network (Chrome DevTools Network throttling)
4. Test with large datasets (10K+ voters)
5. Monitor memory usage over time

## 🎉 Expected Improvements

After implementing these optimizations:
- **50-70% reduction** in initial load time
- **80% reduction** in bundle size
- **60% faster** BigQuery responses
- **90% reduction** in re-render time for large lists
- **Better UX** on mobile devices and slow connections

## Next Steps

1. Run `bash profiling/optimize_frontend.sh` to start frontend optimizations
2. Review and prioritize BigQuery indexes
3. Set up monitoring dashboard
4. Schedule weekly performance reviews