#!/usr/bin/env python3
"""
Fuzzy matching utilities for entity resolution.
Used to match individuals across voter and donation records.
"""

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Dict, List, Tuple, Optional

def normalize_name(name: str) -> str:
    """Normalize a name for matching."""
    if not name:
        return ''
    
    # Convert to uppercase
    name = name.upper()
    
    # Remove accents
    name = ''.join(
        c for c in unicodedata.normalize('NFD', name)
        if unicodedata.category(c) != 'Mn'
    )
    
    # Remove common suffixes
    suffixes = ['JR', 'SR', 'II', 'III', 'IV', 'V', 'ESQ', 'PHD', 'MD']
    for suffix in suffixes:
        name = name.replace(f' {suffix}', '').replace(f',{suffix}', '')
    
    # Remove punctuation except hyphens
    name = re.sub(r'[^\w\s-]', '', name)
    
    # Normalize whitespace
    name = ' '.join(name.split())
    
    return name

def extract_name_parts(full_name: str) -> Dict[str, str]:
    """Extract first, middle, last name from full name."""
    parts = {
        'first': '',
        'middle': '',
        'last': '',
        'suffix': ''
    }
    
    if not full_name:
        return parts
    
    # Clean the name
    clean_name = normalize_name(full_name)
    tokens = clean_name.split()
    
    if not tokens:
        return parts
    
    # Check for suffix
    suffixes = ['JR', 'SR', 'II', 'III', 'IV', 'V']
    if tokens[-1] in suffixes:
        parts['suffix'] = tokens[-1]
        tokens = tokens[:-1]
    
    if len(tokens) == 1:
        parts['last'] = tokens[0]
    elif len(tokens) == 2:
        parts['first'] = tokens[0]
        parts['last'] = tokens[1]
    elif len(tokens) == 3:
        parts['first'] = tokens[0]
        parts['middle'] = tokens[1]
        parts['last'] = tokens[2]
    else:
        # More than 3 parts - assume first is first, last is last, rest is middle
        parts['first'] = tokens[0]
        parts['last'] = tokens[-1]
        parts['middle'] = ' '.join(tokens[1:-1])
    
    return parts

def calculate_name_similarity(name1: Dict[str, str], name2: Dict[str, str]) -> float:
    """Calculate similarity score between two names (0-1)."""
    
    # Exact match on all parts
    if (name1['first'] == name2['first'] and 
        name1['last'] == name2['last'] and
        name1['middle'] == name2['middle']):
        return 1.0
    
    # Last name must match or be very similar
    last_similarity = SequenceMatcher(None, name1['last'], name2['last']).ratio()
    if last_similarity < 0.85:
        return 0.0
    
    # First name similarity
    first_similarity = SequenceMatcher(None, name1['first'], name2['first']).ratio()
    
    # Handle middle name/initial
    middle_similarity = 0.0
    if name1['middle'] and name2['middle']:
        # Both have middle names
        if name1['middle'][0] == name2['middle'][0]:
            # Same initial
            middle_similarity = 0.5
            if name1['middle'] == name2['middle']:
                middle_similarity = 1.0
    elif not name1['middle'] and not name2['middle']:
        # Neither has middle name
        middle_similarity = 1.0
    else:
        # One has middle, one doesn't - slight penalty
        middle_similarity = 0.3
    
    # Weighted average
    score = (
        last_similarity * 0.5 +
        first_similarity * 0.35 +
        middle_similarity * 0.15
    )
    
    return score

def match_individual(
    first_name: str,
    middle_name: str,
    last_name: str,
    address_id: str,
    existing_individuals: List[Dict]
) -> Tuple[Optional[str], float, str]:
    """
    Match an individual against existing individuals.
    
    Returns:
        Tuple of (master_id, confidence, method)
        - master_id: ID of matched individual or None
        - confidence: Match confidence score (0-1)
        - method: Description of matching method used
    """
    
    if not first_name or not last_name:
        return None, 0.0, 'missing_name'
    
    name1 = {
        'first': normalize_name(first_name),
        'middle': normalize_name(middle_name) if middle_name else '',
        'last': normalize_name(last_name)
    }
    
    best_match = None
    best_score = 0.0
    best_method = 'no_match'
    
    for individual in existing_individuals:
        name2 = {
            'first': normalize_name(individual.get('name_first', '')),
            'middle': normalize_name(individual.get('name_middle', '')),
            'last': normalize_name(individual.get('name_last', ''))
        }
        
        # Check if same address
        same_address = (address_id == individual.get('address_id'))
        
        # Calculate name similarity
        name_score = calculate_name_similarity(name1, name2)
        
        # Adjust score based on address
        if same_address and name_score > 0.7:
            # Same address boosts confidence
            total_score = min(1.0, name_score * 1.2)
            method = 'name_address_match'
        elif same_address and name_score > 0.5:
            # Fuzzy name match at same address
            total_score = name_score
            method = 'fuzzy_name_same_address'
        elif name_score > 0.95:
            # Very strong name match even without address
            total_score = name_score * 0.9
            method = 'strong_name_match'
        else:
            continue
        
        if total_score > best_score:
            best_match = individual['master_id']
            best_score = total_score
            best_method = method
    
    # Require minimum confidence
    if best_score >= 0.7:
        return best_match, best_score, best_method
    
    return None, 0.0, 'no_confident_match'

def create_standardized_name(first: str, middle: str, last: str, suffix: str = '') -> str:
    """Create standardized name format for storage."""
    parts = []
    
    if last:
        parts.append(normalize_name(last))
    
    if first:
        parts.append(normalize_name(first))
    
    if middle:
        parts.append(normalize_name(middle))
    
    if suffix:
        parts.append(suffix)
    
    if len(parts) > 1 and last:
        # Format: "LAST, FIRST MIDDLE SUFFIX"
        return f"{parts[0]}, {' '.join(parts[1:])}"
    else:
        # Just concatenate what we have
        return ' '.join(parts)

def test_fuzzy_matcher():
    """Test the fuzzy matching functions."""
    
    print("Testing fuzzy matcher...")
    
    # Test name normalization
    assert normalize_name("John Smith Jr.") == "JOHN SMITH"
    assert normalize_name("María García") == "MARIA GARCIA"
    
    # Test name extraction
    parts = extract_name_parts("John Michael Smith Jr.")
    assert parts['first'] == 'JOHN'
    assert parts['middle'] == 'MICHAEL'
    assert parts['last'] == 'SMITH'
    
    # Test name similarity
    name1 = {'first': 'JOHN', 'middle': 'M', 'last': 'SMITH'}
    name2 = {'first': 'JOHN', 'middle': 'MICHAEL', 'last': 'SMITH'}
    score = calculate_name_similarity(name1, name2)
    assert score > 0.8
    
    print("All tests passed!")

if __name__ == "__main__":
    test_fuzzy_matcher()